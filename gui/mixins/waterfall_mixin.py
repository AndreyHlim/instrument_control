from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout

from gui.controls.controls import CollapsibleSection
from gui.spectrogram import Waterfall


class WaterfallMixin:
    """Миксин: панель спектрограммы (водопада) под основным графиком.

    Предполагается, что у окна есть:
    - self.widget_6 (контейнер под графиком из .ui-файла);
    - self.plotWidget (PlotWidget основного графика — PlotMixin).
    """

    WATERFALL_COLLAPSED = True   # True — стартовать свёрнутым

    def settings_waterfall(self) -> None:
        """Поместить водопад в сворачивающуюся секцию под графиком."""
        layout = self.widget_6.layout()
        if layout is None:
            layout = QVBoxLayout(self.widget_6)
            layout.setContentsMargins(0, 0, 0, 0)

        self._waterfall = Waterfall(main_plot=self.plotWidget)
        self._waterfall.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._waterfall.setMinimumHeight(150)

        self.sec_waterfall = CollapsibleSection("Водопад")
        self.sec_waterfall.add_row_layout('', self._waterfall)
        self.sec_waterfall._toggle(not self.WATERFALL_COLLAPSED)
        layout.addWidget(self.sec_waterfall)
