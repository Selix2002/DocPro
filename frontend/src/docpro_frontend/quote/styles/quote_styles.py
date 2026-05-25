"""
QSS generators for the Quote module.
Every function reads theme.current at call time — hot-swap safe.
"""
import os as _os

import docpro_frontend.theme as _th

_CHEVRON_DOWN = _os.path.join(
    _os.path.dirname(__file__), "..", "..", "resources", "icons", "chevron-down.svg"
).replace("\\", "/")


def _t() -> dict[str, str]:
    return _th.current


# ── Header ────────────────────────────────────────────────────────────────────

def doc_header() -> str:
    t = _t()
    return f"""
QWidget#DocHeader {{
    background: {t['surface']};
    border-bottom: 1px solid {t['border']};
}}
"""


def back_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: none;
    border-right: 1px solid {t['border_soft']};
    padding: 8px 20px 8px 0px;
    font-size: 18px;
    color: {t['muted']};
    text-align: left;
}}
QPushButton:hover {{ color: {t['text']}; }}
"""


def doc_type_pill() -> str:
    t = _t()
    return (
        f"background: {t['amber_light']}; color: {t['amber_dark']}; "
        f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
        f"padding: 3px 10px; border-radius: 6px; background: {t['amber_light']};"
    )


def doc_number_label() -> str:
    t = _t()
    return f"font-size: 17px; font-weight: 600; color: {t['text']}; background: transparent;"


def doc_number_edit_btn() -> str:
    return (
        "QPushButton {"
        "  background: transparent; border: none; border-radius: 4px;"
        "  font-size: 13px; color: #9CA3AF; padding: 1px 3px;"
        "  min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
        "}"
        "QPushButton:hover { background: #F3F4F6; color: #6B7280; }"
    )


def status_pill(status: str) -> str:
    t = _t()
    mapping = {
        "Borrador":   (t["amber_light"], t["amber_dark"]),
        "Finalizado": (t["green_light"], t["green_text"]),
        "Enviado":    (t["blue_light"],  t["blue_dark"]),
        "Aprobado":   (t["green_light"], t["green"]),
        "Rechazado":  (t["red_light"],   t["red_text"]),
    }
    bg, fg = mapping.get(status, (t["border_soft"], t["muted"]))
    return (
        f"background: {bg}; color: {fg}; "
        f"font-size: 12px; font-weight: 600; "
        f"padding: 3px 10px; border-radius: 6px;"
    )


def autosave_label() -> str:
    t = _t()
    return f"font-size: 12px; color: {t['muted']}; background: transparent;"


def autosave_dot(state: str) -> str:
    t = _t()
    color = {"saving": t["amber"], "saved": t["green"], "error": t["red"]}.get(state, t["placeholder"])
    return (
        f"background: {color}; border-radius: 4px; "
        f"min-width: 7px; max-width: 7px; min-height: 7px; max-height: 7px;"
    )


def btn_header_ghost() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 14px; font-weight: 500;
    color: {t['text_secondary']};
}}
QPushButton:hover {{ background: {t['bg']}; border-color: {t['placeholder']}; }}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


def btn_header_danger() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 14px; font-weight: 500;
    color: {t['red']};
}}
QPushButton:hover {{ background: {t['red_light']}; border-color: #FECACA; }}
"""


def btn_header_primary() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['amber']};
    border: none;
    border-radius: 9px;
    padding: 7px 16px;
    font-size: 14px; font-weight: 600;
    color: white;
}}
QPushButton:hover {{ background: {t['amber_dark']}; }}
QPushButton:disabled {{ background: {t['placeholder']}; }}
"""


def btn_approve() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['green_light']};
    border: 1px solid {t['green']};
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 14px; font-weight: 600;
    color: {t['green_text']};
}}
QPushButton:hover {{ background: {t['green']}; color: white; border-color: {t['green']}; }}
"""


