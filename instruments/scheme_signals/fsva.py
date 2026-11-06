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
            **_updown(form, 'reflvl'),
            'amp_unit': form.on_amp_unit_changed,
            **_updown(form, 'ref_range'),
            'combo_preamp': form.on_preamp_changed,
            **_updown(form, 'atten'),
            'combo_transducer': form.on_trans_changed,
        },

        # --- ЧАСТОТА / SPAN / ШАГ ---
        'freq': {
            **_updown(form, 'cf'),
            **_updown(form, 'span'),
            'tb_cfstep': form.on_cfstep_changed,
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
