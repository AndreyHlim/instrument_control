import sys

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from function import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = resource_path("gui/interface.ui")
        uic.loadUi(ui_path, self)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    path_icon = resource_path('gui/icon.ico')
    win.setWindowIcon(QIcon(path_icon))
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
