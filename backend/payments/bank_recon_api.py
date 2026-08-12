import csv
import io
import logging
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from payments.models import (
    BankStatementEntry,
    BankStatementImport,
    BankStatementImportStatus,
    PayoutBankMatch,
    ProviderPayoutBatch,
)
from payments.reconciliation_ops import auto_match_payout_batches_for_school, create_manual_payout_match


logger = logging.getLogger(__name__)


def _finance_only(user):
    return has_finance_runtime_role(user)


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(value: str):
    value = (value or "").replace(",", "").strip()
    if not value:
        return Decimal("0.00")
    return Decimal(str(value))


def _row_has_data(raw: dict) -> bool:
    return any(str(value or "").strip() for value in raw.values())


@transaction.atomic
def _process_bank_statement_bytes(*, import_row: BankStatementImport, raw_bytes: bytes) -> int:
    """Persist one statement atomically; malformed rows fail the whole import."""
    decoded = raw_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValueError("Statement CSV is missing a header row.")

    rows = 0
    for raw in reader:
        if not _row_has_data(raw):
            continue

        posted_date = _parse_date(raw.get("posted_date") or raw.get("date"))
        if posted_date is None:
            raise ValueError(f"Invalid or missing posted_date at CSV row {reader.line_num}.")

        currency = (raw.get("currency") or "USD").strip().upper() or "USD"
        BankStatementEntry.objects.create(
            school_id=import_row.school_id,
            statement_import=import_row,
            posted_date=posted_date,
            description=(raw.get("description") or "")[:255],
            reference=(raw.get("reference") or raw.get("txn_id") or raw.get("id") or "")[:128],
            amount=_parse_amount(raw.get("amount") or raw.get("net_amount") or "0"),
            currency=currency[:8],
            payload=raw,
        )
        rows += 1

    if rows == 0:
        raise ValueError("Statement CSV contained no valid data rows.")

    import_row.status = BankStatementImportStatus.PROCESSED
    import_row.row_count = rows
    import_row.error_message = ""
    import_row.processed_at = timezone.now()
    import_row.save(
        update_fields=["status", "row_count", "error_message", "processed_at"]
    )
    return rows


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_bank_statement_csv(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    upload = request.FILES.get("file")
    if not upload:
        return Response({"detail": "Missing CSV file."}, status=status.HTTP_400_BAD_REQUEST)

    import_row = BankStatementImport.objects.create(
        school_id=school_id,
        uploaded_by=request.user,
        source_name=upload.name,
        status=BankStatementImportStatus.UPLOADED,
    )

    try:
        raw_bytes = upload.read()
        _process_bank_statement_bytes(import_row=import_row, raw_bytes=raw_bytes)
    except Exception as exc:
        import_row.refresh_from_db()
        import_row.status = BankStatementImportStatus.FAILED
        import_row.error_message = str(exc)
        import_row.processed_at = None
        import_row.save(update_fields=["status", "error_message", "processed_at"])
        logger.exception(
            "upload_bank_statement_csv: failed to process uploaded statement",
            extra={"import_id": import_row.id},
        )
        return Response(
            {"ok": False, "error": "Unable to process the uploaded statement file."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    import_row.refresh_from_db()
    return Response(
        {
            "ok": True,
            "import_id": import_row.id,
            "row_count": import_row.row_count,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bank_statement_imports_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = [
        {
            "id": row.id,
            "source_name": row.source_name,
            "status": row.status,
            "row_count": row.row_count,
            "created_at": row.created_at,
            "processed_at": row.processed_at,
        }
        for row in BankStatementImport.objects.filter(school_id=school_id).order_by("-id")
    ]
    return Response({"results": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unmatched_bank_entries_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = [
        {
            "id": row.id,
            "posted_date": row.posted_date,
            "description": row.description,
            "reference": row.reference,
            "amount": str(row.amount),
            "currency": row.currency,
            "statement_import_id": row.statement_import_id,
        }
        for row in BankStatementEntry.objects.filter(
            school_id=school_id,
            is_matched=False,
        ).order_by("-posted_date", "-id")
    ]
    return Response({"results": rows})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auto_match_payouts(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    matched_count = auto_match_payout_batches_for_school(school_id=school_id)
    return Response({"ok": True, "matched_count": matched_count})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manual_match_payout(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    payout_batch_id = request.data.get("payout_batch_id")
    bank_entry_id = request.data.get("bank_entry_id")
    note = request.data.get("note", "")

    payout_batch = ProviderPayoutBatch.objects.filter(school_id=school_id, id=payout_batch_id).first()
    bank_entry = BankStatementEntry.objects.filter(school_id=school_id, id=bank_entry_id).first()

    if not payout_batch or not bank_entry:
        return Response({"detail": "Payout batch or bank entry not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        match = create_manual_payout_match(
            school_id=school_id,
            payout_batch=payout_batch,
            bank_entry=bank_entry,
            user=request.user,
            note=note,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "ok": True,
            "match_id": match.id,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payout_bank_matches_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = [
        {
            "id": row.id,
            "payout_batch_id": row.payout_batch_id,
            "bank_entry_id": row.bank_entry_id,
            "status": row.status,
            "amount_delta": str(row.amount_delta),
            "date_delta_days": row.date_delta_days,
            "note": row.note,
            "matched_by_id": row.matched_by_id,
            "created_at": row.created_at,
        }
        for row in PayoutBankMatch.objects.filter(school_id=school_id).order_by("-id")
    ]
    return Response({"results": rows})