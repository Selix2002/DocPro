STAT_CARD = """
QFrame#ClientStatCard {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

CLIENT_CARD = """
QFrame#ClientCard {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
QFrame#ClientCard:hover {
    border: 1px solid #D97706;
}
"""

TABLE_PANEL = """
QFrame#ClientsPanel {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

ROW_NORMAL      = "QFrame#ClientRow { background: white; border-bottom: 1px solid #F3F4F6; }"
ROW_HOVER       = "QFrame#ClientRow { background: #F9FAFB; border-bottom: 1px solid #F3F4F6; }"
ROW_LAST_NORMAL = "QFrame#ClientRow { background: white; }"
ROW_LAST_HOVER  = "QFrame#ClientRow { background: #F9FAFB; }"

SEARCH_BOX = """
QLineEdit {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 8px 15px;
    font-size: 18px;
    color: #111827;
}
QLineEdit:focus { border: 1px solid #B45309; }
"""

SORT_COMBO = """
QComboBox {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 17px;
    color: #374151;
    min-width: 160px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { width: 0; height: 0; }
QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #E5E7EB;
    selection-background-color: #FEF3C7;
    selection-color: #92400E;
    outline: none;
}
"""

VIEW_TOGGLE_NORMAL = """
QPushButton {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 17px;
    color: #6B7280;
}
QPushButton:hover { background: #F9FAFB; }
"""

VIEW_TOGGLE_ACTIVE = """
QPushButton {
    background: #FEF3C7;
    border: 1px solid #B45309;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 17px;
    color: #92400E;
    font-weight: 600;
}
"""

NEW_CLIENT_BTN = """
QPushButton {
    background: #B45309;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 17px;
    color: white;
    font-weight: 600;
}
QPushButton:hover { background: #92400E; }
"""

NUEVO_DOC_BTN = """
QPushButton {
    background: #B45309;
    border: none;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 15px;
    color: white;
    font-weight: 600;
}
QPushButton:hover { background: #92400E; }
"""

PAGE_BTN_NORMAL = """
QPushButton {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 17px;
    color: #374151;
    min-width: 36px;
}
QPushButton:hover { background: #F9FAFB; }
QPushButton:disabled { color: #D1D5DB; border-color: #F3F4F6; background: white; }
"""

PAGE_BTN_ACTIVE = """
QPushButton {
    background: #B45309;
    border: 1px solid #B45309;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 17px;
    color: white;
    font-weight: 600;
    min-width: 36px;
}
"""

ACTION_BTN = """
QPushButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 22px;
    font-weight: 400;
    color: #9CA3AF;
    padding: 0px;
    min-width: 36px;
    max-width: 36px;
}
QPushButton:hover { background: #FEF3C7; color: #B45309; }
"""
