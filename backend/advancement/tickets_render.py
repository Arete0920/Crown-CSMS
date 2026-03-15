"""
Stage 3.3 – PDF ticket generation using reportlab.

Each ticket gets its own page with:
- Event name, date, venue
- Buyer name + email
- Section / Row / Seat label
- QR code equivalent text (qr_code string, rendered as human-readable for MVP;
  a real QR image can be added when qrcode/Pillow is available)
- Ticket UUID as barcode-style reference
"""
from __future__ import annotations

import base64
import io
import logging
import uuid

logger = logging.getLogger(__name__)


def make_ticket_pdf_bytes(*, ticket, seat) -> bytes:
    """
    Generate a single-page PDF for one ticket + seat assignment.

    Parameters
    ----------
    ticket : advancement.models_stage3.Ticket (or similar) - must have id, event, purchaser_name, purchaser_email
    seat :   advancement.models_stage3.Seat - must have section, row_label, seat_number, label

    Returns bytes of the PDF.
    """
    try:
        from reportlab.lib.pagesizes import A5
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        # Fallback: return a minimal PDF stub if reportlab is missing (should not happen)
        return _minimal_stub_pdf()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A5,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TicketTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "TicketSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#444444"),
        spaceAfter=4,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=13,
        fontName="Helvetica-Bold",
    )

    # Extract event info safely
    event_name = "Event"
    event_date = ""
    try:
        event_name = ticket.event.name if hasattr(ticket, "event") else str(getattr(ticket, "event_id", ""))
        if hasattr(ticket, "event") and hasattr(ticket.event, "date"):
            event_date = str(ticket.event.date or "")
    except Exception:
        logger.debug("ticket event metadata fallback used", exc_info=True)

    # Extract seat info
    section = getattr(seat, "section", "") or "General"
    row = getattr(seat, "row", "") or "-"
    num = getattr(seat, "number", "") or "-"
    seat_label = f"{section}-{row}-{num}"

    buyer_name = getattr(ticket, "purchaser_name", "Guest")
    buyer_email = getattr(ticket, "purchaser_email", "")
    ticket_id = str(getattr(ticket, "id", uuid.uuid4()))

    story = [
        Paragraph("🎟 YOUR TICKET", title_style),
        Paragraph(event_name, subtitle_style),
    ]

    if event_date:
        story.append(Paragraph(event_date, label_style))

    story.append(Spacer(1, 0.5 * cm))

    seat_table_data = [
        [Paragraph("SECTION", label_style), Paragraph("ROW", label_style), Paragraph("SEAT", label_style)],
        [Paragraph(section, value_style), Paragraph(row, value_style), Paragraph(seat_label, value_style)],
    ]
    seat_table = Table(seat_table_data, colWidths=[4 * cm, 3 * cm, 3 * cm])
    seat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTSIZE", (0, 1), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(seat_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("TICKET HOLDER", label_style))
    story.append(Paragraph(buyer_name, value_style))
    story.append(Paragraph(buyer_email, subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    # QR/barcode text block
    story.append(Paragraph("ADMISSION CODE", label_style))
    story.append(Paragraph(ticket_id, ParagraphStyle(
        "Mono", parent=styles["Normal"], fontName="Courier", fontSize=9,
        textColor=colors.HexColor("#333333"),
    )))

    doc.build(story)
    return buf.getvalue()


def to_b64(raw_bytes: bytes) -> str:
    """Encode bytes to base64 string for JSON storage."""
    return base64.b64encode(raw_bytes).decode("ascii")


def _minimal_stub_pdf() -> bytes:
    """Return a valid 1-byte-PDF stub when reportlab is unavailable."""
    return (
        b"%PDF-1.4\n1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj\n"
        b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox [0 0 200 200]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Size 4 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
