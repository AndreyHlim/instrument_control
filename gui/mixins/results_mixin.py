import os

import pyqtgraph as pg
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (QFileDialog, QSizePolicy, QToolButton,
                             QVBoxLayout, QWidget)

from function import resource_path
from gui.controls.controls import CollapsibleSection
from gui.styles import (COL_SPACING, PLOT_ACTIONS_STRIP_W, PLOT_BTN_GAP,
                        PLOT_BTN_ICON_SIZE, PLOT_BTN_SIZE, RES_AXIS_H, Style,
                        plot_background_color, plot_grid_pen)


class ResultsMixin:
    """Миксин: панель результатов измерений над основным графиком.

    Общая инфраструктура графика результатов: полотно, оси, пулы
    линий сетки, полоса кнопок (скриншот). Отрисовка данных — у
    рендеров методов: RES_RENDERERS отображает номер активного метода
    в имя метода-рендера на окне (см. gui/mixins/results/method1.py).
    Активный метод — открытая секция «Метод измерений N»: PanelsMixin
    подписывается на header_button.toggled и вызывает _set_active_method.

    Предполагается, что у окна есть:
    - self.widget_4 (контейнер над графиком из .ui-файла);
    - рендеры методов (миксины gui/mixins/results/*).
    """

    RESULTS_COLLAPSED = True   # True — стартовать свёрнутым

    # Номер метода -> имя метода-рендера на окне
    RES_RENDERERS = {1: 'results_refresh_m1'}

    def settings_results(self) -> None:
        """Обернуть widget_4 в секцию с графиком результатов."""
        layout = self.widget_4.layout()
        if layout is None:
            layout = QVBoxLayout(self.widget_4)
            layout.setContentsMargins(0, 0, 0, 0)

        self._results_content = QWidget()
        lay = QVBoxLayout(self._results_content)
        lay.setContentsMargins(0, 0, 0, 0)

        self.results_plot = pg.PlotWidget()
        self.results_plot.setBackground(plot_background_color())
        pi = self.results_plot.getPlotItem()
        # Полоса справа — под кнопку скриншота (как у основного графика)
        pi.layout.setContentsMargins(0, 5, PLOT_ACTIONS_STRIP_W, 5)
        pi.hideButtons()
        pi.getViewBox().setMenuEnabled(False)
        # Границы области: пустые оси top/right (как у основного графика)
        pi.showAxis('top')
        pi.showAxis('right')
        for side in ('top', 'right'):
            ax = pi.getAxis(side)
            ax.setStyle(showValues=False, tickLength=0)
        self.results_plot.getPlotItem().getAxis('top').setHeight(RES_AXIS_H)
        # Ось Y: тики снаружи; цвет подписей задаёт рендер метода
        ax_left = pi.getAxis('left')
        ax_left.setStyle(tickLength=0)
        self.results_plot.setMouseEnabled(x=True, y=False)
        # Собственная сетка (пулы линий): встроенная showGrid в pyqtgraph
        # 0.13.7+ рисует линии и на минорных тиках — между основными
        self._res_grid_pen = plot_grid_pen()
        self._res_vgrid: list = []
        self._res_hgrid: list = []
        self.results_plot.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.results_plot.setLabel('left', 'Амплитуда')

        # Ось X: компактная колонка, без засечек и зазора до подписей
        ax_bottom = pi.getAxis('bottom')
        ax_bottom.setStyle(tickTextOffset=0, tickLength=0)
        ax_bottom.setTickFont(QFont())
        ax_bottom.setHeight(RES_AXIS_H)

        # Элементы данных рендеров (кривые и т.п.) и активный метод
        self._res_render_items: dict[int, list] = {}
        self._res_y_min: float | None = None
        self._res_y_max: float | None = None
        self._active_method_num: int | None = None

        lay.addWidget(self.results_plot)
        self._build_res_actions()

        self.sec_results = CollapsibleSection("Результаты измерений")
        # График — вплотную к рамке секции: без полей сетки контента
        self.sec_results.content_layout.setContentsMargins(1, 0, 1, 1)
        self.sec_results.content_layout.setSpacing(0)
        self.sec_results.add_row_layout('', self._results_content)
        self.sec_results._toggle(not self.RESULTS_COLLAPSED)
        layout.setSpacing(0)
        layout.addWidget(self.sec_results)

    # --- Диспетчер активного метода ---------------------------------------

    def _set_active_method(self, num: int, checked: bool) -> None:
        """Раскрыта секция метода num: сменить активный метод, перерисовать.

        Секция закрылась — активность не трогаем: в эксклюзивной группе
        закрытие одной секции всегда сопровождается раскрытием другой,
        чей toggled(True) придёт следом.
        """
        if not checked:
            return
        self._active_method_num = num
        self._results_reset()
        self._results_refresh()

    def _results_refresh(self) -> None:
        """Прорисовать график результатов активным методом.

        Вызывается методами при изменении их данных: добавление строки
        в таблицу, кадр измерения, загрузка файла. Активный метод
        задаётся раскрытием его секции (_set_active_method).
        """
        if getattr(self, 'results_plot', None) is None:
            return   # settings_results ещё не выполнялся
        handler = self.RES_RENDERERS.get(
            getattr(self, '_active_method_num', None))
        if handler is not None:
            getattr(self, handler)()

    def _results_reset(self) -> None:
        """Очистить график результатов, сохранив общую инфраструктуру.

        Убирает все элементы данных рендеров (кривые и т.п.), прячет
        пулы линий сетки, чистит тики и шкалу, сбрасывает лимиты X.
        """
        for items in self._res_render_items.values():
            for item in items:
                self.results_plot.removeItem(item)
        self._res_render_items.clear()
        for line in self._res_vgrid + self._res_hgrid:
            line.setVisible(False)
        self.results_plot.getAxis('left').setTicks([[]])
        self.results_plot.getAxis('bottom').setTicks([[]])
        self._res_y_min = self._res_y_max = None
        self.results_plot.getPlotItem().getViewBox().setLimits(
            xMin=0, xMax=1)

        # Сценическая надпись рендера метода 1: не удаляется, а прячется —
        # при следующем refresh рендер покажет её заново
        lbl = getattr(self, '_m1_res_label', None)
        if lbl is not None:
            lbl.setVisible(False)

    # --- Хуки для методов измерений ---------------------------------------

    def _results_expand(self) -> None:
        """Раскрыть секцию результатов (старт измерений S/N и т.п.)."""
        if getattr(self, 'sec_results', None) is not None:
            self.sec_results._toggle(True)

    # --- Общие хелперы шкалы -----------------------------------------------

    @staticmethod
    def _res_y_ticks(ymin: float, ymax: float) -> list:
        """Тики оси Y: ровные значения, кратные 10, внутри шкалы."""
        start = int(-((-ymin) // 10)) * 10   # ceil(ymin/10)*10
        return [(y, f'{y:g}') for y in range(start, int(ymax) + 1, 10)]

    @staticmethod
    def _floor5(v: float) -> float:
        """Ближайшее меньшее кратное 5; само кратное — на 5 ниже."""
        y = 5 * (v // 5)
        return y - 5 if y == v else y

    @staticmethod
    def _ceil5(v: float) -> float:
        """Ближайшее большее кратное 5; само кратное — на 5 выше."""
        y = 5 * ((v + 4.9999999) // 5)   # безопасный ceil для float
        return y if y > v else y + 5

    # --- Кнопка скриншота поверх графика результатов ---------------------

    def _build_res_actions(self) -> None:
        """Плавающая колонка кнопок в правой полосе графика результатов.

        Приём как в PlotActionsMixin: пустая полоса правого поля осей,
        кнопки — дети plotWidget, в layout не входят. Позиционирование
        в singleShot(0) и далее на каждый resize (sigResized ViewBox).
        """
        col = QWidget(self.results_plot)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(COL_SPACING)

        self._but_res_screen = QToolButton(col)
        self._but_res_screen.setToolTip('Сохранить график результатов в PNG')
        self._but_res_screen.setStyleSheet(Style.BUT_ICON)
        self._but_res_screen.setFixedSize(PLOT_BTN_SIZE, PLOT_BTN_SIZE)
        self._but_res_screen.setIcon(
            QIcon(resource_path('gui/icons/screen.png')))
        self._but_res_screen.setIconSize(
            QSize(PLOT_BTN_ICON_SIZE, PLOT_BTN_ICON_SIZE))
        self._but_res_screen.clicked.connect(self._but_res_screen_clicked)
        lay.addWidget(self._but_res_screen)

        col.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        col.raise_()
        self._res_actions_col = col
        QTimer.singleShot(0, self._place_res_actions_col)
        self.results_plot.getPlotItem().getViewBox().sigResized.connect(
            self._place_res_actions_col)

    def _place_res_actions_col(self) -> None:
        """Уложить колонку кнопок в правую полосу графика результатов."""
        col = getattr(self, '_res_actions_col', None)
        if col is None:
            return
        w = self.results_plot
        if w.width() < PLOT_ACTIONS_STRIP_W:
            col.setVisible(False)
            return
        x = w.width() - PLOT_ACTIONS_STRIP_W + PLOT_BTN_GAP
        col.setGeometry(x, RES_AXIS_H + 4,
                        PLOT_BTN_SIZE, col.sizeHint().height())
        col.setVisible(True)
        col.raise_()

    def _but_res_screen_clicked(self) -> None:
        """Диалог сохранения графика результатов в PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить график',
            os.path.join(self.work_dir(), 'График результатов_'),
            'PNG (*.png)')
        if not path:
            return
        if not path.lower().endswith('.png'):
            path += '.png'
        self.results_plot.grab().save(path)
        self._adopt_dialog_dir(path)

    def _place_res_grid(self, x: list, ymin: float, ymax: float) -> None:
        """Собственная сетка графика результатов.

        Вертикали — по одной на строку таблицы (позиции совпадают с
        тиками оси X), горизонтали — на позициях тиков Y (кратные 10).
        Пулы линий при необходимости растут; лишние прячутся, как в
        _update_y_grid основного графика.
        """
        # Вертикали: одна на строку таблицы
        while len(self._res_vgrid) < len(x):
            line = pg.InfiniteLine(angle=90, movable=False,
                                   pen=self._res_grid_pen)
            line.setVisible(False)
            self.results_plot.addItem(line)
            self._res_vgrid.append(line)
        for i, line in enumerate(self._res_vgrid):
            if i < len(x):
                line.setPos(x[i])
                line.setVisible(True)
            else:
                line.setVisible(False)

        # Горизонтали: на позициях тиков оси Y
        ys = [y for y, _ in self._res_y_ticks(ymin, ymax)]
        while len(self._res_hgrid) < len(ys):
            line = pg.InfiniteLine(angle=0, movable=False,
                                   pen=self._res_grid_pen)
            line.setVisible(False)
            self.results_plot.addItem(line)
            self._res_hgrid.append(line)
        for i, line in enumerate(self._res_hgrid):
            if i < len(ys):
                line.setPos(ys[i])
                line.setVisible(True)
            else:
                line.setVisible(False)
