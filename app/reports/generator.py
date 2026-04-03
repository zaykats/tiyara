"""PDF maintenance report generator (bilingual EN/FR).

Produces a professional MRO-style diagnostic report.
Section 04 contains the step-by-step operations sequence extracted
from the AI conversation's ## Procedure section.
"""

import io
import json
from datetime import datetime, timezone
from typing import Optional

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
    C_MID,
    C_RES_BG,
    C_ROW_ALT,
    C_SUCCESS,
    C_WARNING,
    C_WHITE,
    build_styles,
    doc_footer,
    extract_steps,
    fmt_date,
    get_latest_ai_message,
    kv4_table,
    parse_ai_sections,
    safe_para,
    section_block,
    signoff_block,
    xml_escape,
)
from app.sessions.models import Message, Session


def generate_session_report(
    session: Session,
    messages: list[Message],
    technician: User,
    case_history: Optional[CaseHistory] = None,
    lang: Lang = "en",
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

    S = build_styles()
    base_styles = S

    # Build extra inline styles that depend on colours
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet
    _base = getSampleStyleSheet()

    status_color = C_SUCCESS if session.status == "resolved" else C_WARNING
    wo_status_style = ParagraphStyle(
        "TWOStatus", parent=_base["Normal"], fontSize=9,
        textColor=status_color, fontName="Helvetica-Bold",
    )
    sb_right_style = ParagraphStyle(
        "TSBRight", parent=_base["Normal"], fontSize=8,
        textColor=C_WHITE, fontName="Helvetica", alignment=TA_RIGHT,
    )
    status_bar_colored = ParagraphStyle(
        "TStatusColored", parent=_base["Normal"],
        fontSize=8, textColor=status_color, fontName="Helvetica-Bold",
    )

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
                f"{t('report_number', lang)}<br/><b>{report_number}</b>",
                S["header_right"],
            ),
        ],
        [
            Paragraph(t("diag_report_title", lang), S["subtitle"]),
            "",
            Paragraph(fmt_date(session.created_at), S["header_right_sm"]),
        ],
    ]
    header_table = Table(header_data, colWidths=["55%", "5%", "40%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(header_table)

    # Status bar
    bar_data = [[
        Paragraph(f"{t('status', lang)}: {session.status.upper()}", status_bar_colored),
        Paragraph(f"{t('engine_type', lang)}: {xml_escape(session.engine_type)}", S["status_bar"]),
        Paragraph(
            f"{t('technician', lang)}: {xml_escape(technician.full_name.upper())}",
            sb_right_style,
        ),
    ]]
    bar_table = Table(bar_data, colWidths=["33%", "34%", "33%"])
    bar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(bar_table)
    story.append(Spacer(1, 10))

    sec = 0

    # ═══════════════════════════════════════════════════════════════════════════
    # 01 — WORK ORDER INFORMATION
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    section_block(story, f"{sec:02d}", t("wo_info", lang), S)

    wo_rows = [
        (t("report_number", lang), report_number,
         t("session_id", lang), str(session.id)),
        (t("date_opened", lang), fmt_date(session.created_at),
         t("date_updated", lang), fmt_date(session.updated_at)),
        (t("engine_type", lang), session.engine_type,
         t("status", lang), session.status.upper()),
    ]
    # Build the table manually to colour the status cell
    wo_data = [
        [
            Paragraph(r[0], S["label"]), safe_para(r[1], S["body"]),
            Paragraph(r[2], S["label"]), safe_para(r[3], S["body"]),
        ]
        for r in wo_rows[:2]
    ]
    wo_data.append([
        Paragraph(wo_rows[2][0], S["label"]), safe_para(wo_rows[2][1], S["body"]),
        Paragraph(wo_rows[2][2], S["label"]),
        Paragraph(wo_rows[2][3], wo_status_style),
    ])
    wo_table = Table(wo_data, colWidths=["18%", "32%", "18%", "32%"])
    wo_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), C_ROW_ALT),
        ("BACKGROUND", (2, 0), (2, -1), C_ROW_ALT),
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
    section_block(story, f"{sec:02d}", t("fault_reported", lang), S)

    fault_table = Table(
        [[safe_para(session.problem_description, S["body"])]],
        colWidths=["100%"],
    )
    fault_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), C_FAULT_BG),
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
    section_block(story, f"{sec:02d}", t("personnel", lang), S)

    pers_rows = [
        (t("full_name", lang), technician.full_name,
         t("role", lang), technician.role.title()),
        (t("company", lang), technician.company,
         t("email", lang), technician.email),
    ]
    story.append(kv4_table(pers_rows, S))
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 04 — OPERATIONS SEQUENCE (extracted from AI ## Procedure section)
    # ═══════════════════════════════════════════════════════════════════════════
    sec += 1
    section_block(story, f"{sec:02d}", t("ops_sequence", lang), S)

    ai_content = get_latest_ai_message(messages)
    procedure_steps: list[dict] = []
    if ai_content:
        sections_map = parse_ai_sections(ai_content)
        procedure_text = sections_map.get("Procedure", "")
        if procedure_text:
            procedure_steps = extract_steps(procedure_text)

    if procedure_steps:
        for step in procedure_steps:
            instruction_text = xml_escape(step["instruction"])
            if step.get("details"):
                detail_lines = "<br/>".join(f"• {xml_escape(d)}" for d in step["details"])
                instruction_text += "<br/>" + detail_lines

            step_data = [
                [
                    Paragraph(step["number"], S["step_num"]),
                    Paragraph(xml_escape(step["title"]), S["step_title"]),
                ],
                [
                    "",
                    Paragraph(instruction_text, S["step_body"]),
                ],
            ]
            step_table = Table(step_data, colWidths=["8%", "92%"])
            step_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), C_ACCENT),
                ("SPAN", (0, 0), (0, 1)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_BORDER),
            ]))
            story.append(step_table)
            story.append(Spacer(1, 3))
    else:
        story.append(safe_para(t("no_procedure", lang), S["body"]))

    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # 0N — AI RESOLUTION SUMMARY  (only if session resolved)
    # ═══════════════════════════════════════════════════════════════════════════
    if case_history:
        sec += 1
        section_block(story, f"{sec:02d}", t("ai_resolution_summary", lang), S)
        try:
            res_sum = (
                json.loads(case_history.resolution_summary)
                if isinstance(case_history.resolution_summary, str)
                else case_history.resolution_summary
            )
        except Exception:
            res_sum = {"raw": str(case_history.resolution_summary)}

        res_rows = []
        for key, label_key in [
            ("fault_description", "fault_description"),
            ("root_cause", "root_cause"),
            ("outcome", "outcome"),
            ("ata_chapter", "ata_chapter"),
        ]:
            if res_sum.get(key):
                res_rows.append([
                    Paragraph(t(label_key, lang), S["label"]),
                    safe_para(str(res_sum[key]), S["body"]),
                ])

        if res_sum.get("steps_applied"):
            steps = res_sum["steps_applied"]
            if isinstance(steps, list):
                steps_text = "<br/>".join(
                    f"{i + 1}.  {xml_escape(str(s))}" for i, s in enumerate(steps)
                )
            else:
                steps_text = xml_escape(str(steps))
            res_rows.append([
                Paragraph(t("steps_applied", lang), S["label"]),
                Paragraph(steps_text, S["mono"]),
            ])

        if res_sum.get("raw"):
            res_rows.append([
                Paragraph(t("summary", lang), S["label"]),
                safe_para(res_sum["raw"], S["body"]),
            ])

        if res_rows:
            res_table = Table(res_rows, colWidths=["25%", "75%"])
            res_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("BACKGROUND", (0, 0), (0, -1), C_RES_BG),
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
    section_block(story, f"{sec:02d}", t("transcript", lang), S)

    if messages:
        tech_label = t("technician", lang).upper()
        ai_label = "TIYARA AI"
        for msg in messages:
            is_user = msg.role == "user"
            role_label = tech_label if is_user else ai_label
            header_bg = C_MID if is_user else C_ACCENT

            header_para = Paragraph(
                f"  {role_label}  —  {fmt_date(msg.created_at)}",
                S["role_user"] if is_user else S["role_ai"],
            )
            content_para = safe_para(msg.content, S["mono"])

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
                ("BOX", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(msg_table)
            story.append(Spacer(1, 4))
    else:
        story.append(safe_para(t("no_messages", lang), S["body"]))

    story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════════════════════════
    # SIGN-OFF & CERTIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    from reportlab.platypus import HRFlowable
    story.append(Paragraph(t("signoff_certification", lang), S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_ACCENT))
    story.append(Spacer(1, 8))
    story.append(Paragraph(t("signoff_notice", lang), S["signoff_note"]))

    signoff_block(story, [
        t("certifying_technician", lang),
        t("engineer_supervisor", lang),
        t("quality_assurance", lang),
    ], S)

    # Footer
    doc_footer(story, report_number, t("confidential", lang), S)

    doc.build(story)
    return buffer.getvalue()
