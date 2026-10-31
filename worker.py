from PyQt6.QtCore import QObject, pyqtSignal

from dataclass import DeviceState
from fsva import RS_FSVA3013, Dim


class TraceWorker(QObject):
    state_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, analyzer: RS_FSVA3013):
        super().__init__()
        self._analyzer = analyzer
        self._running = False
        self._commands: list[str] = []
        self._first_run = True

        # Как часто опрашивать каждый параметр (в итерациях цикла)
        self._poll_intervals = {
            'rbw': 10,          # каждые 10 кадров
            'span': 10,         # каждые 10 кадров
            'center': 1,        # каждый кадр
            'reflevel': 10,
            'amp_unit': 10,
            'atten': 20,        # редко меняется
            'range': 50,       # редко меняется
            'preamp': 50,      # редко меняется
            'cfstep': 50,
            'det': 50,
            'trace_acc': 50,
            'sweep': 50,
            'sweep_count': 50,
        }
        self._counters = {k: 0 for k in self._poll_intervals}
        self._cmd_to_param = {
            'rbw_up': 'rbw', 'rbw_down': 'rbw',
            'span_up': 'span', 'span_down': 'span',
            'cf_up': 'center', 'cf_down': 'center',
            'reflvl_up': 'reflevel', 'reflvl_down': 'reflevel',
            'amp_unit': 'amp_unit',
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
                        self._poll_param(quick_state, param)
                        self._counters[param] = 0
                    self.state_ready.emit(quick_state)

                state = DeviceState()

                state.levels = self._analyzer.get_trace_data_lvl(1)
                state.freqs = self._analyzer.get_trace_data_freq(1, dim=Dim.Hz)

                # Максимум трассы — вместо get_lvl() маркера
                if state.levels:
                    state.marker_level = float(max(state.levels))

                for param in self._poll_intervals:
                    if self._first_run:
                        self._counters[param] = self._poll_intervals[param]
                    self._counters[param] += 1
                    if self._counters[param] >= self._poll_intervals[param]:
                        self._counters[param] = 0
                        self._poll_param(state, param)

                if self._first_run:
                    self._first_run = False

                self.state_ready.emit(state)

            except Exception as e:
                self._first_run = True
                self.error_occurred.emit(str(e))
                # print(f"[WORKER] Ошибка: {e} — ждём 1с и продолжаем")
                # time.sleep(1)

    def _poll_param(self, state: DeviceState, param: str):
        if param == 'rbw':
            state.rbw = self._analyzer.get_rbw(dim=Dim.kHz)
        elif param == 'span':
            state.span = self._analyzer.get_span(dim=Dim.MHz)
        elif param == 'center':
            state.center = self._analyzer.get_cf(dim=Dim.MHz)
        elif param == 'reflevel':
            state.reflevel = float(self._analyzer.get_reflvl())
        elif param == 'amp_unit':
            state.amp_unit = self._analyzer.get_amp_unit()
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
        if cmd == 'rbw_up':
            self._analyzer.rbw_up()
        elif cmd == 'rbw_down':
            self._analyzer.rbw_down()
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
        elif cmd == 'amp_unit':
            val = cmd.split('amp_unit:', 1)[1]
            self._analyzer.set_amp_unit(val)
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
        self._commands.append(command)

    def stop(self):
        self._running = False
