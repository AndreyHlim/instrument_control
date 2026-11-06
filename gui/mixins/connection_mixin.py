from PyQt6.QtCore import QThread, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox

from instruments.fsva import RS_FSVA3013
from worker import TraceWorker


class ConnectionMixin:
    """Миксин: подключение/отключение анализатора и поток трассы.

    Предполагается, что у окна есть:
    - self.tb_ip_analyzer, self.but_analyzer_conn (ControlsMixin);
    - self.check_auto_max (ControlsMixin);
    - self._set_analyzer_controls_enabled (ControlsMixin);
    - self.update_state (PlotMixin).
    """

    _analyzer: 'RS_FSVA3013 | None'
    _trace_worker: 'TraceWorker | None'

    def preparation_variables(self) -> None:
        """Создать переменные состояния подключения с значениями по умолчанию.

        Вызывается один раз в __init__ до всех методов, использующих
        self._analyzer / self._trace_worker / self._trace_thread.
        """
        self._analyzer = None
        self._trace_worker = None
        self._trace_thread = None

    def on_analyzer_connect(self) -> None:
        """Обработчик кнопки подключения.

        Работает как переключатель:
        - если прибор не подключён — создаёт RS_FSVA3013 по IP из поля
          ввода и запускает поток чтения трассы;
        - если подключён — останавливает поток, закрывает прибор и
          возвращает элементы управления в заблокированное состояние.

        Raises:
            ConnectionError: прибор недоступен по сети (перехватывается,
                состояние подключения не меняется).
            ValueError: некорректный IP-адрес (перехватывается).
        """
        ip = self.tb_ip_analyzer.text().strip()
        if not ip:
            return

        # Если уже подключены — отключаемся
        if self._analyzer is not None:
            self._stop_trace_thread()
            try:
                self._analyzer.close()
            except Exception as e:
                print(f"[ANALYZER] Ошибка закрытия: {e}")
            finally:
                self._analyzer = None
            self._set_analyzer_conn_state(False)
            return

        try:
            self._analyzer = RS_FSVA3013(ip)
        except (ConnectionError, ValueError) as e:
            print(f"[ANALYZER] Не удалось подключиться: {e}")
            return

        self._start_trace_thread()
        self._set_analyzer_conn_state(True)

        # Автослежение за максимумом
        if not self.check_auto_max.isChecked():
            self.check_auto_max.setChecked(True)
        else:
            self._trace_worker.send_command('auto_max_on')

    def _start_trace_thread(self) -> None:
        """Запустить рабочий поток чтения трассы.

        Создаёт QThread и TraceWorker, переносит воркер в поток,
        подключает его сигналы state_ready и error_occurred к окну
        и стартует выполнение.

        Note:
            Вызывать после успешного создания self._analyzer.
        """
        self._trace_thread = QThread()
        self._trace_worker = TraceWorker(self._analyzer)
        self._trace_worker.moveToThread(self._trace_thread)
        self._trace_thread.started.connect(self._trace_worker.run)
        self._trace_worker.state_ready.connect(self.update_state)
        self._trace_worker.error_occurred.connect(
            lambda msg: print(f"Ошибка потока трассы: {msg}"))
        self._trace_thread.start()

    def _stop_trace_thread(self) -> None:
        """Корректно остановить рабочий поток чтения трассы.

        Сначала просит воркер завершить цикл (stop), затем останавливает
        очередь событий QThread. Если поток не завершился за 3 секунды —
        принудительный terminate с ожиданием ещё 1 секунды.

        Note:
            После terminate корректное освобождение ресурсов VISA
            не гарантируется — использовать как последний резерв.
        """
        if self._trace_worker is not None:
            self._trace_worker.stop()
        if self._trace_thread is not None:
            self._trace_thread.quit()
            self._trace_thread.wait(3000)
            if self._trace_thread.isRunning():
                print("[CLOSE] Поток не завершился, terminate()")
                self._trace_thread.terminate()
                self._trace_thread.wait(1000)

    def _set_analyzer_conn_state(self, connected: bool) -> None:
        """Обновить UI по факту подключения.

        Args:
            connected: True — прибор подключён (кнопка становится
                «Отключиться», элементы управления разблокируются,
                поле IP блокируется); False — обратное состояние.
        """
        if connected:
            self.but_analyzer_conn.setText(" Отключиться ")
            self._set_analyzer_controls_enabled(True)
            self.tb_ip_analyzer.setEnabled(False)
        else:
            self.but_analyzer_conn.setText("Подключиться")
            self._set_analyzer_controls_enabled(False)
            self.tb_ip_analyzer.setEnabled(True)

    def open_analyzer_web(self, ip: str | None = None) -> None:
        """Открыть Web-интерфейс прибора в браузере по умолчанию.

        Args:
            ip: IP-адрес прибора. Если не задан, берётся из поля
                tb_ip_analyzer и открывается страница web-control
                анализатора; если задан — корень сайта прибора.

        Note:
            При пустом IP (и ip=None) показывает предупреждение
            и ничего не открывает.
        """
        if ip is None:
            ip_address = self.tb_ip_analyzer.text().strip()
            url_string = f"http://{ip_address}/device-web/#/lxi/web-control"
        else:
            ip_address = ip
            url_string = f"http://{ip_address}/"

        if not ip_address:
            QMessageBox.critical(
                self, 'Ошибка параметра',
                'Неправильно задан IP-адрес прибора'
            )
            return

        QDesktopServices.openUrl(QUrl(url_string))
