"""PDF maintenance report generator.

Produces a professional MRO-style work order report for a completed
or in-progress diagnostic session, matching the format used in
real-world aircraft maintenance shops.
"""

import io
import json
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.auth.models import User
from app.documents.models import CaseHistory
from app.sessions.models import Message, Session

# ── Colour palette ─────────────────────────────────────────────────────────────
_DARK = colors.HexColor("#0d1117")
_MID = colors.HexColor("#1c2433")
_ACCENT = colors.HexColor("#2d6af0")
_LIGHT_GRAY = colors.HexColor("#8b949e")
_BORDER = colors.HexColor("#e1e4e8")
_ROW_ALT = colors.HexColor("#f6f8fa")
_FAULT_BG = colors.HexColor("#fffbf0")
_RES_BG = colors.HexColor("#f0fff4")
_SUCCESS = colors.HexColor("#3fb950")
_WARNING = colors.HexColor("#d29922")
_WHITE = colors.white


def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d %b %Y  %H:%M UTC")


def _xml_escape(text: str) -> str:
    """Escape characters that would break reportlab's XML parser."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def _safe_para(text: str, style: ParagraphStyle) -> Paragraph:
    """Return a Paragraph with XML-escaped content, truncated if very long."""
    safe = _xml_escape(str(text))
    if len(safe) > 4000:
        safe = safe[:4000] + " … [truncated]"
    return Paragraph(safe, style)


def _section_block(
    story: list,
    number: str,
    title: str,
    section_style: ParagraphStyle,
) -> None:
    story.append(Paragraph(f"{number}  {title}", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_ACCENT))
    story.append(Spacer(1, 6))


def generate_session_report(
    session: Session,
    messages: list[Message],
    technician: User,
    case_history: Optional[CaseHistory] = None,
) -> bytes:
    """Build and return a PDF maintenance report as raw bytes."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Tiyara Maintenance Report — {session.engine_type}",
        author="Tiyara Aviation AI Platform",
        subject="Aircraft Maintenance Diagnostic Report",
    )

    base = getSampleStyleSheet()

    # ── Custom styles ────────────────────────────────────────────────────────
    S = {
        "title": ParagraphStyle(
            "TTitle", parent=base["Normal"],
            fontSize=20, textColor=_WHITE, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "TSubtitle", parent=base["Normal"],
            fontSize=8.5, textColor=_LIGHT_GRAY, alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "header_right": ParagraphStyle(
            "THeaderRight", parent=base["Normal"],
            fontSize=9, textColor=_WHITE, alignment=TA_RIGHT,
            fontName="Helvetica-Bold", leading=14,
        ),
        "header_right_sm": ParagraphStyle(
            "THeaderRightSm", parent=base["Normal"],
            fontSize=8, textColor=_LIGHT_GRAY, alignment=TA_RIGHT,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "TSection", parent=base["Normal"],
            fontSize=8, textColor=_ACCENT,
            fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3,
        ),
        "label": ParagraphStyle(
            "TLabel", parent=base["Normal"],
            fontSize=7.5, textColor=_LIGHT_GRAY, fontName="Helvetica",
        ),
        "body": ParagraphStyle(
            "TBody", parent=base["Normal"],
            fontSize=9, textColor=_DARK, leading=14,
            fontName="Helvetica", spaceAfter=3,
        ),
        "mono": ParagraphStyle(
            "TMono", parent=base["Normal"],
            fontSize=8, textColor=_DARK, fontName="Courier",
            leading=12, spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "TFooter", parent=base["Normal"],
            fontSize=7, textColor=_LIGHT_GRAY, alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "signoff_note": ParagraphStyle(
            "TSignNote", parent=base["Normal"],
            fontSize=7.5, textColor=_LIGHT_GRAY, fontName="Helvetica-Oblique",
            spaceAfter=10,
        ),
        "status_bar": ParagraphStyle(
            "TStatusBar", parent=base["Normal"],
            fontSize=8, textColor=_WHITE, fontName="Helvetica",
        ),
        "role_user": ParagraphStyle(
            "TRoleUser", parent=base["Normal"],
            fontSize=7, textColor=_WHITE, fontName="Helvetica-Bold",
        ),
        "role_ai": ParagraphStyle(
            "TRoleAI", parent=base["Normal"],
            fontSize=7, textColor=_WHITE, fontName="Helvetica-Bold",
        ),
    }

    story: list = []
    report_number = f"TIY-{str(session.id).upper()[:8]}"

    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(
                f"Report No.<br/><b>{report_number}</b>",
                S["header_right"],
            ),
        ],
        [
            Paragraph("AVIATION MAINTENANCE DIAGNOSTIC REPORT", S["subtitle"]),
            "",
            Paragraph(_fmt_date(session.created_at), S["header_right_sm"]),
        ],
    ]
    header_table = Table(header_data, colWidths=["55%", "5%", "40%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(header_table)

    # Status bar
    status_color = _SUCCESS if session.status == "resolved" else _WARNING
    status_p = ParagraphStyle(
        "TStatusColored", parent=base["Normal"],
        fontSize=8, textColor=status_color, fontName="Helvetica-Bold",
    )
    bar_data = [[
        Paragraph(f"STATUS: {session.status.upper()}", status_p),
        Paragraph(f"ENGINE: {_xml_escape(session.engine_type)}", S["status_bar"]),
        Paragraph(
            f"TECHNICIAN: {_xml_escape(technician.full_name.upper())}",
            ParagraphStyle("TSBRight", parent=base["Normal"], fontSize=8,
                           textColor=_WHITE, fontName="Helvetica", alignment=TA_RIGHT),
        ),
    ]]
    bar_table = Table(bar_data, colWidths=["33%", "34%", "33%"])
    bar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _MID),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(bar_table)
    story.append(Spacer(1, 10))

    sec = 0  # section counter

    # ═══════════════════════════════════════════════════════════════════════════
    # 01 — WORK ORDER INFORMATION
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    _section_block(story, f"{sec:02d}", "WORK ORDER INFORMATION", S["section"])

    wo_rows = [
        [
            Paragraph("Report Number", S["label"]),
            Paragraph(report_number, S["body"]),
            Paragraph("Session ID", S["label"]),
            _safe_para(str(session.id), S["mono"]),
        ],
        [
            Paragraph("Date Opened", S["label"]),
            Paragraph(_fmt_date(session.created_at), S["body"]),
            Paragraph("Date Closed / Updated", S["label"]),
            Paragraph(_fmt_date(session.updated_at), S["body"]),
        ],
        [
            Paragraph("Engine / A/C Type", S["label"]),
            _safe_para(session.engine_type, S["body"]),
            Paragraph("Final Status", S["label"]),
            Paragraph(
                session.status.upper(),
                ParagraphStyle("TWOStatus", parent=base["Normal"], fontSize=9,
                               textColor=status_color, fontName="Helvetica-Bold"),
            ),
        ],
    ]
    wo_table = Table(wo_rows, colWidths=["18%", "32%", "18%", "32%"])
    wo_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
        ("BACKGROUND", (0, 0), (0, -1), _ROW_ALT),
        ("BACKGROUND", (2, 0), (2, -1), _ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(wo_table)
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 02 — FAULT REPORTED
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    _section_block(story, f"{sec:02d}", "FAULT REPORTED", S["section"])

    fault_table = Table(
        [[_safe_para(session.problem_description, S["body"])]],
        colWidths=["100%"],
    )
    fault_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), _FAULT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(fault_table)
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 03 — PERSONNEL ON RECORD
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    _section_block(story, f"{sec:02d}", "PERSONNEL ON RECORD", S["section"])

    pers_rows = [
        [
            Paragraph("Full Name", S["label"]),
            _safe_para(technician.full_name, S["body"]),
            Paragraph("Role", S["label"]),
            _safe_para(technician.role.title(), S["body"]),
        ],
        [
            Paragraph("Company / Operator", S["label"]),
            _safe_para(technician.company, S["body"]),
            Paragraph("Email", S["label"]),
            _safe_para(technician.email, S["body"]),
        ],
    ]
    pers_table = Table(pers_rows, colWidths=["18%", "32%", "18%", "32%"])
    pers_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
        ("BACKGROUND", (0, 0), (0, -1), _ROW_ALT),
        ("BACKGROUND", (2, 0), (2, -1), _ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pers_table)
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 04 — MAINTENANCE HISTORY PATTERNS  (only if Excel data available)
    # ═══════════════════════════════════════════════════════════════════════════
    if session.excel_pattern_summary:
        sec += 1
        _section_block(story, f"{sec:02d}", "MAINTENANCE HISTORY PATTERNS", S["section"])
        summary = session.excel_pattern_summary
        pat_rows = []
        if summary.get("top_faults"):
            pat_rows.append([
                Paragraph("Top Recurring Faults", S["label"]),
                _safe_para(", ".join(summary["top_faults"]), S["body"]),
            ])
        if summary.get("recurring_components"):
            pat_rows.append([
                Paragraph("Recurring Components", S["label"]),
                _safe_para(", ".join(summary["recurring_components"]), S["body"]),
            ])
        if summary.get("unresolved_patterns"):
            pat_rows.append([
                Paragraph("Unresolved Patterns", S["label"]),
                _safe_para(
                    ", ".join(str(p) for p in summary["unresolved_patterns"]),
                    S["body"],
                ),
            ])
        if summary.get("risk_summary"):
            pat_rows.append([
                Paragraph("Risk Summary", S["label"]),
                _safe_para(summary["risk_summary"], S["body"]),
            ])
        if pat_rows:
            pat_table = Table(pat_rows, colWidths=["25%", "75%"])
            pat_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("BACKGROUND", (0, 0), (0, -1), _ROW_ALT),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(pat_table)
        story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 0N — AI RESOLUTION SUMMARY  (only if session has been resolved)
    # ═══════════════════════════════════════════════════════════════════════════
    if case_history:
        sec += 1
        _section_block(story, f"{sec:02d}", "AI RESOLUTION SUMMARY", S["section"])
        try:
            res_sum = (
                json.loads(case_history.resolution_summary)
                if isinstance(case_history.resolution_summary, str)
                else case_history.resolution_summary
            )
        except Exception:
            res_sum = {"raw": str(case_history.resolution_summary)}

        res_rows = []
        for key, label in [
            ("fault_description", "Fault Description"),
            ("root_cause", "Root Cause"),
            ("outcome", "Outcome"),
            ("ata_chapter", "ATA Chapter"),
        ]:
            if res_sum.get(key):
                res_rows.append([
                    Paragraph(label, S["label"]),
                    _safe_para(str(res_sum[key]), S["body"]),
                ])

        if res_sum.get("steps_applied"):
            steps = res_sum["steps_applied"]
            if isinstance(steps, list):
                steps_text = "<br/>".join(
                    f"{i + 1}.  {_xml_escape(str(s))}" for i, s in enumerate(steps)
                )
            else:
                steps_text = _xml_escape(str(steps))
            res_rows.append([
                Paragraph("Steps Applied", S["label"]),
                Paragraph(steps_text, S["mono"]),
            ])

        if res_sum.get("raw"):
            res_rows.append([
                Paragraph("Summary", S["label"]),
                _safe_para(res_sum["raw"], S["body"]),
            ])

        if res_rows:
            res_table = Table(res_rows, colWidths=["25%", "75%"])
            res_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("BACKGROUND", (0, 0), (0, -1), _RES_BG),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(res_table)
        story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 0N — DIAGNOSTIC CONVERSATION TRANSCRIPT
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    _section_block(story, f"{sec:02d}", "DIAGNOSTIC CONVERSATION TRANSCRIPT", S["section"])

    if messages:
        for msg in messages:
            is_user = msg.role == "user"
            role_label = "TECHNICIAN" if is_user else "TIYARA AI"
            header_bg = _MID if is_user else _ACCENT
            role_style = S["role_user"] if is_user else S["role_ai"]

            header_para = Paragraph(
                f"  {role_label}  —  {_fmt_date(msg.created_at)}",
                role_style,
            )
            content_para = _safe_para(msg.content, S["mono"])

            msg_table = Table(
                [[header_para], [content_para]],
                colWidths=["100%"],
            )
            msg_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), header_bg),
                ("TOPPADDING", (0, 0), (0, 0), 5),
                ("BOTTOMPADDING", (0, 0), (0, 0), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (0, 1), 8),
                ("BOTTOMPADDING", (0, 1), (0, 1), 8),
                ("BOX", (0, 0), (-1, -1), 0.4, _BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(msg_table)
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No conversation messages recorded.", S["body"]))

    story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════════════════════════
    # SIGN-OFF & CERTIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("SIGN-OFF &amp; CERTIFICATION", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_ACCENT))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "I certify that the maintenance described in this report was performed in accordance "
        "with the applicable Aircraft Maintenance Manual (AMM) procedures and all relevant "
        "regulatory requirements.",
        S["signoff_note"],
    ))

    _line = "_" * 38
    _date_line = "_" * 16
    signoff_rows = [
        [
            Paragraph("Certifying Technician", S["label"]),
            Paragraph(_line, S["body"]),
            Paragraph("Date", S["label"]),
            Paragraph(_date_line, S["body"]),
        ],
        [Paragraph("", S["label"]), Paragraph("", S["body"]),
         Paragraph("", S["label"]), Paragraph("", S["body"])],
        [
            Paragraph("Engineer / Supervisor", S["label"]),
            Paragraph(_line, S["body"]),
            Paragraph("Date", S["label"]),
            Paragraph(_date_line, S["body"]),
        ],
        [Paragraph("", S["label"]), Paragraph("", S["body"]),
         Paragraph("", S["label"]), Paragraph("", S["body"])],
        [
            Paragraph("Quality Assurance", S["label"]),
            Paragraph(_line, S["body"]),
            Paragraph("Date", S["label"]),
            Paragraph(_date_line, S["body"]),
        ],
    ]
    signoff_table = Table(signoff_rows, colWidths=["22%", "35%", "10%", "33%"])
    signoff_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(signoff_table)
    story.append(Spacer(1, 16))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.3, color=_LIGHT_GRAY))
    story.append(Spacer(1, 4))
    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")
    story.append(Paragraph(
        f"Generated by TIYARA Aviation AI Platform  |  {report_number}  |  "
        f"{generated_at}  |  CONFIDENTIAL — FOR MAINTENANCE USE ONLY",
        S["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
