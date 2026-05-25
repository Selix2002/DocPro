"""
QSS generators for the Report module.
Every function reads theme.current at call time — hot-swap safe.
Blue theme: #1D4ED8 (not amber).
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
        f"background: {t['blue_light']}; color: {t['blue_dark']}; "
        f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
        f"padding: 3px 10px; border-radius: 6px;"
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


def title_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: none;
    border-bottom: 1px solid {t['border']};
    border-radius: 0px;
    padding: 4px 8px;
    font-size: 15px; font-weight: 500;
    color: {t['text']};
    background: transparent;
    min-width: 180px; max-width: 280px;
}}
QLineEdit:focus {{ border-bottom-color: {t['blue']}; }}
QLineEdit::placeholder {{ color: {t['placeholder']}; }}
"""


def status_pill(status: str) -> str:
    t = _t()
    mapping = {
        "Borrador":   (t["amber_light"], t["amber_dark"]),
        "Finalizado": (t["green_light"], t["green_text"]),
        "Enviado":    (t["blue_light"],  t["blue_dark"]),
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
    color = {"saving": t["blue"], "saved": t["green"], "error": t["red"]}.get(state, t["placeholder"])
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
    background: {t['blue']};
    border: none;
    border-radius: 9px;
    padding: 7px 16px;
    font-size: 14px; font-weight: 600;
    color: white;
}}
QPushButton:hover {{ background: {t['blue_dark']}; }}
QPushButton:disabled {{ background: {t['placeholder']}; }}
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


# ── Form panel ────────────────────────────────────────────────────────────────

def form_panel() -> str:
    t = _t()
    return f"QWidget#FormPanel {{ background: {t['bg']}; }}"


def meta_row() -> str:
    return """
QWidget#MetaRow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EFF6FF, stop:1 #F0F4FF);
    border: 1px solid #93C5FD;
    border-radius: 14px;
}
"""


def meta_label() -> str:
    t = _t()
    return (
        f"font-size: 11px; font-weight: 600; text-transform: uppercase; "
        f"letter-spacing: 1px; color: {t['muted']}; background: transparent;"
    )


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
QLineEdit:focus {{ border-color: {t['blue']}; }}
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
        f"font-size: 13px; font-weight: 600; color: {t['blue_dark']}; "
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
QDateEdit:focus {{ border-color: {t['blue']}; }}
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
    return f"font-size: 16px; color: {t['blue']}; background: transparent;"


def section_number_label() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 700; color: {t['blue']}; "
        f"background: {t['blue_light']}; padding: 2px 7px; border-radius: 4px;"
    )


def section_title_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: none;
    border-radius: 0px;
    padding: 0px 4px;
    font-size: 14px; font-weight: 600;
    color: {t['text']};
    background: transparent;
}}
QLineEdit:focus {{ border-bottom: 1px solid {t['blue']}; background: transparent; }}
QLineEdit:read-only {{ color: {t['muted']}; }}
"""


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
QLineEdit:focus {{ border-color: {t['blue']}; background: {t['surface']}; }}
QLineEdit:read-only {{
    background: {t['border_soft']};
    color: {t['muted']};
    border-color: {t['border_soft']};
}}
QLineEdit:disabled {{ background: {t['border_soft']}; color: {t['placeholder']}; }}
"""


# ── Section content ───────────────────────────────────────────────────────────

def section_textarea() -> str:
    t = _t()
    return f"""
QTextEdit {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 10px 12px;
    font-size: 14px;
    color: {t['text']};
    background: {t['surface']};
}}
QTextEdit:focus {{ border-color: {t['blue']}; }}
QTextEdit:disabled {{ background: {t['border_soft']}; color: {t['placeholder']}; }}
"""


def sub_textarea() -> str:
    return section_textarea()


# ── Section/subsection action buttons ─────────────────────────────────────────

def btn_section_icon() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 6px;
    min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px;
    font-size: 11px; color: {t['muted']};
}}
QPushButton:hover {{ background: {t['bg']}; color: {t['text']}; }}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


def btn_section_delete() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 6px;
    min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px;
    font-size: 11px; color: {t['placeholder']};
}}
QPushButton:hover {{ background: {t['red_light']}; color: {t['red']}; border-color: #FECACA; }}
"""


def add_sub_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px dashed {t['border']};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px; font-weight: 500;
    color: {t['muted']};
    text-align: left;
}}
QPushButton:hover {{
    background: {t['blue_light']};
    border-color: {t['blue']};
    color: {t['blue']};
}}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


def add_section_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 2px dashed {t['border']};
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px; font-weight: 500;
    color: {t['muted']};
}}
QPushButton:hover {{
    background: {t['blue_light']};
    border-color: {t['blue']};
    color: {t['blue']};
}}
QPushButton:disabled {{ color: {t['placeholder']}; border-color: {t['border_soft']}; }}
"""


def ai_btn_stub() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['purple_light']};
    border: 1px solid #E9D5FF;
    border-radius: 7px;
    padding: 5px 10px;
    font-size: 12px; font-weight: 500;
    color: {t['purple']};
}}
QPushButton:hover {{ background: #EDE9FE; }}
QPushButton:disabled {{
    color: {t['placeholder']};
    border-color: {t['border_soft']};
    background: {t['border_soft']};
}}
"""


# ── Subsection card ───────────────────────────────────────────────────────────

def subsection_card() -> str:
    t = _t()
    return f"""
QFrame#SubsectionCard {{
    background: {t['bg']};
    border: 1px solid {t['border_soft']};
    border-radius: 10px;
}}
"""


# ── Observations ──────────────────────────────────────────────────────────────

def obs_inactive() -> str:
    t = _t()
    return f"""
QWidget#ObsInactive {{
    background: {t['border_soft']};
    border: 1px dashed {t['border']};
    border-radius: 12px;
}}
"""


def obs_inactive_label() -> str:
    t = _t()
    return f"font-size: 14px; color: {t['muted']}; background: transparent;"


def btn_activate_section() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px; font-weight: 500;
    color: {t['blue']};
}}
QPushButton:hover {{ background: {t['blue_light']}; border-color: {t['blue']}; }}
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
        f"background: {t['blue_light']}; color: {t['blue']}; "
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
    background: {t['blue_light']};
    border: 1px solid {t['blue']};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px; font-weight: 600;
    color: {t['blue_dark']};
}}
QPushButton:hover {{ background: {t['blue']}; color: white; border-color: {t['blue']}; }}
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
QLineEdit:focus {{ border-color: {t['blue']}; }}
"""
