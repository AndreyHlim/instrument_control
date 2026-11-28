import pyqtgraph as pg
from PyQt6.QtCore import QEvent, QObject, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from constants import FREQ_DIM
from dataclass import DeviceState
from gui.styles import (BORDER_COLOR, FRAME_RADIUS, PLOT_ACTIONS_STRIP_W,
                        PLOT_LABEL_FONT_BOLD, PLOT_LABEL_FONT_FAMILY,
                        PLOT_LABEL_FONT_SIZE, PLOT_N_HGRID_LINES,
                        PLOT_N_VGRID_LINES, Style, plot_background_color,
                        plot_grid_pen)
from instruments.fsva import RS_FSVA3013


class _RoundedBorderOverlay(QWidget):
    """Прозрачная накладка поверх графика: рисует только рамку.

    Тот же приём, что в CollapsibleSection: рамка рисуется самим
    виджетом, а не stylesheet'ом. Полотно графика оставляем непрозрачным
    цветом окна — тогда углы за дугой рамки визуально неотличимы от фона.
    """

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(BORDER_COLOR), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Полпикселя внутрь, чтобы линия не срезалась краем виджета
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
            FRAME_RADIUS, FRAME_RADIUS)


class PlotMixin:
    """Миксин: настройка графика и его обновление.

    Предполагается, что у окна есть:
    - self.plotWidget (PlotWidget из .ui-файла);
    - self._trace_worker (создаётся ConnectionMixin);
    - self._apply_state_params (метод StateMixin — вызывается в конце
      update_state, связность через множественное наследование).
    """
    # Стартовый экран до подключения прибора
    START_X_MIN, START_X_MAX = 750*1e6, 1.25*1e9    # Гц: 0.75…1.25 ГГц
    START_REFLEVEL, START_RANGE = -50, 100.0    # дБ

    def settings_plot(self) -> None:
        """Настроить график и создать вспомогательные элементы.

        Делает однократную инициализацию: пустая кривая трассы, пулы
        линий сетки (20 горизонтальных, 9 вертикальных), текстовые
        метки CF/Span/цена деления/RBW-VBW, оси, фиксация диапазонов и
        дебаунс-таймер для ручного изменения диапазона X мышкой.

        Note:
            Повторный вызов безопасен: перед созданием удаляются ранее
            созданные кривая и метки (защита от дублей). Пулы линий
            сетки при этом НЕ пересоздаются — позиции задаются позже
            в update_state.
        """
        # Видимость основной трассы — чисто GUI, прибору ничего не шлём
        self._main_visible: bool = True

        # Фон полотна
        self.plotWidget.setBackground(plot_background_color())

        # Защита от дублей при пересоздании
        if hasattr(self, '_curve') and self._curve is not None:
            self.plotWidget.removeItem(self._curve)
        scene = self.plotWidget.scene()
        for attr in (
            '_cf_label', '_span_label', '_perdiv_label', '_rvbw_label',
            '_errors_label',
        ):
            if hasattr(self, attr) and getattr(self, attr) is not None:
                scene.removeItem(getattr(self, attr))
        for attr in ('_hgrid_lines', '_vgrid_lines'):
            for line in getattr(self, attr, []):
                self.plotWidget.removeItem(line)
        self._curve = self.plotWidget.plot([], [], pen=Style.MAIN_TRACE_COLOR)

        # Цвет и стиль линий сетки
        grid_pen = plot_grid_pen()
        # --- Горизонтальные линии (пул, позиции задаются в update_state) ---
        self._hgrid_lines = []
        for _ in range(PLOT_N_HGRID_LINES):
            line = pg.InfiniteLine(angle=0, movable=False, pen=grid_pen)
            line.setVisible(False)
            self.plotWidget.addItem(line)
            self._hgrid_lines.append(line)

        # --- Вертикальные линии (позиции зададим в update_state) ---
        # Линии сетки
        self._vgrid_lines = []
        for i in range(PLOT_N_VGRID_LINES):
            line = pg.InfiniteLine(angle=90, movable=False, pen=grid_pen)
            self.plotWidget.addItem(line)
            self._vgrid_lines.append(line)

        # --- Текстовые метки CF / Span / цена деления ПОД осью X ---
        self._cf_label = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(0, 1))
        self._span_label = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(1, 1))
        self._perdiv_label = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(0.5, 1))
        self._rvbw_label = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(0.5, 1))
        self._errors_label = pg.TextItem(
            text='', color=Style.PLOT_ERRORS_LABEL_COLOR, anchor=(0, 1))
        font = QFont(PLOT_LABEL_FONT_FAMILY)
        font.setPointSizeF(PLOT_LABEL_FONT_SIZE)
        font.setBold(PLOT_LABEL_FONT_BOLD)
        self._errors_label.textItem.setFont(font)

        # Метки добавляем прямо в сцену: их позиция задаётся в ПИКСЕЛЯХ
        # области графика, поэтому при панорамировании они не движутся
        # вместе с полотном — позиции в координатах данных ездили бы
        for label in (
            self._cf_label, self._span_label,
            self._perdiv_label, self._rvbw_label,
            self._errors_label,
        ):
            self.plotWidget.scene().addItem(label)
        self.plotWidget.getAxis('bottom').enableAutoSIPrefix(False)
        self.plotWidget.setLabel('bottom', 'Частота')
        self.plotWidget.setLabel('left', 'Уровень', units='дБ')

        self.plotWidget.getAxis('left').enableAutoSIPrefix(False)

        # Границы полотна: оси top/right показываем пустыми —
        # от них остаётся только линия (засечки и подписи заглушены)
        pi = self.plotWidget.getPlotItem()
        pi.layout.setContentsMargins(0, 25, PLOT_ACTIONS_STRIP_W, 5)
        pi.showAxis('top')
        pi.showAxis('right')
        for side in ('top', 'right'):
            axis = self.plotWidget.getAxis(side)
            axis.setStyle(showValues=False, tickLength=0)
            axis.setTicks([[], []])   # major и minor уровни — пустые

        # Нижняя и левая оси: только подписи, без засечек —
        # сетку рисуют наши линии
        self.plotWidget.getAxis('bottom').setStyle(tickLength=0)
        self.plotWidget.getAxis('left').setStyle(tickLength=0)

        self.plotWidget.setMouseEnabled(x=True, y=False)  # X—мышка, Y—прибор
        self.plotWidget.enableAutoRange(x=False)
        self.plotWidget.getViewBox().setDefaultPadding(0)

        self._current_x_min: float | None = None
        self._current_x_max: float | None = None
        self._current_y_min: float | None = None
        self._current_y_max: float | None = None
        self._current_reflevel: float | None = None
        self._current_range: float | None = None
        # Последние строки RBW/VBW для метки на графике
        self._rbw_str: str = ''
        self._vbw_str: str = ''
        self._errors_str: str = ''
        # Режим накопления/детектор главного графика — для легенды
        # доп. трасс (кэш: кадр может прийти без опроса этих полей)
        self._main_trace_acc: str | None = None
        self._main_trace_det: str | None = None
        self._current_amp_unit: str | None = None

        # --- Дебаунс для ручного изменения X ---
        self._updating_from_state = False
        self._pending_x_range: tuple[float, float] | None = None
        self._x_debounce = QTimer()
        self._x_debounce.setSingleShot(True)
        self._x_debounce.setInterval(300)  # мс
        self._x_debounce.timeout.connect(self._send_x_range_cmd)

        # Реакции на мышь над графиком: перетаскивание/колесо меняют
        # span (вместо кнопок), resize перепривязывает пиксельные метки
        vb = self.plotWidget.getPlotItem().getViewBox()
        self._apply_x_limits()
        vb.sigRangeChanged.connect(self._on_x_range_changed)
        vb.sigResized.connect(self._reposition_labels)
        vb.sigResized.connect(self._markers_reposition)
        pi.hideButtons()            # скрыть кнопку автомасштаба
        vb.setMenuEnabled(False)    # запретить контекстное меню графика

        # Стартовая сетка до подключения прибора
        self._apply_start_grid()

        # Рамка основного графика — накладкой поверх, как у секций
        self._frame_overlay = _RoundedBorderOverlay(self.plotWidget)
        self._frame_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._frame_overlay.setGeometry(self.plotWidget.rect())
        self._frame_overlay.raise_()
        self.plotWidget.installEventFilter(self)

    def _reposition_labels(self) -> None:
        """Метки в пикселях: при изменении геометрии окна перепривязать."""
        if self._current_x_min is None or self._current_x_max is None:
            return
        self._update_info_labels(self._current_x_min, self._current_x_max)

    def _update_x_grid(self, x_min: float, x_max: float) -> None:
        """Выровнять вертикальные линии сетки и деления оси X по окну.

        Линии и деления привязаны к видимой области (10 делений), а не
        к «красивым» значениям частоты — при панорамировании остаются
        на местах, меняются только числа под ними. Единица измерения
        выбирается по абсолютному значению центра окна (как на приборе)
        и выводится в названии оси.

        Размерности частот перечислены по убыванию делителя
        — на этом основан автоподбор размерности
        """
        x_span = x_max - x_min
        if x_span <= 0:
            return
        x_step = x_span / 10.0

        # Размерность — по центру окна, а не по шагу: окно вокруг 1 ГГц
        # остаётся в ГГц независимо от ширины span
        abs_center = abs((x_min + x_max) / 2)
        for unit, div in FREQ_DIM.items():
            if abs_center >= div:
                break
        else:
            unit, div = 'Гц', 1.0

        # Знаков после запятой — столько, чтобы соседние деления
        # различались при любом шаге
        step_scaled = x_step / div
        if step_scaled >= 10:
            dec = 0
        elif step_scaled >= 1:
            dec = 1
        elif step_scaled >= 0.1:
            dec = 2
        else:
            dec = 3

        ticks = [
            (x_min + i * x_step, f'{(x_min + i * x_step) / div:.{dec}f}')
            for i in range(11)
        ]
        axis_bottom = self.plotWidget.getAxis('bottom')
        axis_bottom.setTicks([ticks])
        axis_bottom.setLabel(f'Частота ({unit})')

        for i, line in enumerate(self._vgrid_lines):
            line.setPos(x_min + (i + 1) * x_step)

    def _on_x_range_changed(self, viewbox, ranges) -> None:
        """Срабатывает при перетаскивании/зуме оси X мышкой."""
        if self._updating_from_state:
            return
        if getattr(self, '_paused', False):
            self._ensure_unpaused()
        x_range = ranges[0]
        x_min, x_max = x_range[0], x_range[1]
        self._pending_x_range = (x_min, x_max)
        self._x_debounce.start()

        self._update_x_grid(x_min, x_max)
        self._update_info_labels(x_min, x_max)
        self._markers_view_changed(x_min, x_max)

    def _place_errors_label(self) -> None:
        """Разместить метку ошибок у левой кромки виджета.

        Позиция осознанно привязана не к полотну данных, а к краю
        всего PlotItem: метка должна висеть под осью Y, левее сетки,
        даже если поле осей изменит ширину. Поэтому прямоугольник
        берём у PlotItem, а не у ViewBox (его sceneBoundingRect
        описывает только область данных — отсюда «под началом сетки»).
        """
        rect = self.plotWidget.getPlotItem().sceneBoundingRect()
        self._errors_label.setPos(rect.left(), rect.bottom())

    def _update_info_labels(self, x_min, x_max):
        """Обновить метки CF / Span / цена деления под осью X.

        Args:
            x_min: левая граница видимого диапазона, Гц.
            x_max: правая граница видимого диапазона, Гц.

        Note:
            Ничего не делает, пока не известен Y-диапазон
            (self._current_y_min / _current_y_max are None).

            Геометрия берётся в координатах сцены (sceneBoundingRect):
            локальный boundingRect() ViewBox не знает о смещении на
            ширину осей и поля графика — раньше это компенсировали
            константами (+50/+20), привязанными к текущей разметке.
        """
        if self._current_y_min is None or self._current_y_max is None:
            return

        # Область данных в координатах сцены
        vb = self.plotWidget.getPlotItem().getViewBox()
        rect = vb.sceneBoundingRect()

        x_px = rect.left()
        y_px = rect.bottom() - 5

        center_hz = (x_min + x_max) / 2
        span_hz = x_max - x_min
        per_div_hz = span_hz / 10.0

        self._cf_label.setText(
            f'CF = {self._format_freq(center_hz, force_decimals=6)}')
        self._cf_label.setPos(x_px, y_px)

        # Раскладка меток по долям ширины окна (подбирается по вкусу)
        self._perdiv_label.setText(f'{self._format_freq(per_div_hz)} /')
        self._perdiv_label.setPos(x_px + 0.35 * rect.width(), y_px)

        if self._rbw_str and self._vbw_str:
            self._rvbw_label.setText(
                f'RBW/VBW = {self._rbw_str}/{self._vbw_str}')
            self._rvbw_label.setPos(x_px + 0.65 * rect.width(), y_px)

        self._span_label.setText(f'Span = ±{self._format_freq(span_hz/2)}')
        self._span_label.setPos(rect.right(), y_px)
        self._place_errors_label()

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

        # Автоподбор: первая (крупнейшая) единица, в которой значение >= 1
        for unit, div in FREQ_DIM.items():
            if abs_val >= div:
                break
        else:
            unit, div = 'Гц', 1.0
        value = hz / div

        if force_decimals is not None:
            return f'{value:.{force_decimals}f} {unit}'
        if dim in FREQ_DIM:
            return f'{abs_val / FREQ_DIM[dim]:.0f} {dim}'

        # Все значащие цифры, но не больше 6 знаков после запятой:
        # 1.562 ГГц, 937.499996 МГц, 50.0 кГц, 500 Гц
        text = f'{value:.6f}'.rstrip('0').rstrip('.')
        return f'{text} {unit}'

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
        self._user_send(f'set_cf:{new_center}')
        self._user_send(f'set_span:{new_span}')

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

        if getattr(self, '_paused', False):
            return

        # График
        self._curve.setData(state.freqs, state.levels)
        # Кэш последнего полного кадра — для поиска пика маркерами
        if state.freqs:
            self._last_freqs = state.freqs
            self._last_levels = state.levels
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

                self._update_x_grid(x_min, x_max)

                # Частотная сетка сменилась — накопление доп. трасс
                # с прежней сеткой невалидно, сбрасываем
                if hasattr(self, '_acc_traces'):
                    self._reset_acc_traces()
                self._markers_view_changed()

                # Метки CF/Span/цена деления привязаны к окну X —
                # обновляем при любой смене диапазона
                self._update_info_labels(x_min, x_max)

                # Подписи по Y: строго каждые 10 дБ
                axis_left = self.plotWidget.getAxis('left')
                axis_left.setTickSpacing(major=10, minor=10)

            # Водопад (live): шкала цветов — как ось Y графика
            if (
                self._current_reflevel is not None
                and self._current_range is not None
            ):
                self.add_waterfall_frame(
                    state.levels,
                    vmin=self._current_reflevel - self._current_range,
                    vmax=self._current_reflevel,
                )
            else:
                self.add_waterfall_frame(state.levels)

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
                self._update_y_grid(y_min, y_max)

                if (
                    self._current_x_min is not None
                    and self._current_x_max is not None
                ):
                    self._update_info_labels(
                        self._current_x_min, self._current_x_max)
                    self._markers_reposition()

        # --- RBW/VBW для подписи на графике ---
        rvbw_changed = False
        if state.rbw is not None:
            self._rbw_hz = state.rbw * 1e3     # Гц — сырые, для экспорта
            self._rbw_str = self._format_freq(self._rbw_hz)
            rvbw_changed = True
        if state.vbw is not None:
            self._vbw_hz = state.vbw * 1e3
            self._vbw_str = self._format_freq(self._vbw_hz)
            rvbw_changed = True
        if rvbw_changed and (
            self._current_x_min is not None
            and self._current_x_max is not None
        ):
            self._update_info_labels(self._current_x_min, self._current_x_max)

        # Ошибки индикации дисплея (None = кадр без опроса ошибок)
        if state.errors is not None:
            self._errors_str = ' '.join(state.errors)
            self._errors_label.setText(self._errors_str)

        # Режим накопления/детектор главного графика (None = кадр
        # без опроса) — легенда доп. трасс читает кэш каждый кадр
        if state.trace_acc is not None:
            self._main_trace_acc = state.trace_acc
        if state.det is not None:
            self._main_trace_det = state.det
        if state.amp_unit is not None:
            self._current_amp_unit = state.amp_unit

        # Накопительные трассы (AccTracesMixin)
        if hasattr(self, '_acc_traces'):
            self._update_acc_traces(state)

        # Автопоиск пика для включённых маркеров
        if hasattr(self, '_marker_entries'):
            self._markers_autopeak_step()
        # Параметры (None = не опрашивался в этом кадре)
        self._apply_state_params(state)
        self._update_markers_legend()

    def _update_y_grid(self, y_min: float, y_max: float) -> None:
        """Переставить горизонтальные линии сетки (шаг 10 дБ) и ось Y."""
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

        self.plotWidget.getAxis('left').setTickSpacing(major=10, minor=10)

    def _apply_start_grid(self) -> None:
        """Сетка и диапазоны до первого кадра с прибора.

        Значения совпадают с теми, что обычно приходят с первым кадром,
        поэтому после подключения экран не «прыгает».
        """
        self._current_x_min = self.START_X_MIN
        self._current_x_max = self.START_X_MAX
        self._current_reflevel = self.START_REFLEVEL
        self._current_range = self.START_RANGE
        self._current_y_min = self._current_reflevel - self._current_range
        self._current_y_max = self._current_reflevel

        vb = self.plotWidget.getPlotItem().getViewBox()
        self._updating_from_state = True
        vb.setRange(
            xRange=(self._current_x_min, self._current_x_max),
            yRange=(self._current_y_min, self._current_y_max),
            padding=0)
        self._updating_from_state = False

        self._update_x_grid(self._current_x_min, self._current_x_max)
        self._update_y_grid(self._current_y_min, self._current_y_max)
        self._update_info_labels(self._current_x_min, self._current_x_max)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Накладка-рамка и колонка кнопок следуют за геометрией графика."""
        if watched is self.plotWidget and event.type() == QEvent.Type.Resize:
            self._frame_overlay.setGeometry(self.plotWidget.rect())
            placer = getattr(self, '_place_plot_actions_col', None)
            if placer is not None:
                placer()
        parent_filter = getattr(super(), 'eventFilter', None)
        if parent_filter is not None:
            return parent_filter(watched, event)
        return False

    def _apply_x_limits(self) -> None:
        """Зажать панорамирование и зум в рабочий диапазон прибора.

        setLimits ограничивает видимую область жёстко: потянуть левее
        FREQ_MIN_HZ нельзя, а зум «отдаление» не расширяет окно дальше
        полного диапазона прибора — при попытке вид сжимается до
        [FREQ_MIN_HZ, FREQ_MAX_HZ]. Ограничение только по X: ось Y
        полностью управляется прибором (reflevel/range).
        """
        self.plotWidget.getPlotItem().getViewBox().setLimits(
            xMin=RS_FSVA3013.FREQ_MIN_HZ,
            xMax=RS_FSVA3013.FREQ_MAX_HZ)

    def on_main_visible_changed(self, visible: bool) -> None:
        """Скрыть/показать основную трассу на графике (чекбокс is_visible).

        Только отображение: кэш кадра (_last_freqs/_last_levels),
        накопление прибора и водопад продолжают работать как раньше —
        маркеры и экспорт видят данные даже при скрытой кривой.
        Прибору команда не отправляется.
        """
        self._main_visible = visible
        if self._curve is not None:
            self._curve.setVisible(visible)
        self._update_acc_legend()
        self._update_markers_legend()
