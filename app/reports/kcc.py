"""KCC — Keepership Concern Communication Draft PDF generator."""

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
    C_FAULT_BG,
    C_LIGHT_GRAY,
    C_MID,
    C_ROW_ALT,
    C_WARNING,
    C_WHITE,
    build_styles,
    doc_footer,
    draft_banner,
    extract_ata_from_messages,
    fmt_date,
    fmt_date_short,
    get_latest_ai_message,
    kv_table,
    parse_ai_sections,
    safe_para,
    section_block,
    signoff_block,
    xml_escape,
)
from app.sessions.models import Message, Session


def generate_kcc(
    session: Session,
    messages: list[Message],
    technician: User,
    lang: Lang = "en",
) -> bytes:
    """Generate a KCC (Keepership Concern Communication) Draft PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Tiyara — KCC Draft",
        author="Tiyara Aviation AI Platform",
    )

    S = build_styles()
    story: list = []
    report_number = f"KCC-{str(session.id).upper()[:8]}"

    # Header
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(t("kcc_title", lang), S["subtitle"]),
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
    story.append(Spacer(1, 4))

    # KCC confidential subtitle
    sub_table = Table(
        [[Paragraph(t("kcc_subtitle", lang), S["draft_notice"])]],
        colWidths=["100%"],
    )
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a0a00")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 6))
    draft_banner(story, t("draft_notice", lang), S)

    ai_content = get_latest_ai_message(messages)
    ai_sections = parse_ai_sections(ai_content) if ai_content else {}
    ata = extract_ata_from_messages(messages)

    # ── Section 1: Identification ─────────────────────────────────────────────
    section_block(story, "1", t("kcc_s01", lang), S)

    s1_rows = [
        (t("kcc_number", lang), t("to_complete", lang)),
        (t("issue_date", lang), fmt_date_short(session.created_at)),
        (t("issued_by", lang), xml_escape(technician.full_name)),
        (t("recipient", lang), t("kcc_recipient_val", lang)),
        (t("urgency", lang), t("kcc_urgency_val", lang)),
    ]
    story.append(kv_table(s1_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 2: Engine & Component Identification ─────────────────────────
    section_block(story, "2", t("kcc_s02", lang), S)

    s2_rows = [
        (t("engine_type", lang), xml_escape(session.engine_type)),
        (t("esn", lang), t("to_complete", lang)),
        (t("associated_aircraft", lang), t("to_complete", lang)),
        (t("ata_chapter", lang), ata),
        (t("component", lang), t("to_complete", lang)),
        (t("reference", lang), t("to_complete", lang)),
        (t("efh_finding", lang), t("to_complete", lang)),
        (t("efc_finding", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s2_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 3: Technical Finding Description ─────────────────────────────
    section_block(story, "3", t("kcc_s03", lang), S)

    diag_text = ai_sections.get("Diagnosis", xml_escape(session.problem_description))
    s3_rows = [
        (t("finding_nature", lang), xml_escape(session.problem_description)),
        (t("ai_diagnosis", lang), diag_text[:500]),
        (t("precise_location", lang), t("to_complete", lang)),
        (t("dimensions", lang), t("to_complete", lang)),
        (t("esm_refs_consulted", lang), t("to_complete", lang)),
        (t("adjacent_parts", lang), t("to_complete", lang)),
        (t("photos_kcc", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s3_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 4: History & Precedents ──────────────────────────────────────
    section_block(story, "4", t("kcc_s04", lang), S)

    history_text = ai_sections.get("History Patterns", "—")
    s4_rows = [
        (t("similar_cases", lang), history_text[:300] if history_text != "—" else t("to_complete", lang)),
        (t("observed_trend", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s4_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 5: Questions to Manufacturer ─────────────────────────────────
    section_block(story, "5", t("kcc_s05", lang), S)

    s5_rows = [
        (t("main_question", lang), t("kcc_q1", lang)),
        (t("secondary_question", lang), t("kcc_q2", lang)),
        (t("tertiary_question", lang), t("kcc_q3", lang)),
        (t("pending_decision", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s5_rows, S))
    story.append(Spacer(1, 14))

    signoff_block(story, [
        t("workscoper", lang),
        t("quality_assurance", lang),
    ], S)

    doc_footer(story, report_number, t("confidential", lang), S)
    doc.build(story)
    return buffer.getvalue()
