from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .payload_contract import alert, build_dashboard_payload, metric, queue_item


def billing_live_payload(school_id):
    """Build the billing dashboard from tenant-scoped production billing/ledger rows."""
    from billing.models import Invoice
    from ledger.models import Payment

    today = timezone.localdate()
    invoices = Invoice.objects.filter(school_id=school_id)
    payments = Payment.objects.filter(school_id=school_id, is_void=False)

    billed_total = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    paid_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    outstanding_total = billed_total - paid_total
    invoice_count = invoices.count()
    overdue_count = invoices.filter(due_on__lt=today).count()
    payments_today = (
        payments.filter(created_at__date=today).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    alerts = []
    if overdue_count:
        alerts.append(
            alert(
                f'{overdue_count} invoice(s) are past their due date',
                'High',
                'Finance team follow-up is required.',
            )
        )
    else:
        alerts.append(
            alert(
                'No past-due invoices are currently recorded',
                'Low',
                'Continue routine receivables review.',
            )
        )

    return build_dashboard_payload(
        dashboard_key='billing',
        metrics=[
            metric('Invoices Issued', str(invoice_count)),
            metric('Outstanding Balances', f'${outstanding_total:,.2f}'),
            metric('Overdue Invoices', str(overdue_count)),
            metric('Payments Collected Today', f'${payments_today:,.2f}'),
        ],
        alerts=alerts,
        queue=[
            queue_item('Review overdue invoices and assign follow-up'),
            queue_item('Reconcile billing totals against the ledger'),
            queue_item('Review today payment activity'),
            queue_item('Confirm the next billing run schedule'),
        ],
        meta={
            'school_id': str(school_id),
            'served_from': 'live_db',
            'source': 'billing_invoice_and_ledger_payment',
            'billed_total': str(billed_total),
            'paid_total': str(paid_total),
            'outstanding_total': str(outstanding_total),
        },
    )


def summer_camp_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='summer-camp',
        metrics=[
            metric('Registered Campers', '79'),
            metric('Staffed Sessions', '11'),
            metric('Waitlist Families', '9'),
            metric('Transport Confirmed', '92%'),
        ],
        alerts=[
            alert(
                'Two afternoon sessions have unconfirmed counselors',
                'High',
                'Resolve assignment before staffing freeze.',
            ),
            alert(
                'Route sheet is waiting on final roster export',
                'Medium',
                'Transportation lead requires approved roster export.',
            ),
            alert(
                'Nine waitlist families need callbacks',
                'Low',
                'Offer open seats before orientation packet lock.',
            ),
        ],
        queue=[
            queue_item('Finalize counselor staffing swaps'),
            queue_item('Call top 9 waitlist families'),
            queue_item('Publish week-one route sheet'),
            queue_item('Confirm transportation roster export'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


BATCH5_EXTRA_PAYLOAD_BUILDERS = {
    'billing': billing_live_payload,
    'summer-camp': summer_camp_sample_payload,
}
