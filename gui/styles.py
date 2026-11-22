import tempfile
from enum import StrEnum
from pathlib import Path

from function import resource_path

FRAME_RADIUS = 0
BORDER_COLOR = '#777777'
HEADER_COLOR = '#2c3e50'      # цвет заголовков секций
DISABLED_BG = '#c4c4c4'       # фон выключенных контролов
DISABLED_FG = '#777777'       # текст выключенных контролов
HEADER_BG = '#e8eef5'         # фон полосы заголовка
HEADER_HOVER_BG = "#d0d1d3"   # фон полосы при наведении
CTRL_ENABLE_TEXT = '#000000'
BORDER_CTRL_COLOR = '#ababab'
CTRL_HOVER_BG = '#e6e6e6'
CTRL_PRESSED_BG = '#d0d0d0'

PLOT_BTN_SIZE = 28        # квадрат кнопки панели действий, px
PLOT_BTN_ICON_SIZE = 20
PLOT_BTN_GAP = 4          # зазор кнопка↔рамка графика, px
PLOT_ACTIONS_STRIP_W = PLOT_BTN_SIZE + 2 * PLOT_BTN_GAP
COL_TOP = 24
COL_SPACING = 2

_ARROW = resource_path("gui/icons/combo_arrow.svg").replace("\\", "/")

# Для настройки основного графика
PLOT_GRID_COLOR = (120, 120, 120, 40)   # сетка главного графика
PLOT_GRID_WIDTH = 1

PLOT_N_HGRID_LINES = 20    # горизонтальных линий сетки
PLOT_N_VGRID_LINES = 9     # вертикальных

PLOT_LABEL_FONT_FAMILY = 'Segoe UI'
PLOT_LABEL_FONT_SIZE = 10  # pt, метка ошибок индикации
FONT_SIZE_CTRL = 9
PLOT_LABEL_FONT_BOLD = True


def plot_grid_pen():
    """Пен линий сетки главного графика (единственная точка стиля)."""
    import pyqtgraph as pg
    from PyQt6.QtCore import Qt
    return pg.mkPen(color=PLOT_GRID_COLOR, width=PLOT_GRID_WIDTH,
                    style=Qt.PenStyle.SolidLine)


def plot_background_color():
    """Цвет фона полотна графика.

    'palette' — цвет окна из системной палитры (поддержка тем),
    строка-хекс — фиксированный цвет.
    """
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication
    if Style.PLOT_BACKGROUND == 'palette':
        return QApplication.instance().palette().color(
            QPalette.ColorRole.Window)
    return QColor(Style.PLOT_BACKGROUND)


