from PyQt6.QtWidgets import QMainWindow


def callbacks_map_conn(form: QMainWindow):
    """Сопоставить элементам управления сигналы для ПОДКЛЮЧЕНИЯ К ПРИБОРАМ."""

    return {
        # Анализатор
        "but_analyzer_conn": form.on_analyzer_connect,
        "but_analyzer_web": lambda: form.open_analyzer_web(None),

        # НЧ генератор
        # "but_singen_conn": form.on_singen_connect,
        # "but_singen_web": form.open_singen_web,
    }
