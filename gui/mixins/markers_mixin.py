from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QPainter,
                         QPainterPath, QPen)
from PyQt6.QtWidgets import QGraphicsObject

from constants import MARKER_TRACES, TRACE_OFF, TRACE_ON
from gui.styles import PLOT_LABEL_FONT_FAMILY, Style


class MarkerLabelItem(QGraphicsObject):
    """Ярлычок маркера: перевёрнутый пятиугольник-«домик» с текстом.

    Добавляется прямо в сцену (координаты — пиксельные, как у меток
    CF/Span). Тянется левой кнопкой мыши; наружу идут координаты X
    в координатах данных — миксин сам решает, что с ними делать.
    """

    drag_started = pyqtSignal()
    drag_moved = pyqtSignal(float)      # X в координатах данных

    W, H, TIP = 24.0, 15.0, 9.0        # ширина, высота, остриё

    def __init__(self, text: str, color: str, vb):
        super().__init__()
        self._text = text
        self._color = color
        self._vb = vb
        self._drag = False
        self._font = QFont(PLOT_LABEL_FONT_FAMILY)
        self._font.setPointSizeF(9)
        self._font.setBold(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)
        self.setZValue(20)      # поверх сетки и трасс

    def boundingRect(self) -> QRectF:
        return QRectF(-2, -2, self.W + 4, self.H + self.TIP + 4)

    def paint(self, p: QPainter, option, widget=None) -> None:
        w, h, tip = self.W, self.H, self.TIP
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.lineTo(w / 2, h + tip)      # остриё вниз — «домик вверх ногами»
        path.lineTo(0, h)
        path.closeSubpath()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(path, QBrush(QColor(self._color)))
        p.setFont(self._font)
        p.setPen(QPen(QColor('#ffffff')))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter,
                   self._text)

    def hoverEnterEvent(self, ev) -> None:
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        ev.accept()

    def hoverLeaveEvent(self, ev) -> None:
        self.unsetCursor()
        ev.accept()

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag = True
            self.drag_started.emit()
            ev.accept()
        else:
            ev.ignore()

    def mouseMoveEvent(self, ev) -> None:
        if not self._drag:
            ev.ignore()
            return
        self.drag_moved.emit(self._vb.mapSceneToView(ev.scenePos()).x())
        ev.accept()

    def mouseReleaseEvent(self, ev) -> None:
        if self._drag:
            self._drag = False
            ev.accept()
        else:
            ev.ignore()


