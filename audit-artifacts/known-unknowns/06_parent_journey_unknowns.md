=== PARENT JOURNEY UNKNOWNS ===
## Parent route/guard references
backend/parent360\tests\test_parent_overview_api.py:18:PARENT360_V1_URL = "/api/v1/parent360/me/overview/"
backend/parent360\tests\test_parent_overview_api.py:19:PARENT360_URL = "/api/parent360/me/overview/"
backend/parent360\tests\test_parent_overview_api.py:22:def _make_parent_client(*, school: School, email: str = "parent@example.com"):
backend/parent360\tests\test_parent_overview_api.py:24:        username=f"parent-{school.id}",
backend/parent360\tests\test_parent_overview_api.py:39:    email: str = "parent@example.com",
backend/parent360\tests\test_parent_overview_api.py:140:def test_parent_self_overview_v1_route_returns_200_and_household_shape():
backend/parent360\tests\test_parent_overview_api.py:142:    client, _ = _make_parent_client(school=school)
backend/parent360\tests\test_parent_overview_api.py:155:def test_parent_self_overview_rejects_foreign_school_guardian_email_match():
backend/parent360\tests\test_parent_overview_api.py:158:    email = "shared-parent@example.com"
backend/parent360\tests\test_parent_overview_api.py:161:    client, _ = _make_parent_client(school=school, email=email)
backend/parent360\tests\test_parent_overview_api.py:168:def test_parent_self_overview_service_hours_do_not_bridge_across_schools():
backend/parent360\tests\test_parent_overview_api.py:171:    client, _ = _make_parent_client(school=school, email="service-parent@example.com")
backend/parent360\tests\test_parent_overview_api.py:174:        email="service-parent@example.com",
backend/parent360\tests\test_parent_overview_api.py:193:def test_parent_self_overview_ignores_assignments_for_unenrolled_sections():
backend/parent360\tests\test_parent_overview_api.py:195:    client, _ = _make_parent_client(school=school, email="assignments-parent@example.com")
backend/parent360\tests\test_parent_overview_api.py:198:        email="assignments-parent@example.com",
backend/parent360\api\urls.py:5:    path("me/overview/", ParentSelfOverview.as_view(), name="parent_360_self"),
frontend/dashboards/src/routes\router.jsx:23:import ParentDashboard from "../pages/ParentDashboard.jsx";
frontend/dashboards/src/routes\router.jsx:65:import RoleGuard from "./RoleGuard.jsx";
frontend/dashboards/src/routes\router.jsx:146:    // Unified role dashboard ∩┐╜ /dash/admin, /dash/teacher, /dash/parent, etc.
frontend/dashboards/src/routes\router.jsx:232:  // Contract-preserving parent alias routes.
frontend/dashboards/src/routes\router.jsx:235:    path: '/parent/attendance',
frontend/dashboards/src/routes\router.jsx:239:    path: '/parent/communications',
frontend/dashboards/src/routes\router.jsx:243:    path: '/parent/schedule',
frontend/dashboards/src/routes\router.jsx:250:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src/routes\router.jsx:252:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:256:    path: '/parent',
frontend/dashboards/src/routes\router.jsx:257:    element: <ParentDashboard />,
frontend/dashboards/src/routes\router.jsx:260:    path: '/parent/dashboard',
frontend/dashboards/src/routes\router.jsx:261:    element: <ParentDashboard />,
frontend/dashboards/src/routes\router.jsx:278:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src/routes\router.jsx:280:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:286:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src/routes\router.jsx:288:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:294:      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
frontend/dashboards/src/routes\router.jsx:296:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:302:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src/routes\router.jsx:304:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:351:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src/routes\router.jsx:353:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:359:      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
frontend/dashboards/src/routes\router.jsx:361:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:367:      <RoleGuard allowedRoles={ROLE_GROUPS.FAMILY_VIEW}>
frontend/dashboards/src/routes\router.jsx:369:      </RoleGuard>
frontend/dashboards/src/routes\router.jsx:377:    path: '/parent/students/:id',
frontend/dashboards/src/routes\router.jsx:606:          "parent",
frontend/dashboards/src/routes\router.jsx:621:          "parent",
frontend/dashboards/src/routes\routeGroups.js:7:    'parent',
frontend/dashboards/src/routes\routeGroups.js:18:  FAMILY_VIEW: ['parent', 'student'],
frontend/dashboards/src/routes\RoleGuard.jsx:6:export default function RoleGuard({ allowedRoles = [], children }) {
frontend/dashboards/src/routes\paths.js:52:  PARENT_ATTENDANCE: '/parent/attendance',
frontend/dashboards/src/routes\paths.js:55:  PARENT: '/parent',
frontend/dashboards/src/routes\paths.js:65:  ACADEMICS_PARENT_SNAPSHOT: '/academics/parent-snapshot',
frontend/dashboards/src/routes\paths.js:67:  PARENT_STUDENT_DETAIL: '/parent/students/:id',
frontend/dashboards/src/routes\financeRouteAccess.test.jsx:52:  it("blocks parent and student roles from finance routes", () => {
frontend/dashboards/src/routes\financeRouteAccess.test.jsx:53:    expect(canAccess(["parent"], financeRoutes[0].allowedRoles)).toBe(false);
backend/crown_api\api_urls.py:31:    teacher_metrics, parent_metrics, student_metrics,
backend/crown_api\api_urls.py:57:from apps.compliance.api.parent_rights import ParentDataRightsRequestView
backend/crown_api\api_urls.py:62:    path('compliance/parent-rights/', ParentDataRightsRequestView.as_view(), name='parent-rights'),
backend/crown_api\api_urls.py:68:    path('parent/metrics/',         parent_metrics,         name='parent-metrics'),
backend/crown_api\api_v1_urls.py:74:    path("parent360/", include("parent360.api.urls")),
backend/crown_api\authenticated_contract_probe.py:10:ROOT = Path(__file__).resolve().parents[2]
backend/crown_api\health_views.py:28:        version_path = Path(__file__).resolve().parents[2] / "VERSION"
backend/crown_api\financial_aid_views.py:129:            | Q(family__parent_email__icontains=q)
backend/crown_api\financial_aid_views.py:153:            | Q(family__parent_email__icontains=q)
frontend/dashboards/src/routes\compuwerxRouteAccess.test.jsx:17:  it("blocks parent", () => {
frontend/dashboards/src/routes\compuwerxRouteAccess.test.jsx:18:    expect(canAccess(["parent"], route.allowedRoles)).toBe(false);
frontend/dashboards/src/routes\compuwerxPackage4RouteAccess.test.jsx:14:  it("blocks parent", () => {
frontend/dashboards/src/routes\compuwerxPackage4RouteAccess.test.jsx:15:    expect(canAccess(["parent"], financeOnly)).toBe(false);
frontend/dashboards/src/routes\compuwerxPackage3RouteAccess.test.jsx:8:  "parent",
frontend/dashboards/src/routes\compuwerxPackage3RouteAccess.test.jsx:20:  it("admits parent only to household-linked routes", () => {
frontend/dashboards/src/routes\compuwerxPackage3RouteAccess.test.jsx:21:    expect(canAccess(["parent"], householdRoutes)).toBe(true);
frontend/dashboards/src/routes\compuwerxPackage3RouteAccess.test.jsx:22:    expect(canAccess(["parent"], financeOnly)).toBe(false);
backend/crown_api\director_views.py:84:def build_director_priority_snapshot(school_id, academic_year):
backend/crown_api\director_views.py:86:    Build a lightweight snapshot of priority items for the UI.
backend/crown_api\director_views.py:995:                "priority_refresh": build_director_priority_snapshot(school_id, academic_year),
backend/crown_api\director_views.py:1058:                "priority_refresh": build_director_priority_snapshot(school_id, academic_year),
frontend/dashboards/src/routes\compuwerxOpsRouteAccess.test.jsx:29:  it("blocks parent for every route", () => {
frontend/dashboards/src/routes\compuwerxOpsRouteAccess.test.jsx:31:      expect(canAccess(["parent"], route.allowedRoles)).toBe(false);
backend/crown_api\dashboards\views.py:141:        snapshot = DashboardSnapshot.objects.filter(
backend/crown_api\dashboards\views.py:146:        if snapshot:
backend/crown_api\dashboards\views.py:147:            payload = deepcopy(snapshot.payload or {})
backend/crown_api\dashboards\views.py:149:            payload['meta']['served_from'] = 'snapshot'
backend/crown_api\dashboards\views.py:150:            payload['meta']['snapshot_updated_at'] = snapshot.updated_at.isoformat()
backend/crown_api\dashboards\views.py:151:            payload['meta']['snapshot_source'] = snapshot.source
backend/crown_api\dashboards\academics.py:3:Returns enrollment snapshot: student count + sections count
backend/crown_api\dashboards\summary.py:37:        "parent": [
backend/crown_api\dashboards\summary.py:38:            {"label": "View child's grades", "to": "/parent"},
backend/crown_api\dashboards\summary.py:39:            {"label": "View attendance", "to": "/parent/attendance"},
backend/crown_api\dashboards\summary.py:85:def _enrollment_snapshot(school_id: str) -> dict:
backend/crown_api\dashboards\summary.py:92:        logger.debug("enrollment_snapshot: graceful stub (households.Student unavailable)", exc_info=True)
backend/crown_api\dashboards\summary.py:124:    Phase A stub ΓÇö family balance for parent view.
backend/crown_api\dashboards\summary.py:131:    """Phase A stub ΓÇö 6-week grade trend for parent/student views."""
backend/crown_api\dashboards\summary.py:151:def _ar_snapshot(school_id: str) -> dict:
backend/crown_api\dashboards\summary.py:248:            {"key": "enrollment_snapshot", "type": "stat", "title": "Enrollment",
backend/crown_api\dashboards\summary.py:249:             "size": "sm", "priority": 30, "data": _enrollment_snapshot(school_id)},
backend/crown_api\dashboards\summary.py:271:    if role == "parent":
backend/crown_api\dashboards\summary.py:295:             "size": "sm", "priority": 35, "data": _ar_snapshot(school_id),
backend/crown_api\dashboards\sample_payloads.py:25:                'Two parent outreach messages bounced',
backend/crown_api\dashboards\sample_payloads.py:32:            queue_item('Send parent outreach for chronic absence group'),
backend/crown_api\dashboards\sample_payloads.py:381:            queue_item('Post this week event schedule to parent portal'),
backend/crown_api\dashboards\sample_payloads.py:397:            alert('23 parent messages failed delivery', 'High', 'Verify contact records and retry.'),
backend/crown_api\dashboards\sample_payloads.py:595:            queue_item('Send parent communication for route delay'),
backend/crown_api\dashboards\sample_payloads.py:854:            alert('17 volunteer slots for spring events unfilled', 'Medium', 'Promote through parent communication.'),
backend/crown_api\dashboards\sample_payloads.py:859:            queue_item('Promote 17 open volunteer slots in parent newsletter'),
backend/crown_api\migrations\0012_dashboard_snapshot.py:24:                'db_table': 'dashboard_snapshots',
backend/crown_api\migrations\0012_dashboard_snapshot.py:30:            model_name='dashboardsnapshot',
backend/crown_api\dashboards\models.py:14:        db_table = 'dashboard_snapshots'
backend/crown_api\lifecycle_contract_probe.py:13:ROOT = Path(__file__).resolve().parents[2]
backend/crown_api\metrics_views.py:66:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:108:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:150:            "snapshot_date": _today(),
backend/crown_api\metrics_views.py:171:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:176:@require_permission("parent.view")
backend/crown_api\metrics_views.py:177:def parent_metrics(request):
backend/crown_api\metrics_views.py:205:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:212:    """Student dashboard ΓÇö today's schedule, assignments due, grade snapshot."""
backend/crown_api\metrics_views.py:218:        "grade_snapshot": [
backend/crown_api\metrics_views.py:229:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:254:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:281:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:310:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:335:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:367:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:404:            {"label": "1 pending parent callback ΓÇö Sofia Medina",            "severity": "yellow"},
backend/crown_api\metrics_views.py:407:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:440:            {"label": "Tyler Green ΓÇö 3rd truancy, parent meeting needed",            "severity": "red"},
backend/crown_api\metrics_views.py:444:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:487:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:524:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:563:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:591:            {"label": "Route 3 running 12 min late ΓÇö parents notified",        "severity": "yellow"},
backend/crown_api\metrics_views.py:596:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:636:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:671:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:714:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:726:        "parent_volunteers":      22,
backend/crown_api\metrics_views.py:751:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:792:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:830:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:870:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:908:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:946:        "snapshot_date": _today(),
backend/crown_api\metrics_views.py:989:        "snapshot_date": _today(),
backend/crown_api\dashboards\migrations\0001_dashboard_snapshot.py:24:                'db_table': 'dashboard_snapshots',
backend/crown_api\dashboards\migrations\0001_dashboard_snapshot.py:30:            model_name='dashboardsnapshot',
backend/crown_api\write_contract_probe.py:16:ROOT = Path(__file__).resolve().parents[2]
backend/crown_api\dashboards\management\commands\seed_dashboard_snapshots.py:11:    help = 'Seed dashboard snapshot records for attendance and release reliability.'
backend/crown_api\dashboards\management\commands\seed_dashboard_snapshots.py:18:            help='School identifier for school-scoped dashboard snapshots.',
backend/crown_api\dashboards\management\commands\seed_dashboard_snapshots.py:34:                'notes': 'Seeded attendance reference snapshot.',
backend/crown_api\dashboards\management\commands\seed_dashboard_snapshots.py:48:                'notes': 'Seeded release reliability reference snapshot.',
backend/crown_api\dashboards\management\commands\seed_dashboard_snapshots.py:53:            f'Seeded dashboard snapshots for school_id="{school_id}".'
backend/crown_api\scoping_students.py:7:Uses HouseholdFamilyLink to link families to households for parent scoping.
backend/crown_api\settings.py.phase9_backup_20260508_172117:47:BASE_DIR = Path(__file__).resolve().parent.parent
backend/crown_api\settings.py.phase9_backup_20260508_172117:220:    'parent360',
backend/crown_api\settings.py.phase9_backup_20260508_172117:634:if str(BASE_DIR.parent) not in sys.path:
backend/crown_api\settings.py.phase9_backup_20260508_172117:635:    sys.path.append(str(BASE_DIR.parent))
backend/crown_api\management\commands\proof_phase4_gradebook_demo.py:2:Phase 4 demo-token API proof: parent gradebook endpoint.
backend/crown_api\management\commands\proof_phase4_gradebook_demo.py:35:    help = "Phase 4 demo-token API proof: gradebook parent endpoint returns demo payload (Alex Demo)"
backend/crown_api\management\commands\proof_phase4_gradebook_demo.py:83:            "Alex Demo student not found. Run seed_demo_parent_gradebook first.",
backend/crown_api\management\commands\proof_phase4_gradebook_demo.py:100:        # Step 2: call parent grades endpoint
backend/crown_api\views_integrity.py:61:        version_path = Path(__file__).resolve().parents[2] / "VERSION"
backend/crown_api\settings.py.phase9_backup_20260508_155955:47:BASE_DIR = Path(__file__).resolve().parent.parent
backend/crown_api\settings.py.phase9_backup_20260508_155955:204:    'parent360',
backend/crown_api\settings.py.phase9_backup_20260508_155955:618:if str(BASE_DIR.parent) not in sys.path:
backend/crown_api\settings.py.phase9_backup_20260508_155955:619:    sys.path.append(str(BASE_DIR.parent))
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:2:Seed deterministic parent-gradebook demo data.
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:15:  python manage.py seed_demo_parent_gradebook [--verbose]
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:36:    help = "Seed deterministic parent-gradebook demo data (Alex Demo, idempotent)"
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:55:        log(f"seed_demo_parent_gradebook: school_id={school.id}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:62:        log(f"seed_demo_parent_gradebook: household_id={household.pk}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:80:        log(f"seed_demo_parent_gradebook: student_id={student.pk}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:88:        log(f"seed_demo_parent_gradebook: course_id={course.pk}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:96:        log(f"seed_demo_parent_gradebook: section_id={section.pk}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:104:        log(f"seed_demo_parent_gradebook: enrollment_id={enrollment.pk}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:119:            log(f"seed_demo_parent_gradebook: grade_entry '{name}' {'created' if created else 'exists'}")
backend/crown_api\management\commands\seed_demo_parent_gradebook.py:122:            f"seed_demo_parent_gradebook: OK  student_id={student.pk}"
backend/crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:47:BASE_DIR = Path(__file__).resolve().parent.parent
backend/crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:220:    'parent360',
backend/crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:634:if str(BASE_DIR.parent) not in sys.path:
backend/crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:635:    sys.path.append(str(BASE_DIR.parent))
backend/crown_api\management\commands\seed_dashboard_snapshots.py:1:from crown_api.dashboards.management.commands.seed_dashboard_snapshots import Command
backend/crown_api\management\commands\reset_demo_passwords.py:14:    {"username": "parent", "email": "parent@crown-demo.local", "role_code": "PARENT"},
backend/crown_api\management\commands\reset_demo_passwords.py:81:            f"Created missing teacher/parent users: {created}."
backend/crown_api\settings.py:47:BASE_DIR = Path(__file__).resolve().parent.parent
backend/crown_api\settings.py:213:    'parent360',
backend/crown_api\settings.py:627:if str(BASE_DIR.parent) not in sys.path:
backend/crown_api\settings.py:628:    sys.path.append(str(BASE_DIR.parent))
backend/crown_api\views_billing.py:50:    # Force 404 if household doesn't exist at all (staff or in-scope parent)
backend/crown_api\seeded_contract_probe.py:12:ROOT = Path(__file__).resolve().parents[2]
backend/crown_api\tests\test_dashboard_snapshot_summary_api.py:11:def test_attendance_summary_serves_snapshot_first():
backend/crown_api\tests\test_dashboard_snapshot_summary_api.py:16:        notes='test snapshot',
backend/crown_api\tests\test_dashboard_snapshot_summary_api.py:20:            'alerts': [{'title': 'Snapshot Alert', 'level': 'High', 'secondary': 'snapshot'}],
backend/crown_api\tests\test_dashboard_snapshot_summary_api.py:22:            'meta': {'served_from': 'snapshot'},
backend/crown_api\tests\test_dashboard_snapshot_summary_api.py:35:    assert data['meta']['served_from'] == 'snapshot'
backend/crown_api\version_views.py:29:        version_path = Path(__file__).resolve().parents[2] / "VERSION"
backend/crown_api\version_view.py:19:        version_path = Path(__file__).resolve().parents[2] / "VERSION"
backend/crown_api\tests\test_students_api.py:25:        self.parent_user = UserAccount.objects.create_user(
backend/crown_api\tests\test_students_api.py:26:            username="parentuser",
backend/crown_api\tests\test_students_api.py:27:            email="parent@example.com",
backend/crown_api\tests\test_students_api.py:33:        UserRole.objects.create(user=self.parent_user, school=self.school, role_code="PARENT")
backend/crown_api\tests\test_students_api.py:45:        # Guardian for household_a matching parent_user email
backend/crown_api\tests\test_students_api.py:46:        self.parent_guardian = Guardian.objects.create(
backend/crown_api\tests\test_students_api.py:51:            email="parent@example.com",
backend/crown_api\tests\test_students_api.py:81:    def test_list_students_parent_scoped_to_household(self):
backend/crown_api\tests\test_students_api.py:83:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_students_api.py:89:    def test_student_detail_parent_out_of_scope_404(self):
backend/crown_api\tests\test_students_api.py:91:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\fixtures\rbac_endpoints_readonly.txt:20:/api/v1/board/snapshots/
backend/crown_api\tests\test_comms_api.py:38:        self.parent_user = UserAccount.objects.create_user(
backend/crown_api\tests\test_comms_api.py:39:            username="parentuser",
backend/crown_api\tests\test_comms_api.py:40:            email="parent@example.com",
backend/crown_api\tests\test_comms_api.py:49:        self.parent_person = Person.objects.create(
backend/crown_api\tests\test_comms_api.py:52:            email="parent@example.com",
backend/crown_api\tests\test_comms_api.py:54:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend/crown_api\tests\test_comms_api.py:57:            person=self.parent_person,
backend/crown_api\tests\test_comms_api.py:105:            created_by=self.parent_person,
backend/crown_api\tests\test_comms_api.py:112:            created_by=self.parent_person,
backend/crown_api\tests\test_comms_api.py:130:        self._add_messages(self.thread_a_household, self.parent_person, _dt(2026, 1, 2, 12, 0))
backend/crown_api\tests\test_comms_api.py:131:        self._add_messages(self.thread_a_student, self.parent_person, _dt(2026, 1, 3, 12, 0))
backend/crown_api\tests\test_comms_api.py:179:    def test_threads_list_parent_scoped_to_household(self):
backend/crown_api\tests\test_comms_api.py:180:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_comms_api.py:189:    def test_thread_detail_parent_in_scope_200(self):
backend/crown_api\tests\test_comms_api.py:190:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_comms_api.py:194:    def test_thread_detail_parent_out_of_scope_404(self):
backend/crown_api\tests\test_comms_api.py:195:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_metrics_permissions_contract.py:50:    ("parent",           "/api/v1/parent/metrics/"),
backend/crown_api\tests\test_seed_edge_cases.py:30:    "/api/v1/board/snapshots/",
backend/crown_api\tests\test_billing_summary_api.py:27:        self.parent_user = UserAccount.objects.create_user(
backend/crown_api\tests\test_billing_summary_api.py:28:            username="parentuser",
backend/crown_api\tests\test_billing_summary_api.py:29:            email="parent@example.com",
backend/crown_api\tests\test_billing_summary_api.py:38:        self.parent_person = Person.objects.create(
backend/crown_api\tests\test_billing_summary_api.py:41:            email="parent@example.com",
backend/crown_api\tests\test_billing_summary_api.py:43:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend/crown_api\tests\test_billing_summary_api.py:46:            person=self.parent_person,
backend/crown_api\tests\test_billing_summary_api.py:100:    def test_parent_scoped_and_no_existence_leak(self):
backend/crown_api\tests\test_billing_summary_api.py:101:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_scheduling_api.py:27:        self.parent_user = UserAccount.objects.create_user(
backend/crown_api\tests\test_scheduling_api.py:28:            username="parentuser",
backend/crown_api\tests\test_scheduling_api.py:29:            email="parent@example.com",
backend/crown_api\tests\test_scheduling_api.py:38:        self.parent_person = Person.objects.create(
backend/crown_api\tests\test_scheduling_api.py:41:            email="parent@example.com",
backend/crown_api\tests\test_scheduling_api.py:43:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend/crown_api\tests\test_scheduling_api.py:46:            person=self.parent_person,
backend/crown_api\tests\test_scheduling_api.py:76:        # Link families to households for parent scoping
backend/crown_api\tests\test_scheduling_api.py:103:        # for parent schedule scoping (replaces AdmissionsApplication bridge)
backend/crown_api\tests\test_scheduling_api.py:164:        # Enroll student_b into math_b so staff sees it, parent does not
backend/crown_api\tests\test_scheduling_api.py:185:    def test_parent_scoped_terms_sections_and_schedule(self):
backend/crown_api\tests\test_scheduling_api.py:186:        self.client.force_authenticate(user=self.parent_user)
frontend/dashboards/src/pages\billing_wizard\Step1Mode.jsx:91:                  background: mode === billingModeOption.value ? "var(--crown-surface-2)" : "transparent",
backend/crown_api\tests\test_rbac_matrix_readonly.py:25:FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rbac_endpoints_readonly.txt"
backend/crown_api\tests\test_rbac_matrix_readonly.py:99:    "/api/v1/board/snapshots/",
backend/crown_api\tests\test_academics_api.py:35:        self.parent_user = UserAccount.objects.create_user(
backend/crown_api\tests\test_academics_api.py:36:            username="parentuser",
backend/crown_api\tests\test_academics_api.py:37:            email="parent@example.com",
backend/crown_api\tests\test_academics_api.py:46:        self.parent_person = Person.objects.create(
backend/crown_api\tests\test_academics_api.py:49:            email="parent@example.com",
backend/crown_api\tests\test_academics_api.py:51:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend/crown_api\tests\test_academics_api.py:54:            person=self.parent_person,
backend/crown_api\tests\test_academics_api.py:84:        # Link families to households for parent scoping
backend/crown_api\tests\test_academics_api.py:112:        # for parent attendance/grades scoping (replaces AdmissionsApplication bridge)
backend/crown_api\tests\test_academics_api.py:165:    def test_attendance_parent_scoped_and_no_existence_leak(self):
backend/crown_api\tests\test_academics_api.py:166:        self.client.force_authenticate(user=self.parent_user)
backend/crown_api\tests\test_academics_api.py:186:    def test_grades_parent_scoped_and_no_existence_leak(self):
backend/crown_api\tests\test_academics_api.py:187:        self.client.force_authenticate(user=self.parent_user)
frontend/dashboards/src/pages\AdmissionsPipelineList.jsx:11:const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\AdmissionsPipelineList.jsx:13:const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\AdmissionsDashboard.jsx:187:      title: 'Inquiry to enrolled funnel snapshot',
frontend/dashboards/src/pages\BellScheduleWizard.jsx:11: *   3. Done       ? commit result: schedule_id, template_count, snapshot
frontend/dashboards/src/pages\AcademicSupportDashboard.jsx:23:  snapshot_date: 'Feb 26, 2026',
frontend/dashboards/src/pages\AcademicSupportDashboard.jsx:112:      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
frontend/dashboards/src/pages\AftercareRosterPage.jsx:15:const BTN_OUT = { cursor: "pointer", padding: "4px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--crown-border)", background: "transparent" };
frontend/dashboards/src/pages\ClassroomsDashboard.jsx:23:    definition: "Active classroom announcements published to students and parents this week.",
frontend/dashboards/src/pages\CommunicationsThreadsList.jsx:10:const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\CommunicationsThreadsList.jsx:12:const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\AcademicsParentSnapshot.jsx:118:        Parent Snapshot
frontend/dashboards/src/pages\AcademicsParentSnapshot.jsx:145:              onClick={() => navigate(`/parent/students/${studentId}`)}
frontend/dashboards/src/pages\CommunicationsDirectorDashboard.jsx:24:  snapshot_date: '2026-02-28',
frontend/dashboards/src/pages\CommunicationsDirectorDashboard.jsx:101:    <CrownLayout title="Communications Director" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
frontend/dashboards/src/pages\AcademicsDashboard.jsx:42:  const [parentStudents, setParentStudents] = useState([]);
frontend/dashboards/src/pages\AcademicsDashboard.jsx:44:  const [parentError, setParentError] = useState('');
frontend/dashboards/src/pages\AcademicsDashboard.jsx:62:    ['parent', 'school_admin', 'super_admin', 'head_of_school', 'academic_admin', 'teacher', 'registrar', 'staff', 'admin'].includes(role)
frontend/dashboards/src/pages\AcademicsDashboard.jsx:105:      .catch((err) => setParentError(err?.message ?? 'Failed to load parent students.'));
frontend/dashboards/src/pages\AcademicsDashboard.jsx:319:          <div>Parent-linked students are only available for parent/family and staff roles.</div>
frontend/dashboards/src/pages\AcademicsDashboard.jsx:320:        ) : parentError ? (
frontend/dashboards/src/pages\AcademicsDashboard.jsx:321:          <ErrorBanner title="Failed to load parent students" message={parentError} />
frontend/dashboards/src/pages\AcademicsDashboard.jsx:324:            {parentStudents.length === 0 && <div>No linked students.</div>}
frontend/dashboards/src/pages\AcademicsDashboard.jsx:325:            {parentStudents.map((st) => (
frontend/dashboards/src/pages\AcademicsDashboard.jsx:745:                                <button type="button" onClick={() => handleOpenStudent(student)} style={{ width: '100%', textAlign: 'left', padding: '8px', border: 'none', background: 'transparent', fontSize: 13, cursor: 'pointer' }} title="Open student snapshot">
frontend/dashboards/src/pages\comms_wizard\Step3Recipients.jsx:83:                    placeholder="parent@example.com"
backend/crown_api\settings.py.phase9_backup_20260508_172135:47:BASE_DIR = Path(__file__).resolve().parent.parent
backend/crown_api\settings.py.phase9_backup_20260508_172135:220:    'parent360',
backend/crown_api\settings.py.phase9_backup_20260508_172135:634:if str(BASE_DIR.parent) not in sys.path:
backend/crown_api\settings.py.phase9_backup_20260508_172135:635:    sys.path.append(str(BASE_DIR.parent))
frontend/dashboards/src/pages\FinanceInvoicesList.jsx:10:const SM = { fontSize: '0.75rem', padding: '3px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\FinanceInvoicesList.jsx:12:const BTN = { fontSize: '0.875rem', padding: '5px 15px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #1976d2', background: 'transparent', color: '#1976d2' };
frontend/dashboards/src/pages\financial_aid_wizard\Step2Buckets.jsx:62:              background: selected.includes(b.value) ? "var(--crown-surface-2)" : "transparent",
frontend/dashboards/src/pages\HomeDashboard.jsx:27:            <li><Link to="/parent">Parent</Link></li>
frontend/dashboards/src/pages\LibraryDashboard.jsx:20:  snapshot_date: 'Feb 26, 2026',
frontend/dashboards/src/pages\LibraryDashboard.jsx:42:    { label: '17 overdue items  2 over 21 days, contact parents', severity: 'red'    },
frontend/dashboards/src/pages\LibraryDashboard.jsx:109:      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
frontend/dashboards/src/pages\LoginPage.jsx:16:  { value: "parent", label: "Parent", route: "/parent" },
frontend/dashboards/src/pages\LoginPage.jsx:25:  { value: "parent", label: "Parent", route: "/parent" },
frontend/dashboards/src/pages\ParentAttendancePage.jsx:24:        const res = await fetchJson("/api/v1/academics/parents/me/students/");
frontend/dashboards/src/pages\ParentAttendancePage.jsx:27:        setMsg("Failed to load parent students.");
frontend/dashboards/src/pages\ParentDashboard.jsx:4:export default function ParentDashboard() {
frontend/dashboards/src/pages\ParentDashboard.jsx:5:  const config = getDashboardTemplate('parent');
frontend/dashboards/src/pages\ParentDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="parent" />;
frontend/dashboards/src/pages\PDDashboard.jsx:21:  snapshot_date: 'Feb 26, 2026',
frontend/dashboards/src/pages\PDDashboard.jsx:115:      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
frontend/dashboards/src/pages\ProspectiveFamilyAdmissionsWizard.jsx:91:  "Grandparent",
frontend/dashboards/src/pages\ProspectiveFamilyAdmissionsWizard.jsx:323:        <li>Human-led review and transparent next steps</li>
frontend/dashboards/src/pages\ProspectiveFamilyAdmissionsWizard.jsx:973:        <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Application snapshot</p>
frontend/dashboards/src/pages\ProspectiveFamilyAdmissionsWizard.jsx:1206:        transparent communication milestones.
frontend/dashboards/src/pages\RoleHomeRedirect.jsx:54:  ['parent',            '/parent'],
frontend/dashboards/src/pages\StudentServicesDashboard.jsx:21:  snapshot_date: 'Feb 26, 2026',
frontend/dashboards/src/pages\StudentServicesDashboard.jsx:43:    { label: '31 student lunch balances below $5  parent notifications pending', severity: 'red'    },
frontend/dashboards/src/pages\StudentServicesDashboard.jsx:52:    definition: "Students with a lunch account balance below $5  parent notifications are pending.",
frontend/dashboards/src/pages\StudentServicesDashboard.jsx:115:      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
frontend/dashboards/src/pages\wizards\FinanceSetupWizard.jsx:476:            Full snapshot (JSON)
frontend/dashboards/src/pages\wizards\FinanceSetupWizard.jsx:536:  const [snapshot, setSnapshot] = useState(null);
frontend/dashboards/src/pages\wizards\FinanceSetupWizard.jsx:660:          policy={snapshot}
## Parent-related test references
frontend/dashboards/src/tests\permissionContract.test.js:20:  it('parent cannot edit billing', () => {
frontend/dashboards/src/tests\permissionContract.test.js:22:      userHasPermission({ role: 'parent' }, APP_PERMISSIONS.BILLING_EDIT),
frontend/dashboards/src/tests\permissionContract.test.js:28:      role: 'parent',
frontend/dashboards/src/tests\dashboardCardContract.test.jsx:8:import ParentDashboard from '../pages/ParentDashboard.jsx';
frontend/dashboards/src/tests\dashboardCardContract.test.jsx:90:  it('teacher, parent, and student routes use canonical shared shell', () => {
frontend/dashboards/src/tests\dashboardCardContract.test.jsx:96:    const parentRender = render(<ParentDashboard />);
frontend/dashboards/src/tests\dashboardCardContract.test.jsx:97:    expect(screen.getByText('Parent Dashboard')).toBeTruthy();
frontend/dashboards/src/tests\dashboardCardContract.test.jsx:99:    parentRender.unmount();
backend\academics\tests\test_academics_readonly_api.py:184:def test_parent_only_sees_linked_students():
backend\academics\tests\test_academics_readonly_api.py:186:    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
backend\academics\tests\test_academics_readonly_api.py:196:        last_name="Parent",
backend\academics\tests\test_academics_readonly_api.py:197:        email="parent@example.com",
backend\academics\tests\test_academics_readonly_api.py:218:    resp = client.get("/api/v1/academics/parents/me/students/")
backend\financial_aid\tests\test_financial_aid_authz.py:90:        ("PARENT",  "parent.view"),
backend\financial_aid\tests\test_financial_aid_authz.py:112:        ("PARENT",  "parent.view"),
backend\core\tests\test_scoping.py:102:# Test: Parent ΓåÆ Students via Guardian.email ΓåÆ Household
backend\core\tests\test_scoping.py:106:class TestScopingStudentsParent(TestCase):
backend\core\tests\test_scoping.py:110:        self.parent = UserAccount.objects.create_user(
backend\core\tests\test_scoping.py:111:            username="parent_scope_test", password=TEST_AUTH_SECRET, email="mama@family.com"
backend\core\tests\test_scoping.py:113:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:115:        # Own household ΓÇö guardian email matches parent user email.
backend\core\tests\test_scoping.py:135:    def test_parent_sees_only_own_household_students(self):
backend\core\tests\test_scoping.py:137:        result = scope_queryset(self.parent, qs, DOMAIN_STUDENTS)
backend\core\tests\test_scoping.py:142:    def test_parent_email_match_is_case_insensitive(self):
backend\core\tests\test_scoping.py:144:        case_parent = UserAccount.objects.create_user(
backend\core\tests\test_scoping.py:145:            username="case_parent_scope_test", password=TEST_AUTH_SECRET,
backend\core\tests\test_scoping.py:148:        case_parent.role = "PARENT"
backend\core\tests\test_scoping.py:150:        result = scope_queryset(case_parent, qs, DOMAIN_STUDENTS)
backend\core\tests\test_scoping.py:153:    def test_parent_with_no_guardian_record_sees_nothing(self):
backend\core\tests\test_scoping.py:155:            username="orphan_parent_scope_test", password=TEST_AUTH_SECRET,
backend\core\tests\test_scoping.py:164:# Test: Parent ΓåÆ FinancialAidApplication via Guardian.email ΓåÆ household_id
backend\core\tests\test_scoping.py:168:class TestScopingFinancialAidParent(TestCase):
backend\core\tests\test_scoping.py:172:        self.parent = UserAccount.objects.create_user(
backend\core\tests\test_scoping.py:173:            username="aid_parent_scope_test", password=TEST_AUTH_SECRET,
backend\core\tests\test_scoping.py:176:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:199:    def test_parent_sees_only_own_household_applications(self):
backend\core\tests\test_scoping.py:201:        result = scope_queryset(self.parent, qs, DOMAIN_FINANCIAL_AID)
backend\core\tests\test_scoping.py:206:    def test_parent_with_no_guardian_record_sees_nothing(self):
backend\core\tests\test_scoping.py:217:# Test: Parent ΓåÆ LedgerEntry via user.guardian.family
backend\core\tests\test_scoping.py:221:# Rename to test_scope_financial_parent_family once DB test is feasible.
backend\core\tests\test_scoping.py:224:class TestScopingFinancialParentFamily(TestCase):
backend\core\tests\test_scoping.py:238:        self.parent = UserAccount.objects.create_user(
backend\core\tests\test_scoping.py:239:            username="fin_parent_scope_test", password=TEST_AUTH_SECRET,
backend\core\tests\test_scoping.py:241:        UserAccount.objects.filter(pk=self.parent.pk).update(guardian=self.guardian)
backend\core\tests\test_scoping.py:242:        self.parent.refresh_from_db()
backend\core\tests\test_scoping.py:243:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:245:    def test_scope_financial_parent_family__contract_only(self):
backend\core\tests\test_scoping.py:246:        """Contract: scope_queryset calls qs.filter(family=<parent's family>).
backend\core\tests\test_scoping.py:253:        result = scope_queryset(self.parent, mock_qs, DOMAIN_FINANCIAL)
backend\core\tests\test_scoping.py:258:    def test_scope_financial_parent_no_guardian__contract_only(self):
backend\core\tests\test_scoping.py:259:        """Contract: parent with no guardian FK gets qs.none(), not an exception.
backend\_spectacular_latest.txt:61:Error [parent_students]: unable to guess serializer. This is graceful fallback 
backend\_spectacular_latest.txt:490:Error [parent_view]: unable to guess serializer. This is graceful fallback 
backend\_spectacular_latest.txt:580:[parent_award_response]: unable to guess serializer. This is graceful fallback 
backend\_spectacular_latest.txt:650:[parent_aid_status]: unable to guess serializer. This is graceful fallback 
backend\_spectacular_latest.txt:655:[parent_aid_timeline]: unable to guess serializer. This is graceful fallback 
backend\_spectacular_latest.txt:660:[parent_aid_verification]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:832:536: Error [ParentExcuseHistoryView]: unable to guess serializer. This is 
backend\_spectacular_latest.txt:837:522: Error [ParentRespondToNotificationView]: unable to guess serializer. This 
backend\_spectacular_latest.txt:842:458: Error [ParentAttendanceStatusView]: unable to guess serializer. This is 
backend\_spectacular_latest.txt:847:485: Error [ParentStudentAttendanceView]: unable to guess serializer. This is 
backend\_spectacular_latest.txt:852:495: Error [ParentSubmitAttendanceExcuseView]: unable to guess serializer. 
backend\_spectacular_latest.txt:937:Error [parent_autopay_status]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:942:Error [parent_autopay_cancel]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:947:Error [parent_autopay_enroll]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:952:Error [parent_autopay_pause]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:957:Error [parent_autopay_resume]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:962:Error [parent_billing_invoices]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:967:Error [parent_billing_payments]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:972:Error [parent_billing_receipts]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:977:Error [parent_billing_summary]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:982:Error [parent_tax_documents]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:1333:597: Error [ParentDisciplineAcknowledgeIncidentView]: unable to guess 
backend\_spectacular_latest.txt:1338:583: Error [ParentDisciplineIncidentDetailView]: unable to guess serializer. 
backend\_spectacular_latest.txt:1343:566: Error [ParentDisciplineIncidentListView]: unable to guess serializer. 
backend\_spectacular_latest.txt:1348:610: Error [ParentDisciplineRespondView]: unable to guess serializer. This is 
backend\_spectacular_latest.txt:1363:500: Error [DisciplineParentRecordSummaryView]: unable to guess serializer. 
backend\_spectacular_latest.txt:1473:: Error [parent_balance]: unable to guess serializer. This is graceful 
backend\_spectacular_latest.txt:1548:.py: Error [food_parent_summary]: unable to guess serializer. This is graceful 
backend\core\tests\test_rbac_contract.py:53:        "PARENT": _mk_user("parent"),
backend\gradebook\tests\test_parent_grades_routing.py:6:def test_parent_grades_summary_route_is_registered():
backend\gradebook\tests\test_parent_grades_e2e.py:2:Phase 4 Step 2: E2E payload test for parent grades summary endpoint.
backend\gradebook\tests\test_parent_grades_e2e.py:89:def test_parent_grades_summary_requires_auth():
backend\gradebook\tests\test_parent_grades_e2e.py:109:def test_parent_grades_summary_invalid_tenant_header_returns_400():
backend\gradebook\tests\test_parent_grades_e2e.py:128:def test_parent_grades_summary_unknown_student_returns_404():
backend\gradebook\tests\test_parent_grades_e2e.py:141:def test_parent_grades_summary_payload_shape():
backend\gradebook\tests\test_parent_grades_e2e.py:196:def test_parent_grades_summary_no_grades_returns_empty_courses():
backend\core\tests\test_nav_endpoint.py:88:    def test_parent_does_not_see_finance_admissions_billing_integrity(self):
backend\core\tests\test_nav_endpoint.py:89:        school = _school("Parent Nav School")
backend\core\tests\test_nav_endpoint.py:90:        parent = _user("parent1")
backend\core\tests\test_nav_endpoint.py:91:        _assign_role(parent, school, "parent")
backend\core\tests\test_nav_endpoint.py:92:        _grant("parent", "parent.view")
backend\core\tests\test_nav_endpoint.py:95:        c.force_login(parent)
backend\core\tests\test_nav_endpoint.py:103:        assert "Parent" in labels
backend\core\tests\test_nav_endpoint.py:104:        assert "/parent" in hrefs
backend\core\tests\test_nav_endpoint.py:134:        assert "/parent" not in hrefs
backend\core\tests\test_nav_endpoint.py:199:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:200:        _grant("parent", "parent.view")
backend\core\tests\test_nav_endpoint.py:213:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:214:        _grant("parent", "parent.view")
backend\core\tests\test_nav_endpoint.py:229:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:230:        _grant("parent", "parent.view")
backend\onboarding\tests\test_solomon_services.py:228:            audience="parent",
backend\onboarding\tests\test_solomon_services.py:295:        audience = SolomonAudience.objects.create(slug="parent-aud", name="Parent")
backend\onboarding\tests\test_solomon_services.py:296:        targeted = _article("parent-targeted", module="fin")
backend\onboarding\tests\test_solomon_services.py:299:        payload = search_solomon_content(_FakeRequest(), audience="parent-aud")
backend\onboarding\tests\test_solomon_services.py:301:        assert "parent-targeted" in slugs
backend\onboarding\tests\test_parent_enrollment_guidance.py:27:class ParentEnrollmentGuidanceSurfaceTests(TestCase):
backend\onboarding\tests\test_parent_enrollment_guidance.py:42:    def _build_parent_enrollment_context(self):
backend\onboarding\tests\test_parent_enrollment_guidance.py:49:            name=f"Parent {uuid.uuid4().hex[:6]}",
backend\onboarding\tests\test_parent_enrollment_guidance.py:50:            slug=f"parent-{uuid.uuid4().hex[:8]}",
backend\onboarding\tests\test_parent_enrollment_guidance.py:51:            role_code="parent",
backend\onboarding\tests\test_parent_enrollment_guidance.py:56:            title="Parent Enrollment Guide",
backend\onboarding\tests\test_parent_enrollment_guidance.py:57:            slug=f"parent-enrollment-guide-{uuid.uuid4().hex[:8]}",
backend\onboarding\tests\test_parent_enrollment_guidance.py:69:            title="Parent Enrollment Playbook",
backend\onboarding\tests\test_parent_enrollment_guidance.py:70:            slug=f"parent-enrollment-playbook-{uuid.uuid4().hex[:8]}",
backend\onboarding\tests\test_parent_enrollment_guidance.py:71:            summary="Parent enrollment steps",
backend\onboarding\tests\test_parent_enrollment_guidance.py:83:            context_key="parent-enrollment",
backend\onboarding\tests\test_parent_enrollment_guidance.py:91:    def test_progress_can_include_parent_enrollment_guidance(self):
backend\onboarding\tests\test_parent_enrollment_guidance.py:92:        self._build_parent_enrollment_context()
backend\onboarding\tests\test_parent_enrollment_guidance.py:97:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:102:        self.assertIn("parent_enrollment_guidance", data)
backend\onboarding\tests\test_parent_enrollment_guidance.py:103:        guidance = data["parent_enrollment_guidance"]
backend\onboarding\tests\test_parent_enrollment_guidance.py:111:        self._build_parent_enrollment_context()
backend\onboarding\tests\test_parent_enrollment_guidance.py:116:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:120:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:126:            res1.json().get("parent_enrollment_guidance"),
backend\onboarding\tests\test_parent_enrollment_guidance.py:127:            res2.json().get("parent_enrollment_guidance"),
backend\onboarding\tests\test_parent_enrollment_guidance.py:132:        self._build_parent_enrollment_context()
backend\onboarding\tests\test_parent_enrollment_guidance.py:137:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:141:        self.assertNotIn("parent_enrollment_guidance", res.json())
backend\onboarding\tests\test_parent_enrollment_guidance.py:145:        self._build_parent_enrollment_context()
backend\onboarding\tests\test_parent_enrollment_guidance.py:150:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:154:        self.assertNotIn("parent_enrollment_guidance", res.json())
backend\onboarding\tests\test_parent_enrollment_guidance.py:163:                {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:167:        self.assertNotIn("parent_enrollment_guidance", res.json())
backend\onboarding\tests\test_parent_enrollment_guidance.py:175:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:179:        guidance = res.json().get("parent_enrollment_guidance")
backend\onboarding\tests\test_parent_enrollment_guidance.py:189:                {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:193:        self.assertNotIn("parent_enrollment_guidance", res.json())
backend\onboarding\tests\test_parent_enrollment_guidance.py:201:            {"include_parent_guidance": "1"},
backend\onboarding\tests\test_parent_enrollment_guidance.py:213:            {"include_parent_guidance": "1"},
backend\gradebook\tests\test_gradebook_ro_api.py:131:    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
backend\tests_list.txt:47:backend/academics/tests/test_academics_readonly_api.py::test_parent_only_sees_linked_students
backend\tests_list.txt:511:backend/core/tests/test_nav_endpoint.py::TestNavPermissionFiltering::test_parent_does_not_see_finance_admissions_billing_integrity
backend\tests_list.txt:550:backend/core/tests/test_scoping.py::TestScopingStudentsParent::test_parent_email_match_is_case_insensitive
backend\tests_list.txt:551:backend/core/tests/test_scoping.py::TestScopingStudentsParent::test_parent_sees_only_own_household_students
backend\tests_list.txt:552:backend/core/tests/test_scoping.py::TestScopingStudentsParent::test_parent_with_no_guardian_record_sees_nothing
backend\tests_list.txt:553:backend/core/tests/test_scoping.py::TestScopingFinancialAidParent::test_parent_sees_only_own_household_applications
backend\tests_list.txt:554:backend/core/tests/test_scoping.py::TestScopingFinancialAidParent::test_parent_with_no_guardian_record_sees_nothing
backend\tests_list.txt:555:backend/core/tests/test_scoping.py::TestScopingFinancialParentFamily::test_scope_financial_parent_family__contract_only
backend\tests_list.txt:556:backend/core/tests/test_scoping.py::TestScopingFinancialParentFamily::test_scope_financial_parent_no_guardian__contract_only
backend\tests_list.txt:616:backend/crown_api/tests/test_academics_api.py::AcademicsApiTests::test_attendance_parent_scoped_and_no_existence_leak
backend\tests_list.txt:618:backend/crown_api/tests/test_academics_api.py::AcademicsApiTests::test_grades_parent_scoped_and_no_existence_leak
backend\tests_list.txt:647:backend/crown_api/tests/test_billing_summary_api.py::BillingSummaryApiTests::test_parent_scoped_and_no_existence_leak
backend\tests_list.txt:651:backend/crown_api/tests/test_comms_api.py::CommsApiTests::test_thread_detail_parent_in_scope_200
backend\tests_list.txt:652:backend/crown_api/tests/test_comms_api.py::CommsApiTests::test_thread_detail_parent_out_of_scope_404
backend\tests_list.txt:654:backend/crown_api/tests/test_comms_api.py::CommsApiTests::test_threads_list_parent_scoped_to_household
backend\tests_list.txt:738:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:765:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:792:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:949:backend/crown_api/tests/test_scheduling_api.py::SchedulingApiTests::test_parent_scoped_terms_sections_and_schedule
backend\tests_list.txt:966:backend/crown_api/tests/test_students_api.py::StudentsApiTests::test_list_students_parent_scoped_to_household
backend\tests_list.txt:968:backend/crown_api/tests/test_students_api.py::StudentsApiTests::test_student_detail_parent_out_of_scope_404
backend\tests_list.txt:1103:backend/finance/tests/test_finance_api.py::TestParentBalanceEndpoint::test_balance_deducts_allocations
backend\tests_list.txt:1104:backend/finance/tests/test_finance_api.py::TestParentBalanceEndpoint::test_balance_reflects_obligations
backend\tests_list.txt:1105:backend/finance/tests/test_finance_api.py::TestParentBalanceEndpoint::test_void_obligations_excluded
backend\tests_list.txt:1140:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_missing_header_fail_closed
backend\tests_list.txt:1141:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_only_shows_own_obligations
backend\tests_list.txt:1156:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_summary[PARENT-parent.view]
backend\tests_list.txt:1159:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_drilldown[PARENT-parent.view]
backend\tests_list.txt:1292:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_requires_auth
backend\tests_list.txt:1293:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_invalid_tenant_header_returns_400
backend\tests_list.txt:1294:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_unknown_student_returns_404
backend\tests_list.txt:1295:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_payload_shape
backend\tests_list.txt:1296:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_no_grades_returns_empty_courses
backend\tests_list.txt:1297:backend/gradebook/tests/test_parent_grades_routing.py::test_parent_grades_summary_route_is_registered
backend\tests_list.txt:1329:backend/households/tests/test_guardian_scoping.py::TestParentGuardianScopingHouseholds::test_parent_no_matching_household_gets_empty_list
backend\tests_list.txt:1330:backend/households/tests/test_guardian_scoping.py::TestParentGuardianScopingHouseholds::test_parent_sees_own_household_only
backend\tests_list.txt:1331:backend/households/tests/test_guardian_scoping.py::TestParentGuardianScopingStudents::test_parent_sees_own_students_only
backend\tests_list.txt:1332:backend/households/tests/test_guardian_scoping.py::TestNonParentRolesNotGuardianScoped::test_registrar_sees_all_school_households
backend\tests_list.txt:1333:backend/households/tests/test_guardian_scoping.py::TestNonParentRolesNotGuardianScoped::test_teacher_sees_all_school_households
backend\tests_list.txt:1550:backend/parent360/tests/test_parent_overview_api.py::test_parent_self_overview_v1_route_returns_200_and_household_shape
backend\tests_list.txt:1551:backend/parent360/tests/test_parent_overview_api.py::test_parent_self_overview_rejects_foreign_school_guardian_email_match
backend\tests_list.txt:1552:backend/parent360/tests/test_parent_overview_api.py::test_parent_self_overview_service_hours_do_not_bridge_across_schools
backend\tests_list.txt:1553:backend/parent360/tests/test_parent_overview_api.py::test_parent_self_overview_ignores_assignments_for_unenrolled_sections
backend\tests_list.txt:2149:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_unauthenticated_request_returns_401_or_403
backend\tests_list.txt:2150:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_health_endpoint_reachable
backend\tests_list.txt:2151:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_authenticated_request_with_school_header
backend\tests_list.txt:2152:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_school_record_persists
backend\tests_list.txt:2153:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_user_school_binding_correct
backend\tests_list.txt:2154:backend/tests/test_parent_portal_api.py::TestParentPortalApi::test_parent_portal_api_client_request_response_cycle
backend\tests_list.txt:2155:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_unauthenticated_request_is_forbidden
backend\tests_list.txt:2156:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_invalid_uuid_school_header_is_rejected
backend\tests_list.txt:2157:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_post_with_empty_body_returns_400_or_405
backend\tests_list.txt:2158:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_nonexistent_resource_returns_404
backend\tests_list.txt:2159:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_delete_on_readonly_endpoint_returns_403_or_405
backend\tests_list.txt:2160:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_raises_when_school_missing_from_request
backend\tests_list.txt:2161:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_tenant_school_ids_are_distinct
backend\tests_list.txt:2162:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_user_bound_to_correct_school
backend\tests_list.txt:2163:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2164:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_same_tenant_request_is_allowed
backend\tests_list.txt:2165:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2166:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_isolation_keyword_present_in_source
backend\tests_list.txt:2676:backend/tests/test_51x51_evidence_28_parent_portal.py::test_51x51_module_metadata_present_28
backend\tests_list.txt:2677:backend/tests/test_51x51_evidence_28_parent_portal.py::test_51x51_module_text_has_context_28
backend\tests_list.txt:2678:backend/tests/test_51x51_evidence_28_parent_portal.py::test_51x51_required_keywords_present_28
backend\tests_list.txt:2795:backend/tests/test_parent_portal_unit.py::test_parent_portal_module_source_exists
backend\tests_list.txt:2796:backend/tests/test_parent_portal_unit.py::test_parent_portal_pytest_config_present
backend\tests_list.txt:2797:backend/tests/test_parent_portal_unit.py::test_parent_portal_no_placeholder_in_source
backend\tests_list.txt:2798:backend/tests/test_parent_portal_unit.py::test_parent_portal_school_keyword_in_source
backend\tests_list.txt:2894:backend/tests/audit_51x51/test_51x51_module_28_parent_portal_closure.py::test_51x51_module_identity_28
backend\tests_list.txt:2895:backend/tests/audit_51x51/test_51x51_module_28_parent_portal_closure.py::test_51x51_required_check_tokens_28
backend\gradebook\tests\test_gradebook_list_endpoints.py:168:    user = _mk_user(school=school, email="parent@example.com", is_staff=False)
backend\gradebook\tests\test_gradebook_list_endpoints.py:182:    user = _mk_user(school=school, email="parent2@example.com", is_staff=False)
backend\finance\tests\test_finance_tenant.py:7:  3. Parent balance only shows authenticated user's obligations.
backend\finance\tests\test_finance_tenant.py:94:        parent = _make_user("parent_nostaff")
backend\finance\tests\test_finance_tenant.py:96:        c.force_authenticate(user=parent)
backend\finance\tests\test_finance_tenant.py:113:class TestParentBalanceTenantScoping(TestCase):
backend\finance\tests\test_finance_tenant.py:117:        self.parent = _make_user("parent_alpha")
backend\finance\tests\test_finance_tenant.py:119:        self.client.force_authenticate(user=self.parent)
backend\finance\tests\test_finance_tenant.py:121:    def test_parent_balance_only_shows_own_obligations(self):
backend\finance\tests\test_finance_tenant.py:122:        """Parent sees only their obligations in the requested school."""
backend\finance\tests\test_finance_tenant.py:124:        _make_obligation(self.school1, self.parent, amount_cents=5_000)
backend\finance\tests\test_finance_tenant.py:126:        _make_obligation(self.school2, self.parent, amount_cents=3_000)
backend\finance\tests\test_finance_tenant.py:129:            "/api/finance/parent/balance/",
backend\finance\tests\test_finance_tenant.py:134:        # Only self.parent's school1 obligation
backend\finance\tests\test_finance_tenant.py:138:    def test_parent_balance_missing_header_fail_closed(self):
backend\finance\tests\test_finance_tenant.py:140:        r = self.client.get("/api/finance/parent/balance/")
backend\comms_wizard\tests\test_views.py:19:    {"to": "parent1@example.com", "name": "Parent One"},
backend\comms_wizard\tests\test_views.py:20:    {"to": "parent2@example.com", "name": "Parent Two"},
backend\crown_api\tests\test_students_api.py:25:        self.parent_user = UserAccount.objects.create_user(
backend\crown_api\tests\test_students_api.py:26:            username="parentuser",
backend\crown_api\tests\test_students_api.py:27:            email="parent@example.com",
backend\crown_api\tests\test_students_api.py:33:        UserRole.objects.create(user=self.parent_user, school=self.school, role_code="PARENT")
backend\crown_api\tests\test_students_api.py:45:        # Guardian for household_a matching parent_user email
backend\crown_api\tests\test_students_api.py:46:        self.parent_guardian = Guardian.objects.create(
backend\crown_api\tests\test_students_api.py:49:            first_name="Parent",
backend\crown_api\tests\test_students_api.py:51:            email="parent@example.com",
backend\crown_api\tests\test_students_api.py:81:    def test_list_students_parent_scoped_to_household(self):
backend\crown_api\tests\test_students_api.py:83:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_students_api.py:89:    def test_student_detail_parent_out_of_scope_404(self):
backend\crown_api\tests\test_students_api.py:91:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_scheduling_api.py:27:        self.parent_user = UserAccount.objects.create_user(
backend\crown_api\tests\test_scheduling_api.py:28:            username="parentuser",
backend\crown_api\tests\test_scheduling_api.py:29:            email="parent@example.com",
backend\crown_api\tests\test_scheduling_api.py:38:        self.parent_person = Person.objects.create(
backend\crown_api\tests\test_scheduling_api.py:39:            first_name="Parent",
backend\crown_api\tests\test_scheduling_api.py:41:            email="parent@example.com",
backend\crown_api\tests\test_scheduling_api.py:43:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend\crown_api\tests\test_scheduling_api.py:46:            person=self.parent_person,
backend\crown_api\tests\test_scheduling_api.py:76:        # Link families to households for parent scoping
backend\crown_api\tests\test_scheduling_api.py:103:        # for parent schedule scoping (replaces AdmissionsApplication bridge)
backend\crown_api\tests\test_scheduling_api.py:164:        # Enroll student_b into math_b so staff sees it, parent does not
backend\crown_api\tests\test_scheduling_api.py:185:    def test_parent_scoped_terms_sections_and_schedule(self):
backend\crown_api\tests\test_scheduling_api.py:186:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_rbac_matrix_readonly.py:25:FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rbac_endpoints_readonly.txt"
backend\finance\tests\test_finance_api.py:9:  GET  /api/finance/parent/balance/
backend\finance\tests\test_finance_api.py:125:        self.parent = _user("o_parent")
backend\finance\tests\test_finance_api.py:140:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:147:            "payer_user_id": str(self.parent.id),
backend\finance\tests\test_finance_api.py:162:            "payer_user_id": str(self.parent.id),
backend\finance\tests\test_finance_api.py:173:        body = {"obligation_type": "tuition", "description": "No payer", "payer_user_id": str(self.parent.id)}
backend\finance\tests\test_finance_api.py:231:# Parent balance
backend\finance\tests\test_finance_api.py:234:class TestParentBalanceEndpoint(TestCase):
backend\finance\tests\test_finance_api.py:237:        self.parent = _user("bal_parent")
backend\finance\tests\test_finance_api.py:240:        _obligation(self.school, self.parent, amount_cents=20_000)
backend\finance\tests\test_finance_api.py:241:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:242:        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
backend\finance\tests\test_finance_api.py:250:        ob = _obligation(self.school, self.parent, amount_cents=10_000)
backend\finance\tests\test_finance_api.py:251:        pay = _payment(self.school, self.parent, amount_cents=10_000)
backend\finance\tests\test_finance_api.py:256:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:257:        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
backend\finance\tests\test_finance_api.py:264:        _obligation(self.school, self.parent, amount_cents=5_000)
backend\finance\tests\test_finance_api.py:265:        FinanceObligation.objects.filter(school=self.school, payer_user=self.parent).update(
backend\finance\tests\test_finance_api.py:268:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:269:        r = c.get("/api/finance/parent/balance/", HTTP_X_SCHOOL_ID=str(self.school.id))
backend\finance\tests\test_finance_api.py:282:        self.parent = _user("pi_parent")
backend\finance\tests\test_finance_api.py:285:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:294:        c = _auth_client(self.parent)
backend\finance\tests\test_finance_api.py:300:        c = _auth_client(self.parent)
backend\crown_api\tests\test_metrics_permissions_contract.py:50:    ("parent",           "/api/v1/parent/metrics/"),
backend\crown_api\tests\test_comms_api.py:38:        self.parent_user = UserAccount.objects.create_user(
backend\crown_api\tests\test_comms_api.py:39:            username="parentuser",
backend\crown_api\tests\test_comms_api.py:40:            email="parent@example.com",
backend\crown_api\tests\test_comms_api.py:49:        self.parent_person = Person.objects.create(
backend\crown_api\tests\test_comms_api.py:50:            first_name="Parent",
backend\crown_api\tests\test_comms_api.py:52:            email="parent@example.com",
backend\crown_api\tests\test_comms_api.py:54:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend\crown_api\tests\test_comms_api.py:57:            person=self.parent_person,
backend\crown_api\tests\test_comms_api.py:105:            created_by=self.parent_person,
backend\crown_api\tests\test_comms_api.py:112:            created_by=self.parent_person,
backend\crown_api\tests\test_comms_api.py:130:        self._add_messages(self.thread_a_household, self.parent_person, _dt(2026, 1, 2, 12, 0))
backend\crown_api\tests\test_comms_api.py:131:        self._add_messages(self.thread_a_student, self.parent_person, _dt(2026, 1, 3, 12, 0))
backend\crown_api\tests\test_comms_api.py:179:    def test_threads_list_parent_scoped_to_household(self):
backend\crown_api\tests\test_comms_api.py:180:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_comms_api.py:189:    def test_thread_detail_parent_in_scope_200(self):
backend\crown_api\tests\test_comms_api.py:190:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_comms_api.py:194:    def test_thread_detail_parent_out_of_scope_404(self):
backend\crown_api\tests\test_comms_api.py:195:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_billing_summary_api.py:27:        self.parent_user = UserAccount.objects.create_user(
backend\crown_api\tests\test_billing_summary_api.py:28:            username="parentuser",
backend\crown_api\tests\test_billing_summary_api.py:29:            email="parent@example.com",
backend\crown_api\tests\test_billing_summary_api.py:38:        self.parent_person = Person.objects.create(
backend\crown_api\tests\test_billing_summary_api.py:39:            first_name="Parent",
backend\crown_api\tests\test_billing_summary_api.py:41:            email="parent@example.com",
backend\crown_api\tests\test_billing_summary_api.py:43:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend\crown_api\tests\test_billing_summary_api.py:46:            person=self.parent_person,
backend\crown_api\tests\test_billing_summary_api.py:100:    def test_parent_scoped_and_no_existence_leak(self):
backend\crown_api\tests\test_billing_summary_api.py:101:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_academics_api.py:35:        self.parent_user = UserAccount.objects.create_user(
backend\crown_api\tests\test_academics_api.py:36:            username="parentuser",
backend\crown_api\tests\test_academics_api.py:37:            email="parent@example.com",
backend\crown_api\tests\test_academics_api.py:46:        self.parent_person = Person.objects.create(
backend\crown_api\tests\test_academics_api.py:47:            first_name="Parent",
backend\crown_api\tests\test_academics_api.py:49:            email="parent@example.com",
backend\crown_api\tests\test_academics_api.py:51:        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
backend\crown_api\tests\test_academics_api.py:54:            person=self.parent_person,
backend\crown_api\tests\test_academics_api.py:84:        # Link families to households for parent scoping
backend\crown_api\tests\test_academics_api.py:112:        # for parent attendance/grades scoping (replaces AdmissionsApplication bridge)
backend\crown_api\tests\test_academics_api.py:165:    def test_attendance_parent_scoped_and_no_existence_leak(self):
backend\crown_api\tests\test_academics_api.py:166:        self.client.force_authenticate(user=self.parent_user)
backend\crown_api\tests\test_academics_api.py:186:    def test_grades_parent_scoped_and_no_existence_leak(self):
backend\crown_api\tests\test_academics_api.py:187:        self.client.force_authenticate(user=self.parent_user)
backend\payments\tests\test_household_finance_access.py:62:        role_groups=("parent",),
backend\parent360\tests\test_parent_overview_api.py:18:PARENT360_V1_URL = "/api/v1/parent360/me/overview/"
backend\parent360\tests\test_parent_overview_api.py:19:PARENT360_URL = "/api/parent360/me/overview/"
backend\parent360\tests\test_parent_overview_api.py:22:def _make_parent_client(*, school: School, email: str = "parent@example.com"):
backend\parent360\tests\test_parent_overview_api.py:24:        username=f"parent-{school.id}",
backend\parent360\tests\test_parent_overview_api.py:39:    email: str = "parent@example.com",
backend\parent360\tests\test_parent_overview_api.py:53:        last_name="Parent",
backend\parent360\tests\test_parent_overview_api.py:140:def test_parent_self_overview_v1_route_returns_200_and_household_shape():
backend\parent360\tests\test_parent_overview_api.py:141:    school = School.objects.create(name="Heritage Parent Academy")
backend\parent360\tests\test_parent_overview_api.py:142:    client, _ = _make_parent_client(school=school)
backend\parent360\tests\test_parent_overview_api.py:155:def test_parent_self_overview_rejects_foreign_school_guardian_email_match():
backend\parent360\tests\test_parent_overview_api.py:158:    email = "shared-parent@example.com"
backend\parent360\tests\test_parent_overview_api.py:161:    client, _ = _make_parent_client(school=school, email=email)
backend\parent360\tests\test_parent_overview_api.py:168:def test_parent_self_overview_service_hours_do_not_bridge_across_schools():
backend\parent360\tests\test_parent_overview_api.py:171:    client, _ = _make_parent_client(school=school, email="service-parent@example.com")
backend\parent360\tests\test_parent_overview_api.py:174:        email="service-parent@example.com",
backend\parent360\tests\test_parent_overview_api.py:193:def test_parent_self_overview_ignores_assignments_for_unenrolled_sections():
backend\parent360\tests\test_parent_overview_api.py:195:    client, _ = _make_parent_client(school=school, email="assignments-parent@example.com")
backend\parent360\tests\test_parent_overview_api.py:198:        email="assignments-parent@example.com",
backend\applications\tests\test_admissions_endpoints.py:114:                        "guardianName": "Maria Parent",
backend\applications\tests\test_admissions_endpoints.py:115:                        "email": "maria.parent@example.com",
backend\applications\tests\test_admissions_endpoints.py:126:                    "lastName": "Parent",
backend\applications\tests\test_admissions_endpoints.py:539:            f"admissions_submit_rl:email:{self.school_id}:maria.parent@example.com",
backend\tests\test_volunteer_family_engagement_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_volunteer_family_engagement_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\solomon\tests\test_models.py:73:        audience = SolomonAudience.objects.create(name="Parent", slug="parent")
backend\tests\test_transportation_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_transportation_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\households\tests\test_guardian_scoping.py:77:class TestParentGuardianScopingHouseholds(TestCase):
backend\households\tests\test_guardian_scoping.py:81:        self.school = _school("Parent Own")
backend\households\tests\test_guardian_scoping.py:82:        self.parent_email = f"parent-{uuid.uuid4()}@example.com"
backend\households\tests\test_guardian_scoping.py:85:        self.parent_user = _user(self.parent_email, self.school)
backend\households\tests\test_guardian_scoping.py:86:        _assign_role(self.parent_user, self.school, "PARENT")
backend\households\tests\test_guardian_scoping.py:88:        self.own_hh = _make_household(self.school, "Own Family", self.parent_email)
backend\households\tests\test_guardian_scoping.py:91:    def test_parent_sees_own_household_only(self):
backend\households\tests\test_guardian_scoping.py:93:        c.force_login(self.parent_user)
backend\households\tests\test_guardian_scoping.py:102:    def test_parent_no_matching_household_gets_empty_list(self):
backend\households\tests\test_guardian_scoping.py:103:        school = _school("Parent Empty")
backend\households\tests\test_guardian_scoping.py:104:        parent_email = f"nobody-{uuid.uuid4()}@example.com"
backend\households\tests\test_guardian_scoping.py:105:        parent_user = _user(parent_email, school)
backend\households\tests\test_guardian_scoping.py:106:        _assign_role(parent_user, school, "PARENT")
backend\households\tests\test_guardian_scoping.py:110:        c.force_login(parent_user)
backend\households\tests\test_guardian_scoping.py:126:class TestParentGuardianScopingStudents(TestCase):
backend\households\tests\test_guardian_scoping.py:130:        self.school = _school("Parent Students")
backend\households\tests\test_guardian_scoping.py:131:        self.parent_email = f"parent2-{uuid.uuid4()}@example.com"
backend\households\tests\test_guardian_scoping.py:134:        self.parent_user = _user(self.parent_email, self.school)
backend\households\tests\test_guardian_scoping.py:135:        _assign_role(self.parent_user, self.school, "PARENT")
backend\households\tests\test_guardian_scoping.py:137:        self.own_hh = _make_household(self.school, "Own Family 2", self.parent_email)
backend\households\tests\test_guardian_scoping.py:143:    def test_parent_sees_own_students_only(self):
backend\households\tests\test_guardian_scoping.py:145:        c.force_login(self.parent_user)
backend\households\tests\test_guardian_scoping.py:164:class TestNonParentRolesNotGuardianScoped(TestCase):
backend\solomon\tests\test_adapters.py:37:            name="Parent",
backend\solomon\tests\test_adapters.py:38:            slug="parent",
backend\solomon\tests\test_adapters.py:39:            role_code="parent",
backend\solomon\tests\test_adapters.py:71:            context_key="welcome-parent",
backend\solomon\tests\test_adapters.py:93:            audience="parent",
backend\solomon\tests\test_adapters.py:127:            audience="parent",
backend\solomon\tests\test_adapters.py:158:        self.parent_audience = SolomonAudience.objects.create(
backend\solomon\tests\test_adapters.py:159:            name="Parent",
backend\solomon\tests\test_adapters.py:160:            slug="parent-ob",
backend\solomon\tests\test_adapters.py:161:            role_code="parent",
backend\solomon\tests\test_adapters.py:166:            title="Parent Enrollment Guide",
backend\solomon\tests\test_adapters.py:167:            slug="parent-enrollment-guide",
backend\solomon\tests\test_adapters.py:176:        self.resource.audiences.add(self.parent_audience)
backend\solomon\tests\test_adapters.py:179:            title="Parent Onboarding",
backend\solomon\tests\test_adapters.py:180:            slug="parent-onboarding",
backend\solomon\tests\test_adapters.py:181:            summary="Getting started as a parent",
backend\solomon\tests\test_adapters.py:188:        self.playbook.audiences.add(self.parent_audience)
backend\solomon\tests\test_adapters.py:193:            context_key="parent-checklist",
backend\solomon\tests\test_adapters.py:194:            audience=self.parent_audience,
backend\solomon\tests\test_adapters.py:210:    def test_onboarding_adapter_resolves_parent_context(self):
backend\solomon\tests\test_adapters.py:215:            audience="parent",
backend\solomon\tests\test_adapters.py:233:            audience="parent",
backend\solomon\tests\test_adapters.py:247:            audience="parent",
backend\aftercare\tests\test_aftercare_services.py:71:        pickup_contact_id=None, pickup_name_freeform="Parent", pickup_verified=True,
backend\aftercare\tests\test_aftercare_services.py:88:    assert inc.parent_notified is False
backend\tests\test_survey_sentiment_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_survey_sentiment_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_student_master_record_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_audit_logging_tenant.py:78:        root = Path(__file__).resolve().parents[1]
backend\tests\test_student_master_record_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_51x51_evidence_20_grades___report_cards.py:13:MODULE_TEXT = 'Grades / Report Cards\nStores gradebook results, term grades, report-card output, and parent/student visibility.\nGrade entry | Grade calculation | Report card | Parent view | Teacher workflow\nRecord grade | Calculate term result | Publish report | Protect edits | Audit change\ngrade posting rate | missing grades | report generation success | parent view accuracy | grade correction count\ncourses | terms | teacher portal | parent portal | transcripts\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_20_grades___report_cards.py:36:# Stores gradebook results, term grades, report-card output, and parent/student visibility.
backend\tests\test_51x51_evidence_20_grades___report_cards.py:37:# Grade entry | Grade calculation | Report card | Parent view | Teacher workflow
backend\tests\test_51x51_evidence_20_grades___report_cards.py:39:# grade posting rate | missing grades | report generation success | parent view accuracy | grade correction count
backend\tests\test_51x51_evidence_20_grades___report_cards.py:40:# courses | terms | teacher portal | parent portal | transcripts
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:13:MODULE_TEXT = 'Nurse Office / Health Office\nManages health visits, medications, alerts, incidents, and parent health communication.\nHealth visit | Medication | Medical alerts | Incident | Parent follow-up\nLog visit | Track medication | Show alerts | Notify parent | Protect sensitive data\nvisits today | medication due | health alerts | parent follow-ups | incident closure\nstudents | medical essentials | RBAC | communications | audit\nDev 3\nSecond-Wave Module'
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:36:# Manages health visits, medications, alerts, incidents, and parent health communication.
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:37:# Health visit | Medication | Medical alerts | Incident | Parent follow-up
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:38:# Log visit | Track medication | Show alerts | Notify parent | Protect sensitive data
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:39:# visits today | medication due | health alerts | parent follow-ups | incident closure
backend\tests\test_student_care_discipline_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:2:51x51 remediation closure evidence for ModuleId 28: Parent Portal
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:12:MODULE_NAME = 'Parent Portal'
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:38:# Module 28: Parent Portal
backend\tests\test_51x51_evidence_28_parent_portal.py:2:51x51 remediation evidence tests for ModuleId 28: Parent Portal
backend\tests\test_51x51_evidence_28_parent_portal.py:12:MODULE_NAME = 'Parent Portal'
backend\tests\test_51x51_evidence_28_parent_portal.py:13:MODULE_TEXT = 'Parent Portal\nProvides family-scoped access to students, attendance, grades, billing, messages, documents, and tasks.\nFamily dashboard | Student view | Billing view | Messages | Forms\nAuthenticate parent | Scope children | Show records | Submit tasks | Pay balance\nparent login success | task completion | payment completion | message read rate | data leakage count\nauth | households | students | billing | communications\nDev 4\nFirst-Wave Module'
backend\tests\test_51x51_evidence_28_parent_portal.py:35:# Parent Portal
backend\tests\test_51x51_evidence_28_parent_portal.py:38:# Authenticate parent | Scope children | Show records | Submit tasks | Pay balance
backend\tests\test_51x51_evidence_28_parent_portal.py:39:# parent login success | task completion | payment completion | message read rate | data leakage count
backend\tests\test_student_care_discipline_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:13:MODULE_TEXT = 'Mobile App / Family App\nProvides mobile access to family, student, teacher, alerts, calendar, and school-life workflows.\nMobile login | Push alerts | Family view | Calendar | Messages\nAuthenticate mobile user | Send push | Show scoped records | Support tasks | Respect permissions\nmobile active users | push delivery | crash rate | task completion | mobile login success\nauth | parent portal | communications | calendar | notifications\nProduct + Dev 4\nLater Add-on'
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:40:# auth | parent portal | communications | calendar | notifications
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:13:MODULE_TEXT = 'Student Care / Discipline Summary\nStores behavior/care summary layer and student-support references.\nCare summary | Behavior summary | Incident link | Referral | Admin view\nRecord incident | Summarize care | Restrict sensitive access | Notify approved users | Audit changes\nopen care items | incident response time | discipline trend | sensitive access violations | care closure rate\nstudents | RBAC | parent portal | counselor | audit\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:40:# students | RBAC | parent portal | counselor | audit
backend\tests\test_document_file_framework_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_mobile_family_app_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_communications_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_grades_report_cards_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_staff_faculty_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_grades_report_cards_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_mobile_family_app_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_staff_faculty_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_christian_pd_hub_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_board_governance_suite_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_christian_pd_hub_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_board_governance_suite_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_mission_metrics_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:13:MODULE_TEXT = 'Extended Discipline Workflows\nManages behavior incidents, consequences, escalation, parent communication, and reviews.\nIncident | Consequence | Escalation | Parent notice | Admin review\nRecord incident | Assign consequence | Escalate case | Notify parent | Close review\nincident count | closure time | repeat incidents | parent notification rate | escalation backlog\nstudents | student care | communications | RBAC | audit\nDev 3\nSecond-Wave Module'
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:36:# Manages behavior incidents, consequences, escalation, parent communication, and reviews.
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:37:# Incident | Consequence | Escalation | Parent notice | Admin review
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:38:# Record incident | Assign consequence | Escalate case | Notify parent | Close review
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:39:# incident count | closure time | repeat incidents | parent notification rate | escalation backlog
backend\tests\test_mission_metrics_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_audit_logging_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_extended_discipline_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_crown_compass_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_chaplain_pastoral_care_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_chaplain_pastoral_care_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_crm_marketing_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_shell_backend_contract_parity.py:10:REPO_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_extended_discipline_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_crm_marketing_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_crown_compass_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_communications_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_emergency_medical_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_shared_frontend_shell_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_grade_levels_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_emergency_medical_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_document_file_framework_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_shared_frontend_shell_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_service_outreach_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_school_year_term_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_tenant.py:2:Tenant isolation tests for the Parent Portal module.
backend\tests\test_parent_portal_tenant.py:3:Module keywords: ParentPortal, parent, guardian_portal, family_dashboard, parent_dashboard
backend\tests\test_parent_portal_tenant.py:18:def _two_schools_parent_portal():
backend\tests\test_parent_portal_tenant.py:19:    school_a = School.objects.create(name="Parent Portal Isolation School A")
backend\tests\test_parent_portal_tenant.py:20:    school_b = School.objects.create(name="Parent Portal Isolation School B")
backend\tests\test_parent_portal_tenant.py:23:        username=f"tenant-a-parent_portal-{token}",
backend\tests\test_parent_portal_tenant.py:24:        email=f"ta-parent_portal-{token}@example.com",
backend\tests\test_parent_portal_tenant.py:31:class TestParentPortalTenantIsolation:
backend\tests\test_parent_portal_tenant.py:32:    """Cross-tenant isolation tests for Parent Portal."""
backend\tests\test_parent_portal_tenant.py:35:        self.school_a, self.school_b, self.user_a = _two_schools_parent_portal()
backend\tests\test_parent_portal_tenant.py:38:    def test_parent_portal_tenant_school_ids_are_distinct(self):
backend\tests\test_parent_portal_tenant.py:42:    def test_parent_portal_user_bound_to_correct_school(self):
backend\tests\test_parent_portal_tenant.py:47:    def test_parent_portal_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_parent_portal_tenant.py:58:    def test_parent_portal_same_tenant_request_is_allowed(self):
backend\tests\test_parent_portal_tenant.py:67:    def test_parent_portal_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_parent_portal_tenant.py:75:    def test_parent_portal_isolation_keyword_present_in_source(self):
backend\tests\test_parent_portal_tenant.py:76:        """Tenant isolation keywords exist in the Parent Portal module source."""
backend\tests\test_parent_portal_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_tenant.py:87:        assert found, f"Parent Portal: tenant isolation keywords not found in source"
backend\tests\test_grade_levels_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_notifications_framework_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_school_year_term_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_service_outreach_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_nurse_health_office_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_negative.py:2:Negative / error-path tests for the Parent Portal module.
backend\tests\test_parent_portal_negative.py:3:Module keywords: ParentPortal, parent, guardian_portal, family_dashboard, parent_dashboard
backend\tests\test_parent_portal_negative.py:18:def _school_neg_parent_portal():
backend\tests\test_parent_portal_negative.py:19:    return School.objects.create(name="Parent Portal Negative School")
backend\tests\test_parent_portal_negative.py:22:def _user_neg_parent_portal(school):
backend\tests\test_parent_portal_negative.py:25:        username=f"neg-parent_portal-{token}",
backend\tests\test_parent_portal_negative.py:26:        email=f"neg-parent_portal-{token}@example.com",
backend\tests\test_parent_portal_negative.py:32:class TestParentPortalNegativeCases:
backend\tests\test_parent_portal_negative.py:33:    """Negative tests for Parent Portal: unauthorized, invalid, forbidden paths."""
backend\tests\test_parent_portal_negative.py:36:        self.school = _school_neg_parent_portal()
backend\tests\test_parent_portal_negative.py:37:        self.user = _user_neg_parent_portal(self.school)
backend\tests\test_parent_portal_negative.py:40:    def test_parent_portal_unauthenticated_request_is_forbidden(self):
backend\tests\test_parent_portal_negative.py:45:    def test_parent_portal_invalid_uuid_school_header_is_rejected(self):
backend\tests\test_parent_portal_negative.py:54:    def test_parent_portal_post_with_empty_body_returns_400_or_405(self):
backend\tests\test_parent_portal_negative.py:65:    def test_parent_portal_nonexistent_resource_returns_404(self):
backend\tests\test_parent_portal_negative.py:66:        """Accessing a nonexistent Parent Portal resource returns 404."""
backend\tests\test_parent_portal_negative.py:69:            f"/api/v1/parent-portal/nonexistent-item-99999/",
backend\tests\test_parent_portal_negative.py:74:    def test_parent_portal_delete_on_readonly_endpoint_returns_403_or_405(self):
backend\tests\test_parent_portal_negative.py:83:    def test_parent_portal_raises_when_school_missing_from_request(self):
backend\tests\test_notifications_framework_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_reporting_data_access_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_api.py:2:API tests for the Parent Portal module.
backend\tests\test_parent_portal_api.py:3:Module keywords: ParentPortal, parent, guardian_portal, family_dashboard, parent_dashboard
backend\tests\test_parent_portal_api.py:17:def _school_parent_portal(suffix=""):
backend\tests\test_parent_portal_api.py:18:    return School.objects.create(name=f"Parent Portal API School {suffix}")
backend\tests\test_parent_portal_api.py:21:def _user_parent_portal(school, *, staff=False):
backend\tests\test_parent_portal_api.py:24:        username=f"api-parent_portal-{token}",
backend\tests\test_parent_portal_api.py:25:        email=f"api-parent_portal-{token}@example.com",
backend\tests\test_parent_portal_api.py:32:class TestParentPortalApi:
backend\tests\test_parent_portal_api.py:33:    """API surface tests for Parent Portal."""
backend\tests\test_parent_portal_api.py:36:        self.school = _school_parent_portal()
backend\tests\test_parent_portal_api.py:37:        self.user = _user_parent_portal(self.school)
backend\tests\test_parent_portal_api.py:38:        self.staff = _user_parent_portal(self.school, staff=True)
backend\tests\test_parent_portal_api.py:41:    def test_parent_portal_unauthenticated_request_returns_401_or_403(self):
backend\tests\test_parent_portal_api.py:46:    def test_parent_portal_health_endpoint_reachable(self):
backend\tests\test_parent_portal_api.py:47:        """Health endpoint confirms API layer is operational for Parent Portal."""
backend\tests\test_parent_portal_api.py:51:    def test_parent_portal_authenticated_request_with_school_header(self):
backend\tests\test_parent_portal_api.py:60:    def test_parent_portal_school_record_persists(self):
backend\tests\test_parent_portal_api.py:61:        """School record for Parent Portal tenant is created and queryable."""
backend\tests\test_parent_portal_api.py:62:        count = School.objects.filter(name__icontains="Parent Portal API School").count()
backend\tests\test_parent_portal_api.py:65:    def test_parent_portal_user_school_binding_correct(self):
backend\tests\test_parent_portal_api.py:69:    def test_parent_portal_api_client_request_response_cycle(self):
backend\tests\test_parent_portal_api.py:70:        """APIClient request/response cycle works for Parent Portal."""
backend\tests\test_nurse_health_office_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_shared_design_system_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_school_profile_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_unit.py:2:Unit tests for the Parent Portal module.
backend\tests\test_parent_portal_unit.py:3:Module keywords: ParentPortal, parent, guardian_portal, family_dashboard, parent_dashboard
backend\tests\test_parent_portal_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_parent_portal_unit.py:13:def test_parent_portal_module_source_exists():
backend\tests\test_parent_portal_unit.py:14:    """Verify Parent Portal implementation source is present in the repository."""
backend\tests\test_parent_portal_unit.py:22:    keywords = ["ParentPortal", "parent", "guardian_portal", "family_dashboard", "parent_dashboard"]
backend\tests\test_parent_portal_unit.py:24:    assert found, f"Parent Portal module keywords not found in source: {keywords}"
backend\tests\test_parent_portal_unit.py:27:def test_parent_portal_pytest_config_present():
backend\tests\test_parent_portal_unit.py:28:    """Verify pytest.ini exists for Parent Portal test suite."""
backend\tests\test_parent_portal_unit.py:35:def test_parent_portal_no_placeholder_in_source():
backend\tests\test_parent_portal_unit.py:36:    """Verify Parent Portal source does not consist entirely of placeholder stubs."""
backend\tests\test_parent_portal_unit.py:41:def test_parent_portal_school_keyword_in_source():
backend\tests\test_parent_portal_unit.py:42:    """Verify tenant/school scoping keywords appear in the Parent Portal source tree."""
backend\tests\test_parent_portal_unit.py:53:    ), f"Parent Portal: tenant/school scoping not found in source"
backend\tests\test_portrait_graduate_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_schedule_builder_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_shared_design_system_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_school_profile_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_portrait_graduate_unit.py:10:PROJECT_ROOT = Path(__file__).resolve().parents[2]
backend\tests\test_schedule_builder_tenant.py:78:        root = Path(__file__).resolve().parents[2]
backend\tests\test_reporting_data_access_tenant.py:78:        root = Path(__file__).resolve().parents[2]
