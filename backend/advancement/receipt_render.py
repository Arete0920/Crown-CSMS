"""
Stage 3.4 – Receipt PDF renderer.

Generates an A4 PDF receipt via reportlab.  Returns raw bytes (suitable for
base64-encoding into EmailOutbox.attachments_json).

Sponsor logos are listed as URLs in the PDF (fetching remote images in
server-side PDF generation is deliberately avoided for reliability; the frontend
and Wallet passes render them visually).
"""
from __future__ import annotations

import base64
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def to_b64(raw_bytes: bytes) -> str:
    """Base64-encode bytes for JSON storage."""
    return base64.b64encode(raw_bytes).decode("ascii")


def make_receipt_pdf_bytes(
    *,
    school_name: str,
    receipt_no: str,
    event_name: str,
    purchaser_name: str,
    purchaser_email: str,
    subtotal: str,
    donation: str,
    total: str,
    seat_labels: list[str] | None = None,
    sponsor_names: list[str] | None = None,
) -> bytes:
    """
    Render a branded receipt PDF and return raw bytes.

    Args:
        school_name      – e.g. "Lincoln Academy"
        receipt_no       – e.g. "R-<uuid>-<ts>"
        event_name       – e.g. "Spring Gala 2026"
        purchaser_name   – buyer full name
        purchaser_email  – buyer email
        subtotal         – formatted string, e.g. "50.00"
        donation         – formatted string, e.g. "10.00"
        total            – formatted string, e.g. "60.00"
        seat_labels      – list of seat strings, e.g. ["VIP-A-1", "VIP-A-2"]
        sponsor_names    – list of sponsor name strings

    Returns:
        bytes (PDF content)
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    margin_left = 2 * cm
    margin_top = height - 2 * cm
    y = margin_top

    # ── Header ──────────────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin_left, y, school_name)
    y -= 0.8 * cm

    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(margin_left, y, "Event Receipt")
    c.setFillColorRGB(0, 0, 0)
    y -= 0.5 * cm

    # divider
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(margin_left, y, width - margin_left, y)
    y -= 0.7 * cm

    # ── Receipt metadata ─────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Receipt Details")
    y -= 0.5 * cm

    c.setFont("Helvetica", 10)
    for label, value in [
        ("Receipt #", receipt_no),
        ("Event", event_name),
        ("Buyer", purchaser_name),
        ("Email", purchaser_email),
    ]:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin_left, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(margin_left + 3.5 * cm, y, value)
        y -= 0.45 * cm

    y -= 0.3 * cm
    c.line(margin_left, y, width - margin_left, y)
    y -= 0.7 * cm

    # ── Seats ────────────────────────────────────────────────────────────────
    if seat_labels:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_left, y, "Seats")
        y -= 0.5 * cm
        c.setFont("Helvetica", 10)
        for seat in seat_labels:
            c.drawString(margin_left + 0.5 * cm, y, f"• {seat}")
            y -= 0.4 * cm
        y -= 0.3 * cm
        c.line(margin_left, y, width - margin_left, y)
        y -= 0.7 * cm

    # ── Financial summary ────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Payment Summary")
    y -= 0.5 * cm

    right_col = width - margin_left
    for label, value in [
        ("Tickets subtotal", f"${subtotal}"),
        ("Donation", f"${donation}"),
    ]:
        c.setFont("Helvetica", 10)
        c.drawString(margin_left, y, label)
        c.drawRightString(right_col, y, value)
        y -= 0.45 * cm

    y -= 0.15 * cm
    c.line(margin_left, y, right_col, y)
    y -= 0.4 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Total Paid")
    c.drawRightString(right_col, y, f"${total}")
    y -= 0.7 * cm

    c.line(margin_left, y, width - margin_left, y)
    y -= 0.7 * cm

    # ── Sponsors ─────────────────────────────────────────────────────────────
    if sponsor_names:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_left, y, "Event Sponsors")
        y -= 0.5 * cm
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        for name in sponsor_names[:8]:
            c.drawString(margin_left + 0.5 * cm, y, f"• {name}")
            y -= 0.38 * cm
        c.setFillColorRGB(0, 0, 0)
        y -= 0.3 * cm

    # ── Footer ───────────────────────────────────────────────────────────────
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, 1.5 * cm, "Thank you for your support. This receipt is your record of payment.")
    c.setFillColorRGB(0, 0, 0)

    c.showPage()
    c.save()
    return buf.getvalue()