class MarkersMixin:
    """Миксин: маркеры М1/М2 — контролы секции sec_mrk и линии на графике.

    Предполагается, что у окна есть:
    - self.sec_mrk (декларативная секция из fsva_ctrl.SECTION_MRK);
    - self.plotWidget, self._trace_worker;
    - атрибуты _current_x_min/_current_x_max/_current_y_max,
      _last_freqs/_last_levels (PlotMixin), _acc_traces (AccTracesMixin).

    Маркеры прибора (1 и 2) всегда сидят на его единственной трассе;
    комбобокс «трасса маркера» влияет только на источник данных для
    поиска пика: основная — кэш кадра прибора, Трасса 1/2 —
    накопительные буферы доп. трасс (существуют только в программе).
    """

    # Место появления по умолчанию: М1 между 3-й и 4-й линией сетки,
    # М2 — между 6-й и 7-й (сетка: 10 делений)
    DEF_FRAC = {1: 0.35, 2: 0.65}

    def settings_markers(self) -> None:
        """Присвоить ссылки на виджеты sec_mrk и подключить сигналы.

        Вызывается после set_layout_left (по образцу
        initialization_form_elements_fsva), но до создания линий:
        они лениво создаются при первом включении маркера.
        """
        w = self.sec_mrk.widgets
        self.but_mrk_1 = w['but_mrk_1']
        self.but_mrk_2 = w['but_mrk_2']
        self.combo_mrk_trace = w['combo_mrk_trace']
        self.chk_mrk_hold = w['chk_mrk_hold']
        self.but_mrk_peak = w['but_mrk_peak']
        self.but_mrk_next_peak = w['but_mrk_next_peak']
        self.chk_mrk_autopeak = w['chk_mrk_autopeak']
        self.but_mrk_to_center = w['but_mrk_to_center']
        self.but_mrk_span_delta = w['but_mrk_span_delta']
        self.but_mrk_delta_center = w['but_mrk_delta_center']
        self.but_mrk_all_off = w['but_mrk_all_off']

        self._marker_btns = {1: self.but_mrk_1, 2: self.but_mrk_2}
        self._marker_entries: dict[int, dict] = {}
        for num in (1, 2):
            self._marker_entries[num] = {
                'line': None, 'label': None,
                'freq': None, 'frac': self.DEF_FRAC[num],
                'hold': False, 'autopeak': False,
                'trace_idx': 1,  # 1 — основная, 2 — трасса 1, 3 — трасса 2
            }
        self._marker_active: int | None = None

        # Видимость маркера меняется ТОЛЬКО кликом пользователя:
        # clicked эмитится только от мыши/клавиатуры и несёт новое
        # состояние (после переключения), в отличие от toggled, который
        # стреляет и при программном setChecked
        for num in (1, 2):
            self._marker_btns[num].clicked.connect(
                lambda checked, n=num: self._on_m_btn_clicked(n, checked))

        self.chk_mrk_hold.toggled.connect(self._on_hold_toggled)
        self.but_mrk_peak.clicked.connect(self._on_peak)
        self.but_mrk_next_peak.clicked.connect(self._on_next_peak)
        self.chk_mrk_autopeak.toggled.connect(self._on_autopeak_toggled)
        self.but_mrk_to_center.clicked.connect(self._on_to_center)
        self.but_mrk_delta_center.clicked.connect(self._on_delta_to_center)
        self.but_mrk_span_delta.clicked.connect(self._on_span_to_delta)
        self.but_mrk_all_off.clicked.connect(self._on_all_off)

        # Контролы активного маркера — заблокированы, пока ни один
        # маркер не включён (спец. пункт 3). All off включён всегда:
        # глобальное действие, безвредное и без маркеров.
        self._marker_ctrls = [
            self.combo_mrk_trace, self.chk_mrk_hold,
            self.but_mrk_peak, self.but_mrk_next_peak,
            self.chk_mrk_autopeak, self.but_mrk_to_center,
            self.but_mrk_delta_center, self.but_mrk_span_delta,
        ]
        self._set_marker_ctrls_enabled(False)

        # Легенда маркеров: две колонки — два TextItem. Один текстовый
        # элемент с HTML-таблицей не годится: QTextDocument распределяет
        # ширину таблицы по содержимому колонок, и при смене частоты
        # граница колонок плывёт. Здесь граница фиксируется вручную
        # (_update_markers_legend пишет её ширину в _legend_name_w)
        self._markers_legend_name = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(0, 0))
        self._markers_legend_val = pg.TextItem(
            text='', color=Style.PLOT_LABEL_COLOR, anchor=(0, 0))
        self._legend_name_w = 0.0
        for item in (self._markers_legend_name, self._markers_legend_val):
            item.setVisible(False)
            self.plotWidget.scene().addItem(item)
        self.combo_mrk_trace.currentTextChanged.connect(
            self._on_mrk_trace_changed)

    def _set_marker_ctrls_enabled(self, enabled: bool) -> None:
        for widget in self._marker_ctrls:
            widget.setEnabled(enabled)

    # --- Вкл/выкл маркера кнопками М1/М2 ---------------------------------
    def _on_m_btn_clicked(self, num: int, checked: bool) -> None:
        """Клик пользователя по кнопке М1/М2.

        Нажатие: маркер num становится активным, его линия показывается
        (создаётся лениво), линия другого маркера остаётся как была.
        Повторный клик по уже нажатой кнопке (checked=False): линия
        маркера num скрывается; если видима линия другого маркера —
        активация переходит к нему, иначе активных нет.

        Args:
            num: номер маркера (1 или 2).
            checked: новое состояние кнопки.
        """
        entry = self._marker_entries[num]
        other = 2 if num == 1 else 1
        if checked:
            # Снять соседнюю кнопку программно: clicked не эмитится,
            # линия другого маркера НЕ прячется
            self._marker_btns[other].setChecked(False)
            self._activate_marker(num)
            if entry['line'] is None:
                x_min, x_max = self._current_x_min, self._current_x_max
                if x_min is not None and entry['freq'] is None:
                    entry['freq'] = x_min + entry['frac'] * (x_max - x_min)
                self._create_marker_item(num)
            entry['line'].setVisible(True)
            entry['label'].setVisible(True)
        else:
            # Повторный клик по активной кнопке: скрыть её линию
            if entry['line'] is not None:
                entry['line'].setVisible(False)
                entry['label'].setVisible(False)
            other_entry = self._marker_entries[other]
            if other_entry['line'] is not None \
                    and other_entry['line'].isVisible():
                # Активация переходит к видимому маркеру: кнопку соседа
                # включаем программно (clicked молчит), состояние — хелпером
                self._marker_btns[other].setChecked(True)
                self._activate_marker(other)
            else:
                self._marker_active = None
                self._set_marker_ctrls_enabled(False)
        self._update_markers_legend()

    def _activate_marker(self, num: int) -> None:
        """Сделать маркер num активным и синхронизировать чекбоксы."""
        entry = self._marker_entries[num]
        self._marker_active = num

        # Комбобокс отражает трассу активного маркера. setCurrentText
        # триггерит _on_mrk_trace_changed, тот запишет в entry то же
        # значение — безвредно, и легенда обновится сама
        self.combo_mrk_trace.setCurrentText(
            MARKER_TRACES[entry['trace_idx'] - 1])

        self.chk_mrk_hold.blockSignals(True)
        self.chk_mrk_hold.setChecked(entry['hold'])
        self.chk_mrk_hold.blockSignals(False)
        self.chk_mrk_autopeak.blockSignals(True)
        self.chk_mrk_autopeak.setChecked(entry['autopeak'])
        self.chk_mrk_autopeak.blockSignals(False)
        self._set_marker_ctrls_enabled(True)

    def _create_marker_item(self, num: int) -> None:
        """Создать линию и ярлычок маркера (однократно)."""
        color = Style.MARKER_COLOR_1 if num == 1 else Style.MARKER_COLOR_2
        entry = self._marker_entries[num]
        line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(color, width=1, style=Qt.PenStyle.DashLine))
        self.plotWidget.addItem(line)
        vb = self.plotWidget.getPlotItem().getViewBox()
        label = MarkerLabelItem(f'М{num}', color, vb)
        label.drag_started.connect(lambda n=num: self._on_label_drag_start(n))
        label.drag_moved.connect(
            lambda x, n=num: self._on_label_drag_move(n, x))
        self.plotWidget.scene().addItem(label)
        entry['line'] = line
        entry['label'] = label
        self._place_marker_line(num)

    # --- Геометрия -------------------------------------------------------
    def _place_marker_line(self, num: int) -> None:
        entry = self._marker_entries[num]
        if entry['line'] is None or self._current_x_min is None:
            return
        vb = self.plotWidget.getPlotItem().getViewBox()
        x_min, x_max = vb.viewRange()[0]   # видимая область, не трасса
        x = min(max(entry['freq'], x_min), x_max)
        entry['line'].setPos(x)
        if self._current_y_max is not None:
            top = vb.mapViewToScene(QPointF(x, self._current_y_max))
            entry['label'].setPos(
                top.x() - entry['label'].W / 2,
                top.y() - entry['label'].H - entry['label'].TIP)

    def _markers_view_changed(
            self, x_min: float | None = None,
            x_max: float | None = None) -> None:
        """Реакция на смену видимой области X (спан/зум/кадр прибора).

        Hold: частота пересчитывается из зафиксированной доли видимого
        окна — маркер «прилипает» к сетке. Без hold частота неизменна,
        линия прижимается к краю окна, если частота ушла за экран.

        Args:
            x_min, x_max: видимая область; None — взять текущую из
                ViewBox (вызов без аргументов из update_state).
        """
        if not getattr(self, '_marker_entries', None):
            return   # settings_markers ещё не выполнялся

        vb = self.plotWidget.getPlotItem().getViewBox()
        if x_min is None or x_max is None:
            (x_min, x_max), _ = vb.viewRange()
        span = x_max - x_min
        if span <= 0:
            return
        changed = False
        for num in (1, 2):
            entry = self._marker_entries[num]
            if entry['line'] is None or not entry['line'].isVisible():
                continue
            if entry['hold']:
                freq = x_min + entry['frac'] * span
                if freq != entry['freq']:
                    entry['freq'] = freq
            elif entry['freq'] is not None:
                # Выход за обзор — прилипание к краю: частота становится
                # крайним значением видимой области и следует за ним,
                # пока обзор не вернётся к ней
                if entry['freq'] < x_min:
                    entry['freq'] = x_min
                    changed = True
                elif entry['freq'] > x_max:
                    entry['freq'] = x_max
                    changed = True
            self._place_marker_line(num)

        if changed:
            self._update_markers_legend()

    def _markers_reposition(self) -> None:
        """Перепривязать ярлычки при resize/смене Y-диапазона."""
        if not getattr(self, '_marker_entries', None):
            return   # settings_markers ещё не выполнялся
        for num in (1, 2):
            entry = self._marker_entries[num]
            if entry['line'] is not None and entry['line'].isVisible():
                self._place_marker_line(num)

        self._place_markers_legend()

    # --- Перетаскивание ярлычка ------------------------------------------
    def _on_label_drag_start(self, num: int) -> None:
        # Активировать маркер ярлычка: кнопки синхронизируем программно
        # (clicked молчит), активность — хелпером
        other = 2 if num == 1 else 1
        if not self._marker_btns[num].isChecked():
            self._marker_btns[other].setChecked(False)
            self._marker_btns[num].setChecked(True)
        self._activate_marker(num)
        self._disable_autopeak(num)

    def _on_label_drag_move(self, num: int, x: float) -> None:
        x_min, x_max = self._current_x_min, self._current_x_max
        if x_min is None or x_max <= x_min:
            return
        entry = self._marker_entries[num]
        x = min(max(x, x_min), x_max)
        entry['freq'] = x
        entry['frac'] = (x - x_min) / (x_max - x_min)
        self._place_marker_line(num)

    # --- Чекбоксы hold / Auto Peak ---------------------------------------
    def _on_hold_toggled(self, checked: bool) -> None:
        num = self._marker_active
        if num is None:
            return
        entry = self._marker_entries[num]
        entry['hold'] = checked
        if checked and self._current_x_min is not None:
            span = self._current_x_max - self._current_x_min
            if span > 0 and entry['freq'] is not None:
                x = min(max(entry['freq'], self._current_x_min),
                        self._current_x_max)
                entry['frac'] = (x - self._current_x_min) / span

    def _on_autopeak_toggled(self, checked: bool) -> None:
        num = self._marker_active
        if num is None:
            return
        entry = self._marker_entries[num]
        entry['autopeak'] = checked
        if checked:
            if self.chk_mrk_hold.isChecked():
                # Снятие hold штатно через сигнал _on_hold_toggled
                self.chk_mrk_hold.setChecked(False)
            self._marker_autopeak_once(num)

    # --- Поиск пика (локально, по данным программы) -----------------------
    def _trace_data_for_peak(self, trace_idx: int):
        """(freqs, levels) источника пика: 1/2/3 — основной кадр/буферы.

        Основная трасса — кэш кадра. Доп. трассы: On-буфер лежит на
        кадровой сетке, Hold-буфер — на своей, замороженной вместе с
        уровнями (entry['freqs']); при несовпадении с кадровой она
        приоритетнее. None/None — данных или согласованной пары нет.
        """
        freqs = getattr(self, '_last_freqs', None)
        if trace_idx == 1:
            levels = getattr(self, '_last_levels', None)
        else:
            acc = getattr(self, '_acc_traces', None)
            entry = acc.get(trace_idx - 1) if acc else None
            levels = entry.get('arr') if entry else None
            own = entry.get('freqs') if entry else None
            # Hold-буфер со своей сеткой: она приоритетнее кадра
            if own is not None and freqs is not None and own != freqs:
                freqs = own
        if freqs is None or levels is None or len(freqs) != len(levels):
            return None, None
        return freqs, levels

    def _find_peak_freq(self, num: int) -> float | None:
        trace_idx = self._marker_entries[num]['trace_idx']
        freqs, levels = self._trace_data_for_peak(trace_idx)
        if freqs is None or levels is None or len(levels) == 0:
            return None
        levels = np.asarray(levels, dtype=float)
        if not np.isfinite(levels).any():
            return None
        return float(freqs[int(np.nanargmax(levels))])

    def _find_next_peak_freq(self, num: int) -> float | None:
        """Частота следующего пика вниз по амплитуде.

        Собираются все локальные максимумы трассы; текущим считается
        ближайший к положению маркера, а результатом — самый высокий
        пик с амплитудой строго ниже его. При отсутствии текущего
        положения ведёт себя как Peak (максимальный пик).
        """
        trace_idx = self._marker_entries[num]['trace_idx']
        freqs, levels = self._trace_data_for_peak(trace_idx)
        if freqs is None or levels is None or len(levels) < 3:
            return None
        freqs = np.asarray(freqs, dtype=float)
        levels = np.asarray(levels, dtype=float)
        if not np.isfinite(levels).any():
            return None

        # Локальные максимумы: точка не ниже соседей слева и выше справа
        # (>=/> — чтобы плато не зацикливались)
        idx = np.arange(1, len(levels) - 1)
        mask = (
            (levels[idx] >= levels[idx - 1])
            & (levels[idx] > levels[idx + 1]))
        peaks = idx[mask]
        if len(peaks) == 0:
            return None

        cur = self._marker_entries[num]['freq']
        if cur is None:
            # Нет текущего положения — ведём на самый высокий пик
            best = peaks[int(np.argmax(levels[peaks]))]
            return float(freqs[best])

        # Ближайший к маркеру локальный максимум — «текущий пик»
        nearest = peaks[int(np.argmin(np.abs(freqs[peaks] - cur)))]
        cur_lvl = levels[nearest]

        # Самый высокий пик строго ниже текущего
        lower = peaks[levels[peaks] < cur_lvl]
        if len(lower) == 0:
            return None
        best = lower[int(np.argmax(levels[lower]))]
        return float(freqs[best])

    def _marker_autopeak_once(self, num: int) -> None:
        freq = self._find_peak_freq(num)
        if freq is not None:
            self._marker_entries[num]['freq'] = freq
            self._place_marker_line(num)

    def _on_peak(self) -> None:
        if self._marker_active is None:
            return
        self._disable_autopeak(self._marker_active)
        self._marker_autopeak_once(self._marker_active)

    def _on_next_peak(self) -> None:
        num = self._marker_active
        if num is None:
            return
        self._disable_autopeak(num)
        freq = self._find_next_peak_freq(num)
        if freq is not None:
            self._marker_entries[num]['freq'] = freq
            self._place_marker_line(num)

    def _disable_autopeak(self, num: int) -> None:
        """Погасить Auto Peak у маркера num (чекбокс — без петли сигналов)."""
        entry = self._marker_entries[num]
        if entry['autopeak']:
            self.chk_mrk_autopeak.blockSignals(True)
            self.chk_mrk_autopeak.setChecked(False)
            self.chk_mrk_autopeak.blockSignals(False)
            entry['autopeak'] = False

    def _markers_autopeak_step(self) -> None:
        """Вызывается из update_state каждого кадра: двигает Auto Peak."""
        for num in (1, 2):
            entry = self._marker_entries[num]
            if not entry['autopeak'] or entry['line'] is None:
                continue
            if not entry['line'].isVisible():
                continue
            freq = self._find_peak_freq(num)
            if freq is not None and freq != entry['freq']:
                entry['freq'] = freq
                self._place_marker_line(num)

    # --- Кнопки секции -----------------------------------------------------
    def _on_to_center(self) -> None:
        num = self._marker_active
        if num is None:
            return
        freq = self._marker_entries[num]['freq']
        if freq is not None:
            self._send_cmd(f'set_cf:{freq}')

    def _on_delta_to_center(self) -> None:
        """Центрировать CF на середине между маркерами М1/М2."""
        f1 = self._marker_entries[1]['freq']
        f2 = self._marker_entries[2]['freq']
        if f1 is not None and f2 is not None:
            self._send_cmd(f'set_cf:{(f1 + f2) / 2}')

    def _on_span_to_delta(self) -> None:
        """Задать обзор по маркерам: старт — меньшая частота,
        стоп — большая из частот М1/М2."""
        f1 = self._marker_entries[1]['freq']
        f2 = self._marker_entries[2]['freq']
        if f1 is not None and f2 is not None:
            lo, hi = (f1, f2) if f1 <= f2 else (f2, f1)
            self._send_cmd(f'set_freq_start:{lo:.0f}')
            self._send_cmd(f'set_freq_stop:{hi:.0f}')

    def _on_all_off(self) -> None:
        for num in (1, 2):
            entry = self._marker_entries[num]
            if entry['line'] is not None:
                entry['line'].setVisible(False)
                entry['label'].setVisible(False)
            # Снятие кнопки программное: обработчик clicked не сработает,
            # линия уже спрятана выше
            self._marker_btns[num].setChecked(False)
            entry['freq'] = None
            entry['frac'] = self.DEF_FRAC[num]
            entry['hold'] = False
            entry['autopeak'] = False
        self._marker_active = None
        self.chk_mrk_hold.blockSignals(True)
        self.chk_mrk_hold.setChecked(False)
        self.chk_mrk_hold.blockSignals(False)
        self.chk_mrk_autopeak.blockSignals(True)
        self.chk_mrk_autopeak.setChecked(False)
        self.chk_mrk_autopeak.blockSignals(False)
        self._set_marker_ctrls_enabled(False)
        self._update_markers_legend()

    def _on_mrk_trace_changed(self, text: str) -> None:
        """Смена трассы в комбобоксе: присвоить её активному маркеру.

        Выбор выключенной доп. трассы автоматически включает её (On):
        пользователь явно хочет маркер на этой трассе — включение за
        один шаг вместо похода к чекбоксу режима. Если активного
        маркера нет — только перерисовать легенду.
        """
        idx = MARKER_TRACES.index(text) + 1
        num = self._marker_active
        if num is not None:
            self._marker_entries[num]['trace_idx'] = idx
            if idx > 1 and self._acc_mode(idx - 1) == TRACE_OFF:
                combo = getattr(self, f'trc_{idx - 1}_on', None)
                if combo is not None:
                    combo.setCurrentText(TRACE_ON)
        self._update_markers_legend()

    def _place_markers_legend(self) -> None:
        """Привязать обе колонки легенды к левому верхнему углу.

        Колонка значений ставится на ширину колонки имён плюс зазор —
        пиксельная граница, не зависящая ни от панорамирования, ни от
        длины значений.
        """
        name_it = getattr(self, '_markers_legend_name', None)
        if name_it is None:
            return
        vb = self.plotWidget.getPlotItem().getViewBox()
        rect = vb.sceneBoundingRect()
        x, y = rect.left() + 8, rect.top() + 4
        name_it.setPos(x, y)
        self._markers_legend_val.setPos(x + self._legend_name_w + 6.0, y)

    def _acc_trace_info(self, idx: int) -> tuple:
        """(enabled, color, arr, freqs) доп. трассы: idx 0 — трасса 1.

        freqs — сетка буфера этой трассы (у Hold-трассы — своя,
        замороженная вместе с буфером).
        """
        num = idx + 1
        if self._acc_mode(num) == TRACE_OFF:
            return False, None, None, None
        entry = getattr(self, '_acc_traces', {}).get(num)
        if entry is None:
            return False, None, None, None
        return True, self.ACC_TRACE_PEN[num], entry.get('arr'), \
            entry.get('freqs')

    def _amp_at_freq(self, freq: float, levels,
                     freqs=None) -> float | None:
        """Амплитуда трассы levels на частоте freq (линейная интерполяция).

        freqs: частотная сетка этой трассы. None — кэш кадра
        (_last_freqs), это основной график. Доп. трассы передают
        собственную сетку: у Hold-буфера она может не совпадать
        с текущим окном прибора.
        """
        if freqs is None:
            freqs = getattr(self, '_last_freqs', None)
        if freqs is None or levels is None or len(freqs) != len(levels):
            return None
        fa = np.asarray(freqs, dtype=float)
        la = np.asarray(levels, dtype=float)
        if len(fa) < 2:
            return None
        if fa[0] > fa[-1]:               # интерполяция требует возрастания X
            fa, la = fa[::-1], la[::-1]
        if np.isnan(la).any():
            idx = np.arange(len(la))
            valid = np.isfinite(la)
            if not valid.any():
                return None
            la = np.interp(idx, idx[valid], la[valid])
        if freq < fa[0] or freq > fa[-1]:
            return None
        return float(np.interp(freq, fa, la))

    def _legend_value_html(self, value: float, color) -> str:
        """Значение амплитуды, окрашенное в цвет трассы."""
        text = f'{value:.1f}'
        if color:
            return f'<span style="color:{color};">{text}</span>'
        return text

    def _legend_value_html_text(self, text: str, color) -> str:
        """Текст, окрашенный в цвет трассы (для размерности и пр.)."""
        if color:
            return f'<span style="color:{color};">{text}</span>'
        return text

    def _update_markers_legend(self) -> None:
        """Пересобрать легенду маркеров (две колонки — два TextItem).

        Граница колонок пиксельная: ширина самой длинной строки имён,
        измеренная QFontMetricsF. Поэтому смена значения частоты ничего
        не сдвигает. ∆M живёт в колонке имён — по её левому краю.
        """
        name_it = getattr(self, '_markers_legend_name', None)
        if name_it is None:
            return
        val_it = self._markers_legend_val
        visible = [num for num in (1, 2)
                   if self._marker_entries[num]['line'] is not None
                   and self._marker_entries[num]['line'].isVisible()]
        if not visible:
            name_it.setVisible(False)
            val_it.setVisible(False)
            return
        on1, color1, arr1, fr1 = self._acc_trace_info(0)
        on2, color2, arr2, fr2 = self._acc_trace_info(1)

        lines_name = []
        lines_val = []
        plain_names = []   # чистые строки имён — для замера ширины колонки
        for num in visible:
            entry = self._marker_entries[num]
            freq = entry['freq']
            if freq is None:
                continue
            trace_idx = entry['trace_idx']
            name = f'Мrk_{num}' if trace_idx == 1 \
                else f'Мrk_{num}[{trace_idx - 1}]'
            # Цвет ярлычка — цвет маркера; цвет частоты — цвет трассы,
            # на которой маркер стоит
            m_color = Style.MARKER_COLOR_1 if num == 1 \
                else Style.MARKER_COLOR_2
            t_color = Style.MAIN_TRACE_COLOR if trace_idx == 1 \
                else self.ACC_TRACE_PEN[trace_idx - 1]
            segs = []
            last_color = None
            amp = self._amp_at_freq(freq, getattr(self, '_last_levels', None))
            if amp is not None:
                segs.append(self._legend_value_html(
                    amp, Style.MAIN_TRACE_COLOR))
                last_color = Style.MAIN_TRACE_COLOR
            if on1:
                amp1 = self._amp_at_freq(freq, arr1, fr1)
                if amp1 is not None:
                    segs.append(self._legend_value_html(amp1, color1))
                    last_color = color1
            if on2:
                amp2 = self._amp_at_freq(freq, arr2, fr2)
                if amp2 is not None:
                    segs.append(self._legend_value_html(amp2, color2))
                    last_color = color2
            lines_name.append(
                f'<span style="color:{m_color};">{name}:</span>')
            plain_names.append(f'{name}:')
            lines_val.append(
                f'<span style="color:{t_color};">'
                f'{self._format_freq(freq)}</span>')
            lines_name.append('')
            amp_line = ' | '.join(segs)
            unit = getattr(self, '_current_amp_unit', None)
            if segs and unit:
                # Размерность — цветом последнего значения строки
                unit_html = self._legend_value_html_text(unit, last_color)
                amp_line = f'{amp_line} {unit_html}'
            lines_val.append(amp_line)

        if len(visible) == 2:
            f1 = self._marker_entries[1]['freq']
            f2 = self._marker_entries[2]['freq']
            if f1 is not None and f2 is not None:
                lines_name.append(f'∆Mrk = {self._format_freq(abs(f1 - f2))}')
                lines_val.append('')

        name_it.textItem.setHtml('<br>'.join(lines_name))
        val_it.textItem.setHtml('<br>'.join(lines_val))

        # Граница колонок: ширина самой длинной строки имён
        fm = QFontMetricsF(name_it.textItem.font())
        self._legend_name_w = max(
            (fm.horizontalAdvance(s) for s in plain_names),
            default=0.0)
        name_it.setVisible(True)
        val_it.setVisible(True)
        self._place_markers_legend()