def btn_reject() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 14px; font-weight: 600;
    color: {t['red']};
}}
QPushButton:hover {{ background: {t['red_light']}; border-color: #FECACA; }}
"""


def btn_header_icon() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 9px;
    min-width: 36px; max-width: 36px;
    min-height: 36px; max-height: 36px;
    font-size: 18px; color: {t['muted']};
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""


def header_separator() -> str:
    t = _t()
    return f"background: {t['border']}; min-width: 1px; max-width: 1px; min-height: 28px; max-height: 28px;"


# ── Form panel ────────────────────────────────────────────────────────────────

def form_panel() -> str:
    t = _t()
    return f"QWidget#FormPanel {{ background: {t['bg']}; }}"


def meta_row() -> str:
    t = _t()
    return f"""
QWidget#MetaRow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(180,83,9,0.04), stop:1 rgba(29,78,216,0.04));
    border: 1px solid {t['border']};
    border-radius: 14px;
}}
"""


def meta_label() -> str:
    t = _t()
    return (
        f"font-size: 11px; font-weight: 600; text-transform: uppercase; "
        f"letter-spacing: 1px; color: {t['muted']}; background: transparent;"
    )


def meta_value() -> str:
    t = _t()
    return f"font-size: 15px; font-weight: 600; color: {t['text']}; background: transparent;"


def meta_number_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 14px; font-weight: 600;
    color: {t['text']};
    background: {t['surface']};
    min-width: 110px; max-width: 110px;
}}
QLineEdit:focus {{ border-color: {t['amber']}; }}
QLineEdit:read-only {{
    background: {t['border_soft']};
    color: {t['muted']};
    border-color: {t['border_soft']};
}}
"""


def meta_info_note() -> str:
    t = _t()
    return f"font-size: 12px; color: {t['muted']}; background: transparent;"


def meta_company_name() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 600; color: {t['amber_dark']}; "
        f"background: transparent;"
    )


def meta_company_detail() -> str:
    t = _t()
    return f"font-size: 11px; color: {t['muted']}; background: transparent;"


def date_edit() -> str:
    t = _t()
    return f"""
QDateEdit {{
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 10px 6px 10px;
    font-size: 14px; font-weight: 600;
    color: {t['text']};
    background: {t['surface']};
}}
QDateEdit:focus {{ border-color: {t['amber']}; }}
QDateEdit::drop-down {{
    subcontrol-origin: border;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    border-left: 1px solid {t['border']};
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
    background: {t['bg']};
}}
QDateEdit::drop-down:hover {{ background: {t['border_soft']}; }}
QDateEdit::drop-down:disabled {{ background: transparent; border-left-color: {t['border_soft']}; }}
QDateEdit::down-arrow {{ image: url("{_CHEVRON_DOWN}"); width: 12px; height: 12px; }}
"""


# ── Section block (card) ──────────────────────────────────────────────────────

def section_block() -> str:
    t = _t()
    return f"""
QFrame#SectionBlock {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 14px;
}}
"""


def section_head() -> str:
    t = _t()
    return f"""
QWidget#SectionHead {{
    background: {t['surface_alt']};
    border-bottom: 1px solid {t['border_soft']};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}}
"""


def section_head_label() -> str:
    t = _t()
    return (
        f"font-size: 12px; font-weight: 700; text-transform: uppercase; "
        f"letter-spacing: 1px; color: {t['text_secondary']}; background: transparent;"
    )


def section_head_icon() -> str:
    t = _t()
    return f"font-size: 16px; color: {t['muted']}; background: transparent;"


# ── Form fields ───────────────────────────────────────────────────────────────

def field_label() -> str:
    t = _t()
    return (
        f"font-size: 11px; font-weight: 600; letter-spacing: 1px; "
        f"color: {t['muted']}; background: transparent;"
    )


