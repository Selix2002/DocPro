BORDER_NORMAL = "1px solid #E5E7EB"
BORDER_AMBER = "1px solid #B45309"
BORDER_BLUE = "1px solid #1D4ED8"

CREATE_CARD = """
CreateCard {{
    background: white;
    border: {border};
    border-radius: 15px;
}}
"""

RECENT_CARD_NORMAL = "RecentCard { background: white; border: 1px solid #E5E7EB; border-radius: 14px; }"
RECENT_CARD_HOVER = "RecentCard { background: white; border: 1px solid #D1D5DB; border-radius: 14px; }"

BADGE = {
    "Borrador": (
        "background: #FEF3C7; color: #92400E; font-size: 15px; "
        "font-weight: 500; padding: 3px 12px; border-radius: 8px;"
    ),
    "Finalizado": (
        "background: #D1FAE5; color: #065F46; font-size: 15px; "
        "font-weight: 500; padding: 3px 12px; border-radius: 8px;"
    ),
    "Enviado": (
        "background: #DBEAFE; color: #1E40AF; font-size: 15px; "
        "font-weight: 500; padding: 3px 12px; border-radius: 8px;"
    ),
    "Aprobado": (
        "background: #D1FAE5; color: #059669; font-size: 15px; "
        "font-weight: 500; padding: 3px 12px; border-radius: 8px;"
    ),
    "Rechazado": (
        "background: #FEE2E2; color: #991B1B; font-size: 15px; "
        "font-weight: 500; padding: 3px 12px; border-radius: 8px;"
    ),
}

STAT_CARD = """
QFrame#StatCard {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

DRAFTS_PANEL = """
QFrame#DraftsPanel {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""

COUNT_BADGE = """
    background: #FEF3C7;
    color: #92400E;
    font-size: 15px;
    padding: 2px 11px;
    border-radius: 6px;
    font-weight: 500;
"""

SUMMARY_CARD = """
QFrame#SummaryCard {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 15px;
}
"""
