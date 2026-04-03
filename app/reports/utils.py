"""Shared PDF building utilities for all Tiyara report generators."""

import re
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from app.sessions.models import Message

# ── Colour palette ─────────────────────────────────────────────────────────────
C_DARK = colors.HexColor("#0d1117")
C_MID = colors.HexColor("#1c2433")
C_ACCENT = colors.HexColor("#2d6af0")
C_LIGHT_GRAY = colors.HexColor("#8b949e")
C_BORDER = colors.HexColor("#e1e4e8")
C_ROW_ALT = colors.HexColor("#f6f8fa")
C_FAULT_BG = colors.HexColor("#fffbf0")
C_RES_BG = colors.HexColor("#f0fff4")
C_SUCCESS = colors.HexColor("#3fb950")
C_WARNING = colors.HexColor("#d29922")
C_WHITE = colors.white


# ── Text helpers ───────────────────────────────────────────────────────────────

def fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d %b %Y  %H:%M UTC")


def fmt_date_short(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d %b %Y")


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def safe_para(text: str, style: ParagraphStyle) -> Paragraph:
    safe = xml_escape(str(text))
    if len(safe) > 4000:
        safe = safe[:4000] + " … [truncated]"
    return Paragraph(safe, style)


# ── Style builder ──────────────────────────────────────────────────────────────

def build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TTitle", parent=base["Normal"],
            fontSize=20, textColor=C_WHITE, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "TSubtitle", parent=base["Normal"],
            fontSize=8.5, textColor=C_LIGHT_GRAY, alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "header_right": ParagraphStyle(
            "THeaderRight", parent=base["Normal"],
            fontSize=9, textColor=C_WHITE, alignment=TA_RIGHT,
            fontName="Helvetica-Bold", leading=14,
        ),
        "header_right_sm": ParagraphStyle(
            "THeaderRightSm", parent=base["Normal"],
            fontSize=8, textColor=C_LIGHT_GRAY, alignment=TA_RIGHT,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "TSection", parent=base["Normal"],
            fontSize=8, textColor=C_ACCENT,
            fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3,
        ),
        "label": ParagraphStyle(
            "TLabel", parent=base["Normal"],
            fontSize=7.5, textColor=C_LIGHT_GRAY, fontName="Helvetica",
        ),
        "body": ParagraphStyle(
            "TBody", parent=base["Normal"],
            fontSize=9, textColor=C_DARK, leading=14,
            fontName="Helvetica", spaceAfter=3,
        ),
        "body_bold": ParagraphStyle(
            "TBodyBold", parent=base["Normal"],
            fontSize=9, textColor=C_DARK, leading=14,
            fontName="Helvetica-Bold",
        ),
        "mono": ParagraphStyle(
            "TMono", parent=base["Normal"],
            fontSize=8, textColor=C_DARK, fontName="Courier",
            leading=12, spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "TFooter", parent=base["Normal"],
            fontSize=7, textColor=C_LIGHT_GRAY, alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "signoff_note": ParagraphStyle(
            "TSignNote", parent=base["Normal"],
            fontSize=7.5, textColor=C_LIGHT_GRAY, fontName="Helvetica-Oblique",
            spaceAfter=10,
        ),
        "status_bar": ParagraphStyle(
            "TStatusBar", parent=base["Normal"],
            fontSize=8, textColor=C_WHITE, fontName="Helvetica",
        ),
        "role_user": ParagraphStyle(
            "TRoleUser", parent=base["Normal"],
            fontSize=7, textColor=C_WHITE, fontName="Helvetica-Bold",
        ),
        "role_ai": ParagraphStyle(
            "TRoleAI", parent=base["Normal"],
            fontSize=7, textColor=C_WHITE, fontName="Helvetica-Bold",
        ),
        "draft_notice": ParagraphStyle(
            "TDraft", parent=base["Normal"],
            fontSize=7, textColor=C_WARNING, alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "step_num": ParagraphStyle(
            "TStepNum", parent=base["Normal"],
            fontSize=9, textColor=C_WHITE, alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "step_title": ParagraphStyle(
            "TStepTitle", parent=base["Normal"],
            fontSize=9, textColor=C_DARK, fontName="Helvetica-Bold",
        ),
        "step_body": ParagraphStyle(
            "TStepBody", parent=base["Normal"],
            fontSize=8.5, textColor=C_DARK, fontName="Helvetica", leading=13,
        ),
    }


# ── PDF building blocks ────────────────────────────────────────────────────────

def section_block(story: list, number: str, title: str, S: dict) -> None:
    story.append(Paragraph(f"{number}  {title}", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_ACCENT))
    story.append(Spacer(1, 6))


def doc_header(story: list, doc_title: str, doc_subtitle: str,
               report_number: str, date_str: str, S: dict) -> None:
    """Render the dark top header band common to all document types."""
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(doc_title, S["subtitle"]),
            "",
            Paragraph(date_str, S["header_right_sm"]),
        ],
        [
            Paragraph(doc_subtitle, S["subtitle"]) if doc_subtitle else Paragraph("", S["subtitle"]),
            "", "",
        ],
    ]
    ht = Table(header_data, colWidths=["55%", "5%", "40%"])
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(ht)


def draft_banner(story: list, text: str, S: dict) -> None:
    """Orange warning banner for AI-generated documents."""
    t = Table([[Paragraph(text, S["draft_notice"])]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2a1f00")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def kv_table(rows: list[tuple[str, str]], S: dict) -> Table:
    """Two-column key-value table (label | value)."""
    data = [
        [Paragraph(lbl, S["label"]), safe_para(val, S["body"])]
        for lbl, val in rows
    ]
    t = Table(data, colWidths=["30%", "70%"])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), C_ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def kv4_table(rows: list[tuple[str, str, str, str]], S: dict) -> Table:
    """Four-column key-value table (label|value|label|value)."""
    data = [
        [
            Paragraph(r[0], S["label"]), safe_para(r[1], S["body"]),
            Paragraph(r[2], S["label"]), safe_para(r[3], S["body"]),
        ]
        for r in rows
    ]
    t = Table(data, colWidths=["18%", "32%", "18%", "32%"])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), C_ROW_ALT),
        ("BACKGROUND", (2, 0), (2, -1), C_ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def doc_footer(story: list, report_number: str, lang_label: str, S: dict) -> None:
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.3, color=C_LIGHT_GRAY))
    story.append(Spacer(1, 4))
    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")
    story.append(Paragraph(
        f"TIYARA Aviation AI Platform  |  {report_number}  |  {generated_at}  |  {lang_label}",
        S["footer"],
    ))


