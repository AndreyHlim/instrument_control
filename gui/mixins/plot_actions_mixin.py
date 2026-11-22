from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QToolButton, QVBoxLayout, QWidget

from function import resource_path
from gui.styles import (COL_SPACING, COL_TOP, PLOT_ACTIONS_STRIP_W,
                        PLOT_BTN_GAP, PLOT_BTN_ICON_SIZE, PLOT_BTN_SIZE, Style)


class PlotActionsMixin:
    """Миксин: колонка кнопок поверх правого края основного графика.

    Кнопки — плавающий ребёнок plotWidget (приём как у панели шкалы
    водопада): живут в пустой полосе правого поля осей, внутри рамки
    графика, не входят ни в какой layout.
    """

    ACTIONS = (
        ('but_screen', 'screen.png', 'Сделать скриншот основного графика'),
        ('but_save_txt', 'to_txt.png', 'Сохранить трассы в файл txt'),
        ('but_open_screen_data', 'open_screen.png', 'Открыть данные графиков'),
        ('but_pausa', 'pausa.png', 'Пауза'),
    )

    def settings_plot_actions(self) -> None:
        """Создать плавающую колонку кнопок поверх plotWidget.

        Вызывается после settings_plot: правое поле осей уже расширено
        под полосу кнопок (PLOT_ACTIONS_STRIP_W), геометрия виджета
        ещё нулевая — позиционирование делается в singleShot(0) и далее
        по каждому resize (eventFilter PlotMixin).
        """
        col = QWidget(self.plotWidget)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(COL_SPACING)

        self._plot_action_btns = {}
        for name, icon_file, tip in self.ACTIONS:
            btn = QToolButton(col)
            btn.setObjectName(name)
            btn.setToolTip(tip)
            btn.setStyleSheet(Style.BUT_ICON)
            btn.setFixedSize(PLOT_BTN_SIZE, PLOT_BTN_SIZE)
            btn.setIcon(QIcon(resource_path(f'gui/icons/{icon_file}')))
            btn.setIconSize(QSize(PLOT_BTN_ICON_SIZE, PLOT_BTN_ICON_SIZE))
            if name == 'but_pausa':
                btn.setCheckable(True)
                btn.toggled.connect(self._on_pausa_toggled)
            else:
                btn.clicked.connect(getattr(self, f'_{name}_clicked'))
            lay.addWidget(btn)
            self._plot_action_btns[name] = btn
        # Без addStretch: колонка ровно по высоте кнопок, не растягивается

        col.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        col.raise_()
        self._plot_actions_col = col
        QTimer.singleShot(0, self._place_plot_actions_col)

    def _place_plot_actions_col(self) -> None:
        """Уложить колонку в пустую полосу правого поля осей.

        Полоса — последние PLOT_ACTIONS_STRIP_W пикселей ширины виджета.
        Кнопки центрируются в ней; рамка графика остаётся правее всех
        кликабельных зон, кнопки не её перекрывают.
        """
        col = getattr(self, '_plot_actions_col', None)
        if col is None:
            return
        w = self.plotWidget
        if w.width() < PLOT_ACTIONS_STRIP_W:
            col.setVisible(False)
            return
        strip_left = w.width() - PLOT_ACTIONS_STRIP_W
        x = strip_left + PLOT_BTN_GAP   # ровно PLOT_BTN_GAP от рамки
        col.setGeometry(x, COL_TOP, PLOT_BTN_SIZE,
                        col.sizeHint().height())
        col.setVisible(True)
        col.raise_()   # поверх рамки-накладки после её raise_ в settings_plot

    # --- Обработчики (часть — заглушки, наполнение позже) ---------------
    def _but_screen_clicked(self) -> None:
        """Диалог сохранения графика в PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить график', 'trace', 'PNG (*.png)')
        if not path:
            return
        if not path.lower().endswith('.png'):
            path += '.png'
        self.plotWidget.grab().save(path)

    def _but_save_txt_clicked(self) -> None:
        """Диалог сохранения трассы в TXT. Запись — заглушка."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить в TXT', 'trace', 'TXT (*.txt)')
        if not path:
            return
        if not path.lower().endswith('.txt'):
            path += '.txt'
        self._save_trace_txt(path)

    def _save_trace_txt(self, path: str) -> None:
        """Заглушка: реальное сохранение трассы опишете позже."""
        print(f'[PLOT ACTIONS] save txt: {path}')

    def _but_open_screen_data_clicked(self) -> None:
        """Заглушка: открытие сохранённых данных экрана."""
        print('[PLOT ACTIONS] open screen data')

    def _on_pausa_toggled(self, checked: bool) -> None:
        """Заглушка: пауза обновления графика."""
        print(f'[PLOT ACTIONS] pausa: {"on" if checked else "off"}')
