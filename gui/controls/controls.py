from typing import Any, Dict, List, Union

from PyQt6.QtCore import QRegularExpression, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QColor, QIcon, QPainter, QPen,
                         QRegularExpressionValidator)
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
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Заголовок ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 4, 0, 4)
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
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(3)
        self.content_layout.setVerticalSpacing(2)
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
        elif w_type == "freq_edit":
            widget = FreqLineEdit(item.get("text", ""))
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
        """Массовое подключение сигналов через словарь.

        Значение словаря:
        - callable — стандартный сигнал по типу виджета (clicked,
          toggled, valueChanged, currentTextChanged), для FreqLineEdit —
          freq_accepted;
        - dict {'<имя сигнала>': handler} — подключение по именам
          (для FreqLineEdit: 'freq_accepted', 'wheel_step').

        Note:
            Виджеты без известного типа (например, QLabel) молча
            пропускаются. Для радиогруппы подключайте только одну
            кнопку группы — toggled придёт при любом переключении.
        """
        for key, cb in mapping.items():
            widget = self.widgets.get(key)
            if not widget:
                continue

            if isinstance(cb, dict):
                for sig_name, handler in cb.items():
                    getattr(widget, sig_name).connect(handler)
                continue

            if isinstance(widget, QPushButton):
                widget.clicked.connect(cb)
            elif isinstance(widget, (QCheckBox, QRadioButton)):
                widget.toggled.connect(cb)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(cb)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(cb)
            elif isinstance(widget, FreqLineEdit):
                widget.freq_accepted.connect(cb)

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


class FreqLineEdit(QLineEdit):
    """Поле частоты: число + клавиша-суффикс, без Enter.

    Клавиши-суффиксы (учитывается регистр, раскладка не важна):
      ГГц: Г U G П     Гц: г u g п
      МГц: М м V v M m Ь ь
      кГц: К к R r K k Л л
    Enter — применить в той единице, которая была в поле до правки
    (в поле значение приходит в МГц — это и есть «текущие» единицы).
    При получении фокуса текст выделяется целиком.
    """

    freq_accepted = pyqtSignal(float)  # значение в герцах
    wheel_step = pyqtSignal(int)        # +1 — колесо вверх, -1 — вниз

    _CHAR_UNITS = {
        'Г': 1e9, 'U': 1e9, 'G': 1e9, 'П': 1e9,
        'г': 1.0, 'u': 1.0, 'g': 1.0, 'п': 1.0,
        'М': 1e6, 'м': 1e6, 'V': 1e6, 'v': 1e6,
        'M': 1e6, 'm': 1e6, 'Ь': 1e6, 'ь': 1e6,
        'К': 1e3, 'к': 1e3, 'R': 1e3, 'r': 1e3,
        'K': 1e3, 'k': 1e3, 'Л': 1e3, 'л': 1e3,
    }
    _SUFFIXES = (('ГГц', 1e9), ('МГц', 1e6), ('кГц', 1e3), ('Гц', 1.0))

    def __init__(self, text: str = '', parent=None):
        super().__init__(text, parent)
        # Только цифры и один разделитель: '937,5', '3.5', '937'
        validator = QRegularExpressionValidator(
            QRegularExpression(r'\d*[.,]?\d*'), self)
        self.setValidator(validator)
        self._enter_factor = 1e6  # единица поля до правки
        self._wheel_accum = 0

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        # selectAll делаем отложенно: при клике мышью после focusInEvent
        # сработает mousePressEvent и поставит каретку, затерев выделение
        QTimer.singleShot(0, self.selectAll)
        # Запомнить единицу текущего значения: '937,5 МГц' → 1e6
        text = self.text().strip()
        for suffix, factor in self._SUFFIXES:
            if text.endswith(suffix):
                self._enter_factor = factor
                return
        self._enter_factor = 1e6

    def wheelEvent(self, event) -> None:
        """Колесо над полем → сигнал направления.

        Мышь шлёт по 120 единиц на «щелчок», тачпады — мелкие дельты,
        поэтому накапливаем и эмитим по полному шагу.
        """
        self._wheel_accum += event.angleDelta().y()
        while abs(self._wheel_accum) >= 120:
            step = 1 if self._wheel_accum > 0 else -1
            self._wheel_accum -= 120 * step
            self.wheel_step.emit(step)
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            if self.isModified():
                self._commit(self._enter_factor)
            event.accept()
            return

        factor = self._CHAR_UNITS.get(event.text())
        if factor is not None and self.text().strip():
            self._commit(factor)
            event.accept()
            return

        super().keyPressEvent(event)

    def _commit(self, factor: float) -> None:
        """Разобрать число, отправить сигнал и уйти из редактирования."""
        text = self.text().strip().replace(',', '.')
        try:
            value_hz = float(text) * factor
        except ValueError:
            return
        if value_hz <= 0:
            return
        self.setModified(False)
        self.clearFocus()
        self.freq_accepted.emit(value_hz)