def signoff_block(story: list, roles: list[str], S: dict) -> None:
    """Render a sign-off table with the given role names."""
    _line = "_" * 38
    _date_line = "_" * 16
    rows = []
    for role_name in roles:
        rows.append([
            Paragraph(role_name, S["label"]),
            Paragraph(_line, S["body"]),
            Paragraph("Date", S["label"]),
            Paragraph(_date_line, S["body"]),
        ])
        rows.append([Paragraph("", S["label"]), Paragraph("", S["body"]),
                     Paragraph("", S["label"]), Paragraph("", S["body"])])
    t = Table(rows, colWidths=["22%", "35%", "10%", "33%"])
    t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))


# ── AI message parsing ─────────────────────────────────────────────────────────

def get_latest_ai_message(messages: list[Message]) -> Optional[str]:
    """Return the content of the last assistant message, or None."""
    for m in reversed(messages):
        if m.role == "assistant" and m.content:
            return m.content
    return None


def parse_ai_sections(content: str) -> dict[str, str]:
    """Parse ## Section headings from an AI response into a dict."""
    sections: dict[str, str] = {}
    current_key: Optional[str] = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line[3:].strip()
            current_lines = []
        elif current_key:
            # Stop collecting at SUGGESTIONS line
            if line.startswith("SUGGESTIONS:"):
                sections[current_key] = "\n".join(current_lines).strip()
                current_key = None
                break
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def extract_steps(procedure_text: str) -> list[dict]:
    """Extract numbered steps from Procedure section text.

    Returns a list of dicts with keys: number, title, instruction.
    """
    steps: list[dict] = []
    current: Optional[dict] = None

    for line in procedure_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Match "1. **Title** — instruction" or "1. Title — instruction"
        m = re.match(r"^(\d+)\.\s+(?:\*\*(.+?)\*\*\s*[—-]\s*)?(.+)$", line)
        if m:
            if current:
                steps.append(current)
            title = m.group(2) or f"Step {m.group(1)}"
            instruction = m.group(3).strip()
            current = {
                "number": m.group(1),
                "title": title,
                "instruction": instruction,
                "details": [],
            }
        elif current and line.startswith(("-", "•", "*")):
            current["details"].append(line.lstrip("-•* "))
        elif current:
            # continuation of previous step instruction
            current["instruction"] += " " + line

    if current:
        steps.append(current)

    return steps


def extract_risk_level(messages: list[Message]) -> str:
    """Extract the risk level from the latest AI message."""
    content = get_latest_ai_message(messages)
    if not content:
        return "—"
    sections = parse_ai_sections(content)
    risk_text = sections.get("Risk Level", "")
    # Take first non-empty line
    for line in risk_text.splitlines():
        line = line.strip()
        if line:
            return line
    return "—"


def extract_ata_from_messages(messages: list[Message]) -> str:
    """Try to find ATA chapter reference in AI messages."""
    for m in reversed(messages):
        if m.role != "assistant" or not m.content:
            continue
        match = re.search(r"ATA\s+(\d{2}[-–]\d{2}(?:[-–]\d{2})?)", m.content)
        if match:
            return match.group(1)
    return "—"
