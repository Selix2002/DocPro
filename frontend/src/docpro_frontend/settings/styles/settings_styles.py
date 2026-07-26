"""
QSS generators for the Settings module (Propuesta A layout).

Every function reads `theme.current` at call time — theme-aware by design.
After theme.activate(mode), call these functions again and re-apply with
setStyleSheet() to hot-swap themes with zero logic changes.
"""
import docpro_frontend.theme as _th


def _t() -> dict[str, str]:
    return _th.current


def _badge(color: str) -> tuple[str, str]:
    bg_key, fg_key = _th.ICON_BADGE.get(color, ("border_soft", "muted"))
    return _t()[bg_key], _t()[fg_key]


# ── App header ────────────────────────────────────────────────────────

def settings_header() -> str:
    t = _t()
    return f"""
QWidget#SettingsHeader {{
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


def header_title_icon() -> str:
    t = _t()
    return f"font-size: 22px; color: {t['muted']}; background: transparent;"


def header_title_text() -> str:
    t = _t()
    return f"font-size: 20px; font-weight: 600; color: {t['text']}; background: transparent;"


# ── Sidebar ───────────────────────────────────────────────────────────

def sidebar() -> str:
    t = _t()
    return f"""
QWidget#Sidebar {{
    background: {t['surface']};
    border-right: 1px solid {t['border']};
}}
"""


def nav_group_label() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 700; letter-spacing: 2px; "
        f"color: {t['placeholder']}; background: transparent;"
    )


def nav_item(active: bool) -> str:
    t = _t()
    if active:
        return f"""
QWidget#NavItem {{
    background: {t['amber_light']};
    border-radius: 9px;
}}
"""
    return f"""
QWidget#NavItem {{
    background: transparent;
    border-radius: 9px;
}}
QWidget#NavItem:hover {{ background: {t['border_soft']}; }}
"""


def nav_item_icon(active: bool) -> str:
    t = _t()
    color = t["amber"] if active else t["muted"]
    return f"font-size: 20px; color: {color}; background: transparent;"


def nav_item_text(active: bool) -> str:
    t = _t()
    color = t["amber_dark"] if active else t["muted"]
    weight = "600" if active else "500"
    return f"font-size: 17px; font-weight: {weight}; color: {color}; background: transparent;"


def nav_badge(state: str) -> str:
    t = _t()
    bg_key, text_key, _ = _th.STATUS_PALETTE.get(state, ("border_soft", "muted", "placeholder"))
    return (
        f"background: {t[bg_key]}; color: {t[text_key]}; "
        f"font-size: 13px; font-weight: 700; "
        f"padding: 2px 8px; border-radius: 5px;"
    )


# ── Content area ──────────────────────────────────────────────────────

def content_area() -> str:
    t = _t()
    return f"QWidget#ContentArea {{ background: {t['surface']}; }}"


def content_scroll() -> str:
    t = _t()
    return f"QWidget#ContentScroll {{ background: {t['surface']}; }}"


def page_head_title() -> str:
    t = _t()
    return f"font-size: 24px; font-weight: 700; color: {t['text']}; background: transparent;"


def page_head_sub() -> str:
    t = _t()
    return f"font-size: 16px; color: {t['muted']}; background: transparent;"


# ── Card section ──────────────────────────────────────────────────────

def card() -> str:
    t = _t()
    return f"""
QFrame#CardSection {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 14px;
}}
"""


def card_head() -> str:
    t = _t()
    return f"""
QWidget#CardHead {{
    background: {t['surface_alt']};
    border-bottom: 1px solid {t['border_soft']};
    border-radius: 0px;
}}
"""


def card_icon_badge(color: str) -> str:
    bg, fg = _badge(color)
    return (
        f"background: {bg}; border-radius: 8px; "
        f"font-size: 18px; color: {fg};"
    )


def card_head_title() -> str:
    t = _t()
    return f"font-size: 17px; font-weight: 600; color: {t['text']}; background: transparent;"


def card_head_sub() -> str:
    t = _t()
    return f"font-size: 14px; color: {t['muted']}; background: transparent;"


def card_body() -> str:
    return "background: transparent;"


# ── Status pill (card-head + future use) ─────────────────────────────

def status_pill(state: str) -> str:
    t = _t()
    bg_key, text_key, _ = _th.STATUS_PALETTE.get(state, ("border_soft", "muted", "placeholder"))
    return (
        f"background: {t[bg_key]}; color: {t[text_key]}; "
        f"font-size: 13px; font-weight: 600; "
        f"padding: 4px 12px; border-radius: 20px;"
    )


def status_pill_dot(state: str) -> str:
    t = _t()
    _, _, dot_key = _th.STATUS_PALETTE.get(state, ("border_soft", "muted", "placeholder"))
    return (
        f"background: {t[dot_key]}; border-radius: 4px; "
        f"min-width: 7px; max-width: 7px; min-height: 7px; max-height: 7px;"
    )


# ── Form shared ───────────────────────────────────────────────────────

def d_section_title() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 700; letter-spacing: 1px; "
        f"color: {t['muted']}; background: transparent;"
    )


def field_label() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 600; letter-spacing: 1px; "
        f"color: {t['muted']}; background: transparent;"
    )


def field_input() -> str:
    t = _t()
    return f"""
