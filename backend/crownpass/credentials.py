from __future__ import annotations

import base64
import hashlib
import io

from django.core import signing

SALT = "crownpass.admission.v1"
MAX_AGE_SECONDS = 60 * 60 * 12


def issue_admission_credential(*, ticket) -> str:
    return signing.dumps(
        {"ticket_id": str(ticket.id), "school_id": str(ticket.school_id)},
        salt=SALT,
        compress=True,
    )


def verify_admission_credential(*, credential: str, school_id):
    payload = signing.loads(credential, salt=SALT, max_age=MAX_AGE_SECONDS)
    if str(payload.get("school_id")) != str(school_id):
        raise signing.BadSignature("Credential tenant mismatch.")
    return payload


def credential_fingerprint(credential: str) -> str:
    return "crownpass:" + hashlib.sha256(credential.encode("utf-8")).hexdigest()[:32]


def render_qr_data_url(credential: str) -> str:
    import qrcode

    image = qrcode.make(credential)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return "data:image/png;base64," + encoded
