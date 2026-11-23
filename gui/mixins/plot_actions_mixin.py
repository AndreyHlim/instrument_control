import json

import numpy as np
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QToolButton,
                             QVBoxLayout, QWidget)

from constants import (ADD_TRACE_MODE, DETECTORS_FSVA_REV, MARKER_TRACES,
                       TRACE_ACC_REV, TRACE_HOLD, TRACE_OFF)
from function import resource_path
from gui.styles import (COL_SPACING, COL_TOP, PLOT_ACTIONS_STRIP_W,
                        PLOT_BTN_GAP, PLOT_BTN_ICON_SIZE, PLOT_BTN_SIZE, Style)


class PlotActionsMixin:
    """Миксин: колонка кнопок поверх правого края основного графика.

    Кнопки — плавающий ребёнок plotWidget (приём как у панели шкалы
    водопада): живут в пустой полосе правого поля осей, внутри рамки
    графика, не входят ни в какой layout.
    """

    ACTIONS = (
        ('but_screen', 'screen.png', 'Сохранить график в PNG'),
        ('but_export_file', 'to_txt.png', 'Экспорт трассы в TXT/JSON'),
        ('but_open_screen_data', 'open_screen.png', 'Открыть данные экрана'),
        ('but_pausa', 'pausa.png', 'Пауза'),
    )

    def settings_plot_actions(self) -> None:
        """Создать плавающую колонку кнопок поверх plotWidget.

        Вызывается после settings_plot: правое поле осей уже расширено
        под полосу кнопок (PLOT_ACTIONS_STRIP_W), геометрия виджета
        ещё нулевая — позиционирование делается в singleShot(0) и далее
        по каждому resize (eventFilter PlotMixin).
        """
        col = QWidget(self.plotWidget)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(COL_SPACING)
        self._paused = False

        self._plot_action_btns = {}
        for name, icon_file, tip in self.ACTIONS:
            btn = QToolButton(col)
            btn.setObjectName(name)
            btn.setToolTip(tip)
            btn.setStyleSheet(Style.BUT_ICON)
            btn.setFixedSize(PLOT_BTN_SIZE, PLOT_BTN_SIZE)
            btn.setIcon(QIcon(resource_path(f'gui/icons/{icon_file}')))
            btn.setIconSize(QSize(PLOT_BTN_ICON_SIZE, PLOT_BTN_ICON_SIZE))
            if name == 'but_pausa':
                btn.setCheckable(True)
                btn.setIcon(self._pausa_icon())
                btn.toggled.connect(self._on_pausa_toggled)
            else:
                btn.clicked.connect(getattr(self, f'_{name}_clicked'))
            lay.addWidget(btn)
            self._plot_action_btns[name] = btn
        # Без addStretch: колонка ровно по высоте кнопок, не растягивается

        col.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        col.raise_()
        self._plot_actions_col = col
        QTimer.singleShot(0, self._place_plot_actions_col)

    def _pausa_icon(self) -> QIcon:
        """Иконка паузы: Off — pausa.png, On (нажата) — play.png."""
        icon = QIcon()
        icon.addPixmap(QPixmap(resource_path('gui/icons/pausa.png')),
                       QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(QPixmap(resource_path('gui/icons/play.png')),
                       QIcon.Mode.Normal, QIcon.State.On)
        return icon

    def _on_pausa_toggled(self, checked: bool) -> None:
        """Переключение паузы кнопкой."""
        self._paused = checked

    def _set_paused(self, paused: bool) -> None:
        """Установить паузу, синхронизировав кнопку без рекурсии."""
        if self._paused == paused:
            return
        self._paused = paused
        btn = self._plot_action_btns.get('but_pausa')
        if btn is not None:
            btn.blockSignals(True)   # setChecked вызовет toggled — глушим
            btn.setChecked(paused)
            btn.blockSignals(False)

    def _ensure_unpaused(self) -> None:
        """Снять паузу при действии, влияющем на отображение."""
        self._set_paused(False)

    def _user_send(self, cmd: str) -> None:
        """Команда прибора, влияющая на отображение: сначала снять паузу.

        Пауза — только GUI: прибору ничего не запрещается, но любое
        пользовательское изменение параметров экрана её сбрасывает,
        иначе изменённое значение будет «заморожено» до снятия паузы.
        """
        self._ensure_unpaused()
        if self._trace_worker is not None:
            self._trace_worker.send_command(cmd)

    def _place_plot_actions_col(self) -> None:
        """Уложить колонку в пустую полосу правого поля осей.

        Полоса — последние PLOT_ACTIONS_STRIP_W пикселей ширины виджета.
        Кнопки центрируются в ней; рамка графика остаётся правее всех
        кликабельных зон, кнопки не её перекрывают.
        """
        col = getattr(self, '_plot_actions_col', None)
        if col is None:
            return
        w = self.plotWidget
        if w.width() < PLOT_ACTIONS_STRIP_W:
            col.setVisible(False)
            return
        strip_left = w.width() - PLOT_ACTIONS_STRIP_W
        x = strip_left + PLOT_BTN_GAP   # ровно PLOT_BTN_GAP от рамки
        col.setGeometry(x, COL_TOP, PLOT_BTN_SIZE,
                        col.sizeHint().height())
        col.setVisible(True)
        col.raise_()   # поверх рамки-накладки после её raise_ в settings_plot

    # --- Обработчики (часть — заглушки, наполнение позже) ---------------
    def _but_screen_clicked(self) -> None:
        """Диалог сохранения графика в PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить график', 'trace', 'PNG (*.png)')
        if not path:
            return
        if not path.lower().endswith('.png'):
            path += '.png'
        self.plotWidget.grab().save(path)

    def _collect_export_data(self) -> dict:
        """Собрать снимок кадра для экспорта: параметры + данные трасс.

        Возвращает сырые значения (Гц, дБ, коды прибора) — строки
        формируют рендеры TXT/JSON. Источники: кэш кадра PlotMixin,
        буферы AccTracesMixin, состояния маркеров MarkersMixin.
        """
        freqs = getattr(self, '_last_freqs', None)
        levels = getattr(self, '_last_levels', None)
        if freqs is None or levels is None or len(freqs) != len(levels):
            freqs = levels = None
        else:
            freqs = [self._round_hz(f) for f in freqs]

        traces = {}
        for n in (1, 2):
            mode = self._acc_mode(n)
            arr = fqs = None
            if mode != TRACE_OFF:
                entry = getattr(self, '_acc_traces', {}).get(n)
                if entry is not None:
                    arr = entry.get('arr')
                    fqs = entry.get('freqs')
            traces[n] = {
                'on': mode != TRACE_OFF,
                'mode': mode,
                'acc_kind': self._acc_kind_text(n),
                'arr': arr if arr is not None and fqs is not None else None,
                'freqs': ([self._round_hz(f) for f in fqs]
                          if fqs is not None else None),
            }

        markers = {}
        for n in (1, 2):
            entry = getattr(self, '_marker_entries', {}).get(n, {})
            line = entry.get('line')
            markers[n] = {
                'on': line is not None and line.isVisible(),
                'trc': MARKER_TRACES[entry.get('trace_idx', 1) - 1],
                'freq': self._round_hz(entry.get('freq')),
            }

        return {
            'freq_start': self._round_hz(self._current_x_min),
            'freq_stop': self._round_hz(self._current_x_max),
            'span': (self._round_hz(self._current_x_max - self._current_x_min)
                     if self._current_x_min is not None else None),
            'rbw': self._round_hz(getattr(self, '_rbw_hz', None)),
            'vbw': self._round_hz(getattr(self, '_vbw_hz', None)),
            'det': self._main_trace_det,
            'acc': self._main_trace_acc,
            'traces': traces,
            'markers': markers,
            'ref_lvl': self._current_reflevel,
            'range': self._current_range,
            'amp_unit': self._current_amp_unit,
            'freqs': freqs,
            'levels': levels,
        }

    def _acc_kind_text(self, num: int) -> str:
        """Текст типа накопления трассы num из её комбобокса."""
        combo = getattr(self, f'trc_{num}_acc', None)
        return combo.currentText() if combo is not None else ''

    def _but_export_file_clicked(self) -> None:
        """Диалог экспорта кадра: TXT или JSON — по выбранному фильтру."""
        d = self._collect_export_data()
        path, flt = QFileDialog.getSaveFileName(
            self, 'Экспорт данных', 'trace',
            'Текст с разделителями (*.txt);;JSON (*.json)')
        if not path:
            return
        if 'JSON' in flt and not path.lower().endswith('.json'):
            path += '.json'
        elif 'JSON' not in flt and not path.lower().endswith('.txt'):
            path += '.txt'
        if path.lower().endswith('.json'):
            self._export_json(path, d)
        else:
            self._export_txt(path, d)

    @staticmethod
    def _fmt_opt(fmt, value) -> str:
        """Значение строкой или '—', если оно ещё не приходило."""
        return '—' if value is None else fmt(value)

    @staticmethod
    def _fmt_amp(v) -> str:
        """Амплитуда ячейкой: фиксированные 4 знака; NaN/None — пустая."""
        if v is None or v != v:   # NaN не равен сам себе
            return ''
        return f'{float(v):.4f}'

    @staticmethod
    def _round_hz(value) -> float | None:
        """Частота с точностью 1 Гц (квантуем округлением), None — как есть."""
        return None if value is None else float(round(value))

    def _export_txt(self, path: str, d: dict) -> None:
        """Записать кадр в TXT: параметры, затем столбцы через \\t."""
        fmt = self._format_freq
        det = d['det']
        acc = d['acc']
        det_txt = DETECTORS_FSVA_REV.get(det, det) if det else '—'
        acc_txt = TRACE_ACC_REV.get(acc, acc) if acc else '—'
        unit = d['amp_unit'] or '—'

        lines = [
            f'Начало диапазона: {self._fmt_opt(fmt, d["freq_start"])}',
            f'Конец диапазона: {self._fmt_opt(fmt, d["freq_stop"])}',
            f'Ширина обзора: {self._fmt_opt(fmt, d["span"])}',
            f'RBW / VBW: {self._fmt_opt(fmt, d["rbw"])} / '
            f'{self._fmt_opt(fmt, d["vbw"])}',
            f'Основная трасса: {det_txt}, {acc_txt}',
        ]
        for n in (1, 2):
            t = d['traces'][n]
            if t['on']:
                suffix = ' (hold)' if t['mode'] == TRACE_HOLD else ''
                lines.append(
                    f'Трасса {n}: {det_txt}, {t["acc_kind"] or "—"}{suffix}')
            else:
                lines.append(f'Трасса {n}: отсутствует')
        for n in (1, 2):
            m = d['markers'][n]
            if m['on'] and m['freq'] is not None:
                lines.append(
                    f'Маркер {n}: {m["trc"].lower()}, '
                    f'частота: {fmt(m["freq"])}')
            else:
                lines.append(f'Маркер {n}: отсутствует')
        ref, rng = d['ref_lvl'], d['range']
        lines.append(
            f'Ref lvl, range: '
            f'{f"{ref:g} {unit}" if ref is not None else "—"}, '
            f'{f"{rng:g} dB" if rng is not None else "—"}')
        lines.append('Графики:')

        # Столбцы: частота + основная + включённые трассы
        freqs, levels = d['freqs'], d['levels']
        cols = []
        if freqs is not None:
            cols.append(('частота, Hz',
                         [f'{f:.0f}' for f in freqs]))
            if levels is not None:
                cols.append((f'Основной, {unit}',
                             [self._fmt_amp(v) for v in levels]))
            for n in (1, 2):
                t = d['traces'][n]
                if t['on'] and t['arr'] is not None \
                        and self._trace_intersects(freqs, t):
                    cols.append(
                        (f'Трасса {n}, {unit}',
                         self._trace_txt_column(freqs, t)))

        if cols:
            lines.append('\t'.join(h for h, _ in cols))
            for row in zip(*(vals for _, vals in cols)):
                lines.append('\t'.join(row))

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    def _export_json(self, path: str, d: dict) -> None:
        """Записать кадр в JSON: коды прибора и сырые значения.

        Частотные значения (Гц) несут суффикс _hz в имени ключа —
        размерность зашита в контракт формата.
        """
        det = d['det']
        traces = {}
        for n in (1, 2):
            t = d['traces'][n]
            traces[f'trace_{n}'] = {
                'on': t['on'],
                'trc_det': det,
                'trc_acc': (ADD_TRACE_MODE.get(t['acc_kind'])
                            if t['acc_kind'] else None),
            }

        markers = {}
        for n in (1, 2):
            m = d['markers'][n]
            markers[f'marker_{n}'] = {
                'on': m['on'] and m['freq'] is not None,
                'trc': m['trc'],
                'freq_hz': m['freq'] if m['on'] else None,
            }

        payload = {
            'freq_start_hz': d['freq_start'],
            'freq_stop_hz': d['freq_stop'],
            'span_hz': d['span'],
            'rbw_hz': d['rbw'],
            'vbw_hz': d['vbw'],
            'trace_0': {'on': d['freqs'] is not None,
                        'trc_det': det, 'trc_acc': d['acc']},
            **traces,
            **markers,
            'ref_lvl': d['ref_lvl'],
            'ampl_unit': d['amp_unit'],
            'range': d['range'],
        }
        for key, (f_arr, v_arr) in (
                ('trc_0_data', (d['freqs'], d['levels'])),
                ('trc_1_data', (d['traces'][1]['freqs'],
                                d['traces'][1]['arr'])),
                ('trc_2_data', (d['traces'][2]['freqs'],
                                d['traces'][2]['arr']))):
            payload[key] = ([[f, a] for f, a in zip(f_arr, v_arr)]
                            if f_arr is not None and v_arr is not None else [])

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)

    def _trace_txt_column(self, main_freqs, t: dict) -> list[str]:
        """Столбец трассы для TXT: значения на сетке основной трассы.

        On-трасса лежит на сетке кадра — интерполяция возвращает
        значения точка-в-точку. Hold-трасса со своей (замороженной)
        сеткой: внутри её диапазона — линейная интерполяция, за
        пределами — пустая ячейка (данных нет).
        """
        fa = np.asarray(t['freqs'], dtype=float)
        la = np.asarray(t['arr'], dtype=float)
        if fa[0] > fa[-1]:               # интерполяция требует возрастания X
            fa, la = fa[::-1], la[::-1]

        # NaN в буфере — заполнить интерполяцией по валидным точкам,
        # иначе np.interp протащит NaN в середину диапазона
        if np.isnan(la).any():
            idx = np.arange(len(la))
            valid = np.isfinite(la)
            if not valid.any():
                return [''] * len(main_freqs)
            la = np.interp(idx, idx[valid], la[valid])

        targets = np.asarray(main_freqs, dtype=float)
        in_range = (targets >= fa[0]) & (targets <= fa[-1])
        vals = np.interp(targets[in_range], fa, la)

        col = [''] * len(targets)
        it = iter(vals)
        for i, ok in enumerate(in_range):
            if ok:
                col[i] = self._fmt_amp(next(it))
        return col

    @staticmethod
    def _trace_intersects(main_freqs, t: dict) -> bool:
        """Есть ли пересечение сетки трассы с окном основной трассы.

        Замороженная (hold) трасса, целиком ушедшая за экран, столбца
        в TXT не получает: колонка из одних пустых ячеек — визуальный
        шум. В JSON она сохраняется как раньше, без обрезки.
        """
        fa = t['freqs']
        lo, hi = (fa[0], fa[-1]) if fa[0] <= fa[-1] else (fa[-1], fa[0])
        return hi >= main_freqs[0] and lo <= main_freqs[-1]

    def _but_open_screen_data_clicked(self) -> None:
        """Заглушка: открытие сохранённых данных экрана."""
        print('[PLOT ACTIONS] open screen data')
        QMessageBox.information(
            self, 'Открыть данные скриншота',
            'В разработке...'
        )
