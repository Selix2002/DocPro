STAT_CARD = """
QFrame#HistStatCard {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

TABLE_PANEL = """
QFrame#HistoryPanel {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

ROW_NORMAL = "QWidget#HistRow { background: white; border-bottom: 1px solid #F3F4F6; }"
ROW_HOVER  = "QWidget#HistRow { background: #F9FAFB; border-bottom: 1px solid #F3F4F6; }"
ROW_LAST_NORMAL = "QWidget#HistRow { background: white; }"
ROW_LAST_HOVER  = "QWidget#HistRow { background: #F9FAFB; }"

FILTER_CHIP_NORMAL = """
QPushButton {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 17px;
    color: #6B7280;
    font-weight: 500;
}
QPushButton:hover { background: #F9FAFB; }
"""

FILTER_CHIP_ACTIVE = """
QPushButton {
    background: #FEF3C7;
    border: 1px solid #B45309;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 17px;
    color: #92400E;
    font-weight: 600;
}
"""

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
    min-width: 150px;
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

PAGE_SIZE_COMBO = """
QComboBox {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 17px;
    color: #374151;
    min-width: 72px;
    max-width: 72px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { width: 0; height: 0; }
QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #E5E7EB;
    selection-background-color: #FEF3C7;
    selection-color: #92400E;
    outline: none;
}
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
    font-size: 18px;
    color: #9CA3AF;
    padding: 2px 6px;
    min-width: 36px;
    max-width: 36px;
}
QPushButton:hover { background: #F3F4F6; color: #374151; }
"""

BADGE = {
    "Borrador": (
        "background: #FEF3C7; color: #92400E; font-size: 15px; "
        "font-weight: 500; padding: 3px 10px; border-radius: 8px;"
    ),
    "Finalizado": (
        "background: #D1FAE5; color: #065F46; font-size: 15px; "
        "font-weight: 500; padding: 3px 10px; border-radius: 8px;"
    ),
    "Enviado": (
        "background: #DBEAFE; color: #1E40AF; font-size: 15px; "
        "font-weight: 500; padding: 3px 10px; border-radius: 8px;"
    ),
    "Aprobado": (
        "background: #ECFDF5; color: #047857; font-size: 15px; "
        "font-weight: 500; padding: 3px 10px; border-radius: 8px;"
    ),
    "Rechazado": (
        "background: #FEE2E2; color: #991B1B; font-size: 15px; "
        "font-weight: 500; padding: 3px 10px; border-radius: 8px;"
    ),
}
