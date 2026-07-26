from PySide6.QtCore import QEasingCurve, QVariantAnimation, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout

from docpro_frontend.header.views.menu_bar import MenuBar
from docpro_frontend.header.views.toolbar import Toolbar
from docpro_frontend.header.widgets.filter_bar import FilterBar

_FILTER_H = 44
_ANIM_MS  = 160


class HeaderWidget(QWidget):
    tab_changed          = Signal(str)
    new_quote_requested  = Signal()
    new_report_requested = Signal()
    import_pdf_requested = Signal()
    settings_requested   = Signal()
    search_changed       = Signal(str)
    filter_changed       = Signal(object, object)  # type_val, status_val
    switch_profile_requested = Signal(str)
    new_profile_requested = Signal()
    rename_profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._menu_bar   = MenuBar()
        self._toolbar    = Toolbar()
        self._filter_bar = FilterBar()
        self._filter_bar.setFixedHeight(0)
        self._filter_bar.setVisible(True)   # visible but height=0 so it's hidden visually
        self._filter_open = False

        layout.addWidget(self._menu_bar)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._filter_bar)

        # Animation drives the filter bar height
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(_ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(
            lambda v: self._filter_bar.setFixedHeight(int(v))
        )

        self._menu_bar.tab_changed.connect(self.tab_changed)
        self._menu_bar.new_quote_requested.connect(self.new_quote_requested)
        self._menu_bar.new_report_requested.connect(self.new_report_requested)
        self._menu_bar.import_pdf_requested.connect(self.import_pdf_requested)
        self._menu_bar.settings_requested.connect(self.settings_requested)
        self._menu_bar.switch_profile_requested.connect(self.switch_profile_requested)
        self._menu_bar.new_profile_requested.connect(self.new_profile_requested)
        self._menu_bar.rename_profile_requested.connect(self.rename_profile_requested)
        self._toolbar.search_changed.connect(self.search_changed)
        self._toolbar.filter_toggled.connect(self._toggle_filter_bar)
        self._filter_bar.filter_changed.connect(self.filter_changed)

    @property
    def search_field(self):
        return self._toolbar.search_field

    @property
    def profile_chip(self):
        return self._menu_bar.profile_chip

    def _toggle_filter_bar(self) -> None:
        self._filter_open = not self._filter_open
        self._anim.stop()
        self._anim.setStartValue(self._filter_bar.height())
        self._anim.setEndValue(_FILTER_H if self._filter_open else 0)
        self._anim.start()
