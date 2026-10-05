from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School, UserAccount
from core.permissions import CrownModulePermission, user_has_permission

from .models import ElectronicEnvelope, ElectronicFormTemplate, ElectronicSigner
from .services import (
    add_signer,
    consent_disclosure,
    create_envelope,
    record_consent,
    request_paper_copy,
    send_envelope,
    sign_envelope,
    withdraw_consent,
)


def _school(request):
    school = getattr(request, "school", None)
    if school:
        return school
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        return None
    return School.objects.filter(pk=school_id).first()


def _validation_response(exc):
    if hasattr(exc, "message_dict"):
        detail = exc.message_dict
    elif hasattr(exc, "messages"):
        detail = exc.messages
    else:
        detail = str(exc)
    return Response({"detail": detail}, status=status.HTTP_409_CONFLICT)


def _signer_for_user(*, envelope, user):
    return ElectronicSigner.objects.filter(
        envelope=envelope,
        school=envelope.school,
        user=user,
    ).select_related("envelope").first()


def _serialize_signer(signer):
    return {
        "id": str(signer.id),
        "display_name": signer.display_name,
        "role_label": signer.role_label,
        "signing_order": signer.signing_order,
        "status": signer.status,
        "signed_at": signer.signed_at.isoformat() if signer.signed_at else None,
    }


def _serialize_envelope(envelope, *, include_document=False):
    payload = {
        "id": str(envelope.id),
        "title": envelope.title,
        "template_key": envelope.template_key,
        "template_version": envelope.template_version,
        "subject_type": envelope.subject_type,
        "subject_id": envelope.subject_id,
        "document_sha256": envelope.document_sha256,
        "provider_code": envelope.provider_code,
        "status": envelope.status,
        "sent_at": envelope.sent_at.isoformat() if envelope.sent_at else None,
        "completed_at": envelope.completed_at.isoformat() if envelope.completed_at else None,
        "signers": [_serialize_signer(s) for s in envelope.signers.all()],
    }
    if include_document:
        payload["document_snapshot"] = envelope.document_snapshot
    return payload


class ElectronicConsentDisclosureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(consent_disclosure())


class ElectronicFormTemplateListCreateView(APIView):
    permission_classes = [CrownModulePermission("forms.manage")]

    def get(self, request):
        school = _school(request)
        if not school:
            return Response({"detail": "Missing or invalid school context"}, status=400)
        rows = ElectronicFormTemplate.objects.filter(school=school, is_active=True)
        return Response([
            {
                "id": str(row.id),
                "key": row.key,
                "version": row.version,
                "name": row.name,
                "title": row.title,
                "form_schema": row.form_schema,
            }
            for row in rows
        ])

    def post(self, request):
        school = _school(request)
        if not school:
            return Response({"detail": "Missing or invalid school context"}, status=400)
        payload = request.data or {}
        required = ["key", "name", "title", "body"]
        missing = [key for key in required if not str(payload.get(key) or "").strip()]
        if missing:
            return Response({"detail": f"Missing required fields: {', '.join(missing)}"}, status=400)
        try:
            template = ElectronicFormTemplate.objects.create(
                school=school,
                key=str(payload["key"]).strip(),
                version=int(payload.get("version") or 1),
                name=str(payload["name"]).strip(),
                title=str(payload["title"]).strip(),
                body=str(payload["body"]),
                form_schema=payload.get("form_schema") or {},
                created_by=request.user,
            )
        except (ValidationError, ValueError) as exc:
            return _validation_response(exc)
        return Response({"id": str(template.id), "key": template.key, "version": template.version}, status=201)


class ElectronicEnvelopeCreateView(APIView):
    permission_classes = [CrownModulePermission("forms.manage")]

    def post(self, request):
        school = _school(request)
        if not school:
            return Response({"detail": "Missing or invalid school context"}, status=400)
        payload = request.data or {}
        template = ElectronicFormTemplate.objects.filter(
            pk=payload.get("template_id"),
            school=school,
            is_active=True,
        ).first()
        if not template:
            return Response({"detail": "Template not found."}, status=404)

        signer_payloads = payload.get("signers")
        if not isinstance(signer_payloads, list) or not signer_payloads:
            return Response({"detail": "At least one signer is required."}, status=400)

        try:
            with transaction.atomic():
                envelope = create_envelope(
                    template=template,
                    created_by=request.user,
                    form_data=payload.get("form_data") or {},
                    subject_type=str(payload.get("subject_type") or ""),
                    subject_id=str(payload.get("subject_id") or ""),
                    title=str(payload.get("title") or ""),
                )
                for index, signer_payload in enumerate(signer_payloads, start=1):
                    signer_user = UserAccount.objects.filter(
                        pk=signer_payload.get("user_id"),
                        school=school,
                    ).first()
                    if signer_user is None:
                        raise ValidationError("Each signer must be an existing user in this school.")
                    add_signer(
                        envelope=envelope,
                        user=signer_user,
                        display_name=str(signer_payload.get("display_name") or signer_user.get_full_name() or signer_user.email),
                        email=str(signer_payload.get("email") or signer_user.email or ""),
                        role_label=str(signer_payload.get("role_label") or ""),
                        signing_order=int(signer_payload.get("signing_order") or index),
                    )
                envelope = send_envelope(envelope)
        except (ValidationError, ValueError) as exc:
            return _validation_response(exc)

        envelope = ElectronicEnvelope.objects.prefetch_related("signers").get(pk=envelope.pk)
        return Response(_serialize_envelope(envelope, include_document=True), status=201)


class MyElectronicEnvelopesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _school(request)
        if not school:
            return Response({"detail": "Missing or invalid school context"}, status=400)
        envelopes = (
            ElectronicEnvelope.objects.filter(school=school, signers__user=request.user)
            .prefetch_related("signers")
            .distinct()
        )
        payload = []
        for row in envelopes:
            item = _serialize_envelope(row)
            signer = _signer_for_user(envelope=row, user=request.user)
            item["current_signer"] = _serialize_signer(signer) if signer else None
            payload.append(item)
        return Response(payload)


class ElectronicEnvelopeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, envelope_id):
        school = _school(request)
        if not school:
            return Response({"detail": "Missing or invalid school context"}, status=400)
        envelope = ElectronicEnvelope.objects.filter(pk=envelope_id, school=school).prefetch_related("signers").first()
        if envelope is None:
            return Response({"detail": "Envelope not found."}, status=404)
        signer = _signer_for_user(envelope=envelope, user=request.user)
        can_manage = user_has_permission(request.user, "forms.manage", school=school)
        if signer is None and not can_manage:
            return Response({"detail": "Permission denied."}, status=403)
        payload = _serialize_envelope(envelope, include_document=True)
        payload["current_signer"] = _serialize_signer(signer) if signer else None
        return Response(payload)


class ElectronicEnvelopeConsentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, envelope_id):
        school = _school(request)
        envelope = ElectronicEnvelope.objects.filter(pk=envelope_id, school=school).first() if school else None
        if envelope is None:
            return Response({"detail": "Envelope not found."}, status=404)
        signer = _signer_for_user(envelope=envelope, user=request.user)
        if signer is None:
            return Response({"detail": "Permission denied."}, status=403)
        payload = request.data or {}
        try:
            evidence = record_consent(
                signer=signer,
                user=request.user,
                disclosure_version=str(payload.get("disclosure_version") or ""),
                hardware_software_ack=payload.get("hardware_software_ack") is True,
                request_meta=request.META,
            )
        except ValidationError as exc:
            return _validation_response(exc)
        return Response({"evidence_id": str(evidence.id), "status": "CONSENTED"})


class ElectronicEnvelopeSignView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, envelope_id):
        school = _school(request)
        envelope = ElectronicEnvelope.objects.filter(pk=envelope_id, school=school).first() if school else None
        if envelope is None:
            return Response({"detail": "Envelope not found."}, status=404)
        signer = _signer_for_user(envelope=envelope, user=request.user)
        if signer is None:
            return Response({"detail": "Permission denied."}, status=403)
        payload = request.data or {}
        try:
            evidence = sign_envelope(
                signer=signer,
                user=request.user,
                signed_name=str(payload.get("signed_name") or ""),
                intent_to_sign=payload.get("intent_to_sign") is True,
                request_meta=request.META,
            )
        except ValidationError as exc:
            return _validation_response(exc)
        envelope.refresh_from_db()
        return Response({
            "evidence_id": str(evidence.id),
            "document_sha256": evidence.document_sha256,
            "envelope_status": envelope.status,
        })


class ElectronicEnvelopeWithdrawView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, envelope_id):
        school = _school(request)
        envelope = ElectronicEnvelope.objects.filter(pk=envelope_id, school=school).first() if school else None
        if envelope is None:
            return Response({"detail": "Envelope not found."}, status=404)
        signer = _signer_for_user(envelope=envelope, user=request.user)
        if signer is None:
            return Response({"detail": "Permission denied."}, status=403)
        try:
            evidence = withdraw_consent(signer=signer, user=request.user, request_meta=request.META)
        except ValidationError as exc:
            return _validation_response(exc)
        return Response({"evidence_id": str(evidence.id), "status": "WITHDRAWN"})


class ElectronicEnvelopePaperCopyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, envelope_id):
        school = _school(request)
        envelope = ElectronicEnvelope.objects.filter(pk=envelope_id, school=school).first() if school else None
        if envelope is None:
            return Response({"detail": "Envelope not found."}, status=404)
        signer = _signer_for_user(envelope=envelope, user=request.user)
        if signer is None:
            return Response({"detail": "Permission denied."}, status=403)
        try:
            evidence = request_paper_copy(signer=signer, user=request.user, request_meta=request.META)
        except ValidationError as exc:
            return _validation_response(exc)
        return Response({"evidence_id": str(evidence.id), "status": "PAPER_REQUESTED"})
