"""Preview, approval and atomic distribution.

# Content operations: re-enrollment

## Change boundary

Base: `231f458a048c106082c7457aed21ec38a0d2fe87`.
Outcome: a school employee prepares, previews, approves and schedules a reusable
re-enrollment release; authorized guardians see the same published content and
record their response. Existing school, household, student, billing, help and
outbox authorities remain canonical.
Allowed: comms release models/services/API/tests, re-enrollment deadline and guards,
existing wizard, parent dashboard and status center, targeted verification workflow.
Forbidden: deployment, credentials, dependency changes, relaxed repository gates,
new wizard patterns, finance/grade/identity truth, marketing tracking services.
Decision owner: product owner; implementation authorized in this conversation.
Rollback: revert application commit; additive tables may remain until data has been
exported and a deliberate reverse migration is approved.
Verification: tenant and role denial, approval invalidation, schedule/expiry,
recipient drift, safe rendering, idempotency, transaction guards, family responses,
worker retry/context, migration consistency, frontend tests/build/lint.
Hosted delivery and production deployment require separate runtime evidence.

## Rules

A template is code-versioned; school overrides are explicit editable fields.
Year and deadline come from the existing re-enrollment session, never copied back
from editor text. Any change invalidates approval. Publication rechecks the preview
fingerprint and audience. Published content is immutable; corrections use a new
release with a reference to the superseded release. Expiry removes it from the
family feed; it cannot retract email already sent.

Blocks are plain text: announcement, event, permission, lesson resource and action
required. Links must be local paths or HTTPS. Public, published Solomon articles
may be referenced by slug; their revision and content hash enter approval proof.
Private help content cannot enter family-facing releases.

Publication and email enqueue share one database transaction. Email SENT means
provider accepted, not delivered or read. Attempts, retry errors, dead messages,
portal availability, acknowledgement and declared family intent are distinct.
An acknowledgement is not enrollment completion or payment. Billing counters
remain existing invoice-generation results, not evidence of enrollment acceptance.
Scheduling uses timezone-aware instants. The existing ten-second outbox task also
activates due releases. Worker/beat absence means schedules do not execute.

The workbench is an admissions interface and the existing parent dashboard and status center provide
the family interfaces. Both use the same versioned release. No extra CMS is needed.

Provider retry semantics are at-least-once: a crash after external acceptance but
before the database commit can cause another attempt. Exactly-once email delivery
is not claimed. Public resource summaries are reused with version/hash provenance;
private resources remain outside family notices. School-store quote and inventory
controls were inspected: quotes explicitly report unreserved stock and disabled
payment collection, while stock adjustments use locked, audited, idempotent writes.
"""
import hashlib
import json
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape

from audit.models import AuditLog
from households.models import Guardian, Student
from onboarding.models_tasks import HelpArticle
from .models import ContentRelease, NotificationPreference, OutboxMessage, ReleaseReceipt

BLOCK_TYPES = ('announcement', 'event', 'permission', 'lesson', 'action')


def validate_blocks(blocks):
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= 12:
        raise ValidationError('Use between one and twelve content blocks.')
    for block in blocks:
        if not isinstance(block, dict) or set(block) - {'type', 'title', 'body', 'link', 'resource_slug'}:
            raise ValidationError('Unknown content block fields.')
        if block.get('type') not in BLOCK_TYPES:
            raise ValidationError('Unknown content block type.')
        for key, limit in (('title', 200), ('body', 4000), ('link', 500), ('resource_slug', 200)):
            value = block.get(key, '')
            if not isinstance(value, str) or len(value) > limit:
                raise ValidationError(f'Invalid {key}.')
        if not block.get('title', '').strip() or not block.get('body', '').strip():
            raise ValidationError('Each block needs a title and body.')
        link = block.get('link', '')
        if link:
            parsed = urlsplit(link)
            if any(c.isspace() or ord(c) < 32 for c in link) or '\\' in link:
                raise ValidationError('Invalid link.')
            if not (link.startswith('/') and not link.startswith('//')) and not (parsed.scheme == 'https' and parsed.netloc and not parsed.username):
                raise ValidationError('Links must be local paths or HTTPS.')


