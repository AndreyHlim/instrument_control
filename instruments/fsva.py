from __future__ import annotations

import re
from enum import IntEnum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from pyvisa import ResourceManager, VisaIOError

from constants import ANT_NAMES


class Dim(IntEnum):
    Hz = 0
    kHz = 3
    MHz = 6
    GHz = 9


class RS_FSVA3013:
    FREQ_MIN_HZ = 10  # 100 кГц
    FREQ_MAX_HZ = 13e9   # 20 ГГц

    def __init__(self, address: str):
        """Инициализация анализатора спектра.

        Args:
            address: IP‑адрес прибора (пример: '10.255.0.100') или полный адрес

        Raises:
            ValueError: Если адрес некорректен
            ConnectionError: Если прибор недоступен
        """
        self._resource = None
        self._address = self._validate_address(address)
        self.act_mrk: int = 1
        self.active_trace_num = 1

        try:
            self._resource = ResourceManager().open_resource(
                f'TCPIP0::{self._address}::INSTR'
            )
            self._resource.read_termination = '\n'
            self._resource.write_termination = '\n'
            self._resource.timeout = 20000  # мс

            # Проверка связи с прибором
            self._check_connection()

        except VisaIOError as e:
            if self._resource:
                self._resource.close()
            message = (
                "Не удалось подключиться к анализатору "
                f"по адресу {self._address}"
            )
            QMessageBox.warning(None, 'Ошибка подключения', message)
            raise ConnectionError(f'{message}: {e}') from e
        except Exception as e:
            if self._resource:
                self._resource.close()
            raise ConnectionError(
                f"Ошибка при подключении к анализатору: {e}"
            ) from e

        # Инициализируем маркеры (1–9, а вообще 16 штук их)
        self._markers = {}
        for i in range(1, 10):
            self._markers[f'Marker {i}'] = Marker(
                num=i,
                analyzer=self,
            )
        # Создаём атрибуты marker1–marker9
        for name, marker in self._markers.items():
            setattr(self, name, marker)

        # Инициализируем трассы (1–4, а вообще 6 штук их)
        self._traces = {}
        for i in range(1, 5):
            self._traces[f'Trace {i}'] = Trace(
                num=i,
                analyzer=self,
            )
        # Создаём атрибуты trace1–trace4
        for name, trace in self._traces.items():
            setattr(self, name, trace)

    def connect(self):
        self._resource = ResourceManager().open_resource(
            f'TCPIP0::{self._address}::INSTR'
        )

    def _validate_address(self, address: str) -> str:
        """Валидация IP‑адреса или полного адреса.

        Args:
            address: Введённый адрес

        Returns:
            Корректный IP‑адрес

        Raises:
            ValueError: Если адрес не соответствует формату
        """
        # Если адрес уже содержит полный формат (с портом и т. д.),
        # возвращаем как есть
        if '::' in address:
            return address

        # Проверяем формат IP‑адреса
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, address):
            raise ValueError(
                f"Некорректный формат IP‑адреса: '{address}'. "
                "Ожидаемый формат: 'xxx.xxx.xxx.xxx'"
            )

        # Дополнительная проверка диапазонов cоктетов
        octets = address.split('.')
        for octet in octets:
            num = int(octet)
            if num < 0 or num > 255:
                raise ValueError(f"Некорректное значение в IP‑адресе: {octet}")

        return address

    def is_run_single_on(self) -> bool:
        return self._resource.query(':INIT:CONT?') == '0'

    def set_sweep_mode(self, mode: bool, sweep_count: int = 0):
        """
        Установить режим непрерывных измерений
        Args:
            mode: True - непрерывный режим, False - одиночный
        """
        if mode:
            self._resource.write(':INIT:CONT ON')
        else:
            self._resource.write(':INIT:CONT OFF')

    def get_sweep_count(self) -> int:
        count = self._resource.query(':SENS:SWE:COUN?')
        return int(count)

    def set_sweep_count(self, count: int):
        self._resource.write(f':SENS:SWE:COUN {count}')

    def spg_is_on(self) -> Qt.CheckState:
        if self._resource.query(':CALC:SGR?') == '1':
            return Qt.CheckState.Checked
        return Qt.CheckState.Unchecked

    def spg_on(self):
        """Включение водопада."""
        self._resource.write(":LAY:ADD:WIND? '2',BEL,SGR")

    def spg_off(self):
        """Выключение водопада."""
        self._resource.write(":LAY:REM:WIND '2'")

    def _check_connection(self):
        """Проверка связи с прибором — отправляем простой запрос."""
        try:
            # Запрос идентификационной строки прибора
            idn = self._resource.query('*IDN?')
            print(idn)
            if not idn or 'unknown' in idn.lower():
                raise VisaIOError("Прибор не отвечает корректно")
        except VisaIOError:
            raise ConnectionError(
                "Прибор подключён, но не отвечает на запросы (*IDN?)"
            )

    def get_rbw(self, dim: Dim = Dim.Hz) -> float:
        """
        Ширина полосы пропускания в требуемой размерности
        Args:
            dim: размерность, в которой нужна полоса пропускания
        """
        rbw = int(float(self._resource.query(':SENS:BAND:RES?')))
        return rbw / (10 ** dim)

    def get_vbw(self, dim: Dim = Dim.Hz) -> float:
        """
        Ширина полосы видеополосы в требуемой размерности
        Args:
            dim: размерность
        """
        vbw = int(float(self._resource.query(':SENS:BAND:VID?')))
        return vbw / (10 ** dim)

    def set_rbw(self, rbw: float, dim: Dim = Dim.Hz):
        """
        Установить ширину полосы пропускания в требуемой размерности
        Args:
            dim: размерность, в которой указана полоса пропускания
        """
        rbw_hz = int(rbw * (10 ** dim))
        cur_span = self.get_span()
        if rbw_hz > cur_span:
            self.set_span(rbw_hz)
        self._resource.write(f':SENS:BAND:RES {rbw_hz}')

    def set_vbw(self, vbw: float, dim: Dim = Dim.Hz):
        """
        Установить видеоширину в требуемой размерности
        Args:
            dim: размерность
        """
        vbw_hz = int(vbw * (10 ** dim))
        self._resource.write(f':SENS:BAND:VID {vbw_hz}')

    def set_rbw_auto(self, state: bool = False):
        """Установить/отключить авто RBW"""
        if state:
            self._resource.write(':SENS:BAND:RES:AUTO ON')
            return
        self._resource.write(':SENS:BAND:RES:AUTO OFF')

    def set_vbw_auto(self, state: bool = False):
        """Установить/отключить авто VBW"""
        if state:
            self._resource.write(':SENS:BAND:VID:AUTO ON')
            return
        self._resource.write(':SENS:BAND:VID:AUTO OFF')

    def is_rbw_auto_on(self) -> bool:
        """Установлена ли RBV в авто?"""
        is_rbw_auto_on = self._resource.query(':SENS:BAND:RES:AUTO?')
        return is_rbw_auto_on == '1'

    def is_vbw_auto_on(self) -> bool:
        """Установлена ли RBV в авто?"""
        is_vbw_auto_on = self._resource.query(':SENS:BAND:VID:AUTO?')
        return is_vbw_auto_on == '1'

    def get_cf(self, dim: Dim = Dim.Hz) -> float:
        """Текущая центральная частота анализатора спектра.

        Args:
            dim: Единица измерения частоты (Dimension.Hz/Dimension.kHz и т. д.)

        Returns:
            Частота в указанных единицах измерения
        """
        freq_Hz = float(self._resource.query(':SENS:FREQ:CENT?'))
        return freq_Hz / (10 ** dim)

    def set_cf(self, freq: float, dim: Dim = Dim.Hz):
        """Установить центральную частоту анализатора спектра.

        Args:
            freq: Значение частоты
            dim: Единица измерения частоты
        """
        freq_Hz = freq * (10 ** dim)
        self._resource.write(f':SENS:FREQ:CENT {freq_Hz}')

    def get_start_freq_span(self, dim: Dim = Dim.Hz) -> float:
        """
        Стартовая частота в ширине обзора
        Args:
            dim: в какой размерности вернуть значение
        """
        freq_start = float(self._resource.query(':FREQ:STAR?'))
        return freq_start / (10 ** dim)

    def get_stop_freq_span(self, dim: Dim = Dim.Hz) -> float:
        """
        Стартовая частота в ширине обзора
        Args:
            dim: в какой размерности вернуть значение
        """
        freq_start = float(self._resource.query(':FREQ:STOP?'))
        return freq_start / (10 ** dim)

    def get_trace_data_freq(
        self, num_trace: int, dim: Dim = Dim.Hz
    ) -> list[float]:
        """
        Получить значение частот трассы в каждой её точке
        Args:
            num_trace: номер требуемой трассы
            dim: размерность в получившемся частот в возвращаемом массиве
        """
        freq_list = self._resource.query(
            f'TRAC:DATA:X? TRACE{num_trace}'
        ).split(',')
        freq_list = [float(f) for f in freq_list]
        freq_all = [f/(10 ** dim) for f in freq_list]
        return freq_all

    def get_span(self, dim: Dim = Dim.Hz) -> float:
        """
        Значение установленной ширины обзора (span)
        в заданных единицах измерений.
        Args:
            dim: единицы измерений span
        """
        span = float(self._resource.query(':FREQ:SPAN?'))
        return span / (10 ** dim)

    def set_span(self, span: float, dim: Dim = Dim.Hz):
        """
        Установить ширину обзора анализатора.
        Args:
            span: ширина полосы обзора
            dim: размерность введенноё ширины обзора (по умолчанию - Гц)
        """
        span = span * (10 ** dim)
        self._resource.write(f':FREQ:SPAN {span}')

    def span_down(self):
        """Уменьшение SPAN'a "стрелочкой"."""
        self._resource.write(':FREQ:SPAN DOWN')

    def span_up(self):
        """Увеличесние SPAN'a "стрелочкой"."""
        self._resource.write(':FREQ:SPAN UP')

    def imm_emit(self) -> bool:
        """Пнуть обновления измерений"""
        return self._resource.query(':INIT;*OPC?') == '1'

    def set_type_filter_rbw(self, type: str):
        """Установить тип фильтр RBW."""
        val_set = {
            'Normal (3dB)': 'NORM',
            'CISPR (6dB)': 'PULS',
            'Cannel': 'CFIL',
            'RRC': 'RRC',
            '5-Pole': 'P5',
            'MIL (6dB)': 'MIL',
        }
        if type not in val_set:
            print(f'Неверный параметр. Допустимые значения: {val_set.keys()}')
            return
        self._resource.write(f':SENS:BAND:RES:TYPE {val_set[type]}')

    def get_type_filter_rbw(self) -> str | None:
        """Установить тип фильтр RBW."""
        val_set = {
            'NORM': 'Normal (3dB)',
            'PULS': 'CISPR (6dB)',
            'CFIL': 'Cannel',
            'RRC': 'RRC',
            'P5': '5-Pole',
            'MIL': 'MIL (6dB)',
        }
        val = self._resource.query(':SENS:BAND:RES:TYPE?')
        if val in val_set:
            return val_set[val]
        return None

    def get_step_freq(self, dim: Dim = Dim.Hz):
        """
        Узнать шаг по частоте
        Args:
            dim: размерность шага
        """
        if self._resource.query(
            ':SENSe:FREQ:CENT:STEP:LINK?;*OPC?'
        ).split(';')[0] == 'SPAN':
            span = self.get_span()
            factor = self._resource.query(':SENS:FREQ:CENT:STEP:LINK:FACT?')
            step = span * float(factor) / 100
            return step / (10 ** dim)
        step = int(self._resource.query(':FREQ:CENT:STEP?'))
        return step / (10 ** dim)

    def search_peak(self):
        """Установить маркер на максимальный пик"""
        self.active_mrk().search_peak()

    def mrk_next_peak(self):
        """Установить маркер на следующий максимальный пик"""
        self.active_mrk().search_next_peak()

    def mrk_mrk_to_cf(self):
        """Переместить частоту маркера на центр спана"""
        self.active_mrk().freq_mrt_to_center()

    def mrk_off(self):
        """Отключить активный маркер"""
        self.active_mrk().off()

    def set_step_freq(self, step: float, dim: Dim = Dim.Hz):
        """
        Установить шаг по частоте
        Args:
            step: значение шага по частоте
            dim: размерность указанного шага
        """
        step = step * (10 ** dim)
        self._resource.write(f':FREQ:CENT:STEP {step}')

    def get_trace_data_lvl(self, num_trace: int) -> list[float]:
        """
        Получить значение амплитуд трассы в каждой её точке
        Args:
            num_trace: номер требуемой трассы
        """
        signals_all = self._resource.query(
            f':TRAC:DATA? TRACE{num_trace}'
        ).split(',')
        signals_all = [float(signals_all[i]) for i in range(len(signals_all))]
        return signals_all

    def cf_step(self, vector: bool):
        """Уменьшение/увеличение частоты "стрелочкой"."""
        if vector:
            self._resource.write(':SENS:FREQ:CENT UP')
        else:
            self._resource.write(':SENS:FREQ:CENT DOWN')

    def rbw_down(self):
        """Уменьшение RBW "стрелочкой"."""
        self._resource.write(':SENS:BAND:RES DOWN')

    def rbw_up(self):
        """Увеличение RBW "стрелочкой"."""
        self._resource.write(':SENS:BAND:RES UP')

    def vbw_up(self):
        """Увеличение VBW "стрелочкой"."""
        self._resource.write(':BAND:VID UP')

    def vbw_down(self):
        """Уменьшение VBW "стрелочкой"."""
        self._resource.write(':BAND:VID DOWN')

    def rbw_auto(self):
        """Поставить "Авто" для rbw"""
        self._resource.write(':SENS:BAND:RES:AUTO ON')

    def make_fast_screen(self):
        """Сделать быстрый скриншот."""
        self._resource.write('HCOP:DEV:LANG BMP')
        self._resource.write("HCOP:DEST 'MMEM'")
        self._resource.write("MMEM:NAME 'Z:\\Print.bmp'")
        self._resource.write('HCOP:NEXT')

    def make_screen(self, name: str):
        """Сделать скриншот"""
        self._resource.write('HCOP:DEV:LANG BMP')
        self._resource.write("HCOP:DEST 'MMEM'")
        self._resource.write(f"MMEM:NAME '{name}'")
        self._resource.write('HCOP')

    def set_activate_trace(self, num_trace: int):
        """Выбор трассы.
        Args:
            num_trace: номер трассы (от 1 до 6)
        """
        if 1 <= num_trace <= 6:
            self._resource.write(f'DISP:TRAC{num_trace} ON')
            return
        QMessageBox.warning(
            None,
            'Ошибка',
            f'Трассы под номером {num_trace} не существует\n'
            'возможные варианты трасс: от 1 до 6'
        )

    def set_unit_detector(self, det: str, num_trace: int = None):
        """
        Установить тип детектора анализатора для трассы
        Args:
            det: тип детектора при измерении, например: AVER или MAX
        """
        if num_trace is None:
            num_trace = self.active_trace_num
        if det in ['APE', 'NEG', 'POS', 'SAMP', 'RMS', 'AVER', 'QPE']:
            self._resource.write(f'DET{num_trace} {det}')

    def set_type_trace(self, trace_type: str, num_trace: int = None):
        """
        Установить "накопление" трассы.
        Args:
            trace_type: типа накопления трассы AVER/MAX/MIN/WRIT
            num_trace: номер трассы (по умолчанию - активная трасса)
        """
        if num_trace is None:
            num_trace = self.active_trace_num
        if trace_type in ['WRIT', 'VIEW', 'AVER', 'MAXH', 'MINH', 'BLAN']:
            self._resource.write(f'DISP:TRAC{num_trace}:MODE {trace_type}')

    def set_trace_update(self, state: bool, num_trace: int = None):
        """
        Поставить галочку 'Обновлять' для трассы.
        Args:
            num_trace: номер трассы (по умолчанию - активная трасса)
        """
        if num_trace is None:
            num_trace = self.active_trace_num
        if state:
            self._resource.write(f'DISP:TRAC{num_trace}:STAT ON')
        else:
            self._resource.write(f'DISP:TRAC{num_trace}:MODE VIEW')

    def close(self):
        """Закрыть соединение с анализатором."""
        self._resource.close()

    def __enter__(self):
        """Поддержка контекстного менеджера (with statement)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из контекста."""
        self.close()

    def get_unit_ampl(self) -> str:
        """Получить единицы измерений по оси Y (Амплитуды сигналов)."""
        return self._resource.query('CALC:UNIT:POW?')

    def on_corr_tran(self) -> bool:
        """Узнать используются ли калибровочные поправки в амплитуде."""
        tran_sel = self._resource.query(':SENS:CORR:TRAN:SEL?')
        if tran_sel == "''":
            return False
        else:
            return self._resource.query(':SENS:CORR:TRAN:STAT?') == '1'

    def set_corr_tran(self, trans: str | None):
        """Установить калибровочную поправку амплитуд."""
        self._resource.write(':SENS:CORR:TRAN:STAT OFF')
        self._resource.write(":SENS:CORR:TRAN:SEL ''")
        if trans is None or trans == "''":
            return
        ant_name_fsva = {v: k for k, v in ANT_NAMES.items()}
        self._resource.write(f":SENS:CORR:TRAN:SEL {ant_name_fsva[trans]}")
        self._resource.write(':SENS:CORR:TRAN:STAT ON')

    def get_name_corr_tran(self) -> str:
        """Получить название калибровочной таблицы."""
        ant_name_fsva = self._resource.query(':SENS:CORR:TRAN:SEL?')
        if ant_name_fsva not in ANT_NAMES:
            self.set_corr_tran(trans=None)
            ant_name_fsva = "''"
        return ANT_NAMES[ant_name_fsva]

    def get_mrk_x(self, dim: Dim = Dim.Hz, mrk_num: int = 0) -> float:
        """Значение частоты активного маркера

        Args:
            dim: Единица измерения ширины канала
            mrk_num: номер маркера, по умолчанию - активный маркер
        """
        if mrk_num == 0:
            mrk_num = self.active_trace_num
        freq_mrk = float(self._resource.query(f'CALC:MARK{mrk_num}:X?'))
        return freq_mrk / (10 ** dim)

    def get_mrk_y(self, mrk_num: int = 0) -> float:
        """Значение уровня активного маркера

        Args:
            mrk_num: номер маркера, по умолчанию - активный маркер
        """
        if mrk_num == 0:
            mrk_num = self.active_trace_num
        lvl_mrk = float(self._resource.query(f'CALC:MARK{mrk_num}:Y?'))
        return round(float(lvl_mrk), 2)

    def active_mrk(self) -> Marker:
        """Получить экземпляр активного маркера."""
        return self._markers[f'Marker {self.act_mrk}']

    def active_trc(self) -> Trace:
        """Получить экземпляр активной трассы."""
        return self._traces[f'Trace {self.active_trace_num}']

    def get_reflvl(self) -> str:
        """Получить опорный уровень"""
        return str(self._resource.query(':DISP:WIND:TRAC:Y:SCAL:RLEV?'))

    def set_reflvl(self, reflvl):
        """Устанвоить опорный уровень"""
        reflvl = int(reflvl)
        self._resource.write(f':DISP:WIND:TRAC:Y:SCAL:RLEV {reflvl}')

    def set_reflvl_up(self, vector: bool = True):
        """Увеличение/уменьшение RefLvl стрелочками"""
        if vector:
            self._resource.write(':DISP:WIND:TRAC:Y:SCAL:RLEV UP')
        else:
            self._resource.write(':DISP:WIND:TRAC:Y:SCAL:RLEV DOWN')

    def get_ref_range(self) -> int:
        """Получить значение текущего динамического диапазона"""
        ref_range = self._resource.query(':DISP:WIND1:SUBW:TRAC:Y:SCAL?')
        return int(float(ref_range))

    def set_ref_range(self, ref_range: int):
        """Задать значение динамического диапазона анализатора"""
        try:
            self._resource.write(f':DISP:WIND1:SUBW:TRAC:Y:SCAL {ref_range}')
        except Exception as e:
            QMessageBox.critical(
                self, 'Ошибка',
                f'Не удалось установить уровень {ref_range}: {e}')

    def ref_range_up(self, vector: bool):
        """Изменение динамического диапазонами вверх/внихз срелочками"""
        dir = 'UP' if vector else 'DOWN'
        self._resource.write(f':DISP:WIND1:SUBW:TRAC:Y:SCAL {dir}')

    def get_atten(self) -> int:
        """Получить значение текущего аттенюатора"""
        atten = self._resource.query(':INP:ATT?')
        return int(float(atten))

    def atten_auto_on(self):
        """Нажатие кнопки RF Atten Auto"""
        self._resource.write(':INP:ATT:AUTO ON')

    def atten_up(self, vector: bool):
        """Изменение аттенюатора вверх/внихз срелочками"""
        dir = 'UP' if vector else 'DOWN'
        self._resource.write(f':INP:ATT {dir}')

    def get_preamp(self) -> str:
        """Получить значение предусилителя"""
        preamp_on = self._resource.query(':INP:GAIN:STAT?') == '1'
        if preamp_on:
            preamp_val = self._resource.query(':INP:GAIN?')
            return f'{preamp_val} dB'
        return 'Off'

    def get_amp_unit(self) -> str:
        """Получить значение размерности амплитуды"""
        amp_unit_val = self._resource.query(':CALC:UNIT:POW?')
        val_set = {
            'DBM': 'dBm',
            'DBUV': 'dBµV',
            'DBMV': 'dBmV',
            'V': 'V',
            'W': 'W',
            'DBVP': 'dBV',
            'DBUV_HZ': 'dBµV/Hz',
            'DBMV_HZ': 'dBmV/Hz',
            'DBUV/M': 'dBµV/m',
        }
        return val_set[amp_unit_val]

    def set_preamp(self, val: str):
        """Установить значение предусилителя"""
        if val == 'Off':
            self._resource.write(':INP:GAIN:STAT OFF')
            return
        self._resource.write(f':INP:GAIN:VAL {val[:2]}')
        self._resource.write(':INP:GAIN:STAT ON')

    def set_amp_unit(self, val: str):
        """Установить размерность по оси амплитуд"""
        val_set = {
            'dBm': 'DBM',
            'dBµV': 'DBUV',
            'dBmV': 'DBMV',
            'V': 'V',
            'W': 'W',
            'dBV': 'DBVP',
            'dBµV/Hz': 'DBUV_HZ',
            'dBmV/Hz': 'DBMV_HZ',
            'dBmV/m': 'DBUV/M',
        }
        if val not in val_set:
            return
        self._resource.write(f':CALC:UNIT:POW {val_set[val]}')

    def set_auto_scale(self):
        """Установить автомасштаб"""
        self._resource.write(':DISP:WIND1:SUBW:TRAC:Y:SCAL:AUTO ONCE')


