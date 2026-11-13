from PyQt6.QtWidgets import QVBoxLayout

from gui.spectrogram import Waterfall


class WaterfallMixin:
    """Миксин: панель спектрограммы (водопада) под основным графиком.

    Предполагается, что у окна есть:
    - self.widget_6 (контейнер под графиком из .ui-файла);
    - self.plotWidget (PlotWidget основного графика — PlotMixin);
    """

    def settings_waterfall(self) -> None:
        """Поместить водопад в widget_6 под графиком."""
        layout = self.widget_6.layout()
        if layout is None:
            layout = QVBoxLayout(self.widget_6)
            layout.setContentsMargins(0, 0, 0, 0)
        self._waterfall = Waterfall(main_plot=self.plotWidget)
        layout.addWidget(self._waterfall)

    def add_waterfall_frame(self, levels, vmin=None, vmax=None) -> None:
        """Добавить строку в водопад по текущему кадру трассы.

        Прокладка между PlotMixin (кадры из update_state) и Waterfall:
        все вызовы идут через неё, PlotMixin не знает устройство
        водопада. Будущие режимы и условия добавления строк меняются
        здесь, не трогая PlotMixin.
        """
        self._waterfall.add_frame(levels, vmin=vmin, vmax=vmax)
