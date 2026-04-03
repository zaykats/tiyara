"""Service Order (Ordre de Service) PDF generator."""

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
    extract_steps,
    fmt_date,
    fmt_date_short,
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


def generate_service_order(
    session: Session,
    messages: list[Message],
    technician: User,
    lang: Lang = "en",
) -> bytes:
    """Generate a Service Order (Ordre de Service) PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Tiyara — Service Order",
        author="Tiyara Aviation AI Platform",
    )

    S = build_styles()
    story: list = []
    report_number = f"OS-{str(session.id).upper()[:8]}"

    # Header
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(t("so_title", lang), S["subtitle"]),
            "",
            Paragraph(fmt_date(session.created_at), S["header_right_sm"]),
        ],
        [
            Paragraph(t("so_subtitle", lang), S["subtitle"]),
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

    # ── Section 1: General Information ───────────────────────────────────────
    section_block(story, "1", t("so_s01", lang), S)

    s1_rows = [
        (t("so_number", lang), report_number,
         t("date_opened", lang), fmt_date_short(session.created_at)),
        (t("order_type", lang), t("order_type_val", lang),
         t("engine_type", lang), xml_escape(session.engine_type)),
        (t("engine_sn", lang), t("to_complete", lang),
         t("ata_chapter", lang), t("to_complete", lang)),
        (t("technician", lang), xml_escape(technician.full_name),
         t("workscoper", lang), t("to_complete", lang)),
        (t("created_by_ai", lang), fmt_date_short(session.created_at),
         t("validated_by", lang), t("to_complete", lang)),
        (t("validation_date", lang), t("to_complete", lang),
         t("priority", lang), t("to_complete", lang)),
    ]
    story.append(kv4_table(s1_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 2: Technical Work Description ─────────────────────────────────
    section_block(story, "2", t("so_s02", lang), S)

    diag_text = ai_sections.get("Diagnosis", xml_escape(session.problem_description))
    s2_rows = [
        (t("work_object", lang), xml_escape(session.problem_description)),
        (t("ai_diagnosis", lang), diag_text[:500]),
        (t("tech_references", lang), t("to_complete", lang)),
        (t("applicable_standard", lang), t("to_complete", lang)),
        (t("applicable_precedent", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s2_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 3: Operations Sequence ────────────────────────────────────────
    section_block(story, "3", t("so_s03", lang), S)

    procedure_text = ai_sections.get("Procedure", "")
    steps = extract_steps(procedure_text) if procedure_text else []

    if steps:
        step_header = [
            Paragraph(t("step_col", lang), S["label"]),
            Paragraph(t("detail_col", lang), S["label"]),
            Paragraph(t("amm_ref_col", lang), S["label"]),
            Paragraph(t("duration_col", lang), S["label"]),
        ]
        step_rows = [step_header]
        for s in steps:
            detail = xml_escape(s["title"]) + "<br/>" + xml_escape(s["instruction"])
            if s.get("details"):
                detail += "<br/>" + "<br/>".join(f"• {xml_escape(d)}" for d in s["details"])
            step_rows.append([
                Paragraph(s["number"], S["body"]),
                Paragraph(detail, S["body"]),
                Paragraph(t("to_complete", lang), S["body"]),
                Paragraph(t("to_complete", lang), S["body"]),
            ])
        step_table = Table(step_rows, colWidths=["8%", "60%", "18%", "14%"])
        step_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
            ("BACKGROUND", (0, 0), (-1, 0), C_MID),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
        ]))
        story.append(step_table)
    else:
        story.append(safe_para(t("no_steps_so", lang), S["body"]))
    story.append(Spacer(1, 10))

    # ── Section 4: Parts & Tooling ─────────────────────────────────────────────
    section_block(story, "4", t("so_s04", lang), S)

    parts_text = ai_sections.get("Parts & Tooling", "")
    s4_rows = [
        (t("main_part", lang), t("to_complete", lang)),
        (t("consumables", lang), t("to_complete", lang)),
        (t("special_tool_1", lang), t("to_complete", lang)),
        (t("special_tool_2", lang), t("to_complete", lang)),
        (t("standard_tooling", lang), t("to_complete", lang)),
        (t("documentation_field", lang), t("to_complete", lang)),
    ]
    if parts_text:
        s4_rows.insert(0, (t("parts_tooling", lang), parts_text[:300]))
    story.append(kv_table(s4_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 5: Required Qualifications ────────────────────────────────────
    section_block(story, "5", t("so_s05", lang), S)

    s5_rows = [
        (t("operator_qual", lang), t("to_complete", lang)),
        (t("internal_auth", lang), t("to_complete", lang)),
        (t("inspection_req", lang), t("to_complete", lang)),
        (t("rts_approval", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s5_rows, S))
    story.append(Spacer(1, 14))

    signoff_block(story, [
        t("technician", lang),
        t("workscoper", lang),
        t("quality_assurance", lang),
    ], S)

    doc_footer(story, report_number, t("confidential", lang), S)
    doc.build(story)
    return buffer.getvalue()
