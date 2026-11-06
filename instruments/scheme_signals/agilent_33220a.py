from PyQt6.QtWidgets import QMainWindow


def callbacks_map(form: QMainWindow):
    """Сопоставить элементам управления сигналы для УПРАВЛЕНИЯ ГЕНЕРАТОРОМ"""

    return {
        "tb_freq_sin": form.on_singen_freq_changed,
        "tb_lvl_sound": form.on_singen_lvl_changed,
        "combo_form_sound": form.on_singen_form_changed,
        "check_on_sound": form.on_singen_output_changed,
    }
