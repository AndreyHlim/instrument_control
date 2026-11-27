import os
from bisect import bisect_left

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView,
                             QMessageBox, QSizePolicy, QTableWidget,
                             QTableWidgetItem)

from constants import DETECTORS_FSVA, TRACE_ON
from gui.controls.methods.method_1 import SECTION_M1_BOTTOM


class M1Table(QTableWidget):
    """Таблица результатов метода 1.

    Delete перехватывается до базового класса: иначе AnyKeyPressed-
    редактирование успело бы очистить ячейку до подтверждения миксина.
    """

    delete_requested = pyqtSignal()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class Method1Mixin:
    """Миксин: секция «Метод измерений 1» — таблица результатов.

    Предполагается, что у окна есть:
    - self.sec_method_1 (PanelsMixin._create_method_sections);
    - self.work_dir (WorkDirMixin);
    - self.label_center, self.label_span (ControlsMixin);
    - self._marker_entries, self._marker_active (MarkersMixin);
    - self._trace_data_for_peak, self._amp_at_freq (MarkersMixin);
    - self._send_cmd (ControlsMixin);
    - self.amp_unit (ControlsMixin — комбобокс размерности амплитуды).

    Первый столбец — частоты в МГц, всегда отсортированы по возрастанию;
    параллельный список _m1_freqs — мера истины по числам (bisect),
    тексты ячеек — только отображение. Дубликаты частот не добавляются.
    """
    # --------- Измерения СИГНАЛОВ и ШУМОВ -----------------------

    _M1_SEQ_CFG = {
        'S': dict(col=1, trace=1, acc='Максимум',
                  det_key='m1_det_s',
                  title='Измерить сигналы',
                  done='Измерения сигналов завершены'),
        'N': dict(col=2, trace=2, acc='Средний',
                  det_key='m1_det_n',
                  title='Измерить шумы',
                  done='Измерения шумов завершены'),
    }

    def settings_method_1(self) -> None:
        """Собрать содержимое секции: таблица, нижний ряд, привязки.

        Схема SECTION_M1 применена циклом панелей до этого вызова;
        таблица вставляется между её рядами и SECTION_M1_BOTTOM —
        поэтому нижняя схема применяется миксином, а не циклом.
        """
        self._m1_freqs: list[float] = []
        self._m1_table = M1Table(0, 3)
        self._m1_seq: dict | None = None   # активная последовательность S
        self._m1_seq_stop = False
        self._m1_table.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Expanding)
        self._setup_m1_table()
        self.sec_method_1.add_row_layout('', self._m1_table)
        self.sec_method_1.add_inputs(SECTION_M1_BOTTOM)
        self._wire_m1_controls()

        # Размерность — заполнителем: amp_unit появится позже
        # (initialization_form_elements_fsva); заголовки обновятся
        # из _apply_state_params при первом опросе прибора
        self._m1_refresh_unit()
        self._m1_markers_state_changed()

    def _setup_m1_table(self) -> None:
        """Поведение таблицы: выделение строками, равные колонки, высота."""
        t = self._m1_table
        t.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setHighlightSections(False)   # заголовок не жирнеет при выделении
        vh = t.verticalHeader()
        vh.setVisible(True)              # стандартная нумерация строк
        vh.setHighlightSections(False)   # номер строки не жирнеет
        vh.setMinimumSectionSize(18)
        vh.setDefaultSectionSize(18)
        t.setMinimumHeight(400)
        t.cellDoubleClicked.connect(self._m1_on_cell_double_clicked)
        t.delete_requested.connect(self._m1_delete_selected)

    def _wire_m1_controls(self) -> None:
        """Подсказки и обработчики кнопок; чекбоксы/спинбокс — без сигналов."""
        w = self.sec_method_1.widgets
        for key, tip in (
            ('m1_open', 'Выбрать файл для загрузки в таблицу'),
            ('m1_save', 'Сохранить файл с результатами измерений'),
            ('m1_clear', 'Очистить таблицу с результатами измерений'),
            ('m1_search', 'Посчитать тактовую'),
            ('m1_s', 'Измерить сигналы'),
            ('m1_n', 'Измерить шумы'),
            ('m1_stop', 'Остановить измерения'),
            ('m1_sel_only', 'Измерять только выделенные в таблице частоты'),
            ('m1_screens', 'Сохранять скриншот при измерении'),
            ('m1_accum', 'Количество накоплений трассы при измерении'),
        ):
            w[key].setToolTip(tip)
        w['m1_open'].clicked.connect(self._m1_open_clicked)
        w['m1_save'].clicked.connect(self._m1_save_clicked)
        w['m1_clear'].clicked.connect(self._m1_clear_clicked)
        w['m1_add_cf'].clicked.connect(self._m1_add_cf_clicked)
        w['m1_add_mrk'].clicked.connect(self._m1_add_marker_clicked)
        w['m1_add_df'].clicked.connect(self._m1_add_delta_clicked)
        w['m1_search'].clicked.connect(self._m1_search_clicked)
        w['m1_s'].clicked.connect(self._m1_s_clicked)
        w['m1_n'].clicked.connect(self._m1_n_clicked)
        w['m1_stop'].clicked.connect(self._m1_stop_clicked)
        self._m1_btn_delta = w['m1_add_df']

    def _m1_refresh_unit(self, *_args) -> None:
        """Заголовки колонок 2/3 — по кэшу _current_amp_unit.

        Источник — тот же, что у легенды маркеров: значение,
        подтверждённое прибором (update_state) или взятое из файла
        снимка (_load_screen_state). Комбобокс amp_unit отражает
        фактическую настройку прибора и при загрузке снимка осознанно
        не меняется — поэтому он лишь запасной источник, пока кэш
        ещё не заведён (до первого кадра).
        """
        if getattr(self, '_m1_table', None) is None:
            return   # settings_method_1 ещё не выполнялся
        unit = getattr(self, '_current_amp_unit', None)
        if not unit:
            combo = getattr(self, 'amp_unit', None)
            unit = combo.currentText().strip() if combo is not None else ''
        self._m1_table.setHorizontalHeaderLabels(
            ['Частота, МГц', f'Usn, {unit or "дБм"}', f'Un, {unit or "дБм"}'])

    # --- Ядро таблицы: добавление, поиск, форматирование ------------------

    @staticmethod
    def _m1_fmt_mhz(freq_mhz: float) -> str:
        """МГц: до шести знаков после запятой, хвостовые нули отброшены."""
        s = f'{freq_mhz:.6f}'
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s

    @staticmethod
    def _m1_fmt_amp(value: float) -> str:
        """Амплитудные колонки: два знака после запятой."""
        return f'{value:.2f}'

    def _m1_find(self, freq_mhz: float) -> int | None:
        """Индекс строки с частотой freq_mhz или None (список отсортирован)."""
        i = bisect_left(self._m1_freqs, freq_mhz)
        if i < len(self._m1_freqs) and self._m1_freqs[i] == freq_mhz:
            return i
        return None

    def _m1_add_row(self, freq_mhz: float, usn: str = '', un: str = '') -> int:
        """Вставить строку по возрастанию частоты; вернуть её индекс."""
        idx = bisect_left(self._m1_freqs, freq_mhz)
        self._m1_freqs.insert(idx, freq_mhz)
        t = self._m1_table
        t.insertRow(idx)
        align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        freq_it = QTableWidgetItem(self._m1_fmt_mhz(freq_mhz))
        # Первый столбец нередактируем: частоты меняются только добавлением
        freq_it.setFlags(freq_it.flags() & ~Qt.ItemFlag.ItemIsEditable)
        freq_it.setTextAlignment(align)
        it_usn = QTableWidgetItem(usn)
        it_un = QTableWidgetItem(un)
        it_usn.setTextAlignment(align)
        it_un.setTextAlignment(align)
        t.setItem(idx, 0, freq_it)
        t.setItem(idx, 1, it_usn)
        t.setItem(idx, 2, it_un)
        return idx

    def _m1_select_row(self, idx: int) -> None:
        """Выделить строку idx целиком (сняв прочие выделения)."""
        t = self._m1_table
        t.clearSelection()
        t.setCurrentCell(idx, 0)
        t.selectRow(idx)

    def _m1_try_add(self, freq_hz: float, usn: str = '', un: str = '') -> bool:
        """Добавить частоту (Гц) с проверкой дубликата; выделить строку."""
        freq_mhz = freq_hz / 1e6
        if self._m1_find(freq_mhz) is not None:
            QMessageBox.information(
                self, 'Метод измерений 1',
                f'Частота {self._m1_fmt_mhz(freq_mhz)} МГц '
                f'уже есть в таблице.')
            return False
        idx = self._m1_add_row(freq_mhz, usn, un)
        self._m1_select_row(idx)
        return True

    def _m1_clear_table(self) -> None:
        self._m1_freqs.clear()
        self._m1_table.setRowCount(0)

    # --- Кнопки добавления частот ------------------------------------------

    def _m1_add_cf_clicked(self) -> None:
        """+Fц: центральная частота графика из метки CF."""
        hz = self._freq_text_to_hz(self.label_center)
        if hz is None:
            QMessageBox.warning(self, 'Метод измерений 1',
                                'Центральная частота не определена.')
            return
        self._m1_try_add(hz)

    def _m1_add_marker_clicked(self) -> None:
        """+Fмрк: частота активного маркера + амплитуда его трассы."""
        num = self._marker_active
        if num is None:
            QMessageBox.warning(self, 'Метод измерений 1',
                                'Нет активного маркера — включите М1 или М2.')
            return
        entry = self._marker_entries[num]
        if entry['freq'] is None:
            QMessageBox.warning(self, 'Метод измерений 1',
                                'У активного маркера не задана частота.')
            return
        freqs, levels = self._trace_data_for_peak(entry['trace_idx'])
        amp = self._amp_at_freq(entry['freq'], levels, freqs)
        self._m1_try_add(
            entry['freq'], '' if amp is None else self._m1_fmt_amp(amp))

    def _m1_add_delta_clicked(self) -> None:
        """+∆Fмрк: среднее частот М1/М2; кнопка активна лишь при обоих."""
        f1 = self._marker_entries[1]['freq']
        f2 = self._marker_entries[2]['freq']
        if f1 is None or f2 is None:
            return          # страховка: кнопка должна быть неактивна
        self._m1_try_add((f1 + f2) / 2)

    def _m1_markers_state_changed(self) -> None:
        """Хук маркеров: +∆Fмрк активна только при обоих маркерах."""
        if getattr(self, '_m1_btn_delta', None) is None:
            return   # settings_method_1 ещё не выполнялся

        def ready(n: int) -> bool:
            e = self._marker_entries[n]
            return (e['line'] is not None and e['line'].isVisible()
                    and e['freq'] is not None)

        self._m1_btn_delta.setEnabled(ready(1) and ready(2))

    # --- Очистка, удаление, двойной клик -----------------------------------

    def _m1_clear_clicked(self) -> None:
        if self._m1_table.rowCount() == 0:
            return
        if QMessageBox.question(
                self, 'Очистка таблицы',
                'Очистить таблицу с результатами измерений?') \
                is not QMessageBox.StandardButton.Yes:
            return
        self._m1_clear_table()

    def _m1_delete_selected(self) -> None:
        """Delete в таблице: удалить выделенные строки после подтверждения."""
        if self._m1_seq is not None:
            return   # во время измерения таблицу не трогаем

        rows = sorted({i.row() for i in self._m1_table.selectedIndexes()},
                      reverse=True)
        if not rows:
            return
        if QMessageBox.question(
                self, 'Удаление строк',
                f'Удалить выделенные строки ({len(rows)})?') \
                is not QMessageBox.StandardButton.Yes:
            return
        for r in rows:
            self._m1_table.removeRow(r)
            # параллельный список режется тем же порядком
            self._m1_freqs.pop(r)

    def _m1_on_cell_double_clicked(self, row: int, col: int) -> None:
        """Двойной клик по частоте: перестроить прибор на эту частоту."""
        if col != 0:
            return
        it = self._m1_table.item(row, 0)
        if it is None:
            return
        try:
            hz = float(it.text().replace(',', '.')) * 1e6
        except ValueError:
            return
        self._send_cmd(f'set_cf:{hz:.0f}')

    # --- Загрузка файла -----------------------------------------------------

    def _m1_open_clicked(self) -> None:
        """Загрузка результатов: при непустой таблице — добавить/заменить.

        Файл валидируется целиком до загрузки: пустой файл, строка не
        из трёх полей через \\t или нечисловые поля (кроме первой
        строки-заголовка) — отказ без частичной загрузки.
        """
        replace = True
        if self._m1_table.rowCount() > 0:
            box = QMessageBox(self)
            box.setWindowTitle('Загрузка результатов')
            box.setText('В таблице уже есть строки. Что сделать с файлом?')
            b_add = box.addButton('Добавить строки',
                                  QMessageBox.ButtonRole.AcceptRole)
            b_repl = box.addButton('Заменить',
                                   QMessageBox.ButtonRole.DestructiveRole)
            box.addButton('Отмена', QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is b_add:
                replace = False
            elif box.clickedButton() is not b_repl:
                return
        rows = self._m1_read_file()
        if not rows:
            return
        if replace:
            self._m1_clear_table()
        added = skipped = 0
        first = None
        for f_mhz, usn, un in rows:
            if self._m1_find(f_mhz) is not None:
                skipped += 1
                continue
            idx = self._m1_add_row(f_mhz, usn, un)
            if first is None:
                first = idx
            added += 1
        if added:
            self._m1_select_row(first)
        if skipped:
            QMessageBox.information(
                self, 'Метод измерений 1',
                f'Загружено строк: {added}. Пропущено дубликатов: {skipped}.')

    def _m1_read_file(self) -> list[tuple[float, str, str]]:
        """Выбрать и разобрать файл; [] — отмена/брак.

        Формат: три числа через \\t в строке; первая строка может быть
        заголовком (не числа — игнорируется). Кодировка: utf-8, при
        сбое — cp1251 (файлы, писанные не этой программой).
        """
        path, _ = QFileDialog.getOpenFileName(
            self, 'Загрузка результатов', self.work_dir(),
            'Текст с разделителями (*.txt)')
        if not path:
            return []
        try:
            try:
                with open(path, encoding='utf-8') as f:
                    lines = f.read().splitlines()
            except UnicodeDecodeError:
                with open(path, encoding='cp1251') as f:
                    lines = f.read().splitlines()
        except OSError as exc:
            QMessageBox.warning(self, 'Загрузка результатов',
                                f'Файл не читается:\n{exc}')
            return []
        if not any(ln.strip() for ln in lines):
            QMessageBox.warning(self, 'Загрузка результатов', 'Файл пуст.')
            return []
        rows = []
        for i, ln in enumerate(lines):
            parsed = self._m1_parse_row(ln.split('\t'))
            if parsed is None:
                if i == 0:
                    continue   # строка заголовков колонок — пропустить
                QMessageBox.warning(
                    self, 'Загрузка результатов',
                    f'Строка {i + 1}: ожидались три числовых значения '
                    f'через табуляцию.\nЗагрузка прервана.')
                return []
            rows.append(parsed)
        return rows

    @staticmethod
    def _m1_parse_row(parts: list[str]) -> tuple | None:
        """(частота МГц, Usn, Un) или None: три поля, все три — числа."""
        if len(parts) != 3:
            return None
        parts = [p.strip() for p in parts]
        try:
            f = float(parts[0].replace(',', '.'))
            usn = float(parts[1].replace(',', '.'))
            un = float(parts[2].replace(',', '.'))
        except ValueError:
            return None
        return f, Method1Mixin._m1_fmt_amp(usn), Method1Mixin._m1_fmt_amp(un)

    # --- Сохранение файла ---------------------------------------------------

    def _m1_save_clicked(self) -> None:
        """Сохранить таблицу в TXT: заголовки + строки через \\t."""
        t = self._m1_table
        if t.rowCount() == 0:
            QMessageBox.information(self, 'Сохранение результатов',
                                    'Таблица пуста — сохранять нечего.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранение результатов',
            os.path.join(self.work_dir(), 'method1.txt'),
            'Текст с разделителями (*.txt)')
        if not path:
            return
        if not path.lower().endswith('.txt'):
            path += '.txt'
        unit = self.amp_unit.currentText().strip() or '—'
        lines = ['\t'.join(('Частота, МГц', f'Usn, {unit}', f'Un, {unit}'))]
        for r in range(t.rowCount()):
            lines.append('\t'.join(
                t.item(r, c).text() if t.item(r, c) is not None else ''
                for c in range(3)))
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
        except OSError as exc:
            QMessageBox.warning(self, 'Сохранение результатов',
                                f'Файл не записан:\n{exc}')
            return

    # --- Заглушки: действия будут описаны позже ---------------------------
    def _m1_search_clicked(self) -> None:
        """Посчитать тактовую — поведение будет описано позже."""

    # --------- Измерения СИГНАЛОВ -----------------------
    def _m1_s_clicked(self) -> None:
        """Измерить сигналы: максимум по N развёрткам в трассе 1."""
        self._m1_start_seq('S')

    def _m1_n_clicked(self) -> None:
        """Измерить шумы: детектор RMS, среднее по N развёрткам в трассе 2."""
        self._m1_start_seq('N')

    def _m1_start_seq(self, kind: str) -> None:
        """Общий запуск последовательности измерений S/N.

        Схема едина: Single, перестройка CF, пакет из N развёрток
        (кадр на каждую), уровень из буфера доп. трассы в столбец.
        Отличия S/N — в _M1_SEQ_CFG; для N дополнительно ставится
        детектор RMS (и возвращается по завершении).
        """
        cfg = self._M1_SEQ_CFG[kind]
        if getattr(self, '_m1_seq', None) is not None:
            return
        if self._m1_table.rowCount() == 0:
            QMessageBox.information(self, 'Метод измерений 1',
                                    'Таблица пуста — измерять нечего.')
            return
        if self._trace_worker is None:
            QMessageBox.warning(self, 'Метод измерений 1',
                                'Анализатор не подключён.')
            return
        sel_only = self.sec_method_1.widgets['m1_sel_only'].isChecked()
        if sel_only:
            rows = sorted({i.row() for i in self._m1_table.selectedIndexes()})
            if not rows:
                QMessageBox.information(
                    self, 'Метод измерений 1',
                    'Галочка «Select» стоит, но строки не выделены.')
                return
        else:
            rows = list(range(self._m1_table.rowCount()))
        if not self._m1_confirm(kind):
            return

        self._m1_seq_stop = False
        self._m1_seq = {'kind': kind, 'col': cfg['col'], 'trace': cfg['trace'],
                        'rows': rows, 'idx': 0, 'freq_hz': None,
                        'phase': 'idle', 'watchdog': None,
                        'det_saved': self.combo_det.currentText(),
                        'radio_count': self.radio_count.isChecked(),
                        'trc_saved': {
                            t: (getattr(self, f'trc_{t}_on').currentText(),
                                getattr(self, f'trc_{t}_acc').currentText())
                            for t in (1, 2)}}
        self._m1_seq_lock_ui(True)
        # Блокируем элементы управления анализатором
        self._set_analyzer_controls_enabled(False)
        # Кнопки подключения/отключения — тоже под замок:
        # разрыв соединения посреди прогона оставит прибор в Single
        # без шансов на восстановление
        if getattr(self, 'but_analyzer_conn', None) is not None:
            self.but_analyzer_conn.setEnabled(False)

        self._ensure_unpaused()

        # Single — явной командой: иначе INIT;*OPC? в Continuous
        # возвращается мгновенно и синхронизации нет
        self._send_cmd('sweep_mode:single')
        self._set_checked(self.radio_single, True)
        self._set_checked(self.radio_count, False)
        self._update_sweep_init()

        # Детектор измерения — из комбобокса этого типа измерений;
        # сохранённый детектор прибора вернём в _m1_finish
        det_name = self.sec_method_1.widgets[cfg['det_key']].currentText()
        det_code = DETECTORS_FSVA.get(det_name.strip())
        if det_code:
            self._send_cmd(f'det_set:{det_code}')

        # Доп. трасса: включить и выбрать режим накопления (чисто GUI)
        trc_on = getattr(self, f'trc_{cfg["trace"]}_on')
        trc_acc = getattr(self, f'trc_{cfg["trace"]}_acc')
        trc_acc.blockSignals(True)
        trc_acc.setCurrentText(cfg['acc'])
        trc_acc.blockSignals(False)
        trc_on.blockSignals(True)
        trc_on.setCurrentText(TRACE_ON)
        trc_on.blockSignals(False)
        self._acc_clear(cfg['trace'])
        self._update_acc_legend()

        # Основную трассу скрыть на время измерения: сигнал чекбокса
        # сам вызовет on_main_visible_changed(False) — кривая спрячется,
        # легенда и маркеры пересоберутся. Прибору ничего не шлём.
        # На накопление скрытие не влияет: буферы копятся из кадров
        # независимо от видимости основной кривой.
        self.chk_main_visible.setChecked(False)

        self._trace_worker.state_ready.connect(self._m1_on_frame)
        self._trace_worker.sweeps_done.connect(self._m1_on_sweeps_done)
        QTimer.singleShot(0, self._m1_next_frequency)

    def _m1_confirm(self, kind: str) -> bool:
        """Подтверждение и сводка текущих настроек измерения."""
        cfg = self._M1_SEQ_CFG[kind]
        w = self.sec_method_1.widgets
        n = int(w['m1_accum'].value())
        span_hz = self._freq_text_to_hz(self.label_span)
        span_str = self._format_freq(span_hz) if span_hz is not None else '—'
        text = (f'Режим {cfg["title"]}.\n\n'
                f'Накоплений:\t{n}\n'
                f'Детектор:\t{w[cfg["det_key"]].currentText() or "—"}\n'
                f'RBW/VBW =\t{self._rbw_str or "—"}/{self._vbw_str or "—"}\n'
                f'Span =\t\t{span_str}\n'
                f'Аттенюатор:\t{self.label_atten.text().strip() or "—"} дБ\n'
                f'Предусилитель:\t{self.combo_preamp.currentText() or "—"}\n\n'
                'Приступить?')
        return QMessageBox.question(
            self, 'Метод измерений 1', text) is QMessageBox.StandardButton.Yes

    def _m1_on_sweeps_done(self) -> None:
        seq = self._m1_seq
        if seq is None or seq['phase'] != 'sweep':
            return
        if self._m1_seq_stop:
            self._m1_finish()
            return
        seq['phase'] = 'read'

    def _m1_next_frequency(self) -> None:
        """Очередная частота: только set_cf."""
        seq = self._m1_seq
        if seq is None:
            return
        if self._m1_seq_stop or seq['idx'] >= len(seq['rows']):
            self._m1_finish(done=True)
            return
        row = seq['rows'][seq['idx']]
        hz = self._m1_freqs[row] * 1e6      # таблица хранит МГц
        seq['freq_hz'] = hz
        seq['phase'] = 'tune'
        self._send_cmd(f'set_cf:{hz:.0f}')
        self._m1_start_watchdog()

    def _m1_on_frame(self, state) -> None:
        """Полные кадры ведут фазы tune/sweep/read (quick-кадры мимо).

        tune: ждём кадр с подтверждённым центром → очищаем буфер
        трассы 1 и ставим пакет развёрток. sweep: кадры пакета
        накапливает буфер, сами они для машины не действия. read:
        первый полный кадр после sweeps_done — буфер готов, пишем
        уровень и переходим к следующей частоте.
        """
        seq = self._m1_seq
        if seq is None:
            return
        if not state.freqs or not state.levels:
            return   # quick_state или пустой кадр — для фаз не годится
        if self._m1_seq_stop:
            self._m1_finish()
            return

        if seq['phase'] == 'tune':
            center = state.center
            if center is not None:
                center *= 1e6   # из воркера приходит в МГц → в Гц
            else:
                center = (state.freqs[0] + state.freqs[-1]) / 2
            span = abs(state.freqs[-1] - state.freqs[0])
            tol = max(1.0, span * 1e-6)
            if abs(center - seq['freq_hz']) > tol:
                return   # ещё старое окно — ждём
            self._acc_clear(seq['trace'])
            seq['phase'] = 'sweep'
            n = int(self.sec_method_1.widgets['m1_accum'].value())
            self._trace_worker.send_command(f'sweep_batch:{n}')
            return

        if seq['phase'] == 'read':
            freqs, levels = self._trace_data_for_peak(seq['trace'] + 1)
            if freqs is None or levels is None or not len(levels):
                return
            amp = self._amp_at_freq(seq['freq_hz'], levels, freqs)
            row = seq['rows'][seq['idx']]
            it = self._m1_table.item(row, seq['col'])
            if it is not None:
                it.setText('' if amp is None else self._m1_fmt_amp(amp))
            seq['idx'] += 1
            seq['phase'] = 'idle'
            QTimer.singleShot(0, self._m1_next_frequency)

    def _m1_start_watchdog(self) -> None:
        """Таймер сбоя на весь шаг частоты: tune + N кадров."""
        seq = self._m1_seq
        old = seq.get('watchdog')
        if old is not None:
            old.stop()
            old.deleteLater()
        n = int(self.sec_method_1.widgets['m1_accum'].value())
        sec = self._m1_sweeptime_sec() or 0.1
        timeout_ms = max(10_000, int((n + 2) * sec * 1000 * 3) + 5_000)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(timeout_ms)
        timer.timeout.connect(self._m1_watchdog_fired)
        seq['watchdog'] = timer
        timer.start()

    def _m1_sweeptime_sec(self) -> float | None:
        """Время развёртки из метки ('10 мс', '1.5 с') в секундах."""
        mult = {'с': 1.0, 'мс': 1e-3, 'мкс': 1e-6, 'нс': 1e-9}
        parts = self.label_sweeptime.text().strip().split()
        if len(parts) != 2 or parts[1] not in mult:
            return None
        try:
            val = float(parts[0].replace(',', '.'))
        except ValueError:
            return None
        return val * mult[parts[1]]

    def _m1_watchdog_fired(self) -> None:
        if self._m1_seq is not None:
            QMessageBox.warning(self, 'Метод измерений 1',
                                'Измерение не завершилось (таймаут).')
            self._m1_finish()

    def _m1_stop_clicked(self) -> None:
        """Стоп: прервать последовательность. Восстанавливать нечего —
        на приборе менялась только частота."""
        if self._m1_seq is not None:
            self._m1_seq_stop = True
            self._m1_finish()

    def _m1_finish(self, done: bool = False) -> None:
        seq, self._m1_seq = self._m1_seq, None
        self._m1_seq_stop = False
        if seq is None:
            return
        wd = seq.get('watchdog')
        if wd is not None:
            wd.stop()
            wd.deleteLater()
        worker = self._trace_worker
        if worker is not None:
            for sig, slot in ((worker.sweeps_done, self._m1_on_sweeps_done),
                              (worker.state_ready, self._m1_on_frame)):
                try:
                    sig.disconnect(slot)
                except TypeError:
                    pass
        self._m1_seq_lock_ui(False)
        self._set_analyzer_controls_enabled(True)
        if getattr(self, 'but_analyzer_conn', None) is not None:
            self.but_analyzer_conn.setEnabled(True)

        # Единственное приборное изменение сверх CF — режим развёртки:
        # возвращаем его явно (иначе INIT не ждёт развёртки в будущем
        # прогоне, а экран сейчас замер бы в Single)
        if seq['radio_count']:
            self._send_cmd('sweep_mode:cont')
        else:
            self._send_cmd('sweep_mode:single')
        self._set_checked(self.radio_count, seq['radio_count'])
        self._set_checked(self.radio_single, not seq['radio_count'])
        self._update_sweep_init()

        # Детектор прибора — вернуть то, что было до прогона
        code = DETECTORS_FSVA.get(seq['det_saved'])
        if code:
            self._send_cmd(f'det_set:{code}')
        else:
            print('[M1] детектор до измерения не определён, '
                  f'на приборе остался {seq["det_saved"] or "?"}')

        # Трассы 1/2 — вернуть то, что было до прогона. Сигналы не
        # глушим: за комбобоксами команд прибору нет, а внутренняя
        # логика накопления должна узнать о выключении трассы.
        # Буферы очищаем: если трасса возвращается включённой, её
        # накопление должно начаться с чистого листа, а не продолжать
        # измерные максимумы/средние.
        for t, (on_txt, acc_txt) in seq['trc_saved'].items():
            getattr(self, f'trc_{t}_on').setCurrentText(on_txt)
            getattr(self, f'trc_{t}_acc').setCurrentText(acc_txt)
            self._acc_clear(t)
        self._update_acc_legend()

        # Основная трасса — на экран независимо от того, что было
        # до прогона (ваше требование: всегда True, без сохранения)
        self.chk_main_visible.setChecked(True)

        if done:
            QMessageBox.information(
                self, 'Метод измерений 1',
                f'{self._M1_SEQ_CFG[seq["kind"]]["done"]}: '
                f'обработано частот — {len(seq["rows"])}.')

    def _m1_seq_lock_ui(self, locked: bool) -> None:
        w = self.sec_method_1.widgets
        for key in ('m1_open', 'm1_save', 'm1_clear',
                    'm1_add_cf', 'm1_add_mrk', 'm1_add_df', 'm1_search',
                    'm1_s', 'm1_n', 'm1_accum'):
            w[key].setEnabled(not locked)
        if not locked:
            # Зависимые кнопки: их активность определяется состоянием
            # (маркерами), а не снятием блокировки прогона
            self._m1_markers_state_changed()
