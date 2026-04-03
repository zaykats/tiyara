"""Capability Analysis PDF generator (Methods Department)."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.auth.models import User
from app.reports.translations import Lang, t
from app.reports.utils import (
    C_ACCENT,
    C_BORDER,
    C_DARK,
    C_LIGHT_GRAY,
    C_MID,
    C_ROW_ALT,
    C_WARNING,
    C_WHITE,
    build_styles,
    doc_footer,
    draft_banner,
    extract_risk_level,
    fmt_date,
    get_latest_ai_message,
    kv4_table,
    kv_table,
    parse_ai_sections,
    safe_para,
    section_block,
    signoff_block,
    xml_escape,
)
from app.sessions.models import Message, Session


def generate_capability(
    session: Session,
    messages: list[Message],
    technician: User,
    lang: Lang = "en",
) -> bytes:
    """Generate a Capability Analysis PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Tiyara — Capability Analysis",
        author="Tiyara Aviation AI Platform",
    )

    S = build_styles()
    story: list = []
    report_number = f"CA-{str(session.id).upper()[:8]}"

    # Header
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(t("ca_title", lang), S["subtitle"]),
            "",
            Paragraph(fmt_date(session.created_at), S["header_right_sm"]),
        ],
        [
            Paragraph(t("ca_subtitle", lang), S["subtitle"]),
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
    story.append(Spacer(1, 6))
    draft_banner(story, t("draft_notice", lang), S)

    ai_content = get_latest_ai_message(messages)
    ai_sections = parse_ai_sections(ai_content) if ai_content else {}

    # ── Section A: Technical Capability Assessment ────────────────────────────
    section_block(story, "A", t("ca_sA", lang), S)

    from reportlab.lib.styles import getSampleStyleSheet
    _base = getSampleStyleSheet()
    ai_eval_style = ParagraphStyle("CAEval", parent=_base["Normal"],
                                   fontSize=8.5, textColor=C_DARK, fontName="Helvetica-Oblique")

    diag_text = ai_sections.get("Diagnosis", "—")[:400]
    assessment_rows = [
        [
            Paragraph(t("eval_criterion", lang), S["label"]),
            Paragraph(t("ai_evaluation", lang), S["label"]),
            Paragraph(t("methods_decision", lang), S["label"]),
        ],
        [
            Paragraph(t("fault_description", lang) if "fault_description" in t.__doc__ or True else "Fault Description", S["body"]),
            safe_para(diag_text, ai_eval_style),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("risk_level", lang), S["body"]),
            safe_para(extract_risk_level(messages), ai_eval_style),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("repair_type", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("saesm_precedents", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("personnel_qual", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("special_tooling", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("tooling_avail", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("replacement_part", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("constructor_approval", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("estimated_time", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
        [
            Paragraph(t("estimated_cost", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
        ],
    ]
    assess_table = Table(assessment_rows, colWidths=["30%", "35%", "35%"])
    assess_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), C_MID),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("BACKGROUND", (0, 1), (0, -1), C_ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(assess_table)
    story.append(Spacer(1, 12))

    # ── Section B: Final Methods Decision ────────────────────────────────────
    section_block(story, "B", t("ca_sB", lang), S)

    options = [
        t("opt1", lang),
        t("opt2", lang),
        t("opt3", lang),
        t("opt4", lang),
    ]
    opt_rows = [
        [
            Paragraph(t("option", lang), S["label"]),
            Paragraph(t("description", lang), S["label"]),
            Paragraph(t("conditions", lang), S["label"]),
            Paragraph(t("decision", lang), S["label"]),
        ],
    ]
    for opt in options:
        opt_rows.append([
            safe_para(opt, S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("to_complete", lang), S["body"]),
            Paragraph(t("retained_rejected", lang), S["body"]),
        ])
    opt_table = Table(opt_rows, colWidths=["28%", "28%", "24%", "20%"])
    opt_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), C_MID),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(opt_table)
    story.append(Spacer(1, 14))

    signoff_block(story, [
        t("technician", lang),
        t("workscoper", lang),
        t("quality_assurance", lang),
    ], S)

    doc_footer(story, report_number, t("confidential", lang), S)
    doc.build(story)
    return buffer.getvalue()
