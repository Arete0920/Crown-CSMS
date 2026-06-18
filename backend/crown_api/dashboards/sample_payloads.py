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


def portrait_service_sample_payload(school_id):
    try:
        from core.models import School
        from spiritual_life.services import build_mission_metrics_dashboard

        school = School.objects.get(pk=school_id)
        detail_metrics = build_mission_metrics_dashboard(school)
        queue = [
            queue_item(item.get('label') or item.get('secondary') or 'Review mission metrics')
            for item in (detail_metrics.get('approval_queue') or [])[:2]
        ]
        queue.extend(
            queue_item(item.get('label') or 'Review portrait record')
            for item in (detail_metrics.get('portrait_review_queue') or [])[:2]
        )
        if not queue:
            queue = [queue_item('Review mission readiness dashboard')]

        payload = build_dashboard_payload(
            dashboard_key='portrait-service',
            metrics=[
                metric('Mission readiness', detail_metrics.get('mission_readiness_pct', 0)),
                metric('Approved service hours', detail_metrics.get('approved_service_hours', 0)),
                metric('Pending service hours', detail_metrics.get('pending_service_hours', 0)),
                metric('Portrait completion', detail_metrics.get('portrait_completion_pct', 0)),
            ],
            alerts=detail_metrics.get('alerts', []),
            queue=queue,
            meta={
                'school_id': str(school_id),
                'served_from': detail_metrics.get('source', 'live_db'),
                'certification_candidate': 'live',
            },
        )
        payload['detail_metrics'] = detail_metrics
        return payload
    except Exception:
        payload = build_dashboard_payload(
            dashboard_key='portrait-service',
            metrics=[metric('Mission readiness', '0')],
            alerts=[
                alert(
                    'Mission metrics are temporarily using the safe fallback contract',
                    'Low',
                    'Live portrait or spiritual-life data was unavailable during this request.',
                )
            ],
            queue=[queue_item('Review mission readiness dashboard')],
            meta={
                'school_id': str(school_id),
                'served_from': 'sample',
                'certification_candidate': 'hybrid',
            },
        )
        payload['detail_metrics'] = {
            'approved_service_hours': 0.0,
            'pending_service_hours': 0.0,
            'portrait_completion_pct': 0.0,
            'mission_readiness_pct': 0.0,
            'source': 'sample',
        }
        return payload


