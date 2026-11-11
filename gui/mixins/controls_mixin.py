from constants import DETECTORS_FSVA, FREQ_DIM, TRACE_ACC


class ControlsMixin:
    """Миксин: ссылки на элементы управления и обработчики изменений.

    Предполагается, что у окна есть:
    - self.sec_instr / self.sec_rbw / self.sec_freq / self.sec_ampl /
      self.sec_sweep / self.sec_mrk (создаются в gui.settings.set_layout_left);
    - self._trace_worker (создаётся ConnectionMixin.preparation_variables);
    - self._marker_centered (инициализируется до первого _send_cmd).
    """

    def initialization_form_elements_connect(self) -> None:
        """Присвоить короткие ссылки на виджеты секции подключения.

        Должен вызываться после set_layout_left: берёт виджеты по ключам
        из словаря self.sec_instr.widgets.
        """
        self.tb_ip_analyzer = self.sec_instr.widgets['tb_ip_analyzer']
        self.but_analyzer_conn = self.sec_instr.widgets['but_analyzer_conn']
        self.but_analyzer_web = self.sec_instr.widgets['but_analyzer_web']

    def initialization_form_elements_fsva(self) -> None:
        """Присвоить короткие ссылки на виджеты управления анализатором.

        Заполняет атрибуты для секций RBW/VBW, Частоты, Амплитуды, Sweep
        и Markers. Вызывать после set_layout_left, до signal_connection
        и _apply_state_params.
        """
        # Ручное управление анализатором
        # RBW, VBW
        self.rbw_type = self.sec_rbw.widgets['rbw_type_filter']
        self.but_rbw_up = self.sec_rbw.widgets['but_rbw_up']
        self.but_rbw_down = self.sec_rbw.widgets['but_rbw_down']
        self.label_rbw = self.sec_rbw.widgets['label_rbw']
        self.rbw_unit = self.sec_rbw.widgets['rbw_unit']
        self.rbw_auto = self.sec_rbw.widgets['rbw_auto']
        self.but_vbw_up = self.sec_rbw.widgets['but_vbw_up']
        self.but_vbw_down = self.sec_rbw.widgets['but_vbw_down']
        self.label_vbw = self.sec_rbw.widgets['label_vbw']
        self.vbw_unit = self.sec_rbw.widgets['vbw_unit']
        self.vbw_auto = self.sec_rbw.widgets['vbw_auto']

        # SPAN
        self.label_span = self.sec_freq.widgets['label_span']
        self.but_span_set_stepcf = self.sec_freq.widgets['but_span_set_stepcf']
        self.but_span_set_div2 = self.sec_freq.widgets['but_span_set_div2']
        self.but_span_set_mul2 = self.sec_freq.widgets['but_span_set_mul2']
        self.lbl_stop = self.sec_freq.widgets['lbl_stop']
        # Старт/стоп обзора
        self.freq_start = self.sec_freq.widgets['freq_start']
        self.freq_stop = self.sec_freq.widgets['freq_stop']
        # Center Freq
        self.label_center = self.sec_freq.widgets['label_center']
        self.but_cf_down = self.sec_freq.widgets['but_cf_down']
        self.but_cf_up = self.sec_freq.widgets['but_cf_up']
        # CF STEP
        self.tb_cfstep = self.sec_freq.widgets['tb_cfstep']
        self.but_stepcf_set_span = self.sec_freq.widgets['but_stepcf_set_span']
        self.lbl_step = self.sec_freq.widgets['lbl_step']

        # REF LEVEL
        self.label_reflevel = self.sec_ampl.widgets['label_reflevel']
        # self.but_reflvl_down = self.sec_ampl.widgets['but_reflvl_down']
        # self.but_reflvl_up = self.sec_ampl.widgets['but_reflvl_up']
        self.amp_unit = self.sec_ampl.widgets['amp_unit']
        self.transducer = self.sec_ampl.widgets['combo_transducer']
        # REF RANGE
        self.label_range = self.sec_ampl.widgets['label_range']
        self.lbl_range = self.sec_ampl.widgets['lbl_range']
        # self.but_ref_range_down = self.sec_ampl.widgets['but_ref_range_down']
        # self.but_ref_range_up = self.sec_ampl.widgets['but_ref_range_up']
        # PREAMP
        self.combo_preamp = self.sec_ampl.widgets['combo_preamp']
        # ATTEN
        self.label_atten = self.sec_ampl.widgets['label_atten']
        self.atten_auto = self.sec_ampl.widgets['atten_auto']
        self.label_preamp = self.sec_ampl.widgets['label_preamp']
        # self.but_atten_down = self.sec_ampl.widgets['but_atten_down']
        # self.but_atten_up = self.sec_ampl.widgets['but_atten_up']

        # SWEEP
        self.combo_det = self.sec_sweep.widgets['combo_det']
        self.combo_trace_acc = self.sec_sweep.widgets['combo_trace_acc']
        self.tb_sweep_count = self.sec_sweep.widgets['tb_sweep_count']
        self.radio_count = self.sec_sweep.widgets['radio_count']
        self.radio_single = self.sec_sweep.widgets['radio_single']
        self.check_auto_max = self.sec_mrk.widgets['check_auto_max']
        self.but_mrk_to_cf = self.sec_mrk.widgets['but_mrk_to_cf']

    def _send_cmd(self, command: str) -> None:
        """Отправить команду прибору через рабочий поток.

        Args:
            command: строка вида '<префикс>:<значение>' либо короткая
                команда без значения ('reflvl_up', 'atten_down' и т.п.),
                понимаемая TraceWorker._execute_command.

        Note:
            При неподключённом приборе (worker is None) команда
            молча игнорируется. Побочный эффект: помечает
            self._marker_centered = True.
        """
        if self._trace_worker is not None:
            self._trace_worker.send_command(command)
            self._marker_centered = True

    def _set_analyzer_controls_enabled(self, enabled: bool) -> None:
        """Блокировать/разблокировать элементы управления анализатором.

        Используется при подключении/отключении прибора.

        Args:
            enabled: True — разблокировать контролы (прибор подключён);
                False — заблокировать (прибор отключён).
        """
        controls = [
            # управление RBW / VBW
            self.rbw_type, self.but_rbw_down, self.label_rbw, self.but_rbw_up,
            self.rbw_unit, self.rbw_auto,
            self.but_vbw_down, self.label_vbw, self.but_vbw_up,
            self.vbw_unit, self.vbw_auto,
            # управление частотой / спаном / шагом
            self.label_span, self.but_span_set_stepcf,
            self.but_span_set_div2, self.but_span_set_mul2,
            self.freq_start, self.freq_stop, self.lbl_stop,
            self.but_cf_down, self.label_center, self.but_cf_up,
            self.tb_cfstep, self.but_stepcf_set_span, self.lbl_step,
            # управление амплитудой
            self.label_reflevel, self.amp_unit, self.label_range,
            self.combo_preamp, self.label_atten, self.lbl_range,
            self.transducer, self.atten_auto, self.label_preamp,
            # управление sweep
            self.combo_det,
            self.combo_trace_acc,
            self.tb_sweep_count,
            self.radio_count, self.radio_single,
            # управление маркерами
            self.check_auto_max, self.but_mrk_to_cf,
        ]
        for w in controls:
            w.setEnabled(enabled)

    # === ОБРАБОТЧИКИ ИЗМЕНЕНИЙ КОНТРОЛОВ =====================================
    # --- Обработчики контролов для управления Частотой, спаном ---------------
    @staticmethod
    def _freq_text_to_hz(widget) -> float | None:
        """'937.5 МГц' → 937500000.0 Гц; None при пустом/нечисловом поле.

        Обратная операция к PlotMixin._format_freq: первое слово — число
        (запятая допускается), второе — единица из FREQ_DIM.
        """
        parts = widget.text().strip().split()
        if not parts:
            return None
        try:
            value = float(parts[0].replace(',', '.'))
        except ValueError:
            return None
        unit = parts[1] if len(parts) > 1 else 'Гц'
        return value * FREQ_DIM.get(unit, 1.0)

    def on_span_set_stepcf(self) -> None:
        """Установить span равным шагу CF (значение из поля CF Step)."""
        val = self._freq_text_to_hz(self.tb_cfstep)
        if val is not None and val > 0:
            self._send_cmd(f'set_span:{val:.0f}')

    def on_span_half(self) -> None:
        """Уменьшить span вдвое."""
        val = self._freq_text_to_hz(self.label_span)
        if val is not None and val > 0:
            self._send_cmd(f'set_span:{val / 2:.0f}')

    def on_span_double(self) -> None:
        """Увеличить span вдвое."""
        val = self._freq_text_to_hz(self.label_span)
        if val is not None and val > 0:
            self._send_cmd(f'set_span:{val * 2:.0f}')

    def on_stepcf_set_span(self) -> None:
        """Установить шаг CF равным текущему span."""
        val = self._freq_text_to_hz(self.label_span)
        if val is not None and val > 0:
            self._send_cmd(f'cfstep_set:{val:.0f}')
    # -------------------------------------------------------------------------

    # --- Обработчики контролов для управления Амплитудой ---------------------
    def on_amp_unit_changed(self, text: str) -> None:
        """Сменить единицы амплитуды.

        Args:
            text: новый текст комбобокса (например, 'дБм', 'В').
        """
        self._send_cmd(f'amp_unit:{text}')

    def on_trans_changed(self, text: str) -> None:
        """Сменить калибровочную поправку (трансдьюсер).

        Args:
            text: выбранное название антенны либо 'Не выбрана (0 дБ)'
                — тогда передаётся сброс коррекции ('transducer:''').
        """
        if text != 'Не выбрана (0 дБ)':
            self._send_cmd(f'transducer:{text}')
        else:
            self._send_cmd("transducer:''")

    def on_preamp_changed(self, text: str) -> None:
        """Сменить состояние предусилителя.

        Args:
            text: новый текст комбобокса (например, 'Off', 'On').
        """
        self._send_cmd(f'preamp:{text}')

    def on_atten_auto_toggled(self, checked: bool) -> None:
        """Переключить автоаттенюатор на приборе."""
        self._send_cmd(f'atten_auto_set:{"on" if checked else "off"}')
    # -------------------------------------------------------------------------

    # --- Обработчики контролов для управления RBW, VBW -----------------------
    def rbw_type_changed(self, text: str) -> None:
        """Сменить тип фильтра RBW.

        Args:
            text: тип фильтра в терминах прибора (например, 'Normal',
                'Power', 'Pulse').
        """
        self._send_cmd(f'rbw_type_set:{text}')

    def on_rbw_unit_changed(self, text: str) -> None:
        """Сменить единицу отображения RBW.

        Args:
            text: 'Гц', 'кГц' или 'МГц'.
        """
        self._send_cmd(f'rbw_unit:{text}')

    def on_rbw_auto_toggled(self, checked: bool) -> None:
        """Включить/выключить авто-RBW.

        Args:
            checked: новое состояние переключателя (True — auto on).
        """
        self._send_cmd(f'rbw_auto_set:{"on" if checked else "off"}')

    def on_vbw_unit_changed(self) -> None:
        """Применить VBW из поля с учётом выбранной единицы.

        Считывает значение из self.label_vbw (допускает запятую как
        десятичный разделитель), умножает на коэффициент единицы
        ('Гц'/'кГц'/'МГц') и отправляет на прибор в герцах.

        Note:
            При некорректном числе в поле команда не отправляется.
        """
        try:
            val = float(self.label_vbw.text().replace(',', '.'))
        except ValueError:
            return
        factor = {'Гц': 1, 'кГц': 1e3, 'МГц': 1e6}.get(
            self.vbw_unit.currentText(), 1)
        self._trace_worker.send_command(f'set_vbw:{val * factor:.0f}')

    def on_vbw_auto_toggled(self, checked: bool) -> None:
        """Включить/выключить авто-VBW.

        Args:
            checked: новое состояние переключателя (True — auto on).
        """
        self._send_cmd(f'vbw_auto_set:{"on" if checked else "off"}')
    # -------------------------------------------------------------------------

    # --- Обработчики контролов для управления SWEEP --------------------------
    def on_det_changed(self, text: str) -> None:
        """Сменить тип детектора.

        Args:
            text: название детектора из комбобокса (ключ DETECTORS_FSVA).
        """
        code = DETECTORS_FSVA.get(text)
        if code:
            self._send_cmd(f'det_set:{code}')

    def on_trace_acc_changed(self, text: str) -> None:
        """Сменить режим накопления трассы.

        Args:
            text: режим из комбобокса (ключ TRACE_ACC).
        """
        code = TRACE_ACC.get(text)
        if code:
            self._send_cmd(f'trace_acc_set:{code}')

    def on_sweep_mode_changed(self, checked: bool) -> None:
        """Переключить режим развёртки Continuous/Single.

        Подключён только к radio_count: при переключении радиокнопки
        сигнал toggled приходит у обеих кнопок группы, но нам важен
        факт смены, а не какая именно включилась.

        Args:
            checked: True — непрерывный sweep, False — одиночный.
        """
        self._send_cmd(f'sweep_mode:{"cont" if checked else "single"}')

    def on_sweep_count_changed(self) -> None:
        """Установить число развёрток для одиночного режима."""
        self._send_cmd(f'sweep_count_set:{int(self.tb_sweep_count.value())}')
    # -------------------------------------------------------------------------