QLineEdit, QTextEdit {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 9px 12px;
    font-size: 17px;
    color: {t['text']};
    background: {t['surface']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {t['amber']};
}}
"""


def field_combobox() -> str:
    t = _t()
    return f"""
QComboBox {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 8px 12px;
    font-size: 17px;
    color: {t['text']};
    background: {t['surface']};
}}
QComboBox:focus {{
    border: 1px solid {t['amber']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    selection-background-color: {t['amber_light']};
    selection-color: {t['amber']};
    outline: 0;
    padding: 4px 0;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    min-height: 22px;
}}
"""


def field_hint() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


# ── Buttons ───────────────────────────────────────────────────────────

def btn_primary() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['amber']};
    border: none;
    border-radius: 9px;
    padding: 9px 18px;
    font-size: 17px; font-weight: 500;
    color: white;
}}
QPushButton:hover {{ background: {t['amber_dark']}; }}
"""


def btn_ghost() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent;
    border: 1px solid {t['border']};
    border-radius: 9px;
    padding: 9px 18px;
    font-size: 17px; font-weight: 500;
    color: {t['text_secondary']};
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""


def btn_small() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 15px; font-weight: 500;
    color: {t['text_secondary']};
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""


def btn_danger_small() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 15px; font-weight: 500;
    color: {t['red']};
}}
QPushButton:hover {{ background: {t['red_light']}; border-color: #FECACA; }}
"""


def btn_validate() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['blue_light']};
    border: 1px solid {t['blue_light']};
    border-radius: 9px;
    padding: 8px 14px;
    font-size: 15px; font-weight: 500;
    color: {t['blue_dark']};
}}
QPushButton:hover {{ background: #BFDBFE; }}
"""


def btn_add_template() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['bg']};
    border: 1px dashed #93C5FD;
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 16px; font-weight: 500;
    color: {t['blue']};
    text-align: left;
}}
QPushButton:hover {{
    background: {t['blue_light']};
    border-style: solid;
    border-color: {t['blue']};
}}
"""


# ── Counter row ───────────────────────────────────────────────────────

def counter_row_bg() -> str:
    t = _t()
    return f"""
QWidget#CounterRow {{
    background: {t['border_soft']};
    border-radius: 10px;
}}
"""


def counter_label_name() -> str:
    t = _t()
    return f"font-size: 16px; font-weight: 500; color: {t['text']}; background: transparent;"


def counter_label_next() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


def counter_tag() -> str:
    t = _t()
    return (
        f"font-size: 13px; font-weight: 600; letter-spacing: 1px; "
        f"color: {t['muted']}; background: transparent;"
    )


def counter_input() -> str:
    t = _t()
    return f"""
QLineEdit {{
    border: 1px solid {t['border']};
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 16px; font-weight: 600;
    background: {t['surface']};
    color: {t['text']};
}}
QLineEdit:focus {{ border: 1px solid {t['amber']}; }}
"""


def counter_reset_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 15px; font-weight: 500;
    color: {t['muted']};
}}
QPushButton:hover {{
    background: {t['red_light']};
    border-color: #FECACA;
    color: {t['red']};
}}
"""


# ── Theme option (Propuesta A: visual preview cards) ──────────────────

def theme_option(active: bool) -> str:
    t = _t()
    if active:
        return f"""
QFrame#ThemeOption {{
    border: 2px solid {t['amber']};
    border-radius: 11px;
    background: {t['surface']};
}}
"""
    return f"""
QFrame#ThemeOption {{
    border: 2px solid {t['border']};
    border-radius: 11px;
    background: {t['surface']};
}}
QFrame#ThemeOption:hover {{ border-color: {t['placeholder']}; }}
"""


