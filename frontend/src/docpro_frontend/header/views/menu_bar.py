from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

from docpro_frontend.header.widgets.tab_bar import TabBar
from docpro_frontend.header.widgets.action_bar import ActionBar
from docpro_frontend.header.widgets.profile_chip import ProfileChip
from docpro_frontend.header.styles.header_styles import MENU_BAR


class MenuBar(QWidget):
    tab_changed = Signal(str)
    new_quote_requested = Signal()
    new_report_requested = Signal()
    import_pdf_requested = Signal()
    settings_requested = Signal()
    switch_profile_requested = Signal(str)
    new_profile_requested = Signal()
    rename_profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(69)
        self.setObjectName("MenuBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(MENU_BAR)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_brand())

        self._profile_chip = ProfileChip()
        layout.addWidget(self._profile_chip)

        self._tab_bar = TabBar()
        layout.addWidget(self._tab_bar)

        layout.addStretch()

        self._action_bar = ActionBar()
        layout.addWidget(self._action_bar)

        self._tab_bar.tab_changed.connect(self.tab_changed)
        self._action_bar.new_quote_requested.connect(self.new_quote_requested)
        self._action_bar.new_report_requested.connect(self.new_report_requested)
        self._action_bar.import_pdf_requested.connect(self.import_pdf_requested)
        self._action_bar.settings_requested.connect(self.settings_requested)
        self._profile_chip.switch_requested.connect(self.switch_profile_requested)
        self._profile_chip.new_profile_requested.connect(self.new_profile_requested)
        self._profile_chip.rename_profile_requested.connect(self.rename_profile_requested)

    @property
    def profile_chip(self) -> ProfileChip:
        return self._profile_chip

    @staticmethod
    def _build_brand() -> QWidget:
        widget = QWidget()
        widget.setFixedWidth(225)
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet("background: transparent; border-right: 1px solid #F3F4F6;")

        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 0, 27, 0)
        h.setSpacing(12)

        icon_box = QLabel("D")
        icon_box.setFixedSize(39, 39)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icon_box.setStyleSheet("""
            background: #B45309;
            border-radius: 9px;
            font-size: 20px;
            font-weight: 700;
            color: white;
        """)

        name = QLabel("DocPro")
        name.setStyleSheet(
            "font-size: 21px; font-weight: 600; color: #111827; background: transparent;"
        )

        h.addWidget(icon_box)
        h.addWidget(name)
        return widget