def _make_arrow_svg(name: str, d: str, w: int, h: int) -> str:
    """Нарисовать шеврон в SVG с цветом заголовков и вернуть путь к файлу."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<path d="{d}" stroke="{HEADER_COLOR}" stroke-width="0.5" '
        'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    path = Path(tempfile.gettempdir()) / "analyzer_styles" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return str(path).replace("\\", "/")


_ARROW_DOWN = _make_arrow_svg(
    "arrow_down.svg", d="M0.75 0.5 L3 2.75 L5.25 0.5", w=6, h=3)
_ARROW_RIGHT = _make_arrow_svg(
    "arrow_right.svg", d="M0.5 0.75 L2.75 3 L0.5 5.25", w=3, h=6)
_ARROW_LEFT = _make_arrow_svg(
    "arrow_left.svg", d="M4.6 0.6 L2.3 2.5 L4.6 4.4", w=4, h=5)


class Style(StrEnum):
    """Управление стилями для элементов управления формы программы."""

    # Section Control
    LABEL_HEADER_SECTION = (
        f'font-weight: bold; color: {HEADER_COLOR};'
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "background-color: transparent;border: none;"
    )
    BUTTON_HEADER = (
        "QToolButton {"
        "border: none;padding: 0px;"
        "background-color: transparent;"
        "}"
        "QToolButton:hover { background-color: transparent; }"
        "QToolButton:pressed { background-color: transparent; }"
        "QToolButton:focus { background-color: transparent; }"
        f"QToolButton::down-arrow {{ image: url(\"{_ARROW_DOWN}\"); }}"
        f"QToolButton::right-arrow {{ image: url(\"{_ARROW_RIGHT}\"); }}"
        f"QToolButton::left-arrow {{ image: url(\"{_ARROW_LEFT}\"); }}"
    )
    CONTAINER_HEADER = (
        "QWidget {"
        "background-color: transparent;"
        "border: 1px solid transparent;"
        "padding: 2px 4px 2px 4px;"
        "}"
        "QWidget:hover {"
        f"border: 1px solid {BORDER_COLOR};"
        f"background-color: {HEADER_HOVER_BG};"
        "}"
    )
    WIDGET_SECTION = '.QWidget { border: none; }'

    # Поля QLineEdit для ввода значений
    TEXT_BOX = (
        "QLineEdit {"
        f"color: {CTRL_ENABLE_TEXT};"   # Цвет шрифта
        "background-color: #ffffff;"    # Фон
        f"border: 1px solid {BORDER_CTRL_COLOR};"    # Рамка
        "border-radius: 0px;"           # Скругления углов
        "padding: 0px 2px;"
        "min-height: 18px;max-height: 18px;"
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "selection-background-color: #3399ff;"
        "selection-color: #ffffff;"
        "qproperty-alignment: 'AlignHCenter|AlignVCenter';"  # Центровка
        "}"
        "QLineEdit:disabled {"
        f"color: {DISABLED_FG};"
        f"background-color: {DISABLED_BG};"
        "border-color: #bbbbbb;"
        "}"
    )

    # Подписи к полям в секциях — полный набор
    LBL_ROW = (
        "qproperty-alignment: 'AlignLeft|AlignVCenter';"
        f"color: {CTRL_ENABLE_TEXT};"     # Цвет шрифта
        "background-color: transparent;"  # Фон — прозрачный
        "border: none;"                   # Без рамки
        "min-height: 18px;"               # Высота (строки полей выровнены)
        "max-height: 18px;"
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"        # Тип шрифта
        f"font-size: {FONT_SIZE_CTRL}pt;"                  # Размер шрифта
    )

    FRAME_BORDER = f'1px solid {BORDER_COLOR}'

    # Квадратные кнопки
    BUT_SQUARE = (
        "QPushButton {"
        f"color: {CTRL_ENABLE_TEXT};"
        "background-color: transparent;"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "border-radius: 1px;"
        "padding: 0px 1px;"
        "min-height: 18px; max-height: 18px;"
        "min-width: 18px; max-width: 18px;"
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "}"
        "QPushButton:hover { background-color: #e6e6e6; }"
        "QPushButton:pressed { background-color: #d0d0d0; }"
        "QPushButton:disabled {"
        f"color: {DISABLED_FG};"
        f"background-color: {DISABLED_BG};"
        "border-color: #bbbbbb;"
        "}"
    )

    # Высоты элементов
    H_20 = (
        "QPushButton {"
        f"color: {CTRL_ENABLE_TEXT};"
        "background-color: transparent;"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "border-radius: 0px;"
        "padding: 0px 8px;"
        "min-height: 18px;max-height: 18px;"
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "}"
        "QPushButton:hover { background-color: #e6e6e6; }"
        "QPushButton:pressed { background-color: #d0d0d0; }"
    )

    COMBO_BOX = (
        "QComboBox {"
        "background-color: #ffffff;"
        f"color: {CTRL_ENABLE_TEXT};"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "border-radius: 0px;"
        "padding: 0px 0px 0px 6px;"      # правый отступ меньше — место стрелке
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "min-height: 18px;max-height: 18px;"
        "}"
        "QComboBox:disabled {"
        f"color: {DISABLED_FG};"
        f"background-color: {DISABLED_BG};"
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
        f"color: {CTRL_ENABLE_TEXT};"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "selection-background-color: #3399ff;"
        "selection-color: #ffffff;"
        "}"
    )

    # Конкретные кнопки
    VAL_CFSTEP_TO_SPAN = (
        "QPushButton {"
        f"color: {CTRL_ENABLE_TEXT};"
        "background-color: transparent;"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "border-radius: 0px;"
        "padding: 0px;"
        "min-height: 18px;max-height: 18px;"
        "min-width: 45px;max-width: 45px;"
        f"font-family: '{PLOT_LABEL_FONT_FAMILY}';"
        f"font-size: {FONT_SIZE_CTRL}pt;"
        "}"
        "QPushButton:disabled {"
        f"color: {DISABLED_FG};"
        f"background-color: {DISABLED_BG};"
        "border-color: #bbbbbb;"
        "}"
        "QPushButton:hover { background-color: #e6e6e6; }"
        "QPushButton:pressed { background-color: #d0d0d0; }"
    )
    BUT_SPAN_TO_STEPCF = VAL_CFSTEP_TO_SPAN.replace(
        "min-width: 45px;max-width: 45px;",
        "min-width: 66px;max-width: 66px;"
    )

    # Квадратные кнопки только с иконкой (панель справа от графика)
    BUT_ICON = (
        "QToolButton {"
        "background-color: transparent;"
        f"border: 1px solid {BORDER_CTRL_COLOR};"
        "border-radius: 1px;"
        "padding: 0px;"
        "}"
        "QToolButton:hover { background-color: #e6e6e6; }"
        "QToolButton:pressed { background-color: #d0d0d0; }"
        "QToolButton:checked { background-color: #d0d0d0; }"
        "QToolButton:disabled {"
        f"color: {DISABLED_FG};"
        f"background-color: {DISABLED_BG};"
        "border-color: #bbbbbb;"
        "}"
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
        f"border: 1px solid {BORDER_CTRL_COLOR}; "     # Тонкая серая рамка
        "min-height: 18px;"
        "max-height: 18px;"
        # "border-radius: 2px; "          # Небольшое скругления
        # "padding: 2px 5px; "            # Отступы внутри рамки
        "background-color: #ffffff;"      # Белый фон под текстом
    )

    MAIN_TRACE_COLOR = "#5353fd"    # основной график трассы
    ACC_TRACE_COLOR_1 = '#d9822b'   # кривая доп. трассы 1
    ACC_TRACE_COLOR_2 = '#4aa52f'   # кривая доп. трассы 2
    MARKER_COLOR_1 = "#b83dc4"   # маркер М1
    MARKER_COLOR_2 = "#00a0a0"   # маркер М2

    PLOT_LABEL_COLOR = CTRL_ENABLE_TEXT     # метки CF/Span/Div/RBW-VBW
    PLOT_ERRORS_LABEL_COLOR = "#ff0000"   # UNCAL, OVLD, ... — индикация ошибок
    PLOT_BACKGROUND = 'palette'
