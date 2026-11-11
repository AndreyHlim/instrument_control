from functools import partial

from PyQt6.QtWidgets import QMainWindow


def _updown(form: QMainWindow, prefix: str) -> dict[str, partial]:
    """
    Пара кнопок but_<prefix>_down / but_<prefix>_up → команда <prefix>_down/up.
    """
    return {
        f'but_{prefix}_down': partial(form._send_cmd, f'{prefix}_down'),
        f'but_{prefix}_up': partial(form._send_cmd, f'{prefix}_up'),
    }


def callbacks_map_fsva(form: QMainWindow, ctrl: str):
    """Сопоставить элементам управления сигналы для УПРАВЛЕНИЯ АНАЛИЗАТОРОМ.

    Строки команд формируются из имени виджета, обработчики — ссылки на методы.
    """
    return {
        # --- АМПЛИТУДА ---
        'amp': {
            'label_reflevel': {
                'value_accepted': lambda v: form._send_cmd(
                    f'set_reflvl:{v:g}'),
                'wheel_step': lambda step: form._send_cmd(
                    'reflvl_up' if step > 0 else 'reflvl_down'),
            },
            'amp_unit': form.on_amp_unit_changed,
            'label_range': {
                'value_accepted': lambda v: form._send_cmd(
                    f'set_ref_range:{v:g}'),
                'wheel_step': lambda step: form._send_cmd(
                    'ref_range_up' if step > 0 else 'ref_range_down'),
            },
            'combo_preamp': form.on_preamp_changed,
            'label_atten': {
                'value_accepted': lambda v: form._send_cmd(
                    f'set_atten:{round(v)}'),
                'wheel_step': lambda step: form._send_cmd(
                    'atten_up' if step > 0 else 'atten_down'),
            },
            'atten_auto': form.on_atten_auto_toggled,
            'combo_transducer': form.on_trans_changed,
        },

        # --- ЧАСТОТА / SPAN / ШАГ ---
        'freq': {
            **_updown(form, 'cf'),
            **_updown(form, 'span'),
            'label_center': lambda hz: form._send_cmd(f'set_cf:{hz:.0f}'),
            'label_span': {
                'freq_accepted': lambda hz: form._send_cmd(
                    f'set_span:{hz:.0f}'),
                'wheel_step': lambda step: form._send_cmd(
                    'span_up' if step > 0 else 'span_down'),
            },
            'tb_cfstep': lambda hz: form._send_cmd(f'cfstep_set:{hz:.0f}'),
            'freq_start': lambda hz: form._send_cmd(
                f'set_freq_start:{hz:.0f}'),
            'freq_stop': lambda hz: form._send_cmd(f'set_freq_stop:{hz:.0f}'),
            'but_span_set_stepcf': form.on_span_set_stepcf,
            'but_stepcf_set_span': form.on_stepcf_set_span,
            'but_span_set_div2': form.on_span_half,
            'but_span_set_mul2': form.on_span_double,
        },

        # --- RBW, VBW ---
        'rbw': {
            'rbw_type_filter': form.rbw_type_changed,
            **_updown(form, 'rbw'),
            'rbw_unit': form.on_rbw_unit_changed,
            'rbw_auto': form.on_rbw_auto_toggled,
            **_updown(form, 'vbw'),
            'vbw_unit': form.on_vbw_unit_changed,
            'vbw_auto': form.on_vbw_auto_toggled,
        },
        'sweep': {
            'combo_det': form.on_det_changed,
            'combo_trace_acc': form.on_trace_acc_changed,
            'radio_count': form.on_sweep_mode_changed,
            'tb_sweep_count': form.on_sweep_count_changed,
        },
    }[ctrl]