def field_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 9px 12px;
    font-size: 14px;
    color: {t['text']};
    background: {t['surface']};
}}
QLineEdit:focus {{
    border-color: {t['amber']};
    background: {t['surface']};
}}
QLineEdit:read-only {{
    background: {t['border_soft']};
    color: {t['muted']};
    border-color: {t['border_soft']};
}}
QLineEdit:disabled {{
    background: {t['border_soft']};
    color: {t['placeholder']};
}}
"""


def rut_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 9px 12px;
    font-size: 14px; font-weight: 500;
    color: {t['text']};
    background: {t['surface']};
}}
QLineEdit:focus {{ border-color: {t['amber']}; }}
"""


def rut_badge_found() -> str:
    t = _t()
    return (
        f"background: {t['green_light']}; color: {t['green_text']}; "
        f"font-size: 11px; font-weight: 600; "
        f"padding: 2px 8px; border-radius: 5px;"
    )


def rut_badge_new() -> str:
    t = _t()
    return (
        f"background: {t['amber_light']}; color: {t['amber_dark']}; "
        f"font-size: 11px; font-weight: 600; "
        f"padding: 2px 8px; border-radius: 5px;"
    )


def btn_new_client() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px dashed {t['amber']};
    border-radius: 9px;
    padding: 8px 14px;
    font-size: 13px; font-weight: 500;
    color: {t['amber']};
}}
QPushButton:hover {{ background: {t['amber_light']}; border-style: solid; }}
"""


# ── Items table ───────────────────────────────────────────────────────────────

def items_table() -> str:
    t = _t()
    return f"""
QTableWidget {{
    background: {t['surface']};
    border: none;
    gridline-color: transparent;
    outline: none;
    selection-background-color: {t['amber_light']};
    selection-color: {t['text']};
}}
QTableWidget::item {{
    padding: 0px;
    border: none;
    border-bottom: 1px solid {t['border_soft']};
}}
QTableWidget::item:selected {{
    background: {t['amber_light']};
    color: {t['text']};
}}
QHeaderView::section {{
    background: {t['bg']};
    border: none;
    border-bottom: 1px solid {t['border']};
    padding: 9px 12px;
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: {t['muted']};
}}
"""


def item_cell_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 14px;
    color: {t['text']};
    background: transparent;
}}
QLineEdit:hover {{ background: {t['border_soft']}; }}
QLineEdit:focus {{
    border-color: {t['amber']};
    background: {t['surface']};
}}
QLineEdit:disabled {{ color: {t['placeholder']}; }}
"""


def item_subtotal_label() -> str:
    t = _t()
    return (
        f"font-size: 14px; font-weight: 500; color: {t['text']}; "
        f"background: transparent; padding: 7px 10px;"
    )


def item_del_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: none;
    border-radius: 7px;
    font-size: 17px;
    color: {t['placeholder']};
    min-width: 30px; max-width: 30px;
    min-height: 30px; max-height: 30px;
}}
QPushButton:hover {{ background: {t['red_light']}; color: {t['red']}; }}
"""


def add_row_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: none;
    border-top: 1px dashed {t['border']};
    border-radius: 0px;
    padding: 10px 12px;
    font-size: 13px; font-weight: 500;
    color: {t['amber']};
    text-align: left;
}}
QPushButton:hover {{ background: {t['amber_light']}; }}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


# ── Totals bar ────────────────────────────────────────────────────────────────

def totals_block() -> str:
    t = _t()
    return f"""
QWidget#TotalsBlock {{
    background: {t['bg']};
    border-top: 1px solid {t['border_soft']};
}}
"""


def totals_label() -> str:
    t = _t()
    return f"font-size: 14px; color: {t['muted']}; background: transparent;"


def totals_value() -> str:
    t = _t()
    return f"font-size: 14px; font-weight: 500; color: {t['text']}; background: transparent;"


def totals_total_label() -> str:
    t = _t()
    return (
        f"font-size: 18px; font-weight: 700; color: {t['amber']}; "
        f"background: transparent; border-top: 2px solid {t['border']}; padding-top: 6px;"
    )


def totals_total_value() -> str:
    t = _t()
    return (
        f"font-size: 18px; font-weight: 700; color: {t['amber']}; "
        f"background: transparent; border-top: 2px solid {t['border']}; padding-top: 6px;"
    )


# ── Observations ──────────────────────────────────────────────────────────────

def obs_textarea() -> str:
    t = _t()
    return f"""
