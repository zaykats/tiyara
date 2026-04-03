"""AI Analysis & Recommendations PDF generator."""

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
from app.documents.models import CaseHistory
from app.reports.translations import Lang, t
from app.reports.utils import (
    C_ACCENT,
    C_BORDER,
    C_DARK,
    C_FAULT_BG,
    C_LIGHT_GRAY,
    C_RES_BG,
    C_ROW_ALT,
    C_WHITE,
    build_styles,
    doc_footer,
    draft_banner,
    extract_risk_level,
    extract_steps,
    fmt_date,
    get_latest_ai_message,
    kv_table,
    parse_ai_sections,
    safe_para,
    section_block,
    signoff_block,
    xml_escape,
)
from app.sessions.models import Message, Session


def generate_ai_analysis(
    session: Session,
    messages: list[Message],
    technician: User,
    case_history: "CaseHistory | None" = None,
    lang: Lang = "en",
) -> bytes:
    """Generate an AI Analysis & Recommendations PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Tiyara — AI Analysis Report",
        author="Tiyara Aviation AI Platform",
    )

    S = build_styles()
    story: list = []
    report_number = f"AA-{str(session.id).upper()[:8]}"

    # Header
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(t("aa_title", lang), S["subtitle"]),
            "",
            Paragraph(fmt_date(session.created_at), S["header_right_sm"]),
        ],
    ]
    ht = Table(header_data, colWidths=["55%", "5%", "40%"])
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(ht)
    story.append(Spacer(1, 6))
    draft_banner(story, t("draft_notice", lang), S)

    # Context info strip
    ctx_rows = [
        (t("engine_type", lang), xml_escape(session.engine_type),
         t("technician", lang), xml_escape(technician.full_name)),
        (t("fault_reported", lang), xml_escape(session.problem_description),
         t("risk_level", lang), extract_risk_level(messages)),
    ]

    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import getSampleStyleSheet
    _base = getSampleStyleSheet()
    ctx_label = ParagraphStyle("AACtxL", parent=_base["Normal"],
                               fontSize=7.5, textColor=C_LIGHT_GRAY, fontName="Helvetica")
    ctx_body = ParagraphStyle("AACtxB", parent=_base["Normal"],
                              fontSize=8.5, textColor=C_DARK, fontName="Helvetica")

    ctx_data = [
        [
            Paragraph(r[0], ctx_label), safe_para(r[1], ctx_body),
            Paragraph(r[2], ctx_label), safe_para(r[3], ctx_body),
        ]
        for r in ctx_rows
    ]
    ctx_table = Table(ctx_data, colWidths=["18%", "32%", "18%", "32%"])
    ctx_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), C_ROW_ALT),
        ("BACKGROUND", (2, 0), (2, -1), C_ROW_ALT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(ctx_table)
    story.append(Spacer(1, 10))

    # Parse AI sections from latest assistant message
    ai_content = get_latest_ai_message(messages)
    ai_sections: dict[str, str] = {}
    if ai_content:
        ai_sections = parse_ai_sections(ai_content)

    # ── Section A: ESM Search Result ─────────────────────────────────────────
    section_block(story, "A", t("aa_sA", lang), S)

    esm_rows = [
        (t("nearest_esm", lang), t("to_complete", lang)),
        (t("applicable_insp", lang), t("to_complete", lang)),
        (t("tolerance_limit", lang), t("to_complete", lang)),
        (t("esm_status", lang), t("to_complete", lang)),
        (t("ai_result", lang), xml_escape(ai_sections.get("Diagnosis", t("to_complete", lang))[:300])),
        (t("confidence", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(esm_rows, S))
    story.append(Spacer(1, 10))

    # ── Section B: Similar Historical Cases ──────────────────────────────────
    section_block(story, "B", t("aa_sB", lang), S)

    history_text = ai_sections.get("History Patterns", "")
    if history_text:
        hist_table = Table(
            [[safe_para(history_text, S["body"])]],
            colWidths=["100%"],
        )
        hist_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.4, C_BORDER),
            ("BACKGROUND", (0, 0), (-1, -1), C_RES_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(hist_table)
    else:
        story.append(safe_para(t("no_history", lang), S["body"]))
    story.append(Spacer(1, 10))

    # ── Section C: AI Recommendation — Decision Flow ─────────────────────────
    section_block(story, "C", t("aa_sC", lang), S)

    # Procedure steps
    procedure_text = ai_sections.get("Procedure", "")
    steps = extract_steps(procedure_text) if procedure_text else []

    if steps:
        step_header = [
            Paragraph(t("step_col", lang), S["label"]),
            Paragraph(t("detail_col", lang), S["label"]),
            Paragraph(t("amm_ref_col", lang), S["label"]),
        ]
        step_rows = [step_header]
        for s in steps:
            detail = xml_escape(s["title"]) + " — " + xml_escape(s["instruction"])
            step_rows.append([
                Paragraph(s["number"], S["body"]),
                safe_para(detail, S["body"]),
                Paragraph(t("to_complete", lang), S["body"]),
            ])
        step_table = Table(step_rows, colWidths=["8%", "72%", "20%"])
        step_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
            ("BACKGROUND", (0, 0), (-1, 0), C_ROW_ALT),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(step_table)
    else:
        story.append(safe_para(t("no_analysis", lang), S["body"]))

    story.append(Spacer(1, 10))

    # Parts & Tooling
    parts_text = ai_sections.get("Parts & Tooling", "")
    if parts_text:
        section_block(story, " ", t("parts_tooling", lang), S)
        story.append(safe_para(parts_text, S["body"]))
        story.append(Spacer(1, 6))

    # Follow-up
    followup_text = ai_sections.get("Follow-up", "")
    if followup_text:
        section_block(story, " ", t("follow_up", lang), S)
        story.append(safe_para(followup_text, S["body"]))
        story.append(Spacer(1, 10))

    signoff_block(story, [
        t("technician", lang),
        t("engineer_supervisor", lang) if lang == "en" else t("eng_supervisor", lang),
    ], S)

    doc_footer(story, report_number, t("confidential", lang), S)
    doc.build(story)
    return buffer.getvalue()
