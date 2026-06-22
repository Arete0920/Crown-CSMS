from .payload_contract import alert, build_dashboard_payload, metric, queue_item


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
    'summer-camp': summer_camp_sample_payload,
}