class Marker:
    def __init__(
            self,
            num: int,
            analyzer: RS_FSVA3013,
            trace: int = 1
    ):
        """
        Args:
            num: номер маркера (1–9)
            analyzer: ссылка на экземпляр анализатора
            trace: номер трассы, к которой привязан маркер
        """
        if not (1 <= num <= 9):
            raise ValueError("Номер маркера должен быть от 1 до 9")
        self._analyzer = analyzer
        self.num = num
        self.trace = trace

    def set_freq(self, freq: float, dim: Dim = Dim.Hz):
        """Установить частоту маркера.

        Args:
            freq: частота в Гц
            dim: размерность указанной частоты
        """
        freq_hz = freq * (10 ** dim)
        self._analyzer._resource.write(f'CALC:MARK{self.num}:X {freq_hz}')

    def get_freq(self, dim: Dim = Dim.Hz) -> float:
        """Получить частоту маркера в заданных единицах.

        Args:
            dim: единица измерения частоты

        Returns:
            Частота маркера в указанных единицах
        """
        freq_hz = float(
            self._analyzer._resource.query(f':CALC:MARK{self.num}:X?')
        )
        return freq_hz / (10 ** dim)

    def get_lvl(self, val_round=None) -> float:
        """Получить амплитуду маркера.
        Returns:
            Частота маркера в текущих единицах измерений
        """
        lvl = float(
            self._analyzer._resource.query(f':CALC:MARK{self.num}:Y?')
        )
        if val_round is not None:
            lvl = round(lvl, val_round)
        return lvl

    def set_delta(self, state: bool):
        """
        Установить типа маркера Delta
        Args:
            state:
                - True: Активирован режим маркера 'Delta'
                - False: Декктивирован режим маркера 'Delta'
        """
        if state:
            self._analyzer._resource.write(f':CALC:DELT{self.num} ON')
        else:
            self._analyzer._resource.write(f':CALC:DELT{self.num} OFF')
            self._analyzer._resource.write(f':CALC:MARK{self.num} ON')

    def search_peak(self):
        """Найти ближайший пик для этого маркера."""
        self._analyzer._resource.write(f':CALC:MARK{self.num}:MAX:PEAK')

    def search_next_peak(self):
        """Найти ближайший пик для этого маркера."""
        self._analyzer._resource.write(f':CALC:MARK{self.num}:MAX:NEXT')

    def search_maxpeak_freq(self, dim: Dim = Dim.Hz) -> float:
        """Найти ближайший пик для этого маркера."""
        self._analyzer._resource.write(f':CALC:MARK{self.num}:MAX:PEAK')
        return self.get_freq(dim=dim)

    def search_maxpeak_lvl(self) -> float:
        """Найти максимальный уровень."""
        self._analyzer._resource.write(f':CALC:MARK{self.num}:MAX:PEAK')
        lvl = self.get_lvl()
        return lvl

    def off(self):
        """Отключить маркер."""
        self._analyzer._resource.write(f'CALC:MARK{self.num} OFF')

    def on(self):
        """Включить маркер."""
        self._analyzer._resource.write(f'CALC:MARK{self.num} ON')

    def get_trace_num(self):
        """получить номер трассы, на которой стоит маркер"""
        return self._analyzer._resource.query(
            f':CALC1:MARK{self.num}:TRAC?'
        )

    def to_trace(self, num_trace: int):
        """Установить маркер на трассу."""
        self._analyzer._resource.write(
            f':CALC:MARK{self.num}:TRAC {num_trace}'
        )

    def freq_mrt_to_center(self):
        """Установить частоту маркер на центр."""
        self._analyzer._resource.write(f':CALC:MARK{self.num}:FUNC:CENT')

    def peak_track(self, mode: int):
        """Включить/выключить автослежение за максимумом."""
        if mode == 2:
            self._analyzer._resource.write(f':CALC:MARK{self.num}:MAX:AUTO ON')
        else:
            self._analyzer._resource.write(
                f':CALC:MARK{self.num}:MAX:AUTO OFF'
            )

    def is_auto_peak_on(self) -> Qt.CheckState:
        state = self._analyzer._resource.query(
            f':CALC:MARK{self.num}:MAX:AUTO?'
        )
        if state == '1':
            return Qt.CheckState.Checked
        return Qt.CheckState.Unchecked


