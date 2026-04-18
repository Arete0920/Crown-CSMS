from io import BytesIO
from datetime import datetime, timezone

from django.http import HttpResponse

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    canvas = None
    letter = (612, 792)


def _fallback_pdf_bytes(title: str, lines: list[str]) -> bytes:
    content = [title, f"Generated: {datetime.now(timezone.utc).isoformat()}", *lines]
    text = "\n".join(str(line) for line in content)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<<>>endobj\n"
        b"2 0 obj<< /Length 3 0 R >>stream\n" + text.encode("utf-8", errors="ignore") + b"\nendstream\nendobj\n"
        b"3 0 obj " + str(len(text.encode("utf-8", errors="ignore"))).encode("ascii") + b" endobj\n"
        b"trailer<<>>\n%%EOF\n"
    )


def pdf_response(title: str, lines: list[str], filename: str) -> HttpResponse:
    if canvas is None:
        response = HttpResponse(_fallback_pdf_bytes(title, lines), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setTitle(title)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, title)
    y -= 24

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    y -= 18

    for line in lines:
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50
        p.drawString(50, y, str(line)[:110])
        y -= 14

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response