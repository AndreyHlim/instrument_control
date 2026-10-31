from enum import StrEnum


class Style(StrEnum):
    """Управление стилями для элементов управления формы программы."""

    # Section Control
    LABEL_HEADER_SECTION = 'font-weight: bold; color: #2c3e50; border: none;'
    BUTTON_HEADER = 'QToolButton { border: none; padding: 0px; }'
    CONTAINER_HEADER = 'border: none; margin: 0px; padding: 0px;'
    WIDGET_SECTION = '.QWidget { border: none; }'

    # Кнопки перехода по IP адресу прибора для открытия его WEB интерфейса
    TEXT_BOX = (
        "qproperty-alignment: 'AlignHCenter|AlignVCenter';"
        "min-height: 18px;"
        "max-height: 18px;"
        "border: 1px solid #ababab;"
        "background-color: #ffffff;"
    )

    # Кнопки перехода по IP адресу прибора для открытия его WEB интерфейса
    BUT_WEB = (
        "min-height: 20px;"
        "max-height: 20px;"
        "min-width: 20px;"
        "max-width: 20px;"
    )

    # Высота элемента 20px
    H_20 = "min-height: 20px;max-height: 20px;"
