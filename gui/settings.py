
from PyQt6.QtWidgets import QFormLayout

from gui.controls import fsva3013_ctrl as FSVA
from gui.controls.agilent_33220a import SECTION_SINGEN
from gui.controls.connect import SECTION_INSTR
from gui.controls.controls import CollapsibleSection


def set_layout_left(layout: QFormLayout):
    """Настройка скрывающийхся списков в левой части окна программы."""

    layout.setSpacing(5)

    # 1. Создание секции "ПОДКЛЮЧЕНИЕ К ПРИБОРАМ"
    sec_indtr = CollapsibleSection("Подключение к приборам")
    sec_indtr.add_inputs(SECTION_INSTR)
    sec_indtr._toggle(True)

    # 2. Создание секции "УПРАВЛЕНИЕ ГЕНЕРАТОРОМ НЧ"
    sec_singen = CollapsibleSection("Управление генератором НЧ")
    sec_singen.add_inputs(SECTION_SINGEN)
    sec_singen._toggle(False)

    # 3. Создание секции "АМПЛИТУДА"
    sec_ampl = CollapsibleSection("Амплитуда")
    sec_ampl.add_inputs(FSVA.SECTION_AMP)
    sec_ampl._toggle(False)

    # 4. Создание секции "ЧАСТОТА"
    sec_freq = CollapsibleSection("Частота")
    sec_freq.add_inputs(FSVA.SECTION_FREQ)
    sec_freq._toggle(False)

    # 5. Создание секции "ЧАСТОТА"
    sec_rbw = CollapsibleSection("RBW, VBW")
    sec_rbw.add_inputs(FSVA.SECTION_RBW)
    sec_rbw._toggle(False)

    # 6. Создание секции "SWEEP"
    sec_sweep = CollapsibleSection("Sweep")
    sec_sweep.add_inputs(FSVA.SECTION_SWEEP)
    sec_sweep._toggle(False)

    # 7. Создание секции "Traces"
    sec_traces = CollapsibleSection("Traces")
    sec_traces.add_inputs(FSVA.SECTION_TRACES)
    sec_traces._toggle(False)

    # 8. Создание секции "Traces"
    sec_mrk = CollapsibleSection("Markers")
    sec_mrk.add_inputs(FSVA.SECTION_MRK)
    sec_mrk._toggle(False)

    # Добавление секций на форму программы
    layout.addWidget(sec_indtr)
    layout.addWidget(sec_singen)
    layout.addWidget(sec_ampl)
    layout.addWidget(sec_freq)
    layout.addWidget(sec_rbw)
    layout.addWidget(sec_sweep)
    layout.addWidget(sec_traces)
    layout.addWidget(sec_mrk)