def billing_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='billing',
        metrics=[
            metric('Invoices Issued This Month', '312'),
            metric('Outstanding Balances', '$47,820'),
            metric('Overdue Accounts', '18'),
            metric('Payments Collected Today', '$6,450'),
        ],
        alerts=[
            alert('18 accounts are 30+ days past due', 'High', 'Finance team follow-up required.'),
            alert('Tuition invoice run scheduled for tomorrow', 'Medium', 'Verify invoice batch before release.'),
            alert('3 ACH returns need resolution', 'Low', 'Check payment gateway for details.'),
        ],
        queue=[
            queue_item('Review overdue account list and assign follow-up'),
            queue_item('Approve tomorrow invoice batch before 8 AM'),
            queue_item('Resolve ACH return errors in payment gateway'),
            queue_item('Send monthly billing statement reminders'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def financial_aid_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='financial-aid',
        metrics=[
            metric('Active Aid Applications', '64'),
            metric('Approved Awards This Year', '$218,400'),
            metric('Pending Review', '11'),
            metric('Aid Disbursed YTD', '$189,700'),
        ],
        alerts=[
            alert('11 applications awaiting review committee decision', 'Medium', 'Committee meeting is Thursday.'),
            alert('2 approved awards pending final disbursement authorization', 'Low', 'CFO signature required.'),
        ],
        queue=[
            queue_item('Prepare review committee packet for Thursday'),
            queue_item('Obtain CFO authorization for pending disbursements'),
            queue_item('Notify families of award decisions within 5 business days'),
            queue_item('Update aid tracker with Q3 actuals'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def registrar_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='registrar',
        metrics=[
            metric('Total Enrolled', '487'),
            metric('Pending Registrations', '23'),
            metric('Withdrawn This Term', '4'),
            metric('Transcript Requests Open', '9'),
        ],
        alerts=[
            alert('23 new registrations awaiting document verification', 'High', 'Enrollment opens next week.'),
            alert('9 transcript requests have been open 5+ business days', 'Medium', 'Prioritize before grade closure.'),
            alert('4 student records have missing emergency contacts', 'Low', 'Parent portal reminder needed.'),
        ],
        queue=[
            queue_item('Complete document verification for new registrations'),
            queue_item('Process and close open transcript requests'),
            queue_item('Send missing emergency contact reminder to families'),
            queue_item('Confirm enrollment numbers with administration'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def scheduling_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='scheduling',
        metrics=[
            metric('Sections Scheduled', '142'),
            metric('Unresolved Conflicts', '6'),
            metric('Teacher Load Alerts', '3'),
            metric('Student Without Full Schedule', '14'),
        ],
        alerts=[
            alert('6 section conflicts require manual resolution', 'High', 'Affects student scheduling window.'),
            alert('3 teachers exceed recommended period load', 'Medium', 'Review with HR and academic dean.'),
            alert('14 students still missing elective selections', 'Low', 'Elective deadline is Friday.'),
        ],
        queue=[
            queue_item('Resolve 6 section scheduling conflicts'),
            queue_item('Review teacher load with academic dean'),
            queue_item('Contact families of students missing elective selections'),
            queue_item('Lock master schedule after conflict resolution'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def gradebook_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='gradebook',
        metrics=[
            metric('Grades Posted This Week', '1,204'),
            metric('Missing Grade Submissions', '37'),
            metric('Students Below 70%', '29'),
            metric('Academic Alerts Open', '12'),
        ],
        alerts=[
            alert('37 grades not posted by weekly deadline', 'High', 'Teacher follow-up required before Friday.'),
            alert('29 students below passing threshold', 'Medium', 'Intervention referrals may be needed.'),
            alert('12 academic alerts open with no assigned counselor', 'Low', 'Assign counselor support promptly.'),
        ],
        queue=[
            queue_item('Contact teachers with overdue grade submissions'),
            queue_item('Generate intervention list for students below 70%'),
            queue_item('Assign academic alert cases to counselors'),
            queue_item('Publish grade summary to administration'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def student_care_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='student-care',
        metrics=[
            metric('Open Care Cases', '18'),
            metric('Counseling Sessions This Week', '34'),
            metric('Referrals Pending', '5'),
            metric('At-Risk Students Monitored', '11'),
        ],
        alerts=[
            alert('5 referrals awaiting counselor acknowledgment', 'High', 'Respond within 24 hours per policy.'),
            alert('2 students flagged for attendance-related wellness check', 'Medium', 'Coordinate with attendance office.'),
            alert('11 at-risk students have upcoming academic reviews', 'Low', 'Schedule team meetings this week.'),
        ],
        queue=[
            queue_item('Acknowledge and assign pending referrals'),
            queue_item('Conduct wellness checks for attendance-flagged students'),
            queue_item('Schedule academic review meetings for at-risk group'),
            queue_item('Update care case notes before end of week'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def activities_athletics_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='activities-athletics',
        metrics=[
            metric('Active Clubs & Activities', '24'),
            metric('Student Participants', '318'),
            metric('Upcoming Events This Week', '7'),
            metric('Eligibility Flags', '5'),
        ],
        alerts=[
            alert('5 students flagged for academic eligibility review', 'High', 'Must clear before next game.'),
            alert('Varsity game venue confirmation pending for Friday', 'Medium', 'Contact facilities before Wednesday.'),
            alert('3 club rosters have not been submitted for the term', 'Low', 'Advisors need to submit by Friday.'),
        ],
        queue=[
            queue_item('Process academic eligibility reviews before Friday'),
            queue_item('Confirm Friday varsity game venue with facilities'),
            queue_item('Follow up with 3 club advisors on roster submissions'),
            queue_item('Post this week event schedule to parent portal'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def communications_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='communications',
        metrics=[
            metric('Messages Sent This Week', '1,847'),
            metric('Delivery Failures', '23'),
            metric('Open Rate (Last Blast)', '68%'),
            metric('Unread Inbox Items', '14'),
        ],
        alerts=[
            alert('23 parent messages failed delivery', 'High', 'Verify contact records and retry.'),
            alert('14 inbound messages unread for 24+ hours', 'Medium', 'Assign staff to clear inbox queue.'),
            alert('Next scheduled blast has no subject line set', 'Low', 'Complete draft before scheduled send.'),
        ],
        queue=[
            queue_item('Retry failed message deliveries and update contact records'),
            queue_item('Clear 14 unread inbox items'),
            queue_item('Finalize subject line for scheduled communication blast'),
            queue_item('Review weekly engagement metrics with admin team'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def school_administrator_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='school-administrator',
        metrics=[
            metric('Enrollment This Term', '487'),
            metric('Staff Headcount', '62'),
            metric('Open Action Items', '9'),
            metric('Days Until Term End', '47'),
        ],
        alerts=[
            alert('9 administrative action items require principal sign-off', 'High', 'Review pending approvals in queue.'),
            alert('Staff CPD hours are below target for 8 teachers', 'Medium', 'CPD deadline is end of term.'),
            alert('Facilities work order backlog exceeds 10 items', 'Low', 'Facilities director follow-up needed.'),
        ],
        queue=[
            queue_item('Review and sign off on 9 pending administrative items'),
            queue_item('Contact 8 teachers regarding CPD hour shortfall'),
            queue_item('Escalate facilities backlog to maintenance director'),
            queue_item('Confirm term-end communications schedule'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def master_control_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='master-control',
        metrics=[
            metric('Platform Uptime (30d)', '99.91%'),
            metric('Active Tenants', '51'),
            metric('Open Support Tickets', '7'),
            metric('Pending Data Migrations', '2'),
        ],
        alerts=[
            alert('2 tenant data migrations are stalled', 'High', 'Platform engineering must unblock by EOD.'),
            alert('7 open support tickets older than 48 hours', 'Medium', 'Support SLA at risk.'),
            alert('One tenant has an expired SSL certificate in 14 days', 'Low', 'Renew before expiration.'),
        ],
        queue=[
            queue_item('Unblock stalled tenant data migrations'),
            queue_item('Triage and resolve 48-hour+ support tickets'),
            queue_item('Initiate SSL certificate renewal for flagged tenant'),
            queue_item('Publish platform status update to all schools'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def admissions_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='admissions',
        metrics=[
            metric('Inquiries This Month', '84'),
            metric('Applications In Progress', '41'),
            metric('Accepted Applicants', '29'),
            metric('Enrolled from This Cohort', '22'),
        ],
        alerts=[
            alert('41 applications have not moved in 7+ days', 'Medium', 'Follow up with families to prevent drop-off.'),
            alert('Decision letters for 12 applicants are overdue', 'High', 'Send within 3 business days.'),
            alert('Open house registration is at 78% capacity', 'Low', 'Promote remaining spots before closing.'),
        ],
        queue=[
            queue_item('Send overdue decision letters to 12 applicants'),
            queue_item('Re-engage 41 stalled applicants via personal outreach'),
            queue_item('Promote remaining open house spots on social media'),
            queue_item('Update admissions funnel metrics for board report'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def advancement_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='advancement',
        metrics=[
            metric('Annual Fund Goal', '$250,000'),
            metric('Raised YTD', '$164,300'),
            metric('Donor Retention Rate', '61%'),
            metric('Gifts This Month', '47'),
        ],
        alerts=[
            alert('Annual fund is 34% below YTD pace to hit goal', 'High', 'Accelerate major donor outreach.'),
            alert('Spring gala sponsorship packages need final sign-off', 'Medium', 'Deadline is 2 weeks out.'),
            alert('Donor retention rate below 65% target', 'Low', 'Review lapsed donor reactivation plan.'),
        ],
        queue=[
            queue_item('Contact top 10 major donor prospects this week'),
            queue_item('Finalize and distribute spring gala sponsorship packages'),
            queue_item('Activate lapsed donor re-engagement campaign'),
            queue_item('Publish monthly advancement update to board'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def hr_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='hr',
        metrics=[
            metric('Total Staff', '62'),
            metric('Open Positions', '3'),
            metric('Background Checks Pending', '2'),
            metric('CPD Hours Behind Schedule', '8'),
        ],
        alerts=[
            alert('2 staff background checks are overdue', 'High', 'Must clear before next duty assignment.'),
            alert('3 open positions have no active candidate pipeline', 'Medium', 'Post roles and initiate sourcing.'),
            alert('8 staff CPD hours below required threshold for term', 'Low', 'Term deadline approaching.'),
        ],
        queue=[
            queue_item('Resolve 2 overdue background check submissions'),
            queue_item('Post 3 open roles and activate hiring pipeline'),
            queue_item('Notify 8 staff of CPD hour shortfall and deadline'),
            queue_item('Confirm annual performance review schedule'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def facilities_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='facilities',
        metrics=[
            metric('Open Work Orders', '14'),
            metric('Completed This Week', '9'),
            metric('Critical Safety Items', '1'),
            metric('Scheduled Inspections', '2'),
        ],
        alerts=[
            alert('1 critical safety work order unresolved for 3 days', 'High', 'Escalate immediately to principal.'),
            alert('2 state safety inspections scheduled for next week', 'Medium', 'Prepare inspection checklists.'),
            alert('HVAC maintenance in building C is overdue by 30 days', 'Low', 'Schedule before summer.'),
        ],
        queue=[
            queue_item('Resolve critical safety work order today'),
            queue_item('Prepare documentation for next week inspections'),
            queue_item('Schedule overdue HVAC maintenance for building C'),
            queue_item('Review and close 9 completed work orders'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def health_office_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='health-office',
        metrics=[
            metric('Student Visits Today', '12'),
            metric('Medication Administration Log', '8 doses'),
            metric('Immunization Compliance', '94%'),
            metric('Incident Reports This Month', '3'),
        ],
        alerts=[
            alert('6% of students have incomplete immunization records', 'Medium', 'Families need to submit by month-end.'),
            alert('1 incident report from yesterday requires follow-up note', 'High', 'Complete documentation within 24 hours.'),
            alert('Two student medication authorizations expire this week', 'Low', 'Request updated forms from families.'),
        ],
        queue=[
            queue_item('Complete incident report documentation'),
            queue_item('Send immunization compliance reminders to families'),
            queue_item('Request renewed medication authorization forms'),
            queue_item('Confirm medication log accuracy with nurse'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def transportation_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='transportation',
        metrics=[
            metric('Buses in Service', '8'),
            metric('Students on Routes', '213'),
            metric('Late Arrivals Today', '2'),
            metric('Maintenance Alerts', '1'),
        ],
        alerts=[
            alert('Bus #4 flagged for maintenance — tire inspection required', 'High', 'Do not deploy until cleared.'),
            alert('2 route delays reported this morning', 'Medium', 'Parent notifications may be needed.'),
            alert('3 student route assignments changed but not confirmed', 'Low', 'Confirm with families before tomorrow.'),
        ],
        queue=[
            queue_item('Take bus #4 out of service for tire inspection'),
            queue_item('Send parent communication for route delay'),
            queue_item('Confirm 3 updated route assignments with families'),
            queue_item('Submit weekly route log to transportation director'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def food_service_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='food-service',
        metrics=[
            metric('Meals Served Today', '421'),
            metric('Free & Reduced Eligible', '87'),
            metric('Balance Alerts (Low/Negative)', '22'),
            metric('Menu Compliance Rate', '98%'),
        ],
        alerts=[
            alert('22 student accounts have low or negative lunch balances', 'High', 'Notify families before lunch today.'),
            alert('Milk delivery short 30 units for tomorrow', 'Medium', 'Contact vendor to arrange replacement.'),
            alert('2 new students not yet set up in the meal system', 'Low', 'Complete onboarding before first meal service.'),
        ],
        queue=[
            queue_item('Send low balance alerts to 22 families'),
            queue_item('Contact milk vendor regarding short delivery'),
            queue_item('Onboard 2 new students into meal system'),
            queue_item('Submit daily meal count report to district'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def it_support_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='it-support',
        metrics=[
            metric('Open Help Desk Tickets', '19'),
            metric('Avg Resolution Time', '4.2 hrs'),
            metric('Devices Checked Out', '34'),
            metric('Critical System Alerts', '0'),
        ],
        alerts=[
            alert('19 open help desk tickets — 5 older than 48 hours', 'Medium', 'SLA target: 24-hour resolution.'),
            alert('Classroom projector in Room 211 reported down', 'High', 'Schedule repair before 1st period.'),
            alert('WiFi access point in gym wing showing intermittent drops', 'Low', 'Monitor or replace after school hours.'),
        ],
        queue=[
            queue_item('Repair or swap projector in Room 211 before first period'),
            queue_item('Resolve 5 tickets that exceeded 48-hour SLA'),
            queue_item('Investigate gym wing WiFi access point'),
            queue_item('Review and close resolved tickets in help desk system'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def fine_arts_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='fine-arts',
        metrics=[
            metric('Active Ensembles & Groups', '9'),
            metric('Students Enrolled in Fine Arts', '148'),
            metric('Upcoming Performances', '3'),
            metric('Budget Utilized YTD', '61%'),
        ],
        alerts=[
            alert('Spring concert program not finalized with 3 weeks out', 'High', 'Program must go to print by next week.'),
            alert('2 instrument repair requisitions pending approval', 'Medium', 'Approve before next rehearsal cycle.'),
            alert('Fine arts field trip permission slips are at 72% return', 'Low', 'Send final reminder to families.'),
        ],
        queue=[
            queue_item('Finalize spring concert program for printing'),
            queue_item('Approve pending instrument repair requisitions'),
            queue_item('Send field trip permission slip reminders'),
            queue_item('Confirm performance venue logistics with facilities'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def athletics_director_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='athletics-director',
        metrics=[
            metric('Active Varsity Programs', '12'),
            metric('Student Athletes', '187'),
            metric('Games This Week', '5'),
            metric('Eligibility Reviews Pending', '4'),
        ],
        alerts=[
            alert('4 student athletes pending eligibility clearance before Friday', 'High', 'Review academic records today.'),
            alert('Gym conflict with pep rally and JV practice on Thursday', 'Medium', 'Reschedule one event with facilities.'),
            alert('2 coaches missing annual safety certification renewal', 'Low', 'Submit documentation by end of month.'),
        ],
        queue=[
            queue_item('Clear 4 pending athletic eligibility reviews'),
            queue_item('Resolve Thursday gym scheduling conflict with facilities'),
            queue_item('Follow up with 2 coaches on safety certification renewal'),
            queue_item('Submit weekly game results to athletic association'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def library_media_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='library-media',
        metrics=[
            metric('Books Checked Out', '312'),
            metric('Overdue Items', '47'),
            metric('New Acquisitions This Term', '38'),
            metric('Student Visits This Week', '221'),
        ],
        alerts=[
            alert('47 overdue items — 12 over 30 days', 'Medium', 'Send overdue notices to families.'),
            alert('3 damaged items need replacement order', 'Low', 'Submit purchase requisition by Friday.'),
            alert('Digital media licenses expire in 30 days', 'High', 'Renew before access is cut off.'),
        ],
        queue=[
            queue_item('Renew expiring digital media licenses immediately'),
            queue_item('Send overdue notices for 47 outstanding items'),
            queue_item('Submit replacement purchase requisition for 3 damaged items'),
            queue_item('Update catalog with 38 new acquisitions'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def extended_care_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='extended-care',
        metrics=[
            metric('Students Enrolled in After Care', '94'),
            metric('Check-Ins Today', '87'),
            metric('Outstanding Balances', '$2,340'),
            metric('Staff On Duty Now', '6'),
        ],
        alerts=[
            alert('7 students checked in without pre-registration today', 'High', 'Verify guardian authorization.'),
            alert('$2,340 in unpaid after care balances', 'Medium', 'Send billing reminders before Friday.'),
            alert('One after care staff member called out — coverage is below ratio', 'High', 'Arrange substitute coverage.'),
        ],
        queue=[
            queue_item('Verify guardian authorization for 7 unregistered check-ins'),
            queue_item('Arrange substitute coverage for missing staff'),
            queue_item('Send after care billing reminders to families with balances'),
            queue_item('Submit daily headcount report'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def safety_security_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='safety-security',
        metrics=[
            metric('Visitor Badges Active Now', '4'),
            metric('Drills Completed This Year', '3'),
            metric('Open Safety Incidents', '1'),
            metric('Camera Systems Online', '98%'),
        ],
        alerts=[
            alert('1 safety incident report requires administrator review', 'High', 'Complete documentation within 24 hours.'),
            alert('Fire drill is overdue for this term', 'Medium', 'Schedule within the next 2 weeks.'),
            alert('2 exterior cameras showing offline status', 'Low', 'IT to investigate before end of week.'),
        ],
        queue=[
            queue_item('Complete safety incident documentation review'),
            queue_item('Schedule overdue fire drill with administration'),
            queue_item('Escalate offline camera issue to IT support'),
            queue_item('Confirm all visitor logs are current and complete'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def curriculum_pd_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='curriculum-pd',
        metrics=[
            metric('Active Curriculum Units', '86'),
            metric('PD Sessions Scheduled This Term', '12'),
            metric('Teacher Participation Rate', '89%'),
            metric('Curriculum Reviews Pending', '5'),
        ],
        alerts=[
            alert('5 curriculum units pending alignment review', 'Medium', 'Complete before next academic calendar lock.'),
            alert('11% of teachers have not registered for required PD session', 'High', 'Registration deadline is Friday.'),
            alert('2 PD facilitators have not confirmed availability', 'Low', 'Confirm or find replacements.'),
        ],
        queue=[
            queue_item('Follow up with unregistered teachers for PD session'),
            queue_item('Confirm facilitator availability for upcoming PD events'),
            queue_item('Complete 5 pending curriculum alignment reviews'),
            queue_item('Publish updated curriculum map to department chairs'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def chaplain_spiritual_life_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='chaplain-spiritual-life',
        metrics=[
            metric('Chapel Sessions This Term', '18'),
            metric('Student Service Hours YTD', '1,204'),
            metric('Spiritual Care Requests', '7'),
            metric('Mission Trip Applications', '34'),
        ],
        alerts=[
            alert('7 spiritual care referrals awaiting chaplain response', 'High', 'Respond within 48 hours per care policy.'),
            alert('Mission trip deposit deadline is in 5 days', 'Medium', 'Notify families of 34 applicants.'),
            alert('Chapel speaker for next week not yet confirmed', 'Low', 'Finalize by Wednesday.'),
        ],
        queue=[
            queue_item('Respond to 7 spiritual care referrals'),
            queue_item('Send mission trip deposit deadline reminders'),
            queue_item('Confirm chapel speaker for next week'),
            queue_item('Publish spiritual life calendar update to students'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def advancement_operations_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='advancement-operations',
        metrics=[
            metric('Active Grant Applications', '4'),
            metric('Alumni Engagement Events', '2'),
            metric('Donor Database Records', '1,847'),
            metric('Stewardship Reports Due', '3'),
        ],
        alerts=[
            alert('3 stewardship reports are past due date', 'High', 'Complete before donor meetings this week.'),
            alert('One grant application deadline is in 10 days', 'Medium', 'Final narrative review required.'),
            alert('87 donor records have incomplete contact information', 'Low', 'Update before next campaign.'),
        ],
        queue=[
            queue_item('Complete 3 overdue stewardship reports'),
            queue_item('Complete final review of grant application narrative'),
            queue_item('Update 87 incomplete donor records'),
            queue_item('Confirm logistics for alumni engagement events'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def volunteer_management_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='volunteer-management',
        metrics=[
            metric('Registered Volunteers', '142'),
            metric('Background Checks Current', '89%'),
            metric('Volunteer Hours This Month', '384'),
            metric('Open Volunteer Slots', '17'),
        ],
        alerts=[
            alert('16 volunteers have background checks expiring in 30 days', 'High', 'Send renewal notices now.'),
            alert('17 volunteer slots for spring events unfilled', 'Medium', 'Promote through parent communication.'),
            alert('Volunteer appreciation event planning not started', 'Low', 'Begin planning at least 4 weeks out.'),
        ],
        queue=[
            queue_item('Send background check renewal notices to 16 volunteers'),
            queue_item('Promote 17 open volunteer slots in parent newsletter'),
            queue_item('Start planning volunteer appreciation event'),
            queue_item('Export volunteer hours log for grant reporting'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def alumni_relations_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='alumni-relations',
        metrics=[
            metric('Alumni in Database', '2,341'),
            metric('Active Engagements YTD', '187'),
            metric('Alumni Giving Rate', '14%'),
            metric('Upcoming Reunion Events', '1'),
        ],
        alerts=[
            alert('Alumni giving rate is below 18% peer benchmark', 'Medium', 'Review engagement strategy with advancement.'),
            alert('Reunion event logistics not finalized — 8 weeks out', 'High', 'Complete venue and catering contracts.'),
            alert('342 alumni email addresses are bouncing', 'Low', 'Run record hygiene before next campaign.'),
        ],
        queue=[
            queue_item('Finalize reunion event venue and catering contracts'),
            queue_item('Review and refresh alumni engagement strategy'),
            queue_item('Clean 342 bouncing email records'),
            queue_item('Send class notes survey to recent graduates'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def network_benchmarking_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='network-benchmarking',
        metrics=[
            metric('Peer Schools Benchmarked', '21'),
            metric('Crown Schools Above Median', '14'),
            metric('KPIs Tracked', '38'),
            metric('Last Data Refresh', 'April 2026'),
        ],
        alerts=[
            alert('7 Crown schools are below peer median in 3+ KPIs', 'Medium', 'Schedule support review calls.'),
            alert('Benchmarking data refresh is 45 days overdue', 'High', 'Initiate data collection from peer network.'),
            alert('2 schools have not submitted their term data package', 'Low', 'Follow up with school contacts.'),
        ],
        queue=[
            queue_item('Initiate overdue benchmarking data refresh cycle'),
            queue_item('Schedule support reviews for 7 below-median schools'),
            queue_item('Follow up with 2 schools on missing data packages'),
            queue_item('Publish updated benchmarking report to school leaders'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def compliance_audit_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='compliance-audit',
        metrics=[
            metric('Open Compliance Items', '11'),
            metric('Audits Completed This Year', '4'),
            metric('Policies Reviewed', '23'),
            metric('Training Completion Rate', '87%'),
        ],
        alerts=[
            alert('3 compliance items are past due by 14+ days', 'High', 'Escalate to administration immediately.'),
            alert('Annual policy review is 60% complete — deadline in 30 days', 'Medium', 'Accelerate review sessions.'),
            alert('13% of staff have not completed required compliance training', 'Low', 'Final reminder before enforcement date.'),
        ],
        queue=[
            queue_item('Escalate 3 overdue compliance items to administration'),
            queue_item('Schedule remaining policy review sessions before deadline'),
            queue_item('Send final compliance training reminders to staff'),
            queue_item('Publish compliance status report to board'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def dashboard_certification_center_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='dashboard-certification-center',
        metrics=[
            metric('Dashboards Certified', '0'),
            metric('Mapped Only', '40'),
            metric('Pending Independent Review', '0'),
            metric('Cert Rate', '0%'),
        ],
        alerts=[
            alert(
                'No dashboards are certified yet',
                'High',
                'Current verified state remains 40 mapped dashboards and 0 live-data certified dashboards.',
            ),
            alert(
                'Owner and independent reviewer are still TBD',
                'High',
                'Assign governance roles before certification promotion.',
            ),
        ],
        queue=[
            queue_item('Assign dashboard certification owner'),
            queue_item('Assign independent dashboard certification reviewer'),
            queue_item('Wire certification proof state from the dashboard matrix'),
            queue_item('Attach permission, tenant, and runtime proof'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def revenue_operations_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='revenue-operations',
        metrics=[
            metric('Total Revenue YTD', '$2.4M'),
            metric('Collections Rate', '91%'),
            metric('Outstanding AR', '$214,000'),
            metric('Revenue vs Budget', '+2.3%'),
        ],
        alerts=[
            alert('$214K in outstanding receivables aging beyond 60 days', 'High', 'Initiate collections workflow.'),
            alert('3 tuition plans have lapsed without renegotiation', 'Medium', 'Finance team to contact families.'),
            alert('Month-end close is scheduled for Friday — reconciliation needed', 'Low', 'Ensure all entries are posted.'),
        ],
        queue=[
            queue_item('Initiate collections workflow for 60+ day AR'),
            queue_item('Contact families with lapsed tuition plans'),
            queue_item('Complete month-end reconciliation before Friday close'),
            queue_item('Submit revenue variance analysis to CFO'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def implementation_success_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='implementation-success',
        metrics=[
            metric('Schools in Active Onboarding', '7'),
            metric('Go-Lives This Quarter', '3'),
            metric('Open Implementation Tickets', '14'),
            metric('Avg Onboarding Days', '42'),
        ],
        alerts=[
            alert('2 onboarding schools are behind schedule by 2+ weeks', 'High', 'Escalate to implementation lead.'),
            alert('14 open implementation tickets — 5 blocking go-live', 'High', 'Clear blockers before next launch date.'),
            alert('1 school has not completed required data migration', 'Medium', 'Data cutover is in 10 days.'),
        ],
        queue=[
            queue_item('Escalate 2 behind-schedule onboarding schools'),
            queue_item('Resolve 5 go-live blocking tickets'),
            queue_item('Complete data migration for school at cutover risk'),
            queue_item('Publish weekly implementation status to leadership'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def integrations_automation_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='integrations-automation',
        metrics=[
            metric('Active Integrations', '18'),
            metric('Sync Errors (Last 24h)', '3'),
            metric('Automations Running', '27'),
            metric('Last Successful Sync', '14 min ago'),
        ],
        alerts=[
            alert('3 integration sync errors in the last 24 hours', 'High', 'Review integration log for root cause.'),
            alert('SIS → Crown data sync is 6 hours behind schedule', 'Medium', 'Trigger manual sync if automated job stalled.'),
            alert('API rate limit warning from one partner service', 'Low', 'Review call volume and apply throttling.'),
        ],
        queue=[
            queue_item('Investigate and resolve 3 integration sync errors'),
            queue_item('Trigger manual SIS sync if automated job is stalled'),
            queue_item('Apply rate-limit throttling to partner service calls'),
            queue_item('Review integration health dashboard with engineering'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


def data_migration_sample_payload(school_id):
    return build_dashboard_payload(
        dashboard_key='data-migration',
        metrics=[
            metric('Active Migration Jobs', '2'),
            metric('Records Migrated YTD', '48,302'),
            metric('Failed Records', '14'),
            metric('Validation Errors', '6'),
        ],
        alerts=[
            alert('14 records failed migration and need manual review', 'High', 'Resolve before next sync window.'),
            alert('6 data validation errors blocking student import', 'High', 'Fix source data format before retry.'),
            alert('Migration job for school B has not run in 24 hours', 'Medium', 'Check job scheduler health.'),
        ],
        queue=[
            queue_item('Manually review and resolve 14 failed migration records'),
            queue_item('Fix 6 source data validation errors and retry import'),
            queue_item('Investigate stalled migration job for school B'),
            queue_item('Publish migration status report to implementation team'),
        ],
        meta={'school_id': str(school_id), 'served_from': 'sample'},
    )


SAMPLE_PAYLOAD_BUILDERS = {
    'attendance': attendance_sample_payload,
    'release-reliability': release_reliability_sample_payload,
    'school-board': school_board_sample_payload,
    'portrait-service': portrait_service_sample_payload,
    # Tier 1
    'billing': billing_sample_payload,
    'financial-aid': financial_aid_sample_payload,
    'registrar': registrar_sample_payload,
    # Tier 2
    'scheduling': scheduling_sample_payload,
    'gradebook': gradebook_sample_payload,
    'student-care': student_care_sample_payload,
    'activities-athletics': activities_athletics_sample_payload,
    'communications': communications_sample_payload,
    # Tier 3
    'school-administrator': school_administrator_sample_payload,
    'master-control': master_control_sample_payload,
    'admissions': admissions_sample_payload,
    'advancement': advancement_sample_payload,
    # Tier 4
    'hr': hr_sample_payload,
    'facilities': facilities_sample_payload,
    'health-office': health_office_sample_payload,
    'transportation': transportation_sample_payload,
    'food-service': food_service_sample_payload,
    'it-support': it_support_sample_payload,
    # Tier 5
    'fine-arts': fine_arts_sample_payload,
    'athletics-director': athletics_director_sample_payload,
    'library-media': library_media_sample_payload,
    'extended-care': extended_care_sample_payload,
    'safety-security': safety_security_sample_payload,
    'curriculum-pd': curriculum_pd_sample_payload,
    # Tier 6
    'chaplain-spiritual-life': chaplain_spiritual_life_sample_payload,
    'advancement-operations': advancement_operations_sample_payload,
    'volunteer-management': volunteer_management_sample_payload,
    'alumni-relations': alumni_relations_sample_payload,
    'network-benchmarking': network_benchmarking_sample_payload,
    # Platform
    'dashboard-certification-center': dashboard_certification_center_sample_payload,
    'compliance-audit': compliance_audit_sample_payload,
    'revenue-operations': revenue_operations_sample_payload,
    'implementation-success': implementation_success_sample_payload,
    'integrations-automation': integrations_automation_sample_payload,
    'data-migration': data_migration_sample_payload,
}
