from PyQt6.QtWidgets import QVBoxLayout, QWidget

from gui.controls.controls import CollapsibleSection


class ResultsMixin:
    """Миксин: панель результатов измерений над основным графиком.

    Предполагается, что у окна есть:
    - self.widget_4 (контейнер над графиком из .ui-файла).
    """

    RESULTS_COLLAPSED = True   # True — стартовать свёрнутым

    def settings_results(self) -> None:
        """Обернуть widget_4 в сворачивающуюся секцию (заготовка).

        Контент секции — пустой контейнер self._results_content;
        в будущем сюда добавится линейный график результатов.
        """
        layout = self.widget_4.layout()
        if layout is None:
            layout = QVBoxLayout(self.widget_4)
            layout.setContentsMargins(0, 0, 0, 0)

        self._results_content = QWidget()
        self._results_content = QWidget()
        self._results_content.setMinimumHeight(200)

        self.sec_results = CollapsibleSection("Результаты измерений")
        self.sec_results.add_row_layout('', self._results_content)
        self.sec_results._toggle(not self.RESULTS_COLLAPSED)
        layout.addWidget(self.sec_results)
