import sys

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from function import resource_path
from gui.mixins.connection_mixin import ConnectionMixin
from gui.mixins.controls_mixin import ControlsMixin
from gui.mixins.panels_mixin import PanelsMixin
from gui.mixins.plot_mixin import PlotMixin
from gui.mixins.signals_mixin import SignalsMixin
from gui.mixins.state_mixin import StateMixin
from gui.mixins.waterfall_mixin import WaterfallMixin


class MainWindow(
    QMainWindow, PanelsMixin, WaterfallMixin, PlotMixin, StateMixin,
    ControlsMixin, ConnectionMixin, SignalsMixin,
):
    def __init__(self):
        super().__init__()
        ui_path = resource_path("gui/interface.ui")
        self.setWindowIcon(QIcon(resource_path('gui/icon.ico')))
        uic.loadUi(ui_path, self)

        self.settings_panels()
        self.preparation_variables()
        self.initialization_form_elements_connect()
        self.initialization_form_elements_fsva()
        self.signal_connection()

    def closeEvent(self, event):
        self._stop_trace_thread()
        if self._analyzer is not None:
            self._analyzer.close()
        self._set_analyzer_controls_enabled(False)
        event.accept()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
