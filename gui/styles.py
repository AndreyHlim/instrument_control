from enum import StrEnum


class Style(StrEnum):
    """Управление стилями для элементов управления формы программы."""

    # Section Control
    LABEL_HEADER_SECTION = 'font-weight: bold; color: #2c3e50; border: none;'
    BUTTON_HEADER = 'QToolButton { border: none; padding: 0px; }'
    CONTAINER_HEADER = 'border: none; margin: 0px; padding: 0px;'
    WIDGET_SECTION = '.QWidget { border: none; }'

    # Поля QLineEdit для ввода значений
    TEXT_BOX = (
        "qproperty-alignment: 'AlignHCenter|AlignVCenter';"
        "min-height: 18px;"
        "max-height: 18px;"
        "border: 1px solid #ababab;"
        "background-color: #ffffff;"
    )

    # Квадратные кнопки
    BUT_SQUARE = (
        "min-height: 20px;"
        "max-height: 20px;"
        "min-width: 20px;"
        "max-width: 20px;"
    )

    # Высоты элементов
    H_20 = "min-height: 20px;max-height: 20px;"
    H_18 = "min-height: 18px;max-height: 18px;"

    # Конкретные кнопки
    BUT_SPAN_TO_STEPCF = (
        "min-height: 20px;"
        "max-height: 20px;"
        "min-width: 50px;"
        "max-width: 50px;"
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
        "max-height: 18px;}"
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
