from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt

from docpro_frontend.settings.styles import settings_styles as S


class CardSection(QFrame):
    """
    Propuesta A card wrapper: card-head (icon + title + subtitle + optional
    status pill) + card-body containing the form widget passed in.
    """

    def __init__(
        self,
        icon: str,
        color: str,
        title: str,
        subtitle: str,
        status_text: str = "",
        status_state: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._color = color
        self._status_state = status_state

        self.setObjectName("CardSection")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.card())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Card head ─────────────────────────────────────────────────
        head = QWidget()
        head.setObjectName("CardHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.card_head())

        head_row = QHBoxLayout(head)
        head_row.setContentsMargins(20, 14, 20, 14)
        head_row.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icon_lbl.setStyleSheet(S.card_icon_badge(color))

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(S.card_head_title())
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(S.card_head_sub())
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)

        head_row.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)
        head_row.addLayout(text_col, 1)

        # Optional status pill (Gmail connected, Groq unvalidated…)
        if status_text and status_state:
            pill_row = QHBoxLayout()
            pill_row.setSpacing(6)
            pill_row.setContentsMargins(0, 0, 0, 0)

            dot = QLabel()
            dot.setFixedSize(9, 9)
            dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            dot.setStyleSheet(S.status_pill_dot(status_state))

            pill_text = QLabel(status_text)

            pill_wrap = QWidget()
            pill_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            pill_wrap.setStyleSheet(S.status_pill(status_state))
            pw_layout = QHBoxLayout(pill_wrap)
            pw_layout.setContentsMargins(0, 0, 0, 0)
            pw_layout.setSpacing(6)
            pw_layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            pw_layout.addWidget(pill_text, 0, Qt.AlignmentFlag.AlignVCenter)

            self._pill_wrap = pill_wrap
            self._pill_dot = dot
            self._pill_text = pill_text

            head_row.addWidget(pill_wrap, 0, Qt.AlignmentFlag.AlignTop)
        else:
            self._pill_wrap = None
            self._pill_dot = None
            self._pill_text = None

        outer.addWidget(head)

        # ── Card body ─────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setObjectName("CardBody")
        self._body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._body.setStyleSheet(S.card_body())
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(20, 20, 20, 20)
        self._body_layout.setSpacing(0)
        outer.addWidget(self._body)

    # ── Public ────────────────────────────────────────────────────────

    def set_form(self, form: QWidget) -> None:
        self._body_layout.addWidget(form)

    def update_status(self, text: str, state: str) -> None:
        if self._pill_wrap:
            self._pill_text.setText(text)
            self._pill_wrap.setStyleSheet(S.status_pill(state))
            self._pill_dot.setStyleSheet(S.status_pill_dot(state))
