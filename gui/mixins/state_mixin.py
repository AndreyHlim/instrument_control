from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit,
                             QRadioButton, QSpinBox)

from constants import DETECTORS_FSVA_REV, TRACE_ACC_REV

if TYPE_CHECKING:
    from worker import DeviceState


class StateMixin:
    """Миксин: маппинги значений прибора и применение состояния к контролам.

    Использует self._format_freq из PlotMixin.
    """

    # --- Хелперы синхронизации без срабатывания пользовательских сигналов ---
    @staticmethod
    def _set_combo(combo: QComboBox, text: str) -> None:
        combo.blockSignals(True)
        combo.setCurrentText(text)
        combo.blockSignals(False)

    @staticmethod
    def _set_spin(spin: QSpinBox | QDoubleSpinBox, value) -> None:
        clamped = max(spin.minimum(), min(spin.maximum(), value))
        spin.blockSignals(True)
        spin.setValue(clamped)
        spin.blockSignals(False)

    @staticmethod
    def _set_checked(widget: QCheckBox | QRadioButton, checked: bool) -> None:
        widget.blockSignals(True)
        widget.setChecked(checked)
        widget.blockSignals(False)

    def _apply_state_params(self, state: 'DeviceState') -> None:
        """Обновить текстовые метки и контролы параметров прибора.

        None = параметр не опрашивался в этом кадре — не трогаем.
        """
        if state.rbw_type is not None:
            self._set_combo(self.rbw_type, state.rbw_type)
        if state.rbw is not None:
            rbw_val, rbw_unit = self._format_freq(state.rbw * 1e3).split()
            self.label_rbw.setText(rbw_val)
            self._set_combo(self.rbw_unit, rbw_unit)
        if state.vbw is not None:
            vbw_val, vbw_unit = self._format_freq(state.vbw * 1e3).split()
            self.label_vbw.setText(vbw_val)
            self._set_combo(self.vbw_unit, vbw_unit)
        if state.rbw_auto is not None:
            self._set_checked(self.rbw_auto, state.rbw_auto)
        if state.vbw_auto is not None:
            self._set_checked(self.vbw_auto, state.vbw_auto)
        if state.span is not None:
            self._safe_set_text(
                self.label_span, self._format_freq(state.span * 1e6))
        if state.center is not None:
            self._safe_set_text(
                self.label_center, self._format_freq(state.center * 1e6))
        if state.freq_start is not None:
            self._safe_set_text(
                self.freq_start, self._format_freq(state.freq_start))
        if state.freq_stop is not None:
            self._safe_set_text(
                self.freq_stop, self._format_freq(state.freq_stop))
        if state.reflevel is not None:
            self._safe_set_text(
                self.label_reflevel, f'{state.reflevel:g}')
        if state.amp_unit is not None:
            self._set_combo(self.amp_unit, state.amp_unit)
        if state.transducer is not None:
            self._set_combo(self.transducer, state.transducer)
        if state.atten is not None:
            self._safe_set_text(self.label_atten, f'{state.atten}')
        if state.atten_auto is not None:
            self._set_checked(self.atten_auto, state.atten_auto)
        if state.range_val is not None:
            self._safe_set_text(self.label_range, f'{state.range_val:g}')
        if state.preamp is not None:
            self._set_combo(self.combo_preamp, state.preamp)
        if state.cfstep is not None:
            self._safe_set_text(
                self.tb_cfstep, self._format_freq(state.cfstep, 1))
        if state.det is not None:
            self._set_combo(
                self.combo_det, DETECTORS_FSVA_REV.get(state.det, state.det))
        if state.trace_acc is not None:
            self._set_combo(
                self.combo_trace_acc,
                TRACE_ACC_REV.get(state.trace_acc, state.trace_acc))
        if state.sweep_single is not None:
            self._set_checked(self.radio_single, state.sweep_single)
            self._set_checked(self.radio_count, not state.sweep_single)
        if state.sweep_count is not None:
            self._set_spin(self.tb_sweep_count, state.sweep_count)

    def _safe_set_text(self, widget: QLineEdit, text: str) -> None:
        """Записать значение в поле, не мешая пользователю.

        Пропускаем запись, только если пользователь реально набрал
        текст в поле (фокус + isModified) — иначе setText затёр бы
        недопечатанное значение. Просто фокус с выделением не мешает:
        после колёсика или прихода состояния с прибора поле
        перезаписывается сразу.
        """
        if widget.hasFocus() and widget.isModified():
            return
        if widget.text() == text:
            return
        widget.setText(text)
