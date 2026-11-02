import sys

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QFormLayout, QMainWindow

from function import resource_path
from gui.settings import set_layout_left


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = resource_path("gui/interface.ui")
        path_icon = resource_path('gui/icon.ico')
        self.setWindowIcon(QIcon(path_icon))
        uic.loadUi(ui_path, self)

        self.layout_left = self.findChild(QFormLayout, 'layout_left')
        set_layout_left(self.layout_left)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
