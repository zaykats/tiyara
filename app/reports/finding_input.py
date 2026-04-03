"""Finding Input Form (Fiche de Saisie) PDF generator."""

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
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
from app.reports.translations import Lang, t
from app.reports.utils import (
    C_ACCENT,
    C_BORDER,
    C_DARK,
    C_FAULT_BG,
    C_LIGHT_GRAY,
    C_MID,
    C_ROW_ALT,
    C_WHITE,
    build_styles,
    doc_footer,
    draft_banner,
    fmt_date,
    kv4_table,
    kv_table,
    safe_para,
    section_block,
    signoff_block,
    xml_escape,
)
from app.sessions.models import Session


def generate_finding_input(
    session: Session,
    technician: User,
    lang: Lang = "en",
) -> bytes:
    """Generate a Finding Input Form PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Tiyara — Finding Input Form",
        author="Tiyara Aviation AI Platform",
    )

    S = build_styles()
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet
    _base = getSampleStyleSheet()
    sb_right = ParagraphStyle(
        "FISBRight", parent=_base["Normal"], fontSize=8,
        textColor=C_WHITE, fontName="Helvetica", alignment=TA_RIGHT,
    )

    story: list = []
    report_number = f"FI-{str(session.id).upper()[:8]}"
    now_str = fmt_date(session.created_at)

    # Header
    header_data = [
        [
            Paragraph("TIYARA", S["title"]),
            "",
            Paragraph(f"Ref: <b>{report_number}</b>", S["header_right"]),
        ],
        [
            Paragraph(t("fi_title", lang), S["subtitle"]),
            "",
            Paragraph(now_str, S["header_right_sm"]),
        ],
        [
            Paragraph(t("fi_subtitle", lang), S["subtitle"]),
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
    story.append(Spacer(1, 8))

    # ── Section 1: Engine & Context ──────────────────────────────────────────
    section_block(story, "1", t("fi_s01", lang), S)

    s1_rows = [
        (t("wo_number", lang), t("to_complete", lang),
         t("date_opened", lang), fmt_date(session.created_at)),
        (t("engine_type", lang), xml_escape(session.engine_type),
         t("engine_sn", lang), t("to_complete", lang)),
        (t("aircraft_sn", lang), t("to_complete", lang),
         t("maintenance_phase", lang), t("to_complete", lang)),
        (t("efh", lang), t("to_complete", lang),
         t("efc", lang), t("to_complete", lang)),
        (t("shop_zone", lang), t("to_complete", lang),
         t("technician", lang), xml_escape(technician.full_name)),
        (t("workscoper", lang), t("to_complete", lang),
         t("company", lang), xml_escape(technician.company)),
    ]
    story.append(kv4_table(s1_rows, S))
    story.append(Spacer(1, 10))

    # ── Section 2: Finding Description ──────────────────────────────────────
    section_block(story, "2", t("fi_s02", lang), S)

    s2_rows = [
        (t("discovery_date", lang), t("to_complete", lang)),
        (t("ata_chapter", lang), t("to_complete", lang)),
        (t("ata_zone", lang), t("to_complete", lang)),
        (t("component", lang), t("to_complete", lang)),
        (t("reference", lang), t("to_complete", lang)),
        (t("free_desc", lang), xml_escape(session.problem_description)),
        (t("precise_location", lang), t("to_complete", lang)),
        (t("dimensions", lang), t("to_complete", lang)),
        (t("discovery_conditions", lang), t("to_complete", lang)),
        (t("esm_covered", lang), t("to_complete", lang)),
        (t("photos", lang), t("to_complete", lang)),
        (t("estimated_urgency", lang), t("to_complete", lang)),
    ]
    story.append(kv_table(s2_rows, S))
    story.append(Spacer(1, 14))

    # Sign-off
    signoff_block(story, [
        t("technician", lang),
        t("workscoper", lang),
    ], S)

    doc_footer(story, report_number, t("confidential", lang), S)
    doc.build(story)
    return buffer.getvalue()
