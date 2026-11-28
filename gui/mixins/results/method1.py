import os

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from gui.styles import Style


class Method1ResultsMixin:
    """Рендер графика результатов «Метода измерений 1».

    Две линии по точкам (с кружками-маркерами) в цветах доп. трасс 1
    и 2. Ось X — порядковые номера строк таблицы метода 1 (не
    частоты), ось Y — амплитуды столбцов Usn/Un. Границы шкалы Y —
    ближайшие кратные 5 (строго вне данных). Строка без измеренного
    значения даёт точку на нижней границе шкалы (y_min).

    Выделенная строка таблицы (мышкой или подсветкой прогона)
    отмечается на графике вертикальной жёлтой линией, над верхней
    кромкой полотна — надпись с уровнями Usn/Un этой строки.

    Подразумевается, что окно смешивает ResultsMixin (общая
    инфраструктура графика результатов) и Method1Mixin (таблица
    _m1_table). Вызывается через диспетчер ResultsMixin по словарю
    RES_RENDERERS; название метода-рендера — results_refresh_m1.
    """

    RES_SYMBOL = 'o'
    RES_SYMBOL_SIZE = 3

    def _m1_res_items(self) -> list:
        """Элементы метода 1: кривые и линия выделения.

        Ленивое создание с регистрацией в кэше: _results_reset
        удаляет зарегистрированные элементы и чистит кэш — при
        следующем refresh всё создаётся заново, без битых ссылок.
        """
        items = self._res_render_items.get(1)
        if items is not None:
            return items
        c1 = self.results_plot.plot(
            [], [], pen=pg.mkPen(Style.ACC_TRACE_COLOR_1, width=1),
            symbol=self.RES_SYMBOL, symbolSize=self.RES_SYMBOL_SIZE,
            symbolBrush=Style.ACC_TRACE_COLOR_1,
            symbolPen=pg.mkPen(Style.ACC_TRACE_COLOR_1, width=0.5))
        c2 = self.results_plot.plot(
            [], [], pen=pg.mkPen(Style.ACC_TRACE_COLOR_2, width=1),
            symbol=self.RES_SYMBOL, symbolSize=self.RES_SYMBOL_SIZE,
            symbolBrush=Style.ACC_TRACE_COLOR_2,
            symbolPen=pg.mkPen(Style.ACC_TRACE_COLOR_2, width=0.5))
        # Линия выделенной строки: синяя, сплошная, поверх кривых
        sel_line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(Style.MAIN_TRACE_COLOR, width=1.5))
        sel_line.setVisible(False)
        self.results_plot.addItem(sel_line)
        items = [c1, c2, sel_line]
        self._res_render_items[1] = items

        self._m1_res_ensure_label()
        return items

    def _m1_res_ensure_label(self) -> None:
        """Создать надпись уровней (один раз на жизнь окна) и привязать
        перепозиционирование к ресайзу графика.

        Надпись — сценическая (позиция в пикселях), как метки CF/Span:
        при пане/зуме полоса оси top не смещается, пересчитывать нужно
        только на изменение геометрии. В _results_reset не удаляется,
        а прячется — ссылка живёт в self._m1_res_label.
        """
        if getattr(self, '_m1_res_label', None) is None:
            self._m1_res_label = pg.TextItem(
                text='', color=Style.MAIN_TRACE_COLOR, anchor=(0.5, 1))
            self._m1_res_label.setVisible(False)
            self.results_plot.scene().addItem(self._m1_res_label)
        if not getattr(self, '_m1_res_lbl_bound', False):
            self.results_plot.getPlotItem().getViewBox().sigResized.connect(
                self._m1_res_place_label)
            self.results_plot.getPlotItem(
            ).getViewBox().sigRangeChanged.connect(
                self._m1_res_update_selection)
            self._m1_res_lbl_bound = True

        if not getattr(self, '_m1_res_click_bound', False):
            self.results_plot.scene().sigMouseClicked.connect(
                self._m1_res_on_click)
            self._m1_res_click_bound = True

    def _m1_res_place_label(self) -> None:
        """Надпись уровней: центр полосы оси top или край при уходе
        линии за видимую область (см. _m1_res_lbl_edge)."""
        lbl = getattr(self, '_m1_res_label', None)
        if lbl is None or not lbl.isVisible():
            return
        rect = self.results_plot.getPlotItem().getViewBox(
            ).sceneBoundingRect()
        edge = getattr(self, '_m1_res_lbl_edge', None)
        if edge == 'left':
            lbl.setPos(rect.left() + 2, rect.top() - 2)
        elif edge == 'right':
            lbl.setPos(rect.right() - 2, rect.top() - 2)
        else:
            lbl.setPos(rect.center().x(), rect.top() - 2)

    def _m1_res_load_snapshot(self, ev) -> None:
        """Двойной клик: загрузить снимок строки на основной график.

        Имя файла — по соглашению автоснимков метода 1:
        '<частота>.json' в рабочей директории, частота — МГц с одним
        знаком после запятой без округления (_m1_file_freq).
        Загрузка выполняется тем же кодом, что кнопкой
        but_open_screen_data (см. _load_screen_file).
        """
        vb = self.results_plot.getPlotItem().getViewBox()
        if not vb.sceneBoundingRect().contains(ev.scenePos()):
            return
        t = self._m1_table
        n = t.rowCount()
        if n == 0:
            return
        row = max(0, min(n - 1, int(round(vb.mapSceneToView(
            ev.scenePos()).x() - 1))))
        it = t.item(row, 0)
        if it is None:
            return
        try:
            freq_hz = float(it.text().replace(',', '.')) * 1e6
        except ValueError:
            return
        path = os.path.join(self.work_dir(),
                            f'{self._m1_file_freq(freq_hz)}.json')
        if not os.path.exists(path):
            # Показ: частота — МГц (freq_hz → /1e6), путь — в едином
            # виде разделителей (normpath), иначе сообщение смешает
            # слэши разных направлений
            QMessageBox.information(
                self, 'Метод измерений 1',
                f'Снимок для {self._m1_fmt_mhz(freq_hz / 1e6)} МГц '
                f'не найден:\n{os.path.normpath(path)}')
            return
        self._load_screen_file(path)

    def _m1_res_on_click(self, ev) -> None:
        """Клик по полотну результатов: выделить ближайшую строку таблицы.

        Только метод 1 и вне прогона S/N (_m1_seq — замок). Точка
        переводится в координаты оси X; строка выбирается ближайшей
        по номеру (тики 1…N стоят ровно на x строк). Выделение
        триггерит itemSelectionChanged — линия и надпись обновятся
        штатным путём, отдельной перерисовки не нужно.
        """
        if getattr(self, '_m1_seq', None) is not None:
            return   # идёт измерение — мышь на графике не меняет выделение
        if getattr(self, '_active_method_num', None) != 1:
            return
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        if ev.double():
            self._m1_res_load_snapshot(ev)
            return
        vb = self.results_plot.getPlotItem().getViewBox()
        if not vb.sceneBoundingRect().contains(ev.scenePos()):
            return   # клик мимо полотна (например, в полосу оси top)
        n = self._m1_table.rowCount()
        if n == 0:
            return
        x = vb.mapSceneToView(ev.scenePos()).x()
        row = int(round(x - 1))          # строка i ↔ x = i + 1
        row = max(0, min(n - 1, row))
        self._m1_select_row(row)

    def results_refresh_m1(self) -> None:
        """Перестроить кривые по таблице метода 1 и подогнать шкалу Y.

        X — номера строк (1…N); края окна совпадают с крайними точками:
        первая лежит на оси Y, последняя — на правой границе сетки.
        Ось Y — тики кратно 10 между границами шкалы (ближайшие кратные
        5, строго вне данных). Пустая ячейка даёт точку на y_min.
        """
        c1, c2, _sel_line = self._m1_res_items()
        t = getattr(self, '_m1_table', None)
        n = t.rowCount() if t is not None else 0
        axis_bottom = self.results_plot.getAxis('bottom')

        if n == 0:
            self._results_reset()
            return

        x = list(range(1, n + 1))
        y1 = self._results_column(t, 1)
        y2 = self._results_column(t, 2)

        nums = [v for v in (y1 + y2) if v is not None]
        if not nums:
            if self._res_y_min is None:
                # Ни одного значения и шкалы ещё нет — рисовать нечего
                c1.setData([], [])
                c2.setData([], [])
                axis_bottom.setTicks([[(i, str(i)) for i in x]])
                self._m1_res_update_selection()
                return
            ymin, ymax = self._res_y_min, self._res_y_max
        else:
            ymin = self._floor5(min(nums))
            ymax = self._ceil5(max(nums))

        self._res_y_min, self._res_y_max = ymin, ymax

        c1.setData(x, [v if v is not None else ymin for v in y1])
        c2.setData(x, [v if v is not None else ymin for v in y2])
        axis_bottom.setTicks([[(i, str(i)) for i in x]])
        self.results_plot.getPlotItem().getViewBox().setLimits(
            xMin=1, xMax=n)
        self.results_plot.setRange(
            xRange=(1, n), yRange=(ymin, ymax), padding=0)
        self.results_plot.showGrid(x=False, y=False)
        self._place_res_grid(x, ymin, ymax)
        self.results_plot.getAxis('left').setTicks(
            [self._res_y_ticks(ymin, ymax)])
        self._m1_res_update_selection()

    # --- Выделенная строка: линия и надпись уровней -----------------------

    def _m1_res_sel_row(self, n: int) -> int | None:
        """Индекс строки для линии: подсветка прогона, затем выделение.

        Подсветка прогона приоритетнее мышиного выделения: во время
        S/N линия ведёт за жёлтой строкой, после завершения —
        возвращается к выделенной. Из выделенных берётся первая
        (минимальный индекс).
        """
        hl = getattr(self, '_m1_hl_row', None)
        if hl is not None and hl < n:
            return hl
        rows = sorted({i.row() for i in self._m1_table.selectedIndexes()})
        return rows[0] if rows and rows[0] < n else None

    def _m1_res_update_selection(self) -> None:
        """Линия выделенной строки и надпись её уровней над полотном.

        Молчит, если рендер ещё не создавался или сброшен (нет в
        _res_render_items) — линия появится при ближайшем refresh.
        """
        if getattr(self, '_res_render_items', None) is None \
                or 1 not in self._res_render_items:
            return
        t = self._m1_table
        n = t.rowCount()
        sel_line = self._res_render_items[1][2]
        row = self._m1_res_sel_row(n)
        if row is None:
            sel_line.setVisible(False)
            lbl = getattr(self, '_m1_res_label', None)
            if lbl is not None:
                lbl.setVisible(False)
            return

        # Линия — в координатах данных: x строки = row + 1
        sel_line.setPos(row + 1)
        sel_line.setVisible(True)

        # Надпись: частота и уровни Usn/Un строки; если линия вне
        # видимой области — текст у соответствующего края со стрелкой
        unit = getattr(self, '_current_amp_unit', None)
        if not unit:
            combo = getattr(self, 'amp_unit', None)
            unit = combo.currentText().strip() if combo is not None else ''

        def cell(col: int) -> str:
            it = t.item(row, col)
            txt = it.text().strip() if it is not None else ''
            return txt if txt else '—'

        lbl = self._m1_res_label

        text = (f'F = {cell(0)} МГц    '
                f'Usn = {cell(1)} {unit or "—"}    '
                f'Un = {cell(2)} {unit or "—"}')

        vb = self.results_plot.getPlotItem().getViewBox()
        x0, x1 = vb.viewRange()[0]
        rect = vb.sceneBoundingRect()
        sel_x = row + 1
        if sel_x < x0:
            self._m1_res_lbl_edge = 'left'
            lbl.setAnchor((0, 1))
            lbl.setText('← ' + text)
            lbl.setPos(rect.left() + 2, rect.top() - 2)
        elif sel_x > x1:
            self._m1_res_lbl_edge = 'right'
            lbl.setAnchor((1, 1))
            lbl.setText(text + ' →')
            lbl.setPos(rect.right() - 2, rect.top() - 2)
        else:
            self._m1_res_lbl_edge = None
            lbl.setAnchor((0.5, 1))
            lbl.setText(text)
            lbl.setPos(rect.center().x(), rect.top() - 2)
        lbl.setVisible(True)

    @staticmethod
    def _results_column(t, col: int) -> list:
        """Столбец col таблицы списком float/None (пустая ячейка — None)."""
        out = []
        for r in range(t.rowCount()):
            it = t.item(r, col)
            txt = it.text().strip() if it is not None else ''
            try:
                out.append(float(txt.replace(',', '.')))
            except ValueError:
                out.append(None)
        return out
