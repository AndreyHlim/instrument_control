from instruments.scheme_signals.connect import callbacks_map_conn
from instruments.scheme_signals.fsva import callbacks_map_fsva


class SignalsMixin:
    """Миксин: подключение сигналов всех секций формы.

    Предполагается, что секции уже созданы (set_layout_left), а ссылки
    на виджеты инициализированы (initialization_form_elements_*).
    """

    def signal_connection(self) -> None:
        """Подключить сигналы секций к картам обработчиков.

        Содержимое подключений живёт в instruments/scheme_signals:
        каждый контрол секции знает свой обработчик, этот метод только
        раздаёт карты по секциям.
        """
        for section, ctrl in (
            (self.sec_instr, 'connect'),
            (self.sec_ampl, 'amp'),
            (self.sec_freq, 'freq'),
            (self.sec_rbw, 'rbw'),
            (self.sec_sweep, 'sweep'),
        ):
            map_ = (callbacks_map_conn(self) if ctrl == 'connect'
                    else callbacks_map_fsva(self, ctrl))
            section.connect_callbacks(map_)
