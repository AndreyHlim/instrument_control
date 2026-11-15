from enum import StrEnum

from function import resource_path

FRAME_RADIUS = 0
BORDER_COLOR = '#777777'
_ARROW = resource_path("gui/icons/combo_arrow.svg").replace("\\", "/")


class Style(StrEnum):
    """Управление стилями для элементов управления формы программы."""

    # Section Control
    LABEL_HEADER_SECTION = 'font-weight: bold; color: #2c3e50; border: none;'
    BUTTON_HEADER = 'QToolButton { border: none; padding: 0px; }'
    CONTAINER_HEADER = 'border: none; margin: 0px; padding: 0px;'
    WIDGET_SECTION = '.QWidget { border: none; }'

    # Поля QLineEdit для ввода значений
    TEXT_BOX = (
        "QLineEdit {"
        "color: #000000;"               # Цвет шрифта
        "background-color: #ffffff;"    # Фон
        "border: 1px solid #ababab;"    # Рамка
        "border-radius: 0px;"           # Скругления углов
        "padding: 0px 2px;"
        "min-height: 18px;max-height: 18px;"
        "font-family: 'Segoe UI';font-size: 9pt;"
        "selection-background-color: #3399ff;"
        "selection-color: #ffffff;"
        "qproperty-alignment: 'AlignHCenter|AlignVCenter';"  # Центровка
        "}"
        "QLineEdit:disabled {"
        "color: #777777;"
        "background-color: #DADADA;"
        "border-color: #bbbbbb;"
        "}"
    )

    # Подписи к полям в секциях — полный набор
    LBL_ROW = (
        "qproperty-alignment: 'AlignLeft|AlignVCenter';"
        "color: #000000;"                 # Цвет шрифта
        "background-color: transparent;"  # Фон — прозрачный
        "border: none;"                   # Без рамки
        "min-height: 18px;"               # Высота (строки полей выровнены)
        "max-height: 18px;"
        "font-family: 'Segoe UI';"        # Тип шрифта
        "font-size: 9pt;"                 # Размер шрифта
    )

    FRAME_BORDER = '1px solid #777777'

    # Квадратные кнопки
    BUT_SQUARE = (
        "QPushButton {"
        "color: #000000;"
        "background-color: transparent;"
        "border: 1px solid #ababab;"
        "border-radius: 1px;"
        "padding: 0px 1px;"
        "min-height: 18px; max-height: 18px;"
        "min-width: 18px; max-width: 18px;"
        "font-family: 'Segoe UI';font-size: 9pt;"
        "}"
        "QPushButton:hover { background-color: #e6e6e6; }"
        "QPushButton:pressed { background-color: #d0d0d0; }"
        "QPushButton:disabled {"
        "color: #777777;"
        "background-color: #c4c4c4;"
        "border-color: #bbbbbb;"
        "}"
    )

    # Высоты элементов
    H_20 = (
        "QPushButton {"
        "color: #000000;"
        "background-color: transparent;"
        "border: 1px solid #ababab;"
        "border-radius: 0px;"
        "padding: 0px 8px;"
        "min-height: 18px;max-height: 18px;"
        "font-family: 'Segoe UI';font-size: 9pt;"
        "}"
        "QPushButton:hover { background-color: #e6e6e6; }"
        "QPushButton:pressed { background-color: #d0d0d0; }"
    )

    COMBO_BOX = (
        "QComboBox {"
        "background-color: #ffffff;"
        "color: #000000;"
        "border: 1px solid #ababab;"
        "border-radius: 0px;"
        "padding: 0px 4px 0px 8px;"      # правый отступ меньше — место стрелке
        "font-family: 'Segoe UI';font-size: 9pt;"
        "min-height: 18px;max-height: 18px;"
        "}"
        "QComboBox:disabled {"
        "color: #777777;"
        "background-color: #c4c4c4;"
        "border-color: #bbbbbb;"
        "}"
        "QComboBox::drop-down {"
        "subcontrol-origin: padding;"
        "subcontrol-position: center right;"
        "width: 18px;"
        "background: transparent;"
        "}"
        "QComboBox::down-arrow {"
        f'image: url("{_ARROW}");'
        "}"
        "QComboBox QAbstractItemView {"
        "background-color: #ffffff;"
        "color: #000000;"
        "border: 1px solid #ababab;"
        "selection-background-color: #3399ff;"
        "selection-color: #ffffff;"
        "}"
    )

    # Конкретные кнопки
    BUT_SPAN_TO_STEPCF = (
        "min-height: 20px;"
        "max-height: 20px;"
        "min-width: 68px;"
        "max-width: 68px;"
    )
    VAL_CFSTEP_TO_SPAN = (
        "min-height: 20px;"
        "max-height: 20px;"
        "min-width: 45px;"
        "max-width: 45px;"
    )

    # Все QDoubleSpinBox
    SPIN_BOX = (
        "qproperty-alignment:"
        "'AlignHCenter|AlignVCenter';"
        "min-height: 18px;"
        "max-height: 18px;"
    )

    # Label в рамке
    LBL_BORDER = (
        "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
        "border: 1px solid #ababab; "     # Тонкая серая рамка
        "min-height: 18px;"
        "max-height: 18px;"
        # "border-radius: 2px; "          # Небольшое скругления
        # "padding: 2px 5px; "            # Отступы внутри рамки
        "background-color: #ffffff;"      # Белый фон под текстом
    )