class Trace:
    def __init__(
        self,
        num: int,
        analyzer: RS_FSVA3013,
    ):
        """
        Args:
            num: номер маркера (1–9)
            analyzer: ссылка на экземпляр анализатора
            trace: номер трассы, к которой привязан маркер
        """
        if not (1 <= num <= 4):
            raise ValueError("Номер маркера должен быть от 1 до 4")
        self._analyzer = analyzer
        self.num = num

    def set_accumulation(self, type_acc):
        """Установить тип накопления для трассы"""
        if type_acc in ['WRIT', 'VIEW', 'AVER', 'MAXH', 'MINH', 'BLAN']:
            self._analyzer._resource.write(
                f'DISP:TRAC{self.num}:MODE {type_acc}'
            )
        else:
            raise ValueError(
                "Возможное накопление трассы только:\n"
                "WRIT/VIEW/AVER/MAXH/MINH/BLAN"
            )

    def off(self, type_acc):
        """отключить трассу"""
        self.set_accumulation('BLAN')

    def freeze(self):
        """Остановить обновление трассы"""
        self.set_accumulation('VIEW')

    def set_detector(self, type_det):
        """Установить тип детектора трассы"""
        if type_det in [
            'APE', 'POS', 'NEG',
            'RMS', 'AVER', 'VIEW',
            'SAMP', 'QPE', 'CRMS', 'CAV',
        ]:
            self._analyzer._resource.write(f'DET{self.num} {type_det}')
        else:
            raise ValueError(
                "Возможное накопление трассы только:\n"
                "APE/POS/NEG/RMS/VIEW/AVER/SAMP/QPE/CRMS/CAV/"
            )

    def get_trace_acc_type(self) -> str:
        return self._analyzer._resource.query(f'DISP:TRAC{self.num}:MODE?')

    def get_trace_det_type(self) -> str:
        return self._analyzer._resource.query(f'DET{self.num}?')
