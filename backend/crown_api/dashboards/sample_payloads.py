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


def school_board_sample_payload(school_id):
    try:
        from governance.services import build_board_dashboard_payload

        dashboard = build_board_dashboard_payload(school_id=school_id)
        enrollment = dashboard.get('enrollment', {})
        spiritual_life = dashboard.get('spiritual_life', {})
        crown_compass = dashboard.get('crown_compass', {})
        compliance = dashboard.get('compliance', {})
        watchlist = list(crown_compass.get('watchlist') or [])

        alerts = [
            alert(item, 'Medium', 'Board watchlist item')
            for item in watchlist[:3]
        ]
        if not alerts:
            alerts = [
                alert(
                    'No high-risk governance alerts are currently flagged',
                    'Low',
                    'Board-facing health signals are stable right now.',
                )
            ]

        return build_dashboard_payload(
            dashboard_key='school-board',
            metrics=[
                metric('Current enrollment', enrollment.get('current_enrollment', 0)),
                metric('Waitlist total', enrollment.get('waitlist_total', 0)),
                metric('Service hours YTD', spiritual_life.get('service_hours_ytd', 0)),
                metric('Overall health score', crown_compass.get('overall_score', 0)),
            ],
            alerts=alerts,
            queue=[
                queue_item('Review governance dashboard'),
                queue_item('Confirm board packet agenda'),
                queue_item(f"Open audit items: {compliance.get('open_audit_items', 0)}"),
            ],
            meta={
                'school_id': str(school_id),
                'served_from': 'live_db',
                'certification_candidate': 'live',
            },
        )
    except Exception:
        return build_dashboard_payload(
            dashboard_key='school-board',
            metrics=[
                metric('Current enrollment', '0'),
                metric('Waitlist total', '0'),
                metric('Service hours YTD', '0.0'),
                metric('Overall health score', '0'),
            ],
            alerts=[
                alert(
                    'School board dashboard is using the safe fallback contract',
                    'Low',
                    'Live governance metrics were unavailable during this request.',
                )
            ],
            queue=[
                queue_item('Review governance dashboard'),
                queue_item('Confirm board packet agenda'),
            ],
            meta={
                'school_id': str(school_id),
                'served_from': 'sample',
                'certification_candidate': 'hybrid',
            },
        )


SAMPLE_PAYLOAD_BUILDERS = {
    'attendance': attendance_sample_payload,
    'release-reliability': release_reliability_sample_payload,
    'school-board': school_board_sample_payload,
}
