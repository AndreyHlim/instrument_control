from PyQt6.QtWidgets import QFormLayout

from gui.controls import fsva3013_ctrl as FSVA
from gui.controls.agilent_33220a import SECTION_SINGEN
from gui.controls.connect import SECTION_INSTR
from gui.controls.controls import CollapsibleSection


class PanelsMixin:
    """Миксин: инициализация трёх панелей окна (левая, средняя, правая).

    Левая — секции управления (CollapsibleSection), средняя — графики
    (настройка конкретного графика живёт в PlotMixin), правая — заготовка.
    """

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
        self.settings_plot()       # <- от PlotMixin
        self.settings_waterfall()  # <- от WaterfallMixin

    def settings_right_panel(self) -> None:
        """Заготовка под будущую правую панель."""
