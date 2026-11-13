from PyQt6 import sip
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QSizePolicy,
                             QSpacerItem, QToolButton, QVBoxLayout, QWidget)

from gui.controls import fsva3013_ctrl as FSVA
from gui.controls.agilent_33220a import SECTION_SINGEN
from gui.controls.connect import SECTION_INSTR
from gui.controls.controls import CollapsibleSection
from gui.styles import Style


class PanelsMixin:
    """Миксин: инициализация трёх панелей окна (левая, средняя, правая).

    Левая — секции управления (CollapsibleSection), средняя — графики
    (настройка конкретного графика живёт в PlotMixin), правая — заготовка.
    """
    RIGHT_PANEL_MIN_W = 300   # развёрнутая панель
    RIGHT_PANEL_MAX_W = 360

    def settings_panels(self) -> None:
        """Инициализировать все панели окна. Одна точка входа из main."""
        self.settings_left_panel()
        self.settings_mid_panel()
        self.settings_right_panel()

    def settings_left_panel(self) -> None:
        """Создать и наполнить сворачивающиеся секции левой панели."""
        layout = self.findChild(QFormLayout, 'layout_left')
        layout.setSpacing(5)

        self.sec_instr = CollapsibleSection("Подключение к приборам")
        self.sec_instr.add_inputs(SECTION_INSTR)
        self.sec_instr._toggle(True)

        self.sec_singen = CollapsibleSection("Управление генератором НЧ")
        self.sec_singen.add_inputs(SECTION_SINGEN)
        self.sec_singen._toggle(False)

        self.sec_ampl = CollapsibleSection("Амплитуда")
        self.sec_ampl.add_inputs(FSVA.SECTION_AMP)
        self.sec_ampl._toggle(False)

        self.sec_freq = CollapsibleSection("Частота")
        self.sec_freq.add_inputs(FSVA.SECTION_FREQ)
        self.sec_freq._toggle(False)

        self.sec_rbw = CollapsibleSection("RBW, VBW")
        self.sec_rbw.add_inputs(FSVA.SECTION_RBW)
        self.sec_rbw._toggle(False)

        self.sec_sweep = CollapsibleSection("Sweep")
        self.sec_sweep.add_inputs(FSVA.SECTION_SWEEP)
        self.sec_sweep._toggle(False)

        self.sec_traces = CollapsibleSection("Traces")
        self.sec_traces.add_inputs(FSVA.SECTION_TRACES)
        self.sec_traces._toggle(False)

        self.sec_mrk = CollapsibleSection("Markers")
        self.sec_mrk.add_inputs(FSVA.SECTION_MRK)
        self.sec_mrk._toggle(False)

        layout.addWidget(self.sec_instr)
        layout.addWidget(self.sec_singen)
        layout.addWidget(self.sec_ampl)
        layout.addWidget(self.sec_freq)
        layout.addWidget(self.sec_rbw)
        layout.addWidget(self.sec_sweep)
        layout.addWidget(self.sec_traces)
        layout.addWidget(self.sec_mrk)

    def settings_mid_panel(self) -> None:
        """Настроить среднюю панель: графики и сопутствующие элементы."""
        self.settings_results()    # <- от ResultsMixin
        self.settings_plot()       # <- от PlotMixin
        self.settings_waterfall()  # <- от WaterfallMixin

    def settings_right_panel(self) -> None:
        """Свернуть правую панель под кнопку-стрелку (как секции слева).

        layout_right из .ui пуст и не может быть «переложен» на другой
        виджет — Qt запрещает переносить родительский лейаут. Удаляем
        его и создаём заново с тем же именем внутри контейнера, который
        скрывается кнопкой. Будущие секции добавляются в
        self.layout_right как раньше.
        """
        old = self.widget_3.layout()
        if old is not None:
            sip.delete(old)

        content = QWidget()
        self.layout_right = QFormLayout(content)
        self.layout_right.setObjectName('layout_right')
        self.layout_right.setContentsMargins(0, 5, 5, 5)
        self.layout_right.setHorizontalSpacing(3)
        self.layout_right.setVerticalSpacing(5)

        header = QHBoxLayout()
        header.setContentsMargins(0, 4, 0, 4)
        header.setSpacing(4)

        self.but_right_toggle = QToolButton()
        self.but_right_toggle.setCheckable(True)
        self.but_right_toggle.setChecked(True)
        self.but_right_toggle.setArrowType(Qt.ArrowType.DownArrow)
        self.but_right_toggle.setStyleSheet(Style.BUTTON_HEADER)

        self.lbl_right_header = QLabel('Методы измерений')
        self.lbl_right_header.setStyleSheet(Style.LABEL_HEADER_SECTION)

        header.addWidget(self.but_right_toggle)
        header.addWidget(self.lbl_right_header)
        header.addStretch()

        header_container = QWidget()
        header_container.setLayout(header)
        header_container.setStyleSheet(Style.CONTAINER_HEADER)

        lay = QVBoxLayout(self.widget_3)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(header_container, 0, Qt.AlignmentFlag.AlignTop)
        lay.addWidget(content)

        self._right_content = content

        self.but_right_toggle.toggled.connect(self._toggle_right_panel)
        self._toggle_right_panel(True)

        # Секции методов (будущие измерения)
        self._create_method_sections()

        # Всё лишнее место — в пустую строку ниже секций (прижать к верху)
        spacer = QSpacerItem(
            20, 0,
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout_right.setItem(
            self.layout_right.rowCount(),
            QFormLayout.ItemRole.SpanningRole, spacer)

        header_container.mousePressEvent = lambda event: (
            self.but_right_toggle.setChecked(
                not self.but_right_toggle.isChecked()))

    def _toggle_right_panel(self, checked: bool) -> None:
        """Показать/скрыть правую панель по горизонтали (к правому краю)."""
        self._right_content.setVisible(checked)
        self.lbl_right_header.setVisible(checked)
        if checked:
            self.widget_3.setMinimumWidth(self.RIGHT_PANEL_MIN_W)
            self.widget_3.setMaximumWidth(self.RIGHT_PANEL_MAX_W)
            self.but_right_toggle.setArrowType(Qt.ArrowType.RightArrow)
        else:
            self.widget_3.setMinimumWidth(0)
            self.widget_3.setMaximumWidth(
                self.but_right_toggle.sizeHint().width() + 8)
            self.but_right_toggle.setArrowType(Qt.ArrowType.LeftArrow)

    def _create_method_sections(self) -> None:
        """Создать секции методов измерений на правой панели.

        Секции стартуют свёрнутыми, как «Амплитуда». Контент каждой
        добавляется через add_inputs со своей схемой, когда он появится.
        """
        self.sec_method_1 = self._add_method_section('Метод измерений 1')
        self.sec_method_2 = self._add_method_section('Метод измерений 2')
        self.sec_method_3 = self._add_method_section('Метод измерений 3')

    def _add_method_section(self, title: str) -> CollapsibleSection:
        """Создать одну секцию метода: свёрнутая, прижата к верху панели."""
        section = CollapsibleSection(title)
        section._toggle(False)
        self.layout_right.addWidget(section)
        return section
