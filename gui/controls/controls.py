from typing import Any, Dict, List, Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QRadioButton, QSizePolicy, QSpinBox, QToolButton,
                             QVBoxLayout, QWidget)

from function import resource_path
from gui.styles import Style


class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_expanded = True
        self.widgets: Dict[str, QWidget] = {}

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Заголовок ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 10, 5)
        header_layout.setSpacing(0)

        self.header_button = QToolButton()
        self.header_button.setCheckable(True)
        self.header_button.setChecked(True)
        self.header_button.setArrowType(Qt.ArrowType.DownArrow)
        self.header_button.setStyleSheet(Style.BUTTON_HEADER)

        self.header_button.toggled.connect(self._toggle_via_button)

        self.header_label = QLabel(title)
        self.header_label.setStyleSheet(Style.LABEL_HEADER_SECTION)

        header_layout.addWidget(self.header_button)
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()

        self.header_container = QWidget()
        self.header_container.setLayout(header_layout)
        self.header_container.mousePressEvent = self._on_header_click
        self.header_container.setStyleSheet(Style.CONTAINER_HEADER)

        layout.addWidget(self.header_container)

        # --- Контейнер контента ---
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 10, 5)
        self.content_layout.setHorizontalSpacing(15)
        self.content_layout.setVerticalSpacing(3)
        self.content_widget.setStyleSheet(Style.WIDGET_SECTION)

        layout.addWidget(self.content_widget)

    def _create_single_widget(self, item: Dict[str, Any]) -> QWidget:
        """Создание одного виджета по его описанию"""
        w_type = item.get("type")
        key = item.get("key")

        widget = None

        if w_type == "int":
            widget = QSpinBox()
            widget.setRange(item.get("min", 0), item.get("max", 100))
            widget.setValue(item.get("value", 0))

        elif w_type == "double":
            widget = QDoubleSpinBox()
            widget.setDecimals(item.get("decimals", 1))
            widget.setRange(item.get("min", 0.0), item.get("max", 100.0))
            widget.setValue(item.get("value", 0.0))
            widget.setSuffix(item.get("suffix", ""))
            if "style" in item:
                widget.setStyleSheet(item["style"])

        elif w_type == "combo":
            widget = QComboBox()
            widget.addItems(item.get("items", []))
            model = widget.model()
            for i in range(model.rowCount()):
                item_obj = model.item(i)
                if item_obj:
                    # Центрируем текст по горизонтали и вертикали
                    item_obj.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Дополнительно центрируем текст на самой плашке закрытого Combobox
            widget.setStyleSheet(
                "QComboBox {qproperty-alignment: "
                "'AlignHCenter|AlignVCenter';"
                "min-height: 18px;max-height: 18px;}"
            )
        elif w_type == "button":
            widget = QPushButton(item.get("text", ""))
            if len(item.get("text", "")) <= 3:
                widget.setMaximumWidth(30)
            if "style" in item:
                widget.setStyleSheet(item["style"])
            if "icon" in item and item["icon"]:
                widget.setIcon(QIcon(resource_path(item["icon"])))
                # Можно также опционально настраивать размер иконки:
                # widget.setIconSize(QtCore.QSize(16, 16))

        elif w_type == "checkbox":
            widget = QCheckBox(item.get("text", ""))
            widget.setChecked(item.get("value", False))

        elif w_type == "radio":
            widget = QRadioButton(item.get("text", ""))
            widget.setChecked(item.get("checked", False))

        if w_type == "custom":
            # Готовый виджет, собранный в коде (таблицы, списки и т.п.)
            widget = item.get("widget")

        elif w_type in ("vbox", "hbox"):
            inner = QVBoxLayout() if w_type == "vbox" else QHBoxLayout()
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(4)
            for sub in item.get("items", []):
                if sub.get("type") == "spacer":
                    inner.addStretch()
                    continue
                sub_widget = self._create_single_widget(sub)
                if sub_widget is not None:
                    if w_type == "hbox":
                        inner.addWidget(sub_widget, sub.get("stretch", 0))
                    else:
                        inner.addWidget(sub_widget)
            widget = QWidget()
            widget.setLayout(inner)

        elif w_type == "label":
            widget = QLabel(item.get("text", ""))
            if item.get("align") == "center":
                widget.setAlignment(
                    Qt.AlignmentFlag.AlignHCenter |
                    Qt.AlignmentFlag.AlignVCenter)
            elif item.get("align") == "right":
                widget.setAlignment(
                    Qt.AlignmentFlag.AlignRight |
                    Qt.AlignmentFlag.AlignVCenter)
            if "style" in item:
                widget.setStyleSheet(item["style"])

        elif w_type == "text_box":
            widget = QLineEdit(item.get("text", ""))
            if "style" in item:
                widget.setStyleSheet(item["style"])

        if widget and key:
            self.widgets[key] = widget

        return widget

    def add_row_layout(
        self, label_text: str, content: Union[QWidget, QHBoxLayout]
    ):
        """Добавление в сетку виджета или макета для кнопок"""
        current_row = self.content_layout.rowCount()

        if label_text:
            lbl = QLabel(label_text)
            lbl.setSizePolicy(QSizePolicy.Policy.Preferred,
                              QSizePolicy.Policy.Preferred)
            self.content_layout.addWidget(lbl, current_row, 0)

            if isinstance(content, QWidget):
                content.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Preferred)
                self.content_layout.addWidget(content, current_row, 1)
            else:
                self.content_layout.addLayout(content, current_row, 1)
        else:
            if isinstance(content, QWidget):
                content.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Preferred)
                self.content_layout.addWidget(content, current_row, 0, 1, 2)
            else:
                self.content_layout.addLayout(content, current_row, 0, 1, 2)

    def add_inputs(self, schema: List[Dict[str, Any]]):
        """Построение интерфейса с поддержкой пропорций stretch"""
        for item in schema:
            if "widgets" in item:
                label = item.get("label", "")
                row_hbox = QHBoxLayout()
                row_hbox.setContentsMargins(0, 0, 0, 0)
                row_hbox.setSpacing(3)

                for sub_item in item["widgets"]:
                    sub_widget = self._create_single_widget(sub_item)
                    if sub_widget:
                        if isinstance(sub_widget, QLabel):
                            sub_widget.setSizePolicy(
                                QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Preferred
                            )
                        else:
                            sub_widget.setSizePolicy(
                                QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Preferred
                            )

                        stretch_val = sub_item.get("stretch", 0)
                        row_hbox.addWidget(sub_widget, stretch_val)

                self.add_row_layout(label, row_hbox)
            else:
                label = item.get("label", "")
                widget = self._create_single_widget(item)
                if widget:
                    self.add_row_layout(label, widget)

    def connect_callbacks(self, mapping: Dict[str, Any]):
        """Массовое подключение обработчиков сигналов через словарь.

        Сигнал выбирается по типу виджета:
        QPushButton → clicked; QCheckBox/QRadioButton → toggled;
        QSpinBox/QDoubleSpinBox → valueChanged; QComboBox → currentTextChanged.

        Note:
            Виджеты без известного типа (например, QLabel) молча
            пропускаются. Для радиогруппы подключайте только одну
            кнопку группы — toggled придёт при любом переключении.
        """
        for key, callback in mapping.items():
            widget = self.widgets.get(key)
            if not widget:
                continue

            if isinstance(widget, QPushButton):
                widget.clicked.connect(callback)
            elif isinstance(widget, (QCheckBox, QRadioButton)):
                widget.toggled.connect(callback)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(callback)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(callback)

    def get_values(self) -> Dict[str, Any]:
        values = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[key] = widget.value()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QLabel):
                values[key] = widget.text()
        return values

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 4, 4)

    def _on_header_click(self, event):
        self._toggle(not self._is_expanded)

    def _toggle_via_button(self, checked: bool):
        self._toggle(checked)

    def _toggle(self, checked: bool):
        self._is_expanded = checked
        self.header_button.setArrowType(
            Qt.ArrowType.DownArrow if checked
            else Qt.ArrowType.RightArrow
        )
        self.header_button.setChecked(checked)
        self.content_widget.setVisible(checked)
        self.setMaximumHeight(16777215)
        self.updateGeometry()