QTextEdit {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 12px;
    font-size: 14px;
    color: {t['text']};
    background: {t['surface']};
}}
QTextEdit:focus {{ border-color: {t['amber']}; }}
QTextEdit:disabled {{ background: {t['border_soft']}; color: {t['placeholder']}; }}
"""


def btn_ai_stub() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['purple_light']};
    border: 1px solid #E9D5FF;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 12px; font-weight: 500;
    color: {t['purple']};
}}
QPushButton:hover {{ background: #EDE9FE; }}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; background: {t['border_soft']}; }}
"""


# ── Preview panel ─────────────────────────────────────────────────────────────

def preview_panel() -> str:
    t = _t()
    return f"""
QWidget#PreviewPanel {{
    background: #F1F0EE;
    border-left: 1px solid {t['border']};
}}
"""


def preview_header() -> str:
    t = _t()
    return f"""
QWidget#PreviewHeader {{
    background: {t['surface']};
    border-bottom: 1px solid {t['border']};
}}
"""


def preview_header_label() -> str:
    t = _t()
    return (
        f"font-size: 11px; font-weight: 700; letter-spacing: 1px; "
        f"color: {t['muted']}; background: transparent;"
    )


def preview_phase_badge() -> str:
    t = _t()
    return (
        f"background: {t['border_soft']}; color: {t['muted']}; "
        f"font-size: 10px; font-weight: 600; "
        f"padding: 2px 8px; border-radius: 5px;"
    )


def preview_placeholder_label() -> str:
    t = _t()
    return f"font-size: 14px; color: {t['placeholder']}; background: transparent;"


def btn_preview_icon() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 6px;
    min-width: 28px; max-width: 28px;
    min-height: 28px; max-height: 28px;
    font-size: 14px; color: {t['muted']};
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""


def btn_preview_download() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['amber_light']};
    border: 1px solid {t['amber']};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px; font-weight: 600;
    color: {t['amber_dark']};
}}
QPushButton:hover {{ background: {t['amber']}; color: white; border-color: {t['amber']}; }}
QPushButton:disabled {{
    background: {t['border_soft']};
    border-color: {t['border_soft']};
    color: {t['placeholder']};
}}
"""


def preview_loading_label() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


def zoom_bar() -> str:
    t = _t()
    return f"""
QWidget#ZoomBar {{
    background: {t['surface']};
    border-top: 1px solid {t['border']};
}}
"""


def btn_zoom() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    min-width: 28px; max-width: 28px;
    min-height: 28px; max-height: 28px;
    font-size: 16px; font-weight: 700;
    color: {t['text_secondary']};
}}
QPushButton:hover {{ background: {t['bg']}; color: {t['text']}; }}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


def zoom_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 3px 6px;
    font-size: 13px; font-weight: 500;
    color: {t['text']};
    background: {t['surface']};
    min-width: 58px; max-width: 58px;
}}
QLineEdit:focus {{ border-color: {t['amber']}; }}
"""


# ── New client dialog ─────────────────────────────────────────────────────────

def dialog_bg() -> str:
    t = _t()
    return f"QDialog {{ background: {t['surface']}; }}"


def dialog_title() -> str:
    t = _t()
    return f"font-size: 18px; font-weight: 700; color: {t['text']}; background: transparent;"


def dialog_subtitle() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


def btn_primary() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['amber']};
    border: none;
    border-radius: 9px;
    padding: 9px 20px;
    font-size: 15px; font-weight: 500;
    color: white;
}}
QPushButton:hover {{ background: {t['amber_dark']}; }}
QPushButton:disabled {{ background: {t['placeholder']}; }}
"""


def btn_ghost() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 9px 20px;
    font-size: 15px; font-weight: 500;
    color: {t['text_secondary']};
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""
