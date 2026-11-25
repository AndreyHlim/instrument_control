import os

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)

from constants import DEFAULT_PATH
from function import resource_path
from gui.styles import CTRL_ALERT_COLOR, Style


class WorkDirMixin:
    """Миксин: глобальная рабочая директория программы.

    Хранит путь, отображает его на правой панели (tb_workdir + кнопка
    but_workdir), персистентен через QSettings. Дефолт — DEFAULT_PATH
    из constants; если он не существует на диске, используется
    домашний каталог пользователя.

    Использование: os.path.join(self.work_dir(), 'файл.txt') —
    стартовая папка диалогов сохранения/загрузки и любых будущих
    действий методов измерений.
    """

    _SETTINGS_ORG = 'Measurements'
    _SETTINGS_APP = 'AnalyzerGUI'
    _SETTINGS_KEY = 'work_dir'

    def preparation_workdir(self) -> None:
        """Определить рабочую директорию на запуск (вызывается из main).

        Каждый запуск стартует с DEFAULT_PATH. Если диск/папка недоступны
        (съёмный носитель, удалённый каталог) — фолбэк на домашний
        каталог, чтобы диалоги не открывались в пустоту.
        """
        path = (DEFAULT_PATH if os.path.isdir(DEFAULT_PATH)
                else os.path.expanduser('~'))
        self._work_dir = path

    def work_dir(self) -> str:
        """Текущая рабочая директория (строкой, без trailing-слэша)."""
        return self._work_dir

    def _set_work_dir(self, path: str) -> None:
        """Присвоить рабочую директорию: поле, тултип, курсор, цвет."""
        self._work_dir = path
        self.tb_workdir.setText(path)
        self.tb_workdir.setToolTip(path)
        self.tb_workdir.setCursorPosition(len(path))
        self._apply_workdir_color()

    def _build_workdir_row(self) -> None:
        """Собрать блок панели: подпись над полем пути + две кнопки.

        Кнопка '…' — выбор рабочей директории, кнопка с иконкой папки —
        открыть её в проводнике системы. Поле readOnly: путь меняется
        только через диалог. Курсор принудительно ставится в конец
        текста — при длинном пути виден его «хвост» (имя текущей
        папки), а не начало с D:\\...; полный путь — в тултипе.
        """
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        label = QLabel('Рабочая папка')
        label.setStyleSheet(Style.LBL_ROW)
        lay.addWidget(label)

        row = QWidget()
        hlay = QHBoxLayout(row)
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(3)

        self.tb_workdir = QLineEdit(self._work_dir)
        self.tb_workdir.setReadOnly(True)
        self.tb_workdir.setStyleSheet(Style.TEXT_BOX)
        self.tb_workdir.setToolTip(self._work_dir)
        self.tb_workdir.setCursorPosition(len(self._work_dir))
        hlay.addWidget(self.tb_workdir, 1)

        self.but_workdir_open = QPushButton()
        self.but_workdir_open.setIcon(
            QIcon(resource_path('gui/icons/open_folder.png')))
        self.but_workdir_open.setStyleSheet(Style.BUT_SQUARE)
        self.but_workdir_open.setToolTip('Открыть папку в проводнике')
        self.but_workdir_open.clicked.connect(self._on_but_workdir_open)
        hlay.addWidget(self.but_workdir_open, 0)

        self.but_workdir = QPushButton('…')
        self.but_workdir.setStyleSheet(Style.BUT_SQUARE)
        self.but_workdir.setToolTip('Выбрать рабочую директорию')
        self.but_workdir.clicked.connect(self._on_but_workdir_clicked)
        hlay.addWidget(self.but_workdir, 0)

        lay.addWidget(row)
        self.layout_right.addRow(box)

        self._apply_workdir_color()

    def _on_but_workdir_clicked(self) -> None:
        """Диалог выбора рабочей директории с записью в QSettings."""
        path = QFileDialog.getExistingDirectory(
            self, 'Выбор рабочей директории', self._work_dir)
        if path:
            self._set_work_dir(path)

    def _on_but_workdir_open(self) -> None:
        """Открыть рабочую директорию средствами ОС.

        Путь проверяется перед запуском: папка могла быть удалена
        после выбора — тогда открываем ближайший существующий
        родитель, а не молча игнорируем клик.
        """
        path = self._work_dir
        while not os.path.isdir(path):
            parent = os.path.dirname(path)
            if parent == path:      # добрались до корня — нечего открывать
                return
            path = parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _apply_workdir_color(self) -> None:
        """Красный текст поля, пока рабочая папка — DEFAULT_PATH.

        Сигнал: директория ещё дефолтная. Пользовательский выбор через
        диалог (или уход за файлом через диалог сохранения) возвращает
        обычный цвет. Сравнение нормализовано: диалог может вернуть
        тот же путь с другим регистром диска или разделителями.
        """
        same = (os.path.normcase(os.path.normpath(self._work_dir))
                == os.path.normcase(os.path.normpath(DEFAULT_PATH)))
        self.tb_workdir.setStyleSheet(
            Style.TEXT_BOX
            + (f"QLineEdit {{ color: {CTRL_ALERT_COLOR}; }}" if same else ''))
