from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


class GreetingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self._title = QLabel()
        self._title.setStyleSheet(
            "font-size: 30px; font-weight: 600; color: #111827;"
        )

        self._subtitle = QLabel()
        self._subtitle.setStyleSheet("font-size: 18px; color: #9CA3AF;")

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

        self._draft_count = 0
        self._refresh()

    def set_draft_count(self, count: int) -> None:
        self._draft_count = count
        self._refresh()

    def _refresh(self) -> None:
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Buenos días"
        elif hour < 19:
            greeting = "Buenas tardes"
        else:
            greeting = "Buenas noches"
        self._title.setText(greeting)

        now = datetime.now()
        day_name = _DAYS[now.weekday()].capitalize()
        month_name = _MONTHS[now.month - 1]
        date_str = f"{day_name} {now.day} de {month_name}"

        if self._draft_count:
            n = self._draft_count
            sub = (
                f"{date_str} · {n} documento{'s' if n != 1 else ''} "
                f"en borrador pendiente{'s' if n != 1 else ''}"
            )
        else:
            sub = date_str
        self._subtitle.setText(sub)
