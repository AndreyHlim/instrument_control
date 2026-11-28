import sys

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from function import resource_path
from gui.mixins.acc_traces_mixin import AccTracesMixin
from gui.mixins.connection_mixin import ConnectionMixin
from gui.mixins.controls_mixin import ControlsMixin
from gui.mixins.markers_mixin import MarkersMixin
from gui.mixins.methods.method1 import Method1Mixin
from gui.mixins.panels_mixin import PanelsMixin
from gui.mixins.plot_actions_mixin import PlotActionsMixin
from gui.mixins.plot_mixin import PlotMixin
from gui.mixins.results.method1 import Method1ResultsMixin
from gui.mixins.results_mixin import ResultsMixin
from gui.mixins.signals_mixin import SignalsMixin
from gui.mixins.state_mixin import StateMixin
from gui.mixins.waterfall_mixin import WaterfallMixin
from gui.mixins.workdir_mixin import WorkDirMixin


class MainWindow(
    QMainWindow, PanelsMixin, WaterfallMixin, ResultsMixin, PlotMixin,
    PlotActionsMixin, StateMixin, ControlsMixin, MarkersMixin,
    ConnectionMixin, SignalsMixin, AccTracesMixin, WorkDirMixin,
    Method1ResultsMixin, Method1Mixin,
):
    def __init__(self):
        super().__init__()
        ui_path = resource_path("gui/interface.ui")
        self.setWindowIcon(QIcon(resource_path('gui/icon.ico')))
        uic.loadUi(ui_path, self)

        self.preparation_workdir()
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
    win.setWindowTitle("Управление измерениями")
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
