"""Executive Diagnosis PDF export — deterministic memo from computed health payload."""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Executive palette (matches diagnostic UI)
NAVY = colors.HexColor("#0f172a")
AMBER = colors.HexColor("#9a3412")
AMBER_LIGHT = colors.HexColor("#fff7ed")
SLATE_700 = colors.HexColor("#334155")
SLATE_500 = colors.HexColor("#64748b")
SLATE_200 = colors.HexColor("#e2e8f0")
WHITE = colors.white
ROSE = colors.HexColor("#9f1239")
EMERALD = colors.HexColor("#065f46")


def _status_label(score: int | None) -> tuple[str, colors.Color]:
    if score is None:
        return "—", SLATE_500
    if score >= 85:
        return "Healthy", EMERALD
    if score >= 70:
        return "Moderate", colors.HexColor("#0369a1")
    if score >= 55:
        return "Pressure", colors.HexColor("#92400e")
    return "Critical", ROSE


def _safe(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inr(amount: int | float | None) -> str:
    if amount is None:
        return "—"
    return f"Rs {int(amount):,}"


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "diagnosis").strip().lower())
    return slug.strip("-") or "diagnosis"


def _color_hex(c: colors.Color) -> str:
    return "#" + c.hexval()[2:8]


def build_diagnostic_pdf(
    health: dict,
    org_name: str | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    """Render an executive diagnosis memo. Raises ValueError if insufficient evidence."""
    if not health.get("sufficient"):
        raise ValueError(
            health.get("message")
            or "Not enough evidence to export a diagnosis. Complete the Revenue Audit first."
        )

    generated_at = generated_at or datetime.now(timezone.utc)
    org = org_name or "Your business"
    pc = health["primary_constraint"]
    rec = health.get("recommendation") or {}
    epi = health.get("epistemic_confidence") or health.get("confidence_breakdown") or {}
    epi_overall = int((epi.get("overall") or health.get("confidence") or 0) * 100)
    score = health["health_score"]
    status, status_color = _status_label(score)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"AFK Executive Diagnosis — {org}",
        author="AFK Revenue Intelligence",
    )

    base = getSampleStyleSheet()
    styles = {
        "hero_kicker": ParagraphStyle(
            "hero_kicker", parent=base["Normal"],
            fontSize=8, leading=10, textColor=colors.HexColor("#fbbf24"),
            fontName="Helvetica-Bold", spaceAfter=4, letterSpacing=1.2,
        ),
        "hero_title": ParagraphStyle(
            "hero_title", parent=base["Heading1"],
            fontSize=20, leading=24, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=6,
        ),
        "hero_sub": ParagraphStyle(
            "hero_sub", parent=base["Normal"],
            fontSize=10, leading=14, textColor=colors.HexColor("#cbd5e1"),
        ),
        "section": ParagraphStyle(
            "section", parent=base["Normal"],
            fontSize=8, leading=10, textColor=AMBER, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=6, letterSpacing=1.0,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, leading=14, textColor=SLATE_700,
        ),
        "body_sm": ParagraphStyle(
            "body_sm", parent=base["Normal"],
            fontSize=9, leading=12, textColor=SLATE_500,
        ),
        "score_num": ParagraphStyle(
            "score_num", parent=base["Heading1"],
            fontSize=36, leading=40, textColor=SLATE_700, fontName="Helvetica-Bold",
        ),
        "status": ParagraphStyle(
            "status", parent=base["Normal"],
            fontSize=14, leading=16, fontName="Helvetica-Bold",
        ),
        "finding": ParagraphStyle(
            "finding", parent=base["Normal"],
            fontSize=9, leading=13, textColor=SLATE_700, leftIndent=8,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontSize=7.5, leading=10, textColor=SLATE_500,
        ),
    }

    story: list = []

    # Header band
    header_tbl = Table([
        [Paragraph("EXECUTIVE DIAGNOSIS", styles["hero_kicker"])],
        [Paragraph("Revenue Health", styles["hero_title"])],
        [Paragraph(
            f"{_safe(health.get('risk_level'))} · primary constraint {_safe(pc.get('label'))}",
            styles["hero_sub"],
        )],
        [Paragraph(
            f"{_safe(org)} · generated {generated_at.strftime('%d %b %Y')}",
            styles["hero_sub"],
        )],
    ], colWidths=[16 * cm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.45 * cm))

    # Score row
    score_tbl = Table(
        [[
            Paragraph(f"{score}<font size='14' color='#64748b'>/100</font>", styles["score_num"]),
            Paragraph(
                f'<font color="{_color_hex(status_color)}">{status}</font>',
                styles["status"],
            ),
            Paragraph(
                f"<b>Epistemic confidence</b><br/>{epi_overall}%",
                styles["body"],
            ),
        ]],
        colWidths=[5 * cm, 4 * cm, 7 * cm],
    )
    score_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), AMBER_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 0.35 * cm))

    # Primary constraint
    story.append(Paragraph("PRIMARY CONSTRAINT", styles["section"]))
    story.append(Paragraph(
        f"<b>{_safe(pc.get('label'))}</b> — dimension score {pc.get('score')}/100",
        styles["body"],
    ))
    priority = pc.get("priority") or {}
    if priority:
        story.append(Paragraph(
            f"Impact priority {priority.get('priority_score', '—')} "
            f"(severity {priority.get('severity_index', '—')} × "
            f"exposure {priority.get('effective_revenue_exposure', priority.get('revenue_exposure', '—'))} × "
            f"fixability {priority.get('fixability', '—')}).",
            styles["body_sm"],
        ))

    # Findings
    findings = (pc.get("findings") or [])[:4]
    if findings:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph("WHY AFK BELIEVES THIS", styles["section"]))
        for f in findings:
            rule = f.get("rule_id")
            prefix = f"<b>{_safe(rule)}</b> — " if rule else "• "
            story.append(Paragraph(prefix + _safe(f.get("reasoning")), styles["finding"]))
            ev_bits = []
            for e in (f.get("evidence") or [])[:3]:
                ev_bits.append(f"{_safe(e.get('question'))}: {_safe(e.get('answer'))}")
            if ev_bits:
                story.append(Paragraph("Evidence: " + "; ".join(ev_bits), styles["body_sm"]))

    # Recommendation
    if rec.get("action"):
        story.append(Paragraph("RECOMMENDED NEXT ACTION", styles["section"]))
        story.append(Paragraph(f"<b>{_safe(rec.get('constraint'))}</b>", styles["body"]))
        story.append(Paragraph(_safe(rec.get("action")), styles["body"]))
        story.append(Spacer(1, 0.1 * cm))
        rec_rows = [
            ["Why", _safe(rec.get("why"))],
            ["Confidence", f"{rec.get('confidence_pct', '—')}% — {_safe(rec.get('confidence_basis'))}"],
            ["Expected impact", _safe(rec.get("expected_impact"))],
            ["Assumptions", _safe(rec.get("assumptions"))],
        ]
        rec_tbl = Table(rec_rows, colWidths=[3.2 * cm, 12.8 * cm])
        rec_tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), AMBER),
            ("TEXTCOLOR", (1, 0), (1, -1), SLATE_700),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(rec_tbl)

    # Revenue opportunity
    opp = health.get("revenue_opportunity")
    if opp:
        story.append(Paragraph("REVENUE OPPORTUNITY (DIRECTIONAL)", styles["section"]))
        story.append(Paragraph(
            f"<b>{_inr(opp.get('amount'))}</b> per year — {_safe(opp.get('basis'))}",
            styles["body_sm"],
        ))

    # Hypothesis verdict
    hv = health.get("hypothesis_verdict")
    if hv:
        story.append(Paragraph("FOUNDER HYPOTHESIS VS MEASURED CONSTRAINT", styles["section"]))
        story.append(Paragraph(f'You said: "{_safe(hv.get("founder_hypothesis"))}"', styles["body_sm"]))
        story.append(Paragraph(
            f"Verdict: <b>{_safe(hv.get('verdict'))}</b> — {_safe(hv.get('explanation'))}",
            styles["body_sm"],
        ))

    # Contradictions
    contradictions = (health.get("contradictions") or [])[:2]
    if contradictions:
        story.append(Paragraph("BELIEF VS UPLOADED EVIDENCE", styles["section"]))
        for c in contradictions:
            story.append(Paragraph(
                f'You said "{_safe(c.get("belief", {}).get("answer"))}" · '
                f'Evidence shows {_safe(c.get("evidence", {}).get("value"))} '
                f"({_safe(c.get('evidence', {}).get('basis'))})",
                styles["body_sm"],
            ))
            story.append(Paragraph(_safe(c.get("explanation")), styles["finding"]))

    # Dimension table
    story.append(Paragraph("ALL DIMENSIONS", styles["section"]))
    dim_rows = [["Dimension", "Score", "Confidence"]]
    for d in health.get("dimensions") or []:
        dim_rows.append([
            _safe(d.get("label")),
            str(d.get("score")) if d.get("score") is not None else "—",
            f"{int((d.get('confidence') or 0) * 100)}%",
        ])
    dim_tbl = Table(dim_rows, colWidths=[9 * cm, 3.5 * cm, 3.5 * cm], repeatRows=1)
    dim_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.25, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(dim_tbl)

    # Evidence stats
    stats = health.get("evidence_stats") or {}
    if stats:
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph(
            f"Evidence basis: {stats.get('total_points', 0)} points · "
            f"{stats.get('audit_answers', 0)} audit answers · "
            f"{stats.get('evidence_citations', 0)} citations · "
            f"{stats.get('dimensions_analyzed', 0)}/{stats.get('dimensions_total', 6)} dimensions analyzed",
            styles["body_sm"],
        ))

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE_200, spaceBefore=6, spaceAfter=8))

    # Footer / provenance
    prov = health.get("science_provenance") or {}
    prov_bits = [
        prov.get("priority_model_id"),
        prov.get("confidence_model_id"),
        prov.get("engine_version"),
        prov.get("rule_pack"),
    ]
    prov_line = " · ".join(x for x in prov_bits if x)
    if prov_line:
        story.append(Paragraph(f"Science provenance: {_safe(prov_line)}", styles["footer"]))

    story.append(Paragraph(_safe(health.get("method_note")), styles["footer"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "<b>Honest limits:</b> This memo is computed from your audit answers and uploaded evidence. "
        "Scores are rule-based and deterministic — not AI-generated. Revenue opportunity figures are "
        "directional heuristics, not predictions. Outcome efficacy is not claimed until observed in "
        "real businesses (AFK validation corpus N&lt;10).",
        styles["footer"],
    ))
    story.append(Paragraph(
        "AFK Revenue Intelligence · afk.agency · Confidential — prepared for the founding team only.",
        styles["footer"],
    ))

    doc.build(story)
    return buf.getvalue()


def export_filename(org_name: str | None, generated_at: datetime | None = None) -> str:
    ts = (generated_at or datetime.now(timezone.utc)).strftime("%Y%m%d")
    return f"afk-executive-diagnosis-{_slug(org_name)}-{ts}.pdf"