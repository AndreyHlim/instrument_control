import time

from PyQt6.QtCore import QObject, pyqtSignal

from dataclass import DeviceState
from instruments.fsva import RS_FSVA3013, Dim


class TraceWorker(QObject):
    """Рабочий поток: непрерывный опрос анализатора и выполнение команд.

    Живёт в собственном QThread (см. ConnectionMixin._start_trace_thread),
    циклически читает трассу, опрашивает параметры прибора по расписанию
    и выполняет команды из очереди. Результаты отдаёт сигналом
    state_ready, ошибки — error_occurred.

    Signals:
        state_ready(object): DeviceState с текущими данными трассы и
            значениями параметров. Эмитится полным кадром (после чтения
            трассы) либо быстрым кадром (quick_state — только параметры,
            затронутые командами пользователя).
        error_occurred(str): текст исключения из цикла run(); после
            ошибки делается пауза 1 с и цикл продолжается.
    """

    state_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, analyzer: RS_FSVA3013):
        """Подготовить воркер к запуску.

        Args:
            analyzer: уже созданный и подключённый объект анализатора
                (RS_FSVA3013). Владение ресурсом VISA остаётся за
                вызывающей стороной: воркер не закрывает соединение.

        Note:
            Реальный запуск — метод run(), вызываемый сигналом
            QThread.started после moveToThread.
        """
        super().__init__()
        self._analyzer = analyzer
        self._running = False
        self._commands: list[str] = []
        self._first_run = True

        # Как часто опрашивать каждый параметр (в итерациях цикла)
        self._poll_intervals = {
            'rbw_type': 50,
            'rbw': 10,          # каждые 10 кадров
            'vbw': 10,
            'rbw_auto': 30,
            'vbw_auto': 30,
            'span': 10,         # каждые 10 кадров
            'center': 1,        # каждый кадр
            'reflevel': 10,
            'amp_unit': 10,
            'atten': 20,        # редко меняется
            'range': 50,       # редко меняется
            'preamp': 50,      # редко меняется
            'transducer': 100,
            'cfstep': 50,
            'det': 50,
            'trace_acc': 50,
            'sweep': 50,
            'sweep_count': 50,
        }
        self._counters = {k: 0 for k in self._poll_intervals}
        self._cmd_to_param = {
            'rbw_type_set': 'rbw_type', 'rbw_up': 'rbw', 'rbw_down': 'rbw',
            'vbw_up': 'vbw', 'vbw_down': 'vbw',
            'set_vbw': 'vbw',
            'vbw_auto_set': 'vbw_auto',
            'rbw_auto_set': 'rbw_auto',
            'span_up': 'span', 'span_down': 'span',
            'cf_up': 'center', 'cf_down': 'center',
            'reflvl_up': 'reflevel', 'reflvl_down': 'reflevel',
            'amp_unit': 'amp_unit', 'transducer': 'transducer',
            'ref_range_up': 'range', 'ref_range_down': 'range',
            'atten_up': 'atten', 'atten_down': 'atten',
            'preamp': 'preamp', 'cfstep_set': 'cfstep',
            'set_cf': 'center', 'set_span': 'span',
            'det_set': 'det', 'trace_acc_set': 'trace_acc',
            'sweep_count_set': 'sweep_count',
            'sweep_mode': 'sweep',
            'set_rbw': 'rbw',
        }

    def run(self):
        """Основной цикл опроса прибора (выполняется в QThread).

        На каждой итерации:
        1. Выполняет все накопившиеся команды из очереди и формирует
           множество затронутых параметров.
        2. Для затронутых параметров делает немедленный опрос
           (quick_state) и эмитит его — интерфейс отреагирует на
           действия пользователя без ожидания полного кадра.
        3. Читает трассу (уровни и частоты), вычисляет максимум.
        4. Опрашивает параметры по расписанию _poll_intervals; на
           первой итерации — все сразу (счётчики предзаполняются).
        5. Эмитит полный DeviceState.

        Ошибки отдельных опросов не прерывают кадр: имя параметра и
        текст исключения печатаются в консоль. Ошибки на уровне трассы
        или выполнения команд эмитятся через error_occurred, после чего
        цикл делает паузу 1 с (первый запуск сбрасывается, чтобы в
        следующем кадре опросить все параметры заново).

        Note:
            Завершение — только через stop(): цикл крутится, пока
            self._running. Ожидание ответов прибора может задержать
            фактический выход из метода после stop().
        """
        self._running = True
        while self._running:
            try:
                affected_params = set()
                while self._commands:
                    cmd = self._commands.pop(0)
                    self._execute_command(cmd)
                    base_cmd = cmd.split(':')[0]
                    param = self._cmd_to_param.get(base_cmd)
                    if param:
                        affected_params.add(param)

                if affected_params:
                    quick_state = DeviceState()
                    for param in affected_params:
                        try:
                            self._poll_param(quick_state, param)
                            self._counters[param] = 0
                        except Exception as e:
                            print(f"[WORKER] quick poll {param}: {e}")
                    self.state_ready.emit(quick_state)

                state = DeviceState()
                state.levels = self._analyzer.get_trace_data_lvl(1)
                state.freqs = self._analyzer.get_trace_data_freq(1, dim=Dim.Hz)
                if state.levels:
                    state.marker_level = float(max(state.levels))

                failed = []
                for param in self._poll_intervals:
                    if self._first_run:
                        self._counters[param] = self._poll_intervals[param]
                    self._counters[param] += 1
                    if self._counters[param] >= self._poll_intervals[param]:
                        self._counters[param] = 0
                        try:
                            self._poll_param(state, param)
                        except Exception as e:
                            failed.append(f'{param}: {e}')

                self._first_run = False
                self.state_ready.emit(state)

                if failed:
                    print('[WORKER] Не опрошены:', '; '.join(failed))

            except Exception as e:
                self._first_run = True
                self.error_occurred.emit(str(e))
                time.sleep(1)  # не крутим цикл вхолостую

    def _poll_param(self, state: DeviceState, param: str):
        """Опросить один параметр прибора и записать его в состояние.

        Args:
            state: снимок DeviceState, в который пишется результат;
                при исключении поле останется None — кадр не пострадает.
            param: имя параметра из _poll_intervals, например 'rbw',
                'reflevel', 'transducer'.

        Raises:
            Любое исключение VISA/SCPI пробрасывается вызывающей
            стороне (run решает: печатать или эмитить ошибку).
        """
        if param == 'rbw_type':
            state.rbw_type = self._analyzer.get_type_filter_rbw()
        elif param == 'rbw':
            state.rbw = self._analyzer.get_rbw(dim=Dim.kHz)
        elif param == 'vbw':
            state.vbw = self._analyzer.get_vbw(dim=Dim.kHz)
        elif param == 'rbw_auto':
            state.rbw_auto = self._analyzer.is_rbw_auto_on()
        elif param == 'vbw_auto':
            state.vbw_auto = self._analyzer.is_vbw_auto_on()
        elif param == 'span':
            state.span = self._analyzer.get_span(dim=Dim.MHz)
        elif param == 'center':
            state.center = self._analyzer.get_cf(dim=Dim.MHz)
        elif param == 'reflevel':
            state.reflevel = float(self._analyzer.get_reflvl())
        elif param == 'amp_unit':
            state.amp_unit = self._analyzer.get_amp_unit()
        elif param == 'transducer':
            if self._analyzer.on_corr_tran():
                state.transducer = self._analyzer.get_name_corr_tran()
            else:
                state.transducer = 'Не выбрана (0 дБ)'
        elif param == 'atten':
            state.atten = self._analyzer.get_atten()
        elif param == 'range':
            state.range_val = self._analyzer.get_ref_range()
        elif param == 'preamp':
            state.preamp = self._analyzer.get_preamp()
        elif param == 'cfstep':
            state.cfstep = self._analyzer.get_step_freq(dim=Dim.MHz)
        elif param == 'det':
            state.det = self._analyzer.active_trc().get_trace_det_type()
        elif param == 'trace_acc':
            state.trace_acc = self._analyzer.active_trc().get_trace_acc_type()
        elif param == 'sweep':
            state.sweep_single = self._analyzer.is_run_single_on()
        elif param == 'sweep_count':
            state.sweep_count = self._analyzer.get_sweep_count()

    def _execute_command(self, cmd: str):
        """Выполнить одну команду на приборе.

        Формат команды: '<имя>' для безаргументных действий
        ('rbw_up', 'atten_down') либо '<имя>:<значение>' — значение
        отделяется первым двоеточием и парсится по типу (str/int/float).

        Args:
            cmd: команда из очереди, например 'set_cf:1000000000.0',
                'rbw_auto_set:on', 'transducer:VULB9160 зав.№ 9160-3397'.

        Raises:
            ValueError: значение не распарсилось (например,
                'set_cf:abc').
            Любое исключение VISA/SCPI от драйвера анализатора.
        """
        if cmd.startswith('rbw_type_set:'):
            val = cmd.split('rbw_type_set:', 1)[1]
            self._analyzer.set_type_filter_rbw(val)
        elif cmd == 'rbw_up':
            self._analyzer.rbw_up()
        elif cmd == 'rbw_down':
            self._analyzer.rbw_down()
        elif cmd == 'vbw_up':
            self._analyzer.vbw_up()
        elif cmd == 'vbw_down':
            self._analyzer.vbw_down()
        elif cmd.startswith('set_vbw:'):
            val = float(cmd.split('set_vbw:', 1)[1])
            self._analyzer.set_vbw(val, dim=Dim.Hz)
        elif cmd.startswith('rbw_auto_set:'):
            val = cmd.split('rbw_auto_set:', 1)[1] == 'on'
            self._analyzer.set_rbw_auto(val)
        elif cmd.startswith('vbw_auto_set:'):
            val = cmd.split('vbw_auto_set:', 1)[1] == 'on'
            self._analyzer.set_vbw_auto(val)
        elif cmd == 'span_up':
            self._analyzer.span_up()
        elif cmd == 'span_down':
            self._analyzer.span_down()
        elif cmd == 'cf_up':
            self._analyzer.cf_step(True)
        elif cmd == 'cf_down':
            self._analyzer.cf_step(False)
        elif cmd == 'reflvl_up':
            self._analyzer.set_reflvl_up(True)
        elif cmd == 'reflvl_down':
            self._analyzer.set_reflvl_up(False)
        elif cmd.startswith('amp_unit:'):
            val = cmd.split('amp_unit:', 1)[1]
            self._analyzer.set_amp_unit(val)
        elif cmd.startswith('transducer:'):
            val = cmd.split('transducer:', 1)[1]
            self._analyzer.set_corr_tran(val)
        elif cmd == 'ref_range_up':
            self._analyzer.ref_range_up(True)
        elif cmd == 'ref_range_down':
            self._analyzer.ref_range_up(False)
        elif cmd == 'atten_up':
            self._analyzer.atten_up(True)
        elif cmd == 'atten_down':
            self._analyzer.atten_up(False)
        elif cmd.startswith('preamp:'):
            val = cmd.split('preamp:', 1)[1]
            self._analyzer.set_preamp(val)
        elif cmd.startswith('cfstep_set:'):
            val = float(cmd.split('cfstep_set:', 1)[1])
            self._analyzer.set_step_freq(step=val, dim=Dim.MHz)
        elif cmd.startswith('set_cf:'):
            val = float(cmd.split('set_cf:', 1)[1])
            self._analyzer.set_cf(val, dim=Dim.Hz)
        elif cmd.startswith('set_span:'):
            val = float(cmd.split('set_span:', 1)[1])
            self._analyzer.set_span(val, dim=Dim.Hz)
        elif cmd.startswith('det_set:'):
            val = cmd.split('det_set:', 1)[1]
            self._analyzer.set_unit_detector(val)
        elif cmd.startswith('trace_acc_set:'):
            val = cmd.split('trace_acc_set:', 1)[1]
            self._analyzer.set_type_trace(val)
        elif cmd.startswith('sweep_mode:'):
            val = cmd.split('sweep_mode:', 1)[1]
            if val == 'cont':
                self._analyzer.set_sweep_mode(True)
            elif val == 'single':
                self._analyzer.set_sweep_mode(False)
        elif cmd.startswith('sweep_count_set:'):
            val = int(cmd.split('sweep_count_set:', 1)[1])
            self._analyzer.set_sweep_count(val)
        elif cmd == 'auto_max_on':
            self._analyzer.active_mrk().peak_track(2)
        elif cmd == 'auto_max_off':
            self._analyzer.active_mrk().peak_track(0)
        elif cmd == 'mrk_to_cf':
            self._analyzer.active_mrk().freq_mrt_to_center()
        elif cmd.startswith('set_rbw:'):
            val = float(cmd.split('set_rbw:', 1)[1])
            self._analyzer.set_rbw(val, dim=Dim.Hz)

    def send_command(self, command: str):
        """Поставить команду в очередь на выполнение (потокобезопасно).

        Вызывается из GUI-потока; добавление в список из нескольких
        потоков допустимо — dequeue идёт только в run() через pop(0).

        Args:
            command: строка команды в формате _execute_command.
        """
        self._commands.append(command)

    def stop(self):
        """Попросить основной цикл завершиться.

        Меняет только флаг _running: фактический выход из run()
        произойдёт после возврата текущей итерации, то есть с задержкой
        до одного полного опроса прибора. Ожидание — в
        ConnectionMixin._stop_trace_thread (quit + wait).
        """
        self._running = False