def audit(release, actor, action):
    AuditLog.objects.create(user_id=actor.pk if actor else None, action=f'content.{action}', model='comms.ContentRelease', object_id=str(release.pk), metadata={'school_id': str(release.session.school_id), 'revision': release.revision})


def preview(release):
    release.full_clean()
    session = release.session
    if not session.target_year_label or session.status == "draft":
        raise ValidationError("Configure the re-enrollment session first.")
    if not session.deadline_at:
        raise ValidationError('Set the re-enrollment deadline before previewing.')
    try:
        local_deadline = session.deadline_at.astimezone(ZoneInfo(session.communication_timezone))
    except ZoneInfoNotFoundError as exc:
        raise ValidationError('Unknown school communication timezone.') from exc
    selected = sorted(s['id'] for s in (session.candidates_snapshot or []) if s['id'] not in (session.excluded_ids or []))
    students = list(Student.objects.filter(school_id=session.school_id, id__in=selected, is_active=True, household__is_active=True).order_by('id').values('id', 'household_id'))
    if not students or len(students) != len(selected):
        raise ValidationError('Candidate selection has changed; refresh the re-enrollment selection.')
    guardians = Guardian.objects.filter(school_id=session.school_id, household_id__in=[s['household_id'] for s in students]).select_related('account').order_by('id')
    audience = []
    for guardian in guardians:
        account = guardian.account
        email = guardian.email.strip()
        preference = NotificationPreference.objects.filter(user=account).first() if account else None
        if email:
            validate_email(email)
        if account and (not account.is_active or account.school_id != session.school_id):
            raise ValidationError('Recipient account is inactive or belongs to another school.')
        audience.append({'guardian_id': str(guardian.pk), 'account_id': str(account.pk) if account else None, 'email': email, 'email_enabled': bool(email and (not preference or preference.email_enabled))})
    if not audience:
        raise ValidationError('No guardians found for selected households.')
    blocks = [dict(block) for block in release.blocks]
    resources = []
    for block in blocks:
        slug = block.get('resource_slug')
        if slug:
            article = HelpArticle.objects.filter(slug=slug, state='published', published=True, visibility='public').first()
            if not article:
                raise ValidationError('Resource must be a public, published Solomon article.')
            block['body'] += '\n\n' + article.summary
            resources.append({'slug': slug, 'title': article.title, 'updated_at': article.updated_at.isoformat(), 'sha256': hashlib.sha256(article.content.encode()).hexdigest()})
    data = {'template_version': release.template_version, 'revision': release.revision, 'school': session.school.name, 'year': session.target_year_label, 'deadline': local_deadline.isoformat(), 'title': release.title, 'blocks': blocks, 'resources': resources, 'audience': audience, 'students': [{'id': str(s['id']), 'household_id': str(s['household_id'])} for s in students], 'publish_at': release.publish_at.isoformat() if release.publish_at else None, 'expires_at': release.expires_at.isoformat() if release.expires_at else None}
    data['fingerprint'] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return data


def public_content(data):
    return {k: data[k] for k in ('title', 'school', 'year', 'deadline', 'blocks', 'resources', 'template_version', 'revision')}


def render_email(data):
    parts = [f'<h1>{escape(data["title"])}</h1>', f'<p>{escape(data["school"])} · {escape(data["year"])}</p>', f'<p>Re-enrollment deadline: {escape(data["deadline"])}</p>']
    for block in data['blocks']:
        parts.append(f'<h2>{escape(block["title"])}</h2><p>{escape(block["body"]).replace(chr(10), "<br>")}</p>')
        # Relative links are for the portal; email never invents a host.
        if block.get('link', '').startswith('https://'):
            parts.append(f'<p><a href="{escape(block["link"])}">View details</a></p>')
    return ''.join(parts)


