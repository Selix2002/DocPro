from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QWidget,
)

from docpro_frontend.clients.styles.clients_styles import (
    ACTION_BTN, CONTEXT_MENU, DELETE_BTN,
    ROW_HOVER, ROW_LAST_HOVER, ROW_LAST_NORMAL, ROW_NORMAL,
)
from docpro_frontend.clients.widgets.client_card import AVATAR_COLORS

_AVATAR_RADIUS = 18


class ClientsRow(QFrame):
    new_doc_clicked  = Signal(int)        # client_id
    delete_requested = Signal(int, str)   # client_id, client_name
    edit_requested   = Signal(int, dict)  # client_id, row_data

    def __init__(self, row: dict, is_last: bool = False, parent=None):
        super().__init__(parent)
        self._client_id = row["client_id"]
        self._row_data  = row

        self.setObjectName("ClientRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._normal = ROW_LAST_NORMAL if is_last else ROW_NORMAL
        self._hover  = ROW_LAST_HOVER  if is_last else ROW_HOVER
        self.setStyleSheet(self._normal)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(21, 12, 21, 12)
        layout.setSpacing(0)

        # ── Nombre + avatar ───────────────────────────────────────────────
        name_box = QWidget()
        name_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        name_box.setStyleSheet("background: transparent;")
        name_h = QHBoxLayout(name_box)
        name_h.setContentsMargins(0, 0, 0, 0)
        name_h.setSpacing(10)

        color = AVATAR_COLORS[self._client_id % 4]
        avatar = QLabel(_initials(row["name"]))
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        avatar.setStyleSheet(
            f"background: {color}; border-radius: {_AVATAR_RADIUS}px; "
            f"font-size: 13px; font-weight: 700; color: white;"
        )
        name_lbl = QLabel(row["name"])
        name_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #111827; background: transparent;"
        )
        name_h.addWidget(avatar)
        name_h.addWidget(name_lbl)
        name_h.addStretch()
        layout.addWidget(name_box, stretch=2)

        # ── RUT ───────────────────────────────────────────────────────────
        rut_lbl = QLabel(row["rut"])
        rut_lbl.setStyleSheet("font-size: 16px; color: #374151; background: transparent;")
        rut_lbl.setFixedWidth(130)
        layout.addWidget(rut_lbl)

        # ── Email ─────────────────────────────────────────────────────────
        email_lbl = QLabel(row.get("email") or "—")
        email_lbl.setStyleSheet("font-size: 16px; color: #374151; background: transparent;")
        layout.addWidget(email_lbl, stretch=2)

        # ── Phone ─────────────────────────────────────────────────────────
        phone_lbl = QLabel(row.get("phone") or "—")
        phone_lbl.setStyleSheet("font-size: 16px; color: #374151; background: transparent;")
        phone_lbl.setFixedWidth(130)
        layout.addWidget(phone_lbl)

        # ── Doc count ─────────────────────────────────────────────────────
        docs_lbl = QLabel(str(row["doc_count"]))
        docs_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #B45309; background: transparent;"
        )
        docs_lbl.setFixedWidth(100)
        docs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(docs_lbl)

        # ── Acciones: nueva cotización + eliminar ─────────────────────────
        action_btn = QPushButton("+")
        action_btn.setStyleSheet(ACTION_BTN)
        action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        action_btn.setToolTip("Nueva cotización")
        action_btn.clicked.connect(lambda: self.new_doc_clicked.emit(self._client_id))
        layout.addWidget(action_btn)

        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(DELETE_BTN)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setToolTip("Eliminar cliente")
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self._client_id, self._row_data.get("name", ""))
        )
        layout.addWidget(del_btn)

    def enterEvent(self, event):
        self.setStyleSheet(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._normal)
        super().leaveEvent(event)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU)
        edit_action = menu.addAction("✏   Editar cliente")
        if menu.exec(self.mapToGlobal(pos)) is edit_action:
            self.edit_requested.emit(self._client_id, dict(self._row_data))


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "??"
