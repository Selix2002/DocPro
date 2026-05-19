from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator

from docpro_frontend.settings.styles import settings_styles as S


class CounterRow(QWidget):
    """
    Compact counter row: document-type label + preview + prefix input
    + number input + reset button.
    """

    def __init__(self, name: str, prefix: str, number: int, parent=None):
        super().__init__(parent)
        self._initial_prefix = prefix
        self._initial_number = number

        self.setObjectName("CounterRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(10)

        # Left: name + next preview
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name_lbl = QLabel(name)
        self._next_lbl = QLabel()
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._next_lbl)
        layout.addLayout(text_col, 1)

        # Prefix tag + input
        prefix_tag = QLabel("PREFIJO")
        self._prefix_input = QLineEdit(prefix)
        self._prefix_input.setFixedWidth(72)
        self._prefix_input.textChanged.connect(self._update_preview)

        # Number tag + input
        num_tag = QLabel("#")
        self._num_input = QLineEdit(str(number))
        self._num_input.setFixedWidth(60)
        self._num_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._num_input.setValidator(QIntValidator(1, 99999, self))
        self._num_input.textChanged.connect(self._update_preview)

        # Reset button
        self._reset_btn = QPushButton("↺ Reset")
        self._reset_btn.clicked.connect(self._reset)

        for tag in (prefix_tag, num_tag):
            tag.setStyleSheet(S.counter_tag())

        layout.addWidget(prefix_tag, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._prefix_input)
        layout.addWidget(num_tag, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._num_input)
        layout.addWidget(self._reset_btn)

        self._apply_styles()
        self._update_preview()

    # ── Public ────────────────────────────────────────────────────────

    def set_values(self, prefix: str, number: int) -> None:
        self._initial_prefix = prefix
        self._initial_number = number
        self._prefix_input.setText(prefix)
        self._num_input.setText(str(number))

    def get_prefix(self) -> str:
        return self._prefix_input.text()

    def get_number(self) -> int:
        try:
            return int(self._num_input.text())
        except ValueError:
            return self._initial_number

    # ── Internal ──────────────────────────────────────────────────────

    def _update_preview(self) -> None:
        prefix = self._prefix_input.text()
        try:
            num = int(self._num_input.text())
        except ValueError:
            num = 0
        self._next_lbl.setText(f"Próxima: {prefix}{num:04d}")

    def _reset(self) -> None:
        self._prefix_input.setText(self._initial_prefix)
        self._num_input.setText(str(self._initial_number))

    def _apply_styles(self) -> None:
        self.setStyleSheet(S.counter_row_bg())
        self._name_lbl.setStyleSheet(S.counter_label_name())
        self._next_lbl.setStyleSheet(S.counter_label_next())
        self._prefix_input.setStyleSheet(S.counter_input())
        self._num_input.setStyleSheet(S.counter_input())
        self._reset_btn.setStyleSheet(S.counter_reset_btn())
