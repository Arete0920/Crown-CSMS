"""Canonical, school-scoped, current-year Financial Aid dashboard read model.

Counts are application/award *records*, not students or cash transactions.
Do not label an accepted award's face value as a disbursement or claim that
source-level live reads constitute hosted/financial certification.
"""


class FinancialAidDashboardIntegrityError(ValueError):
    """An aid record or current-year scope is inconsistent; do not show totals."""


def _same_id(left, right):
    return left is not None and right is not None and str(left) == str(right)


def _money(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"


def summarize_financial_aid_rows(*, school_id, year_id, applications, awards):
    """Validate relationships before returning integer-only aggregates.

    The ORM producer supplies values()/related FK projections for one verified
    school and current academic year. No PII or individual record details leave
    this function. A partial, inconsistent total must never look authoritative.
    """
    allowed_app_statuses = {
        'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'NEEDS_INFO',
        'APPROVED', 'DENIED', 'WITHDRAWN',
    }
    actionable = {'SUBMITTED', 'UNDER_REVIEW', 'NEEDS_INFO'}
    allowed_decisions = {'OFFERED', 'ACCEPTED', 'DECLINED'}

    submitted_count = 0
    requiring_review_count = 0
    accepted_awards_count = 0
    accepted_face_value_cents = 0
    accepted_without_ledger_count = 0
    submitted_families = set()

    for app in applications:
        if (
            not _same_id(app.get('family__school_id'), school_id)
            or not _same_id(app.get('academic_year__school_id'), school_id)
            or app.get('status') not in allowed_app_statuses
            or app.get('family_id') is None
        ):
            raise FinancialAidDashboardIntegrityError('Inconsistent aid application scope or status')
        status = app['status']
        if status not in {'DRAFT', 'WITHDRAWN'}:
            submitted_count += 1
            submitted_families.add(str(app['family_id']))
        if status in actionable:
            requiring_review_count += 1

    for award in awards:
        if (
            not _same_id(award.get('student__school_id'), school_id)
            or not _same_id(award.get('student__family__school_id'), school_id)
            or not _same_id(award.get('academic_year__school_id'), school_id)
            or award.get('student__family_id') is None
            or award.get('decision_status') not in allowed_decisions
            or type(award.get('awarded_cents')) is not int
            or award['awarded_cents'] < 0
        ):
            raise FinancialAidDashboardIntegrityError('Inconsistent aid award scope or amount')

        if award.get('aid_application_id') is not None and (
            not _same_id(award.get('aid_application__school_id'), school_id)
            or not _same_id(award.get('aid_application__academic_year_id'), year_id)
            or not _same_id(award.get('aid_application__family_id'), award['student__family_id'])
        ):
            raise FinancialAidDashboardIntegrityError('Award application and student family mismatch')

        # A linked ledger entry is additional evidence; validate it without
        # assuming that every historical accepted award was posted.
        if award.get('ledger_entry_id') is not None:
            reversal_count = award.get('ledger_reversal_count')
            if (
                not _same_id(award.get('ledger_entry__school_id'), school_id)
                or not _same_id(award.get('ledger_entry__academic_year_id'), year_id)
                or not _same_id(award.get('ledger_entry__student_id'), award['student_id'])
                or not _same_id(award.get('ledger_entry__family_id'), award['student__family_id'])
                or not _same_id(award.get('ledger_entry__account__school_id'), school_id)
                or award.get('ledger_entry__account__code') != 'AID'
                or award.get('ledger_entry__source') != 'AID_AWARD'
                or award.get('ledger_entry__is_reversal') is not False
                or award.get('ledger_entry__reversal_of_id') is not None
                or award.get('ledger_entry__amount_cents') != -award['awarded_cents']
                or type(reversal_count) is not int
                or reversal_count < 0 or reversal_count > 1
                or award['decision_status'] == 'OFFERED'
                or (award['decision_status'] == 'ACCEPTED' and reversal_count != 0)
                or (award['decision_status'] == 'DECLINED' and (reversal_count != 1 or award.get('ledger_reversal_validated') is not True))
            ):
                raise FinancialAidDashboardIntegrityError('Award ledger linkage requires reconciliation')

        if award['decision_status'] == 'ACCEPTED':
            if award['awarded_cents'] <= 0:
                raise FinancialAidDashboardIntegrityError('Accepted award must have positive face value')
            accepted_awards_count += 1
            accepted_face_value_cents += award['awarded_cents']
            if award.get('ledger_entry_id') is None:
                accepted_without_ledger_count += 1

    return {
        'submitted_applications': submitted_count,
        'submitted_families': len(submitted_families),
        'applications_requiring_review': requiring_review_count,
        'accepted_award_records': accepted_awards_count,
        'accepted_award_face_value_cents': accepted_face_value_cents,
        'accepted_without_ledger_count': accepted_without_ledger_count,
    }


def financial_aid_live_payload(school_id):
    """Return a live source only for exactly one current school academic year.

    Missing current-year configuration returns None so the existing dashboard
    can explicitly fall back to a labeled snapshot/sample/503. Multiple current
    years or inconsistent financial records fail closed and cannot fall back.
    """
    from aid.models import AidApplication, AidAward
    from core.models import AcademicYear
    from django.db.models import Count
    from .payload_contract import alert, build_dashboard_payload, metric

    current_years = list(
        AcademicYear.objects.filter(school_id=school_id, is_current=True)
        .values_list('id', flat=True)[:2]
    )
    if not current_years:
        return None
    if len(current_years) != 1:
        raise FinancialAidDashboardIntegrityError('Multiple current school academic years')
    year_id = current_years[0]

    applications = AidApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id
    ).values('family_id', 'family__school_id', 'academic_year__school_id', 'status')
    awards = AidAward.objects.filter(
        school_id=school_id, academic_year_id=year_id
    ).annotate(
        ledger_reversal_count=Count('ledger_entry__reversals', distinct=True),
    ).values(
        'ledger_reversal_count',
        'student_id', 'student__school_id', 'student__family_id',
        'student__family__school_id', 'academic_year__school_id',
        'aid_application_id', 'aid_application__school_id',
        'aid_application__academic_year_id', 'aid_application__family_id',
        'decision_status', 'awarded_cents', 'ledger_entry_id',
        'ledger_entry__school_id', 'ledger_entry__academic_year_id',
        'ledger_entry__student_id', 'ledger_entry__family_id',
        'ledger_entry__amount_cents', 'ledger_entry__is_reversal',
        'ledger_entry__source', 'ledger_entry__account__school_id',
        'ledger_entry__account__code', 'ledger_entry__reversal_of_id',
        'ledger_entry__account_id',
    )
    # Validate the reversal *transaction*, not merely the existence/count of
    # a record pointing back to the original aid credit.  A single malformed
    # reversal could otherwise make an unreconciled decline look clean.
    award_rows = list(awards)
    posted_declines = [
        row for row in award_rows
        if row.get('decision_status') == 'DECLINED' and row.get('ledger_entry_id') is not None
    ]
    if posted_declines:
        from core.models import LedgerEntry
        original_ids = [row['ledger_entry_id'] for row in posted_declines]
        if len(set(str(pk) for pk in original_ids)) != len(original_ids):
            raise FinancialAidDashboardIntegrityError('Duplicate original aid ledger reference')
        reversal_rows = LedgerEntry.objects.filter(
            reversal_of_id__in=original_ids,
        ).values(
            'reversal_of_id', 'school_id', 'family_id', 'student_id',
            'academic_year_id', 'account_id', 'source', 'amount_cents', 'is_reversal',
        )
        by_original = {}
        for reversal in reversal_rows:
            by_original.setdefault(str(reversal.get('reversal_of_id')), []).append(reversal)
        for row in posted_declines:
            candidates = by_original.get(str(row['ledger_entry_id']), [])
            if len(candidates) != 1:
                raise FinancialAidDashboardIntegrityError('Aid reversal requires reconciliation')
            reversal = candidates[0]
            if (
                not _same_id(reversal.get('reversal_of_id'), row['ledger_entry_id'])
                or not _same_id(reversal.get('school_id'), school_id)
                or not _same_id(reversal.get('family_id'), row.get('ledger_entry__family_id'))
                or not _same_id(reversal.get('student_id'), row.get('ledger_entry__student_id'))
                or not _same_id(reversal.get('academic_year_id'), row.get('ledger_entry__academic_year_id'))
                or not _same_id(reversal.get('account_id'), row.get('ledger_entry__account_id'))
                or reversal.get('source') != row.get('ledger_entry__source')
                or reversal.get('is_reversal') is not True
                or type(reversal.get('amount_cents')) is not int
                or type(row.get('ledger_entry__amount_cents')) is not int
                or reversal['amount_cents'] != -row['ledger_entry__amount_cents']
            ):
                raise FinancialAidDashboardIntegrityError('Invalid aid reversal requires reconciliation')
            row['ledger_reversal_validated'] = True
    facts = summarize_financial_aid_rows(
        school_id=school_id, year_id=year_id,
        applications=applications, awards=award_rows,
    )

    unposted = facts['accepted_without_ledger_count']
    return build_dashboard_payload(
        dashboard_key='financial-aid',
        metrics=[
            metric('Applications submitted (current year)', facts['submitted_applications'],
                   'Application records; draft and withdrawn excluded'),
            metric('Applications requiring review', facts['applications_requiring_review'],
                   'Submitted, under review, or needs information'),
            metric('Accepted award records', facts['accepted_award_records'],
                   'Award records, not distinct students or families'),
            metric('Accepted award face value', _money(facts['accepted_award_face_value_cents']),
                   'Commitment face value; not cash disbursed'),
        ],
        queue=([f'{facts["applications_requiring_review"]} applications require review']
               if facts['applications_requiring_review'] else []),
        alerts=([alert('Accepted awards without linked legacy ledger entries', 'Medium',
                       f'{unposted} records need reconciliation before posting claims')]
                if unposted else []),
        meta={
            'served_from': 'live_db',
            'source': 'canonical_aid_application_and_award_records',
            'school_id': str(school_id),
            'academic_year_id': str(year_id),
            'application_unit': 'application_record_not_student',
            'award_unit': 'accepted_award_record_not_student',
            'money_basis': 'face_value_not_disbursement',
            'source_live_not_hosted_certified': True,
            **facts,
        },
    )
