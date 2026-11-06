"""
Управление генератором низкочастотных сигналов Agilent 33220A.
Связь по LAN (VISA socket).
"""

from enum import Enum

import pyvisa


class Dim(str, Enum):
    """Размерности частоты и амплитуды для SCPI-команд."""
    # Частота
    HZ = "HZ"
    KHZ = "KHZ"
    MHZ = "MHZ"
    # Амплитуда
    VPP = "VPP"
    VRMS = "VRMS"
    DBM = "DBM"


class Agilent33220A:
    """Класс для управления генератором Agilent 33220A по LAN."""

    def __init__(self, ip: str, port: int = 5025):
        """
        Подключиться к генератору по IP-адресу.

        Args:
            ip: IP-адрес генератора (например, "192.168.1.100").
            port: Порт VISA socket (по умолчанию 5025).
        """
        rm = pyvisa.ResourceManager()
        resource_str = f"TCPIP::{ip}::{port}::SOCKET"
        try:
            self._resource = rm.open_resource(resource_str)
            self._resource.read_termination = "\n"
            self._resource.write_termination = "\n"
            self._resource.timeout = 5000
            # Проверяем, что это действительно Agilent 33220A
            idn = self._resource.query("*IDN?")
            if "33220A" not in idn:
                raise ValueError(
                    "Подключённое устройство "
                    f"не является Agilent 33220A: {idn}"
                )
        except Exception as e:
            raise ConnectionError(f"Не удалось подключиться к генератору: {e}")

    # ------------------------------------------------------------------
    #  Идентификация и сброс
    # ------------------------------------------------------------------

    def get_idn(self) -> str:
        """Получить строку идентификации прибора."""
        return self._resource.query("*IDN?")

    def reset(self):
        """Сбросить прибор к заводским настройкам."""
        self._resource.write("*RST")

    def clear_status(self):
        """Очистить очередь ошибок и статус."""
        self._resource.write("*CLS")

    def get_error(self) -> str:
        """Прочитать последнюю ошибку из очереди."""
        return self._resource.query("SYST:ERR?")

    # ------------------------------------------------------------------
    #  Форма сигнала
    # ------------------------------------------------------------------

    # Маппинг: человекочитаемое имя (для combo) -> SCPI-код
    # --- Маппинг форм сигнала: человекочитаемое → SCPI-код ---
    WAVEFORM_MAP = {
        'SINusoid': 'SIN',
        'SQUare': 'SQU',
        'RAMP': 'RAMP',
        'NRAMp': 'NRAMP',
        'TRIangle': 'TRI',
        'NOISe': 'NOISE',
    }
    WAVEFORM_MAP_REV = {v: k for k, v in WAVEFORM_MAP.items()}

    def set_function(self, waveform_name: str):
        """Установить форму сигнала по человекочитаемому имени из combo."""
        code = self.WAVEFORM_MAP.get(waveform_name)
        if not code:
            raise ValueError(f"Неизвестная форма сигнала: {waveform_name}")
        self._resource.write(f"SOUR:FUNC {code}")

    def set_function_by_name(self, name: str):
        """
        Установить форму сигнала по человекочитаемому имени.

        Args:
            name: "Sine", "Square", "Ramp", "Pulse", "Noise", "DC", "User".
        """
        code = self.WAVEFORM_MAP.get(name)
        if code is None:
            raise ValueError(f"Неизвестная форма сигнала: {name}")
        self.set_function(code)

    def get_function(self) -> str:
        """Получить текущую форму сигнала (возвращает человекочитаемое имя)."""
        code = self._resource.query("SOUR:FUNC?").strip()
        # Ищем ключ по значению (обратный поиск)
        for name, c in self.WAVEFORM_MAP.items():
            if c == code:
                return name
        return code  # если вдруг прибор вернёт что-то неожиданное

    def get_function_name(self) -> str:
        """Получить текущую форму сигнала (человекочитаемое имя)."""
        code = self.get_function()
        return self.WAVEFORM_MAP_REV.get(code, code)

    # ------------------------------------------------------------------
    #  Частота
    # ------------------------------------------------------------------

    def set_frequency(self, freq_hz: float):
        """Установить частоту генератора (всегда в Гц)."""
        if not (1e-6 <= freq_hz <= 20e6):
            raise ValueError(
                f"Частота вне диапазона 1 мкГц…20 МГц: {freq_hz} Гц")
        self._resource.write(f"SOUR:FREQ {freq_hz}")

    def get_frequency(self) -> float:
        """Получить текущую частоту в Гц."""
        resp = self._resource.query("SOUR:FREQ?")
        return float(resp)

    # ------------------------------------------------------------------
    #  Амплитуда
    # ------------------------------------------------------------------

    def set_amplitude(self, amplitude_vpp: float):
        """Установить амплитуду в вольтах пик-пик (Vpp)."""
        # Диапазон 33220A: до 10 Впп на 50 Ом, до 20 Впп в высоком импедансе
        if not (0.0 <= amplitude_vpp <= 20.0):
            raise ValueError(
                f"Амплитуда вне диапазона 0…20 В: {amplitude_vpp} В")
        self._resource.write(f"SOUR:VOLT {amplitude_vpp}")

    def get_amplitude(self) -> float:
        """Получить амплитуду в вольтах пик-пик (Vpp)."""
        resp = self._resource.query("SOUR:VOLT?")
        return float(resp)

    def set_voltage_unit(self, unit: Dim):
        """
        Установить единицы измерения амплитуды.

        Args:
            unit: Dim.VPP, Dim.VRMS или Dim.DBM.
        """
        self._resource.write(f"VOLT:UNIT {unit.value}")

    # ------------------------------------------------------------------
    #  Смещение (Offset)
    # ------------------------------------------------------------------

    def set_offset(self, offset: float):
        """
        Установить постоянное смещение (DC offset) в вольтах.

        Args:
            offset: напряжение смещения в В.
        """
        self._resource.write(f"VOLT:OFFS {offset}")

    def get_offset(self) -> float:
        """Получить текущее смещение в вольтах."""
        return float(self._resource.query("VOLT:OFFS?"))

    # ------------------------------------------------------------------
    #  Выход (вкл / выкл)
    # ------------------------------------------------------------------

    def output_on(self):
        self._resource.write("OUTP ON")

    def output_off(self):
        self._resource.write("OUTP OFF")

    def set_output(self, state: bool):
        """
        Включить или выключить выход.

        Args:
            state: True — включить, False — выключить.
        """
        self._resource.write(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        """Узнать, включён ли выход (1 = ON, 0 = OFF)."""
        resp = self._resource.query("OUTP?")
        return resp.strip() == "1"

    # ------------------------------------------------------------------
    #  Нагрузка
    # ------------------------------------------------------------------

    def set_load(self, load: float | str):
        """
        Установить сопротивление нагрузки.

        Args:
            load: сопротивление в омах (число)
            или "INF" для высокого импеданса.
        """
        if isinstance(load, str) and load.upper() in ("INF", "INFINITY"):
            self._resource.write("OUTP:LOAD INF")
        else:
            self._resource.write(f"OUTP:LOAD {load}")

    def get_load(self) -> str:
        """
        Получить текущее сопротивление нагрузки
        ('INF' или значение в омах).
        """
        return self._resource.query("OUTP:LOAD?").strip()

    # ------------------------------------------------------------------
    #  Прямой доступ к ресурсу
    # ------------------------------------------------------------------

    @property
    def resource(self):
        """Доступ к VISA-ресурсу для нестандартных команд."""
        return self._resource

    def write(self, cmd: str):
        """Отправить произвольную SCPI-команду."""
        self._resource.write(cmd)

    def query(self, cmd: str) -> str:
        """Отправить произвольный SCPI-запрос и получить ответ."""
        return self._resource.query(cmd)

    # ------------------------------------------------------------------
    #  Закрытие
    # ------------------------------------------------------------------

    def close(self):
        """Закрыть соединение с генератором."""
        try:
            self._resource.close()
        except Exception:
            pass
