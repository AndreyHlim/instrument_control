import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer

from dataclass import DeviceState


class PlotMixin:
    """Миксин: настройка графика и его обновление.

    Предполагается, что у окна есть:
    - self.plotWidget (PlotWidget из .ui-файла);
    - self._trace_worker (создаётся ConnectionMixin);
    - self._apply_state_params (метод StateMixin — вызывается в конце
      update_state, связность через множественное наследование).
    """

    def settings_plot(self) -> None:
        """Настроить график и создать вспомогательные элементы.

        Делает однократную инициализацию: пустая кривая трассы, пулы
        линий сетки (20 горизонтальных, 9 вертикальных), текстовые
        метки CF/Span/цена деления, оси, фиксация диапазонов и
        дебаунс-таймер для ручного изменения диапазона X мышкой.

        Note:
            Повторный вызов безопасен: перед созданием удаляются ранее
            созданные кривая и метки (защита от дублей). Пулы линий
            сетки при этом НЕ пересоздаются — позиции задаются позже
            в update_state.
        """
        self.plotWidget.setBackground((255, 255, 255))

        # Защита от дублей при пересоздании
        if hasattr(self, '_curve') and self._curve is not None:
            self.plotWidget.removeItem(self._curve)
        for attr in ('_cf_label', '_span_label', '_perdiv_label'):
            if hasattr(self, attr) and getattr(self, attr) is not None:
                self.plotWidget.removeItem(getattr(self, attr))
        for attr in ('_hgrid_lines', '_vgrid_lines'):
            for line in getattr(self, attr, []):
                self.plotWidget.removeItem(line)
        self._curve = self.plotWidget.plot([], [], pen='b')

        # Цвет и стиль линий сетки
        grid_pen = pg.mkPen(
            color=(120, 120, 120, 80), width=1, style=Qt.PenStyle.SolidLine)
        # --- Горизонтальные линии (пул, позиции задаются в update_state) ---
        self._hgrid_lines = []
        for _ in range(20):
            line = pg.InfiniteLine(angle=0, movable=False, pen=grid_pen)
            line.setVisible(False)
            self.plotWidget.addItem(line)
            self._hgrid_lines.append(line)

        # --- Вертикальные линии (позиции зададим в update_state) ---
        # Линии сетки
        self._vgrid_lines = []
        for i in range(9):
            line = pg.InfiniteLine(angle=90, movable=False, pen=grid_pen)
            self.plotWidget.addItem(line)
            self._vgrid_lines.append(line)

        # --- Текстовые метки CF / Span / цена деления ПОД осью X ---
        self._cf_label = pg.TextItem(text='', color="#000000", anchor=(0, 1))
        self._span_label = pg.TextItem(text='', color="#000000", anchor=(1, 1))
        self._perdiv_label = pg.TextItem(
            text='', color="#000000", anchor=(0.5, 1))

        for label in (self._cf_label, self._span_label, self._perdiv_label):
            self.plotWidget.addItem(label)

        self.plotWidget.setLabel('bottom', 'Частота', units='Hz')
        self.plotWidget.setLabel('left', 'Уровень', units='дБ')

        self.plotWidget.getAxis('left').enableAutoSIPrefix(False)

        # Оси сверху/справа для отступов
        self.plotWidget.setLabel('top', ' ')
        self.plotWidget.setLabel('right', ' ')
        self.plotWidget.getAxis('top').setStyle(showValues=False)
        self.plotWidget.getAxis('top').enableAutoSIPrefix(False)
        self.plotWidget.getAxis('right').setStyle(showValues=False)

        self.plotWidget.setMouseEnabled(x=True, y=False)  # X—мышка, Y—прибор
        self.plotWidget.enableAutoRange(x=False)
        self.plotWidget.getViewBox().setDefaultPadding(0)

        self._current_x_min: float | None = None
        self._current_x_max: float | None = None
        self._current_y_min: float | None = None
        self._current_y_max: float | None = None
        self._current_reflevel: float | None = None
        self._current_range: float | None = None

        # --- Дебаунс для ручного изменения X ---
        self._updating_from_state = False
        self._pending_x_range: tuple[float, float] | None = None
        self._x_debounce = QTimer()
        self._x_debounce.setSingleShot(True)
        self._x_debounce.setInterval(300)  # мс
        self._x_debounce.timeout.connect(self._send_x_range_cmd)

        # Сигнал изменения диапазона
        vb = self.plotWidget.getPlotItem().getViewBox()
        vb.sigRangeChanged.connect(self._on_x_range_changed)
        self.plotWidget.showGrid(x=False, y=True)

    def _on_x_range_changed(self, viewbox, ranges) -> None:
        """Срабатывает при перетаскивании/зуме оси X мышкой.

        Сохраняет новый диапазон в self._pending_x_range и запускает
        дебаунс-таймер (300 мс) для отправки команд set_cf/set_span.
        Параллельно переставляет вертикальные линии сетки и обновляет
        текстовые метки, чтобы график реагировал на лету.

        Args:
            viewbox: источник сигнала (ViewBox, не используется).
            ranges: кортеж ((x_min, x_max), (y_min, y_max)).
        """
        if self._updating_from_state:
            return
        x_range = ranges[0]
        x_min, x_max = x_range[0], x_range[1]
        self._pending_x_range = (x_min, x_max)
        self._x_debounce.start()

        # --- На лету переставляем вертикальные линии ---
        x_span = x_max - x_min
        if x_span > 0:
            x_step = x_span / 10.0
            for i, line in enumerate(self._vgrid_lines):
                if i < 9:
                    line.setPos(x_min + (i + 1) * x_step)
                    line.setVisible(True)
                else:
                    line.setVisible(False)
            self.plotWidget.getAxis('bottom').setTickSpacing(
                major=x_step, minor=x_step)

        self._update_info_labels(x_min, x_max)

    def _update_info_labels(self, x_min, x_max):
        """Обновить метки CF / Span / цена деления под осью X.

        Args:
            x_min: левая граница видимого диапазона, Гц.
            x_max: правая граница видимого диапазона, Гц.

        Note:
            Ничего не делает, пока не известен Y-диапазон
            (self._current_y_min / _current_y_max are None) — метки
            привязываются к нижней границе по Y.
        """
        if self._current_y_min is None or self._current_y_max is None:
            return

        y_pos = self._current_y_min

        center_hz = (x_min + x_max) / 2
        span_hz = x_max - x_min
        per_div_hz = span_hz / 10.0

        self._cf_label.setText(
            f'CF = {self._format_freq(center_hz, force_decimals=6)}')
        self._cf_label.setPos(x_min, y_pos)

        self._span_label.setText(f'Span = ±{self._format_freq(span_hz/2)}')
        self._span_label.setPos(x_max, y_pos)

        self._perdiv_label.setText(f'{self._format_freq(per_div_hz)} /')
        self._perdiv_label.setPos(center_hz, y_pos)

    def _format_freq(
        self, hz: float, force_decimals: int | None = None, dim: str = ''
    ) -> str:
        """Форматировать частоту (в Гц) с автоподбором размерности.

        Args:
            hz: значение в герцах.
            force_decimals: принудительно задать число знаков после
                запятой (например, 6 для center frequency); при заданном
                значении dim игнорируется.
            dim: принудительная размерность ('ГГц'/'МГц'/'кГц'/'Гц');
                значение округляется до целых. Пустая строка — авто.

        Returns:
            Строка вида '123.5 кГц'.
        """
        abs_val = abs(hz)

        # Определяем размерность и базовое значение
        if abs_val >= 1e9:
            value = hz / 1e9
            unit = "ГГц"
        elif abs_val >= 1e6:
            value = hz / 1e6
            unit = "МГц"
        elif abs_val >= 1e3:
            value = hz / 1e3
            unit = "кГц"
        else:
            value = hz
            unit = "Гц"

        # Если нужна принудительная точность — применяем её
        if force_decimals is not None:
            return f"{value:.{force_decimals}f} {unit}"

        if dim in ["ГГц", "МГц", "кГц", "Гц"]:
            if dim == 'МГц':
                return f"{abs_val / 1e6:.0f} {dim}"
            if dim == 'ГГц':
                return f"{abs_val / 1e9:.0f} {dim}"
            if dim == 'кГц':
                return f"{abs_val / 1e3:.0f} {dim}"
            if dim == 'Гц':
                return f"{abs_val:.0f} {dim}"

        # Иначе — адаптивная логика (как раньше)
        if value >= 100:
            return f"{value:.0f} {unit}"
        elif value >= 1:
            return f"{value:.1f} {unit}"
        else:
            # Для маленьких значений (например, 0.5 кГц → 500 Гц)
            return f"{value * 1e3:.0f} Гц"

    def _send_x_range_cmd(self):
        """Отправить новые CF и span на прибор (после дебаунса).

        Преобразует self._pending_x_range в центр и ширину, отправляет
        команды set_cf/set_span в герцах через рабочий поток.

        Note:
            Ничего не делает, если диапазон не был изменён или воркер
            не запущен. Слишком малый span (<= 0) отбрасывается.
        """
        if self._pending_x_range is None or self._trace_worker is None:
            return
        x_min, x_max = self._pending_x_range
        self._pending_x_range = None

        new_center = (x_min + x_max) / 2
        new_span = x_max - x_min
        if new_span <= 0:
            return

        # Отправляем в Гц — прибору так удобнее
        self._trace_worker.send_command(f'set_cf:{new_center}')
        self._trace_worker.send_command(f'set_span:{new_span}')

    def update_state(self, state: DeviceState):
        """Применить снимок состояния прибора к графику и контролам.

        Порядок обработки:
        1. Данные трассы: обновление кривой; при изменении границ X —
           перестановка вертикальных линий сетки и шага оси X.
        2. Reflevel / Range: кэширование непустых значений; при изменении
           Y-диапазона — перестановка горизонтальных линий (шаг 10 дБ),
           обновление оси Y и текстовых меток.
        3. Параметры: делегирование в _apply_state_params (StateMixin).

        Args:
            state: снимок состояния из TraceWorker.state_ready. Поля со
                значением None не опрашивались в этом кадре и пропускаются.
        """
        # График
        self._curve.setData(state.freqs, state.levels)
        if state.freqs:
            x_min = state.freqs[0]
            x_max = state.freqs[-1]

            if x_min != self._current_x_min or x_max != self._current_x_max:
                self._current_x_min = x_min
                self._current_x_max = x_max

                # Гарантированно глушим встроенную сетку —
                # pyqtgraph может включать её при setRange
                self.plotWidget.showGrid(x=False, y=False)

                vb = self.plotWidget.getPlotItem().getViewBox()
                self._updating_from_state = True
                vb.setRange(xRange=(x_min, x_max), padding=0)
                self._updating_from_state = False

                x_span = x_max - x_min
                if x_span > 0:
                    x_step = x_span / 10.0
                else:
                    x_step = 1e6

                # Двигаем вертикальные линии (ровно 9 линий для 10 клеток)
                for i, line in enumerate(self._vgrid_lines):
                    line.setPos(x_min + (i + 1) * x_step)

                # --- Подписи по Y: строго каждые 10 дБ ---
                axis_left = self.plotWidget.getAxis('left')
                axis_bottom = self.plotWidget.getAxis('bottom')

                # Для Y фиксируем шаг 10 (major=10, minor=10)
                axis_left.setTickSpacing(major=10, minor=10)

                # Для X оставляем «10 делений» по диапазону
                axis_bottom.setTickSpacing(major=x_step, minor=x_step)

        # --- Храним последние значения reflevel и range ---
        if state.reflevel is not None:
            self._current_reflevel = state.reflevel
        if state.range_val is not None:
            self._current_range = state.range_val

        # --- Обновление Y-диапазона и горизонтальных линий ---
        if (
            self._current_reflevel is not None
            and self._current_range is not None
        ):
            y_max = self._current_reflevel
            y_min = self._current_reflevel - self._current_range

            if y_min != self._current_y_min or y_max != self._current_y_max:
                self._current_y_min = y_min
                self._current_y_max = y_max

                self.plotWidget.showGrid(x=False, y=False)

                vb = self.plotWidget.getPlotItem().getViewBox()
                self._updating_from_state = True
                vb.setRange(yRange=(y_min, y_max), padding=0)
                self._updating_from_state = False

                # Переставляем горизонтальные линии через каждые 10 дБ
                step_y = 10
                start_y = (y_min // step_y) * step_y
                if start_y < y_min:
                    start_y += step_y

                idx = 0
                y = start_y
                while y < y_max and idx < len(self._hgrid_lines):
                    self._hgrid_lines[idx].setPos(y)
                    self._hgrid_lines[idx].setVisible(True)
                    y += step_y
                    idx += 1
                # Прячем лишние линии из пула
                while idx < len(self._hgrid_lines):
                    self._hgrid_lines[idx].setVisible(False)
                    idx += 1

                self.plotWidget.getAxis('left').setTickSpacing(
                    major=10, minor=10)
                if (
                    self._current_x_min is not None
                    and self._current_x_max is not None
                ):
                    self._update_info_labels(
                        self._current_x_min, self._current_x_max)

        # Параметры (None = не опрашивался в этом кадре)
        self._apply_state_params(state)
