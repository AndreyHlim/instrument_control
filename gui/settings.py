
from PyQt6.QtWidgets import QFormLayout, QMainWindow

from gui.controls import fsva3013_ctrl as FSVA
from gui.controls.agilent_33220a import SECTION_SINGEN
from gui.controls.connect import SECTION_INSTR
from gui.controls.controls import CollapsibleSection


def set_layout_left(form: QMainWindow, layout: QFormLayout):
    """Настройка скрывающийхся списков в левой части окна программы."""

    layout.setSpacing(5)

    # 1. Создание секции "ПОДКЛЮЧЕНИЕ К ПРИБОРАМ"
    form.sec_instr = CollapsibleSection("Подключение к приборам")
    form.sec_instr.add_inputs(SECTION_INSTR)
    form.sec_instr._toggle(True)

    # 2. Создание секции "УПРАВЛЕНИЕ ГЕНЕРАТОРОМ НЧ"
    form.sec_singen = CollapsibleSection("Управление генератором НЧ")
    form.sec_singen.add_inputs(SECTION_SINGEN)
    form.sec_singen._toggle(False)

    # 3. Создание секции "АМПЛИТУДА"
    form.sec_ampl = CollapsibleSection("Амплитуда")
    form.sec_ampl.add_inputs(FSVA.SECTION_AMP)
    form.sec_ampl._toggle(False)

    # 4. Создание секции "ЧАСТОТА"
    form.sec_freq = CollapsibleSection("Частота")
    form.sec_freq.add_inputs(FSVA.SECTION_FREQ)
    form.sec_freq._toggle(False)

    # 5. Создание секции "RBW, VBW"
    form.sec_rbw = CollapsibleSection("RBW, VBW")
    form.sec_rbw.add_inputs(FSVA.SECTION_RBW)
    form.sec_rbw._toggle(False)

    # 6. Создание секции "SWEEP"
    form.sec_sweep = CollapsibleSection("Sweep")
    form.sec_sweep.add_inputs(FSVA.SECTION_SWEEP)
    form.sec_sweep._toggle(False)

    # 7. Создание секции "Traces"
    form.sec_traces = CollapsibleSection("Traces")
    form.sec_traces.add_inputs(FSVA.SECTION_TRACES)
    form.sec_traces._toggle(False)

    # 8. Создание секции "Markers"
    form.sec_mrk = CollapsibleSection("Markers")
    form.sec_mrk.add_inputs(FSVA.SECTION_MRK)
    form.sec_mrk._toggle(False)

    # Добавление секций на форму программы
    layout.addWidget(form.sec_instr)
    layout.addWidget(form.sec_singen)
    layout.addWidget(form.sec_ampl)
    layout.addWidget(form.sec_freq)
    layout.addWidget(form.sec_rbw)
    layout.addWidget(form.sec_sweep)
    layout.addWidget(form.sec_traces)
    layout.addWidget(form.sec_mrk)
