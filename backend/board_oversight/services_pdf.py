"""
board_oversight/services_pdf.py

Board packet PDF generator using reportlab.
Falls back gracefully if reportlab is not installed (returns None).
"""
from io import BytesIO
from decimal import Decimal


def _reportlab_available():
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def generate_board_packet(school_id=None) -> BytesIO | None:
    """
    Generate a PDF board packet and return a BytesIO buffer.
    Returns None if reportlab is not installed.

    school_id: UUID or None — if provided, data is tenant-scoped.
    """
    if not _reportlab_available():
        return None

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # ── Title ──────────────────────────────────────────────────────────────
    elements.append(Paragraph("Crown Board Executive Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # ── Revenue ────────────────────────────────────────────────────────────
    try:
        from ledger.models import Payment
        qs = Payment.objects.filter(status="success")
        if school_id:
            qs = qs.filter(school_id=school_id)
        revenue = sum(p.amount for p in qs) or Decimal("0.00")
    except Exception:
        revenue = Decimal("0.00")

    # ── Applications ───────────────────────────────────────────────────────
    try:
        from applications.models import Application
        app_qs = Application.objects.all()
        if school_id:
            app_qs = app_qs.filter(school_id=school_id)
        applications = app_qs.count()
    except Exception:
        applications = 0

    # ── Discipline incidents ────────────────────────────────────────────────
    try:
        from discipline.models import DisciplineIncident
        di_qs = DisciplineIncident.objects.all()
        if school_id:
            di_qs = di_qs.filter(school_id=school_id)
        incidents = di_qs.count()
    except Exception:
        incidents = 0

    # ── Strategic Initiatives ─────────────────────────────────────────────
    try:
        from board_oversight.models_governance import StrategicInitiative
        si_qs = StrategicInitiative.objects.all()
        if school_id:
            si_qs = si_qs.filter(school_id=school_id)
        total_si = si_qs.count()
        complete_si = si_qs.filter(status="complete").count()
    except Exception:
        total_si, complete_si = 0, 0

    # ── Table ──────────────────────────────────────────────────────────────
    data = [
        ["Metric", "Value"],
        ["Total Revenue (Successful Payments)", f"${revenue:,.2f}"],
        ["Applications", str(applications)],
        ["Discipline Incidents", str(incidents)],
        ["Strategic Initiatives (Complete / Total)", f"{complete_si} / {total_si}"],
    ]

    table = Table(data, colWidths=[300, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
