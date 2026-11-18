import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import (QAbstractSpinBox, QApplication, QDoubleSpinBox,
                             QGridLayout, QSizePolicy, QToolButton,
                             QVBoxLayout, QWidget)

from gui.styles import Style


class Waterfall(QWidget):
    """Спектрограмма (водопад) трассы.

    Каждый кадр — одна строка на всю ширину. Новая строка появляется
    СВЕРХУ, старые сдвигаются вниз; за границей буфера строки пропадают.
    Цвет = уровень, дБ (шкала совпадает с осью Y графика).

    Режимы:
      live — строка добавляется по каждому кадру PlotWidget.

    Шкала цветов:
      авто   — COLOR_VMIN/COLOR_VMAX = None: шкала цветов повторяет
               шкалу экрана основного графика;
      ручная — границы задаются спинбоксами в поле слева от водопада
               (или классовыми константами COLOR_VMIN/COLOR_VMAX).
    """
    MODE_LIVE = 'live'

    # --- Настройка ---
    MODE = MODE_LIVE
    COLS = 1001         # ширина спектрограммы, колонок (частотных отсчётов)
    ROWS = 500          # глубина истории, строк
    VMIN = -120.0       # дБ: низ шкалы цветов (fallback)
    VMAX = 10.0         # дБ: верх шкалы цветов (fallback)
    COLORMAP = 'viridis'
    MARGIN_DB = 50.0
    COLOR_VMIN = None   # None = шкала цветов следует за шкалой экрана;
    COLOR_VMAX = None   # числа — своя (ручная) шкала цветов водопада
    COLOR_GAMMA = 1.0   # <1 — осветлить тёмный низ, >1 — усилить верх

    # --- Панель управления шкалой (слева от водопада) ---
    CONTROLS = True     # False — убрать панель совсем
    CTRL_WIDTH = 44     # ширина панели, px
    CTRL_MIN_W = 28
    SPIN_DECIMALS = 0           # знаков после запятой в спинбоксах
    SPIN_STEP = 5               # шаг изменения, дБ
    SPIN_RANGE = (-200, 200)    # допустимые границы, дБ

    scaleChanged = pyqtSignal(float, float, bool)  # vmin, vmax, ручная?

    def __init__(self, main_plot=None, parent=None):
        super().__init__(parent)

        self._main_plot = main_plot  # pg.PlotWidget основного графика

        self._manual = (self.COLOR_VMIN is not None
                        or self.COLOR_VMAX is not None)
        self._last_scale = None      # последняя применённая шкала (авто)
        self._sync_pending = False   # пересинхронизация уже запланирована

        self._lay = QGridLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget()
        self.set_background()
        self.plot.hideAxis('left')
        self.plot.hideAxis('bottom')
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)

        vb = self.plot.getPlotItem().getViewBox()
        vb.setDefaultPadding(0)

        # Запретить любые изменения масштаба
        vb.setMouseEnabled(x=False, y=False)
        vb.disableAutoRange()

        pi = self.plot.getPlotItem()
        pi.hideButtons()            # скрыть кнопку автомасштаба
        vb.setMenuEnabled(False)    # запретить контекстное меню графика

        self._lay.addWidget(self.plot, 0, 0)

        self._img = pg.ImageItem(axisOrder='row-major')
        self.plot.addItem(self._img)
        lut = pg.colormap.get(self.COLORMAP).getLookupTable(0.0, 1.0, 256)
        self._img.setLookupTable(lut)
        self._img.setLevels([self.VMIN, self.VMAX])

        # Буфер и диапазоны — единым блоком после создания всех виджетов
        if self.COLS is not None:
            self._init_buffer(self.COLS)
        else:
            self._buf = None   # создадутся по первому кадру

        # Панель Min/Max шкалы цветов — до первого _sync_margins
        if self.CONTROLS:
            self._make_controls()

        # Держать поля синхронными при любом изменении размеров
        if self._main_plot is not None:
            self._main_vb = self._main_plot.getPlotItem().vb
            self._main_vb.sigResized.connect(self._sync_margins)
            QTimer.singleShot(0, self._sync_margins)  # после первого показа

        self._img.setLookupTable(self._make_lut())

    # ------------------------------------------------------------------
    # Панель управления шкалой
    # ------------------------------------------------------------------
    def _make_controls(self) -> None:
        """Панель «верх/низ шкалы цветов» в поле слева от водопада.

        Панель — плавающий виджет поверх водопада: она НЕ входит в layout
        и не влияет на совпадение водопада с сеткой основного графика.
        Располагается в пустой зоне слева (там, где у основного графика
        ось Y): верх шкалы — сверху, низ — снизу. Если поле уже панели —
        панель ложится лёгким оверлеем на левый край водопада.
        """
        self._ctrl = QWidget(self)
        lay = QVBoxLayout(self._ctrl)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(2)

        lo = self.COLOR_VMIN if self.COLOR_VMIN is not None else self.VMIN
        hi = self.COLOR_VMAX if self.COLOR_VMAX is not None else self.VMAX
        self.sp_min = self._make_spin(lo, 'Низ шкалы цветов водопада, дБ')
        self.sp_max = self._make_spin(hi, 'Верх шкалы цветов водопада, дБ')

        self.btn_auto = QToolButton()
        self.btn_auto.setText('Auto')
        self.btn_auto.setCheckable(True)
        self.btn_auto.setChecked(not self._manual)
        self.btn_auto.setToolTip(
            'Auto = авто: шкала цветов следует за шкалой экрана.\n'
            'Выключено — ручная шкала из полей выше и ниже.')
        self.btn_auto.toggled.connect(self._on_auto_toggled)
        self.btn_auto.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay.addWidget(self.sp_max)
        lay.addStretch(1)
        lay.addWidget(self.btn_auto)
        lay.addStretch(1)
        lay.addWidget(self.sp_min)

        self.sp_min.valueChanged.connect(self._on_spin_changed)
        self.sp_max.valueChanged.connect(self._on_spin_changed)

        self._place_controls()

    def _make_spin(self, value: float, tip: str) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setDecimals(self.SPIN_DECIMALS)
        sb.setSingleStep(self.SPIN_STEP)
        sb.setRange(*self.SPIN_RANGE)
        sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sb.setKeyboardTracking(False)   # не дёргаться на каждом символе
        sb.setMinimumWidth(24)
        sb.lineEdit().setStyleSheet(Style.TEXT_BOX)
        sb.setToolTip(tip)
        sb.setValue(value)
        return sb

    def _set_spin(self, sb: QDoubleSpinBox, val: float) -> None:
        """Программно обновить спинбокс без срабатывания valueChanged."""
        lo, hi = self.SPIN_RANGE
        sb.blockSignals(True)
        sb.setValue(float(np.clip(val, lo, hi)))
        sb.blockSignals(False)

    def _sync_spinboxes(self, vmin, vmax) -> None:
        """Показать в спинбоксах текущую авто-шкалу (как на экране)."""
        if vmin is None or vmax is None:
            return
        self._set_spin(self.sp_min, vmin)
        self._set_spin(self.sp_max, vmax)

    def _on_spin_changed(self) -> None:
        """Ручное редактирование границы шкалы цветов."""
        lo, hi = self.sp_min.value(), self.sp_max.value()
        if hi - lo < 20:   # держим хотя бы 20 дБ между границами
            if self.sender() is self.sp_max:
                self._set_spin(self.sp_min, hi - 20)
            else:
                self._set_spin(self.sp_max, lo + 20)
            lo, hi = self.sp_min.value(), self.sp_max.value()

        self._manual = True
        self.btn_auto.blockSignals(True)
        self.btn_auto.setChecked(False)
        self.btn_auto.blockSignals(False)

        self.COLOR_VMIN, self.COLOR_VMAX = lo, hi
        self._img.setLevels([lo, hi])
        self.scaleChanged.emit(lo, hi, True)

    def _on_auto_toggled(self, checked: bool) -> None:
        self._manual = not checked
        if checked:
            # вернуться к авто: применить последнюю известную шкалу экрана
            if self._last_scale is not None:
                self._img.setLevels(list(self._last_scale))
                self._sync_spinboxes(*self._last_scale)
            self.scaleChanged.emit(self._last_scale[0] if self._last_scale
                                   else np.nan,
                                   self._last_scale[1] if self._last_scale
                                   else np.nan, False)
        else:
            self._on_spin_changed()

    def _place_controls(self, empty_left: int = None) -> None:
        """Уложить панель строго в пустую зону слева от данных водопада.

        Пустая зона — поле оси Y основного графика. Панель сжимается
        под неё и никогда не заходит на область данных; если зоны
        совсем нет (или она уже минимальной ширины) — панель прячется.
        """
        if not self.CONTROLS:
            return
        if empty_left is None:
            empty_left = self._lay.contentsMargins().left()
        width = min(self.CTRL_WIDTH, max(0, empty_left - 2))
        if width >= self.CTRL_MIN_W:
            self._ctrl.setGeometry(0, 0, width, self.height())
            self._ctrl.setVisible(True)
            self._ctrl.raise_()
        else:
            self._ctrl.setVisible(False)

    # ------------------------------------------------------------------
    # Остальное — как было
    # ------------------------------------------------------------------
    def _make_lut(self) -> np.ndarray:
        """LUT колормапы с гамма-коррекцией.

        COLOR_GAMMA < 1 растягивает тёмный низ (слабые сигналы
        становятся различимее), > 1 — сжимает тёмное и усиливает верх.
        """
        cm = pg.colormap.get(self.COLORMAP)
        lut = cm.getLookupTable(0.0, 1.0, 256)
        if self.COLOR_GAMMA != 1.0:
            t = np.linspace(0.0, 1.0, 256) ** self.COLOR_GAMMA
            lut = (cm.map(t, mode='float') * 255).astype(np.ubyte)
        return lut

    def _init_buffer(self, cols: int) -> None:
        """Создать буфер заданной ширины и настроить вид под неё."""
        self._buf = np.full((self.ROWS, cols), np.nan, dtype=np.float32)
        vb = self.plot.getPlotItem().getViewBox()
        vb.setRange(xRange=(0, cols), yRange=(0, self.ROWS))
        vb.setLimits(xMin=0, xMax=cols, yMin=0, yMax=self.ROWS)
        self._img.setImage(self._buf, autoLevels=False)

    def _resample_buffer(self, cols: int) -> None:
        """Пересчитать буфер под новую ширину (смена числа точек прибора).

        История сохраняется: строки без NaN растягиваются/сжимаются
        по колонкам, пустые (NaN) остаются пустыми.
        """
        old = self._buf
        cols_old = old.shape[1]
        idx = np.linspace(0.0, cols_old - 1.0, cols)
        lo = np.clip(idx.astype(int), 0, cols_old - 1)
        hi = np.minimum(lo + 1, cols_old - 1)
        frac = (idx - lo).astype(np.float32)

        new = np.full((self.ROWS, cols), np.nan, dtype=np.float32)
        filled = ~np.isnan(old).all(axis=1)   # строки с данными
        if filled.any():
            new[filled] = (old[filled][:, lo] * (1.0 - frac)
                           + old[filled][:, hi] * frac)
        self._init_buffer(cols)
        self._buf = new
        self._img.setImage(self._buf, autoLevels=False)

    def _sync_margins(self) -> None:
        """Запланировать пересчёт полей на конец текущего цикла событий.

        Сигналы изменения размеров приходят до того, как layout разложит
        виджеты: чтение геометрии «в момент сигнала» даёт устаревшие
        значения (водопад уже/ещё не того размера). Откладываем расчёт
        через singleShot(0): к моменту выполнения все события layout
        обработаны, геометрия консистентна.
        """
        if self._sync_pending:
            return
        self._sync_pending = True
        QTimer.singleShot(0, self._apply_margins)

    def _apply_margins(self) -> None:
        """Пересчитать поля водопада по актуальной геометрии.

        Область данных ViewBox основного графика переводится в координаты
        его виджета; полученные слева/справа отступы задаются водопаду.
        Если водопад живёт внутри контейнера с собственными полями
        (например, CollapsibleSection), смещение виджета относительно
        графика вычитается, чтобы данные водопада совпадали с сеткой.
        """
        self._sync_pending = False
        if self._main_plot is None:
            return
        r = self._main_plot.mapFromScene(
            self._main_vb.sceneBoundingRect()).boundingRect()
        left = max(0, int(r.left()))
        right = max(0, int(self._main_plot.width() - r.right()))

        # Смещение водопада относительно графика в координатах окна
        win = self.window()
        wf_pos = self.mapTo(win, QPoint(0, 0))
        main_pos = self._main_plot.mapTo(win, QPoint(0, 0))
        left -= wf_pos.x() - main_pos.x()
        right -= (main_pos.x() + self._main_plot.width())
        right += wf_pos.x() + self.width()

        self._lay.setContentsMargins(max(0, left), 0, max(0, right), 0)
        self._place_controls()

    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        self._sync_margins()
        if getattr(self, '_ctrl', None) is not None:
            self._place_controls()

    def set_background(self) -> None:
        """Фон водопада = фон окна программы (из палитры приложения)."""
        color = QApplication.instance().palette().color(
            QPalette.ColorRole.Window)
        self.plot.setBackground(color)

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        self._sync_margins()

    def set_scale(self, vmin: float, vmax: float) -> None:
        """Задать шкалу цветов в дБ (например, по reflevel/range графика).

        Действует только в авто-режиме; в ручном шкалу меняют спинбоксы.
        """
        if self._manual:
            return
        self._img.setLevels([vmin * 1.2, vmax * 0.8])
        self._last_scale = (vmin, vmax)
        self._sync_spinboxes(vmin, vmax)

    def clear(self) -> None:
        self._buf[:] = np.nan
        self._img.setImage(self._buf, autoLevels=False)

    def add_frame(self, levels, vmin=None, vmax=None) -> None:
        """Добавить строку по текущему кадру трассы.

        Строка вставляется только если все её уровни попадают
        в диапазон [vmin, vmax] (шкалу основного графика).

        Шкала цветов: в ручном режиме берётся из COLOR_VMIN/COLOR_VMAX,
        в авто — из vmin/vmax кадра (спинбоксы синхронизируются с ней).

        Args:
            levels: уровни, дБ (тот же массив, что уходит на кривую).
            vmin/vmax: границы шкалы этого кадра; None — не проверять.
        """
        if self.MODE != self.MODE_LIVE:
            return
        if levels is None or len(levels) == 0:
            return

        if self._manual:
            lv_min, lv_max = self.COLOR_VMIN, self.COLOR_VMAX
        else:
            lv_min, lv_max = vmin, vmax
        if lv_min is not None and lv_max is not None:
            self._img.setLevels([lv_min, lv_max])
            self._last_scale = (lv_min, lv_max)
            if not self._manual:
                self._sync_spinboxes(lv_min, lv_max)

        # Пересемплировать трассу в COLS точек
        n = len(levels)
        # Ширина ещё не задана (первый кадр) или изменилась
        if self._buf is None:
            self._init_buffer(n)
        elif n != self._buf.shape[1]:
            self._resample_buffer(n)

        cols = self._buf.shape[1]
        if n == cols:
            row = np.asarray(levels, dtype=np.float32)
        else:
            idx = np.linspace(0, n - 1, cols)
            row = np.interp(idx, np.arange(n), levels).astype(np.float32)

        # Фильтр «адекватности»: строка в шкале графика с запасом
        # MARGIN_DB за пределами (значения чуть выше reflevel
        # и чуть ниже дна экрана — тоже валидные данные)
        if vmin is not None and vmax is not None:
            eps = 1e-6   # допуск на погрешность float32 после интерполяции
            lo_limit = vmin - self.MARGIN_DB
            hi_limit = vmax + self.MARGIN_DB
            if (row.min() < lo_limit - eps) or (row.max() > hi_limit + eps):
                return

        # Сдвиг буфера и вставка новой строки сверху
        self._buf = np.roll(self._buf, -1, axis=0)
        self._buf[self.ROWS - 1] = row

        self._img.setImage(self._buf, autoLevels=False)
