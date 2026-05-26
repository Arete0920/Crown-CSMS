# KU-05 Authoritative RBAC / Tenant Runtime Proof

Generated: 2026-05-25 15:29:19
Scope: Evidence-only proof. No app/runtime code edits.

## Repo State

## chore/normalize-powershell-eol-safe...origin/main [behind 16]
M  backend/finance_setup/models.py
A  backend/finance_setup/tests/test_tuition_builder_models.py
A  docs/brand/BRAND_ASSET_INTAKE_CHECKLIST.md
A  docs/brand/CROWN_BRAND_USAGE.md
A  docs/brand/CROWN_LOGO_PLACEMENT_MATRIX.md
A  docs/brand/MICROSOFT_ASSET_SOURCE_REGISTER.md
A  frontend/dashboards/public/brand/crown/README.md
A  frontend/dashboards/public/brand/crown/logo/crown-logo-compact-full-color.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-horizontal-full-color.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-mark-crown-only.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-mark-shield.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-mark-square.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-monochrome-royal.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-monochrome-white.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-primary-stacked-full-color.svg
A  frontend/dashboards/public/brand/crown/logo/crown-logo-wordmark-full-color.svg
A  frontend/dashboards/public/brand/crown/manifest.json
A  frontend/dashboards/public/brand/crown/ui/crown-dashboard-hero-logo.svg
A  frontend/dashboards/public/brand/crown/ui/crown-email-header-logo.svg
A  frontend/dashboards/public/brand/crown/ui/crown-login-brand.svg
A  frontend/dashboards/public/brand/crown/ui/crown-print-header-logo.svg
A  frontend/dashboards/public/brand/crown/ui/crown-report-cover-logo.svg
A  frontend/dashboards/public/brand/crown/ui/crown-sidebar-collapsed.svg
A  frontend/dashboards/public/brand/crown/ui/crown-sidebar-expanded.svg
A  frontend/dashboards/public/brand/crown/ui/crown-topnav-horizontal.svg
A  frontend/dashboards/public/brand/third-party/microsoft/README.md
A  frontend/dashboards/public/brand/third-party/microsoft/license-and-usage-notes.md
A  frontend/dashboards/public/brand/third-party/microsoft/manifest.json
A  frontend/dashboards/public/brand/third-party/microsoft/usage/microsoft-logo-source-register.md
A  frontend/dashboards/src/brand/crownBrandAssets.js
A  frontend/dashboards/src/brand/microsoftBrandAssets.js
A  frontend/dashboards/src/components/brand/BrandLockup.jsx
A  frontend/dashboards/src/components/brand/CrownAppMark.jsx
A  frontend/dashboards/src/components/brand/CrownLogo.jsx
A  frontend/dashboards/src/components/brand/CrownLogo.test.jsx
A  frontend/dashboards/src/components/brand/MicrosoftProductLogo.jsx
A  frontend/dashboards/src/components/brand/MicrosoftProductLogo.test.jsx
M  frontend/dashboards/src/components/crown-dashboard/CrownHeroHeader.jsx
M  frontend/dashboards/src/components/launch/CrownSidebar.jsx
M  frontend/dashboards/src/components/launch/CrownTopbar.jsx
M  frontend/dashboards/src/pages/LoginPage.jsx
M  frontend/dashboards/src/styles/launch-shell.css
A  frontend/dashboards/src/tests/brandIntegrity.test.js
A  scripts/brand/check_brand_asset_readiness.ps1
A  scripts/brand/verify_brand_integrity.ps1
M  tools/add_kpi_imports.ps1
M  tools/appsettings_allowlist_gate.ps1
M  tools/audit/CROWN_MAGUS0_AUDIT.ps1
M  tools/audit/run_audit.ps1
M  tools/audit_integrity.ps1
M  tools/audit_min.ps1
M  tools/audit_patterns.ps1
M  tools/audit_wizard_pack.ps1
M  tools/certify_prod.ps1
M  tools/demo_audit/api_probe.ps1
M  tools/demo_audit/azure_spike.ps1
M  tools/demo_audit/run_demo_audit.ps1
M  tools/demo_reset_smoke.ps1
M  tools/dev_scripts/auth_smoke.ps1
M  tools/dev_scripts/ci_runtime_canary.ps1
M  tools/dev_scripts/demo_one_click.ps1
M  tools/dev_scripts/demo_snapshot.ps1
M  tools/dev_scripts/golden_path.ps1
M  tools/dev_scripts/golden_path_gate.ps1
M  tools/dev_scripts/lockdown_run.ps1
A  tools/dev_scripts/run_parent_release_closeout_check.ps1
A  tools/dev_scripts/run_parent_targeted_backend_suite.ps1
M  tools/dev_scripts/tag_green3.ps1
M  tools/fix_hex_all.ps1
M  tools/fix_hex_colors.ps1
M  tools/fix_hex_colors_pass2.ps1
M  tools/fix_hex_final.ps1
M  tools/fix_hex_mop.ps1
M  tools/full_verification_pack.ps1
M  tools/inject_kpi_strips.ps1
M  tools/prod_health_probe.ps1
M  tools/prod_integrity_check.ps1
M  tools/prod_status.ps1
M  tools/proof_ceremony.ps1
M  tools/proof_phase3_runtime.ps1
M  tools/require_tag_input.ps1
A  tools/run_parent_sandbox_demo_gate.ps1
M  tools/run_pytest_proof.ps1
M  tools/run_rc_live_probes.ps1
M  tools/scan_hex.ps1
M  tools/scan_hex_all.ps1
M  tools/scan_named_colors.ps1
M  tools/verify_demo_surface.ps1
M  tools/verify_deploy_integrity.ps1
M  tools/verify_lane2_billing_loop.ps1
M  tools/verify_lane2_payment_loop.ps1
M  tools/verify_lane3_attendance_loop.ps1
M  tools/verify_m365_sso_and_outbox.ps1
M  tools/verify_phase3_demo_proof.ps1
M  tools/verify_prod_build_sha.ps1
M  tools/verify_prod_deploy.ps1
M  tools/verify_rc_runbook.ps1
M  tools/verify_routes_gate.ps1
M  tools/verify_ui_shell_gate.ps1
chore/normalize-powershell-eol-safe
d6da200523eedf48498abf37a07a80f81bb6c0af
16	0
```

## Security Test Discovery

backend\applications\tests\test_application_decision_api.py:16:def _mk_user_with_school_id(school_id):
backend\applications\tests\test_application_decision_api.py:17:    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
backend\applications\tests\test_application_decision_api.py:20:    if hasattr(u, "school_id"):
backend\applications\tests\test_application_decision_api.py:21:        setattr(u, "school_id", school_id)
backend\applications\tests\test_application_decision_api.py:22:        u.save(update_fields=["school_id"])
backend\applications\tests\test_application_decision_api.py:27:    school_id = uuid.uuid4()
backend\applications\tests\test_application_decision_api.py:28:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\applications\tests\test_application_decision_api.py:30:        school_id=school_id,
backend\applications\tests\test_application_decision_api.py:37:        school_id=school_id,
backend\applications\tests\test_application_decision_api.py:43:    user = _mk_user_with_school_id(school_id)
backend\applications\tests\test_application_decision_api.py:66:    school_id = uuid.uuid4()
backend\applications\tests\test_application_decision_api.py:67:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\applications\tests\test_application_decision_api.py:69:        school_id=school_id,
backend\applications\tests\test_application_decision_api.py:75:        school_id=school_id,
backend\applications\tests\test_application_decision_api.py:81:    user = _mk_user_with_school_id(school_id)
backend\applications\tests\test_applications_api.py:14:def _mk_user_with_school_id(school_id):
backend\applications\tests\test_applications_api.py:17:        id=school_id,
backend\applications\tests\test_applications_api.py:18:        defaults={"name": f"School-{school_id}"},
backend\applications\tests\test_applications_api.py:26:    if hasattr(u, "school_id"):
backend\applications\tests\test_applications_api.py:27:        setattr(u, "school_id", school_id)
backend\applications\tests\test_applications_api.py:28:        u.save(update_fields=["school_id"])
backend\applications\tests\test_applications_api.py:36:    hh_a = Household.objects.create(school_id=school_a, name="A Household")
backend\applications\tests\test_applications_api.py:37:    hh_b = Household.objects.create(school_id=school_b, name="B Household")
backend\applications\tests\test_applications_api.py:39:    Application.objects.create(school_id=school_a, household=hh_a)
backend\applications\tests\test_applications_api.py:40:    Application.objects.create(school_id=school_b, household=hh_b)
backend\applications\tests\test_applications_api.py:42:    user = _mk_user_with_school_id(school_a)
backend\applications\tests\test_applications_api.py:55:    hh_a = Household.objects.create(school_id=school_a, name="A Household")
backend\applications\tests\test_applications_api.py:57:    user = _mk_user_with_school_id(school_a)
backend\applications\tests\test_applications_api.py:68:    assert app.school_id == school_a
backend\applications\tests\test_applications_api.py:74:    hh_a = Household.objects.create(school_id=school_a, name="A Household")
backend\applications\tests\test_applications_api.py:75:    app = Application.objects.create(school_id=school_a, household=hh_a, status=ApplicationStatus.DRAFT)
backend\applications\tests\test_applications_api.py:77:    user = _mk_user_with_school_id(school_a)
backend\attendance_rules_wizard\tests\test_views.py:26:def _headers(school_id):
backend\attendance_rules_wizard\tests\test_views.py:27:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\attendance_rules_wizard\tests\test_views.py:43:def _advance_to_configured(client, school_id):
backend\attendance_rules_wizard\tests\test_views.py:44:    r = client.post(BASE_URL, **_headers(school_id))
backend\attendance_rules_wizard\tests\test_views.py:50:        **_headers(school_id),
backend\attendance_rules_wizard\tests\test_views.py:55:def _advance_to_codes_defined(client, school_id):
backend\attendance_rules_wizard\tests\test_views.py:56:    sid = _advance_to_configured(client, school_id)
backend\attendance_rules_wizard\tests\test_views.py:61:        **_headers(school_id),
backend\attendance_rules_wizard\tests\test_views.py:66:def _advance_to_committed(client, school_id):
backend\attendance_rules_wizard\tests\test_views.py:67:    sid = _advance_to_codes_defined(client, school_id)
backend\attendance_rules_wizard\tests\test_views.py:72:        **_headers(school_id),
backend\athletics\tests\test_athletics.py:4:39 passing target: URL routing, permissions, CRUD, tenant isolation,
backend\athletics\tests\test_athletics.py:518:# 11. Tenant isolation
backend\athletics\tests\test_athletics.py:534:    def test_season_cross_tenant_hidden(self):
backend\athletics\tests\test_athletics.py:540:    def test_event_cross_tenant_hidden(self):
backend\athletics\tests\test_athletics.py:549:    def test_invalid_school_id_returns_not_found(self):
backend\applications\tests\test_admissions_tenant_scoping.py:2:Regression tests: cross-tenant header must NOT grant access to another school's
backend\applications\tests\test_admissions_tenant_scoping.py:9:  - View permission check uses school=request.school (School B instance).
backend\applications\tests\test_admissions_tenant_scoping.py:10:  - user_has_permission(user, "admissions.view", school=School B) -> False.
backend\applications\tests\test_admissions_tenant_scoping.py:32:        if hasattr(self.user, "school_id"):
backend\applications\tests\test_admissions_tenant_scoping.py:33:            self.user.school_id = self.school_a.pk
backend\applications\tests\test_admissions_tenant_scoping.py:36:        # Grant admissions.view permission to REGISTRAR role.
backend\applications\tests\test_admissions_tenant_scoping.py:41:        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)
backend\applications\tests\test_admissions_tenant_scoping.py:48:    # ΓöÇΓöÇ Cross-tenant ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
backend\applications\tests\test_admissions_tenant_scoping.py:50:    def test_summary_cross_tenant_header_is_403(self):
backend\applications\tests\test_admissions_tenant_scoping.py:58:    def test_drilldown_cross_tenant_header_is_403(self):
backend\applications\tests\test_admissions_endpoints.py:27:        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)
backend\applications\tests\test_admissions_endpoints.py:33:        self.school_id = self.school.id
backend\applications\tests\test_admissions_endpoints.py:38:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:53:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:59:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:66:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:73:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:83:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:93:            school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:158:        """Missing X-School-Id should return 400."""
backend\applications\tests\test_admissions_endpoints.py:161:        self.assertIn("X-School-Id", r.json()["detail"])
backend\applications\tests\test_admissions_endpoints.py:167:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:180:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:228:        # User must have a role at other_school now that permission is scoped.
backend\applications\tests\test_admissions_endpoints.py:241:        """Missing X-School-Id should return 400."""
backend\applications\tests\test_admissions_endpoints.py:249:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:264:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:297:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:307:                school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:312:                school_id=self.school_id,
backend\applications\tests\test_admissions_endpoints.py:324:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:335:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:347:        # User must have a role at other_school now that permission is scoped.
backend\applications\tests\test_admissions_endpoints.py:363:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:370:        before_apps = Application.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:371:        before_applicants = Applicant.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:372:        before_events = ApplicationEvent.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:373:        before_fee_obligations = FinanceObligation.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:374:        before_fee_invoices = FinanceInvoice.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:396:            Application.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:400:            Applicant.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:404:            ApplicationEvent.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:408:            FinanceObligation.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:412:            FinanceInvoice.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:416:    def test_submit_requires_campus_when_no_tenant_header(self):
backend\applications\tests\test_admissions_endpoints.py:417:        """Public submit must include inquiry.campus when no tenant header is provided."""
backend\applications\tests\test_admissions_endpoints.py:425:        self.assertEqual(r.data.get("code"), "missing_tenant")
backend\applications\tests\test_admissions_endpoints.py:463:        before_fee_obligations = FinanceObligation.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:464:        before_fee_invoices = FinanceInvoice.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:471:            FinanceObligation.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:475:            FinanceInvoice.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:484:        before_apps = Application.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:485:        before_applicants = Applicant.objects.filter(school_id=self.school_id).count()
backend\applications\tests\test_admissions_endpoints.py:509:            Application.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:513:            Applicant.objects.filter(school_id=self.school_id).count(),
backend\applications\tests\test_admissions_endpoints.py:539:            f"admissions_submit_rl:email:{self.school_id}:maria.parent@example.com",
backend\applications\tests\test_admissions_endpoints.py:556:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\applications\tests\test_admissions_endpoints.py:564:    def test_public_config_allows_missing_tenant_header(self):
backend\applications\tests\test_admissions_endpoints.py:565:        """Public config must be reachable without X-School-Id for public funnel bootstrap."""
backend\attendance_codes_wizard\tests\test_views.py:35:def _h(school_id):
backend\attendance_codes_wizard\tests\test_views.py:36:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\attendance_codes_wizard\tests\test_views.py:129:    def test_cross_tenant_returns_404(self):
backend\aid\tests\test_aid_api.py:56:    """Staff user with school=None; bypasses cross-tenant check."""
backend\aid\tests\test_aid_api.py:182:    def test_tenant_isolation_different_school_data_not_returned(self):
frontend/dashboards/src\tests\loginPagePolish.test.jsx:33:      json: () => Promise.resolve({ access: "token", school_id: "school-1" }),
frontend/dashboards/src\tests\roleGuard.test.jsx:4:describe('RoleGuard role checks', () => {
frontend/dashboards/src\tests\roleGuard.test.jsx:10:  it('blocks unauthorized role', () => {
frontend/dashboards/src\tests\brandIntegrity.test.js:11:  it('has no forbidden public wording in registry values', () => {
frontend/dashboards/src\tests\permissionContract.test.js:6:} from '../auth/permissions';
frontend/dashboards/src\tests\permissionContract.test.js:8:describe('permission contract', () => {
frontend/dashboards/src\tests\permissionContract.test.js:10:    const permissions = resolvePermissions({ role: 'admin' });
frontend/dashboards/src\tests\permissionContract.test.js:11:    expect(permissions.includes('*')).toBe(true);
frontend/dashboards/src\tests\permissionContract.test.js:26:  it('explicit permissions override role fallback', () => {
frontend/dashboards/src\tests\permissionContract.test.js:27:    const permissions = resolvePermissions({
frontend/dashboards/src\tests\permissionContract.test.js:29:      permissions: [APP_PERMISSIONS.RELEASE_VIEW],
frontend/dashboards/src\tests\permissionContract.test.js:32:    expect(permissions).toContain(APP_PERMISSIONS.RELEASE_VIEW);
frontend/dashboards/src\tests\apiContractRegistry.test.js:16:      expect(Boolean(contract.permission)).toBe(true);
backend\gradebook_setup_wizard\tests\test_views.py:27:def _headers(school_id):
backend\gradebook_setup_wizard\tests\test_views.py:28:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\gradebook_setup_wizard\tests\test_views.py:37:def _make_section(school_id):
backend\gradebook_setup_wizard\tests\test_views.py:39:        school_id=school_id, code=f"GS{uuid.uuid4().hex[:4]}", name="Test Course"
backend\gradebook_setup_wizard\tests\test_views.py:41:    return Section.objects.create(school_id=school_id, course=course, term="2026-FALL")
backend\gradebook_setup_wizard\tests\test_views.py:55:def _advance_to_configured(client, school_id, section_id):
backend\gradebook_setup_wizard\tests\test_views.py:56:    r = client.post(BASE_URL, **_headers(school_id))
backend\gradebook_setup_wizard\tests\test_views.py:62:        **_headers(school_id),
backend\gradebook_setup_wizard\tests\test_views.py:67:def _advance_to_categories_defined(client, school_id, section_id):
backend\gradebook_setup_wizard\tests\test_views.py:68:    sid = _advance_to_configured(client, school_id, section_id)
backend\gradebook_setup_wizard\tests\test_views.py:73:        **_headers(school_id),
backend\gradebook_setup_wizard\tests\test_views.py:78:def _advance_to_committed(client, school_id, section_id):
backend\gradebook_setup_wizard\tests\test_views.py:79:    sid = _advance_to_categories_defined(client, school_id, section_id)
backend\gradebook_setup_wizard\tests\test_views.py:84:        **_headers(school_id),
backend\gradebook_setup_wizard\tests\test_views.py:264:        db_count = AssignmentCategory.objects.filter(section=section, school_id=school.id).count()
backend\transportation\tests\test_transportation.py:10:  - Cross-tenant isolation
backend\transportation\tests\test_transportation.py:111:    def test_create_denied_for_readonly_role(self):
backend\transportation\tests\test_transportation.py:138:    def test_cross_tenant_isolation(self):
backend\transportation\tests\test_transportation.py:148:    def test_unauthenticated_denied(self):
backend\transportation\tests\test_transportation.py:185:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:240:    def test_stops_action_cross_tenant_denied(self):
backend\transportation\tests\test_transportation.py:248:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:287:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:338:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:384:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:442:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:492:    def test_run_sheet_cross_tenant(self):
backend\transportation\tests\test_transportation.py:516:    def test_run_sheet_unauthenticated_denied(self):
backend\aftercare\tests\test_aftercare_tenant_scoping.py:11:    AftercareAttendance.objects.create(school_id=1, student_id=2001, date=d, checkin_time=timezone.now())
backend\aftercare\tests\test_aftercare_tenant_scoping.py:12:    AftercareAttendance.objects.create(school_id=2, student_id=2001, date=d, checkin_time=timezone.now())
backend\aftercare\tests\test_aftercare_tenant_scoping.py:13:    assert AftercareAttendance.objects.filter(school_id=1, student_id=2001).count() == 1
backend\aftercare\tests\test_aftercare_tenant_scoping.py:14:    assert AftercareAttendance.objects.filter(school_id=2, student_id=2001).count() == 1
backend\aftercare\tests\test_aftercare_tenant_scoping.py:18:    """Same (school_id, student_id, date) ΓåÆ unique_together violation."""
backend\aftercare\tests\test_aftercare_tenant_scoping.py:20:    AftercareAttendance.objects.create(school_id=3, student_id=3001, date=d, checkin_time=timezone.now())
backend\aftercare\tests\test_aftercare_tenant_scoping.py:22:        AftercareAttendance.objects.create(school_id=3, student_id=3001, date=d, checkin_time=timezone.now())
backend\aftercare\tests\test_aftercare_tenant_scoping.py:25:def test_enrollment_scoped_by_school_id():
backend\aftercare\tests\test_aftercare_tenant_scoping.py:28:        school_id=10, student_id=4001, start_date=date(2026, 1, 1),
backend\aftercare\tests\test_aftercare_tenant_scoping.py:32:        school_id=20, student_id=4001, start_date=date(2026, 1, 1),
backend\aftercare\tests\test_aftercare_tenant_scoping.py:35:    assert AftercareEnrollment.objects.filter(school_id=10, student_id=4001).count() == 1
backend\aftercare\tests\test_aftercare_tenant_scoping.py:36:    assert AftercareEnrollment.objects.filter(school_id=20, student_id=4001).count() == 1
backend\aftercare\tests\test_aftercare_tenant_scoping.py:37:    assert AftercareEnrollment.objects.filter(school_id=99, student_id=4001).count() == 0
backend\aftercare\tests\test_aftercare_services.py:6:Tenant scoping tests live in test_aftercare_tenant_scoping.py.
backend\aftercare\tests\test_aftercare_services.py:29:    cfg1 = ensure_config(school_id=9001)
backend\aftercare\tests\test_aftercare_services.py:30:    cfg2 = ensure_config(school_id=9001)
backend\aftercare\tests\test_aftercare_services.py:36:    c1 = ensure_config(school_id=9001)
backend\aftercare\tests\test_aftercare_services.py:37:    c2 = ensure_config(school_id=9002)
backend\aftercare\tests\test_aftercare_services.py:47:    ensure_config(school_id=42)
backend\aftercare\tests\test_aftercare_services.py:48:    att = checkin_student(school_id=42, student_id=1001, when=when)
backend\aftercare\tests\test_aftercare_services.py:57:    ensure_config(school_id=42)
backend\aftercare\tests\test_aftercare_services.py:58:    att1 = checkin_student(school_id=42, student_id=1002, when=when)
backend\aftercare\tests\test_aftercare_services.py:59:    att2 = checkin_student(school_id=42, student_id=1002, when=when)
backend\aftercare\tests\test_aftercare_services.py:67:    ensure_config(school_id=42)
backend\aftercare\tests\test_aftercare_services.py:68:    checkin_student(school_id=42, student_id=1003, when=cin)
backend\aftercare\tests\test_aftercare_services.py:70:        school_id=42, student_id=1003,
backend\aftercare\tests\test_aftercare_services.py:84:        school_id=55, student_id=2001,
backend\aftercare\tests\test_aftercare_services.py:94:        school_id=55, student_id=2001,
backend\aftercare\tests\test_aftercare_late_fee.py:17:        school_id=91,
backend\aftercare\tests\test_aftercare_late_fee.py:32:        school_id=92,
backend\aftercare\tests\test_aftercare_late_fee.py:46:        school_id=93,
backend\aftercare\tests\test_aftercare_late_fee.py:60:        school_id=94,
backend\aftercare\tests\test_aftercare_late_fee.py:74:        school_id=95,
backend\aftercare\tests\test_aftercare_late_fee.py:88:        school_id=96,
backend\aftercare\tests\test_aftercare_late_fee.py:103:        school_id=97,
backend\tests_list.txt:38:backend/academic_year_wizard/tests/test_views.py::AcademicYearSingleCurrentTest::test_cross_tenant_year_not_affected
backend\tests_list.txt:122:backend/advancement/tests/test_advancement_stage2.py::GiftCheckoutTest::test_gift_tenant_isolation
backend\tests_list.txt:131:backend/advancement/tests/test_advancement_stage2.py::PledgeTest::test_pledge_tenant_isolation
backend\tests_list.txt:132:backend/advancement/tests/test_advancement_stage2.py::SponsorshipAgreementTest::test_agreement_tenant_isolation
backend\tests_list.txt:226:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_attendance_unique_per_student_day_per_school
backend\tests_list.txt:227:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_attendance_duplicate_same_school_raises
backend\tests_list.txt:228:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_enrollment_scoped_by_school_id
backend\tests_list.txt:233:backend/aid/tests/test_aid_api.py::TestAdminAidOverview::test_tenant_isolation_different_school_data_not_returned
backend\tests_list.txt:304:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_drilldown_cross_tenant_header_is_403
backend\tests_list.txt:305:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_drilldown_own_school_is_200
backend\tests_list.txt:306:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_cross_tenant_header_is_403
backend\tests_list.txt:307:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_own_school_is_200
backend\tests_list.txt:308:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_unauthenticated_is_401
backend\tests_list.txt:353:backend/athletics/tests/test_athletics.py::TestTenantIsolation::test_season_cross_tenant_hidden
backend\tests_list.txt:354:backend/athletics/tests/test_athletics.py::TestTenantIsolation::test_event_cross_tenant_hidden
backend\tests_list.txt:355:backend/athletics/tests/test_athletics.py::TestTenantIsolation::test_invalid_school_id_returns_not_found
backend\tests_list.txt:365:backend/attendance_codes_wizard/tests/test_views.py::TestAttendanceCodesWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:416:backend/bell_schedule_wizard/tests/test_views.py::BellScheduleSnapshotTest::test_cross_tenant_isolation
backend\tests_list.txt:431:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:432:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:433:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_fees_isolation
backend\tests_list.txt:434:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_plans_isolation
backend\tests_list.txt:435:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:470:backend/board_oversight/tests/test_board_rbac.py::test_non_board_user_forbidden
backend\tests_list.txt:471:backend/board_oversight/tests/test_board_tenant_required.py::test_missing_school_id_rejected
backend\tests_list.txt:477:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:478:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:479:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_message_isolation
backend\tests_list.txt:480:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_recipients_isolation
backend\tests_list.txt:481:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:509:backend/core/tests/test_nav_endpoint.py::TestNavTenantEnforcement::test_missing_school_id_header_returns_400
backend\tests_list.txt:510:backend/core/tests/test_nav_endpoint.py::TestNavTenantEnforcement::test_unknown_school_id_returns_404
backend\tests_list.txt:519:backend/core/tests/test_nav_endpoint.py::TestNavResponseShape::test_school_scoping_cross_tenant_isolation
backend\tests_list.txt:520:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_true_when_role_granted
backend\tests_list.txt:521:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_when_role_not_granted
backend\tests_list.txt:522:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_for_nonexistent_permission
backend\tests_list.txt:523:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_when_user_has_no_roles
backend\tests_list.txt:524:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_for_unauthenticated_user
backend\tests_list.txt:525:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_scoped_to_correct_school_returns_true
backend\tests_list.txt:526:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_scoped_to_wrong_school_returns_false
backend\tests_list.txt:527:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_unscoped_query_crosses_schools
backend\tests_list.txt:528:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_allows_request_when_permission_granted
backend\tests_list.txt:529:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_denies_request_when_permission_missing
backend\tests_list.txt:530:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_denies_anonymous_user
backend\tests_list.txt:531:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_403_response_body_is_json
backend\tests_list.txt:532:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_no_request_school_attribute_does_not_crash
backend\tests_list.txt:533:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_crown_permission_code_is_unique
backend\tests_list.txt:534:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_role_permission_unique_together
backend\tests_list.txt:535:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_crown_permission_str
backend\tests_list.txt:536:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_role_permission_str
backend\tests_list.txt:537:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_creates_permissions
backend\tests_list.txt:538:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_creates_role_mappings
backend\tests_list.txt:539:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_is_idempotent
backend\tests_list.txt:540:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_dry_run_creates_nothing
backend\tests_list.txt:541:backend/core/tests/test_rbac_contract.py::test_requires_auth_for_invariants
backend\tests_list.txt:542:backend/core/tests/test_rbac_contract.py::test_requires_tenant_header_for_invariants
backend\tests_list.txt:543:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[FINANCE_DIRECTOR-200]
backend\tests_list.txt:544:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[HEAD_OF_SCHOOL-200]
backend\tests_list.txt:545:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[TEACHER-403]
backend\tests_list.txt:546:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[PARENT-403]
backend\tests_list.txt:547:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[STUDENT-403]
backend\tests_list.txt:626:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_cross_tenant_section_returns_404
backend\tests_list.txt:627:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_cross_tenant_student_returns_404
backend\tests_list.txt:628:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_missing_school_header_returns_400
backend\tests_list.txt:629:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_valid_same_tenant_request_returns_200
backend\tests_list.txt:640:backend/crown_api/tests/test_audit_proof.py::test_audit_recent_forbidden_without_role
backend\tests_list.txt:660:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_correct_tenant_returns_200
backend\tests_list.txt:661:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_missing_tenant_returns_400
backend\tests_list.txt:662:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_wrong_tenant_no_leak
backend\tests_list.txt:663:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_correct_tenant_returns_200
backend\tests_list.txt:664:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_invalid_uuid_returns_400
backend\tests_list.txt:665:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_missing_tenant_returns_400
backend\tests_list.txt:666:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_nonexistent_school_returns_404
backend\tests_list.txt:667:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_wrong_tenant_returns_empty
backend\tests_list.txt:668:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_correct_tenant_returns_200
backend\tests_list.txt:669:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_missing_tenant_returns_400
backend\tests_list.txt:670:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_wrong_tenant_no_leak
backend\tests_list.txt:695:backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked
backend\tests_list.txt:699:backend/crown_api/tests/test_director_actions_tenant_isolation.py::DirectorTenantIsolationTest::test_director_cannot_modify_other_school_award
backend\tests_list.txt:708:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_requires_authentication
backend\tests_list.txt:709:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_build_sha
backend\tests_list.txt:710:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_override_info
backend\tests_list.txt:711:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_tenant_info
backend\tests_list.txt:712:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_user_info
backend\tests_list.txt:713:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CTenantGuardTestCase::test_tenant_mixin_allows_valid_tenant
backend\tests_list.txt:714:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CTenantGuardTestCase::test_tenant_mixin_enforces_tenant_required
backend\tests_list.txt:715:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CDefaultDenyTestCase::test_drf_view_requires_auth_by_default
backend\tests_list.txt:718:backend/crown_api/tests/test_households_api.py::HouseholdsApiTests::test_cross_school_isolation
backend\tests_list.txt:734:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:735:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[board-/api/v1/board/metrics/]
backend\tests_list.txt:736:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:737:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:738:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:739:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[student-/api/v1/student/metrics/]
backend\tests_list.txt:740:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[it-/api/v1/it/metrics/]
backend\tests_list.txt:741:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:742:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:743:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:744:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[office-/api/v1/office/metrics/]
backend\tests_list.txt:745:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[health-/api/v1/health/metrics/]
backend\tests_list.txt:746:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:747:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[food-/api/v1/food/metrics/]
backend\tests_list.txt:748:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:749:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:750:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:751:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:752:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[security-/api/v1/security/metrics/]
backend\tests_list.txt:753:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:754:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:755:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[library-/api/v1/library/metrics/]
backend\tests_list.txt:756:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:757:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:758:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:759:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:760:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:761:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:762:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[board-/api/v1/board/metrics/]
backend\tests_list.txt:763:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:764:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:765:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:766:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[student-/api/v1/student/metrics/]
backend\tests_list.txt:767:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[it-/api/v1/it/metrics/]
backend\tests_list.txt:768:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:769:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:770:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:771:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[office-/api/v1/office/metrics/]
backend\tests_list.txt:772:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[health-/api/v1/health/metrics/]
backend\tests_list.txt:773:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:774:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[food-/api/v1/food/metrics/]
backend\tests_list.txt:775:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:776:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:777:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:778:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:779:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[security-/api/v1/security/metrics/]
backend\tests_list.txt:780:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:781:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:782:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[library-/api/v1/library/metrics/]
backend\tests_list.txt:783:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:784:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:785:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:786:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:787:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:788:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:789:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[board-/api/v1/board/metrics/]
backend\tests_list.txt:790:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:791:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:792:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:793:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[student-/api/v1/student/metrics/]
backend\tests_list.txt:794:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[it-/api/v1/it/metrics/]
backend\tests_list.txt:795:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:796:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:797:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:798:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[office-/api/v1/office/metrics/]
backend\tests_list.txt:799:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[health-/api/v1/health/metrics/]
backend\tests_list.txt:800:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:801:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[food-/api/v1/food/metrics/]
backend\tests_list.txt:802:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:803:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:804:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:805:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:806:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[security-/api/v1/security/metrics/]
backend\tests_list.txt:807:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:808:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:809:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[library-/api/v1/library/metrics/]
backend\tests_list.txt:810:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:811:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:812:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:813:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:814:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:817:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_enroll_applicant
backend\tests_list.txt:818:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_issue_refund
backend\tests_list.txt:819:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_settle_payment
backend\tests_list.txt:820:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_staff_user_passes_enroll_gate
backend\tests_list.txt:821:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_staff_user_passes_settle_gate
backend\tests_list.txt:822:backend/crown_api/tests/test_object_level_permissions.py::PaymentOwnershipBoundaryTests::test_staff_can_settle_any_school_payment_not_just_own
backend\tests_list.txt:823:backend/crown_api/tests/test_object_level_permissions.py::SharedSchoolResourceAccessTests::test_shared_installment_plan_list_accessible_to_all_school_members
backend\tests_list.txt:824:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_409_response_does_not_expose_internal_details
backend\tests_list.txt:825:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_enroll_from_draft_returns_409
backend\tests_list.txt:826:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_enroll_from_submitted_returns_409
backend\tests_list.txt:835:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-admin]
backend\tests_list.txt:836:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-SCHOOL_ADMIN]
backend\tests_list.txt:837:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-BOARD_MEMBER]
backend\tests_list.txt:838:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-FINANCE]
backend\tests_list.txt:839:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-ADMISSIONS]
backend\tests_list.txt:840:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-TEACHER]
backend\tests_list.txt:841:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-PARENT]
backend\tests_list.txt:842:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-admin]
backend\tests_list.txt:843:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-SCHOOL_ADMIN]
backend\tests_list.txt:844:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-BOARD_MEMBER]
backend\tests_list.txt:845:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-FINANCE]
backend\tests_list.txt:846:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-ADMISSIONS]
backend\tests_list.txt:847:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-TEACHER]
backend\tests_list.txt:848:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-PARENT]
backend\tests_list.txt:849:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-admin]
backend\tests_list.txt:850:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-SCHOOL_ADMIN]
backend\tests_list.txt:851:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-BOARD_MEMBER]
backend\tests_list.txt:852:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-FINANCE]
backend\tests_list.txt:853:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-ADMISSIONS]
backend\tests_list.txt:854:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-TEACHER]
backend\tests_list.txt:855:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-PARENT]
backend\tests_list.txt:856:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-admin]
backend\tests_list.txt:857:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-SCHOOL_ADMIN]
backend\tests_list.txt:858:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-BOARD_MEMBER]
backend\tests_list.txt:859:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-FINANCE]
backend\tests_list.txt:860:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-ADMISSIONS]
backend\tests_list.txt:861:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-TEACHER]
backend\tests_list.txt:862:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-PARENT]
backend\tests_list.txt:863:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-admin]
backend\tests_list.txt:864:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-SCHOOL_ADMIN]
backend\tests_list.txt:865:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-BOARD_MEMBER]
backend\tests_list.txt:866:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-FINANCE]
backend\tests_list.txt:867:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-ADMISSIONS]
backend\tests_list.txt:868:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-TEACHER]
backend\tests_list.txt:869:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-PARENT]
backend\tests_list.txt:870:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-admin]
backend\tests_list.txt:871:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-SCHOOL_ADMIN]
backend\tests_list.txt:872:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-BOARD_MEMBER]
backend\tests_list.txt:873:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-FINANCE]
backend\tests_list.txt:874:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-ADMISSIONS]
backend\tests_list.txt:875:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-TEACHER]
backend\tests_list.txt:876:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-PARENT]
backend\tests_list.txt:877:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-admin]
backend\tests_list.txt:878:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-SCHOOL_ADMIN]
backend\tests_list.txt:879:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-BOARD_MEMBER]
backend\tests_list.txt:880:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-FINANCE]
backend\tests_list.txt:881:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-ADMISSIONS]
backend\tests_list.txt:882:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-TEACHER]
backend\tests_list.txt:883:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-PARENT]
backend\tests_list.txt:884:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-admin]
backend\tests_list.txt:885:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-SCHOOL_ADMIN]
backend\tests_list.txt:886:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-BOARD_MEMBER]
backend\tests_list.txt:887:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-FINANCE]
backend\tests_list.txt:888:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-ADMISSIONS]
backend\tests_list.txt:889:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-TEACHER]
backend\tests_list.txt:890:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-PARENT]
backend\tests_list.txt:891:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-admin]
backend\tests_list.txt:892:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-SCHOOL_ADMIN]
backend\tests_list.txt:893:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-BOARD_MEMBER]
backend\tests_list.txt:894:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-FINANCE]
backend\tests_list.txt:895:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-ADMISSIONS]
backend\tests_list.txt:896:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-TEACHER]
backend\tests_list.txt:897:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-PARENT]
backend\tests_list.txt:898:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-admin]
backend\tests_list.txt:899:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-SCHOOL_ADMIN]
backend\tests_list.txt:900:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-BOARD_MEMBER]
backend\tests_list.txt:901:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-FINANCE]
backend\tests_list.txt:902:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-ADMISSIONS]
backend\tests_list.txt:903:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-TEACHER]
backend\tests_list.txt:904:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-PARENT]
backend\tests_list.txt:905:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-admin]
backend\tests_list.txt:906:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-SCHOOL_ADMIN]
backend\tests_list.txt:907:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-BOARD_MEMBER]
backend\tests_list.txt:908:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-FINANCE]
backend\tests_list.txt:909:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-ADMISSIONS]
backend\tests_list.txt:910:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-TEACHER]
backend\tests_list.txt:911:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-PARENT]
backend\tests_list.txt:912:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_health_]
backend\tests_list.txt:913:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_finance_]
backend\tests_list.txt:914:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_admissions_]
backend\tests_list.txt:915:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_academics_]
backend\tests_list.txt:916:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_metrics_]
backend\tests_list.txt:917:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_dashboard_]
backend\tests_list.txt:918:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_snapshots_]
backend\tests_list.txt:919:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_packets_]
backend\tests_list.txt:920:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_financial-aid_summary_]
backend\tests_list.txt:921:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_households_]
backend\tests_list.txt:922:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_students_]
backend\tests_list.txt:923:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_public_endpoint_always_200[/api/health/]
backend\tests_list.txt:924:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_health_returns_build_sha_key
backend\tests_list.txt:925:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/metrics/]
backend\tests_list.txt:926:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/dashboard/]
backend\tests_list.txt:927:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/snapshots/]
backend\tests_list.txt:928:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/packets/]
backend\tests_list.txt:929:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/financial-aid/summary/]
backend\tests_list.txt:930:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_non_staff_enroll_returns_403
backend\tests_list.txt:931:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_staff_enroll_passes_gate
backend\tests_list.txt:932:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_unauthenticated_enroll_returns_401
backend\tests_list.txt:933:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_non_staff_can_post_installment_plan
backend\tests_list.txt:934:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_staff_can_post_installment_plan
backend\tests_list.txt:935:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_unauthenticated_installment_plan_post_returns_401
backend\tests_list.txt:936:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancialAidApplicationsRbacTests::test_authenticated_user_can_attempt_faid_application_post
backend\tests_list.txt:937:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancialAidApplicationsRbacTests::test_unauthenticated_faid_application_post_returns_401
backend\tests_list.txt:938:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_authenticated_payment_intent_passes_auth_gate
backend\tests_list.txt:939:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_no_write_without_school_context
backend\tests_list.txt:940:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_unauthenticated_payment_intent_returns_401
backend\tests_list.txt:941:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_forbidden_without_role
backend\tests_list.txt:942:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_allows_admin_via_demo_header
backend\tests_list.txt:943:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_ignores_demo_header_when_flag_disabled
backend\tests_list.txt:952:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/health/]
backend\tests_list.txt:953:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/metrics/]
backend\tests_list.txt:954:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/dashboard/]
backend\tests_list.txt:955:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/snapshots/]
backend\tests_list.txt:956:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/packets/]
backend\tests_list.txt:959:backend/crown_api/tests/test_seed_edge_cases.py::test_missing_school_id_header_not_500[/api/v1/board/metrics/]
backend\tests_list.txt:960:backend/crown_api/tests/test_seed_edge_cases.py::test_missing_school_id_header_not_500[/api/v1/board/dashboard/]
backend\tests_list.txt:961:backend/crown_api/tests/test_seed_edge_cases.py::test_malformed_school_id_not_500[/api/v1/board/metrics/-0]
backend\tests_list.txt:962:backend/crown_api/tests/test_seed_edge_cases.py::test_malformed_school_id_not_500[/api/v1/board/metrics/--1]
backend\tests_list.txt:963:backend/crown_api/tests/test_seed_edge_cases.py::test_malformed_school_id_not_500[/api/v1/board/metrics/-abc]
backend\tests_list.txt:964:backend/crown_api/tests/test_seed_edge_cases.py::test_malformed_school_id_not_500[/api/v1/board/metrics/-null]
backend\tests_list.txt:965:backend/crown_api/tests/test_seed_edge_cases.py::test_malformed_school_id_not_500[/api/v1/board/metrics/-]
backend\tests_list.txt:970:backend/crown_api/tests/test_tenant_enforcement.py::test_tenant_resolves_from_jwt_user_school_id
backend\tests_list.txt:971:backend/crown_api/tests/test_tenant_enforcement.py::test_protected_endpoint_requires_tenant_when_no_jwt_and_no_header
backend\tests_list.txt:972:backend/crown_api/tests/test_tenant_enforcement.py::test_cross_tenant_header_does_not_override_jwt_tenant
backend\tests_list.txt:973:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_unauthenticated_read_blocked
backend\tests_list.txt:974:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_user_a_can_read_own_school_applications
backend\tests_list.txt:975:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_user_b_cannot_read_school_a_applications
backend\tests_list.txt:976:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantWriteTests::test_cross_tenant_post_does_not_create_in_school_b_either
backend\tests_list.txt:977:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantWriteTests::test_user_b_cannot_post_into_school_a
backend\tests_list.txt:978:backend/crown_api/tests/test_tenant_isolation_writes.py::AidAwardCrossTenantTests::test_school_a_award_not_visible_in_school_b_listing
backend\tests_list.txt:979:backend/crown_api/tests/test_tenant_isolation_writes.py::AidAwardCrossTenantTests::test_user_b_cannot_read_school_a_awards
backend\tests_list.txt:980:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curriculum_maps_tenant_isolation
backend\tests_list.txt:981:backend/curricula/tests/test_curricula_tenant_isolation.py::test_units_tenant_isolation
backend\tests_list.txt:982:backend/curricula/tests/test_curricula_tenant_isolation.py::test_lessons_tenant_isolation
backend\tests_list.txt:983:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curriculum_filter_by_course
backend\tests_list.txt:984:backend/curricula/tests/test_curricula_tenant_isolation.py::test_unit_filter_by_curriculum_map
backend\tests_list.txt:985:backend/curricula/tests/test_curricula_tenant_isolation.py::test_lesson_filter_by_unit
backend\tests_list.txt:986:backend/curricula/tests/test_curricula_tenant_isolation.py::test_read_only_endpoints_reject_writes
backend\tests_list.txt:987:backend/curricula/tests/test_curricula_tenant_isolation.py::test_unauthenticated_requests_blocked
backend\tests_list.txt:988:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curricula_detail_views_tenant_isolation
backend\tests_list.txt:1028:backend/enrollment_period_wizard/tests/test_views.py::EnrollmentPeriodSinglePerYearTest::test_cross_tenant_isolation
backend\tests_list.txt:1033:backend/facops/tests/test_facops.py::TestLocations::test_list_unauthenticated_denied
backend\tests_list.txt:1035:backend/facops/tests/test_facops.py::TestLocations::test_create_denied_for_readonly_role
backend\tests_list.txt:1036:backend/facops/tests/test_facops.py::TestLocations::test_cross_tenant_isolation
backend\tests_list.txt:1041:backend/facops/tests/test_facops.py::TestAssets::test_asset_cross_tenant
backend\tests_list.txt:1048:backend/facops/tests/test_facops.py::TestWorkOrders::test_cross_tenant_work_orders
backend\tests_list.txt:1053:backend/facops/tests/test_facops.py::TestSafetyIncidents::test_cross_tenant
backend\tests_list.txt:1059:backend/facops/tests/test_facops.py::TestVisitorLogs::test_cross_tenant
backend\tests_list.txt:1066:backend/facops/tests/test_facops.py::TestSecuritySummary::test_unauthenticated_denied
backend\tests_list.txt:1135:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_missing_school_header_returns_fail_closed
backend\tests_list.txt:1136:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_non_staff_cannot_list_obligations
backend\tests_list.txt:1137:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_obligations_scoped_to_school
backend\tests_list.txt:1138:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_unauthenticated_cannot_list_obligations
backend\tests_list.txt:1139:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_valid_school_header_returns_200
backend\tests_list.txt:1140:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_missing_header_fail_closed
backend\tests_list.txt:1141:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_only_shows_own_obligations
backend\tests_list.txt:1149:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_policy_only_visible_to_owning_school
backend\tests_list.txt:1150:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_separate_schools_store_independently
backend\tests_list.txt:1151:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_school_multi_year_scoping
backend\tests_list.txt:1152:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_finance_policy_version_unique_constraint
backend\tests_list.txt:1167:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidTenantIsolation::test_cross_tenant_row_isolation_on_drilldown
backend\tests_list.txt:1168:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidTenantIsolation::test_same_tenant_drilldown_returns_own_data_only
backend\tests_list.txt:1194:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_awards_isolation
backend\tests_list.txt:1195:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_buckets_isolation
backend\tests_list.txt:1196:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:1197:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:1198:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:1257:backend/grade_scale_wizard/tests/test_views.py::GradeScaleSingleActiveTest::test_cross_tenant_isolation
backend\tests_list.txt:1268:backend/grade_weights_wizard/tests/test_views.py::TestGradeWeightsWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1278:backend/gradebook/tests/test_gradebook_list_endpoints.py::test_assignments_list_non_teacher_role_forbidden
backend\tests_list.txt:1279:backend/gradebook/tests/test_gradebook_list_endpoints.py::test_students_list_non_teacher_role_forbidden
backend\tests_list.txt:1286:backend/gradebook/tests/test_gradebook_ro_api.py::test_non_teacher_role_forbidden
backend\tests_list.txt:1293:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_invalid_tenant_header_returns_400
backend\tests_list.txt:1328:backend/guardian_household_wizard/tests/test_views.py::TestGuardianHouseholdWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1335:backend/households/tests/test_households_api.py::test_household_retrieve_is_scoped_forbidden_by_empty_result
backend\tests_list.txt:1337:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_correct_tenant_returns_200
backend\tests_list.txt:1338:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_finance_endpoint_respects_tenant
backend\tests_list.txt:1339:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_invalid_tenant_header_returns_400
backend\tests_list.txt:1340:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_missing_tenant_returns_400
backend\tests_list.txt:1341:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_nonexistent_tenant_returns_404
backend\tests_list.txt:1342:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_queryset_never_crosses_tenants
backend\tests_list.txt:1343:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_staff_can_override_tenant
backend\tests_list.txt:1344:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_wrong_tenant_returns_404_non_staff
backend\tests_list.txt:1381:backend/journal/tests/test_journal_invariants.py::JournalInvariantTests::test_cross_tenant_account_fails
backend\tests_list.txt:1406:backend/ledger/tests/test_ledger_invariants.py::test_invariants_tenant_isolation
backend\tests_list.txt:1407:backend/ledger/tests/test_ledger_invariants.py::test_allocation_cross_tenant_guard
backend\tests_list.txt:1484:backend/onboarding/tests/test_views.py::TestAuth::test_unauthenticated_create_denied
backend\tests_list.txt:1485:backend/onboarding/tests/test_views.py::TestAuth::test_missing_school_header_denied
backend\tests_list.txt:1488:backend/onboarding/tests/test_views.py::TestTenantIsolation::test_cross_school_upload_denied
backend\tests_list.txt:1489:backend/onboarding/tests/test_views.py::TestTenantIsolation::test_cross_school_validate_denied
backend\tests_list.txt:1490:backend/onboarding/tests/test_views.py::TestTenantIsolation::test_cross_school_preview_denied
backend\tests_list.txt:1491:backend/onboarding/tests/test_views.py::TestTenantIsolation::test_cross_school_commit_denied
backend\tests_list.txt:1492:backend/onboarding/tests/test_views.py::TestTenantIsolation::test_cross_school_verify_denied
backend\tests_list.txt:1511:backend/outreach/tests/test_outreach.py::TestTenantIsolation::test_invalid_school_id_400
backend\tests_list.txt:1512:backend/outreach/tests/test_outreach.py::TestTenantIsolation::test_cross_tenant_partner_hidden
backend\tests_list.txt:1522:backend/outreach/tests/test_outreach.py::TestOpportunity::test_cross_tenant_hidden
backend\tests_list.txt:1533:backend/outreach/tests/test_outreach.py::TestServiceLogScoping::test_cross_tenant_not_visible
backend\tests_list.txt:1541:backend/outreach/tests/test_outreach.py::TestBadge::test_cross_tenant_hidden
backend\tests_list.txt:1565:backend/reenrollment/tests/test_views.py::TestAuth::test_unauthenticated_create_denied
backend\tests_list.txt:1566:backend/reenrollment/tests/test_views.py::TestAuth::test_missing_school_header_denied
backend\tests_list.txt:1598:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:1599:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:1600:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_courses_isolation
backend\tests_list.txt:1601:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_sections_isolation
backend\tests_list.txt:1602:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:1674:backend/section_staffing_wizard/tests/test_views.py::TestSectionStaffingWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1675:backend/signals/tests/test_tenant_scoping.py::test_signal_event_scoped_by_school_id
backend\tests_list.txt:1676:backend/signals/tests/test_tenant_scoping.py::test_snapshot_unique_per_day
backend\tests_list.txt:1677:backend/signals/tests/test_tenant_scoping.py::test_cross_school_snapshots_independent
backend\tests_list.txt:1728:backend/spiritual_life/tests/test_spiritual_life.py::TestPastoralNotes::test_tenant_isolation_pastoral_notes
backend\tests_list.txt:1759:backend/student_import_wizard/tests/test_views.py::TestStudentImportWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1763:backend/student_records/tests/test_student_records_routes.py::test_list_scopes_to_tenant_school
backend\tests_list.txt:1764:backend/student_records/tests/test_student_records_routes.py::test_detail_cross_tenant_returns_404
backend\tests_list.txt:1765:backend/student_records/tests/test_student_records_routes.py::test_detail_not_found_returns_404_with_valid_tenant
backend\tests_list.txt:1789:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_requires_auth
backend\tests_list.txt:1790:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_requires_school_header
backend\tests_list.txt:1791:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_returns_snapshot
backend\tests_list.txt:1792:backend/subscriptions/tests/test_permissions_enforcement.py::test_plan_list_authenticated
backend\tests_list.txt:1793:backend/subscriptions/tests/test_permissions_enforcement.py::test_plan_list_requires_auth
backend\tests_list.txt:1794:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_requires_admin
backend\tests_list.txt:1795:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_get_subscription
backend\tests_list.txt:1796:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_get_nonexistent_404
backend\tests_list.txt:1797:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_post_assigns_plan
backend\tests_list.txt:1798:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_post_missing_plan_id
backend\tests_list.txt:1829:backend/term_structure_wizard/tests/test_views.py::TermStructureSingleActiveTest::test_cross_tenant_isolation
backend\tests_list.txt:1840:backend/tests/test_audit_logging_negative.py::TestAuditLoggingNegativeCases::test_audit_logging_unauthenticated_request_is_forbidden
backend\tests_list.txt:1846:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_tenant_school_ids_are_distinct
backend\tests_list.txt:1847:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_user_bound_to_correct_school
backend\tests_list.txt:1848:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1849:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_same_tenant_request_is_allowed
backend\tests_list.txt:1850:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1851:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_isolation_keyword_present_in_source
backend\tests_list.txt:1858:backend/tests/test_board_governance_suite_negative.py::TestBoardGovernanceSuiteNegativeCases::test_board_governance_suite_unauthenticated_request_is_forbidden
backend\tests_list.txt:1864:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_tenant_school_ids_are_distinct
backend\tests_list.txt:1865:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_user_bound_to_correct_school
backend\tests_list.txt:1866:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1867:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_same_tenant_request_is_allowed
backend\tests_list.txt:1868:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1869:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_isolation_keyword_present_in_source
backend\tests_list.txt:1876:backend/tests/test_chaplain_pastoral_care_negative.py::TestChaplainPastoralCareNegativeCases::test_chaplain_pastoral_care_unauthenticated_request_is_forbidden
backend\tests_list.txt:1882:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_tenant_school_ids_are_distinct
backend\tests_list.txt:1883:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_user_bound_to_correct_school
backend\tests_list.txt:1884:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1885:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_same_tenant_request_is_allowed
backend\tests_list.txt:1886:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1887:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_isolation_keyword_present_in_source
backend\tests_list.txt:1894:backend/tests/test_christian_pd_hub_negative.py::TestChristianPdHubNegativeCases::test_christian_pd_hub_unauthenticated_request_is_forbidden
backend\tests_list.txt:1900:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_tenant_school_ids_are_distinct
backend\tests_list.txt:1901:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_user_bound_to_correct_school
backend\tests_list.txt:1902:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1903:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_same_tenant_request_is_allowed
backend\tests_list.txt:1904:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1905:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_isolation_keyword_present_in_source
backend\tests_list.txt:1912:backend/tests/test_communications_negative.py::TestCommunicationsNegativeCases::test_communications_unauthenticated_request_is_forbidden
backend\tests_list.txt:1918:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_tenant_school_ids_are_distinct
backend\tests_list.txt:1919:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_user_bound_to_correct_school
backend\tests_list.txt:1920:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1921:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_same_tenant_request_is_allowed
backend\tests_list.txt:1922:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1923:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_isolation_keyword_present_in_source
backend\tests_list.txt:1930:backend/tests/test_crm_marketing_negative.py::TestCrmMarketingNegativeCases::test_crm_marketing_unauthenticated_request_is_forbidden
backend\tests_list.txt:1936:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_tenant_school_ids_are_distinct
backend\tests_list.txt:1937:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_user_bound_to_correct_school
backend\tests_list.txt:1938:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1939:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_same_tenant_request_is_allowed
backend\tests_list.txt:1940:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1941:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_isolation_keyword_present_in_source
backend\tests_list.txt:1948:backend/tests/test_crown_compass_negative.py::TestCrownCompassNegativeCases::test_crown_compass_unauthenticated_request_is_forbidden
backend\tests_list.txt:1954:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_tenant_school_ids_are_distinct
backend\tests_list.txt:1955:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_user_bound_to_correct_school
backend\tests_list.txt:1956:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1957:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_same_tenant_request_is_allowed
backend\tests_list.txt:1958:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1959:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_isolation_keyword_present_in_source
backend\tests_list.txt:1972:backend/tests/test_document_file_framework_negative.py::TestDocumentFileFrameworkNegativeCases::test_document_file_framework_unauthenticated_request_is_forbidden
backend\tests_list.txt:1978:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_tenant_school_ids_are_distinct
backend\tests_list.txt:1979:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_user_bound_to_correct_school
backend\tests_list.txt:1980:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1981:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_same_tenant_request_is_allowed
backend\tests_list.txt:1982:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1983:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_isolation_keyword_present_in_source
backend\tests_list.txt:1990:backend/tests/test_emergency_medical_negative.py::TestEmergencyMedicalNegativeCases::test_emergency_medical_unauthenticated_request_is_forbidden
backend\tests_list.txt:1996:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_tenant_school_ids_are_distinct
backend\tests_list.txt:1997:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_user_bound_to_correct_school
backend\tests_list.txt:1998:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1999:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_same_tenant_request_is_allowed
backend\tests_list.txt:2000:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2001:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_isolation_keyword_present_in_source
backend\tests_list.txt:2014:backend/tests/test_extended_discipline_negative.py::TestExtendedDisciplineNegativeCases::test_extended_discipline_unauthenticated_request_is_forbidden
backend\tests_list.txt:2020:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_tenant_school_ids_are_distinct
backend\tests_list.txt:2021:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_user_bound_to_correct_school
backend\tests_list.txt:2022:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2023:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_same_tenant_request_is_allowed
backend\tests_list.txt:2024:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2025:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_isolation_keyword_present_in_source
backend\tests_list.txt:2038:backend/tests/test_grade_levels_negative.py::TestGradeLevelsNegativeCases::test_grade_levels_unauthenticated_request_is_forbidden
backend\tests_list.txt:2044:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_tenant_school_ids_are_distinct
backend\tests_list.txt:2045:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_user_bound_to_correct_school
backend\tests_list.txt:2046:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2047:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_same_tenant_request_is_allowed
backend\tests_list.txt:2048:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2049:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_isolation_keyword_present_in_source
backend\tests_list.txt:2056:backend/tests/test_grades_report_cards_negative.py::TestGradesReportCardsNegativeCases::test_grades_report_cards_unauthenticated_request_is_forbidden
backend\tests_list.txt:2062:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_tenant_school_ids_are_distinct
backend\tests_list.txt:2063:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_user_bound_to_correct_school
backend\tests_list.txt:2064:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2065:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_same_tenant_request_is_allowed
backend\tests_list.txt:2066:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2067:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_isolation_keyword_present_in_source
backend\tests_list.txt:2082:backend/tests/test_mission_metrics_negative.py::TestMissionMetricsNegativeCases::test_mission_metrics_unauthenticated_request_is_forbidden
backend\tests_list.txt:2088:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_tenant_school_ids_are_distinct
backend\tests_list.txt:2089:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_user_bound_to_correct_school
backend\tests_list.txt:2090:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2091:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_same_tenant_request_is_allowed
backend\tests_list.txt:2092:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2093:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_isolation_keyword_present_in_source
backend\tests_list.txt:2100:backend/tests/test_mobile_family_app_negative.py::TestMobileFamilyAppNegativeCases::test_mobile_family_app_unauthenticated_request_is_forbidden
backend\tests_list.txt:2106:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_tenant_school_ids_are_distinct
backend\tests_list.txt:2107:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_user_bound_to_correct_school
backend\tests_list.txt:2108:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2109:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_same_tenant_request_is_allowed
backend\tests_list.txt:2110:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2111:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_isolation_keyword_present_in_source
backend\tests_list.txt:2119:backend/tests/test_notifications_framework_negative.py::TestNotificationsFrameworkNegativeCases::test_notifications_framework_unauthenticated_request_is_forbidden
backend\tests_list.txt:2125:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_tenant_school_ids_are_distinct
backend\tests_list.txt:2126:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_user_bound_to_correct_school
backend\tests_list.txt:2127:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2128:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_same_tenant_request_is_allowed
backend\tests_list.txt:2129:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2130:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_isolation_keyword_present_in_source
backend\tests_list.txt:2137:backend/tests/test_nurse_health_office_negative.py::TestNurseHealthOfficeNegativeCases::test_nurse_health_office_unauthenticated_request_is_forbidden
backend\tests_list.txt:2143:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_tenant_school_ids_are_distinct
backend\tests_list.txt:2144:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_user_bound_to_correct_school
backend\tests_list.txt:2145:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2146:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_same_tenant_request_is_allowed
backend\tests_list.txt:2147:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2148:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_isolation_keyword_present_in_source
backend\tests_list.txt:2155:backend/tests/test_parent_portal_negative.py::TestParentPortalNegativeCases::test_parent_portal_unauthenticated_request_is_forbidden
backend\tests_list.txt:2161:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_tenant_school_ids_are_distinct
backend\tests_list.txt:2162:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_user_bound_to_correct_school
backend\tests_list.txt:2163:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2164:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_same_tenant_request_is_allowed
backend\tests_list.txt:2165:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2166:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_isolation_keyword_present_in_source
backend\tests_list.txt:2167:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2168:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2169:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2170:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2171:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2172:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2173:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2174:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2175:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2176:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_cross_tenant_data_isolation_confirmed
backend\tests_list.txt:2177:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2178:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2179:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2180:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2181:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2182:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2183:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2184:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2185:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2186:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2187:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2188:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2189:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2190:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2191:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2198:backend/tests/test_portrait_graduate_negative.py::TestPortraitGraduateNegativeCases::test_portrait_graduate_unauthenticated_request_is_forbidden
backend\tests_list.txt:2204:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_tenant_school_ids_are_distinct
backend\tests_list.txt:2205:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_user_bound_to_correct_school
backend\tests_list.txt:2206:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2207:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_same_tenant_request_is_allowed
backend\tests_list.txt:2208:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2209:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_isolation_keyword_present_in_source
backend\tests_list.txt:2216:backend/tests/test_reporting_data_access_negative.py::TestReportingDataAccessNegativeCases::test_reporting_data_access_unauthenticated_request_is_forbidden
backend\tests_list.txt:2222:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_tenant_school_ids_are_distinct
backend\tests_list.txt:2223:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_user_bound_to_correct_school
backend\tests_list.txt:2224:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2225:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_same_tenant_request_is_allowed
backend\tests_list.txt:2226:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2227:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_isolation_keyword_present_in_source
backend\tests_list.txt:2233:backend/tests/test_reporting_exports_gate.py::test_unauthorized_export_is_denied
backend\tests_list.txt:2242:backend/tests/test_schedule_builder_negative.py::TestScheduleBuilderNegativeCases::test_schedule_builder_unauthenticated_request_is_forbidden
backend\tests_list.txt:2248:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_tenant_school_ids_are_distinct
backend\tests_list.txt:2249:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_user_bound_to_correct_school
backend\tests_list.txt:2250:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2251:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_same_tenant_request_is_allowed
backend\tests_list.txt:2252:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2253:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_isolation_keyword_present_in_source
backend\tests_list.txt:2260:backend/tests/test_school_profile_negative.py::TestSchoolProfileNegativeCases::test_school_profile_unauthenticated_request_is_forbidden
backend\tests_list.txt:2266:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_tenant_school_ids_are_distinct
backend\tests_list.txt:2267:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_user_bound_to_correct_school
backend\tests_list.txt:2268:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2269:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_same_tenant_request_is_allowed
backend\tests_list.txt:2270:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2271:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_isolation_keyword_present_in_source
backend\tests_list.txt:2278:backend/tests/test_school_year_term_negative.py::TestSchoolYearTermNegativeCases::test_school_year_term_unauthenticated_request_is_forbidden
backend\tests_list.txt:2284:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_tenant_school_ids_are_distinct
backend\tests_list.txt:2285:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_user_bound_to_correct_school
backend\tests_list.txt:2286:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2287:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_same_tenant_request_is_allowed
backend\tests_list.txt:2288:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2289:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_isolation_keyword_present_in_source
backend\tests_list.txt:2293:backend/tests/test_seed_academics_demo_command.py::TestSeedAcademicsDemo::test_invalid_school_id_fails_gracefully
backend\tests_list.txt:2305:backend/tests/test_service_outreach_negative.py::TestServiceOutreachNegativeCases::test_service_outreach_unauthenticated_request_is_forbidden
backend\tests_list.txt:2311:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_tenant_school_ids_are_distinct
backend\tests_list.txt:2312:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_user_bound_to_correct_school
backend\tests_list.txt:2313:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2314:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_same_tenant_request_is_allowed
backend\tests_list.txt:2315:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2316:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_isolation_keyword_present_in_source
backend\tests_list.txt:2323:backend/tests/test_shared_design_system_negative.py::TestSharedDesignSystemNegativeCases::test_shared_design_system_unauthenticated_request_is_forbidden
backend\tests_list.txt:2329:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_tenant_school_ids_are_distinct
backend\tests_list.txt:2330:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_user_bound_to_correct_school
backend\tests_list.txt:2331:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2332:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_same_tenant_request_is_allowed
backend\tests_list.txt:2333:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2334:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_isolation_keyword_present_in_source
backend\tests_list.txt:2341:backend/tests/test_shared_frontend_shell_negative.py::TestSharedFrontendShellNegativeCases::test_shared_frontend_shell_unauthenticated_request_is_forbidden
backend\tests_list.txt:2347:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_tenant_school_ids_are_distinct
backend\tests_list.txt:2348:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_user_bound_to_correct_school
backend\tests_list.txt:2349:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2350:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_same_tenant_request_is_allowed
backend\tests_list.txt:2351:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2352:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_isolation_keyword_present_in_source
backend\tests_list.txt:2354:backend/tests/test_shell_backend_seeded_contract.py::ShellBackendSeededContractTests::test_canonical_shell_contract_returns_success_under_seeded_tenant_context
backend\tests_list.txt:2362:backend/tests/test_staff_faculty_negative.py::TestStaffFacultyNegativeCases::test_staff_faculty_unauthenticated_request_is_forbidden
backend\tests_list.txt:2368:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_tenant_school_ids_are_distinct
backend\tests_list.txt:2369:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_user_bound_to_correct_school
backend\tests_list.txt:2370:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2371:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_same_tenant_request_is_allowed
backend\tests_list.txt:2372:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2373:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_isolation_keyword_present_in_source
backend\tests_list.txt:2380:backend/tests/test_student_care_discipline_negative.py::TestStudentCareDisciplineNegativeCases::test_student_care_discipline_unauthenticated_request_is_forbidden
backend\tests_list.txt:2386:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_tenant_school_ids_are_distinct
backend\tests_list.txt:2387:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_user_bound_to_correct_school
backend\tests_list.txt:2388:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2389:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_same_tenant_request_is_allowed
backend\tests_list.txt:2390:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2391:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_isolation_keyword_present_in_source
backend\tests_list.txt:2398:backend/tests/test_student_master_record_negative.py::TestStudentMasterRecordNegativeCases::test_student_master_record_unauthenticated_request_is_forbidden
backend\tests_list.txt:2404:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_tenant_school_ids_are_distinct
backend\tests_list.txt:2405:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_user_bound_to_correct_school
backend\tests_list.txt:2406:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2407:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_same_tenant_request_is_allowed
backend\tests_list.txt:2408:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2409:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_isolation_keyword_present_in_source
backend\tests_list.txt:2416:backend/tests/test_survey_sentiment_negative.py::TestSurveySentimentNegativeCases::test_survey_sentiment_unauthenticated_request_is_forbidden
backend\tests_list.txt:2422:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_tenant_school_ids_are_distinct
backend\tests_list.txt:2423:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_user_bound_to_correct_school
backend\tests_list.txt:2424:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2425:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_same_tenant_request_is_allowed
backend\tests_list.txt:2426:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2427:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_isolation_keyword_present_in_source
backend\tests_list.txt:2428:backend/tests/test_tenant_auto_scope.py::TenantAutoScopeTests::test_queryset_auto_filters_by_school
backend\tests_list.txt:2429:backend/tests/test_tenant_auto_scope.py::TenantAutoScopeTests::test_queryset_empty_without_school_context
backend\tests_list.txt:2430:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_delete_requires_tenant_context
backend\tests_list.txt:2431:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_ops_scoped_to_current_tenant
backend\tests_list.txt:2432:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_update_requires_tenant_context
backend\tests_list.txt:2433:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_context_sets_and_restores
backend\tests_list.txt:2434:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_nested_context_restores_prior
backend\tests_list.txt:2435:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_require_raises_when_missing
backend\tests_list.txt:2436:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_auth_exempt_no_header
backend\tests_list.txt:2437:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_health_exempt_no_header
backend\tests_list.txt:2438:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_options_request_no_header_allowed
backend\tests_list.txt:2439:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_other_api_requires_header
backend\tests_list.txt:2440:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_invalid_uuid_returns_400
backend\tests_list.txt:2441:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_known_school_allows_request_past_middleware
backend\tests_list.txt:2442:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_missing_header_defers_to_auth_on_exempt_route
backend\tests_list.txt:2443:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_unknown_uuid_defers_to_auth_on_exempt_route
backend\tests_list.txt:2444:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_gradebook_sections_missing_header_returns_400
backend\tests_list.txt:2445:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_gradebook_sections_cross_tenant_returns_404
backend\tests_list.txt:2446:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_billing_runs_cross_tenant_returns_404
backend\tests_list.txt:2447:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_admissions_applications_cross_tenant_returns_404
backend\tests_list.txt:2448:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_admissions_enroll_cross_tenant_returns_404
backend\tests_list.txt:2449:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_staff_same_tenant_can_reach_gradebook_surface
backend\tests_list.txt:2450:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_unauthenticated_request_is_denied
backend\tests_list.txt:2451:backend/tests/test_tenant_isolation_smoke.py::TestCrossTenantIsolation::test_cross_tenant_submission_list_hidden
backend\tests_list.txt:2452:backend/tests/test_tenant_isolation_smoke.py::TestCrossTenantIsolation::test_cross_tenant_submission_detail_denied
backend\tests_list.txt:2453:backend/tests/test_tenant_lifecycle_cleanup.py::TestTenantLifecycleCleanup::test_context_cleared_after_exception_request
backend\tests_list.txt:2454:backend/tests/test_tenant_lifecycle_cleanup.py::TestTenantLifecycleCleanup::test_context_cleared_after_ok_request
backend\tests_list.txt:2455:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_bulk_delete_missing_context
backend\tests_list.txt:2456:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_bulk_update_missing_context
backend\tests_list.txt:2457:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_context_required_violation
backend\tests_list.txt:2458:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_cross_tenant_write_violation
backend\tests_list.txt:2459:backend/tests/test_tenant_write_guard.py::TestTenantWriteGuard::test_create_binds_school_when_missing
backend\tests_list.txt:2460:backend/tests/test_tenant_write_guard.py::TestTenantWriteGuard::test_cross_tenant_write_blocked
backend\tests_list.txt:2467:backend/tests/test_transportation_negative.py::TestTransportationNegativeCases::test_transportation_unauthenticated_request_is_forbidden
backend\tests_list.txt:2473:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_tenant_school_ids_are_distinct
backend\tests_list.txt:2474:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_user_bound_to_correct_school
backend\tests_list.txt:2475:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2476:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_same_tenant_request_is_allowed
backend\tests_list.txt:2477:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2478:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_isolation_keyword_present_in_source
backend\tests_list.txt:2485:backend/tests/test_volunteer_family_engagement_negative.py::TestVolunteerFamilyEngagementNegativeCases::test_volunteer_family_engagement_unauthenticated_request_is_forbidden
backend\tests_list.txt:2491:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_tenant_school_ids_are_distinct
backend\tests_list.txt:2492:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_user_bound_to_correct_school
backend\tests_list.txt:2493:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2494:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_same_tenant_request_is_allowed
backend\tests_list.txt:2495:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2496:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_isolation_keyword_present_in_source
backend\tests_list.txt:2500:backend/tests/test_wizard_contract.py::TestWizardTenantIsolation::test_all_wizards_isolate_tenants
backend\tests_list.txt:2512:backend/transportation/tests/test_transportation.py::TestVehicles::test_create_denied_for_readonly_role
backend\tests_list.txt:2515:backend/transportation/tests/test_transportation.py::TestVehicles::test_cross_tenant_isolation
backend\tests_list.txt:2516:backend/transportation/tests/test_transportation.py::TestVehicles::test_unauthenticated_denied
backend\tests_list.txt:2520:backend/transportation/tests/test_transportation.py::TestDrivers::test_cross_tenant
backend\tests_list.txt:2525:backend/transportation/tests/test_transportation.py::TestRoutes::test_stops_action_cross_tenant_denied
backend\tests_list.txt:2526:backend/transportation/tests/test_transportation.py::TestRoutes::test_cross_tenant
backend\tests_list.txt:2529:backend/transportation/tests/test_transportation.py::TestStops::test_cross_tenant
backend\tests_list.txt:2533:backend/transportation/tests/test_transportation.py::TestStudentRiders::test_cross_tenant
backend\tests_list.txt:2536:backend/transportation/tests/test_transportation.py::TestAssignments::test_cross_tenant
backend\tests_list.txt:2540:backend/transportation/tests/test_transportation.py::TestRideEvents::test_cross_tenant
backend\tests_list.txt:2544:backend/transportation/tests/test_transportation.py::TestDispatchRunSheet::test_run_sheet_cross_tenant
backend\tests_list.txt:2546:backend/transportation/tests/test_transportation.py::TestDispatchRunSheet::test_run_sheet_unauthenticated_denied
backend\tests_list.txt:2563:backend/tests/test_platform_provisioning.py::test_create_school_idempotent
backend\tests_list.txt:2626:backend/student360/tests/test_scope_qs_to_school.py::TestScopeQsToSchool::test_uses_school_id_when_present
backend\tests_list.txt:2627:backend/student360/tests/test_scope_qs_to_school.py::TestScopeQsToSchool::test_uses_school_fk_when_no_school_id
backend\tests_list.txt:2628:backend/student360/tests/test_scope_qs_to_school.py::TestScopeQsToSchool::test_school_id_takes_precedence_over_school_fk
backend\tests_list.txt:2629:backend/student360/tests/test_scope_qs_to_school.py::TestScopeQsToSchool::test_school_id_value_is_string
backend\gradebook\tests\test_seed_gradebook_demo.py:28:        school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:37:        school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:42:        school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:50:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\gradebook\tests\test_seed_gradebook_demo.py:54:            school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:61:        Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\gradebook\tests\test_seed_gradebook_demo.py:76:    entries = GradeEntry.objects.filter(school_id=school.id)
backend\gradebook\tests\test_seed_gradebook_demo.py:101:    first_count = GradeEntry.objects.filter(school_id=school.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:106:    second_count = GradeEntry.objects.filter(school_id=school.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:121:    initial_count = GradeEntry.objects.filter(school_id=school.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:129:    new_count = GradeEntry.objects.filter(school_id=school.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:146:        school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:152:    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")
backend\gradebook\tests\test_seed_gradebook_demo.py:159:        school_id=school.id,
backend\gradebook\tests\test_seed_gradebook_demo.py:170:    entries = GradeEntry.objects.filter(school_id=school.id)
backend\gradebook\tests\test_seed_gradebook_demo.py:188:    school1_count = GradeEntry.objects.filter(school_id=school1.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:189:    school2_count = GradeEntry.objects.filter(school_id=school2.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:197:    assert GradeEntry.objects.filter(school_id=school2.id).count() == school2_count, "School 2 entries should be untouched"
backend\gradebook\tests\test_seed_gradebook_demo.py:199:    assert GradeEntry.objects.filter(school_id=school1.id).count() == school1_count, "School 1 should have reseeded entries"
backend\gradebook\tests\test_seed_gradebook_demo.py:210:        GradeEntry.objects.filter(school_id=school.id)
backend\gradebook\tests\test_seed_gradebook_demo.py:218:        GradeEntry.objects.filter(school_id=school.id)
backend\gradebook\tests\test_seed_gradebook_demo.py:237:        count = GradeEntry.objects.filter(school_id=school.id, student_id=student.id).count()
backend\gradebook\tests\test_seed_gradebook_demo.py:249:    entries = GradeEntry.objects.filter(school_id=school.id)
backend\crown_api\tests\test_wave3_alias_auth_parity.py:5:/api/v1/dashboards/* for authentication and tenant enforcement.
backend\crown_api\tests\test_wave3_alias_auth_parity.py:28:        school_id=school.id,
backend\crown_api\tests\test_wave3_alias_auth_parity.py:62:def test_canonical_and_alias_dashboard_summary_missing_tenant_header(auth_client):
backend\crown_api\tests\test_wave3_alias_auth_parity.py:72:def test_canonical_and_alias_dashboard_summary_nonexistent_tenant(auth_client):
backend\crown_api\tests\test_wave3_alias_auth_parity.py:91:    assert canonical.json().get("school_id") == str(school.id)
backend\crown_api\tests\test_wave3_alias_auth_parity.py:92:    assert alias.json().get("school_id") == str(school.id)
backend\crown_api\tests\test_wave3_alias_auth_parity.py:96:def test_canonical_and_alias_admissions_funnel_missing_tenant_header(auth_client):
backend\advancement\tests\test_advancement_stage3_4.py:38:    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=perm)
backend\advancement\tests\test_advancement_stage3_4.py:98:        school_id = uuid.uuid4()
backend\advancement\tests\test_advancement_stage3_4.py:102:            school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:118:        school_id = uuid.uuid4()
backend\advancement\tests\test_advancement_stage3_4.py:122:            school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:131:                school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:147:        school_id = uuid.uuid4()
backend\advancement\tests\test_advancement_stage3_4.py:149:            school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:156:        school_id = uuid.uuid4()
backend\advancement\tests\test_advancement_stage3_4.py:159:            school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:164:            school_id=school_id,
backend\advancement\tests\test_advancement_stage3_4.py:188:            school_id=school.id,
backend\advancement\tests\test_advancement_stage3_4.py:193:            school_id=school.id,
backend\advancement\tests\test_advancement_stage3_4.py:213:            school_id=school.id,
backend\advancement\tests\test_advancement_stage3_4.py:219:            school_id=school.id,
backend\crown_api\tests\test_audit_proof.py:19:def test_audit_recent_forbidden_without_role():
backend\crown_api\tests\test_audit_proof.py:41:    school_id = uuid.uuid4()
backend\crown_api\tests\test_audit_proof.py:42:    req = rf.get("/x", **{"HTTP_X_SCHOOL_ID": str(school_id), "HTTP_X_DEMO_ROLE": "admin"})
backend\crown_api\tests\test_audit_proof.py:50:        school_id=school_id,
backend\gradebook\tests\test_parent_grades_e2e.py:6:- Tenant scoping works (X-School-Id required)
backend\gradebook\tests\test_parent_grades_e2e.py:42:    hh = Household.objects.create(school_id=school.id, name="Test Household")
backend\gradebook\tests\test_parent_grades_e2e.py:44:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:51:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:56:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:61:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:66:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:74:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:93:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:94:        household=Household.objects.create(school_id=school.id, name="HH"),
backend\gradebook\tests\test_parent_grades_e2e.py:109:def test_parent_grades_summary_invalid_tenant_header_returns_400():
backend\gradebook\tests\test_parent_grades_e2e.py:110:    """Malformed UUID in X-School-Id must return 400 (header_invalid path)."""
backend\gradebook\tests\test_parent_grades_e2e.py:114:        school_id=school.id,
backend\gradebook\tests\test_parent_grades_e2e.py:115:        household=Household.objects.create(school_id=school.id, name="HH"),
backend\gradebook\tests\test_parent_grades_e2e.py:200:    hh = Household.objects.create(school_id=school.id, name="HH2")
backend\gradebook\tests\test_parent_grades_e2e.py:202:        school_id=school.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:2:Crown2026 ΓÇö Tenant isolation proof: WRITE operations.
backend\crown_api\tests\test_tenant_isolation_writes.py:4:Extends Phase 7.2 (which covers GET isolation) with mutation-level checks:
backend\crown_api\tests\test_tenant_isolation_writes.py:5:- Cross-tenant CREATE must not succeed (data for School A cannot be injected via School B)
backend\crown_api\tests\test_tenant_isolation_writes.py:6:- Cross-tenant READ of a School A record as School B user ΓåÆ 404 (not 200)
backend\crown_api\tests\test_tenant_isolation_writes.py:7:- Cross-tenant POST/mutate must return 404, not produce or reveal School A data
backend\crown_api\tests\test_tenant_isolation_writes.py:9:Canonical scoping used throughout: households.scoping.get_request_school_id()
backend\crown_api\tests\test_tenant_isolation_writes.py:12:Evidence: TENANT_PRIVACY_CANON.md ┬º3 ΓÇö non-staff cross-tenant ΓåÆ 404, never 403,
backend\crown_api\tests\test_tenant_isolation_writes.py:45:            school_id=self.school_a.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:51:            school_id=self.school_a.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:58:            school_id=self.school_b.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:64:# 1. Cross-tenant READ isolation ΓÇö FinancialAidApplication
backend\crown_api\tests\test_tenant_isolation_writes.py:76:            school_id=self.school_a.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:85:        Cross-tenant data must not be returned even for the same global resource.
backend\crown_api\tests\test_tenant_isolation_writes.py:92:                f"Expected 404 (cross-tenant block). "
backend\crown_api\tests\test_tenant_isolation_writes.py:121:# 2. Cross-tenant WRITE isolation ΓÇö POST to create
backend\crown_api\tests\test_tenant_isolation_writes.py:143:            school_id=self.school_a.id
backend\crown_api\tests\test_tenant_isolation_writes.py:154:        # Primary assertion: cross-tenant POSTs are rejected (404 or 403)
backend\crown_api\tests\test_tenant_isolation_writes.py:158:                f"Cross-tenant POST must be rejected. "
backend\crown_api\tests\test_tenant_isolation_writes.py:166:            school_id=self.school_a.id
backend\crown_api\tests\test_tenant_isolation_writes.py:171:                "Cross-tenant POST must not create records in School A. "
backend\crown_api\tests\test_tenant_isolation_writes.py:176:    def test_cross_tenant_post_does_not_create_in_school_b_either(self):
backend\crown_api\tests\test_tenant_isolation_writes.py:178:        A cross-tenant POST that fails must not silently create records
backend\crown_api\tests\test_tenant_isolation_writes.py:182:            school_id=self.school_b.id
backend\crown_api\tests\test_tenant_isolation_writes.py:194:            school_id=self.school_b.id
backend\crown_api\tests\test_tenant_isolation_writes.py:198:            msg="Cross-tenant POST must not create records in the attacker's own school.",
backend\crown_api\tests\test_tenant_isolation_writes.py:203:# 3. Cross-tenant READ isolation ΓÇö AidAward (awards list)
backend\crown_api\tests\test_tenant_isolation_writes.py:216:            school_id=self.school_a.id,
backend\crown_api\tests\test_tenant_isolation_writes.py:217:            application=None,  # intentionally null for isolation test
backend\crown_api\tests\test_tenant_isolation_writes.py:228:            msg=f"Cross-tenant awards read returned {resp.status_code}, expected 404.",
backend\crown_api\tests\test_tenant_isolation_writes.py:252:                    "Tenant isolation breach."
backend\create_test_grade.py:14:school_id = "7d965a83-e714-413d-86ba-776c4176b50f"
backend\create_test_grade.py:17:section = Section.objects.filter(school_id=school_id).annotate(ecount=Count('enrollments')).filter(ecount__gt=0).first()
backend\create_test_grade.py:24:            school_id=school_id,
backend\create_test_grade.py:35:            school_id=school_id,
backend\crown_api\tests\test_tenant_enforcement.py:12:def _make_user(role="finance", school_id=None, email="t@t.com", password="Passw0rd!"):
backend\crown_api\tests\test_tenant_enforcement.py:13:    if school_id is None:
backend\crown_api\tests\test_tenant_enforcement.py:14:        school_id = uuid4()
backend\crown_api\tests\test_tenant_enforcement.py:19:        school_id=school_id,
backend\crown_api\tests\test_tenant_enforcement.py:31:        school_id=str(user.school_id) if user.school_id else None,
backend\crown_api\tests\test_tenant_enforcement.py:37:def test_tenant_resolves_from_jwt_user_school_id():
backend\crown_api\tests\test_tenant_enforcement.py:39:    school_id = uuid4()
backend\crown_api\tests\test_tenant_enforcement.py:40:    u = _make_user(role="finance", school_id=school_id, email="a@a.com")
backend\crown_api\tests\test_tenant_enforcement.py:47:    assert str(school_id) in str(data)  # permissive check
backend\crown_api\tests\test_tenant_enforcement.py:50:def test_protected_endpoint_requires_tenant_when_no_jwt_and_no_header():
backend\crown_api\tests\test_tenant_enforcement.py:57:def test_cross_tenant_header_does_not_override_jwt_tenant():
backend\crown_api\tests\test_tenant_enforcement.py:61:    u = _make_user(role="finance", school_id=school_a, email="b@b.com")
backend\crown_api\tests\test_tenant_enforcement.py:64:    # Attempt to override tenant via header. Resolver prioritizes JWT.
backend\crown_api\tests\test_tenant_enforcement.py:71:    # JWT tenant (school_a) should be in the response
backend\crown_api\tests\test_tenant_enforcement.py:72:    assert str(school_a) in str(data) or "school_id" in str(data).lower()
backend\crown_api\tests\test_students_api.py:14:        # Create school for multi-tenant scoping
backend\crown_api\tests\test_students_api.py:38:            school_id=self.school.id,
backend\crown_api\tests\test_students_api.py:42:            school_id=self.school.id,
backend\crown_api\tests\test_students_api.py:47:            school_id=self.school.id,
backend\crown_api\tests\test_students_api.py:57:            school_id=self.school.id,
backend\crown_api\tests\test_students_api.py:65:            school_id=self.school.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:79:def _make_event(school_id, name="Gala31") -> Event:
backend\advancement\tests\test_advancement_stage3_1_2_3.py:81:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:90:def _make_seating_map(school_id, name="Map31") -> SeatingMap:
backend\advancement\tests\test_advancement_stage3_1_2_3.py:91:    venue = Venue.objects.create(school_id=school_id, name="Stage31 Arena")
backend\advancement\tests\test_advancement_stage3_1_2_3.py:92:    return SeatingMap.objects.create(school_id=school_id, venue=venue, name=name)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:104:def _setup_event_with_seats(school_id, name="Gala31"):
backend\advancement\tests\test_advancement_stage3_1_2_3.py:106:    event = _make_event(school_id, name=name)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:107:    smap = _make_seating_map(school_id)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:108:    EventSeating.objects.create(school_id=school_id, event=event, seating_map=smap)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:110:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:114:    seats = list(Seat.objects.filter(school_id=school_id, seating_map=smap).order_by("section", "row", "number"))
backend\advancement\tests\test_advancement_stage3_1_2_3.py:130:        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:139:            school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:144:            school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:147:        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:154:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:158:        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:163:        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:180:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:188:        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 2)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:193:            school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:197:        TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:200:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:209:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:215:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:225:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:231:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:239:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:244:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:248:        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 1)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:261:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:267:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:275:        self.assertEqual(TicketSeat.objects.filter(school_id=self.sid, event_id=self.event.id).count(), 1)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:277:        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 0)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:281:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:294:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:299:            school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:303:        TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:306:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:354:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:365:        self.assertEqual(order.school_id, self.sid)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:380:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:392:        self.assertEqual(Ticket.objects.filter(school_id=self.sid, event=self.event).count(), 2)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:393:        self.assertEqual(TicketSeat.objects.filter(school_id=self.sid, event_id=self.event.id).count(), 2)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:401:        self.assertEqual(Ticket.objects.filter(school_id=self.sid, event=self.event).count(), 1)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:406:            school_id=self.sid, event=self.event, seat=seat,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:412:        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 0)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:444:        price = get_section_price(school_id=self.sid, event_id=self.event.id, section="UNKNOWN")
backend\advancement\tests\test_advancement_stage3_1_2_3.py:449:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:452:        price = get_section_price(school_id=self.sid, event_id=self.event.id, section="VIP")
backend\advancement\tests\test_advancement_stage3_1_2_3.py:461:            school_id=self.sid, event_id=event.id, section="VIP", price_cents=5000
backend\advancement\tests\test_advancement_stage3_1_2_3.py:464:            school_id=self.sid, event_id=event.id, section="GEN", price_cents=2500
backend\advancement\tests\test_advancement_stage3_1_2_3.py:469:        total = compute_seats_amount(school_id=self.sid, event_id=event.id, seat_ids=seat_ids)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:481:        result = best_available(school_id=self.sid, event_id=self.event.id, count=3)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:488:                school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:492:            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:494:        result = best_available(school_id=self.sid, event_id=self.event.id, count=3)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:499:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:512:                school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:516:            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:519:            school_id=self.sid, event_id=self.event.id,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:535:            school_id=self.sid, event_id=self.event.id, section="VIP", price_cents=5000
backend\advancement\tests\test_advancement_stage3_1_2_3.py:538:            school_id=self.sid, event_id=self.event.id, section="GEN", price_cents=2500
backend\advancement\tests\test_advancement_stage3_1_2_3.py:543:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:558:                school_id=self.sid, event=self.event,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:562:            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)
backend\advancement\tests\test_advancement_stage3_1_2_3.py:565:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:584:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3_1_2_3.py:594:            EmailOutbox.objects.filter(school_id=self.sid, kind="ticket_delivery").count(), 1
backend\advancement\tests\test_advancement_stage3_1_2_3.py:596:        outbox = EmailOutbox.objects.get(school_id=self.sid, kind="ticket_delivery")
backend\advancement\tests\test_advancement_stage3_1_2_3.py:612:            school_id=self.sid,
backend\crown_api\tests\test_audit_log_contract.py:28:  - school_id and correlation_id are not direct fields; these would need to
backend\crown_api\tests\test_audit_log_contract.py:67:            school_id=self.school.id,
backend\crown_api\tests\test_attendance_tenant_invariants.py:4:Verifies that section_attendance_submit() enforces tenant isolation after
backend\crown_api\tests\test_attendance_tenant_invariants.py:5:the ATTENDANCE_HARDENING_V2 patch (get_request_school_id required=True,
backend\crown_api\tests\test_attendance_tenant_invariants.py:9:  1. Missing X-School-Id header       ΓåÆ 400 (required=True now enforced)
backend\crown_api\tests\test_attendance_tenant_invariants.py:10:  2. Cross-tenant section (school_b)  ΓåÆ 404 (school_id constraint on Section fetch)
backend\crown_api\tests\test_attendance_tenant_invariants.py:11:  3. Cross-tenant student (school_b)  ΓåÆ 404 (student ownership check before write)
backend\crown_api\tests\test_attendance_tenant_invariants.py:12:  4. Valid same-tenant request        ΓåÆ 200 {"ok": true}
backend\crown_api\tests\test_attendance_tenant_invariants.py:49:        # Courses (school_id is a plain UUID field, not FK)
backend\crown_api\tests\test_attendance_tenant_invariants.py:51:            school_id=self.school_a.pk,
backend\crown_api\tests\test_attendance_tenant_invariants.py:56:            school_id=self.school_b.pk,
backend\crown_api\tests\test_attendance_tenant_invariants.py:63:            school_id=self.school_a.pk,
backend\crown_api\tests\test_attendance_tenant_invariants.py:68:            school_id=self.school_b.pk,
backend\crown_api\tests\test_attendance_tenant_invariants.py:119:    # Invariant 1: missing tenant header ΓåÆ 400
backend\crown_api\tests\test_attendance_tenant_invariants.py:123:        """Omitting X-School-Id must return 400 now that required=True is enforced."""
backend\crown_api\tests\test_attendance_tenant_invariants.py:133:    # Invariant 2: cross-tenant section ΓåÆ 404
backend\crown_api\tests\test_attendance_tenant_invariants.py:136:    def test_cross_tenant_section_returns_404(self):
backend\crown_api\tests\test_attendance_tenant_invariants.py:147:    # Invariant 3: cross-tenant student ΓåÆ 404
backend\crown_api\tests\test_attendance_tenant_invariants.py:150:    def test_cross_tenant_student_returns_404(self):
backend\crown_api\tests\test_attendance_tenant_invariants.py:161:    # Invariant 4: valid same-tenant request ΓåÆ 200
backend\crown_api\tests\test_attendance_tenant_invariants.py:164:    def test_valid_same_tenant_request_returns_200(self):
backend\crown_api\tests\test_seed_edge_cases.py:23:# 1. Nonexistent / empty tenant ΓÇö read endpoints must not 500
backend\crown_api\tests\test_seed_edge_cases.py:37:def test_empty_tenant_read_endpoint_never_500(path, monkeypatch):
backend\crown_api\tests\test_seed_edge_cases.py:46:        f"Path {path!r} returned {r.status_code} for empty tenant.\n"
backend\crown_api\tests\test_seed_edge_cases.py:88:def test_missing_school_id_header_not_500(path, monkeypatch):
backend\crown_api\tests\test_seed_edge_cases.py:107:# 4. Zero-value / boundary tenant IDs
backend\crown_api\tests\test_seed_edge_cases.py:111:@pytest.mark.parametrize("bad_school_id", ["0", "-1", "abc", "null", ""])
backend\crown_api\tests\test_seed_edge_cases.py:113:def test_malformed_school_id_not_500(path, bad_school_id, monkeypatch):
backend\crown_api\tests\test_seed_edge_cases.py:118:    c = Client(HTTP_X_DEMO_ROLE="admin", HTTP_X_SCHOOL_ID=bad_school_id)
backend\crown_api\tests\test_seed_edge_cases.py:121:        f"Path {path!r} returned 500 for X-School-ID={bad_school_id!r}\n"
backend\board_oversight\tests\test_board_tenant_required.py:6:def test_missing_school_id_rejected(client, django_user_model):
backend\board_oversight\tests\test_board_tenant_required.py:7:    user = django_user_model.objects.create_user("board_tenant_test", None, TEST_AUTH_SECRET)
backend\board_oversight\tests\test_board_tenant_required.py:9:    # No X-School-Id header ΓÇö should get 400 (ValidationError) or 403 (no permission)
backend\gradebook\tests\test_gradeentry_upsert.py:28:    The tenant middleware fires before DRF permission checks (returns 400 for
backend\gradebook\tests\test_gradeentry_upsert.py:29:    missing X-School-Id), so any of 400/401/403 is acceptable ΓÇö the endpoint
backend\gradebook\tests\test_gradeentry_upsert.py:40:    """Authenticated user with no X-School-Id header is rejected by tenant middleware."""
backend\gradebook\tests\test_gradeentry_upsert.py:48:    # No X-School-Id header ΓåÆ get_request_school_id raises ΓåÆ 400 or 403
backend\advancement\tests\test_advancement_stage3.py:7:  3.  transition_move_stage raises Prospect.DoesNotExist on wrong school_id (tenant isolation)
backend\advancement\tests\test_advancement_stage3.py:21: 17.  AlumniCohortMember unique_together (school_id, cohort, donor) enforced
backend\advancement\tests\test_advancement_stage3.py:22: 18.  Prospect tenant isolation ΓÇö school A cannot see school B prospects via queryset
backend\advancement\tests\test_advancement_stage3.py:77:def _make_donor(school_id, name="Alice Donor") -> Donor:
backend\advancement\tests\test_advancement_stage3.py:78:    return Donor.objects.create(school_id=school_id, name=name, email=f"{name.lower().replace(' ', '_')}@stage3.test")
backend\advancement\tests\test_advancement_stage3.py:81:def _make_prospect(school_id, donor=None) -> Prospect:
backend\advancement\tests\test_advancement_stage3.py:82:    return Prospect.objects.create(school_id=school_id, donor=donor, capacity_tier="tier1")
backend\advancement\tests\test_advancement_stage3.py:85:def _make_event(school_id, name="Stage3 Gala") -> Event:
backend\advancement\tests\test_advancement_stage3.py:87:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3.py:96:def _make_ticket(event, school_id, qr="QR_S3_001") -> Ticket:
backend\advancement\tests\test_advancement_stage3.py:98:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3.py:106:def _make_seating_map(school_id, name="Map A") -> SeatingMap:
backend\advancement\tests\test_advancement_stage3.py:107:    venue = Venue.objects.create(school_id=school_id, name="Stage3 Arena")
backend\advancement\tests\test_advancement_stage3.py:108:    return SeatingMap.objects.create(school_id=school_id, venue=venue, name=name)
backend\advancement\tests\test_advancement_stage3.py:119:def _make_sponsorship_agreement(school_id) -> SponsorshipAgreement:
backend\advancement\tests\test_advancement_stage3.py:121:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3.py:126:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3.py:134:def _make_deliverable(school_id, agreement, deliverable_type="banner") -> SponsorshipDeliverable:
backend\advancement\tests\test_advancement_stage3.py:136:        school_id=school_id,
backend\advancement\tests\test_advancement_stage3.py:157:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:164:        self.assertEqual(move.school_id, self.sid)
backend\advancement\tests\test_advancement_stage3.py:170:                school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:181:                school_id=other_sid,
backend\advancement\tests\test_advancement_stage3.py:191:                school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:197:        moves = Move.objects.filter(school_id=self.sid, prospect=self.prospect).order_by("created_at")
backend\advancement\tests\test_advancement_stage3.py:203:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:227:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:232:        self.assertEqual(Seat.objects.filter(school_id=self.sid, seating_map=self.smap).count(), 14)
backend\advancement\tests\test_advancement_stage3.py:236:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:243:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:248:        total = Seat.objects.filter(school_id=self.sid, seating_map=self.smap).count()
backend\advancement\tests\test_advancement_stage3.py:256:                school_id=other_sid,
backend\advancement\tests\test_advancement_stage3.py:263:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:282:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:287:        self.seats = list(Seat.objects.filter(school_id=self.sid, seating_map=self.smap)[:3])
backend\advancement\tests\test_advancement_stage3.py:294:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:304:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:310:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:320:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:327:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:338:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:343:        SeatHold.objects.filter(school_id=self.sid, event_id=self.event.id).update(
backend\advancement\tests\test_advancement_stage3.py:348:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:367:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:373:        self.seat = Seat.objects.filter(school_id=self.sid, seating_map=self.smap).first()
backend\advancement\tests\test_advancement_stage3.py:377:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:384:        self.assertEqual(ts.school_id, self.sid)
backend\advancement\tests\test_advancement_stage3.py:388:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:395:                school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:405:                school_id=other_sid,
backend\advancement\tests\test_advancement_stage3.py:425:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:433:        self.assertEqual(imp.school_id, self.sid)
backend\advancement\tests\test_advancement_stage3.py:439:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:452:                school_id=other_sid,
backend\advancement\tests\test_advancement_stage3.py:470:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:477:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:484:                school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:491:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage3.py:495:        AlumniCohortMember.objects.create(school_id=self.sid, cohort=self.cohort, donor=self.donor)
backend\advancement\tests\test_advancement_stage3.py:496:        AlumniCohortMember.objects.create(school_id=self.sid, cohort=cohort2, donor=self.donor)
backend\advancement\tests\test_advancement_stage3.py:498:            AlumniCohortMember.objects.filter(school_id=self.sid, donor=self.donor).count(), 2
backend\advancement\tests\test_advancement_stage3.py:503:# 18: Prospect tenant isolation
backend\advancement\tests\test_advancement_stage3.py:519:        qs_a = Prospect.objects.filter(school_id=self.sid_a)
backend\advancement\tests\test_advancement_stage3.py:520:        qs_b = Prospect.objects.filter(school_id=self.sid_b)
backend\advancement\tests\test_advancement_stage3.py:528:        prospect_a = Prospect.objects.filter(school_id=self.sid_a).first()
backend\advancement\tests\test_advancement_stage3.py:531:                school_id=self.sid_b,
backend\core\tests\test_scoping.py:49:        self.school_id = uuid.uuid4()
backend\core\tests\test_scoping.py:63:        hh = Household.objects.create(school_id=self.school_id, name="Smith Family")
backend\core\tests\test_scoping.py:65:            school_id=self.school_id, household=hh,
backend\core\tests\test_scoping.py:69:            school_id=self.school_id, household=hh,
backend\core\tests\test_scoping.py:74:            school_id=self.school_id, code="MATH001", name="Math"
backend\core\tests\test_scoping.py:77:            school_id=self.school_id,
backend\core\tests\test_scoping.py:83:            school_id=self.school_id,
backend\core\tests\test_scoping.py:89:        qs = Student.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:96:        qs = Student.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:108:        self.school_id = uuid.uuid4()
backend\core\tests\test_scoping.py:116:        own_hh = Household.objects.create(school_id=self.school_id, name="Own Family")
backend\core\tests\test_scoping.py:118:            school_id=self.school_id,
backend\core\tests\test_scoping.py:124:            school_id=self.school_id, household=own_hh,
backend\core\tests\test_scoping.py:129:        other_hh = Household.objects.create(school_id=self.school_id, name="Other Family")
backend\core\tests\test_scoping.py:131:            school_id=self.school_id, household=other_hh,
backend\core\tests\test_scoping.py:136:        qs = Student.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:149:        qs = Student.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:159:        qs = Student.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:170:        self.school_id = uuid.uuid4()
backend\core\tests\test_scoping.py:179:        own_hh = Household.objects.create(school_id=self.school_id, name="Own Family")
backend\core\tests\test_scoping.py:181:            school_id=self.school_id,
backend\core\tests\test_scoping.py:189:            school_id=self.school_id,
backend\core\tests\test_scoping.py:194:            school_id=self.school_id,
backend\core\tests\test_scoping.py:200:        qs = FinancialAidApplication.objects.filter(school_id=self.school_id)
backend\core\tests\test_scoping.py:212:        qs = FinancialAidApplication.objects.filter(school_id=self.school_id)
backend\crown_api\tests\test_role_escalation.py:5:role through the API.  These tests exercise permission-layer hardening
backend\crown_api\tests\test_rbac_proof.py:7:def test_rbac_finance_proof_forbidden_without_role():
backend\crown_api\tests\test_rbac_proof.py:9:    resp = c.get("/api/system/rbac/finance-proof/")
backend\crown_api\tests\test_rbac_proof.py:18:def test_rbac_finance_proof_allows_admin_via_demo_header(monkeypatch):
backend\crown_api\tests\test_rbac_proof.py:22:    resp = c.get("/api/system/rbac/finance-proof/")
backend\crown_api\tests\test_rbac_proof.py:30:def test_rbac_finance_proof_ignores_demo_header_when_flag_disabled(monkeypatch):
backend\crown_api\tests\test_rbac_proof.py:34:    resp = c.get("/api/system/rbac/finance-proof/")
backend\core\tests\test_rbac_contract.py:25:def _client_for(user, school_id):
backend\core\tests\test_rbac_contract.py:28:    c.credentials(HTTP_X_SCHOOL_ID=str(school_id))
backend\core\tests\test_rbac_contract.py:32:def _anon_client(school_id=None):
backend\core\tests\test_rbac_contract.py:34:    if school_id:
backend\core\tests\test_rbac_contract.py:35:        c.credentials(HTTP_X_SCHOOL_ID=str(school_id))
backend\core\tests\test_rbac_contract.py:62:    # Unauthed should not be allowed even with tenant header.
backend\core\tests\test_rbac_contract.py:63:    c = _anon_client(school_id=school.id)
backend\core\tests\test_rbac_contract.py:68:def test_requires_tenant_header_for_invariants(users, school):
backend\core\tests\test_rbac_contract.py:69:    # Authed without tenant header should fail fast (tenant enforcement).
backend\crown_api\tests\test_rbac_matrix_writes.py:53:            username="rbacw_staff",
backend\crown_api\tests\test_rbac_matrix_writes.py:54:            email="rbacw_staff@example.com",
backend\crown_api\tests\test_rbac_matrix_writes.py:56:            school_id=self.school.id,
backend\crown_api\tests\test_rbac_matrix_writes.py:60:            username="rbacw_user",
backend\crown_api\tests\test_rbac_matrix_writes.py:61:            email="rbacw_user@example.com",
backend\crown_api\tests\test_rbac_matrix_writes.py:63:            school_id=self.school.id,
backend\crown_api\tests\test_rbac_matrix_writes.py:208:    Unauthenticated ΓåÆ 401; authenticated cross-tenant ΓåÆ 404; own-school ΓåÆ 400/201.
backend\crown_api\tests\test_rbac_matrix_writes.py:292:        get_request_school_id(required=True) should block or error.
backend\crown_api\tests\test_rbac_matrix_readonly.py:10:Fixture file: fixtures/rbac_endpoints_readonly.txt
backend\crown_api\tests\test_rbac_matrix_readonly.py:25:FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rbac_endpoints_readonly.txt"
backend\crown_api\tests\test_rbac_matrix_readonly.py:49:    if "rbac_path" in metafunc.fixturenames:
backend\crown_api\tests\test_rbac_matrix_readonly.py:50:        metafunc.parametrize("rbac_path", _load_endpoints(), ids=lambda p: p.replace("/", "_"))
backend\crown_api\tests\test_rbac_matrix_readonly.py:51:    if "rbac_role" in metafunc.fixturenames:
backend\crown_api\tests\test_rbac_matrix_readonly.py:52:        metafunc.parametrize("rbac_role", ROLES)
backend\crown_api\tests\test_rbac_matrix_readonly.py:56:def test_readonly_endpoint_never_500(rbac_path, rbac_role, monkeypatch):
backend\crown_api\tests\test_rbac_matrix_readonly.py:62:    c = Client(HTTP_X_DEMO_ROLE=rbac_role, HTTP_X_SCHOOL_ID="1")
backend\crown_api\tests\test_rbac_matrix_readonly.py:63:    r = c.get(rbac_path)
backend\crown_api\tests\test_rbac_matrix_readonly.py:65:        f"HTTP 500 on GET {rbac_path!r} with role={rbac_role!r}\n"
backend\crown_api\tests\test_rbac_matrix_readonly.py:71:def test_readonly_endpoint_unauthenticated_never_500(rbac_path):
backend\crown_api\tests\test_rbac_matrix_readonly.py:77:    r = c.get(rbac_path)
backend\crown_api\tests\test_rbac_matrix_readonly.py:79:        f"HTTP 500 on unauthenticated GET {rbac_path!r}\n"
backend\board_oversight\tests\test_board_rbac.py:8:def test_non_board_user_forbidden(client, django_user_model):
backend\board_oversight\tests\test_board_rbac.py:9:    user = django_user_model.objects.create_user("rbac_test_non_board", None, TEST_AUTH_SECRET)
backend\advancement\tests\test_advancement_stage2.py:21: 17.  Gift tenant isolation ΓÇö school A cannot see school B gifts
backend\advancement\tests\test_advancement_stage2.py:22: 18.  Pledge tenant isolation
backend\advancement\tests\test_advancement_stage2.py:23: 19.  SponsorshipAgreement tenant isolation
backend\advancement\tests\test_advancement_stage2.py:72:def _make_donor(school_id, name="Alice Donor") -> Donor:
backend\advancement\tests\test_advancement_stage2.py:73:    return Donor.objects.create(school_id=school_id, name=name, email="alice@donor.test")
backend\advancement\tests\test_advancement_stage2.py:76:def _make_campaign(school_id, goal="50000") -> Campaign:
backend\advancement\tests\test_advancement_stage2.py:78:        school_id=school_id,
backend\advancement\tests\test_advancement_stage2.py:85:def _make_package(school_id, price="1000") -> SponsorshipPackage:
backend\advancement\tests\test_advancement_stage2.py:87:        school_id=school_id,
backend\advancement\tests\test_advancement_stage2.py:93:def _make_event(school_id, capacity=5) -> Event:
backend\advancement\tests\test_advancement_stage2.py:95:        school_id=school_id,
backend\advancement\tests\test_advancement_stage2.py:104:def _make_ticket(event, school_id, qr="QR_STAGE2_001", checked_in=False) -> Ticket:
backend\advancement\tests\test_advancement_stage2.py:106:        school_id=school_id,
backend\advancement\tests\test_advancement_stage2.py:156:        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("250.00"))
backend\advancement\tests\test_advancement_stage2.py:159:        self.assertEqual(gift.school_id, self.sid)
backend\advancement\tests\test_advancement_stage2.py:162:        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("100.00"))
backend\advancement\tests\test_advancement_stage2.py:167:        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("300.00"))
backend\advancement\tests\test_advancement_stage2.py:168:        paid = mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:172:        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("150.00"))
backend\advancement\tests\test_advancement_stage2.py:173:        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:174:        txn = AdvancementTransaction.objects.filter(school_id=self.sid, category="donation").last()
backend\advancement\tests\test_advancement_stage2.py:181:            school_id=self.sid, amount=Decimal("500.00"), donor_id=donor.id
backend\advancement\tests\test_advancement_stage2.py:183:        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:190:            school_id=self.sid, amount=Decimal("1000.00"), campaign_id=campaign.id
backend\advancement\tests\test_advancement_stage2.py:192:        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:198:        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("75.00"))
backend\advancement\tests\test_advancement_stage2.py:199:        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:201:            mark_gift_paid(gift_id=gift.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:203:    def test_gift_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage2.py:207:        gift_a = create_gift_checkout(school_id=sid_a, amount=Decimal("50.00"))
backend\advancement\tests\test_advancement_stage2.py:208:        self.assertEqual(Gift.objects.filter(school_id=sid_b).count(), 0)
backend\advancement\tests\test_advancement_stage2.py:209:        self.assertEqual(Gift.objects.filter(school_id=sid_a, id=gift_a.id).count(), 1)
backend\advancement\tests\test_advancement_stage2.py:224:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:231:        self.assertEqual(pledge.school_id, self.sid)
backend\advancement\tests\test_advancement_stage2.py:235:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:239:        cancelled = cancel_pledge(pledge_id=pledge.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:244:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:248:        cancel_pledge(pledge_id=pledge.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:250:            cancel_pledge(pledge_id=pledge.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:252:    def test_pledge_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage2.py:255:        create_pledge(school_id=self.sid, total_amount=Decimal("400.00"), start_date=date.today())
backend\advancement\tests\test_advancement_stage2.py:256:        self.assertEqual(Pledge.objects.filter(school_id=sid_b).count(), 0)
backend\advancement\tests\test_advancement_stage2.py:272:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:282:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:290:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:294:        active = mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:299:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:303:        mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:305:            school_id=self.sid, category="sponsorship"
backend\advancement\tests\test_advancement_stage2.py:312:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:316:        mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:318:            mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:320:    def test_agreement_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage2.py:324:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage2.py:328:        self.assertEqual(SponsorshipAgreement.objects.filter(school_id=sid_b).count(), 0)
backend\advancement\tests\test_advancement_stage2.py:344:        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_VALID_001")
backend\advancement\tests\test_advancement_stage2.py:353:        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DUP_001")
backend\advancement\tests\test_advancement_stage2.py:357:        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DOES_NOT_EXIST")
backend\advancement\tests\test_advancement_stage2.py:365:        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_OK_002")
backend\advancement\tests\test_advancement_stage2.py:366:        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DUP_002")
backend\advancement\tests\test_advancement_stage2.py:367:        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_MISSING")
backend\advancement\tests\test_advancement_stage2.py:368:        scans = TicketScan.objects.filter(school_id=self.sid)
backend\advancement\tests\test_advancement_stage2.py:380:        scan = check_in_ticket_by_qr(school_id=other_sid, qr_code="QR_CROSS_001")
backend\gradebook\tests\test_gradebook_section_summary.py:43:        school_id=school.id,
backend\gradebook\tests\test_gradebook_section_summary.py:52:        school_id=school.id,
backend\gradebook\tests\test_gradebook_section_summary.py:57:        school_id=school.id,
backend\gradebook\tests\test_gradebook_section_summary.py:65:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\gradebook\tests\test_gradebook_section_summary.py:69:            school_id=school.id,
backend\gradebook\tests\test_gradebook_section_summary.py:76:        Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\gradebook\tests\test_gradebook_section_summary.py:96:    section_id = GradeEntry.objects.filter(school_id=school.id).values_list("section_id", flat=True).first()
backend\gradebook\tests\test_gradebook_section_summary.py:124:    section_id = GradeEntry.objects.filter(school_id=school.id).values_list("section_id", flat=True).first()
backend\core\tests\test_permission_engine.py:1:# backend/core/tests/test_permission_engine.py
backend\core\tests\test_permission_engine.py:6:#   - user_has_permission() truth / denial / school scoping / anon
backend\core\tests\test_permission_engine.py:7:#   - require_permission() decorator  ΓåÆ  200 / 403 / 401 paths
backend\core\tests\test_permission_engine.py:9:#   - seed_permissions management command idempotency
backend\core\tests\test_permission_engine.py:18:from core.permissions import require_permission, user_has_permission
backend\core\tests\test_permission_engine.py:41:def _grant(role_code, permission_code):
backend\core\tests\test_permission_engine.py:42:    perm = _perm(permission_code)
backend\core\tests\test_permission_engine.py:43:    obj, _ = RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\core\tests\test_permission_engine.py:52:# user_has_permission ΓÇö basic grant / deny
backend\core\tests\test_permission_engine.py:63:        assert user_has_permission(user, "finance.view") is True
backend\core\tests\test_permission_engine.py:71:        assert user_has_permission(user, "finance.view") is False
backend\core\tests\test_permission_engine.py:73:    def test_returns_false_for_nonexistent_permission(self):
backend\core\tests\test_permission_engine.py:78:        assert user_has_permission(user, "nonexistent.code") is False
backend\core\tests\test_permission_engine.py:84:        assert user_has_permission(user, "finance.view") is False
backend\core\tests\test_permission_engine.py:91:        assert user_has_permission(anon, "finance.view") is False
backend\core\tests\test_permission_engine.py:95:# user_has_permission ΓÇö school scoping
backend\core\tests\test_permission_engine.py:106:        assert user_has_permission(user, "finance.view", school=school) is True
backend\core\tests\test_permission_engine.py:116:        assert user_has_permission(user, "finance.view", school=school_b) is False
backend\core\tests\test_permission_engine.py:124:        # No school filter ΓÇö should still find the permission
backend\core\tests\test_permission_engine.py:125:        assert user_has_permission(user, "finance.edit") is True
backend\core\tests\test_permission_engine.py:129:# require_permission decorator
backend\core\tests\test_permission_engine.py:138:        @require_permission(perm_code)
backend\core\tests\test_permission_engine.py:144:    def test_allows_request_when_permission_granted(self):
backend\core\tests\test_permission_engine.py:159:    def test_denies_request_when_permission_missing(self):
backend\core\tests\test_permission_engine.py:204:        assert body.get("detail") == "Permission denied."
backend\core\tests\test_permission_engine.py:230:    def test_crown_permission_code_is_unique(self):
backend\core\tests\test_permission_engine.py:237:    def test_role_permission_unique_together(self):
backend\core\tests\test_permission_engine.py:241:        RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:243:            RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:245:    def test_crown_permission_str(self):
backend\core\tests\test_permission_engine.py:246:        perm = _perm("str.test", "A test permission")
backend\core\tests\test_permission_engine.py:249:    def test_role_permission_str(self):
backend\core\tests\test_permission_engine.py:251:        rp = RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:256:# seed_permissions management command
backend\core\tests\test_permission_engine.py:261:    def test_seed_creates_permissions(self):
backend\core\tests\test_permission_engine.py:265:        call_command("seed_permissions", stdout=out)
backend\core\tests\test_permission_engine.py:272:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:275:            permission__code="finance.view",
backend\core\tests\test_permission_engine.py:279:            permission__code="finance.edit",
backend\core\tests\test_permission_engine.py:285:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:287:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:294:        call_command("seed_permissions", dry_run=True, stdout=StringIO())
backend\billing\tests\test_lane2_payment_endpoints.py:11:    school_id = getattr(settings, "DEMO_SCHOOL_ID", None) or os.environ.get("CROWN_DEMO_SCHOOL_ID")
backend\billing\tests\test_lane2_payment_endpoints.py:12:    if not school_id:
backend\billing\tests\test_lane2_payment_endpoints.py:16:    client.credentials(HTTP_X_SCHOOL_ID=str(school_id))
backend\crown_api\tests\test_object_level_permissions.py:4:This module tests authorization boundaries WITHIN the same tenant (school).
backend\crown_api\tests\test_object_level_permissions.py:5:Tenant-level isolation (cross-school) is covered in test_phase72_tenant_isolation.py
backend\crown_api\tests\test_object_level_permissions.py:6:and test_tenant_isolation_writes.py.
backend\crown_api\tests\test_object_level_permissions.py:8:Scope here: same school_id, different users.
backend\crown_api\tests\test_object_level_permissions.py:54:    This simulates the within-tenant object-access scenario.
backend\crown_api\tests\test_object_level_permissions.py:64:            school_id=self.school.id,
backend\crown_api\tests\test_object_level_permissions.py:71:            school_id=self.school.id,
backend\crown_api\tests\test_object_level_permissions.py:84:    users belong to the same school (same tenant).
backend\crown_api\tests\test_object_level_permissions.py:240:        # Should NOT be 403 (staff has school-level permission, not creator-restricted)
backend\crown_api\exports\tests\test_exports_year_end_csv.py:35:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_year_end_csv.py:36:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_year_end_csv.py:37:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_year_end_csv.py:56:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_year_end_csv.py:57:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_year_end_csv.py:58:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_year_end_csv.py:97:    assert rows[0][0] in ("school_id", "error")
backend\advancement\tests\test_advancement_stage1.py:5:  1. Tenant isolation ΓÇö data from school A not visible to school B
backend\advancement\tests\test_advancement_stage1.py:41:    """Stable UUID per integer for repeatable test isolation."""
backend\advancement\tests\test_advancement_stage1.py:50:def _make_event(school_id, *, ticket_price="25.00", capacity=10, active=True) -> Event:
backend\advancement\tests\test_advancement_stage1.py:52:        school_id=school_id,
backend\advancement\tests\test_advancement_stage1.py:61:def _make_donor(school_id, name="Jane Smith") -> Donor:
backend\advancement\tests\test_advancement_stage1.py:62:    return Donor.objects.create(school_id=school_id, name=name, email="jane@example.com")
backend\advancement\tests\test_advancement_stage1.py:65:def _make_campaign(school_id, goal="10000") -> Campaign:
backend\advancement\tests\test_advancement_stage1.py:66:    return Campaign.objects.create(school_id=school_id, name="Capital Campaign", goal=Decimal(goal))
backend\advancement\tests\test_advancement_stage1.py:69:def _make_store_item(school_id, *, price="20.00", inventory=5, active=True) -> StoreItem:
backend\advancement\tests\test_advancement_stage1.py:71:        school_id=school_id,
backend\advancement\tests\test_advancement_stage1.py:79:def _make_package(school_id, *, price="500.00") -> SponsorshipPackage:
backend\advancement\tests\test_advancement_stage1.py:81:        school_id=school_id,
backend\advancement\tests\test_advancement_stage1.py:88:# Test: Tenant isolation
backend\advancement\tests\test_advancement_stage1.py:99:        Donor.objects.create(school_id=self.sid_a, name="School A Donor", email="a@a.com")
backend\advancement\tests\test_advancement_stage1.py:100:        Donor.objects.create(school_id=self.sid_b, name="School B Donor", email="b@b.com")
backend\advancement\tests\test_advancement_stage1.py:102:        Event.objects.create(school_id=self.sid_a, name="A Gala", date=timezone.now(), ticket_price=10, capacity=100)
backend\advancement\tests\test_advancement_stage1.py:103:        Event.objects.create(school_id=self.sid_b, name="B Gala", date=timezone.now(), ticket_price=10, capacity=100)
backend\advancement\tests\test_advancement_stage1.py:106:        donors_a = Donor.objects.filter(school_id=self.sid_a)
backend\advancement\tests\test_advancement_stage1.py:111:        events_b = Event.objects.filter(school_id=self.sid_b)
backend\advancement\tests\test_advancement_stage1.py:117:        donors = Donor.objects.filter(school_id=self.sid_a)
backend\advancement\tests\test_advancement_stage1.py:135:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage1.py:141:        self.assertEqual(ticket.school_id, self.sid)
backend\advancement\tests\test_advancement_stage1.py:147:            school_id=self.sid,
backend\advancement\tests\test_advancement_stage1.py:152:        txn = AdvancementTransaction.objects.get(school_id=self.sid, category="event_ticket")
backend\advancement\tests\test_advancement_stage1.py:157:        t1 = create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P1", purchaser_email="p1@x.com")
backend\advancement\tests\test_advancement_stage1.py:158:        t2 = create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P2", purchaser_email="p2@x.com")
backend\advancement\tests\test_advancement_stage1.py:164:        create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P", purchaser_email="p@x.com")
backend\advancement\tests\test_advancement_stage1.py:170:        create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="First", purchaser_email="f@x.com")
backend\advancement\tests\test_advancement_stage1.py:173:            create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="Second", purchaser_email="s@x.com")
backend\advancement\tests\test_advancement_stage1.py:178:            create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="X", purchaser_email="x@x.com")
backend\advancement\tests\test_advancement_stage1.py:193:        create_store_purchase(school_id=self.sid, item=item, quantity=3)
backend\advancement\tests\test_advancement_stage1.py:199:        create_store_purchase(school_id=self.sid, item=item, quantity=2)
backend\advancement\tests\test_advancement_stage1.py:200:        txn = AdvancementTransaction.objects.get(school_id=self.sid, category="store_purchase")
backend\advancement\tests\test_advancement_stage1.py:206:            create_store_purchase(school_id=self.sid, item=item, quantity=5)
backend\advancement\tests\test_advancement_stage1.py:211:            create_store_purchase(school_id=self.sid, item=item)
backend\advancement\tests\test_advancement_stage1.py:217:            create_store_purchase(school_id=self.sid, item=item, quantity=999)
backend\advancement\tests\test_advancement_stage1.py:236:        txn = create_sponsorship_sale(school_id=self.sid, package=package)
backend\advancement\tests\test_advancement_stage1.py:239:        self.assertEqual(txn.school_id, self.sid)
backend\advancement\tests\test_advancement_stage1.py:244:        txn = create_sponsorship_sale(school_id=self.sid, package=package, campaign=campaign)
backend\advancement\tests\test_advancement_stage1.py:260:        txn = record_donation(school_id=self.sid, donor=donor, amount="250.00")
backend\advancement\tests\test_advancement_stage1.py:267:        record_donation(school_id=self.sid, donor=donor, amount="500.00")
backend\advancement\tests\test_advancement_stage1.py:275:        record_donation(school_id=self.sid, donor=donor, amount="1000.00", campaign=campaign)
backend\advancement\tests\test_advancement_stage1.py:282:            record_donation(school_id=self.sid, donor=donor, amount="-100.00")
backend\advancement\tests\test_advancement_stage1.py:287:            record_donation(school_id=self.sid, donor=donor, amount="0")
backend\gradebook\tests\test_gradebook_ro_api.py:39:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:45:    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")
backend\gradebook\tests\test_gradebook_ro_api.py:47:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:62:    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)
backend\gradebook\tests\test_gradebook_ro_api.py:91:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\gradebook\tests\test_gradebook_ro_api.py:93:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:99:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\gradebook\tests\test_gradebook_ro_api.py:102:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:127:def test_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_ro_api.py:146:    household = Household.objects.create(school_id=school.id, name="Household Z")
backend\gradebook\tests\test_gradebook_ro_api.py:148:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:154:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\gradebook\tests\test_gradebook_ro_api.py:157:        school_id=school.id,
backend\gradebook\tests\test_gradebook_ro_api.py:165:        school_id=school.id,
backend\crown_api\tests\test_middleware_api_exceptions.py:17:# Unit tests for the middleware in isolation
backend\billing\tests\test_lane2_billing_smoke.py:23:    school_id = getattr(settings, "DEMO_SCHOOL_ID", None) or os.environ.get("CROWN_DEMO_SCHOOL_ID")
backend\billing\tests\test_lane2_billing_smoke.py:24:    if not school_id:
backend\billing\tests\test_lane2_billing_smoke.py:27:    client.credentials(HTTP_X_SCHOOL_ID=str(school_id))
backend\core\tests\test_nav_endpoint.py:3:# Tests for GET /api/v1/nav/ (permission-derived navigation).
backend\core\tests\test_nav_endpoint.py:6:# TenantHeaderRequiredMiddleware enforces X-School-Id for /api/v1/* routes and
backend\core\tests\test_nav_endpoint.py:7:# sets request.school; the nav view filters NAV_ITEMS by user permissions.
backend\core\tests\test_nav_endpoint.py:21:def _enable_tenant_middleware(settings):
backend\core\tests\test_nav_endpoint.py:50:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\core\tests\test_nav_endpoint.py:69:    def test_missing_school_id_header_returns_400(self):
backend\core\tests\test_nav_endpoint.py:70:        """Middleware must reject /api/v1/nav/ with no X-School-Id."""
backend\core\tests\test_nav_endpoint.py:75:    def test_unknown_school_id_returns_404(self):
backend\core\tests\test_nav_endpoint.py:76:        """Middleware must reject an X-School-Id that doesn't resolve to a School."""
backend\core\tests\test_nav_endpoint.py:159:        # No roles assigned, no permissions granted
backend\core\tests\test_nav_endpoint.py:242:    def test_school_scoping_cross_tenant_isolation(self):
backend\billing_wizard\tests\test_views.py:49:def _headers(school_id):
backend\billing_wizard\tests\test_views.py:50:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\billing_wizard\tests\test_views.py:57:    c._school_id = school.id
backend\billing_wizard\tests\test_views.py:99:    def test_configure_isolation(self):
backend\billing_wizard\tests\test_views.py:103:    def test_plans_isolation(self):
backend\billing_wizard\tests\test_views.py:107:    def test_fees_isolation(self):
backend\billing_wizard\tests\test_views.py:111:    def test_commit_isolation(self):
backend\billing_wizard\tests\test_views.py:115:    def test_verify_isolation(self):
backend\billing_wizard\tests\test_views.py:324:        count = InstallmentPlan.objects.filter(school_id=self.school.id, term="2026-FALL").count()
backend\billing_wizard\tests\test_views.py:333:        count = InstallmentPlan.objects.filter(school_id=self.school.id, term="2026-FALL").count()
backend\crown_api\exports\tests\test_exports_throttling.py:22:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_throttling.py:23:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_throttling.py:24:        u.save(update_fields=["school_id"])
backend\crown_api\tests\test_metrics_permissions_contract.py:1:# backend/crown_api/tests/test_metrics_permissions_contract.py
backend\crown_api\tests\test_metrics_permissions_contract.py:3:# Contract tests: every /api/v1/*/metrics/ endpoint must enforce permissions.
backend\crown_api\tests\test_metrics_permissions_contract.py:4:#   - No tenant context        ΓåÆ 400 / 401 / 403
backend\crown_api\tests\test_metrics_permissions_contract.py:38:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\crown_api\tests\test_metrics_permissions_contract.py:43:# module code maps to <module>.view permission used by require_permission().
backend\crown_api\tests\test_metrics_permissions_contract.py:77:def test_metrics_requires_tenant_context(module, url):
backend\crown_api\tests\test_metrics_permissions_contract.py:79:    Requests with no X-School-Id header must never return 200.
backend\crown_api\tests\test_metrics_permissions_contract.py:85:        f"{module}: expected 400/401/403 without tenant context, got {r.status_code}"
backend\crown_api\tests\test_metrics_permissions_contract.py:90:def test_metrics_denies_without_permission(module, url):
backend\crown_api\tests\test_metrics_permissions_contract.py:109:def test_metrics_allows_with_permission(module, url):
backend\billing\tests\test_installments.py:19:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\billing\tests\test_installments.py:22:        school_id=school.id,
backend\billing\tests\test_installments.py:31:        school_id=school.id,
backend\billing\tests\test_installments.py:41:        school_id=school.id,
backend\billing\tests\test_installments.py:48:    assert InstallmentScheduleItem.objects.filter(school_id=school.id, plan=plan, household=hh).count() == 3
backend\billing\tests\test_installments.py:53:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\billing\tests\test_installments.py:56:    st1 = Student.objects.create(school_id=school.id, household=hh, first_name="A", last_name="One")
backend\billing\tests\test_installments.py:57:    st2 = Student.objects.create(school_id=school.id, household=hh, first_name="B", last_name="Two")
backend\billing\tests\test_installments.py:60:    course = Course.objects.create(school_id=school.id, code=f"C-{uuid.uuid4().hex[:6]}", name="Course")
backend\billing\tests\test_installments.py:61:    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL")
backend\billing\tests\test_installments.py:62:    Enrollment.objects.create(school_id=school.id, section=section, student=st1)
backend\billing\tests\test_installments.py:63:    Enrollment.objects.create(school_id=school.id, section=section, student=st2)
backend\billing\tests\test_installments.py:66:        school_id=school.id,
backend\billing\tests\test_installments.py:75:        school_id=school.id,
backend\billing\tests\test_installments.py:83:    invoices = Invoice.objects.filter(school_id=school.id, billing_run=run, household=hh).order_by("due_on")
backend\gradebook\tests\test_gradebook_list_endpoints.py:41:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:49:    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")
backend\gradebook\tests\test_gradebook_list_endpoints.py:51:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:66:    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)
backend\gradebook\tests\test_gradebook_list_endpoints.py:68:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\gradebook\tests\test_gradebook_list_endpoints.py:70:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:76:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\gradebook\tests\test_gradebook_list_endpoints.py:78:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:164:def test_assignments_list_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_list_endpoints.py:178:def test_students_list_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_list_endpoints.py:241:    household = Household.objects.create(school_id=school.id, name="Household B")
backend\gradebook\tests\test_gradebook_list_endpoints.py:243:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:249:    Enrollment.objects.create(school_id=school.id, section=section, student=student_without_grade)
backend\gradebook\tests\test_gradebook_list_endpoints.py:272:        school_id=school.id,
backend\gradebook\tests\test_gradebook_list_endpoints.py:280:        school_id=school.id,
backend\crown_api\tests\test_idempotency_keys.py:51:            school_id=self.school.id,
backend\crown_api\tests\test_idempotency_keys.py:92:            school_id=self.school.id,
backend\crown_api\tests\test_idempotency_keys.py:126:            school_id=self.school.id,
backend\crown_api\tests\test_idempotency_keys.py:178:            school_id=self.school.id,
backend\crown_api\tests\test_idempotency_keys.py:199:            school_id=self.school.id,
backend\crown_api\tests\test_idempotency_keys.py:232:            school_id=self.school_a.id,
backend\crown_api\tests\test_idempotency_keys.py:238:            school_id=self.school_b.id,
backend\crown_api\tests\test_idempotency_keys.py:245:        The DB lookup in payment_intent_create filters by school_id + key:
backend\crown_api\tests\test_idempotency_keys.py:277:            school_id=self.school_a.id, idempotency_key=shared_key
backend\crown_api\tests\test_idempotency_keys.py:280:            school_id=self.school_b.id, idempotency_key=shared_key
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:35:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:36:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:37:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:56:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:57:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:58:        u.save(update_fields=["school_id"])
backend\billing\tests\test_billing_summary_api.py:19:    if hasattr(u, "school_id"):
backend\billing\tests\test_billing_summary_api.py:20:        setattr(u, "school_id", school.id)
backend\billing\tests\test_billing_summary_api.py:21:        u.save(update_fields=["school_id"])
backend\billing\tests\test_billing_summary_api.py:27:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\billing\tests\test_billing_summary_api.py:29:    run = BillingRun.objects.create(school_id=school.id, term="2026-FALL", run_type="TUITION", description="Run", amount_per_student=Decimal("0.00"))
backend\billing\tests\test_billing_summary_api.py:30:    inv = Invoice.objects.create(school_id=school.id, billing_run=run, household=hh, total_amount=Decimal("1000.00"))
backend\billing\tests\test_billing_summary_api.py:32:    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
backend\billing\tests\test_billing_summary_api.py:33:    ch = Charge.objects.create(school_id=school.id, account=acct, description="Tuition", amount=Decimal("1000.00"))
backend\billing\tests\test_billing_summary_api.py:37:    aid = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("400.00"), source="FINANCIAL_AID", reference="award:x")
backend\billing\tests\test_billing_summary_api.py:38:    PaymentAllocation.objects.create(school_id=school.id, payment=aid, charge=ch, amount=Decimal("400.00"))
backend\crown_api\tests\test_households_api.py:14:        # Create school for multi-tenant scoping
backend\crown_api\tests\test_households_api.py:40:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:44:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:50:            school_id=self.other_school.id,
backend\crown_api\tests\test_households_api.py:55:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:63:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:73:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:83:            school_id=self.school.id,
backend\crown_api\tests\test_households_api.py:167:    def test_cross_school_isolation(self):
backend\admissions\tests.py:76:    def test_under_review_to_denied(self):
backend\admissions\tests.py:103:    def test_waitlisted_to_denied(self):
backend\admissions\tests.py:134:    def test_denied_to_accepted_blocked(self):
backend\admissions\tests.py:137:    def test_denied_to_under_review_blocked(self):
backend\billing\tests\test_billing_api.py:32:    if hasattr(u, "school_id"):
backend\billing\tests\test_billing_api.py:33:        setattr(u, "school_id", school.id)
backend\billing\tests\test_billing_api.py:34:        u.save(update_fields=["school_id"])
backend\billing\tests\test_billing_api.py:46:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\billing\tests\test_billing_api.py:47:    st1 = Student.objects.create(school_id=school.id, household=hh, first_name="A", last_name="One", grade_level="5", is_active=True)
backend\billing\tests\test_billing_api.py:48:    st2 = Student.objects.create(school_id=school.id, household=hh, first_name="B", last_name="Two", grade_level="5", is_active=True)
backend\billing\tests\test_billing_api.py:50:    course = Course.objects.create(school_id=school.id, code="MATH5", name="Math 5")
backend\billing\tests\test_billing_api.py:51:    sec = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="T", grade_band="5")
backend\billing\tests\test_billing_api.py:52:    Enrollment.objects.create(school_id=school.id, section=sec, student=st1)
backend\billing\tests\test_billing_api.py:53:    Enrollment.objects.create(school_id=school.id, section=sec, student=st2)
backend\billing\tests\test_billing_api.py:83:    hh = Household.objects.create(school_id=school.id, name="Test Household")
backend\billing\tests\test_billing_api.py:85:        school_id=school.id,
backend\billing\tests\test_billing_api.py:90:        school_id=school.id,
backend\billing\tests\test_billing_api.py:126:    hh1 = Household.objects.create(school_id=school1.id, name="Household 1")
backend\billing\tests\test_billing_api.py:127:    hh2 = Household.objects.create(school_id=school2.id, name="Household 2")
backend\billing\tests\test_billing_api.py:129:    billing_run1 = BillingRun.objects.create(school_id=school1.id, term="2026-TEST", amount_per_student=500.00)
backend\billing\tests\test_billing_api.py:130:    billing_run2 = BillingRun.objects.create(school_id=school2.id, term="2026-TEST", amount_per_student=600.00)
backend\billing\tests\test_billing_api.py:132:    Invoice.objects.create(school_id=school1.id, household=hh1, billing_run=billing_run1, total_amount=500.00, due_on="2026-03-01")
backend\billing\tests\test_billing_api.py:133:    Invoice.objects.create(school_id=school2.id, household=hh2, billing_run=billing_run2, total_amount=600.00, due_on="2026-03-01")
backend\billing\tests\test_billing_api.py:157:    hh = Household.objects.create(school_id=school.id, name="Recon Household")
backend\billing\tests\test_billing_api.py:159:        school_id=school.id,
backend\billing\tests\test_billing_api.py:165:        school_id=school.id,
backend\billing\tests\test_billing_api.py:172:    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
backend\billing\tests\test_billing_api.py:174:        school_id=school.id,
backend\billing\tests\test_billing_api.py:183:        school_id=school.id,
backend\billing\tests\test_billing_api.py:190:        school_id=school.id,
backend\crown_api\exports\tests\test_exports_statements_csv.py:35:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_statements_csv.py:36:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_statements_csv.py:37:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_statements_csv.py:56:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_statements_csv.py:57:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_statements_csv.py:58:        u.save(update_fields=["school_id"])
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:1:# backend/crown_api/tests/test_gate1c_auth_tenant_proof.py
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:3:Gate 1C: Tests for auth hardening, tenant enforcement, and whoami proof.
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:55:    def test_whoami_returns_tenant_info(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:56:        """Whoami includes resolved tenant from middleware."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:66:        self.assertEqual(data['tenant']['resolved_school_id'], str(self.school.id))
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:67:        self.assertEqual(data['tenant']['resolution_source'], 'header')
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:68:        self.assertTrue(data['tenant']['header_present'])
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:90:        # Override should be captured (staff user with header Γëá user.school_id)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:111:        from crown_api.tenant_guards import TenantRequiredMixin
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:116:                # After mixin validation, tenant_school_id should be available
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:118:                school_id = getattr(request, 'tenant_school_id', None)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:119:                return Response({"ok": True, "tenant": str(school_id)})
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:137:        from crown_api.tenant import resolve_tenant_school_id, TENANT_ATTR
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:138:        res = resolve_tenant_school_id(request)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:139:        setattr(request, TENANT_ATTR, res.school_id)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:140:        setattr(request, "_tenant_resolution_source", res.source)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:141:        setattr(request, "_tenant_header_present", res.header_present)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:143:    def test_tenant_mixin_enforces_tenant_required(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:144:        """TenantRequiredMixin raises 400 when tenant missing."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:145:        # Create a user without a school to test missing tenant
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:161:        # No tenant header and no user.school = should raise 400
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:165:    def test_tenant_mixin_allows_valid_tenant(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:166:        """TenantRequiredMixin allows request with valid tenant."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:176:        # Valid tenant header = should succeed
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:179:        self.assertEqual(response.data['tenant'], str(self.school.id))
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:189:        # Create a test view that doesn't explicitly set permissions
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:206:            'rest_framework.permissions.IsAuthenticated',
backend\gradebook\tests\test_gradebook_drilldown.py:43:        school_id=school.id,
backend\gradebook\tests\test_gradebook_drilldown.py:52:        school_id=school.id,
backend\gradebook\tests\test_gradebook_drilldown.py:57:        school_id=school.id,
backend\gradebook\tests\test_gradebook_drilldown.py:65:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\gradebook\tests\test_gradebook_drilldown.py:69:            school_id=school.id,
backend\gradebook\tests\test_gradebook_drilldown.py:76:        Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\crown_api\tests\test_financial_aid_drilldown.py:19:        # Grant financial_aid.view so the permission gate doesn't block contract tests.
backend\crown_api\tests\test_financial_aid_drilldown.py:25:        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=perm)
backend\gradebook\tests\test_gradebook_api_smoke.py:52:        school_id=school.id,
backend\gradebook\tests\test_gradebook_api_smoke.py:61:        school_id=school.id,
backend\gradebook\tests\test_gradebook_api_smoke.py:66:        school_id=school.id,
backend\gradebook\tests\test_gradebook_api_smoke.py:82:    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)
backend\gradebook\tests\test_gradebook_api_smoke.py:84:    household = Household.objects.create(school_id=school.id, name="Test Household")
backend\gradebook\tests\test_gradebook_api_smoke.py:86:        school_id=school.id,
backend\gradebook\tests\test_gradebook_api_smoke.py:92:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\tests\test_wizard_contract.py:7:  3. Requires X-School-Id header (400 when missing)
backend\tests\test_wizard_contract.py:8:  4. Enforces tenant isolation (404 when school mismatch)
backend\tests\test_wizard_contract.py:12:and broken auth/tenant behavior in a single place.
backend\tests\test_wizard_contract.py:85:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\tests\test_wizard_contract.py:93:def _headers(school_id):
backend\tests\test_wizard_contract.py:94:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\tests\test_wizard_contract.py:126:# Contract: missing X-School-Id ΓåÆ 400
backend\tests\test_wizard_contract.py:131:    Every wizard session endpoint must reject requests missing X-School-Id.
backend\tests\test_wizard_contract.py:132:    Auth is present; only the tenant header is missing.
backend\tests\test_wizard_contract.py:143:            f"{description} ({url}): expected 400 for missing X-School-Id, got {r.status_code}."
backend\tests\test_wizard_contract.py:158:    POST to a wizard base URL with valid auth + correct X-School-Id must
backend\tests\test_wizard_contract.py:185:# Contract: cross-tenant access ΓåÆ 404
backend\tests\test_wizard_contract.py:200:    def _assert_tenant_isolation(self, description, url):
backend\tests\test_wizard_contract.py:214:            f"{description} ({detail_url}): expected 404 for cross-tenant access, "
backend\tests\test_wizard_contract.py:215:            f"got {r2.status_code}. Tenant isolation is BROKEN."
backend\tests\test_wizard_contract.py:218:    def test_all_wizards_isolate_tenants(self):
backend\tests\test_wizard_contract.py:221:                self._assert_tenant_isolation(description, url)
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:35:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:36:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:37:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:56:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:57:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:58:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_roster_csv.py:27:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_roster_csv.py:28:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_roster_csv.py:29:        u.save(update_fields=["school_id"])
backend\crown_api\tests\test_director_actions_auth_required.py:52:            "school_id": str(school.id),
backend\bell_schedule_wizard\tests\test_views.py:80:def _headers(school_id):
backend\bell_schedule_wizard\tests\test_views.py:81:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\bell_schedule_wizard\tests\test_views.py:563:    def test_cross_tenant_isolation(self):
backend\tests\test_volunteer_family_engagement_unit.py:42:    """Verify tenant/school scoping keywords appear in the Volunteer Family Engagement source tree."""
backend\tests\test_volunteer_family_engagement_unit.py:50:        "school_id" in source_text
backend\tests\test_volunteer_family_engagement_unit.py:53:    ), f"Volunteer Family Engagement: tenant/school scoping not found in source"
backend\crown_api\tests\test_dashboard_tenant_isolation.py:3:Tests that all dashboard endpoints enforce tenant context per TENANT_PRIVACY_CANON.md
backend\crown_api\tests\test_dashboard_tenant_isolation.py:22:    Verify all dashboard endpoints enforce tenant isolation:
backend\crown_api\tests\test_dashboard_tenant_isolation.py:23:    1. Missing tenant ΓåÆ 400
backend\crown_api\tests\test_dashboard_tenant_isolation.py:26:    4. Wrong tenant (non-staff override) ΓåÆ 404
backend\crown_api\tests\test_dashboard_tenant_isolation.py:27:    5. Correct tenant ΓåÆ 200 with data
backend\crown_api\tests\test_dashboard_tenant_isolation.py:31:        # Create two schools for cross-tenant testing
backend\crown_api\tests\test_dashboard_tenant_isolation.py:44:            school_id=self.school_a.id
backend\crown_api\tests\test_dashboard_tenant_isolation.py:50:            school_id=self.school_b.id
backend\crown_api\tests\test_dashboard_tenant_isolation.py:72:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:76:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:83:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:87:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:94:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:99:            school_id=self.school_a.id,
backend\crown_api\tests\test_dashboard_tenant_isolation.py:104:        # Create test data for school B (to prove isolation)
backend\crown_api\tests\test_dashboard_tenant_isolation.py:126:    def test_admissions_funnel_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:127:        """Missing X-School-Id header ΓåÆ 400 (dashboards require explicit tenant)."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:133:        """Invalid UUID in X-School-Id ΓåÆ 400"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:149:    def test_admissions_funnel_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:150:        """Correct tenant ΓåÆ 200 with school A data only"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:157:        self.assertEqual(response.data["school_id"], str(self.school_a.id))
backend\crown_api\tests\test_dashboard_tenant_isolation.py:166:    def test_admissions_funnel_wrong_tenant_returns_empty(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:167:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:177:    def test_finance_summary_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:178:        """Missing X-School-Id header ΓåÆ 400."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:183:    def test_finance_summary_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:184:        """Correct tenant ΓåÆ 200 with financial data"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:191:        self.assertEqual(response.data["school_id"], str(self.school_a.id))
backend\crown_api\tests\test_dashboard_tenant_isolation.py:196:    def test_finance_summary_wrong_tenant_no_leak(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:197:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:207:    def test_academics_enrollment_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:208:        """Missing X-School-Id header ΓåÆ 400."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:213:    def test_academics_enrollment_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:214:        """Correct tenant ΓåÆ 200 with enrollment data"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:221:        self.assertEqual(response.data["school_id"], str(self.school_a.id))
backend\crown_api\tests\test_dashboard_tenant_isolation.py:225:    def test_academics_enrollment_wrong_tenant_no_leak(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:226:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\crown_api\exports\tests\test_exports_jwt_auth.py:14:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_jwt_auth.py:15:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_jwt_auth.py:16:        u.save(update_fields=["school_id"])
backend\tests\test_volunteer_family_engagement_tenant.py:2:Tenant isolation tests for the Volunteer Family Engagement module.
backend\tests\test_volunteer_family_engagement_tenant.py:23:        username=f"tenant-a-volunteer_family_engagement-{token}",
backend\tests\test_volunteer_family_engagement_tenant.py:32:    """Cross-tenant isolation tests for Volunteer Family Engagement."""
backend\tests\test_volunteer_family_engagement_tenant.py:38:    def test_volunteer_family_engagement_tenant_school_ids_are_distinct(self):
backend\tests\test_volunteer_family_engagement_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_volunteer_family_engagement_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_volunteer_family_engagement_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_volunteer_family_engagement_tenant.py:47:    def test_volunteer_family_engagement_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_volunteer_family_engagement_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_volunteer_family_engagement_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_volunteer_family_engagement_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_volunteer_family_engagement_tenant.py:58:    def test_volunteer_family_engagement_same_tenant_request_is_allowed(self):
backend\tests\test_volunteer_family_engagement_tenant.py:67:    def test_volunteer_family_engagement_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_volunteer_family_engagement_tenant.py:75:    def test_volunteer_family_engagement_isolation_keyword_present_in_source(self):
backend\tests\test_volunteer_family_engagement_tenant.py:76:        """Tenant isolation keywords exist in the Volunteer Family Engagement module source."""
backend\tests\test_volunteer_family_engagement_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_volunteer_family_engagement_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_volunteer_family_engagement_tenant.py:87:        assert found, f"Volunteer Family Engagement: tenant isolation keywords not found in source"
backend\academic_year_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\academic_year_wizard\tests\test_views.py:13:  - Single-current enforcement: committing B deactivates A, cross-tenant isolation
backend\academic_year_wizard\tests\test_views.py:48:def _headers(school_id):
backend\academic_year_wizard\tests\test_views.py:49:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\academic_year_wizard\tests\test_views.py:76:def _advance_to_configured(client, school_id, **overrides):
backend\academic_year_wizard\tests\test_views.py:77:    r = client.post(BASE_URL, **_headers(school_id))
backend\academic_year_wizard\tests\test_views.py:81:    rc = client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
backend\academic_year_wizard\tests\test_views.py:86:def _advance_to_terms_set(client, school_id, terms=None, **overrides):
backend\academic_year_wizard\tests\test_views.py:87:    sid, year_name = _advance_to_configured(client, school_id, **overrides)
backend\academic_year_wizard\tests\test_views.py:89:    rt = client.post(f"{BASE_URL}{sid}/terms/", {"terms": terms}, format="json", **_headers(school_id))
backend\academic_year_wizard\tests\test_views.py:94:def _advance_to_committed(client, school_id, terms=None, **overrides):
backend\academic_year_wizard\tests\test_views.py:95:    sid, year_name = _advance_to_terms_set(client, school_id, terms=terms, **overrides)
backend\academic_year_wizard\tests\test_views.py:96:    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
backend\academic_year_wizard\tests\test_views.py:124:# Tenant isolation
backend\academic_year_wizard\tests\test_views.py:423:    def test_cross_tenant_year_not_affected(self):
backend\academic_year_wizard\tests\test_views.py:442:        self.assertTrue(ay_a.is_current, "Cross-tenant year must not be deactivated")
backend\academic_year_wizard\tests\test_views.py:465:            school_id=school.id,
backend\academic_year_wizard\tests\test_views.py:473:                school_id=school.id,
backend\comms_wizard\tests\test_views.py:33:def _headers(school_id):
backend\comms_wizard\tests\test_views.py:34:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\comms_wizard\tests\test_views.py:48:def _advance_to_configured(client, school_id, purpose="Re-enrollment Reminder", channels=None):
backend\comms_wizard\tests\test_views.py:51:    r = client.post(BASE_URL, **_headers(school_id))
backend\comms_wizard\tests\test_views.py:57:        **_headers(school_id),
backend\comms_wizard\tests\test_views.py:62:def _advance_to_message_drafted(client, school_id):
backend\comms_wizard\tests\test_views.py:63:    session_id = _advance_to_configured(client, school_id)
backend\comms_wizard\tests\test_views.py:68:        **_headers(school_id),
backend\comms_wizard\tests\test_views.py:73:def _advance_to_recipients_staged(client, school_id):
backend\comms_wizard\tests\test_views.py:74:    session_id = _advance_to_message_drafted(client, school_id)
backend\comms_wizard\tests\test_views.py:79:        **_headers(school_id),
backend\comms_wizard\tests\test_views.py:120:    def test_configure_isolation(self):
backend\comms_wizard\tests\test_views.py:129:    def test_message_isolation(self):
backend\comms_wizard\tests\test_views.py:138:    def test_recipients_isolation(self):
backend\comms_wizard\tests\test_views.py:147:    def test_commit_isolation(self):
backend\comms_wizard\tests\test_views.py:156:    def test_verify_isolation(self):
backend\comms_wizard\tests\test_views.py:337:            OutboxMessage.objects.filter(school_id=str(self.school.id)).count(), 2
backend\comms_wizard\tests\test_views.py:346:            OutboxMessage.objects.filter(school_id=str(self.school.id)).count(), 2
backend\crown_api\tests\test_dashboard_snapshot_summary_api.py:13:        school_id='heritage-demo',
backend\crown_api\exports\tests\test_exports_financial_csv.py:28:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_financial_csv.py:29:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_financial_csv.py:30:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_financial_csv.py:49:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_financial_csv.py:50:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_financial_csv.py:51:        u.save(update_fields=["school_id"])
backend\tests\test_volunteer_family_engagement_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_volunteer_family_engagement_negative.py:33:    """Negative tests for Volunteer Family Engagement: unauthorized, invalid, forbidden paths."""
backend\tests\test_volunteer_family_engagement_negative.py:40:    def test_volunteer_family_engagement_unauthenticated_request_is_forbidden(self):
backend\tests\test_volunteer_family_engagement_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\crown_api\tests\test_dashboards_role_contract.py:5:  1. Missing X-School-Id header ΓåÆ 401 (unauthenticated) or 400 (missing header)
backend\crown_api\tests\test_dashboards_role_contract.py:8:  4. Valid tenant + authenticated ΓåÆ 200 with correct schema
backend\crown_api\tests\test_dashboards_role_contract.py:39:        school_id=school.id,
backend\crown_api\tests\test_dashboards_role_contract.py:80:    """Missing X-School-Id ΓåÆ 400."""
backend\crown_api\tests\test_dashboards_role_contract.py:88:    """Non-UUID school_id ΓåÆ 400."""
backend\crown_api\tests\test_dashboards_role_contract.py:110:    assert "school_id" in data
backend\crown_api\tests\test_dashboards_role_contract.py:123:    assert data["school_id"] == str(school.id)
backend\crown_api\tests\test_dashboards_role_contract.py:179:    assert data["school_id"] == str(school.id)
backend\crown_api\tests\test_dashboards_role_contract.py:199:# Cross-tenant: user from school A cannot access school B's data
backend\crown_api\tests\test_dashboards_role_contract.py:203:def test_cross_tenant_access_blocked(db):
backend\crown_api\tests\test_dashboards_role_contract.py:207:        username="tenant_a_user", email="a@test.com", password="pw",
backend\crown_api\tests\test_dashboards_role_contract.py:208:        school_id=school_a.id,
backend\tests\test_volunteer_family_engagement_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_volunteer_family_engagement_api.py:61:        """School record for Volunteer Family Engagement tenant is created and queryable."""
backend\tests\test_volunteer_family_engagement_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_volunteer_family_engagement_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_transportation_unit.py:42:    """Verify tenant/school scoping keywords appear in the Transportation source tree."""
backend\tests\test_transportation_unit.py:50:        "school_id" in source_text
backend\tests\test_transportation_unit.py:53:    ), f"Transportation: tenant/school scoping not found in source"
backend\crown_api\billing_api\tests\test_school_override_header.py:18:    hh_b = Household.objects.create(school_id=school_b.id, name="HH B")
backend\crown_api\billing_api\tests\test_school_override_header.py:26:    # Non-staff users must not be able to override tenant context.
backend\crown_api\billing_api\tests\test_school_override_header.py:39:    hh_b = Household.objects.create(school_id=school_b.id, name="HH B")
backend\crown_api\billing_api\tests\test_school_override_header.py:63:    hh = Household.objects.create(school_id=school.id, name="HH")
backend\crown_api\billing_api\tests\test_school_override_header.py:86:    hh = Household.objects.create(school_id=school.id, name="HH")
backend\tests\test_transportation_tenant.py:2:Tenant isolation tests for the Transportation module.
backend\tests\test_transportation_tenant.py:23:        username=f"tenant-a-transportation-{token}",
backend\tests\test_transportation_tenant.py:32:    """Cross-tenant isolation tests for Transportation."""
backend\tests\test_transportation_tenant.py:38:    def test_transportation_tenant_school_ids_are_distinct(self):
backend\tests\test_transportation_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_transportation_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_transportation_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_transportation_tenant.py:47:    def test_transportation_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_transportation_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_transportation_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_transportation_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_transportation_tenant.py:58:    def test_transportation_same_tenant_request_is_allowed(self):
backend\tests\test_transportation_tenant.py:67:    def test_transportation_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_transportation_tenant.py:75:    def test_transportation_isolation_keyword_present_in_source(self):
backend\tests\test_transportation_tenant.py:76:        """Tenant isolation keywords exist in the Transportation module source."""
backend\tests\test_transportation_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_transportation_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_transportation_tenant.py:87:        assert found, f"Transportation: tenant isolation keywords not found in source"
backend\crown_api\exports\tests\test_exports_csv.py:31:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_csv.py:32:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_csv.py:33:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_csv.py:52:    if hasattr(u, "school_id"):
backend\crown_api\exports\tests\test_exports_csv.py:53:        setattr(u, "school_id", school.id)
backend\crown_api\exports\tests\test_exports_csv.py:54:        u.save(update_fields=["school_id"])
backend\crown_api\exports\tests\test_exports_csv.py:89:    school_id = getattr(finance_user, "school_id")
backend\crown_api\exports\tests\test_exports_csv.py:90:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\crown_api\exports\tests\test_exports_csv.py:91:    run = BillingRun.objects.create(school_id=school_id, term="2026-FALL", run_type="TUITION")
backend\crown_api\exports\tests\test_exports_csv.py:94:        school_id=school_id,
backend\crown_api\exports\tests\test_exports_csv.py:114:    school_id = getattr(finance_user, "school_id")
backend\crown_api\exports\tests\test_exports_csv.py:115:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\crown_api\exports\tests\test_exports_csv.py:118:        school_id=school_id,
backend\crown_api\exports\tests\test_exports_csv.py:127:        school_id=school_id,
backend\financial_aid_wizard\tests\test_views.py:31:def _headers(school_id):
backend\financial_aid_wizard\tests\test_views.py:32:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\financial_aid_wizard\tests\test_views.py:39:    c._school_id = school.id
backend\financial_aid_wizard\tests\test_views.py:43:def _make_application(school_id, academic_year="2026-2027"):
backend\financial_aid_wizard\tests\test_views.py:45:        school_id=school_id,
backend\financial_aid_wizard\tests\test_views.py:91:    def test_configure_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:100:    def test_buckets_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:109:    def test_awards_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:118:    def test_commit_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:127:    def test_verify_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:376:            school_id=self.school.id,
backend\financial_aid_wizard\tests\test_views.py:388:            AidAward.objects.filter(school_id=self.school.id, application=self.app).count(),
backend\crown_api\tests\test_auth_jwt.py:14:    school_id = uuid.uuid4()
backend\crown_api\tests\test_auth_jwt.py:19:        school_id=school_id,
backend\crown_api\tests\test_auth_jwt.py:51:    assert me["user"]["school_id"] == str(school_id)
backend\crown_api\tests\test_auth_jwt.py:59:        school_id=uuid.uuid4(),
backend\crown_api\tests\test_auth_jwt.py:74:    school_id = uuid.uuid4()
backend\crown_api\tests\test_auth_jwt.py:79:        school_id=school_id,
backend\tests\test_transportation_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_transportation_negative.py:33:    """Negative tests for Transportation: unauthorized, invalid, forbidden paths."""
backend\tests\test_transportation_negative.py:40:    def test_transportation_unauthenticated_request_is_forbidden(self):
backend\tests\test_transportation_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\crown_api\exports\tests\test_exports_audit_log.py:14:    school_id = "b45b8c5a-6708-4597-aad9-a226627b2962"  # canonical demo school
backend\crown_api\exports\tests\test_exports_audit_log.py:15:    School.objects.create(id=school_id, name="Demo School")
backend\crown_api\exports\tests\test_exports_audit_log.py:19:    user = User.objects.create_user(username="fin", password=TEST_AUTH_SECRET, school_id=school_id)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:25:    if hasattr(u, "school_id"):
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:26:        setattr(u, "school_id", school.id)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:27:        u.save(update_fields=["school_id"])
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:46:    if hasattr(u, "school_id"):
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:47:        setattr(u, "school_id", school.id)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:48:        u.save(update_fields=["school_id"])
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:59:def _seed_household_with_two_charges(school_id):
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:60:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:61:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:63:        school_id=school_id,
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:69:        school_id=school_id,
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:78:    school_id = getattr(finance_user, "school_id")
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:79:    hh, acct, ch1, ch2 = _seed_household_with_two_charges(school_id)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:100:    assert p.school_id == school_id
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:111:    school_id = getattr(finance_user, "school_id")
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:112:    hh, _, ch1, ch2 = _seed_household_with_two_charges(school_id)
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:150:    school_id = getattr(finance_user, "school_id")
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:151:    hh, _, ch1, ch2 = _seed_household_with_two_charges(school_id)
backend\tests\test_transportation_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_transportation_api.py:61:        """School record for Transportation tenant is created and queryable."""
backend\tests\test_transportation_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_transportation_api.py:67:        assert self.user.school_id == self.school.id
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:31:    if hasattr(u, "school_id"):
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:32:        setattr(u, "school_id", primary_school.id)
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:33:        u.save(update_fields=["school_id"])
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:49:def _seed_household_with_charge(school_id):
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:50:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:51:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:53:        school_id=school_id,
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:89:    assert p.school_id == override_school.id
backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py:93:        school_id=override_school.id,
backend\crown_api\billing_api\tests\test_payments_record_api.py:26:    if hasattr(u, "school_id"):
backend\crown_api\billing_api\tests\test_payments_record_api.py:27:        setattr(u, "school_id", school.id)
backend\crown_api\billing_api\tests\test_payments_record_api.py:28:        u.save(update_fields=["school_id"])
backend\crown_api\billing_api\tests\test_payments_record_api.py:47:    if hasattr(u, "school_id"):
backend\crown_api\billing_api\tests\test_payments_record_api.py:48:        setattr(u, "school_id", school.id)
backend\crown_api\billing_api\tests\test_payments_record_api.py:49:        u.save(update_fields=["school_id"])
backend\crown_api\billing_api\tests\test_payments_record_api.py:60:def _seed_invoice_with_charge(school_id):
backend\crown_api\billing_api\tests\test_payments_record_api.py:61:    hh = Household.objects.create(school_id=school_id, name="Household")
backend\crown_api\billing_api\tests\test_payments_record_api.py:62:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\crown_api\billing_api\tests\test_payments_record_api.py:64:        school_id=school_id,
backend\crown_api\billing_api\tests\test_payments_record_api.py:69:    run = BillingRun.objects.create(school_id=school_id, term="2026-FALL", run_type="TUITION")
backend\crown_api\billing_api\tests\test_payments_record_api.py:71:        school_id=school_id,
backend\crown_api\billing_api\tests\test_payments_record_api.py:91:    school_id = getattr(finance_user, "school_id")
backend\crown_api\billing_api\tests\test_payments_record_api.py:92:    inv, acct, ch = _seed_invoice_with_charge(school_id)
backend\crown_api\billing_api\tests\test_payments_record_api.py:111:    assert p.school_id == school_id
backend\crown_api\billing_api\tests\test_payments_record_api.py:120:        school_id=school_id,
backend\crown_api\billing_api\tests\test_payments_record_api.py:130:    school_id = getattr(finance_user, "school_id")
backend\crown_api\billing_api\tests\test_payments_record_api.py:131:    inv, _, _ = _seed_invoice_with_charge(school_id)
backend\academics\tests\test_transcript_ro_api.py:44:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:53:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:62:    course1 = Course.objects.create(school_id=school.id, code="MATH-101", name="Mathematics")
backend\academics\tests\test_transcript_ro_api.py:63:    course2 = Course.objects.create(school_id=school.id, code="ELA-101", name="English Language Arts")
backend\academics\tests\test_transcript_ro_api.py:66:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:73:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:80:    household = Household.objects.create(school_id=school.id, name="Test Household")
backend\academics\tests\test_transcript_ro_api.py:82:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:89:    Enrollment.objects.create(school_id=school.id, section=section1, student=student)
backend\academics\tests\test_transcript_ro_api.py:90:    Enrollment.objects.create(school_id=school.id, section=section2, student=student)
backend\academics\tests\test_transcript_ro_api.py:94:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:102:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:238:    section = Section.objects.filter(school_id=school.id, course__code="MATH-101").first()
backend\academics\tests\test_transcript_ro_api.py:242:        school_id=school.id,
backend\academics\tests\test_transcript_ro_api.py:273:    section = Section.objects.filter(school_id=school.id, course__code="MATH-101").first()
backend\academics\tests\test_transcript_ro_api.py:277:        school_id=school.id,
backend\tests\test_tenant_write_guard.py:2:Tests for tenant write protection (Layer 07).
backend\tests\test_tenant_write_guard.py:7:from core.tenant_models import set_current_school, clear_current_school, TenantWriteViolation
backend\tests\test_tenant_write_guard.py:15:        # Create two tenants
backend\tests\test_tenant_write_guard.py:23:        """With tenant context, creating without school should auto-bind."""
backend\tests\test_tenant_write_guard.py:28:        self.assertEqual(c.school_id, self.a.id)
backend\tests\test_tenant_write_guard.py:30:    def test_cross_tenant_write_blocked(self):
backend\tests\test_tenant_write_guard.py:31:        """With tenant context A, saving object assigned to B must be blocked."""
backend\enrollment_period_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\enrollment_period_wizard\tests\test_views.py:52:def _headers(school_id):
backend\enrollment_period_wizard\tests\test_views.py:53:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\enrollment_period_wizard\tests\test_views.py:86:def _advance_to_configured(client, school_id, ay=None, **date_overrides):
backend\enrollment_period_wizard\tests\test_views.py:88:        school = School.objects.get(pk=school_id)
backend\enrollment_period_wizard\tests\test_views.py:90:    r = client.post(BASE_URL, **_headers(school_id))
backend\enrollment_period_wizard\tests\test_views.py:95:        payload, format="json", **_headers(school_id),
backend\enrollment_period_wizard\tests\test_views.py:100:def _advance_to_capacities_set(client, school_id, caps=None, ay=None):
backend\enrollment_period_wizard\tests\test_views.py:101:    sid, ay = _advance_to_configured(client, school_id, ay=ay)
backend\enrollment_period_wizard\tests\test_views.py:106:        **_headers(school_id),
backend\enrollment_period_wizard\tests\test_views.py:111:def _advance_to_committed(client, school_id, caps=None, ay=None):
backend\enrollment_period_wizard\tests\test_views.py:112:    sid, ay = _advance_to_capacities_set(client, school_id, caps=caps, ay=ay)
backend\enrollment_period_wizard\tests\test_views.py:113:    client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
backend\enrollment_period_wizard\tests\test_views.py:142:# Tenant isolation
backend\enrollment_period_wizard\tests\test_views.py:483:    def test_cross_tenant_isolation(self):
backend\financial_aid\tests\test_workflows.py:18:            school_id=self.school.id,
backend\enrollment_conversion_wizard\tests\test_views.py:34:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\enrollment_conversion_wizard\tests\test_views.py:37:def _headers(school_id):
backend\enrollment_conversion_wizard\tests\test_views.py:38:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\enrollment_conversion_wizard\tests\test_views.py:66:def _advance_to_configured(client, school_id):
backend\enrollment_conversion_wizard\tests\test_views.py:67:    r = client.post(BASE_URL, **_headers(school_id))
backend\enrollment_conversion_wizard\tests\test_views.py:73:        **_headers(school_id),
backend\enrollment_conversion_wizard\tests\test_views.py:78:def _advance_to_loaded(client, school_id):
backend\enrollment_conversion_wizard\tests\test_views.py:79:    sid = _advance_to_configured(client, school_id)
backend\enrollment_conversion_wizard\tests\test_views.py:80:    client.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school_id))
backend\enrollment_conversion_wizard\tests\test_views.py:84:def _advance_to_committed(client, school_id):
backend\enrollment_conversion_wizard\tests\test_views.py:85:    sid = _advance_to_loaded(client, school_id)
backend\enrollment_conversion_wizard\tests\test_views.py:90:        **_headers(school_id),
backend\enrollment_conversion_wizard\tests\test_views.py:118:    def test_create_forbidden_without_role_permission(self):
backend\academics\tests\test_section_roster.py:43:        school_id=school.id,
backend\academics\tests\test_section_roster.py:52:        school_id=school.id,
backend\academics\tests\test_section_roster.py:57:        school_id=school.id,
backend\academics\tests\test_section_roster.py:65:    household = Household.objects.create(school_id=school.id, name="Household A")
backend\academics\tests\test_section_roster.py:69:            school_id=school.id,
backend\academics\tests\test_section_roster.py:76:        Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\tests\test_tenant_violation_telemetry.py:5:from core.tenant_models import (
backend\tests\test_tenant_violation_telemetry.py:8:    require_tenant_context,
backend\tests\test_tenant_violation_telemetry.py:29:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:31:                require_tenant_context()
backend\tests\test_tenant_violation_telemetry.py:34:    def test_logs_cross_tenant_write_violation(self):
backend\tests\test_tenant_violation_telemetry.py:36:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:43:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:50:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\financial_aid\tests\test_financial_aid_endpoints.py:20:        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=_perm)
backend\financial_aid\tests\test_financial_aid_endpoints.py:25:        self.school_id = self.school.id
backend\financial_aid\tests\test_financial_aid_endpoints.py:29:            school_id=self.school_id,
backend\financial_aid\tests\test_financial_aid_endpoints.py:38:            school_id=self.school_id,
backend\financial_aid\tests\test_financial_aid_endpoints.py:52:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:63:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:99:            school_id=self.school_id,
backend\financial_aid\tests\test_financial_aid_endpoints.py:110:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:122:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:135:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:145:        app = FinancialAidApplication.objects.filter(school_id=self.school_id).first()
backend\financial_aid\tests\test_financial_aid_endpoints.py:148:                school_id=self.school_id,
backend\financial_aid\tests\test_financial_aid_endpoints.py:158:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:169:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:181:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:190:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:209:            self.assertIn(row["award_status"], {"awarded", "denied", "revised", "withdrawn"})
backend\financial_aid\tests\test_financial_aid_endpoints.py:215:            HTTP_X_SCHOOL_ID=str(self.school_id),
backend\financial_aid\tests\test_financial_aid_endpoints.py:224:        """Verify X-School-Id header is required."""
backend\financial_aid\tests\test_auth_smoke.py:7:  400 ΓåÆ tenant-header/middleware fail-closed deny
backend\financial_aid\tests\test_auth_smoke.py:10:  403 ΓåÆ DRF permission denied
backend\financial_aid\tests\test_auth_smoke.py:19:where a refactor swapped in an AllowAny permission or dropped the decorator.
backend\financial_aid\tests\test_auth_smoke.py:40:    An unauthenticated request must be denied by auth/tenant wall.
backend\financial_aid\tests\test_auth_smoke.py:43:    - 200/500 ΓåÆ auth/permission wiring broken
backend\financial_aid\tests\test_auth_smoke.py:50:        f"Expected 400/302/401/403 (auth/tenant wall).\n"
backend\financial_aid\tests\test_auth_smoke.py:52:        f"  200 ΓåÆ @login_required / permission class missing\n"
backend\tests\test_tenant_lifecycle_cleanup.py:7:from core.tenant_models import get_current_school, clear_current_school
backend\tests\test_tenant_lifecycle_cleanup.py:32:        # Make request with tenant header, ensure request processing clears afterwards
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:2:Tests: Finance Setup tenant scoping
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:4:Verifies that policies saved for school_id=1 are invisible to school_id=2.
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:79:    upsert_finance_policies(school_id=1, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:81:    v1 = get_policy_snapshot(school_id=1, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:82:    v2 = get_policy_snapshot(school_id=2, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:96:    upsert_finance_policies(school_id=10, academic_year=YEAR, payload=payload_1)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:97:    upsert_finance_policies(school_id=20, academic_year=YEAR, payload=payload_2)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:99:    v10 = get_policy_snapshot(school_id=10, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:100:    v20 = get_policy_snapshot(school_id=20, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:108:    upsert_finance_policies(school_id=1, academic_year="2026-2027", payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:110:    v_2628 = get_policy_snapshot(school_id=1, academic_year="2027-2028")
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:115:    """(school_id, academic_year) must be unique ΓÇö second create must upsert, not duplicate."""
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:116:    upsert_finance_policies(school_id=5, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:117:    upsert_finance_policies(school_id=5, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:119:    count = FinancePolicyVersion.objects.filter(school_id=5, academic_year=YEAR).count()
backend\financial_aid\tests\test_phase4b_ledger_integration.py:46:    return Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
backend\financial_aid\tests\test_phase4b_ledger_integration.py:50:    return LedgerAccount.objects.create(school_id=sid, household=hh)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:55:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:65:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:71:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:86:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:94:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:116:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:126:    pay = Payment.objects.get(school_id=sid, account=acct, source="FINANCIAL_AID")
backend\financial_aid\tests\test_phase4b_ledger_integration.py:130:    alloc = Allocation.objects.get(school_id=sid, payment=pay, charge=charge)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:135:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:154:    result1 = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:155:    result2 = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:163:    assert Payment.objects.filter(school_id=sid, source="FINANCIAL_AID").count() == 1
backend\financial_aid\tests\test_phase4b_ledger_integration.py:178:    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:198:    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:200:    summary = billing_run_summary(school_id=sid, billing_run=run)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:218:    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:220:    stmt = build_account_statement(school_id=sid, account=acct)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:254:    result = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
backend\financial_aid\tests\test_phase4b_ledger_integration.py:262:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:269:        school_id=sid,
backend\financial_aid\tests\test_phase4b_ledger_integration.py:280:    stmt = build_account_statement(school_id=sid, account=acct)
backend\academics\tests\test_sections_teacher_guard.py:72:        school_id=school.id,
backend\academics\tests\test_sections_teacher_guard.py:81:        school_id=school.id,
backend\academics\tests\test_sections_teacher_guard.py:88:        school_id=school.id,
backend\academics\tests\test_sections_teacher_guard.py:96:        school_id=school.id,
backend\financial_aid\tests\test_financial_aid_authz.py:8:# Tenant isolation (row scope) is also proven here:
backend\financial_aid\tests\test_financial_aid_authz.py:27:def _enable_tenant_middleware(settings):
backend\financial_aid\tests\test_financial_aid_authz.py:29:    The root conftest.py disables it globally; permission gate and cross-tenant
backend\financial_aid\tests\test_financial_aid_authz.py:58:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\financial_aid\tests\test_financial_aid_authz.py:61:def _seed_fa_data(school_id):
backend\financial_aid\tests\test_financial_aid_authz.py:65:        school_id=school_id,
backend\financial_aid\tests\test_financial_aid_authz.py:73:        school_id=school_id,
backend\financial_aid\tests\test_financial_aid_authz.py:191:# Tenant isolation (row scope)
backend\financial_aid\tests\test_financial_aid_authz.py:197:    def test_cross_tenant_row_isolation_on_drilldown(self):
backend\financial_aid\tests\test_financial_aid_authz.py:202:        user = _user("aiddir_isolation")
backend\financial_aid\tests\test_financial_aid_authz.py:214:        # user_has_permission(user, "financial_aid.view", school=school_b) ΓåÆ False
backend\financial_aid\tests\test_financial_aid_authz.py:225:    def test_same_tenant_drilldown_returns_own_data_only(self):
backend\financial_aid\tests\test_financial_aid_authz.py:247:            # The drilldown filters by school_id from require_school_id(request)
backend\financial_aid\tests\test_financial_aid_authz.py:265:    AID_DIRECTOR holds this permission ΓåÆ sees the text.
backend\finance\tests\test_finance_tenant.py:2:finance/tests/test_finance_tenant.py ΓÇö Tenant isolation invariants for Finance module.
backend\finance\tests\test_finance_tenant.py:5:  1. Missing X-School-Id header ΓåÆ fail-closed (400/403/404).
backend\finance\tests\test_finance_tenant.py:10:  python manage.py test finance.tests.test_finance_tenant
backend\finance\tests\test_finance_tenant.py:62:        """No X-School-Id header ΓåÆ 400 (MissingSchoolContext)."""
backend\finance\tests\test_finance_tenant.py:67:        """Valid X-School-Id header ΓåÆ 200."""
backend\curricula\tests\test_curricula_tenant_isolation.py:2:Tenant isolation tests for curricula API.
backend\curricula\tests\test_curricula_tenant_isolation.py:26:    if hasattr(u, "school_id"):
backend\curricula\tests\test_curricula_tenant_isolation.py:27:        setattr(u, "school_id", school.id)
backend\curricula\tests\test_curricula_tenant_isolation.py:28:        u.save(update_fields=["school_id"])
backend\curricula\tests\test_curricula_tenant_isolation.py:38:        school_id=school_a.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:43:        school_id=school_a.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:49:        school_id=school_a.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:55:        school_id=school_a.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:64:        school_id=school_b.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:69:        school_id=school_b.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:75:        school_id=school_b.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:81:        school_id=school_b.id,
backend\curricula\tests\test_curricula_tenant_isolation.py:101:def test_curriculum_maps_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:118:def test_units_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:135:def test_lessons_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:153:    """Verify filtering by course respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:165:    # Try to filter by school B's course - should see nothing (tenant boundary)
backend\curricula\tests\test_curricula_tenant_isolation.py:172:    """Verify filtering by curriculum map respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:191:    """Verify filtering by unit respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:265:def test_curricula_detail_views_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:266:    """Verify detail endpoints respect tenant boundaries."""
backend\tests\test_tenant_isolation_smoke.py:1:# backend/tests/test_tenant_isolation_smoke.py
backend\tests\test_tenant_isolation_smoke.py:3:Minimal cross-tenant isolation proof for writable ViewSets.
backend\tests\test_tenant_isolation_smoke.py:42:    if hasattr(u, "school_id"):
backend\tests\test_tenant_isolation_smoke.py:43:        u.school_id = school.id
backend\tests\test_tenant_isolation_smoke.py:44:        u.save(update_fields=["school_id"])
backend\tests\test_tenant_isolation_smoke.py:54:    hh = Household.objects.create(school_id=school.id, name=f"HH-{uuid.uuid4()}")
backend\tests\test_tenant_isolation_smoke.py:56:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:62:        school_id=school.id, code=f"C-{uuid.uuid4().hex[:6]}", name="Math"
backend\tests\test_tenant_isolation_smoke.py:65:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:71:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:77:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:82:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:88:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:95:        school_id=school.id,
backend\tests\test_tenant_isolation_smoke.py:103:    """Cross-tenant isolation: user A must not see school B data."""
backend\tests\test_tenant_isolation_smoke.py:105:    def test_cross_tenant_submission_list_hidden(self):
backend\tests\test_tenant_isolation_smoke.py:129:    def test_cross_tenant_submission_detail_denied(self):
backend\finance_setup\tests\test_finance_setup_locking.py:8:Uses RequestFactory + patches school_id_from_request to bypass UUID validation.
backend\finance_setup\tests\test_finance_setup_locking.py:80:_patch_tenant = patch("finance_setup.wizard_api.school_id_from_request", return_value=SCHOOL_ID)
backend\finance_setup\tests\test_finance_setup_locking.py:103:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:112:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:114:    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_locking.py:123:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:125:    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_locking.py:126:    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, locked_by="test_suite")
backend\finance_setup\tests\test_finance_setup_locking.py:133:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:135:    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_locking.py:136:    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_locking.py:143:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:145:    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_locking.py:146:    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_locking.py:155:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:163:    upsert_finance_policies(school_id=2, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\finance_setup\tests\test_finance_setup_locking.py:164:    lock_finance_policies(school_id=2, academic_year=YEAR)
backend\finance_setup\tests\test_finance_setup_locking.py:167:        upsert_finance_policies(school_id=2, academic_year=YEAR, payload=FULL_PAYLOAD)
backend\scheduling_wizard\tests\test_views.py:37:def _headers(school_id):
backend\scheduling_wizard\tests\test_views.py:38:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\scheduling_wizard\tests\test_views.py:45:    c._school_id = school.id
backend\scheduling_wizard\tests\test_views.py:86:    def test_configure_isolation(self):
backend\scheduling_wizard\tests\test_views.py:95:    def test_courses_isolation(self):
backend\scheduling_wizard\tests\test_views.py:104:    def test_sections_isolation(self):
backend\scheduling_wizard\tests\test_views.py:113:    def test_commit_isolation(self):
backend\scheduling_wizard\tests\test_views.py:122:    def test_verify_isolation(self):
backend\scheduling_wizard\tests\test_views.py:354:            Course.objects.filter(school_id=self.school.id, code="MATH101").count(), 1
backend\scheduling_wizard\tests\test_views.py:357:            Course.objects.filter(school_id=self.school.id, code="ENG101").count(), 1
backend\scheduling_wizard\tests\test_views.py:363:            Section.objects.filter(school_id=self.school.id, term="2026-FALL").count(), 2
backend\scheduling_wizard\tests\test_views.py:373:            Section.objects.filter(school_id=self.school.id, term="2026-FALL").count(), 2
backend\tests\test_51x51_evidence_17_grade_levels.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_17_grade_levels.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_17_grade_levels.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_17_grade_levels.py:45:# tenant
backend\tests\test_51x51_evidence_17_grade_levels.py:46:# cross-tenant
backend\tests\test_51x51_evidence_17_grade_levels.py:48:# isolation
backend\tests\test_51x51_evidence_17_grade_levels.py:70:# unauthorized
backend\tests\test_51x51_evidence_17_grade_levels.py:72:# forbidden
backend\academics\tests\test_sections_api.py:35:        school_id=school.id,
backend\academics\tests\test_sections_api.py:44:        school_id=school.id,
backend\academics\tests\test_sections_api.py:51:        school_id=school.id,
backend\academics\tests\test_sections_api.py:58:    household = Household.objects.create(school_id=school.id, name="Household")
backend\academics\tests\test_sections_api.py:60:        school_id=school.id,
backend\academics\tests\test_sections_api.py:66:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\finance\tests\test_finance_services.py:82:        school_id=school.id,
backend\finance\tests\test_finance_services.py:88:        hh = Household.objects.create(school_id=school.id, name=f"HH-{payer.username}")
backend\finance\tests\test_finance_services.py:90:            school_id=school.id,
backend\finance\tests\test_finance_services.py:97:    LedgerAccount.objects.get_or_create(school_id=school.id, household=hh)
backend\finance\tests\test_finance_services.py:203:        self.assertEqual(ledger_payment.school_id, self.school.id)
backend\finance\tests\test_finance_services.py:230:        """Obligation from a different school ΓåÆ DoesNotExist (tenant guard)."""
backend\finance\tests\test_finance_services.py:288:                school_id=self.school.id,
backend\tests\test_tenant_isolation.py:14:def _user_for_school(school: School, *, is_staff: bool = False, username_prefix: str = "tenant"):
backend\tests\test_tenant_isolation.py:29:        self.user_a = _user_for_school(self.school_a, username_prefix="tenant-a")
backend\tests\test_tenant_isolation.py:30:        self.staff_a = _user_for_school(self.school_a, is_staff=True, username_prefix="tenant-staff")
backend\tests\test_tenant_isolation.py:33:            username=f"tenant-none-{token}",
backend\tests\test_tenant_isolation.py:34:            email=f"tenant-none-{token}@example.com",
backend\tests\test_tenant_isolation.py:44:    def test_gradebook_sections_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:49:    def test_billing_runs_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:54:    def test_admissions_applications_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:59:    def test_admissions_enroll_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:64:    def test_staff_same_tenant_can_reach_gradebook_surface(self):
backend\tests\test_tenant_isolation.py:69:    def test_unauthenticated_request_is_denied(self):
backend\subscriptions\tests\test_permissions_enforcement.py:2:API permission enforcement tests.
backend\subscriptions\tests\test_permissions_enforcement.py:7:  - /ops/<school_id>/ requires staff/admin
backend\subscriptions\tests\test_permissions_enforcement.py:8:  - POST /ops/<school_id>/ assigns a new plan and closes the old subscription
backend\subscriptions\tests\test_permissions_enforcement.py:66:    school_id = uuid.uuid4()
backend\subscriptions\tests\test_permissions_enforcement.py:67:    TenantSubscription.objects.create(school_id=school_id, plan=plan)
backend\subscriptions\tests\test_permissions_enforcement.py:72:    # Simulate TenantContextMiddleware having resolved the school_id
backend\subscriptions\tests\test_permissions_enforcement.py:75:        # Real path: patch school_id onto request in test
backend\subscriptions\tests\test_permissions_enforcement.py:81:        HTTP_X_SCHOOL_ID=str(school_id),
backend\subscriptions\tests\test_permissions_enforcement.py:83:    # Will be 200 if middleware resolves school_id, or 400 if not (middleware-dependent)
backend\subscriptions\tests\test_permissions_enforcement.py:109:# /api/v1/subscriptions/ops/<school_id>/
backend\subscriptions\tests\test_permissions_enforcement.py:114:    school_id = uuid.uuid4()
backend\subscriptions\tests\test_permissions_enforcement.py:115:    TenantSubscription.objects.create(school_id=school_id, plan=plan)
backend\subscriptions\tests\test_permissions_enforcement.py:120:    resp = client.get(f"/api/v1/subscriptions/ops/{school_id}/")
backend\subscriptions\tests\test_permissions_enforcement.py:126:    school_id = uuid.uuid4()
backend\subscriptions\tests\test_permissions_enforcement.py:127:    TenantSubscription.objects.create(school_id=school_id, plan=plan)
backend\subscriptions\tests\test_permissions_enforcement.py:132:    resp = client.get(f"/api/v1/subscriptions/ops/{school_id}/")
backend\subscriptions\tests\test_permissions_enforcement.py:136:    assert str(data["school_id"]) == str(school_id)
backend\subscriptions\tests\test_permissions_enforcement.py:150:    school_id = uuid.uuid4()
backend\subscriptions\tests\test_permissions_enforcement.py:151:    TenantSubscription.objects.create(school_id=school_id, plan=plan_old)
backend\subscriptions\tests\test_permissions_enforcement.py:157:        f"/api/v1/subscriptions/ops/{school_id}/",
backend\subscriptions\tests\test_permissions_enforcement.py:165:    old_sub = TenantSubscription.objects.get(school_id=school_id, plan=plan_old)
backend\tests\test_51x51_evidence_15_staff___faculty.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_15_staff___faculty.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_15_staff___faculty.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_15_staff___faculty.py:45:# tenant
backend\tests\test_51x51_evidence_15_staff___faculty.py:46:# cross-tenant
backend\tests\test_51x51_evidence_15_staff___faculty.py:48:# isolation
backend\tests\test_51x51_evidence_15_staff___faculty.py:70:# unauthorized
backend\tests\test_51x51_evidence_15_staff___faculty.py:72:# forbidden
backend\tests\test_51x51_evidence_13_student_master_record.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_13_student_master_record.py:13:MODULE_TEXT = 'Student Master Record\nStores official student identity, demographics, status, and record truth.\nCreate student | Edit student | Status | Profile | Search\nPersist official record | Prevent duplicates | Scope to school | Expose APIs | Link modules\nduplicate students | record completeness | student API pass rate | student search success | cross-tenant leakage\nhouseholds | enrollment | attendance | grades | billing\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_13_student_master_record.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_13_student_master_record.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_13_student_master_record.py:39:# duplicate students | record completeness | student API pass rate | student search success | cross-tenant leakage
backend\tests\test_51x51_evidence_13_student_master_record.py:45:# tenant
backend\tests\test_51x51_evidence_13_student_master_record.py:46:# cross-tenant
backend\tests\test_51x51_evidence_13_student_master_record.py:48:# isolation
backend\tests\test_51x51_evidence_13_student_master_record.py:70:# unauthorized
backend\tests\test_51x51_evidence_13_student_master_record.py:72:# forbidden
backend\parent360\tests\test_parent_overview_api.py:45:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:50:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:58:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:106:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:113:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:118:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:124:        school_id=school.id,
backend\parent360\tests\test_parent_overview_api.py:130:        school_id=school.id,
backend\finance\tests\test_finance_api.py:60:        school_id=school.id,
backend\finance\tests\test_finance_api.py:66:        hh = Household.objects.create(school_id=school.id, name=f"HH-{payer.username}")
backend\finance\tests\test_finance_api.py:68:            school_id=school.id,
backend\finance\tests\test_finance_api.py:75:    LedgerAccount.objects.get_or_create(school_id=school.id, household=hh)
backend\finance\tests\test_finance_api.py:108:def _json_post(client, url, data, school_id):
backend\finance\tests\test_finance_api.py:113:        HTTP_X_SCHOOL_ID=str(school_id),
backend\academics\tests\test_lesson_plans.py:5:- Tenant scoping: missing/wrong school_id rejected
backend\academics\tests\test_lesson_plans.py:12:- Cross-school isolation: cannot read another school's plans
backend\academics\tests\test_lesson_plans.py:66:        school_id=school.id,
backend\academics\tests\test_lesson_plans.py:73:        school_id=school.id,
backend\academics\tests\test_lesson_plans.py:78:        school_id=school.id,
backend\academics\tests\test_lesson_plans.py:88:        school_id=school.id,
backend\academics\tests\test_lesson_plans.py:94:        school_id=school.id,
backend\academics\tests\test_lesson_plans.py:112:    """Verify that the endpoint is scoped to X-School-Id."""
backend\academics\tests\test_lesson_plans.py:115:        """An unparseable UUID in X-School-Id must be rejected with 400."""
backend\academics\tests\test_lesson_plans.py:241:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:246:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:479:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:486:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:521:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:538:            school_id=school.id,
backend\academics\tests\test_lesson_plans.py:559:            school_id=school_b.id,
backend\fee_schedule_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\fee_schedule_wizard\tests\test_views.py:46:def _headers(school_id):
backend\fee_schedule_wizard\tests\test_views.py:47:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\fee_schedule_wizard\tests\test_views.py:72:def _advance_to_configured(client, school_id, **overrides):
backend\fee_schedule_wizard\tests\test_views.py:73:    r = client.post(BASE_URL, **_headers(school_id))
backend\fee_schedule_wizard\tests\test_views.py:77:    rc = client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
backend\fee_schedule_wizard\tests\test_views.py:82:def _advance_to_lines_set(client, school_id, lines=None, **overrides):
backend\fee_schedule_wizard\tests\test_views.py:83:    sid, name = _advance_to_configured(client, school_id, **overrides)
backend\fee_schedule_wizard\tests\test_views.py:85:    rl = client.post(f"{BASE_URL}{sid}/lines/", {"lines": lines}, format="json", **_headers(school_id))
backend\fee_schedule_wizard\tests\test_views.py:90:def _advance_to_committed(client, school_id, lines=None, **overrides):
backend\fee_schedule_wizard\tests\test_views.py:91:    sid, name = _advance_to_lines_set(client, school_id, lines=lines, **overrides)
backend\fee_schedule_wizard\tests\test_views.py:92:    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
backend\fee_schedule_wizard\tests\test_views.py:120:# Tenant isolation
backend\fee_schedule_wizard\tests\test_views.py:431:        # school_a schedule remains active (different tenant)
backend\fee_schedule_wizard\tests\test_views.py:433:        self.assertTrue(sched_a.is_active, "Cross-tenant schedule must not be deactivated")
backend\tests\test_tenant_header_validate_school.py:21:        self.assertIn("Invalid X-School-Id", r.json().get("detail", ""))
backend\tests\test_tenant_header_validate_school.py:30:        # not reject the request as a tenant-header error.
backend\tests\test_51x51_evidence_12_school_year___term.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_12_school_year___term.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_12_school_year___term.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_12_school_year___term.py:45:# tenant
backend\tests\test_51x51_evidence_12_school_year___term.py:46:# cross-tenant
backend\tests\test_51x51_evidence_12_school_year___term.py:48:# isolation
backend\tests\test_51x51_evidence_12_school_year___term.py:70:# unauthorized
backend\tests\test_51x51_evidence_12_school_year___term.py:72:# forbidden
backend\subscriptions\tests\test_module_tiers.py:74:        request.school_id = self.school.id
backend\subscriptions\tests\test_module_tiers.py:92:        request.school_id = self.school.id
backend\academics\tests\test_lane3_attendance_smoke.py:4:401/403 is acceptable; 302 means session-auth is leaking (forbidden pattern).
backend\tests\test_51x51_evidence_11_school_profile.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_11_school_profile.py:13:MODULE_TEXT = 'School Profile\nStores official school identity, tenant root, settings, logo, and configuration.\nSchool record | Settings | Branding | Contact data | Tenant setup\nCreate school | Configure school | Attach users | Control settings | Expose identity\nschool setup completion | missing settings | tenant config errors | school profile completeness | logo/config coverage\ntenant | auth | settings | frontend shell | documents\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_11_school_profile.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_11_school_profile.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_11_school_profile.py:36:# Stores official school identity, tenant root, settings, logo, and configuration.
backend\tests\test_51x51_evidence_11_school_profile.py:39:# school setup completion | missing settings | tenant config errors | school profile completeness | logo/config coverage
backend\tests\test_51x51_evidence_11_school_profile.py:40:# tenant | auth | settings | frontend shell | documents
backend\tests\test_51x51_evidence_11_school_profile.py:45:# tenant
backend\tests\test_51x51_evidence_11_school_profile.py:46:# cross-tenant
backend\tests\test_51x51_evidence_11_school_profile.py:48:# isolation
backend\tests\test_51x51_evidence_11_school_profile.py:70:# unauthorized
backend\tests\test_51x51_evidence_11_school_profile.py:72:# forbidden
backend\tests\test_tenant_header_required.py:17:        # middleware's "Missing required header: X-School-Id" error.
backend\tests\test_tenant_header_required.py:18:        self.assertNotIn(b"X-School-Id", r.content)
backend\tests\test_tenant_header_required.py:25:        self.assertIn("X-School-Id", str(r.content))
backend\tests\test_tenant_header_required.py:29:        """CORS preflight OPTIONS requests must pass without X-School-Id header"""
backend\tests\test_51x51_evidence_09_shared_design_system.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_09_shared_design_system.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_09_shared_design_system.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_09_shared_design_system.py:45:# tenant
backend\tests\test_51x51_evidence_09_shared_design_system.py:46:# cross-tenant
backend\tests\test_51x51_evidence_09_shared_design_system.py:48:# isolation
backend\tests\test_51x51_evidence_09_shared_design_system.py:70:# unauthorized
backend\tests\test_51x51_evidence_09_shared_design_system.py:72:# forbidden
backend\subscriptions\tests\test_entitlements_service.py:36:    """Helper: create plan + feature + entitlement + subscription; return (school_id, feature_key)."""
backend\subscriptions\tests\test_entitlements_service.py:46:    school_id = uuid.uuid4()
backend\subscriptions\tests\test_entitlements_service.py:47:    TenantSubscription.objects.create(school_id=school_id, plan=plan)
backend\subscriptions\tests\test_entitlements_service.py:48:    return school_id, feature_key
backend\subscriptions\tests\test_entitlements_service.py:56:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:57:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:63:    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:64:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:69:    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:70:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:80:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:82:    EntitlementOverride.objects.create(school_id=school_id, feature=feat, enabled=False)
backend\subscriptions\tests\test_entitlements_service.py:83:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:88:    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:90:    EntitlementOverride.objects.create(school_id=school_id, feature=feat, enabled=True, limit_int=50)
backend\subscriptions\tests\test_entitlements_service.py:91:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:97:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:99:    EntitlementOverride.objects.create(school_id=school_id, feature=feat, limit_int=500)
backend\subscriptions\tests\test_entitlements_service.py:100:    ent = EntitlementsService.get_entitlement(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:110:    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:111:    EntitlementsService.assert_enabled(school_id, key)  # should not raise
backend\subscriptions\tests\test_entitlements_service.py:115:    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:117:        EntitlementsService.assert_enabled(school_id, key)
backend\subscriptions\tests\test_entitlements_service.py:121:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:122:    EntitlementsService.assert_within_limit(school_id, key, increment=1)  # used_int=0 < 100
backend\subscriptions\tests\test_entitlements_service.py:126:    school_id, key = _make_plan_feature(enabled=True, limit_int=5)
backend\subscriptions\tests\test_entitlements_service.py:130:    UsageCounter.objects.create(school_id=school_id, feature=feat, period_yyyymm=yyyymm, used_int=5)
backend\subscriptions\tests\test_entitlements_service.py:132:        EntitlementsService.assert_within_limit(school_id, key, increment=1)
backend\subscriptions\tests\test_entitlements_service.py:136:    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
backend\subscriptions\tests\test_entitlements_service.py:140:    UsageCounter.objects.create(school_id=school_id, feature=feat, period_yyyymm=yyyymm, used_int=9999)
backend\subscriptions\tests\test_entitlements_service.py:141:    EntitlementsService.assert_within_limit(school_id, key, increment=9999)  # unlimited ΓåÆ no raise
backend\subscriptions\tests\test_entitlements_service.py:149:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:150:    EntitlementsService.increment_usage(school_id, key, increment=3)
backend\subscriptions\tests\test_entitlements_service.py:154:        school_id=school_id, feature=feat, period_yyyymm=Svc._period_yyyymm()
backend\subscriptions\tests\test_entitlements_service.py:160:    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
backend\subscriptions\tests\test_entitlements_service.py:161:    EntitlementsService.increment_usage(school_id, key, increment=10)
backend\subscriptions\tests\test_entitlements_service.py:162:    EntitlementsService.increment_usage(school_id, key, increment=5)
backend\subscriptions\tests\test_entitlements_service.py:166:        school_id=school_id, feature=feat, period_yyyymm=Svc._period_yyyymm()
backend\outreach\tests\test_outreach.py:58:    return PartnerOrganization.objects.create(school_id=school.id, name=name)
backend\outreach\tests\test_outreach.py:62:    return Opportunity.objects.create(school_id=school.id, partner=partner, title=title)
backend\outreach\tests\test_outreach.py:69:    return ServiceLog.objects.create(school_id=school.id, **kw)
backend\outreach\tests\test_outreach.py:77:    def test_invalid_school_id_400(self):
backend\outreach\tests\test_outreach.py:85:    def test_cross_tenant_partner_hidden(self):
backend\outreach\tests\test_outreach.py:87:        PartnerOrganization.objects.create(school_id=sb.id, name="B Partner")
backend\outreach\tests\test_outreach.py:88:        PartnerOrganization.objects.create(school_id=sa.id, name="A Partner")
backend\outreach\tests\test_outreach.py:179:    def test_cross_tenant_hidden(self):
backend\outreach\tests\test_outreach.py:294:    def test_cross_tenant_not_visible(self):
backend\outreach\tests\test_outreach.py:296:        ServiceLog.objects.create(school_id=sb.id, participant_type="STUDENT", hours=1)
backend\outreach\tests\test_outreach.py:323:        ServiceGoal.objects.create(school_id=self.school.id, required_hours=20)
backend\outreach\tests\test_outreach.py:324:        ServiceGoal.objects.create(school_id=self.school.id, required_hours=30)
backend\outreach\tests\test_outreach.py:355:        ReflectionPrompt.objects.create(school_id=self.school.id, title="P1", prompt="Q")
backend\outreach\tests\test_outreach.py:380:        Badge.objects.create(school_id=self.school.id, name="A")
backend\outreach\tests\test_outreach.py:381:        Badge.objects.create(school_id=self.school.id, name="B")
backend\outreach\tests\test_outreach.py:386:    def test_cross_tenant_hidden(self):
backend\outreach\tests\test_outreach.py:388:        Badge.objects.create(school_id=self.school.id, name="Ours")
backend\outreach\tests\test_outreach.py:389:        Badge.objects.create(school_id=sb.id, name="Theirs")
backend\outreach\tests\test_outreach.py:452:            school_id=self.school.id, name="Schoolwide", required_hours=25, active=True, grade=None
backend\integrations\tests\test_oneroster.py:10:- Tenant isolation: only exports data for requested school
backend\integrations\tests\test_oneroster.py:54:        school_id=school.id,
backend\integrations\tests\test_oneroster.py:61:        school_id=school.id,
backend\integrations\tests\test_oneroster.py:66:        school_id=school.id,
backend\integrations\tests\test_oneroster.py:71:    household = Household.objects.create(school_id=school.id, name="Test Family")
backend\integrations\tests\test_oneroster.py:73:        school_id=school.id,
backend\integrations\tests\test_oneroster.py:79:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\integrations\tests\test_oneroster.py:189:# Tenant isolation
backend\integrations\tests\test_oneroster.py:197:        Course.objects.create(school_id=school_a.id, code="MATH-A", name="Math A")
backend\integrations\tests\test_oneroster.py:198:        Course.objects.create(school_id=school_b.id, code="MATH-B", name="Math B")
backend\academics\tests\test_assignments_weights.py:54:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:61:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:66:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:73:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:77:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:84:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:102:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:111:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:120:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:147:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:154:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:163:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:170:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:179:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:187:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:216:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:223:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:230:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:239:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:246:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:255:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:263:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:288:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:325:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:338:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:355:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:374:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:405:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:415:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:433:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:452:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:461:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:489:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:505:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:523:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:539:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:554:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:562:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:579:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:587:        school_id=school.id,
backend\academics\tests\test_assignments_weights.py:602:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:610:        headers={"X-School-Id": str(school.id)},
backend\facops\tests\test_facops.py:9:  - Cross-tenant isolation
backend\facops\tests\test_facops.py:101:    def test_list_unauthenticated_denied(self):
backend\facops\tests\test_facops.py:115:    def test_create_denied_for_readonly_role(self):
backend\facops\tests\test_facops.py:122:    def test_cross_tenant_isolation(self):
backend\facops\tests\test_facops.py:177:    def test_asset_cross_tenant(self):
backend\facops\tests\test_facops.py:249:    def test_cross_tenant_work_orders(self):
backend\facops\tests\test_facops.py:298:    def test_cross_tenant(self):
backend\facops\tests\test_facops.py:367:    def test_cross_tenant(self):
backend\facops\tests\test_facops.py:463:    def test_unauthenticated_denied(self):
backend\tests\test_tenant_context_guardrails.py:5:from core.tenant_models import (
backend\tests\test_tenant_context_guardrails.py:9:    tenant_context,
backend\tests\test_tenant_context_guardrails.py:10:    require_tenant_context,
backend\tests\test_tenant_context_guardrails.py:27:            require_tenant_context()
backend\tests\test_tenant_context_guardrails.py:33:        with tenant_context(self.a):
backend\tests\test_tenant_context_guardrails.py:42:        with tenant_context(self.a):
backend\tests\test_tenant_context_guardrails.py:45:            with tenant_context(self.b):
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:13:MODULE_TEXT = 'Shared Frontend Shell\nProvides one consistent application frame, navigation, layout, and role-aware shell.\nHeader | Sidebar | Layout | Breadcrumbs | Role navigation\nRender app frame | Show allowed nav | Hide forbidden nav | Maintain context | Support dashboards\nroute success rate | nav broken links | shell render errors | role nav coverage | console errors\nReact Router | RBAC | role dashboards | design system | module pages\nDev 4\nPlatform Core'
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:38:# Render app frame | Show allowed nav | Hide forbidden nav | Maintain context | Support dashboards
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:45:# tenant
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:46:# cross-tenant
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:48:# isolation
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:70:# unauthorized
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:72:# forbidden
backend\integrations\tests\test_gate2c_webhook_idempotency.py:21:    household = Household.objects.create(school_id=school.id, name="Test Household")
backend\integrations\tests\test_gate2c_webhook_idempotency.py:22:    ledger_account = LedgerAccount.objects.create(school_id=school.id, household=household)
backend\integrations\tests\test_gate2c_webhook_idempotency.py:38:        school_id=school.id,
backend\academics\tests\test_assessments_api.py:35:        school_id=school.id,
backend\academics\tests\test_assessments_api.py:44:        school_id=school.id,
backend\academics\tests\test_assessments_api.py:51:        school_id=school.id,
backend\academics\tests\test_assessments_api.py:57:    household = Household.objects.create(school_id=school.id, name="Household")
backend\academics\tests\test_assessments_api.py:59:        school_id=school.id,
backend\academics\tests\test_assessments_api.py:65:    Enrollment.objects.create(school_id=school.id, section=section, student=student)
backend\academics\tests\test_assessments_api.py:75:        school_id=school.id,
backend\tests\test_51x51_evidence_06_document___file_framework.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_06_document___file_framework.py:13:MODULE_TEXT = 'Document / File Framework\nStores school, student, family, billing, evidence, and workflow documents safely.\nUpload | Download | Permissioned access | Versioning | Retention\nStore files | Scope to tenant | Attach to record | Restrict access | Audit file access\nupload success rate | download failures | orphan files | unauthorized file access | retention compliance\nstorage | tenant | RBAC | audit | records\nDev 1\nPlatform Core'
backend\tests\test_51x51_evidence_06_document___file_framework.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_06_document___file_framework.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_06_document___file_framework.py:38:# Store files | Scope to tenant | Attach to record | Restrict access | Audit file access
backend\tests\test_51x51_evidence_06_document___file_framework.py:39:# upload success rate | download failures | orphan files | unauthorized file access | retention compliance
backend\tests\test_51x51_evidence_06_document___file_framework.py:40:# storage | tenant | RBAC | audit | records
backend\tests\test_51x51_evidence_06_document___file_framework.py:45:# tenant
backend\tests\test_51x51_evidence_06_document___file_framework.py:46:# cross-tenant
backend\tests\test_51x51_evidence_06_document___file_framework.py:48:# isolation
backend\tests\test_51x51_evidence_06_document___file_framework.py:70:# unauthorized
backend\tests\test_51x51_evidence_06_document___file_framework.py:72:# forbidden
backend\tests\test_51x51_evidence_05_notifications_framework.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_05_notifications_framework.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_05_notifications_framework.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_05_notifications_framework.py:45:# tenant
backend\tests\test_51x51_evidence_05_notifications_framework.py:46:# cross-tenant
backend\tests\test_51x51_evidence_05_notifications_framework.py:48:# isolation
backend\tests\test_51x51_evidence_05_notifications_framework.py:70:# unauthorized
backend\tests\test_51x51_evidence_05_notifications_framework.py:72:# forbidden
backend\tests\test_tenant_bulk_ops_guard.py:4:from core.tenant_models import set_current_school, clear_current_school, TenantBulkOpViolation
backend\tests\test_tenant_bulk_ops_guard.py:15:        # Seed one row in each tenant
backend\tests\test_tenant_bulk_ops_guard.py:22:    def test_bulk_update_requires_tenant_context(self):
backend\tests\test_tenant_bulk_ops_guard.py:27:    def test_bulk_delete_requires_tenant_context(self):
backend\tests\test_tenant_bulk_ops_guard.py:32:    def test_bulk_ops_scoped_to_current_tenant(self):
backend\tests\test_tenant_bulk_ops_guard.py:33:        # With tenant A context, bulk ops must only touch tenant A rows
backend\tests\test_tenant_bulk_ops_guard.py:53:        remaining = list(Classroom._base_manager.values_list("school_id", flat=True))
backend\academics\tests\test_academics_readonly_api.py:60:    assert all(r["school_id"] == str(school_a.id) for r in results)
backend\academics\tests\test_academics_readonly_api.py:73:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:80:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:86:    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")
backend\academics\tests\test_academics_readonly_api.py:89:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:96:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:125:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:131:    course = Course.objects.create(school_id=school.id, code="ENG-201", name="English")
backend\academics\tests\test_academics_readonly_api.py:134:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:141:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:165:    TeacherAssignment.objects.create(school_id=school.id, section=section_a, staff=staff_a)
backend\academics\tests\test_academics_readonly_api.py:166:    TeacherAssignment.objects.create(school_id=school.id, section=section_b, staff=staff_b)
backend\academics\tests\test_academics_readonly_api.py:189:    household_a = Household.objects.create(school_id=school.id, name="Household A")
backend\academics\tests\test_academics_readonly_api.py:190:    household_b = Household.objects.create(school_id=school.id, name="Household B")
backend\academics\tests\test_academics_readonly_api.py:193:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:201:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:208:        school_id=school.id,
backend\academics\tests\test_academics_readonly_api.py:228:    CurriculumSource.objects.create(school_id=school.id, name="BJU Press Heritage Studies")
backend\academics\tests\test_academics_readonly_api.py:229:    CurriculumSource.objects.create(school_id=school.id, name="Abeka Grade 5")
backend\academics\tests\test_academics_readonly_api.py:230:    CurriculumSource.objects.create(school_id=school.id, name="Independent Teacher Notes", source_type="research")
backend\academics\tests\test_academics_readonly_api.py:247:    CurriculumSource.objects.create(school_id=school.id, name="BJU Press Math 6")
backend\academics\tests\test_academics_readonly_api.py:248:    CurriculumSource.objects.create(school_id=school.id, name="Summit Ministries Worldview")
backend\tests\test_51x51_evidence_04_audit_logging.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_04_audit_logging.py:13:MODULE_TEXT = 'Audit Logging\nRecords sensitive user, data, permission, export, billing, and compliance events.\nCreate logs | Update logs | Delete logs | Export logs | Permission-change logs\nCapture actor | Capture tenant | Capture before/after | Persist immutable event | Expose audit review\naudit event count | sensitive action coverage | missing audit events | export log coverage | FERPA audit pass rate\nmodels | middleware | service layer | finance | student data\nDev 1\nPlatform Core'
backend\tests\test_51x51_evidence_04_audit_logging.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_04_audit_logging.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_04_audit_logging.py:36:# Records sensitive user, data, permission, export, billing, and compliance events.
backend\tests\test_51x51_evidence_04_audit_logging.py:38:# Capture actor | Capture tenant | Capture before/after | Persist immutable event | Expose audit review
backend\tests\test_51x51_evidence_04_audit_logging.py:45:# tenant
backend\tests\test_51x51_evidence_04_audit_logging.py:46:# cross-tenant
backend\tests\test_51x51_evidence_04_audit_logging.py:48:# isolation
backend\tests\test_51x51_evidence_04_audit_logging.py:70:# unauthorized
backend\tests\test_51x51_evidence_04_audit_logging.py:72:# forbidden
backend\student_records\tests\test_student_records_routes.py:70:def test_list_scopes_to_tenant_school():
backend\student_records\tests\test_student_records_routes.py:89:def test_detail_cross_tenant_returns_404():
backend\student_records\tests\test_student_records_routes.py:108:def test_detail_not_found_returns_404_with_valid_tenant():
backend\onboarding\tests\test_views.py:6:- Tenant isolation (cross-school session access denied)
backend\onboarding\tests\test_views.py:96:    def test_unauthenticated_create_denied(self, school_a):
backend\onboarding\tests\test_views.py:102:    def test_missing_school_header_denied(self, user):
backend\onboarding\tests\test_views.py:132:# 3. Tenant isolation
backend\onboarding\tests\test_views.py:137:    def test_cross_school_upload_denied(self, client_b, school_a):
backend\onboarding\tests\test_views.py:143:    def test_cross_school_validate_denied(self, client_b, school_a):
backend\onboarding\tests\test_views.py:148:    def test_cross_school_preview_denied(self, client_b, school_a):
backend\onboarding\tests\test_views.py:153:    def test_cross_school_commit_denied(self, client_b, school_a):
backend\onboarding\tests\test_views.py:161:    def test_cross_school_verify_denied(self, client_b, school_a):
backend\tests\conftest.py:4:    # Conventions for API tenant context in tests:
backend\tests\conftest.py:42:    # Disable tenant header enforcement globally in tests.
backend\reenrollment\tests\test_views.py:6:- Tenant isolation (cross-school session access denied on all 6 endpoints)
backend\reenrollment\tests\test_views.py:75:def _make_household_and_students(school_id, n=2, active=True):
backend\reenrollment\tests\test_views.py:76:    """Create a household with n students for the given school_id (UUID)."""
backend\reenrollment\tests\test_views.py:78:        school_id=school_id,
backend\reenrollment\tests\test_views.py:83:            school_id=school_id,
backend\reenrollment\tests\test_views.py:101:    def test_unauthenticated_create_denied(self, school_a):
backend\reenrollment\tests\test_views.py:107:    def test_missing_school_header_denied(self, user):
backend\reenrollment\tests\test_views.py:116:# 2. Tenant isolation
backend\reenrollment\tests\test_views.py:364:        assert InvoiceLine.objects.filter(school_id=school_a.id).count() == 2
backend\reenrollment\tests\test_views.py:376:        assert BillingRun.objects.filter(school_id=school_a.id).count() == 1
backend\academics\tests\test_academics_api.py:18:    if hasattr(u, "school_id"):
backend\academics\tests\test_academics_api.py:19:        setattr(u, "school_id", school.id)
backend\academics\tests\test_academics_api.py:20:        u.save(update_fields=["school_id"])
backend\academics\tests\test_academics_api.py:26:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\academics\tests\test_academics_api.py:62:        school_id=school.id,
backend\academics\tests\test_academics_api.py:95:        school_id=school.id,
backend\tests\test_tenant_auto_scope.py:2:Tests for tenant auto-scoping with fail-closed behavior.
backend\tests\test_tenant_auto_scope.py:6:from core.tenant_models import set_current_school, get_current_school, clear_current_school
backend\households\tests\test_tenant_isolation.py:2:Tenant isolation tests per TENANT_PRIVACY_CANON.md
backend\households\tests\test_tenant_isolation.py:5:- Missing tenant context ΓåÆ fail-closed deny (400/401/403)
backend\households\tests\test_tenant_isolation.py:6:- Wrong tenant context ΓåÆ 404 (non-staff)
backend\households\tests\test_tenant_isolation.py:7:- Correct tenant context ΓåÆ 200
backend\households\tests\test_tenant_isolation.py:8:- Querysets never return cross-tenant rows
backend\households\tests\test_tenant_isolation.py:26:    Tenant isolation enforcement tests.
backend\households\tests\test_tenant_isolation.py:39:            school_id=self.school_a.id
backend\households\tests\test_tenant_isolation.py:46:            school_id=self.school_b.id
backend\households\tests\test_tenant_isolation.py:54:            school_id=self.school_a.id
backend\households\tests\test_tenant_isolation.py:59:            school_id=self.school_a.id,
backend\households\tests\test_tenant_isolation.py:63:            school_id=self.school_b.id,
backend\households\tests\test_tenant_isolation.py:69:            school_id=self.school_a.id,
backend\households\tests\test_tenant_isolation.py:75:            school_id=self.school_b.id,
backend\households\tests\test_tenant_isolation.py:83:    def test_missing_tenant_fails_closed_or_empty_scope(self):
backend\households\tests\test_tenant_isolation.py:85:        Missing tenant context must fail closed (400/401/403), and
backend\households\tests\test_tenant_isolation.py:86:        no-school authenticated requests must not leak cross-tenant data.
backend\households\tests\test_tenant_isolation.py:88:        # Anonymous request (no auth, no tenant)
backend\households\tests\test_tenant_isolation.py:90:        # Missing tenant context may be denied by auth layer (401/403)
backend\households\tests\test_tenant_isolation.py:91:        # or tenant middleware (400), all of which are fail-closed outcomes.
backend\households\tests\test_tenant_isolation.py:94:        # Authenticated but user has no school_id
backend\households\tests\test_tenant_isolation.py:101:        # Endpoints using get_request_school_id(required=True) should return 400
backend\households\tests\test_tenant_isolation.py:110:    def test_wrong_tenant_returns_404_non_staff(self):
backend\households\tests\test_tenant_isolation.py:112:        CANON Rule 3: Non-staff cross-tenant access MUST return 404 (not 403)
backend\households\tests\test_tenant_isolation.py:124:    def test_correct_tenant_returns_200(self):
backend\households\tests\test_tenant_isolation.py:126:        CANON Rule 6: Correct tenant context MUST return 200 and scoped data
backend\households\tests\test_tenant_isolation.py:150:    def test_staff_can_override_tenant(self):
backend\households\tests\test_tenant_isolation.py:152:        CANON Rule 2: Staff may use X-School-Id header to override
backend\households\tests\test_tenant_isolation.py:166:    def test_invalid_tenant_header_returns_400(self):
backend\households\tests\test_tenant_isolation.py:168:        Invalid UUID in tenant header MUST return 400
backend\households\tests\test_tenant_isolation.py:178:    def test_nonexistent_tenant_returns_404(self):
backend\households\tests\test_tenant_isolation.py:191:    def test_queryset_never_crosses_tenants(self):
backend\households\tests\test_tenant_isolation.py:193:        CANON Rule 6: Querysets MUST NOT return cross-tenant rows
backend\households\tests\test_tenant_isolation.py:207:    def test_finance_endpoint_respects_tenant(self):
backend\households\tests\test_tenant_isolation.py:209:        Sensitive endpoints (finance) MUST enforce tenant isolation
backend\households\tests\test_tenant_isolation.py:217:        # Should either succeed with School A data or require explicit tenant
backend\onboarding\tests\test_parent_enrollment_guidance.py:196:    def test_tenant_isolation_remains_enforced(self):
backend\student_import_wizard\tests\test_views.py:31:def _h(school_id):
backend\student_import_wizard\tests\test_views.py:32:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\student_import_wizard\tests\test_views.py:109:    def test_cross_tenant_returns_404(self):
backend\households\tests\test_households_api.py:13:def _mk_user_with_school_id(school_id):
backend\households\tests\test_households_api.py:16:        id=school_id,
backend\households\tests\test_households_api.py:17:        defaults={"name": f"School-{school_id}"},
backend\households\tests\test_households_api.py:25:    # Attach school_id if the model supports it
backend\households\tests\test_households_api.py:26:    if hasattr(u, "school_id"):
backend\households\tests\test_households_api.py:27:        setattr(u, "school_id", school_id)
backend\households\tests\test_households_api.py:28:        u.save(update_fields=["school_id"])
backend\households\tests\test_households_api.py:36:    hh_a = Household.objects.create(school_id=school_a, name="Megahan Household")
backend\households\tests\test_households_api.py:37:    Household.objects.create(school_id=school_b, name="Other School Household")
backend\households\tests\test_households_api.py:39:    user = _mk_user_with_school_id(school_a)
backend\households\tests\test_households_api.py:50:def test_household_retrieve_is_scoped_forbidden_by_empty_result():
backend\households\tests\test_households_api.py:54:    hh_b = Household.objects.create(school_id=school_b, name="Other School Household")
backend\households\tests\test_households_api.py:56:    user = _mk_user_with_school_id(school_a)
backend\households\tests\test_households_api.py:68:    hh = Household.objects.create(school_id=school_a, name="Heritage Household")
backend\households\tests\test_households_api.py:70:        school_id=school_a,
backend\households\tests\test_households_api.py:79:        school_id=school_a,
backend\households\tests\test_households_api.py:87:    user = _mk_user_with_school_id(school_a)
backend\journal\tests\test_journal_invariants.py:84:    def test_cross_tenant_account_fails(self):
backend\households\tests\test_guardian_scoping.py:13:# Uses Django TestCase + @override_settings (matches test_tenant_isolation.py).
backend\households\tests\test_guardian_scoping.py:45:    hh = Household.objects.create(school_id=school.id, name=name)
backend\households\tests\test_guardian_scoping.py:47:        school_id=school.id,
backend\households\tests\test_guardian_scoping.py:60:        school_id=school.id,
backend\quarantine_old_tests\old_test_email_logic_simple.py:31:    school_id = str(school.id)
backend\quarantine_old_tests\old_test_email_logic_simple.py:46:    print(f"  School: {school_id}")
backend\quarantine_old_tests\old_test_email_logic_simple.py:58:    if school_id:
backend\quarantine_old_tests\old_test_email_logic_simple.py:59:        query = query.filter(school_id=school_id)
backend\tests\test_survey_sentiment_unit.py:42:    """Verify tenant/school scoping keywords appear in the Survey Sentiment Engine source tree."""
backend\tests\test_survey_sentiment_unit.py:50:        "school_id" in source_text
backend\tests\test_survey_sentiment_unit.py:53:    ), f"Survey Sentiment Engine: tenant/school scoping not found in source"
backend\tests\test_survey_sentiment_tenant.py:2:Tenant isolation tests for the Survey Sentiment Engine module.
backend\tests\test_survey_sentiment_tenant.py:23:        username=f"tenant-a-survey_sentiment-{token}",
backend\tests\test_survey_sentiment_tenant.py:32:    """Cross-tenant isolation tests for Survey Sentiment Engine."""
backend\tests\test_survey_sentiment_tenant.py:38:    def test_survey_sentiment_tenant_school_ids_are_distinct(self):
backend\tests\test_survey_sentiment_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_survey_sentiment_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_survey_sentiment_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_survey_sentiment_tenant.py:47:    def test_survey_sentiment_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_survey_sentiment_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_survey_sentiment_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_survey_sentiment_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_survey_sentiment_tenant.py:58:    def test_survey_sentiment_same_tenant_request_is_allowed(self):
backend\tests\test_survey_sentiment_tenant.py:67:    def test_survey_sentiment_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_survey_sentiment_tenant.py:75:    def test_survey_sentiment_isolation_keyword_present_in_source(self):
backend\tests\test_survey_sentiment_tenant.py:76:        """Tenant isolation keywords exist in the Survey Sentiment Engine module source."""
backend\tests\test_survey_sentiment_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_survey_sentiment_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_survey_sentiment_tenant.py:87:        assert found, f"Survey Sentiment Engine: tenant isolation keywords not found in source"
backend\quarantine_old_tests\old_test_director_apis.py:43:    req = factory.get(f'/api/director/aid/summary/?school_id={school.id}&academic_year_id={current_year.id}')
backend\quarantine_old_tests\old_test_director_apis.py:57:    req = factory.get(f'/api/director/finance/summary/?school_id={school.id}&academic_year_id={current_year.id}')
backend\quarantine_old_tests\old_test_director_apis.py:71:    req = factory.get(f'/api/director/registrar/summary/?school_id={school.id}&academic_year_id={current_year.id}')
backend\tests\test_survey_sentiment_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_survey_sentiment_negative.py:33:    """Negative tests for Survey Sentiment Engine: unauthorized, invalid, forbidden paths."""
backend\tests\test_survey_sentiment_negative.py:40:    def test_survey_sentiment_unauthenticated_request_is_forbidden(self):
backend\tests\test_survey_sentiment_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_survey_sentiment_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_survey_sentiment_api.py:61:        """School record for Survey Sentiment Engine tenant is created and queryable."""
backend\tests\test_survey_sentiment_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_survey_sentiment_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_student_master_record_unit.py:42:    """Verify tenant/school scoping keywords appear in the Student Master Record source tree."""
backend\tests\test_student_master_record_unit.py:50:        "school_id" in source_text
backend\tests\test_student_master_record_unit.py:53:    ), f"Student Master Record: tenant/school scoping not found in source"
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\invoice_run_wizard\tests\test_views.py:28:def _headers(school_id):
backend\invoice_run_wizard\tests\test_views.py:29:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\invoice_run_wizard\tests\test_views.py:51:def _advance_to_configured(client, school_id):
backend\invoice_run_wizard\tests\test_views.py:52:    r = client.post(BASE_URL, **_headers(school_id))
backend\invoice_run_wizard\tests\test_views.py:58:        **_headers(school_id),
backend\invoice_run_wizard\tests\test_views.py:63:def _advance_to_loaded(client, school_id):
backend\invoice_run_wizard\tests\test_views.py:64:    sid = _advance_to_configured(client, school_id)
backend\invoice_run_wizard\tests\test_views.py:65:    client.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school_id))
backend\invoice_run_wizard\tests\test_views.py:69:def _advance_to_committed(client, school_id):
backend\invoice_run_wizard\tests\test_views.py:70:    sid = _advance_to_loaded(client, school_id)
backend\invoice_run_wizard\tests\test_views.py:75:        **_headers(school_id),
backend\guardian_household_wizard\tests\test_views.py:31:def _h(school_id):
backend\guardian_household_wizard\tests\test_views.py:32:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\guardian_household_wizard\tests\test_views.py:100:    def test_cross_tenant_returns_404(self):
backend\tests\test_student_master_record_tenant.py:2:Tenant isolation tests for the Student Master Record module.
backend\tests\test_student_master_record_tenant.py:23:        username=f"tenant-a-student_master_record-{token}",
backend\tests\test_student_master_record_tenant.py:32:    """Cross-tenant isolation tests for Student Master Record."""
backend\tests\test_student_master_record_tenant.py:38:    def test_student_master_record_tenant_school_ids_are_distinct(self):
backend\tests\test_student_master_record_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_student_master_record_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_student_master_record_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_student_master_record_tenant.py:47:    def test_student_master_record_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_student_master_record_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_student_master_record_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_student_master_record_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_student_master_record_tenant.py:58:    def test_student_master_record_same_tenant_request_is_allowed(self):
backend\tests\test_student_master_record_tenant.py:67:    def test_student_master_record_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_student_master_record_tenant.py:75:    def test_student_master_record_isolation_keyword_present_in_source(self):
backend\tests\test_student_master_record_tenant.py:76:        """Tenant isolation keywords exist in the Student Master Record module source."""
backend\tests\test_student_master_record_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_student_master_record_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_student_master_record_tenant.py:87:        assert found, f"Student Master Record: tenant isolation keywords not found in source"
backend\student360\tests\test_scope_qs_to_school.py:37:    school_id = "field"
backend\student360\tests\test_scope_qs_to_school.py:46:    """Has both school_id and school. school_id must take precedence."""
backend\student360\tests\test_scope_qs_to_school.py:48:    school_id = "field"
backend\student360\tests\test_scope_qs_to_school.py:54:    # no school_id, no school
backend\student360\tests\test_scope_qs_to_school.py:63:    def test_uses_school_id_when_present(self):
backend\student360\tests\test_scope_qs_to_school.py:70:        assert qs.filters == [{"school_id": str(school.id)}]
backend\student360\tests\test_scope_qs_to_school.py:72:    def test_uses_school_fk_when_no_school_id(self):
backend\student360\tests\test_scope_qs_to_school.py:81:    def test_school_id_takes_precedence_over_school_fk(self):
backend\student360\tests\test_scope_qs_to_school.py:82:        """When a model has both school_id and school, school_id wins."""
backend\student360\tests\test_scope_qs_to_school.py:88:        # Must use school_id, not school FK
backend\student360\tests\test_scope_qs_to_school.py:89:        assert qs.filters == [{"school_id": str(school.id)}]
backend\student360\tests\test_scope_qs_to_school.py:91:    def test_school_id_value_is_string(self):
backend\student360\tests\test_scope_qs_to_school.py:92:        """school_id filter value must be str(school.id), matching model field type."""
backend\student360\tests\test_scope_qs_to_school.py:98:        assert qs.filters[0]["school_id"] == "abc-123"
backend\student360\tests\test_scope_qs_to_school.py:99:        assert isinstance(qs.filters[0]["school_id"], str)
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_student_master_record_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_student_master_record_negative.py:33:    """Negative tests for Student Master Record: unauthorized, invalid, forbidden paths."""
backend\tests\test_student_master_record_negative.py:40:    def test_student_master_record_unauthenticated_request_is_forbidden(self):
backend\tests\test_student_master_record_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\student360\tests\test_overview_api.py:25:    if hasattr(user, "school_id"):
backend\student360\tests\test_overview_api.py:59:    household = Household.objects.create(school_id=school.id, name="Stone Household")
backend\student360\tests\test_overview_api.py:61:        school_id=school.id,
backend\tests\test_student_master_record_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_student_master_record_api.py:61:        """School record for Student Master Record tenant is created and queryable."""
backend\tests\test_student_master_record_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_student_master_record_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\grade_weights_wizard\tests\test_views.py:34:def _h(school_id):
backend\grade_weights_wizard\tests\test_views.py:35:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\grade_weights_wizard\tests\test_views.py:126:    def test_cross_tenant_returns_404(self):
backend\tests\test_student_care_discipline_unit.py:42:    """Verify tenant/school scoping keywords appear in the Student Care Discipline Summary source tree."""
backend\tests\test_student_care_discipline_unit.py:50:        "school_id" in source_text
backend\tests\test_student_care_discipline_unit.py:53:    ), f"Student Care Discipline Summary: tenant/school scoping not found in source"
backend\tests\test_student_care_discipline_tenant.py:2:Tenant isolation tests for the Student Care Discipline Summary module.
backend\tests\test_student_care_discipline_tenant.py:23:        username=f"tenant-a-student_care_discipline-{token}",
backend\tests\test_student_care_discipline_tenant.py:32:    """Cross-tenant isolation tests for Student Care Discipline Summary."""
backend\tests\test_student_care_discipline_tenant.py:38:    def test_student_care_discipline_tenant_school_ids_are_distinct(self):
backend\tests\test_student_care_discipline_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_student_care_discipline_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_student_care_discipline_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_student_care_discipline_tenant.py:47:    def test_student_care_discipline_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_student_care_discipline_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_student_care_discipline_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_student_care_discipline_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_student_care_discipline_tenant.py:58:    def test_student_care_discipline_same_tenant_request_is_allowed(self):
backend\tests\test_student_care_discipline_tenant.py:67:    def test_student_care_discipline_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_student_care_discipline_tenant.py:75:    def test_student_care_discipline_isolation_keyword_present_in_source(self):
backend\tests\test_student_care_discipline_tenant.py:76:        """Tenant isolation keywords exist in the Student Care Discipline Summary module source."""
backend\tests\test_student_care_discipline_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_student_care_discipline_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_student_care_discipline_tenant.py:87:        assert found, f"Student Care Discipline Summary: tenant isolation keywords not found in source"
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_student_care_discipline_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_student_care_discipline_negative.py:33:    """Negative tests for Student Care Discipline Summary: unauthorized, invalid, forbidden paths."""
backend\tests\test_student_care_discipline_negative.py:40:    def test_student_care_discipline_unauthenticated_request_is_forbidden(self):
backend\tests\test_student_care_discipline_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_student_care_discipline_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_student_care_discipline_api.py:61:        """School record for Student Care Discipline Summary tenant is created and queryable."""
backend\tests\test_student_care_discipline_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_student_care_discipline_api.py:67:        assert self.user.school_id == self.school.id
backend\ledger\tests\test_gate2b_charge_void_reversal.py:25:    household = Household.objects.create(school_id=school.id, name="Test Household")
backend\ledger\tests\test_gate2b_charge_void_reversal.py:26:    ledger_account = LedgerAccount.objects.create(school_id=school.id, household=household)
backend\ledger\tests\test_gate2b_charge_void_reversal.py:34:        school_id=school.id,
backend\tests\test_staff_faculty_unit.py:42:    """Verify tenant/school scoping keywords appear in the Staff Faculty source tree."""
backend\tests\test_staff_faculty_unit.py:50:        "school_id" in source_text
backend\tests\test_staff_faculty_unit.py:53:    ), f"Staff Faculty: tenant/school scoping not found in source"
backend\tests\test_staff_faculty_tenant.py:2:Tenant isolation tests for the Staff Faculty module.
backend\tests\test_staff_faculty_tenant.py:23:        username=f"tenant-a-staff_faculty-{token}",
backend\tests\test_staff_faculty_tenant.py:32:    """Cross-tenant isolation tests for Staff Faculty."""
backend\tests\test_staff_faculty_tenant.py:38:    def test_staff_faculty_tenant_school_ids_are_distinct(self):
backend\tests\test_staff_faculty_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_staff_faculty_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_staff_faculty_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_staff_faculty_tenant.py:47:    def test_staff_faculty_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_staff_faculty_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_staff_faculty_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_staff_faculty_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_staff_faculty_tenant.py:58:    def test_staff_faculty_same_tenant_request_is_allowed(self):
backend\tests\test_staff_faculty_tenant.py:67:    def test_staff_faculty_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_staff_faculty_tenant.py:75:    def test_staff_faculty_isolation_keyword_present_in_source(self):
backend\tests\test_staff_faculty_tenant.py:76:        """Tenant isolation keywords exist in the Staff Faculty module source."""
backend\tests\test_staff_faculty_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_staff_faculty_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_staff_faculty_tenant.py:87:        assert found, f"Staff Faculty: tenant isolation keywords not found in source"
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\ledger\tests\test_ar_posts_to_journal.py:26:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:31:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:45:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:64:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:83:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:106:            school_id=self.school.id,
backend\ledger\tests\test_ar_posts_to_journal.py:120:            school_id=self.school.id,
backend\grade_scale_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\grade_scale_wizard\tests\test_views.py:53:def _headers(school_id):
backend\grade_scale_wizard\tests\test_views.py:54:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\grade_scale_wizard\tests\test_views.py:96:def _advance_to_configured(client, school_id, ay=None, **cfg_overrides):
backend\grade_scale_wizard\tests\test_views.py:98:        school = School.objects.get(pk=school_id)
backend\grade_scale_wizard\tests\test_views.py:100:    r = client.post(BASE_URL, **_headers(school_id))
backend\grade_scale_wizard\tests\test_views.py:103:    client.post(f"{BASE_URL}{sid}/configure/", payload, format="json", **_headers(school_id))
backend\grade_scale_wizard\tests\test_views.py:107:def _advance_to_bands_set(client, school_id, ay=None, bands=None):
backend\grade_scale_wizard\tests\test_views.py:108:    sid, ay = _advance_to_configured(client, school_id, ay=ay)
backend\grade_scale_wizard\tests\test_views.py:113:        **_headers(school_id),
backend\grade_scale_wizard\tests\test_views.py:118:def _advance_to_committed(client, school_id, ay=None, bands=None, weights=None):
backend\grade_scale_wizard\tests\test_views.py:119:    sid, ay = _advance_to_bands_set(client, school_id, ay=ay, bands=bands)
backend\grade_scale_wizard\tests\test_views.py:125:            **_headers(school_id),
backend\grade_scale_wizard\tests\test_views.py:127:    client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
backend\grade_scale_wizard\tests\test_views.py:155:# Tenant isolation
backend\grade_scale_wizard\tests\test_views.py:577:    def test_cross_tenant_isolation(self):
backend\tests\test_staff_faculty_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_staff_faculty_negative.py:33:    """Negative tests for Staff Faculty: unauthorized, invalid, forbidden paths."""
backend\tests\test_staff_faculty_negative.py:40:    def test_staff_faculty_unauthenticated_request_is_forbidden(self):
backend\tests\test_staff_faculty_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\payments\tests\test_webhook_idempotency.py:28:            "metadata": {"school_id": "00000000-0000-0000-0000-000000000000"},
backend\payments\tests\test_bank_reconciliation.py:17:            school_id=school.id,
backend\payments\tests\test_bank_reconciliation.py:24:            school_id=school.id,
backend\payments\tests\test_bank_reconciliation.py:33:            school_id=school.id,
backend\payments\tests\test_bank_reconciliation.py:45:        matched = auto_match_payout_batches_for_school(school_id=school.id)
backend\ledger\tests\test_ledger_immutability.py:31:    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
backend\ledger\tests\test_ledger_immutability.py:32:    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
backend\ledger\tests\test_ledger_immutability.py:38:        school_id=sid,
backend\ledger\tests\test_ledger_immutability.py:47:        school_id=sid,
backend\ledger\tests\test_ledger_immutability.py:101:    hh2 = Household.objects.create(school_id=sid, name=f"HH2-{uuid.uuid4()}")
backend\ledger\tests\test_ledger_immutability.py:102:    acct2 = LedgerAccount.objects.create(school_id=sid, household=hh2)
backend\staff_onboarding_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required, mismatch ΓåÆ 404)
backend\staff_onboarding_wizard\tests\test_views.py:44:def _headers(school_id):
backend\staff_onboarding_wizard\tests\test_views.py:45:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\staff_onboarding_wizard\tests\test_views.py:65:def _advance_to_configured(client, school_id, **overrides):
backend\staff_onboarding_wizard\tests\test_views.py:67:    r = client.post(BASE_URL, **_headers(school_id))
backend\staff_onboarding_wizard\tests\test_views.py:75:        **_headers(school_id),
backend\staff_onboarding_wizard\tests\test_views.py:81:def _advance_to_previewed(client, school_id, **overrides):
backend\staff_onboarding_wizard\tests\test_views.py:82:    sid, email = _advance_to_configured(client, school_id, **overrides)
backend\staff_onboarding_wizard\tests\test_views.py:83:    rp = client.get(f"{BASE_URL}{sid}/preview/", **_headers(school_id))
backend\staff_onboarding_wizard\tests\test_views.py:88:def _advance_to_committed(client, school_id, **overrides):
backend\staff_onboarding_wizard\tests\test_views.py:89:    sid, email = _advance_to_previewed(client, school_id, **overrides)
backend\staff_onboarding_wizard\tests\test_views.py:90:    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
backend\staff_onboarding_wizard\tests\test_views.py:120:# Tenant isolation
backend\ledger\tests\test_revenue_integrity.py:29:def _school_id() -> uuid.UUID:
backend\ledger\tests\test_revenue_integrity.py:33:def _ensure_school(school_id: uuid.UUID) -> "School":
backend\ledger\tests\test_revenue_integrity.py:35:        id=school_id,
backend\ledger\tests\test_revenue_integrity.py:36:        defaults={"name": f"Test School {school_id}"},
backend\ledger\tests\test_revenue_integrity.py:41:def _make_household(school_id: uuid.UUID) -> Household:
backend\ledger\tests\test_revenue_integrity.py:42:    _ensure_school(school_id)
backend\ledger\tests\test_revenue_integrity.py:43:    return Household.objects.create(school_id=school_id, name="Test Family")
backend\ledger\tests\test_revenue_integrity.py:48:        school_id=household.school_id,
backend\ledger\tests\test_revenue_integrity.py:55:        school_id=account.school_id,
backend\ledger\tests\test_revenue_integrity.py:67:        self.school_id = _school_id()
backend\ledger\tests\test_revenue_integrity.py:68:        self.hh = _make_household(self.school_id)
backend\ledger\tests\test_revenue_integrity.py:73:        record = register_failed_payment(payment=self.payment, school_id=self.school_id)
backend\ledger\tests\test_revenue_integrity.py:79:        r1 = register_failed_payment(payment=self.payment, school_id=self.school_id)
backend\ledger\tests\test_revenue_integrity.py:80:        r2 = register_failed_payment(payment=self.payment, school_id=self.school_id)
backend\ledger\tests\test_revenue_integrity.py:96:        self.school_id = _school_id()
backend\ledger\tests\test_revenue_integrity.py:97:        self.hh = _make_household(self.school_id)
backend\ledger\tests\test_revenue_integrity.py:103:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:119:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:134:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:149:        self.school_id = _school_id()
backend\ledger\tests\test_revenue_integrity.py:150:        self.hh = _make_household(self.school_id)
backend\ledger\tests\test_revenue_integrity.py:156:            [{"amount": "250.00"}], school_id=self.school_id
backend\ledger\tests\test_revenue_integrity.py:164:            [{"amount": "300.00"}], school_id=self.school_id
backend\ledger\tests\test_revenue_integrity.py:171:        summary = build_monthly_summary(school_id=self.school_id)
backend\ledger\tests\test_revenue_integrity.py:181:        self.school_id = _school_id()
backend\ledger\tests\test_revenue_integrity.py:182:        self.hh = _make_household(self.school_id)
backend\ledger\tests\test_revenue_integrity.py:188:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:198:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:214:        self.school_id = _school_id()
backend\ledger\tests\test_revenue_integrity.py:215:        self.hh = _make_household(self.school_id)
backend\ledger\tests\test_revenue_integrity.py:220:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:235:            school_id=self.school_id,
backend\ledger\tests\test_revenue_integrity.py:249:            school_id=self.school_id,
backend\tests\test_staff_faculty_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_staff_faculty_api.py:61:        """School record for Staff Faculty tenant is created and queryable."""
backend\tests\test_staff_faculty_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_staff_faculty_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\ledger\tests\test_ledger_api.py:16:def _mk_user_with_school_id(school_id):
backend\ledger\tests\test_ledger_api.py:17:    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
backend\ledger\tests\test_ledger_api.py:20:    if hasattr(u, "school_id"):
backend\ledger\tests\test_ledger_api.py:21:        setattr(u, "school_id", school_id)
backend\ledger\tests\test_ledger_api.py:22:        u.save(update_fields=["school_id"])
backend\ledger\tests\test_ledger_api.py:30:    hh_a = Household.objects.create(school_id=school_a, name="A Household")
backend\ledger\tests\test_ledger_api.py:31:    Household.objects.create(school_id=school_b, name="B Household")
backend\ledger\tests\test_ledger_api.py:33:    user = _mk_user_with_school_id(school_a)
backend\ledger\tests\test_ledger_api.py:43:    assert LedgerAccount.objects.filter(household=hh_a, school_id=school_a).count() == 1
backend\ledger\tests\test_ledger_api.py:48:    hh_a = Household.objects.create(school_id=school_a, name="A Household")
backend\ledger\tests\test_ledger_api.py:49:    acct = LedgerAccount.objects.create(school_id=school_a, household=hh_a)
backend\ledger\tests\test_ledger_api.py:51:    user = _mk_user_with_school_id(school_a)
backend\payments\tests\test_saved_payment_methods.py:11:        household = Household.objects.create(school_id=school.id, name="Family")
backend\payments\tests\test_saved_payment_methods.py:14:            school_id=school.id,
backend\spiritual_life\tests\test_spiritual_life.py:125:        # User A sends school B's UUID ΓÇö non-staff, cross-tenant ΓåÆ 404
backend\spiritual_life\tests\test_spiritual_life.py:893:    def test_tenant_isolation_pastoral_notes(self):
backend\spiritual_life\tests\test_spiritual_life.py:905:        # Staff A (is_staff=True) can override tenant header ΓÇö so should only see school A's notes
backend\tests\test_shell_backend_seeded_contract.py:12:    def test_canonical_shell_contract_returns_success_under_seeded_tenant_context(self):
backend\ledger\tests\test_ledger_write_safety.py:33:    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
backend\ledger\tests\test_ledger_write_safety.py:34:    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
backend\ledger\tests\test_ledger_write_safety.py:120:        school_id=sid, account=acct, description="Fee", amount=Decimal("200.00")
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\payments\tests\test_payment_support_exception.py:12:            school_id=school.id,
backend\payments\tests\test_household_finance_access.py:22:    if hasattr(user, "school_id"):
backend\payments\tests\test_household_finance_access.py:23:        setattr(user, "school_id", school.id)
backend\payments\tests\test_household_finance_access.py:24:        user.save(update_fields=["school_id"])
backend\payments\tests\test_household_finance_access.py:35:    household = Household.objects.create(school_id=school.id, name="Family One")
backend\payments\tests\test_household_finance_access.py:58:    household = Household.objects.create(school_id=school.id, name="Family One")
backend\ledger\tests\test_ledger_void_endpoints_api.py:35:    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
backend\ledger\tests\test_ledger_void_endpoints_api.py:36:    acct = LedgerAccount.objects.create(school_id=sid, household=hh)
backend\ledger\tests\test_ledger_void_endpoints_api.py:50:        school_id=sid,
backend\ledger\tests\test_ledger_void_endpoints_api.py:59:        school_id=sid,
backend\ledger\tests\test_ledger_void_endpoints_api.py:114:    Allocation.objects.create(school_id=sid, payment=pay, charge=ch, amount=Decimal("200.00"))
backend\ledger\tests\test_ledger_void_endpoints_api.py:171:    Allocation.objects.create(school_id=sid, payment=pay, charge=ch, amount=Decimal("150.00"))
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\ledger\tests\test_ledger_allocations_api.py:20:    if hasattr(u, "school_id"):
backend\ledger\tests\test_ledger_allocations_api.py:21:        setattr(u, "school_id", school.id)
backend\ledger\tests\test_ledger_allocations_api.py:22:        u.save(update_fields=["school_id"])
backend\ledger\tests\test_ledger_allocations_api.py:28:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\ledger\tests\test_ledger_allocations_api.py:29:    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
backend\ledger\tests\test_ledger_allocations_api.py:32:    ch1 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition A", amount=Decimal("1000.00"))
backend\ledger\tests\test_ledger_allocations_api.py:33:    ch2 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition B", amount=Decimal("500.00"))
backend\ledger\tests\test_ledger_allocations_api.py:36:    pay = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("1200.00"))
backend\ledger\tests\test_ledger_payments_correctness_api.py:18:def _mk_user_with_school_id(school_id):
backend\ledger\tests\test_ledger_payments_correctness_api.py:19:    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
backend\ledger\tests\test_ledger_payments_correctness_api.py:22:    if hasattr(u, "school_id"):
backend\ledger\tests\test_ledger_payments_correctness_api.py:23:        setattr(u, "school_id", school_id)
backend\ledger\tests\test_ledger_payments_correctness_api.py:24:        u.save(update_fields=["school_id"])
backend\ledger\tests\test_ledger_payments_correctness_api.py:29:    school_id = uuid.uuid4()
backend\ledger\tests\test_ledger_payments_correctness_api.py:30:    School.objects.create(id=school_id, name="Test School")
backend\ledger\tests\test_ledger_payments_correctness_api.py:31:    hh = Household.objects.create(school_id=school_id, name="HH")
backend\ledger\tests\test_ledger_payments_correctness_api.py:32:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\ledger\tests\test_ledger_payments_correctness_api.py:34:    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))
backend\ledger\tests\test_ledger_payments_correctness_api.py:35:    ch2 = Charge.objects.create(school_id=school_id, account=acct, description="Fees", amount=Decimal("100.00"))
backend\ledger\tests\test_ledger_payments_correctness_api.py:37:    user = _mk_user_with_school_id(school_id)
backend\ledger\tests\test_ledger_payments_correctness_api.py:57:    assert Payment.objects.filter(school_id=school_id, account=acct).count() == 1
backend\ledger\tests\test_ledger_payments_correctness_api.py:58:    p = Payment.objects.get(school_id=school_id, account=acct)
backend\ledger\tests\test_ledger_payments_correctness_api.py:66:    school_id = uuid.uuid4()
backend\ledger\tests\test_ledger_payments_correctness_api.py:67:    School.objects.create(id=school_id, name="Test School")
backend\ledger\tests\test_ledger_payments_correctness_api.py:68:    hh = Household.objects.create(school_id=school_id, name="HH")
backend\ledger\tests\test_ledger_payments_correctness_api.py:69:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\ledger\tests\test_ledger_payments_correctness_api.py:70:    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))
backend\ledger\tests\test_ledger_payments_correctness_api.py:72:    user = _mk_user_with_school_id(school_id)
backend\ledger\tests\test_ledger_payments_correctness_api.py:87:    school_id = uuid.uuid4()
backend\ledger\tests\test_ledger_payments_correctness_api.py:88:    School.objects.create(id=school_id, name="Test School")
backend\ledger\tests\test_ledger_payments_correctness_api.py:89:    hh = Household.objects.create(school_id=school_id, name="HH")
backend\ledger\tests\test_ledger_payments_correctness_api.py:90:    acct = LedgerAccount.objects.create(school_id=school_id, household=hh)
backend\ledger\tests\test_ledger_payments_correctness_api.py:92:    ch1 = Charge.objects.create(school_id=school_id, account=acct, description="Tuition", amount=Decimal("150.00"))
backend\ledger\tests\test_ledger_payments_correctness_api.py:94:    user = _mk_user_with_school_id(school_id)
backend\tests\test_shared_frontend_shell_unit.py:42:    """Verify tenant/school scoping keywords appear in the Shared Frontend Shell source tree."""
backend\tests\test_shared_frontend_shell_unit.py:50:        "school_id" in source_text
backend\tests\test_shared_frontend_shell_unit.py:53:    ), f"Shared Frontend Shell: tenant/school scoping not found in source"
backend\payments\tests\test_dispute_models.py:24:        school_id=school.id,
backend\payments\tests\test_dispute_models.py:36:        school_id=school.id,
backend\payments\tests\test_dispute_models.py:68:        school_id=school.id,
backend\payments\tests\test_dispute_models.py:75:            school_id=school.id,
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\ledger\tests\test_ledger_statements_api.py:20:    if hasattr(u, "school_id"):
backend\ledger\tests\test_ledger_statements_api.py:21:        setattr(u, "school_id", school.id)
backend\ledger\tests\test_ledger_statements_api.py:22:        u.save(update_fields=["school_id"])
backend\ledger\tests\test_ledger_statements_api.py:28:    hh = Household.objects.create(school_id=school.id, name="Household")
backend\ledger\tests\test_ledger_statements_api.py:29:    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
backend\ledger\tests\test_ledger_statements_api.py:31:    ch1 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition", amount=Decimal("1000.00"))
backend\ledger\tests\test_ledger_statements_api.py:32:    ch2 = Charge.objects.create(school_id=school.id, account=acct, description="Fee", amount=Decimal("200.00"))
backend\ledger\tests\test_ledger_statements_api.py:35:    aid = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("400.00"), source="FINANCIAL_AID", reference="award:x")
backend\ledger\tests\test_ledger_statements_api.py:36:    PaymentAllocation.objects.create(school_id=school.id, payment=aid, charge=ch1, amount=Decimal("400.00"))
backend\ledger\tests\test_ledger_statements_api.py:39:    pay = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("300.00"), source="EXTERNAL", reference="rcpt:1")
backend\ledger\tests\test_ledger_statements_api.py:40:    PaymentAllocation.objects.create(school_id=school.id, payment=pay, charge=ch1, amount=Decimal("300.00"))
backend\ledger\tests\test_ledger_invariants.py:30:    """Return (school_id, user) for a fresh school. User is granted HEAD_OF_SCHOOL."""
backend\ledger\tests\test_ledger_invariants.py:35:    if hasattr(user, "school_id"):
backend\ledger\tests\test_ledger_invariants.py:36:        user.school_id = sid
backend\ledger\tests\test_ledger_invariants.py:37:        user.save(update_fields=["school_id"])
backend\ledger\tests\test_ledger_invariants.py:38:    UserRole.objects.create(school_id=sid, user=user, role_code="HEAD_OF_SCHOOL")
backend\ledger\tests\test_ledger_invariants.py:43:    hh = Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")
backend\ledger\tests\test_ledger_invariants.py:44:    return LedgerAccount.objects.create(school_id=sid, household=hh)
backend\ledger\tests\test_ledger_invariants.py:68:    charge = Charge.objects.create(school_id=sid, account=acct, description="Tuition", amount=Decimal("100.00"))
backend\ledger\tests\test_ledger_invariants.py:69:    payment = Payment.objects.create(school_id=sid, account=acct, amount=Decimal("100.00"))
backend\ledger\tests\test_ledger_invariants.py:70:    Allocation.objects.create(school_id=sid, payment=payment, charge=charge, amount=Decimal("100.00"))
backend\ledger\tests\test_ledger_invariants.py:83:    assert data["data"]["school_id"] == str(sid)
backend\ledger\tests\test_ledger_invariants.py:87:# Test 3: over-allocation is detected + tenant isolation
backend\ledger\tests\test_ledger_invariants.py:94:    charge = Charge.objects.create(school_id=sid, account=acct, description="Fee", amount=Decimal("100.00"))
backend\ledger\tests\test_ledger_invariants.py:95:    payment = Payment.objects.create(school_id=sid, account=acct, amount=Decimal("999.00"))
backend\ledger\tests\test_ledger_invariants.py:97:    Allocation.objects.create(school_id=sid, payment=payment, charge=charge, amount=Decimal("150.00"))
backend\ledger\tests\test_ledger_invariants.py:113:# Test 4: tenant isolation ├óΓé¼ΓÇ¥ other school's violations invisible
backend\ledger\tests\test_ledger_invariants.py:116:def test_invariants_tenant_isolation():
backend\ledger\tests\test_ledger_invariants.py:120:    school_b's user must see clean=True (no cross-tenant bleed).
backend\ledger\tests\test_ledger_invariants.py:127:    charge_a = Charge.objects.create(school_id=sid_a, account=acct_a, description="Bad charge", amount=Decimal("50.00"))
backend\ledger\tests\test_ledger_invariants.py:128:    pay_a = Payment.objects.create(school_id=sid_a, account=acct_a, amount=Decimal("999.00"))
backend\ledger\tests\test_ledger_invariants.py:129:    Allocation.objects.create(school_id=sid_a, payment=pay_a, charge=charge_a, amount=Decimal("200.00"))
backend\ledger\tests\test_ledger_invariants.py:133:    Charge.objects.create(school_id=sid_b, account=acct_b, description="Normal", amount=Decimal("300.00"))
backend\ledger\tests\test_ledger_invariants.py:141:    assert body["data"]["school_id"] == str(sid_b)
backend\ledger\tests\test_ledger_invariants.py:147:# Test 5: service rejects cross-tenant allocation (payment school_a, arg school_b)
backend\ledger\tests\test_ledger_invariants.py:150:def test_allocation_cross_tenant_guard():
backend\ledger\tests\test_ledger_invariants.py:151:    """allocate_payment_fifo raises ValueError when payment.school_id != school_id arg."""
backend\ledger\tests\test_ledger_invariants.py:156:        school_id=sid_a, account=acct_a, amount=Decimal("100.00")
backend\ledger\tests\test_ledger_invariants.py:159:    with pytest.raises(ValueError, match="school_id mismatch"):
backend\ledger\tests\test_ledger_invariants.py:160:        allocate_payment_fifo(school_id=sid_b, payment=payment_a)
backend\ledger\tests\test_ledger_invariants.py:173:        school_id=sid, account=acct, description="Void Fee", amount=Decimal("100.00")
backend\ledger\tests\test_ledger_invariants.py:180:        school_id=sid, account=acct, amount=Decimal("100.00")
backend\ledger\tests\test_ledger_invariants.py:183:    result = allocate_payment_fifo(school_id=sid, payment=payment)
backend\section_staffing_wizard\tests\test_views.py:35:def _h(school_id):
backend\section_staffing_wizard\tests\test_views.py:36:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\section_staffing_wizard\tests\test_views.py:110:    def test_cross_tenant_returns_404(self):
backend\tests\test_shared_frontend_shell_tenant.py:2:Tenant isolation tests for the Shared Frontend Shell module.
backend\tests\test_shared_frontend_shell_tenant.py:23:        username=f"tenant-a-shared_frontend_shell-{token}",
backend\tests\test_shared_frontend_shell_tenant.py:32:    """Cross-tenant isolation tests for Shared Frontend Shell."""
backend\tests\test_shared_frontend_shell_tenant.py:38:    def test_shared_frontend_shell_tenant_school_ids_are_distinct(self):
backend\tests\test_shared_frontend_shell_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_shared_frontend_shell_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_shared_frontend_shell_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_shared_frontend_shell_tenant.py:47:    def test_shared_frontend_shell_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_shared_frontend_shell_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_shared_frontend_shell_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_shared_frontend_shell_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_shared_frontend_shell_tenant.py:58:    def test_shared_frontend_shell_same_tenant_request_is_allowed(self):
backend\tests\test_shared_frontend_shell_tenant.py:67:    def test_shared_frontend_shell_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_shared_frontend_shell_tenant.py:75:    def test_shared_frontend_shell_isolation_keyword_present_in_source(self):
backend\tests\test_shared_frontend_shell_tenant.py:76:        """Tenant isolation keywords exist in the Shared Frontend Shell module source."""
backend\tests\test_shared_frontend_shell_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_shared_frontend_shell_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_shared_frontend_shell_tenant.py:87:        assert found, f"Shared Frontend Shell: tenant isolation keywords not found in source"
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\solomon\tests\test_adapters.py:85:        self.mock_request.school_id = None
backend\solomon\tests\test_adapters.py:207:        self.mock_request.school_id = None
backend\solomon\tests\test_adapters.py:297:        self.mock_request.school_id = None
backend\solomon\tests\test_adapters.py:369:        self.mock_request.school_id = None
backend\solomon\tests\test_adapters.py:426:        self.mock_request.school_id = None
backend\solomon\tests\test_adapters.py:453:        self.mock_request.school_id = None
backend\smoke_test_curriculum_demo.py:252:            log_pass(f"Scoping: School B sees 0 courses (correct isolation)")
backend\tests\test_shared_frontend_shell_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_shared_frontend_shell_negative.py:33:    """Negative tests for Shared Frontend Shell: unauthorized, invalid, forbidden paths."""
backend\tests\test_shared_frontend_shell_negative.py:40:    def test_shared_frontend_shell_unauthenticated_request_is_forbidden(self):
backend\tests\test_shared_frontend_shell_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\section_assign_wizard\tests\test_views.py:29:def _make_section(school_id, term="2026-FALL"):
backend\section_assign_wizard\tests\test_views.py:31:        school_id=school_id, code=f"CS{uuid.uuid4().hex[:4]}", name="Test Course"
backend\section_assign_wizard\tests\test_views.py:34:        school_id=school_id, course=course, term=term
backend\section_assign_wizard\tests\test_views.py:38:def _make_student(school_id):
backend\section_assign_wizard\tests\test_views.py:40:    household = Household.objects.create(school_id=school_id, name=f"HH {uuid.uuid4().hex[:6]}")
backend\section_assign_wizard\tests\test_views.py:42:        school_id=school_id,
backend\section_assign_wizard\tests\test_views.py:49:def _headers(school_id):
backend\section_assign_wizard\tests\test_views.py:50:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\section_assign_wizard\tests\test_views.py:64:def _advance_to_configured(client, school_id, section_id, term="2026-FALL"):
backend\section_assign_wizard\tests\test_views.py:65:    r = client.post(BASE_URL, **_headers(school_id))
backend\section_assign_wizard\tests\test_views.py:71:        **_headers(school_id),
backend\section_assign_wizard\tests\test_views.py:76:def _advance_to_students_loaded(client, school_id, section_id, student_ids=None):
backend\section_assign_wizard\tests\test_views.py:77:    session_id = _advance_to_configured(client, school_id, section_id)
backend\section_assign_wizard\tests\test_views.py:84:        **_headers(school_id),
backend\section_assign_wizard\tests\test_views.py:89:def _advance_to_roster_staged(client, school_id, section_id, student_ids=None):
backend\section_assign_wizard\tests\test_views.py:90:    session_id, student_ids = _advance_to_students_loaded(client, school_id, section_id, student_ids)
backend\section_assign_wizard\tests\test_views.py:96:        **_headers(school_id),
backend\section_assign_wizard\tests\test_views.py:402:            Enrollment.objects.create(section=self.section, student=s, school_id=self.school.id)
backend\tests\test_shared_frontend_shell_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_shared_frontend_shell_api.py:61:        """School record for Shared Frontend Shell tenant is created and queryable."""
backend\tests\test_shared_frontend_shell_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_shared_frontend_shell_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\signals\tests\test_tenant_scoping.py:12:    household = Household.objects.create(school_id=school.id, name=f"{school_name} Household")
backend\signals\tests\test_tenant_scoping.py:14:        school_id=school.id,
backend\signals\tests\test_tenant_scoping.py:22:def test_signal_event_scoped_by_school_id():
backend\signals\tests\test_tenant_scoping.py:27:        school_id=school_1.id,
backend\signals\tests\test_tenant_scoping.py:35:        school_id=school_2.id,
backend\signals\tests\test_tenant_scoping.py:43:    assert SignalEvent.objects.filter(school_id=school_1.id).count() == 1
backend\signals\tests\test_tenant_scoping.py:44:    assert SignalEvent.objects.filter(school_id=school_2.id).count() == 1
backend\signals\tests\test_tenant_scoping.py:51:        school_id=school.id,
backend\signals\tests\test_tenant_scoping.py:58:            school_id=school.id,
backend\signals\tests\test_tenant_scoping.py:70:        school_id=school_1.id,
backend\signals\tests\test_tenant_scoping.py:76:        school_id=school_2.id,
backend\signals\tests\test_tenant_scoping.py:82:    assert StudentRiskSnapshot.objects.filter(school_id=school_1.id, student=student_1).first().risk_level == "MED"
backend\signals\tests\test_tenant_scoping.py:83:    assert StudentRiskSnapshot.objects.filter(school_id=school_2.id, student=student_2).first().risk_level == "HIGH"
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_shared_design_system_unit.py:42:    """Verify tenant/school scoping keywords appear in the Shared Design System source tree."""
backend\tests\test_shared_design_system_unit.py:50:        "school_id" in source_text
backend\tests\test_shared_design_system_unit.py:53:    ), f"Shared Design System: tenant/school scoping not found in source"
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_shared_design_system_tenant.py:2:Tenant isolation tests for the Shared Design System module.
backend\tests\test_shared_design_system_tenant.py:23:        username=f"tenant-a-shared_design_system-{token}",
backend\tests\test_shared_design_system_tenant.py:32:    """Cross-tenant isolation tests for Shared Design System."""
backend\tests\test_shared_design_system_tenant.py:38:    def test_shared_design_system_tenant_school_ids_are_distinct(self):
backend\tests\test_shared_design_system_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_shared_design_system_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_shared_design_system_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_shared_design_system_tenant.py:47:    def test_shared_design_system_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_shared_design_system_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_shared_design_system_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_shared_design_system_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_shared_design_system_tenant.py:58:    def test_shared_design_system_same_tenant_request_is_allowed(self):
backend\tests\test_shared_design_system_tenant.py:67:    def test_shared_design_system_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_shared_design_system_tenant.py:75:    def test_shared_design_system_isolation_keyword_present_in_source(self):
backend\tests\test_shared_design_system_tenant.py:76:        """Tenant isolation keywords exist in the Shared Design System module source."""
backend\tests\test_shared_design_system_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_shared_design_system_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_shared_design_system_tenant.py:87:        assert found, f"Shared Design System: tenant isolation keywords not found in source"
backend\tests\test_shared_design_system_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_shared_design_system_negative.py:33:    """Negative tests for Shared Design System: unauthorized, invalid, forbidden paths."""
backend\tests\test_shared_design_system_negative.py:40:    def test_shared_design_system_unauthenticated_request_is_forbidden(self):
backend\tests\test_shared_design_system_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_shared_design_system_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_shared_design_system_api.py:61:        """School record for Shared Design System tenant is created and queryable."""
backend\tests\test_shared_design_system_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_shared_design_system_api.py:67:        assert self.user.school_id == self.school.id
backend\term_structure_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\term_structure_wizard\tests\test_views.py:67:def _headers(school_id):
backend\term_structure_wizard\tests\test_views.py:68:    return {"HTTP_X_SCHOOL_ID": str(school_id)}
backend\term_structure_wizard\tests\test_views.py:87:def _create_session(client, school_id):
backend\term_structure_wizard\tests\test_views.py:88:    r = client.post(BASE_URL, **_headers(school_id))
backend\term_structure_wizard\tests\test_views.py:93:def _configure_session(client, school_id, session_id, ay_id, structure_type="SEMESTER"):
backend\term_structure_wizard\tests\test_views.py:98:        **_headers(school_id),
backend\term_structure_wizard\tests\test_views.py:104:def _set_periods(client, school_id, session_id, periods=None):
backend\term_structure_wizard\tests\test_views.py:109:        **_headers(school_id),
backend\term_structure_wizard\tests\test_views.py:115:def _advance_to_configured(client, school_id, ay=None):
backend\term_structure_wizard\tests\test_views.py:118:        school = School.objects.get(pk=school_id)
backend\term_structure_wizard\tests\test_views.py:120:    sess = _create_session(client, school_id)
backend\term_structure_wizard\tests\test_views.py:121:    _configure_session(client, school_id, sess["session_id"], ay.id)
backend\term_structure_wizard\tests\test_views.py:125:def _advance_to_periods_set(client, school_id, ay=None, periods=None):
backend\term_structure_wizard\tests\test_views.py:127:    sid, ay = _advance_to_configured(client, school_id, ay)
backend\term_structure_wizard\tests\test_views.py:128:    _set_periods(client, school_id, sid, periods=periods)
backend\term_structure_wizard\tests\test_views.py:152:# 2. Tenant isolation
backend\term_structure_wizard\tests\test_views.py:167:        # Use wrong school_id for configure
backend\term_structure_wizard\tests\test_views.py:173:            **_headers(other_school.id),   # school_id matches session's school? No ΓÇö session is under self.school
backend\term_structure_wizard\tests\test_views.py:503:    def test_cross_tenant_isolation(self):
backend\tests\test_service_outreach_unit.py:42:    """Verify tenant/school scoping keywords appear in the Service Outreach source tree."""
backend\tests\test_service_outreach_unit.py:50:        "school_id" in source_text
backend\tests\test_service_outreach_unit.py:53:    ), f"Service Outreach: tenant/school scoping not found in source"
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tenants\test_smoke.py:6:        from tenants.apps import TenantsConfig
backend\tenants\test_smoke.py:8:        self.assertEqual(TenantsConfig.name, "tenants")
backend\tenants\test_smoke.py:10:    def test_tenant_context_importable(self):
backend\tenants\test_smoke.py:11:        from tenants import tenant_context
backend\tenants\test_smoke.py:13:        self.assertIsNotNone(tenant_context)
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_service_outreach_tenant.py:2:Tenant isolation tests for the Service Outreach module.
backend\tests\test_service_outreach_tenant.py:23:        username=f"tenant-a-service_outreach-{token}",
backend\tests\test_service_outreach_tenant.py:32:    """Cross-tenant isolation tests for Service Outreach."""
backend\tests\test_service_outreach_tenant.py:38:    def test_service_outreach_tenant_school_ids_are_distinct(self):
backend\tests\test_service_outreach_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_service_outreach_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_service_outreach_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_service_outreach_tenant.py:47:    def test_service_outreach_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_service_outreach_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_service_outreach_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_service_outreach_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_service_outreach_tenant.py:58:    def test_service_outreach_same_tenant_request_is_allowed(self):
backend\tests\test_service_outreach_tenant.py:67:    def test_service_outreach_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_service_outreach_tenant.py:75:    def test_service_outreach_isolation_keyword_present_in_source(self):
backend\tests\test_service_outreach_tenant.py:76:        """Tenant isolation keywords exist in the Service Outreach module source."""
backend\tests\test_service_outreach_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_service_outreach_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_service_outreach_tenant.py:87:        assert found, f"Service Outreach: tenant isolation keywords not found in source"
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:21:CHECK_44 = 'unauthorized invalid forbidden 403 raises negative tests'
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:46:# check44: unauthorized invalid forbidden 403 raises negative tests
backend\tests\test_service_outreach_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_service_outreach_negative.py:33:    """Negative tests for Service Outreach: unauthorized, invalid, forbidden paths."""
backend\tests\test_service_outreach_negative.py:40:    def test_service_outreach_unauthenticated_request_is_forbidden(self):
backend\tests\test_service_outreach_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_chaplain_pastoral_care_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_chaplain_pastoral_care_negative.py:33:    """Negative tests for Chaplain Pastoral Care: unauthorized, invalid, forbidden paths."""
backend\tests\test_chaplain_pastoral_care_negative.py:40:    def test_chaplain_pastoral_care_unauthenticated_request_is_forbidden(self):
backend\tests\test_chaplain_pastoral_care_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_extended_discipline_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_extended_discipline_api.py:61:        """School record for Extended Discipline Workflows tenant is created and queryable."""
backend\tests\test_extended_discipline_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_extended_discipline_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_crown_compass_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_crown_compass_negative.py:33:    """Negative tests for Crown Compass: unauthorized, invalid, forbidden paths."""
backend\tests\test_crown_compass_negative.py:40:    def test_crown_compass_unauthenticated_request_is_forbidden(self):
backend\tests\test_crown_compass_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:45:# tenant
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:46:# cross-tenant
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:48:# isolation
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:70:# unauthorized
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:72:# forbidden
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:45:# tenant
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:46:# cross-tenant
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:48:# isolation
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:70:# unauthorized
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:72:# forbidden
backend\tests\test_audit_logging_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_audit_logging_negative.py:33:    """Negative tests for Audit Logging: unauthorized, invalid, forbidden paths."""
backend\tests\test_audit_logging_negative.py:40:    def test_audit_logging_unauthenticated_request_is_forbidden(self):
backend\tests\test_audit_logging_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_51x51_evidence_40_service___outreach.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_40_service___outreach.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_40_service___outreach.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_40_service___outreach.py:45:# tenant
backend\tests\test_51x51_evidence_40_service___outreach.py:46:# cross-tenant
backend\tests\test_51x51_evidence_40_service___outreach.py:48:# isolation
backend\tests\test_51x51_evidence_40_service___outreach.py:70:# unauthorized
backend\tests\test_51x51_evidence_40_service___outreach.py:72:# forbidden
backend\tests\test_service_outreach_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_service_outreach_api.py:61:        """School record for Service Outreach tenant is created and queryable."""
backend\tests\test_service_outreach_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_service_outreach_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_chaplain_pastoral_care_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_chaplain_pastoral_care_api.py:61:        """School record for Chaplain Pastoral Care tenant is created and queryable."""
backend\tests\test_chaplain_pastoral_care_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_chaplain_pastoral_care_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_ensure_ci_user_api.py:23:    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
backend\tests\test_ensure_ci_user_api.py:26:    School.objects.filter(pk=test_school_id).delete()
backend\tests\test_ensure_ci_user_api.py:35:            'CI_SMOKE_SCHOOL_ID': str(test_school_id),
backend\tests\test_ensure_ci_user_api.py:49:    school = School.objects.get(pk=test_school_id)
backend\tests\test_ensure_ci_user_api.py:62:    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
backend\tests\test_ensure_ci_user_api.py:65:    School.objects.filter(pk=test_school_id).delete()
backend\tests\test_ensure_ci_user_api.py:67:        id=test_school_id,
backend\tests\test_ensure_ci_user_api.py:79:            'CI_SMOKE_SCHOOL_ID': str(test_school_id),
backend\tests\test_ensure_ci_user_api.py:100:    assert School.objects.filter(pk=test_school_id).count() == 1
backend\tests\test_crown_compass_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_crown_compass_api.py:61:        """School record for Crown Compass tenant is created and queryable."""
backend\tests\test_crown_compass_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_crown_compass_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_audit_logging_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_audit_logging_api.py:61:        """School record for Audit Logging tenant is created and queryable."""
backend\tests\test_audit_logging_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_audit_logging_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:45:# tenant
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:46:# cross-tenant
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:48:# isolation
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:70:# unauthorized
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:72:# forbidden
backend\tests\test_emergency_medical_unit.py:42:    """Verify tenant/school scoping keywords appear in the Emergency Medical Essentials source tree."""
backend\tests\test_emergency_medical_unit.py:50:        "school_id" in source_text
backend\tests\test_emergency_medical_unit.py:53:    ), f"Emergency Medical Essentials: tenant/school scoping not found in source"
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:45:# tenant
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:46:# cross-tenant
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:48:# isolation
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:70:# unauthorized
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:72:# forbidden
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:45:# tenant
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:46:# cross-tenant
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:48:# isolation
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:70:# unauthorized
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:72:# forbidden
backend\tests\test_board_governance_suite_unit.py:42:    """Verify tenant/school scoping keywords appear in the Board Governance Suite source tree."""
backend\tests\test_board_governance_suite_unit.py:50:        "school_id" in source_text
backend\tests\test_board_governance_suite_unit.py:53:    ), f"Board Governance Suite: tenant/school scoping not found in source"
backend\tests\test_crm_marketing_unit.py:42:    """Verify tenant/school scoping keywords appear in the CRM Marketing Suite source tree."""
backend\tests\test_crm_marketing_unit.py:50:        "school_id" in source_text
backend\tests\test_crm_marketing_unit.py:53:    ), f"CRM Marketing Suite: tenant/school scoping not found in source"
backend\tests\test_seed_category_weights_command.py:38:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:45:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:51:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:62:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:68:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:79:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:115:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:121:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:130:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:138:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:156:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:166:        category_count = AssignmentCategory.objects.filter(school_id=self.school.id).count()
backend\tests\test_seed_category_weights_command.py:178:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:184:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:194:        category_count = AssignmentCategory.objects.filter(school_id=self.school.id).count()
backend\tests\test_seed_category_weights_command.py:208:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:214:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:222:            school_id=self.school.id,
backend\tests\test_seed_category_weights_command.py:230:        self.assertEqual(AssignmentCategory.objects.filter(school_id=self.school.id).count(), 1)
backend\tests\test_seed_category_weights_command.py:237:        categories = AssignmentCategory.objects.filter(school_id=self.school.id)
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:45:# tenant
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:46:# cross-tenant
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:48:# isolation
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:70:# unauthorized
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:72:# forbidden
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:45:# tenant
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:46:# cross-tenant
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:48:# isolation
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:70:# unauthorized
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:72:# forbidden
backend\tests\test_51x51_evidence_29_teacher_portal.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_29_teacher_portal.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_29_teacher_portal.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_29_teacher_portal.py:45:# tenant
backend\tests\test_51x51_evidence_29_teacher_portal.py:46:# cross-tenant
backend\tests\test_51x51_evidence_29_teacher_portal.py:48:# isolation
backend\tests\test_51x51_evidence_29_teacher_portal.py:70:# unauthorized
backend\tests\test_51x51_evidence_29_teacher_portal.py:72:# forbidden
backend\tests\test_emergency_medical_tenant.py:2:Tenant isolation tests for the Emergency Medical Essentials module.
backend\tests\test_emergency_medical_tenant.py:23:        username=f"tenant-a-emergency_medical-{token}",
backend\tests\test_emergency_medical_tenant.py:32:    """Cross-tenant isolation tests for Emergency Medical Essentials."""
backend\tests\test_emergency_medical_tenant.py:38:    def test_emergency_medical_tenant_school_ids_are_distinct(self):
backend\tests\test_emergency_medical_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_emergency_medical_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_emergency_medical_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_emergency_medical_tenant.py:47:    def test_emergency_medical_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_emergency_medical_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_emergency_medical_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_emergency_medical_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_emergency_medical_tenant.py:58:    def test_emergency_medical_same_tenant_request_is_allowed(self):
backend\tests\test_emergency_medical_tenant.py:67:    def test_emergency_medical_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_emergency_medical_tenant.py:75:    def test_emergency_medical_isolation_keyword_present_in_source(self):
backend\tests\test_emergency_medical_tenant.py:76:        """Tenant isolation keywords exist in the Emergency Medical Essentials module source."""
backend\tests\test_emergency_medical_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_emergency_medical_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_emergency_medical_tenant.py:87:        assert found, f"Emergency Medical Essentials: tenant isolation keywords not found in source"
backend\tests\test_51x51_evidence_42_board_governance_suite.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_42_board_governance_suite.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_42_board_governance_suite.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_42_board_governance_suite.py:45:# tenant
backend\tests\test_51x51_evidence_42_board_governance_suite.py:46:# cross-tenant
backend\tests\test_51x51_evidence_42_board_governance_suite.py:48:# isolation
backend\tests\test_51x51_evidence_42_board_governance_suite.py:70:# unauthorized
backend\tests\test_51x51_evidence_42_board_governance_suite.py:72:# forbidden
backend\tests\test_board_governance_suite_tenant.py:2:Tenant isolation tests for the Board Governance Suite module.
backend\tests\test_board_governance_suite_tenant.py:23:        username=f"tenant-a-board_governance_suite-{token}",
backend\tests\test_board_governance_suite_tenant.py:32:    """Cross-tenant isolation tests for Board Governance Suite."""
backend\tests\test_board_governance_suite_tenant.py:38:    def test_board_governance_suite_tenant_school_ids_are_distinct(self):
backend\tests\test_board_governance_suite_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_board_governance_suite_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_board_governance_suite_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_board_governance_suite_tenant.py:47:    def test_board_governance_suite_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_board_governance_suite_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_board_governance_suite_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_board_governance_suite_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_board_governance_suite_tenant.py:58:    def test_board_governance_suite_same_tenant_request_is_allowed(self):
backend\tests\test_board_governance_suite_tenant.py:67:    def test_board_governance_suite_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_board_governance_suite_tenant.py:75:    def test_board_governance_suite_isolation_keyword_present_in_source(self):
backend\tests\test_board_governance_suite_tenant.py:76:        """Tenant isolation keywords exist in the Board Governance Suite module source."""
backend\tests\test_board_governance_suite_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_board_governance_suite_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_board_governance_suite_tenant.py:87:        assert found, f"Board Governance Suite: tenant isolation keywords not found in source"
backend\tests\test_crm_marketing_tenant.py:2:Tenant isolation tests for the CRM Marketing Suite module.
backend\tests\test_crm_marketing_tenant.py:23:        username=f"tenant-a-crm_marketing-{token}",
backend\tests\test_crm_marketing_tenant.py:32:    """Cross-tenant isolation tests for CRM Marketing Suite."""
backend\tests\test_crm_marketing_tenant.py:38:    def test_crm_marketing_tenant_school_ids_are_distinct(self):
backend\tests\test_crm_marketing_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_crm_marketing_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_crm_marketing_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_crm_marketing_tenant.py:47:    def test_crm_marketing_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_crm_marketing_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_crm_marketing_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_crm_marketing_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_crm_marketing_tenant.py:58:    def test_crm_marketing_same_tenant_request_is_allowed(self):
backend\tests\test_crm_marketing_tenant.py:67:    def test_crm_marketing_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_crm_marketing_tenant.py:75:    def test_crm_marketing_isolation_keyword_present_in_source(self):
backend\tests\test_crm_marketing_tenant.py:76:        """Tenant isolation keywords exist in the CRM Marketing Suite module source."""
backend\tests\test_crm_marketing_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_crm_marketing_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_crm_marketing_tenant.py:87:        assert found, f"CRM Marketing Suite: tenant isolation keywords not found in source"
backend\tests\test_seed_academics_demo_command.py:24:    def school_id(self):
backend\tests\test_seed_academics_demo_command.py:35:    def test_creates_academics_data(self, school_id):
backend\tests\test_seed_academics_demo_command.py:38:        assert Course.objects.filter(school_id=school_id).count() == 0
backend\tests\test_seed_academics_demo_command.py:39:        assert Section.objects.filter(school_id=school_id).count() == 0
backend\tests\test_seed_academics_demo_command.py:40:        assert Enrollment.objects.filter(school_id=school_id).count() == 0
backend\tests\test_seed_academics_demo_command.py:44:        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)
backend\tests\test_seed_academics_demo_command.py:47:        courses = Course.objects.filter(school_id=school_id)
backend\tests\test_seed_academics_demo_command.py:48:        sections = Section.objects.filter(school_id=school_id)
backend\tests\test_seed_academics_demo_command.py:49:        enrollments = Enrollment.objects.filter(school_id=school_id)
backend\tests\test_seed_academics_demo_command.py:65:    def test_idempotent_double_run(self, school_id):
backend\tests\test_seed_academics_demo_command.py:69:        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)
backend\tests\test_seed_academics_demo_command.py:72:        courses_count_1 = Course.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:73:        sections_count_1 = Section.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:74:        enrollments_count_1 = Enrollment.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:82:        call_command("seed_academics_demo", school_id=str(school_id), stdout=out2)
backend\tests\test_seed_academics_demo_command.py:85:        courses_count_2 = Course.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:86:        sections_count_2 = Section.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:87:        enrollments_count_2 = Enrollment.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:93:    def test_wipe_and_reseed(self, school_id):
backend\tests\test_seed_academics_demo_command.py:97:        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)
backend\tests\test_seed_academics_demo_command.py:99:        courses_count_1 = Course.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:104:        call_command("seed_academics_demo", school_id=str(school_id), wipe=True, stdout=out2)
backend\tests\test_seed_academics_demo_command.py:107:        courses_count_2 = Course.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:108:        sections_count_2 = Section.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:109:        enrollments_count_2 = Enrollment.objects.filter(school_id=school_id).count()
backend\tests\test_seed_academics_demo_command.py:115:    def test_invalid_school_id_fails_gracefully(self):
backend\tests\test_seed_academics_demo_command.py:121:        call_command("seed_academics_demo", school_id="not-a-uuid", stdout=out, stderr=err)
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:45:# tenant
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:46:# cross-tenant
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:48:# isolation
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:70:# unauthorized
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:72:# forbidden
backend\tests\test_51x51_evidence_35_food_services.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_35_food_services.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_35_food_services.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_35_food_services.py:45:# tenant
backend\tests\test_51x51_evidence_35_food_services.py:46:# cross-tenant
backend\tests\test_51x51_evidence_35_food_services.py:48:# isolation
backend\tests\test_51x51_evidence_35_food_services.py:70:# unauthorized
backend\tests\test_51x51_evidence_35_food_services.py:72:# forbidden
backend\tests\test_51x51_evidence_28_parent_portal.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_28_parent_portal.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_28_parent_portal.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_28_parent_portal.py:45:# tenant
backend\tests\test_51x51_evidence_28_parent_portal.py:46:# cross-tenant
backend\tests\test_51x51_evidence_28_parent_portal.py:48:# isolation
backend\tests\test_51x51_evidence_28_parent_portal.py:70:# unauthorized
backend\tests\test_51x51_evidence_28_parent_portal.py:72:# forbidden
backend\tests\test_emergency_medical_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_emergency_medical_negative.py:33:    """Negative tests for Emergency Medical Essentials: unauthorized, invalid, forbidden paths."""
backend\tests\test_emergency_medical_negative.py:40:    def test_emergency_medical_unauthenticated_request_is_forbidden(self):
backend\tests\test_emergency_medical_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_51x51_evidence_41_crown_compass.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_41_crown_compass.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_41_crown_compass.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_41_crown_compass.py:45:# tenant
backend\tests\test_51x51_evidence_41_crown_compass.py:46:# cross-tenant
backend\tests\test_51x51_evidence_41_crown_compass.py:48:# isolation
backend\tests\test_51x51_evidence_41_crown_compass.py:70:# unauthorized
backend\tests\test_51x51_evidence_41_crown_compass.py:72:# forbidden
backend\tests\test_board_governance_suite_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_board_governance_suite_negative.py:33:    """Negative tests for Board Governance Suite: unauthorized, invalid, forbidden paths."""
backend\tests\test_board_governance_suite_negative.py:40:    def test_board_governance_suite_unauthenticated_request_is_forbidden(self):
backend\tests\test_board_governance_suite_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_crm_marketing_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_crm_marketing_negative.py:33:    """Negative tests for CRM Marketing Suite: unauthorized, invalid, forbidden paths."""
backend\tests\test_crm_marketing_negative.py:40:    def test_crm_marketing_unauthenticated_request_is_forbidden(self):
backend\tests\test_crm_marketing_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_school_year_term_unit.py:42:    """Verify tenant/school scoping keywords appear in the School Year Term source tree."""
backend\tests\test_school_year_term_unit.py:50:        "school_id" in source_text
backend\tests\test_school_year_term_unit.py:53:    ), f"School Year Term: tenant/school scoping not found in source"
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:13:MODULE_TEXT = 'Mobile App / Family App\nProvides mobile access to family, student, teacher, alerts, calendar, and school-life workflows.\nMobile login | Push alerts | Family view | Calendar | Messages\nAuthenticate mobile user | Send push | Show scoped records | Support tasks | Respect permissions\nmobile active users | push delivery | crash rate | task completion | mobile login success\nauth | parent portal | communications | calendar | notifications\nProduct + Dev 4\nLater Add-on'
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:38:# Authenticate mobile user | Send push | Show scoped records | Support tasks | Respect permissions
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:45:# tenant
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:46:# cross-tenant
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:48:# isolation
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:70:# unauthorized
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:72:# forbidden
backend\tests\test_51x51_evidence_27_communications.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_27_communications.py:13:MODULE_TEXT = 'Communications\nManages announcements, messages, alerts, templates, and role-targeted communication.\nAnnouncements | Messaging | Templates | Targeting | Delivery\nCreate message | Target audience | Deliver notification | Track read status | Respect permissions\ndelivery success | unread count | message response time | failed sends | announcement reach\nnotifications | RBAC | households | staff | portals\nDev 3\nFirst-Wave Module'
backend\tests\test_51x51_evidence_27_communications.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_27_communications.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_27_communications.py:38:# Create message | Target audience | Deliver notification | Track read status | Respect permissions
backend\tests\test_51x51_evidence_27_communications.py:45:# tenant
backend\tests\test_51x51_evidence_27_communications.py:46:# cross-tenant
backend\tests\test_51x51_evidence_27_communications.py:48:# isolation
backend\tests\test_51x51_evidence_27_communications.py:70:# unauthorized
backend\tests\test_51x51_evidence_27_communications.py:72:# forbidden
backend\tests\test_emergency_medical_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_emergency_medical_api.py:61:        """School record for Emergency Medical Essentials tenant is created and queryable."""
backend\tests\test_emergency_medical_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_emergency_medical_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_51x51_evidence_46_mission_metrics.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_46_mission_metrics.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_46_mission_metrics.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_46_mission_metrics.py:45:# tenant
backend\tests\test_51x51_evidence_46_mission_metrics.py:46:# cross-tenant
backend\tests\test_51x51_evidence_46_mission_metrics.py:48:# isolation
backend\tests\test_51x51_evidence_46_mission_metrics.py:70:# unauthorized
backend\tests\test_51x51_evidence_46_mission_metrics.py:72:# forbidden
backend\tests\test_crm_marketing_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_crm_marketing_api.py:61:        """School record for CRM Marketing Suite tenant is created and queryable."""
backend\tests\test_crm_marketing_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_crm_marketing_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:45:# tenant
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:46:# cross-tenant
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:48:# isolation
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:70:# unauthorized
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:72:# forbidden
backend\tests\test_board_governance_suite_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_board_governance_suite_api.py:61:        """School record for Board Governance Suite tenant is created and queryable."""
backend\tests\test_board_governance_suite_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_board_governance_suite_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_school_year_term_tenant.py:2:Tenant isolation tests for the School Year Term module.
backend\tests\test_school_year_term_tenant.py:23:        username=f"tenant-a-school_year_term-{token}",
backend\tests\test_school_year_term_tenant.py:32:    """Cross-tenant isolation tests for School Year Term."""
backend\tests\test_school_year_term_tenant.py:38:    def test_school_year_term_tenant_school_ids_are_distinct(self):
backend\tests\test_school_year_term_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_school_year_term_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_school_year_term_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_school_year_term_tenant.py:47:    def test_school_year_term_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_school_year_term_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_school_year_term_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_school_year_term_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_school_year_term_tenant.py:58:    def test_school_year_term_same_tenant_request_is_allowed(self):
backend\tests\test_school_year_term_tenant.py:67:    def test_school_year_term_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_school_year_term_tenant.py:75:    def test_school_year_term_isolation_keyword_present_in_source(self):
backend\tests\test_school_year_term_tenant.py:76:        """Tenant isolation keywords exist in the School Year Term module source."""
backend\tests\test_school_year_term_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_school_year_term_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_school_year_term_tenant.py:87:        assert found, f"School Year Term: tenant isolation keywords not found in source"
backend\tests\test_document_file_framework_unit.py:42:    """Verify tenant/school scoping keywords appear in the Document File Framework source tree."""
backend\tests\test_document_file_framework_unit.py:50:        "school_id" in source_text
backend\tests\test_document_file_framework_unit.py:53:    ), f"Document File Framework: tenant/school scoping not found in source"
backend\tests\test_audit_logging_tenant.py:2:Tenant isolation tests for the Audit Logging module.
backend\tests\test_audit_logging_tenant.py:23:        username=f"tenant-a-audit_logging-{token}",
backend\tests\test_audit_logging_tenant.py:32:    """Cross-tenant isolation tests for Audit Logging."""
backend\tests\test_audit_logging_tenant.py:38:    def test_audit_logging_tenant_school_ids_are_distinct(self):
backend\tests\test_audit_logging_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_audit_logging_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_audit_logging_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_audit_logging_tenant.py:47:    def test_audit_logging_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_audit_logging_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_audit_logging_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_audit_logging_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_audit_logging_tenant.py:58:    def test_audit_logging_same_tenant_request_is_allowed(self):
backend\tests\test_audit_logging_tenant.py:67:    def test_audit_logging_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_audit_logging_tenant.py:75:    def test_audit_logging_isolation_keyword_present_in_source(self):
backend\tests\test_audit_logging_tenant.py:76:        """Tenant isolation keywords exist in the Audit Logging module source."""
backend\tests\test_audit_logging_tenant.py:85:        assert "school_id" in audit_helper_text
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:45:# tenant
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:46:# cross-tenant
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:48:# isolation
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:70:# unauthorized
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:72:# forbidden
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:13:MODULE_TEXT = 'Emergency / Medical Essentials\nStores emergency contacts, key medical flags, allergies, and operational health essentials.\nEmergency contact | Medical flag | Allergy | Medication note | Emergency access\nStore emergency info | Restrict medical data | Expose to authorized roles | Update contacts | Audit access\nmissing emergency contacts | medical alert accuracy | unauthorized health access | contact update rate | emergency data completeness\nstudents | households | nurse | RBAC | audit\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:39:# missing emergency contacts | medical alert accuracy | unauthorized health access | contact update rate | emergency data completeness
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:45:# tenant
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:46:# cross-tenant
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:48:# isolation
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:70:# unauthorized
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:72:# forbidden
backend\tests\test_communications_unit.py:42:    """Verify tenant/school scoping keywords appear in the Communications source tree."""
backend\tests\test_communications_unit.py:50:        "school_id" in source_text
backend\tests\test_communications_unit.py:53:    ), f"Communications: tenant/school scoping not found in source"
backend\tests\test_audit_logging_unit.py:42:    """Verify tenant/school scoping keywords appear in the Audit Logging source tree."""
backend\tests\test_audit_logging_unit.py:50:        "school_id" in source_text
backend\tests\test_audit_logging_unit.py:53:    ), f"Audit Logging: tenant/school scoping not found in source"
backend\tests\test_school_year_term_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_school_year_term_negative.py:33:    """Negative tests for School Year Term: unauthorized, invalid, forbidden paths."""
backend\tests\test_school_year_term_negative.py:40:    def test_school_year_term_unauthenticated_request_is_forbidden(self):
backend\tests\test_school_year_term_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_christian_pd_hub_tenant.py:2:Tenant isolation tests for the Christian PD Hub module.
backend\tests\test_christian_pd_hub_tenant.py:23:        username=f"tenant-a-christian_pd_hub-{token}",
backend\tests\test_christian_pd_hub_tenant.py:32:    """Cross-tenant isolation tests for Christian PD Hub."""
backend\tests\test_christian_pd_hub_tenant.py:38:    def test_christian_pd_hub_tenant_school_ids_are_distinct(self):
backend\tests\test_christian_pd_hub_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_christian_pd_hub_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_christian_pd_hub_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_christian_pd_hub_tenant.py:47:    def test_christian_pd_hub_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_christian_pd_hub_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_christian_pd_hub_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_christian_pd_hub_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_christian_pd_hub_tenant.py:58:    def test_christian_pd_hub_same_tenant_request_is_allowed(self):
backend\tests\test_christian_pd_hub_tenant.py:67:    def test_christian_pd_hub_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_christian_pd_hub_tenant.py:75:    def test_christian_pd_hub_isolation_keyword_present_in_source(self):
backend\tests\test_christian_pd_hub_tenant.py:76:        """Tenant isolation keywords exist in the Christian PD Hub module source."""
backend\tests\test_christian_pd_hub_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_christian_pd_hub_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_christian_pd_hub_tenant.py:87:        assert found, f"Christian PD Hub: tenant isolation keywords not found in source"
backend\tests\test_document_file_framework_tenant.py:2:Tenant isolation tests for the Document File Framework module.
backend\tests\test_document_file_framework_tenant.py:23:        username=f"tenant-a-document_file_framework-{token}",
backend\tests\test_document_file_framework_tenant.py:32:    """Cross-tenant isolation tests for Document File Framework."""
backend\tests\test_document_file_framework_tenant.py:38:    def test_document_file_framework_tenant_school_ids_are_distinct(self):
backend\tests\test_document_file_framework_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_document_file_framework_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_document_file_framework_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_document_file_framework_tenant.py:47:    def test_document_file_framework_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_document_file_framework_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_document_file_framework_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_document_file_framework_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_document_file_framework_tenant.py:58:    def test_document_file_framework_same_tenant_request_is_allowed(self):
backend\tests\test_document_file_framework_tenant.py:67:    def test_document_file_framework_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_document_file_framework_tenant.py:75:    def test_document_file_framework_isolation_keyword_present_in_source(self):
backend\tests\test_document_file_framework_tenant.py:76:        """Tenant isolation keywords exist in the Document File Framework module source."""
backend\tests\test_document_file_framework_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_document_file_framework_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_document_file_framework_tenant.py:87:        assert found, f"Document File Framework: tenant isolation keywords not found in source"
backend\tests\test_chaplain_pastoral_care_unit.py:42:    """Verify tenant/school scoping keywords appear in the Chaplain Pastoral Care source tree."""
backend\tests\test_chaplain_pastoral_care_unit.py:50:        "school_id" in source_text
backend\tests\test_chaplain_pastoral_care_unit.py:53:    ), f"Chaplain Pastoral Care: tenant/school scoping not found in source"
backend\tests\test_chaplain_pastoral_care_tenant.py:2:Tenant isolation tests for the Chaplain Pastoral Care module.
backend\tests\test_chaplain_pastoral_care_tenant.py:23:        username=f"tenant-a-chaplain_pastoral_care-{token}",
backend\tests\test_chaplain_pastoral_care_tenant.py:32:    """Cross-tenant isolation tests for Chaplain Pastoral Care."""
backend\tests\test_chaplain_pastoral_care_tenant.py:38:    def test_chaplain_pastoral_care_tenant_school_ids_are_distinct(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_chaplain_pastoral_care_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_chaplain_pastoral_care_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_chaplain_pastoral_care_tenant.py:47:    def test_chaplain_pastoral_care_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_chaplain_pastoral_care_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_chaplain_pastoral_care_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_chaplain_pastoral_care_tenant.py:58:    def test_chaplain_pastoral_care_same_tenant_request_is_allowed(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:67:    def test_chaplain_pastoral_care_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:75:    def test_chaplain_pastoral_care_isolation_keyword_present_in_source(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:76:        """Tenant isolation keywords exist in the Chaplain Pastoral Care module source."""
backend\tests\test_chaplain_pastoral_care_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_chaplain_pastoral_care_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_chaplain_pastoral_care_tenant.py:87:        assert found, f"Chaplain Pastoral Care: tenant isolation keywords not found in source"
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:45:# tenant
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:46:# cross-tenant
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:48:# isolation
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:70:# unauthorized
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:72:# forbidden
backend\tests\test_communications_tenant.py:2:Tenant isolation tests for the Communications module.
backend\tests\test_communications_tenant.py:23:        username=f"tenant-a-communications-{token}",
backend\tests\test_communications_tenant.py:32:    """Cross-tenant isolation tests for Communications."""
backend\tests\test_communications_tenant.py:38:    def test_communications_tenant_school_ids_are_distinct(self):
backend\tests\test_communications_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_communications_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_communications_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_communications_tenant.py:47:    def test_communications_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_communications_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_communications_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_communications_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_communications_tenant.py:58:    def test_communications_same_tenant_request_is_allowed(self):
backend\tests\test_communications_tenant.py:67:    def test_communications_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_communications_tenant.py:75:    def test_communications_isolation_keyword_present_in_source(self):
backend\tests\test_communications_tenant.py:76:        """Tenant isolation keywords exist in the Communications module source."""
backend\tests\test_communications_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_communications_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_communications_tenant.py:87:        assert found, f"Communications: tenant isolation keywords not found in source"
backend\tests\test_christian_pd_hub_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_christian_pd_hub_api.py:61:        """School record for Christian PD Hub tenant is created and queryable."""
backend\tests\test_christian_pd_hub_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_christian_pd_hub_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_school_year_term_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_school_year_term_api.py:61:        """School record for School Year Term tenant is created and queryable."""
backend\tests\test_school_year_term_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_school_year_term_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_document_file_framework_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_document_file_framework_negative.py:33:    """Negative tests for Document File Framework: unauthorized, invalid, forbidden paths."""
backend\tests\test_document_file_framework_negative.py:40:    def test_document_file_framework_unauthenticated_request_is_forbidden(self):
backend\tests\test_document_file_framework_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_christian_pd_hub_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_christian_pd_hub_negative.py:33:    """Negative tests for Christian PD Hub: unauthorized, invalid, forbidden paths."""
backend\tests\test_christian_pd_hub_negative.py:40:    def test_christian_pd_hub_unauthenticated_request_is_forbidden(self):
backend\tests\test_christian_pd_hub_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_communications_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_communications_api.py:61:        """School record for Communications tenant is created and queryable."""
backend\tests\test_communications_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_communications_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_communications_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_communications_negative.py:33:    """Negative tests for Communications: unauthorized, invalid, forbidden paths."""
backend\tests\test_communications_negative.py:40:    def test_communications_unauthenticated_request_is_forbidden(self):
backend\tests\test_communications_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_document_file_framework_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_document_file_framework_api.py:61:        """School record for Document File Framework tenant is created and queryable."""
backend\tests\test_document_file_framework_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_document_file_framework_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_school_profile_unit.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_unit.py:22:    keywords = ["SchoolProfile", "SchoolSettings", "tenant_root", "logo", "school_identity"]
backend\tests\test_school_profile_unit.py:42:    """Verify tenant/school scoping keywords appear in the School Profile source tree."""
backend\tests\test_school_profile_unit.py:50:        "school_id" in source_text
backend\tests\test_school_profile_unit.py:53:    ), f"School Profile: tenant/school scoping not found in source"
backend\tests\test_christian_pd_hub_unit.py:42:    """Verify tenant/school scoping keywords appear in the Christian PD Hub source tree."""
backend\tests\test_christian_pd_hub_unit.py:50:        "school_id" in source_text
backend\tests\test_christian_pd_hub_unit.py:53:    ), f"Christian PD Hub: tenant/school scoping not found in source"
backend\tests\test_51x51_evidence_20_grades___report_cards.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_20_grades___report_cards.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_20_grades___report_cards.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_20_grades___report_cards.py:45:# tenant
backend\tests\test_51x51_evidence_20_grades___report_cards.py:46:# cross-tenant
backend\tests\test_51x51_evidence_20_grades___report_cards.py:48:# isolation
backend\tests\test_51x51_evidence_20_grades___report_cards.py:70:# unauthorized
backend\tests\test_51x51_evidence_20_grades___report_cards.py:72:# forbidden
backend\tests\test_director_actions.py:108:        school_id = str(school.id)
backend\tests\test_director_actions.py:117:                'school_id': school_id,
backend\tests\test_director_actions.py:134:        # Test 2: POST with authenticated non-staff (must be forbidden)
backend\tests\test_director_actions.py:149:                'school_id': school_id,
backend\tests\test_director_actions.py:173:                'school_id': school_id,
backend\tests\test_director_actions.py:190:                'school_id': school_id,
backend\tests\test_director_actions.py:205:                'school_id': school_id,
backend\tests\test_director_actions.py:220:                'school_id': school_id,
backend\tests\test_director_actions.py:235:                'school_id': school_id,
backend\tests\test_director_timeline.py:44:        f"/api/director/timeline/?school_id={school.id}&year_id={academic_year.id}&limit=20"
backend\tests\test_curriculum_pacing.py:19:    - Respects school scoping via X-School-Id header
backend\tests\test_portrait_graduate_tenant.py:2:Tenant isolation tests for the Portrait of the Graduate module.
backend\tests\test_portrait_graduate_tenant.py:23:        username=f"tenant-a-portrait_graduate-{token}",
backend\tests\test_portrait_graduate_tenant.py:32:    """Cross-tenant isolation tests for Portrait of the Graduate."""
backend\tests\test_portrait_graduate_tenant.py:38:    def test_portrait_graduate_tenant_school_ids_are_distinct(self):
backend\tests\test_portrait_graduate_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_portrait_graduate_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_portrait_graduate_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_portrait_graduate_tenant.py:47:    def test_portrait_graduate_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_portrait_graduate_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_portrait_graduate_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_portrait_graduate_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_portrait_graduate_tenant.py:58:    def test_portrait_graduate_same_tenant_request_is_allowed(self):
backend\tests\test_portrait_graduate_tenant.py:67:    def test_portrait_graduate_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_portrait_graduate_tenant.py:75:    def test_portrait_graduate_isolation_keyword_present_in_source(self):
backend\tests\test_portrait_graduate_tenant.py:76:        """Tenant isolation keywords exist in the Portrait of the Graduate module source."""
backend\tests\test_portrait_graduate_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_portrait_graduate_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_portrait_graduate_tenant.py:87:        assert found, f"Portrait of the Graduate: tenant isolation keywords not found in source"
backend\tests\test_school_profile_tenant.py:2:Tenant isolation tests for the School Profile module.
backend\tests\test_school_profile_tenant.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_tenant.py:23:        username=f"tenant-a-school_profile-{token}",
backend\tests\test_school_profile_tenant.py:32:    """Cross-tenant isolation tests for School Profile."""
backend\tests\test_school_profile_tenant.py:38:    def test_school_profile_tenant_school_ids_are_distinct(self):
backend\tests\test_school_profile_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_school_profile_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_school_profile_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_school_profile_tenant.py:47:    def test_school_profile_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_school_profile_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_school_profile_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_school_profile_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_school_profile_tenant.py:58:    def test_school_profile_same_tenant_request_is_allowed(self):
backend\tests\test_school_profile_tenant.py:67:    def test_school_profile_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_school_profile_tenant.py:75:    def test_school_profile_isolation_keyword_present_in_source(self):
backend\tests\test_school_profile_tenant.py:76:        """Tenant isolation keywords exist in the School Profile module source."""
backend\tests\test_school_profile_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_school_profile_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_school_profile_tenant.py:87:        assert found, f"School Profile: tenant isolation keywords not found in source"
backend\tests\test_crown_compass_unit.py:42:    """Verify tenant/school scoping keywords appear in the Crown Compass source tree."""
backend\tests\test_crown_compass_unit.py:50:        "school_id" in source_text
backend\tests\test_crown_compass_unit.py:53:    ), f"Crown Compass: tenant/school scoping not found in source"
backend\tests\test_notifications_framework_tenant.py:2:Tenant isolation tests for the Notifications Framework module.
backend\tests\test_notifications_framework_tenant.py:23:        username=f"tenant-a-notifications_framework-{token}",
backend\tests\test_notifications_framework_tenant.py:32:    """Cross-tenant isolation tests for Notifications Framework."""
backend\tests\test_notifications_framework_tenant.py:38:    def test_notifications_framework_tenant_school_ids_are_distinct(self):
backend\tests\test_notifications_framework_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_notifications_framework_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_notifications_framework_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_notifications_framework_tenant.py:47:    def test_notifications_framework_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_notifications_framework_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_notifications_framework_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_notifications_framework_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_notifications_framework_tenant.py:58:    def test_notifications_framework_same_tenant_request_is_allowed(self):
backend\tests\test_notifications_framework_tenant.py:67:    def test_notifications_framework_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_notifications_framework_tenant.py:75:    def test_notifications_framework_isolation_keyword_present_in_source(self):
backend\tests\test_notifications_framework_tenant.py:76:        """Tenant isolation keywords exist in the Notifications Framework module source."""
backend\tests\test_notifications_framework_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_notifications_framework_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_notifications_framework_tenant.py:87:        assert found, f"Notifications Framework: tenant isolation keywords not found in source"
backend\tests\test_parent_portal_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_parent_portal_negative.py:33:    """Negative tests for Parent Portal: unauthorized, invalid, forbidden paths."""
backend\tests\test_parent_portal_negative.py:40:    def test_parent_portal_unauthenticated_request_is_forbidden(self):
backend\tests\test_parent_portal_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_crown_compass_tenant.py:2:Tenant isolation tests for the Crown Compass module.
backend\tests\test_crown_compass_tenant.py:23:        username=f"tenant-a-crown_compass-{token}",
backend\tests\test_crown_compass_tenant.py:32:    """Cross-tenant isolation tests for Crown Compass."""
backend\tests\test_crown_compass_tenant.py:38:    def test_crown_compass_tenant_school_ids_are_distinct(self):
backend\tests\test_crown_compass_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_crown_compass_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_crown_compass_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_crown_compass_tenant.py:47:    def test_crown_compass_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_crown_compass_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_crown_compass_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_crown_compass_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_crown_compass_tenant.py:58:    def test_crown_compass_same_tenant_request_is_allowed(self):
backend\tests\test_crown_compass_tenant.py:67:    def test_crown_compass_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_crown_compass_tenant.py:75:    def test_crown_compass_isolation_keyword_present_in_source(self):
backend\tests\test_crown_compass_tenant.py:76:        """Tenant isolation keywords exist in the Crown Compass module source."""
backend\tests\test_crown_compass_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_crown_compass_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_crown_compass_tenant.py:87:        assert found, f"Crown Compass: tenant isolation keywords not found in source"
backend\tests\test_graduation_audit_v1.py:6:from core.tenant_models import clear_current_school, set_current_school
backend\tests\test_phase72_tenant_isolation.py:5:Verifies tenant-scoping enforcement across the six major live API surfaces,
backend\tests\test_phase72_tenant_isolation.py:8:  Canonical  (households.scoping.get_request_school_id):
backend\tests\test_phase72_tenant_isolation.py:10:    ├óΓÇáΓÇÖ non-staff cross-tenant request ├óΓÇáΓÇÖ HTTP 404
backend\tests\test_phase72_tenant_isolation.py:14:    ├óΓÇáΓÇÖ cross-tenant request ├óΓÇáΓÇÖ HTTP 200 with empty/school-B-only data
backend\tests\test_phase72_tenant_isolation.py:15:    ├óΓÇáΓÇÖ school-A data MUST NOT appear (ORM-level isolation confirmed)
backend\tests\test_phase72_tenant_isolation.py:18:  1. Missing X-School-Id header  ├óΓÇáΓÇÖ 400
backend\tests\test_phase72_tenant_isolation.py:23:Branch: phase/7.2-tenant-isolation-audit
backend\tests\test_phase72_tenant_isolation.py:46:        # Non-staff user ├óΓé¼ΓÇ¥ used for cross-tenant (wrong school) tests.
backend\tests\test_phase72_tenant_isolation.py:51:            school_id=self.school_a.id,
backend\tests\test_phase72_tenant_isolation.py:58:            school_id=self.school_a.id,
backend\tests\test_phase72_tenant_isolation.py:65:            school_id=self.school_b.id,
backend\tests\test_phase72_tenant_isolation.py:68:        # tenant resolver finds no header and no user.school_id -> None -> 400.
backend\tests\test_phase72_tenant_isolation.py:79:# 1. Gradebook ├óΓé¼ΓÇ¥ CANONICAL scoping (get_request_school_id required=True)
backend\tests\test_phase72_tenant_isolation.py:86:    gradebook/views.py uses households.scoping.get_request_school_id(required=True).
backend\tests\test_phase72_tenant_isolation.py:88:    Mechanism: resolve_tenant_school_id detects header_present + user.school_id mismatch.
backend\tests\test_phase72_tenant_isolation.py:95:        No X-School-Id header -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:96:        Must use user_noschool (no school_id attribute) so tenant resolver
backend\tests\test_phase72_tenant_isolation.py:108:        the tenant guard firing.
backend\tests\test_phase72_tenant_isolation.py:117:        get_request_school_id() enforces: header_present AND user.school_id ├óΓÇ░┬á header ├óΓÇáΓÇÖ 404.
backend\tests\test_phase72_tenant_isolation.py:118:        Canonical cross-tenant prevention confirmed.
backend\tests\test_phase72_tenant_isolation.py:131:# 2. Billing Runs ├óΓé¼ΓÇ¥ CANONICAL scoping (get_request_school_id via @api_view)
backend\tests\test_phase72_tenant_isolation.py:138:    billing/api.py  billing_runs()  uses get_request_school_id (canonical).
backend\tests\test_phase72_tenant_isolation.py:140:      missing header ├óΓÇáΓÇÖ 400, wrong tenant ├óΓÇáΓÇÖ 404.
backend\tests\test_phase72_tenant_isolation.py:147:        No X-School-Id -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:148:        Must use user_noschool (no school_id attribute) so tenant resolver
backend\tests\test_phase72_tenant_isolation.py:165:        get_request_school_id() ├óΓÇáΓÇÖ HTTP 404.
backend\tests\test_phase72_tenant_isolation.py:166:        Canonical cross-tenant prevention confirmed for billing module.
backend\tests\test_phase72_tenant_isolation.py:183:#  Scoping upgraded to get_request_school_id() in Phase 7.2B:
backend\tests\test_phase72_tenant_isolation.py:191:    Phase 7.2B: discipline upgraded to canonical get_request_school_id() scoping.
backend\tests\test_phase72_tenant_isolation.py:192:    Wrong-tenant non-staff requests now return HTTP 404 (was 200 before remediation).
backend\tests\test_phase72_tenant_isolation.py:199:        No X-School-Id header -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:201:        user.school_id, returning None -> MissingSchoolContext -> 400.
backend\tests\test_phase72_tenant_isolation.py:217:        get_request_school_id() enforces the cross-tenant guard.
backend\tests\test_phase72_tenant_isolation.py:223:    def test_cross_tenant_data_isolation_confirmed(self):
backend\tests\test_phase72_tenant_isolation.py:225:        Cross-tenant request blocked at the scoping layer (404).
backend\tests\test_phase72_tenant_isolation.py:246:    Phase 7.2B.2: Financial Aid upgraded to canonical get_request_school_id() scoping.
backend\tests\test_phase72_tenant_isolation.py:247:    Scoping now fires before permission check; wrong-tenant -> 404.
backend\tests\test_phase72_tenant_isolation.py:253:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Uses user_noschool."""
backend\tests\test_phase72_tenant_isolation.py:259:        """Correct school header -> scoping passes (200 or 403 from permission check)."""
backend\tests\test_phase72_tenant_isolation.py:265:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_phase72_tenant_isolation.py:282:#    canonical pattern; scoping fires before staff/permission checks in all three.
backend\tests\test_phase72_tenant_isolation.py:287:    Phase 7.2B.3: Admissions applications/ upgraded to canonical get_request_school_id().
backend\tests\test_phase72_tenant_isolation.py:288:    Scoping fires before staff check; wrong-tenant -> 404, missing header -> 400.
backend\tests\test_phase72_tenant_isolation.py:294:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Uses user_noschool."""
backend\tests\test_phase72_tenant_isolation.py:306:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_phase72_tenant_isolation.py:319:    Phase 7.2B.3: Admissions enroll/ upgraded to canonical get_request_school_id().
backend\tests\test_phase72_tenant_isolation.py:326:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Scoping fires before body parse."""
backend\tests\test_phase72_tenant_isolation.py:341:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_portrait_graduate_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_portrait_graduate_negative.py:33:    """Negative tests for Portrait of the Graduate: unauthorized, invalid, forbidden paths."""
backend\tests\test_portrait_graduate_negative.py:40:    def test_portrait_graduate_unauthenticated_request_is_forbidden(self):
backend\tests\test_portrait_graduate_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_school_profile_negative.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_school_profile_negative.py:33:    """Negative tests for School Profile: unauthorized, invalid, forbidden paths."""
backend\tests\test_school_profile_negative.py:40:    def test_school_profile_unauthenticated_request_is_forbidden(self):
backend\tests\test_school_profile_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_grades_report_cards_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_grades_report_cards_negative.py:33:    """Negative tests for Grades Report Cards: unauthorized, invalid, forbidden paths."""
backend\tests\test_grades_report_cards_negative.py:40:    def test_grades_report_cards_unauthenticated_request_is_forbidden(self):
backend\tests\test_grades_report_cards_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_parent_portal_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_parent_portal_api.py:61:        """School record for Parent Portal tenant is created and queryable."""
backend\tests\test_parent_portal_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_parent_portal_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_notifications_framework_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_notifications_framework_negative.py:33:    """Negative tests for Notifications Framework: unauthorized, invalid, forbidden paths."""
backend\tests\test_notifications_framework_negative.py:40:    def test_notifications_framework_unauthenticated_request_is_forbidden(self):
backend\tests\test_notifications_framework_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_grade_levels_unit.py:42:    """Verify tenant/school scoping keywords appear in the Grade Levels source tree."""
backend\tests\test_grade_levels_unit.py:50:        "school_id" in source_text
backend\tests\test_grade_levels_unit.py:53:    ), f"Grade Levels: tenant/school scoping not found in source"
backend\tests\test_grade_levels_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_grade_levels_api.py:61:        """School record for Grade Levels tenant is created and queryable."""
backend\tests\test_grade_levels_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_grade_levels_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_portrait_graduate_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_portrait_graduate_api.py:61:        """School record for Portrait of the Graduate tenant is created and queryable."""
backend\tests\test_portrait_graduate_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_portrait_graduate_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_school_profile_api.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_school_profile_api.py:61:        """School record for School Profile tenant is created and queryable."""
backend\tests\test_school_profile_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_school_profile_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_nurse_health_office_unit.py:42:    """Verify tenant/school scoping keywords appear in the Nurse Health Office source tree."""
backend\tests\test_nurse_health_office_unit.py:50:        "school_id" in source_text
backend\tests\test_nurse_health_office_unit.py:53:    ), f"Nurse Health Office: tenant/school scoping not found in source"
backend\tests\test_notifications_framework_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_notifications_framework_api.py:61:        """School record for Notifications Framework tenant is created and queryable."""
backend\tests\test_notifications_framework_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_notifications_framework_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_parent_portal_unit.py:42:    """Verify tenant/school scoping keywords appear in the Parent Portal source tree."""
backend\tests\test_parent_portal_unit.py:50:        "school_id" in source_text
backend\tests\test_parent_portal_unit.py:53:    ), f"Parent Portal: tenant/school scoping not found in source"
backend\tests\test_grade_levels_tenant.py:2:Tenant isolation tests for the Grade Levels module.
backend\tests\test_grade_levels_tenant.py:23:        username=f"tenant-a-grade_levels-{token}",
backend\tests\test_grade_levels_tenant.py:32:    """Cross-tenant isolation tests for Grade Levels."""
backend\tests\test_grade_levels_tenant.py:38:    def test_grade_levels_tenant_school_ids_are_distinct(self):
backend\tests\test_grade_levels_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_grade_levels_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_grade_levels_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_grade_levels_tenant.py:47:    def test_grade_levels_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_grade_levels_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_grade_levels_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_grade_levels_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_grade_levels_tenant.py:58:    def test_grade_levels_same_tenant_request_is_allowed(self):
backend\tests\test_grade_levels_tenant.py:67:    def test_grade_levels_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_grade_levels_tenant.py:75:    def test_grade_levels_isolation_keyword_present_in_source(self):
backend\tests\test_grade_levels_tenant.py:76:        """Tenant isolation keywords exist in the Grade Levels module source."""
backend\tests\test_grade_levels_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_grade_levels_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_grade_levels_tenant.py:87:        assert found, f"Grade Levels: tenant isolation keywords not found in source"
backend\tests\test_grades_report_cards_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_grades_report_cards_api.py:61:        """School record for Grades Report Cards tenant is created and queryable."""
backend\tests\test_grades_report_cards_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_grades_report_cards_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_grades_report_cards_unit.py:42:    """Verify tenant/school scoping keywords appear in the Grades Report Cards source tree."""
backend\tests\test_grades_report_cards_unit.py:50:        "school_id" in source_text
backend\tests\test_grades_report_cards_unit.py:53:    ), f"Grades Report Cards: tenant/school scoping not found in source"
backend\tests\test_platform_provisioning.py:18:def test_create_school_idempotent(django_user_model):
backend\tests\test_platform_provisioning.py:26:    from tenants.models import TenantProfile
backend\tests\test_platform_provisioning.py:50:    profile_count = TenantProfile.objects.filter(school_id=job1.school_id).count()
backend\tests\test_platform_provisioning.py:65:    from tenants.models import TenantProfile
backend\tests\test_platform_provisioning.py:88:    profile = TenantProfile.objects.get(school_id=job.school_id)
backend\tests\test_schedule_builder_unit.py:42:    """Verify tenant/school scoping keywords appear in the Standalone Schedule Builder source tree."""
backend\tests\test_schedule_builder_unit.py:50:        "school_id" in source_text
backend\tests\test_schedule_builder_unit.py:53:    ), f"Standalone Schedule Builder: tenant/school scoping not found in source"
backend\tests\test_needs_info_emails.py:47:            "school_id": str(school.id),
backend\tests\test_nurse_health_office_tenant.py:2:Tenant isolation tests for the Nurse Health Office module.
backend\tests\test_nurse_health_office_tenant.py:23:        username=f"tenant-a-nurse_health_office-{token}",
backend\tests\test_nurse_health_office_tenant.py:32:    """Cross-tenant isolation tests for Nurse Health Office."""
backend\tests\test_nurse_health_office_tenant.py:38:    def test_nurse_health_office_tenant_school_ids_are_distinct(self):
backend\tests\test_nurse_health_office_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_nurse_health_office_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_nurse_health_office_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_nurse_health_office_tenant.py:47:    def test_nurse_health_office_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_nurse_health_office_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_nurse_health_office_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_nurse_health_office_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_nurse_health_office_tenant.py:58:    def test_nurse_health_office_same_tenant_request_is_allowed(self):
backend\tests\test_nurse_health_office_tenant.py:67:    def test_nurse_health_office_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_nurse_health_office_tenant.py:75:    def test_nurse_health_office_isolation_keyword_present_in_source(self):
backend\tests\test_nurse_health_office_tenant.py:76:        """Tenant isolation keywords exist in the Nurse Health Office module source."""
backend\tests\test_nurse_health_office_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_nurse_health_office_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_nurse_health_office_tenant.py:87:        assert found, f"Nurse Health Office: tenant isolation keywords not found in source"
backend\tests\test_parent_portal_tenant.py:2:Tenant isolation tests for the Parent Portal module.
backend\tests\test_parent_portal_tenant.py:23:        username=f"tenant-a-parent_portal-{token}",
backend\tests\test_parent_portal_tenant.py:32:    """Cross-tenant isolation tests for Parent Portal."""
backend\tests\test_parent_portal_tenant.py:38:    def test_parent_portal_tenant_school_ids_are_distinct(self):
backend\tests\test_parent_portal_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_parent_portal_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_parent_portal_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_parent_portal_tenant.py:47:    def test_parent_portal_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_parent_portal_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_parent_portal_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_parent_portal_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_parent_portal_tenant.py:58:    def test_parent_portal_same_tenant_request_is_allowed(self):
backend\tests\test_parent_portal_tenant.py:67:    def test_parent_portal_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_parent_portal_tenant.py:75:    def test_parent_portal_isolation_keyword_present_in_source(self):
backend\tests\test_parent_portal_tenant.py:76:        """Tenant isolation keywords exist in the Parent Portal module source."""
backend\tests\test_parent_portal_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_parent_portal_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_parent_portal_tenant.py:87:        assert found, f"Parent Portal: tenant isolation keywords not found in source"
backend\tests\test_golden_path_bootstrap_school_create.py:1:"""Test golden_path_bootstrap creates school when school_id provided."""
backend\tests\test_golden_path_bootstrap_school_create.py:17:    PROOF: golden_path_bootstrap creates school if not exists when school_id provided.
backend\tests\test_golden_path_bootstrap_school_create.py:20:    if school_id was provided but school didn't exist in DB.
backend\tests\test_golden_path_bootstrap_school_create.py:23:    golden_path_bootstrap with a deterministic school_id. Before this fix,
backend\tests\test_golden_path_bootstrap_school_create.py:27:    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
backend\tests\test_golden_path_bootstrap_school_create.py:30:    School.objects.filter(pk=test_school_id).delete()
backend\tests\test_golden_path_bootstrap_school_create.py:31:    assert not School.objects.filter(pk=test_school_id).exists()
backend\tests\test_golden_path_bootstrap_school_create.py:33:    # Run bootstrap with explicit school_id
backend\tests\test_golden_path_bootstrap_school_create.py:37:        f'--school-id={test_school_id}',
backend\tests\test_golden_path_bootstrap_school_create.py:42:    school = School.objects.get(pk=test_school_id)
backend\tests\test_golden_path_bootstrap_school_create.py:53:    Running bootstrap twice with same school_id should not crash or duplicate.
backend\tests\test_golden_path_bootstrap_school_create.py:55:    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
backend\tests\test_golden_path_bootstrap_school_create.py:58:    School.objects.filter(pk=test_school_id).delete()
backend\tests\test_golden_path_bootstrap_school_create.py:62:        f'--school-id={test_school_id}',
backend\tests\test_golden_path_bootstrap_school_create.py:70:        f'--school-id={test_school_id}',
backend\tests\test_golden_path_bootstrap_school_create.py:75:    assert School.objects.filter(pk=test_school_id).count() == 1
backend\tests\test_grade_levels_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_grade_levels_negative.py:33:    """Negative tests for Grade Levels: unauthorized, invalid, forbidden paths."""
backend\tests\test_grade_levels_negative.py:40:    def test_grade_levels_unauthenticated_request_is_forbidden(self):
backend\tests\test_grade_levels_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_grades_report_cards_tenant.py:2:Tenant isolation tests for the Grades Report Cards module.
backend\tests\test_grades_report_cards_tenant.py:23:        username=f"tenant-a-grades_report_cards-{token}",
backend\tests\test_grades_report_cards_tenant.py:32:    """Cross-tenant isolation tests for Grades Report Cards."""
backend\tests\test_grades_report_cards_tenant.py:38:    def test_grades_report_cards_tenant_school_ids_are_distinct(self):
backend\tests\test_grades_report_cards_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_grades_report_cards_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_grades_report_cards_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_grades_report_cards_tenant.py:47:    def test_grades_report_cards_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_grades_report_cards_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_grades_report_cards_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_grades_report_cards_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_grades_report_cards_tenant.py:58:    def test_grades_report_cards_same_tenant_request_is_allowed(self):
backend\tests\test_grades_report_cards_tenant.py:67:    def test_grades_report_cards_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_grades_report_cards_tenant.py:75:    def test_grades_report_cards_isolation_keyword_present_in_source(self):
backend\tests\test_grades_report_cards_tenant.py:76:        """Tenant isolation keywords exist in the Grades Report Cards module source."""
backend\tests\test_grades_report_cards_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_grades_report_cards_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_grades_report_cards_tenant.py:87:        assert found, f"Grades Report Cards: tenant isolation keywords not found in source"
backend\tests\test_reporting_data_access_unit.py:42:    """Verify tenant/school scoping keywords appear in the Reporting Data Access Standards source tree."""
backend\tests\test_reporting_data_access_unit.py:50:        "school_id" in source_text
backend\tests\test_reporting_data_access_unit.py:53:    ), f"Reporting Data Access Standards: tenant/school scoping not found in source"
backend\tests\test_schedule_builder_tenant.py:2:Tenant isolation tests for the Standalone Schedule Builder module.
backend\tests\test_schedule_builder_tenant.py:23:        username=f"tenant-a-schedule_builder-{token}",
backend\tests\test_schedule_builder_tenant.py:32:    """Cross-tenant isolation tests for Standalone Schedule Builder."""
backend\tests\test_schedule_builder_tenant.py:38:    def test_schedule_builder_tenant_school_ids_are_distinct(self):
backend\tests\test_schedule_builder_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_schedule_builder_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_schedule_builder_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_schedule_builder_tenant.py:47:    def test_schedule_builder_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_schedule_builder_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_schedule_builder_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_schedule_builder_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_schedule_builder_tenant.py:58:    def test_schedule_builder_same_tenant_request_is_allowed(self):
backend\tests\test_schedule_builder_tenant.py:67:    def test_schedule_builder_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_schedule_builder_tenant.py:75:    def test_schedule_builder_isolation_keyword_present_in_source(self):
backend\tests\test_schedule_builder_tenant.py:76:        """Tenant isolation keywords exist in the Standalone Schedule Builder module source."""
backend\tests\test_schedule_builder_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_schedule_builder_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_schedule_builder_tenant.py:87:        assert found, f"Standalone Schedule Builder: tenant isolation keywords not found in source"
backend\tests\test_mobile_family_app_unit.py:42:    """Verify tenant/school scoping keywords appear in the Mobile Family App source tree."""
backend\tests\test_mobile_family_app_unit.py:50:        "school_id" in source_text
backend\tests\test_mobile_family_app_unit.py:53:    ), f"Mobile Family App: tenant/school scoping not found in source"
backend\tests\test_nurse_health_office_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_nurse_health_office_negative.py:33:    """Negative tests for Nurse Health Office: unauthorized, invalid, forbidden paths."""
backend\tests\test_nurse_health_office_negative.py:40:    def test_nurse_health_office_unauthenticated_request_is_forbidden(self):
backend\tests\test_nurse_health_office_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_reporting_data_access_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_reporting_data_access_api.py:61:        """School record for Reporting Data Access Standards tenant is created and queryable."""
backend\tests\test_reporting_data_access_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_reporting_data_access_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_golden_path.py:40:    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=perm)
backend\tests\test_golden_path.py:58:    household = Household.objects.create(school_id=school.id, name="Golden Household")
backend\tests\test_golden_path.py:59:    app = Application.objects.create(school_id=school.id, household=household, status="SUBMITTED")
backend\tests\test_golden_path.py:61:        school_id=school.id,
backend\tests\test_golden_path.py:126:    household = Household.objects.create(school_id=school.id, name="Billing Household")
backend\tests\test_golden_path.py:127:    student_one = Student.objects.create(school_id=school.id, household=household, first_name="A", last_name="One", grade_level="5", is_active=True)
backend\tests\test_golden_path.py:128:    student_two = Student.objects.create(school_id=school.id, household=household, first_name="B", last_name="Two", grade_level="5", is_active=True)
backend\tests\test_golden_path.py:129:    course = Course.objects.create(school_id=school.id, code="MATH5", name="Math 5")
backend\tests\test_golden_path.py:130:    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="Teacher", grade_band="5")
backend\tests\test_golden_path.py:131:    Enrollment.objects.create(school_id=school.id, section=section, student=student_one)
backend\tests\test_golden_path.py:132:    Enrollment.objects.create(school_id=school.id, section=section, student=student_two)
backend\tests\test_golden_path.py:162:    course = Course.objects.create(school_id=school.id, code="SCI4", name="Science 4")
backend\tests\test_golden_path.py:163:    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="Teacher", grade_band="4")
backend\tests\test_mission_metrics_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_mission_metrics_negative.py:33:    """Negative tests for Mission Metrics: unauthorized, invalid, forbidden paths."""
backend\tests\test_mission_metrics_negative.py:40:    def test_mission_metrics_unauthenticated_request_is_forbidden(self):
backend\tests\test_mission_metrics_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_nurse_health_office_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_nurse_health_office_api.py:61:        """School record for Nurse Health Office tenant is created and queryable."""
backend\tests\test_nurse_health_office_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_nurse_health_office_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_mobile_family_app_tenant.py:2:Tenant isolation tests for the Mobile Family App module.
backend\tests\test_mobile_family_app_tenant.py:23:        username=f"tenant-a-mobile_family_app-{token}",
backend\tests\test_mobile_family_app_tenant.py:32:    """Cross-tenant isolation tests for Mobile Family App."""
backend\tests\test_mobile_family_app_tenant.py:38:    def test_mobile_family_app_tenant_school_ids_are_distinct(self):
backend\tests\test_mobile_family_app_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_mobile_family_app_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_mobile_family_app_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_mobile_family_app_tenant.py:47:    def test_mobile_family_app_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_mobile_family_app_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_mobile_family_app_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_mobile_family_app_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_mobile_family_app_tenant.py:58:    def test_mobile_family_app_same_tenant_request_is_allowed(self):
backend\tests\test_mobile_family_app_tenant.py:67:    def test_mobile_family_app_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_mobile_family_app_tenant.py:75:    def test_mobile_family_app_isolation_keyword_present_in_source(self):
backend\tests\test_mobile_family_app_tenant.py:76:        """Tenant isolation keywords exist in the Mobile Family App module source."""
backend\tests\test_mobile_family_app_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_mobile_family_app_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_mobile_family_app_tenant.py:87:        assert found, f"Mobile Family App: tenant isolation keywords not found in source"
backend\tests\test_schedule_builder_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_schedule_builder_negative.py:33:    """Negative tests for Standalone Schedule Builder: unauthorized, invalid, forbidden paths."""
backend\tests\test_schedule_builder_negative.py:40:    def test_schedule_builder_unauthenticated_request_is_forbidden(self):
backend\tests\test_schedule_builder_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_microsoft_integration_readiness.py:31:    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-123")
backend\tests\test_microsoft_integration_readiness.py:54:    assert calls[0]["url"].startswith("https://login.microsoftonline.com/tenant-123/")
backend\tests\test_microsoft_integration_readiness.py:74:        school_id="11111111-1111-1111-1111-111111111111",
backend\tests\test_reporting_data_access_tenant.py:2:Tenant isolation tests for the Reporting Data Access Standards module.
backend\tests\test_reporting_data_access_tenant.py:23:        username=f"tenant-a-reporting_data_access-{token}",
backend\tests\test_reporting_data_access_tenant.py:32:    """Cross-tenant isolation tests for Reporting Data Access Standards."""
backend\tests\test_reporting_data_access_tenant.py:38:    def test_reporting_data_access_tenant_school_ids_are_distinct(self):
backend\tests\test_reporting_data_access_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_reporting_data_access_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_reporting_data_access_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_reporting_data_access_tenant.py:47:    def test_reporting_data_access_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_reporting_data_access_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_reporting_data_access_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_reporting_data_access_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_reporting_data_access_tenant.py:58:    def test_reporting_data_access_same_tenant_request_is_allowed(self):
backend\tests\test_reporting_data_access_tenant.py:67:    def test_reporting_data_access_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_reporting_data_access_tenant.py:75:    def test_reporting_data_access_isolation_keyword_present_in_source(self):
backend\tests\test_reporting_data_access_tenant.py:76:        """Tenant isolation keywords exist in the Reporting Data Access Standards module source."""
backend\tests\test_reporting_data_access_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_reporting_data_access_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_reporting_data_access_tenant.py:87:        assert found, f"Reporting Data Access Standards: tenant isolation keywords not found in source"
backend\tests\test_mission_metrics_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_mission_metrics_api.py:61:        """School record for Mission Metrics tenant is created and queryable."""
backend\tests\test_mission_metrics_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_mission_metrics_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_extended_discipline_unit.py:42:    """Verify tenant/school scoping keywords appear in the Extended Discipline Workflows source tree."""
backend\tests\test_extended_discipline_unit.py:50:        "school_id" in source_text
backend\tests\test_extended_discipline_unit.py:53:    ), f"Extended Discipline Workflows: tenant/school scoping not found in source"
backend\tests\test_portrait_graduate_unit.py:42:    """Verify tenant/school scoping keywords appear in the Portrait of the Graduate source tree."""
backend\tests\test_portrait_graduate_unit.py:50:        "school_id" in source_text
backend\tests\test_portrait_graduate_unit.py:53:    ), f"Portrait of the Graduate: tenant/school scoping not found in source"
backend\tests\test_notifications_framework_unit.py:42:    """Verify tenant/school scoping keywords appear in the Notifications Framework source tree."""
backend\tests\test_notifications_framework_unit.py:50:        "school_id" in source_text
backend\tests\test_notifications_framework_unit.py:53:    ), f"Notifications Framework: tenant/school scoping not found in source"
backend\tests\test_schedule_builder_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_schedule_builder_api.py:61:        """School record for Standalone Schedule Builder tenant is created and queryable."""
backend\tests\test_schedule_builder_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_schedule_builder_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_mobile_family_app_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_mobile_family_app_negative.py:33:    """Negative tests for Mobile Family App: unauthorized, invalid, forbidden paths."""
backend\tests\test_mobile_family_app_negative.py:40:    def test_mobile_family_app_unauthenticated_request_is_forbidden(self):
backend\tests\test_mobile_family_app_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_mission_metrics_unit.py:42:    """Verify tenant/school scoping keywords appear in the Mission Metrics source tree."""
backend\tests\test_mission_metrics_unit.py:50:        "school_id" in source_text
backend\tests\test_mission_metrics_unit.py:53:    ), f"Mission Metrics: tenant/school scoping not found in source"
backend\tests\test_reporting_data_access_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_reporting_data_access_negative.py:33:    """Negative tests for Reporting Data Access Standards: unauthorized, invalid, forbidden paths."""
backend\tests\test_reporting_data_access_negative.py:40:    def test_reporting_data_access_unauthenticated_request_is_forbidden(self):
backend\tests\test_reporting_data_access_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_mobile_family_app_api.py:42:        """Unauthenticated API request to protected endpoint is denied."""
backend\tests\test_mobile_family_app_api.py:61:        """School record for Mobile Family App tenant is created and queryable."""
backend\tests\test_mobile_family_app_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_mobile_family_app_api.py:67:        assert self.user.school_id == self.school.id
backend\tests\test_extended_discipline_tenant.py:2:Tenant isolation tests for the Extended Discipline Workflows module.
backend\tests\test_extended_discipline_tenant.py:23:        username=f"tenant-a-extended_discipline-{token}",
backend\tests\test_extended_discipline_tenant.py:32:    """Cross-tenant isolation tests for Extended Discipline Workflows."""
backend\tests\test_extended_discipline_tenant.py:38:    def test_extended_discipline_tenant_school_ids_are_distinct(self):
backend\tests\test_extended_discipline_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_extended_discipline_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_extended_discipline_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_extended_discipline_tenant.py:47:    def test_extended_discipline_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_extended_discipline_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_extended_discipline_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_extended_discipline_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_extended_discipline_tenant.py:58:    def test_extended_discipline_same_tenant_request_is_allowed(self):
backend\tests\test_extended_discipline_tenant.py:67:    def test_extended_discipline_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_extended_discipline_tenant.py:75:    def test_extended_discipline_isolation_keyword_present_in_source(self):
backend\tests\test_extended_discipline_tenant.py:76:        """Tenant isolation keywords exist in the Extended Discipline Workflows module source."""
backend\tests\test_extended_discipline_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_extended_discipline_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_extended_discipline_tenant.py:87:        assert found, f"Extended Discipline Workflows: tenant isolation keywords not found in source"
backend\tests\test_extended_discipline_negative.py:5:Tests unauthorized, invalid, forbidden, and error conditions.
backend\tests\test_extended_discipline_negative.py:33:    """Negative tests for Extended Discipline Workflows: unauthorized, invalid, forbidden paths."""
backend\tests\test_extended_discipline_negative.py:40:    def test_extended_discipline_unauthenticated_request_is_forbidden(self):
backend\tests\test_extended_discipline_negative.py:75:        """DELETE on a read-only endpoint is forbidden or not allowed."""
backend\tests\test_mission_metrics_tenant.py:2:Tenant isolation tests for the Mission Metrics module.
backend\tests\test_mission_metrics_tenant.py:23:        username=f"tenant-a-mission_metrics-{token}",
backend\tests\test_mission_metrics_tenant.py:32:    """Cross-tenant isolation tests for Mission Metrics."""
backend\tests\test_mission_metrics_tenant.py:38:    def test_mission_metrics_tenant_school_ids_are_distinct(self):
backend\tests\test_mission_metrics_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_mission_metrics_tenant.py:44:        assert self.user_a.school_id == self.school_a.id
backend\tests\test_mission_metrics_tenant.py:45:        assert self.user_a.school_id != self.school_b.id
backend\tests\test_mission_metrics_tenant.py:47:    def test_mission_metrics_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_mission_metrics_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_mission_metrics_tenant.py:50:        # Using integrity endpoint with school B's ID ├óΓé¼ΓÇ¥ should be denied or scoped out
backend\tests\test_mission_metrics_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_mission_metrics_tenant.py:58:    def test_mission_metrics_same_tenant_request_is_allowed(self):
backend\tests\test_mission_metrics_tenant.py:67:    def test_mission_metrics_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_mission_metrics_tenant.py:75:    def test_mission_metrics_isolation_keyword_present_in_source(self):
backend\tests\test_mission_metrics_tenant.py:76:        """Tenant isolation keywords exist in the Mission Metrics module source."""
backend\tests\test_mission_metrics_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_mission_metrics_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_mission_metrics_tenant.py:87:        assert found, f"Mission Metrics: tenant isolation keywords not found in source"
backend\tests\test_reporting_exports_gate.py:92:def test_unauthorized_export_is_denied(client):
```

## Backend Check

System check identified no issues (0 silenced).
```

## Backend Targeted RBAC / Tenant Tests

