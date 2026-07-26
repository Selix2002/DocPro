from __future__ import annotations

import json
from datetime import datetime
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from docpro_backend.dtos.config import CompanyProfileReadModel
from docpro_backend.dtos.quotes import QuoteReadModel
from docpro_backend.dtos.reports import ReportReadModel, ReportSectionReadModel
from docpro_backend.services.theme_service import DEFAULT_THEME, build_font_face_css


def _with_font_face(theme: dict | None) -> dict:
    t = dict(theme or DEFAULT_THEME)
    if not t.get("font_face_css"):
        t["font_face_css"] = build_font_face_css(t.get("font_family", ""))
    return t


def _build_env() -> Environment:
    template_dir = str(files("docpro_backend").joinpath("templates"))
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    env.filters["clp"] = _fmt_clp
    env.filters["date_cl"] = _fmt_date
    env.filters["fmt_qty"] = _fmt_qty
    env.filters["fmt_key"] = _fmt_key
    env.filters["content_lines"] = _content_lines
    return env


def render_quote_pdf(
    quote: QuoteReadModel,
    company: CompanyProfileReadModel | None,
    output_path: Path,
    theme: dict | None = None,
    header_imagen: str | None = None,
) -> Path:
    env = _build_env()
    template = env.get_template("quote.html.j2")
    html_str = template.render(
        quote=quote,
        company=company,
        theme=_with_font_face(theme),
        header_imagen=header_imagen,
    )
    HTML(string=html_str).write_pdf(str(output_path))
    return output_path


def quote_pdf_filename(quote: QuoteReadModel) -> str:
    safe_client = "".join(
        c if c.isalnum() or c in " _-" else "" for c in quote.client_name
    ).strip().replace(" ", "_")
    return f"{quote.number}_{safe_client}.pdf"


def render_report_pdf(
    report: ReportReadModel,
    company: CompanyProfileReadModel | None,
    firma_nombre: str | None,
    firma_cargo: str | None,
    firma_imagen: str | None,
    output_path: Path,
    theme: dict | None = None,
    header_imagen: str | None = None,
) -> Path:
    env = _build_env()
    template = env.get_template("report.html.j2")
    observations, tree_sections = _split_observations(report.sections)
    sections_tree = _build_sections_tree(tree_sections)
    html_str = template.render(
        report=report,
        company=company,
        sections_tree=sections_tree,
        observations=observations,
        firma_nombre=firma_nombre,
        firma_cargo=firma_cargo,
        firma_imagen=firma_imagen,
        theme=_with_font_face(theme),
        header_imagen=header_imagen,
    )
    HTML(string=html_str).write_pdf(str(output_path))
    return output_path


def report_pdf_filename(report: ReportReadModel) -> str:
    safe_client = "".join(
        c if c.isalnum() or c in " _-" else "" for c in report.client_name
    ).strip().replace(" ", "_")
    return f"{report.number}_{safe_client}.pdf"


def _split_observations(sections):
    """Extract the observations context section, if any; return (text_or_none, remaining_sections)."""
    observations: str | None = None
    remaining = []
    for s in sections:
        if s.parent_id is None and s.content_json and not s.content:
            try:
                parsed = json.loads(s.content_json)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, dict) and parsed.get("_kind") == "observations":
                observations = parsed.get("text", "")
                continue
        remaining.append(s)
    return observations, remaining


def _build_sections_tree(sections) -> list[dict]:
    nodes: dict[int, dict] = {}
    for s in sections:
        nodes[s.id] = {
            "section": s,
            "number": "",
            "content_json_parsed": json.loads(s.content_json) if s.content_json else None,
            "is_context": bool(s.content_json) and not s.content,
            "children": [],
        }
    roots: list[dict] = []
    for s in sections:
        node = nodes[s.id]
        if s.parent_id is None:
            roots.append(node)
        else:
            parent = nodes.get(s.parent_id)
            if parent:
                parent["children"].append(node)
    section_counter = 0
    for node in roots:
        if not node["is_context"]:
            section_counter += 1
            node["number"] = str(section_counter)
            _assign_child_numbers(node)
    return roots


def _assign_child_numbers(parent: dict) -> None:
    counter = 0
    for child in parent["children"]:
        if not child["is_context"]:
            counter += 1
            child["number"] = f"{parent['number']}.{counter}"
            _assign_child_numbers(child)


# ── Jinja2 filters ──────────────────────────────────────────────────────────

def _fmt_clp(value: float) -> str:
    """12345.6 → '$ 12.346'  (integer rounding, dot as thousands separator)"""
    return f"$ {int(round(value)):,}".replace(",", ".")


def _fmt_date(value: str) -> str:
    """'2026-05-17' or ISO datetime → '17/05/2026'"""
    try:
        return datetime.fromisoformat(value[:10]).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return value


def _fmt_qty(value: float) -> str:
    """3.0 → '3'   |   2.5 → '2.5'"""
    return str(int(value)) if value == int(value) else str(value)


def _fmt_key(value: str) -> str:
    """'tipo_equipo' → 'Tipo Equipo'"""
    return " ".join(word.capitalize() for word in value.replace("_", " ").split())


def _content_lines(value: str) -> list[str]:
    """Split content by newline and drop empty lines."""
    return [line for line in value.split("\n") if line.strip()]