@transaction.atomic
def publish(release_id, actor=None):
    from reenrollment.models import ReenrollmentSession
    session_id = ContentRelease.objects.values_list('session_id', flat=True).get(pk=release_id)
    session = ReenrollmentSession.objects.select_for_update().select_related('school').get(pk=session_id)
    release = ContentRelease.objects.select_for_update().get(pk=release_id)
    release.session = session
    if release.status == 'published':
        return release
    if release.status != 'approved':
        raise ValidationError('Approve the current preview before publishing.')
    now = timezone.now()
    if release.publish_at and release.publish_at > now:
        raise ValidationError('Scheduled publication is not due.')
    if release.expires_at and release.expires_at <= now:
        raise ValidationError('Release has expired.')
    data = preview(release)
    if data['fingerprint'] != release.approved_fingerprint:
        raise ValidationError('Content or audience changed; preview and approve again.')
    for target in data['audience']:
        message = None
        if target['email_enabled']:
            message, _ = OutboxMessage.objects.get_or_create(idempotency_key=f'release:{release.pk}:{target["guardian_id"]}', defaults={'school_id': str(release.session.school_id), 'channel': 'EMAIL', 'to': target['email'], 'subject': release.title, 'body': render_email(data)})
        ReleaseReceipt.objects.create(release=release, guardian_id=target['guardian_id'], outbox=message)
    release.snapshot = public_content(data)
    release.status = 'published'
    release.published_at = now
    release.last_error = ''
    release.save()
    audit(release, actor, 'published')
    return release


def activate_due_releases():
    results = {'published': 0, 'blocked': 0}
    ids = ContentRelease.objects.filter(status='approved', publish_at__lte=timezone.now()).values_list('pk', flat=True)[:25]
    for release_id in list(ids):
        try:
            publish(release_id)
            results['published'] += 1
        except ValidationError as exc:
            with transaction.atomic():
                release = ContentRelease.objects.select_for_update().get(pk=release_id)
                if release.status == 'approved':
                    release.status = 'draft'
                    release.approved_fingerprint = ''
                    release.approved_by = None
                    release.last_error = '; '.join(exc.messages)[:500]
                    release.save()
                    audit(release, None, 'blocked')
            results['blocked'] += 1
    return results


def metrics(release):
    receipts = list(release.receipts.select_related('outbox', 'guardian'))
    return {'recipients': len(receipts), 'portal_available': sum(bool(r.guardian.account_id) for r in receipts), 'email_accepted': sum(bool(r.outbox and r.outbox.status == 'SENT') for r in receipts), 'email_pending': sum(bool(r.outbox and r.outbox.status == 'PENDING') for r in receipts), 'email_dead': sum(bool(r.outbox and r.outbox.status == 'DEAD') for r in receipts), 'email_errors': [{'receipt_id': r.pk, 'state': r.outbox.status, 'attempts': r.outbox.attempts, 'error': r.outbox.last_error} for r in receipts if r.outbox and r.outbox.last_error], 'attempts': sum(r.outbox.attempts if r.outbox else 0 for r in receipts), 'acknowledged': sum(bool(r.acknowledged_at) for r in receipts), 'responses': {choice: sum(r.response == choice for r in receipts) for choice in ('returning', 'declining', 'undecided')}, 'email_delivery_confirmed': None, 'enrollment_completed': None}


def invalidate_session_releases(session, actor):
    """Caller holds the session lock; writers use session-before-release order."""
    for release in ContentRelease.objects.select_for_update().filter(session=session, status='approved'):
        release.status = 'draft'
        release.approved_fingerprint = ''
        release.approved_by = None
        release.last_error = 'Re-enrollment configuration changed; preview and approve again.'
        release.save()
        audit(release, actor, 'invalidated')
