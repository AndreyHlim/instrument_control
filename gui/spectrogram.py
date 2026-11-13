import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QGridLayout, QWidget


class Waterfall(QWidget):
    """Спектрограмма (водопад) трассы.

    Каждый кадр — одна строка на всю ширину. Новая строка появляется
    СВЕРХУ, старые сдвигаются вниз; за границей буфера строки пропадают.
    Цвет = уровень, дБ (шкала совпадает с осью Y графика).

    Режимы:
      live — строка добавляется по каждому кадру PlotWidget.
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
    COLOR_VMIN = -120   # None = шкала цветов следует за шкалой экрана;
    COLOR_VMAX = -30   # числа — своя шкала цветов водопада
    COLOR_GAMMA = 1.0   # <1 — осветлить тёмный низ, >1 — усилить верх

    def __init__(self, main_plot=None, parent=None):
        super().__init__(parent)

        self._main_plot = main_plot  # pg.PlotWidget основного графика

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

        # Держать поля синхронными при любом изменении размеров
        if self._main_plot is not None:
            self._main_vb = self._main_plot.getPlotItem().vb
            self._main_vb.sigResized.connect(self._sync_margins)
            QTimer.singleShot(0, self._sync_margins)  # после первого показа

        self._img.setLookupTable(self._make_lut())

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
        """Поля водопада = отступы до области данных основного графика.

        Область данных ViewBox основного графика переводится в координаты
        его виджета; полученные слева/справа отступы задаются водопаду.
        """
        if self._main_plot is None:
            return
        r = self._main_plot.mapFromScene(
            self._main_vb.sceneBoundingRect()).boundingRect()
        left = max(0, int(r.left()))
        right = max(0, int(self._main_plot.width() - r.right()))
        self._lay.setContentsMargins(left, 0, right, 0)

    def set_background(self) -> None:
        """Фон водопада = фон окна программы (из палитры приложения)."""
        color = QApplication.instance().palette().color(
            QPalette.ColorRole.Window)
        self.plot.setBackground(color)

    def set_scale(self, vmin: float, vmax: float) -> None:
        """Задать шкалу цветов в дБ (например, по reflevel/range графика)."""
        self._img.setLevels([vmin*1.2, vmax*0.8])

    def clear(self) -> None:
        self._buf[:] = np.nan
        self._img.setImage(self._buf, autoLevels=False)

    def add_frame(self, levels, vmin=None, vmax=None) -> None:
        """Добавить строку по текущему кадру трассы.

        Строка вставляется только если все её уровни попадают
        в диапазон [vmin, vmax] (шкалу основного графика).

        Args:
            levels: уровни, дБ (тот же массив, что уходит на кривую).
            vmin/vmax: границы шкалы этого кадра; None — не проверять.
        """
        if self.MODE != self.MODE_LIVE:
            return
        if levels is None or len(levels) == 0:
            return

        lv_min = self.COLOR_VMIN if self.COLOR_VMIN is not None else vmin
        lv_max = self.COLOR_VMAX if self.COLOR_VMAX is not None else vmax
        if lv_min is not None and lv_max is not None:
            self._img.setLevels([lv_min, lv_max])

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