def theme_preview_container() -> str:
    t = _t()
    return f"""
QFrame#ThemePreview {{
    border: 1px solid {t['border']};
    border-radius: 7px;
    background: transparent;
}}
"""


def theme_preview_bar(dark: bool) -> str:
    if dark:
        return "background: #1F2937; border-bottom: 1px solid #374151;"
    return "background: #FFFFFF; border-bottom: 1px solid #E5E7EB;"


def theme_preview_body(dark: bool) -> str:
    return f"background: {'#111827' if dark else '#F4F4F5'};"


def theme_preview_system() -> str:
    return (
        "background: qlineargradient("
        "x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #F4F4F5, stop:0.5 #F4F4F5, "
        "stop:0.5 #111827, stop:1 #111827"
        "); border: 1px solid #E5E7EB; border-radius: 7px;"
    )


def theme_option_label() -> str:
    t = _t()
    return f"font-size: 15px; font-weight: 500; color: {t['text']}; background: transparent;"


def theme_option_sub() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


def theme_check(active: bool) -> str:
    t = _t()
    if active:
        return (
            f"background: {t['amber']}; border-radius: 9px; "
            f"font-size: 14px; font-weight: 700; color: white; "
            f"min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px;"
        )
    return (
        "background: transparent; border-radius: 9px; "
        "min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px;"
    )


# ── Account row ───────────────────────────────────────────────────────

def account_row() -> str:
    return """
QWidget#AccountRow {
    background: #F8FFF9;
    border: 1px solid #6EE7B7;
    border-radius: 11px;
}
"""


def account_avatar() -> str:
    t = _t()
    return (
        f"background: {t['green_light']}; border-radius: 18px; "
        f"font-size: 18px; font-weight: 700; color: {t['green_text']};"
    )


def account_name() -> str:
    t = _t()
    return f"font-size: 16px; font-weight: 600; color: {t['text']}; background: transparent;"


def account_detail() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


# ── Template row ──────────────────────────────────────────────────────

def template_row(hovered: bool) -> str:
    t = _t()
    border_left = t["blue"] if hovered else t["blue_light"]
    return f"""
QWidget#TemplateRow {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-left: 3px solid {border_left};
    border-radius: 10px;
}}
"""


def template_row_icon() -> str:
    t = _t()
    return f"font-size: 20px; color: {t['blue']}; background: transparent;"


def template_row_name() -> str:
    t = _t()
    return f"font-size: 16px; font-weight: 500; color: {t['text']}; background: transparent;"


def template_row_meta() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


def template_action_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent; border: 1px solid {t['border']};
    border-radius: 6px;
    font-size: 16px; color: {t['muted']};
    min-width: 28px; max-width: 28px;
    min-height: 28px; max-height: 28px;
}}
QPushButton:hover {{ background: {t['bg']}; }}
"""


def template_del_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent; border: 1px solid {t['border']};
    border-radius: 6px;
    font-size: 16px; color: {t['muted']};
    min-width: 28px; max-width: 28px;
    min-height: 28px; max-height: 28px;
}}
QPushButton:hover {{ background: {t['red_light']}; border-color: #FECACA; color: {t['red']}; }}
"""


# ── Backup action row ─────────────────────────────────────────────────

def backup_action_row() -> str:
    t = _t()
    return f"""
QWidget#BackupActionRow {{
    background: {t['border_soft']};
    border-radius: 11px;
}}
"""


def backup_icon_badge(color: str) -> str:
    bg, fg = _badge(color)
    return (
        f"background: {bg}; border-radius: 9px; "
        f"font-size: 20px; color: {fg}; "
        f"min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px;"
    )


def backup_action_name() -> str:
    t = _t()
    return f"font-size: 16px; font-weight: 600; color: {t['text']}; background: transparent;"


def backup_action_desc() -> str:
    t = _t()
    return f"font-size: 13px; color: {t['muted']}; background: transparent;"


# ── Password field toggle ─────────────────────────────────────────────

def pass_toggle_btn() -> str:
    t = _t()
    return f"""
QPushButton {{
    background: transparent; border: none;
    font-size: 18px; color: {t['placeholder']};
    min-width: 32px; max-width: 32px;
}}
QPushButton:hover {{ color: {t['muted']}; }}
"""
