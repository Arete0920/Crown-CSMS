from apps.compliance.models import ConsentAudit


def record_consent(
    *,
    tenant_id,
    consent_type,
    version,
    user=None,
    ip_address=None,
    metadata=None,
):
    return ConsentAudit.objects.create(
        tenant_id=tenant_id,
        consent_type=consent_type,
        version=version,
        user=user,
        ip_address=ip_address,
        metadata=metadata or {},
    )
