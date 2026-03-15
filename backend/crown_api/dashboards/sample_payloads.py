from .payload_contract import alert, build_dashboard_payload, metric, queue_item


def attendance_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='attendance',
        metrics=[
            metric('Present Rate Today', '96.1%'),
            metric('Absent Students', '14'),
            metric('Late Check-Ins', '9'),
            metric('Missing Homerooms', '3'),
        ],
        alerts=[
            alert(
                'Three homerooms still need final attendance submission',
                'High',
                'Attendance office follow-up required.',
            ),
            alert(
                'Grade 10 absentee trend is above weekly threshold',
                'Medium',
                'Review with school admin and student care.',
            ),
            alert(
                'Two parent outreach messages bounced',
                'Low',
                'Retry communication workflow.',
            ),
        ],
        queue=[
            queue_item('Review unsubmitted homeroom attendance'),
            queue_item('Send parent outreach for chronic absence group'),
            queue_item('Confirm late-check-in corrections from front office'),
            queue_item('Publish attendance exception summary'),
        ],
        meta={
            'school_id': str(school_id),
            'served_from': 'sample',
            'certification_candidate': 'hybrid',
        },
    )


def release_reliability_sample_payload(_school_id):
    return build_dashboard_payload(
        dashboard_key='release-reliability',
        metrics=[
            metric('Deployments This Month', '9'),
            metric('Open Production Incidents', '2'),
            metric('Failed Checks in Last 24h', '4'),
            metric('Release Readiness', 'Watch'),
        ],
        alerts=[
            alert(
                'Contract gate failed on last main candidate build',
                'High',
                'Platform engineering follow-up required.',
            ),
            alert(
                'Two environments are not on expected build SHA',
                'High',
                'Verify deployment alignment.',
            ),
            alert(
                'Release proof packet is incomplete for one deploy',
                'Medium',
                'Complete evidence before certification.',
            ),
        ],
        queue=[
            queue_item('Review failed release gate evidence'),
            queue_item('Verify environment build SHA alignment'),
            queue_item('Close open production incident postmortem tasks'),
            queue_item('Publish release readiness summary'),
        ],
        meta={
            'school_id': 'platform',
            'served_from': 'sample',
            'certification_candidate': 'hybrid',
        },
    )


SAMPLE_PAYLOAD_BUILDERS = {
    'attendance': attendance_sample_payload,
    'release-reliability': release_reliability_sample_payload,
}
