from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.clients.styles.clients_styles import CLIENT_CARD, NUEVO_DOC_BTN

AVATAR_COLORS = ["#D97706", "#1D4ED8", "#059669", "#7C3AED"]


class ClientCard(QFrame):
    new_doc_clicked = Signal(int)  # client_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client_id = 0
        self.setObjectName("ClientCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(CLIENT_CARD)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Avatar + name
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setContentsMargins(0, 0, 0, 0)

        self._avatar = QLabel()
        self._avatar.setFixedSize(44, 44)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        top_row.addWidget(self._avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_col.setContentsMargins(0, 0, 0, 0)
        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #111827; background: transparent;"
        )
        self._rut_lbl = QLabel()
        self._rut_lbl.setStyleSheet(
            "font-size: 14px; color: #9CA3AF; background: transparent;"
        )
        name_col.addWidget(self._name_lbl)
        name_col.addWidget(self._rut_lbl)
        top_row.addLayout(name_col, stretch=1)
        layout.addLayout(top_row)

        # Contact
        self._email_lbl = QLabel()
        self._email_lbl.setStyleSheet(
            "font-size: 15px; color: #6B7280; background: transparent;"
        )
        self._phone_lbl = QLabel()
        self._phone_lbl.setStyleSheet(
            "font-size: 15px; color: #6B7280; background: transparent;"
        )
        layout.addWidget(self._email_lbl)
        layout.addWidget(self._phone_lbl)

        # Doc count + date
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)
        self._doc_count_lbl = QLabel()
        self._doc_count_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #B45309; background: transparent;"
        )
        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet(
            "font-size: 14px; color: #9CA3AF; background: transparent;"
        )
        meta_row.addWidget(self._doc_count_lbl)
        meta_row.addStretch()
        meta_row.addWidget(self._date_lbl)
        layout.addLayout(meta_row)

        # Action
        nuevo_btn = QPushButton("Nueva cotización")
        nuevo_btn.setStyleSheet(NUEVO_DOC_BTN)
        nuevo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nuevo_btn.clicked.connect(lambda: self.new_doc_clicked.emit(self._client_id))
        layout.addWidget(nuevo_btn)

    def set_data(self, row: dict) -> None:
        self._client_id = row["client_id"]
        color = AVATAR_COLORS[self._client_id % 4]
        self._avatar.setStyleSheet(
            f"background: {color}; border-radius: 22px; "
            f"font-size: 15px; font-weight: 700; color: white;"
        )
        self._avatar.setText(_initials(row["name"]))
        self._name_lbl.setText(row["name"])
        self._rut_lbl.setText(row["rut"])
        self._email_lbl.setText(row.get("email") or "")
        self._phone_lbl.setText(row.get("phone") or "")
        doc_count = row["doc_count"]
        self._doc_count_lbl.setText(
            f"{doc_count} doc" if doc_count == 1 else f"{doc_count} docs"
        )
        self._date_lbl.setText(row.get("created_at_label", ""))


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "??"
