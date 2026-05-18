MENU_BAR = """
QWidget#MenuBar {
    background: white;
    border-bottom: 1px solid #E5E7EB;
}
"""

TAB_BTN = """
QPushButton {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    border-top: 3px solid transparent;
    padding: 0 24px;
    font-size: 20px;
    color: #9CA3AF;
    height: 69px;
}
QPushButton:hover { color: #374151; }
QPushButton[active="true"] {
    color: #B45309;
    border-bottom: 3px solid #B45309;
    font-weight: 500;
}
"""

BTN_GHOST = """
QPushButton {
    background: transparent;
    border: 1px solid #E5E7EB;
    border-radius: 11px;
    padding: 9px 21px;
    font-size: 18px;
    font-weight: 500;
    color: #374151;
}
QPushButton:hover { background: #F9FAFB; }
"""

BTN_AMBER = """
QPushButton {
    background: #B45309;
    border: none;
    border-radius: 11px;
    padding: 9px 21px;
    font-size: 18px;
    font-weight: 500;
    color: white;
}
QPushButton:hover { background: #92400E; }
"""

BTN_BLUE = """
QPushButton {
    background: #1D4ED8;
    border: none;
    border-radius: 11px;
    padding: 9px 21px;
    font-size: 18px;
    font-weight: 500;
    color: white;
}
QPushButton:hover { background: #1E40AF; }
"""

BTN_ICON = """
QPushButton {
    background: transparent;
    border: none;
    border-radius: 11px;
    font-size: 27px;
    color: #6B7280;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}
QPushButton:hover { background: #F3F4F6; }
"""

TOOLBAR = """
QWidget#Toolbar {
    background: white;
    border-bottom: 1px solid #F3F4F6;
}
"""

TOOLBAR_BTN = """
QPushButton {
    background: transparent;
    border: 1px solid #E5E7EB;
    border-radius: 11px;
    padding: 9px 15px;
    font-size: 18px;
    font-weight: 500;
    color: #374151;
}
QPushButton:hover { background: #F9FAFB; }
"""

TOOLBAR_SEARCH = """
QLineEdit {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 11px;
    padding: 9px 18px;
    font-size: 20px;
    color: #111827;
}
"""
