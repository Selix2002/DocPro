from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

from docpro_frontend.body.styles.body_styles import STAT_CARD


class StatCard(QFrame):
    def __init__(self, label: str, value: str, color_variant: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet(STAT_CARD)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)

        self._label_widget = QLabel(label.upper())
        self._label_widget.setStyleSheet(
            "font-size: 15px; color: #6B7280; letter-spacing: 1px; background: transparent;"
        )

        value_color = {"amber": "#B45309", "blue": "#1D4ED8"}.get(color_variant or "", "#111827")
        self._value_widget = QLabel(value)
        self._value_widget.setStyleSheet(
            f"font-size: 36px; font-weight: 600; color: {value_color}; background: transparent;"
        )

        layout.addWidget(self._label_widget)
        layout.addWidget(self._value_widget)

    def set_value(self, value: str) -> None:
        self._value_widget.setText(value)
