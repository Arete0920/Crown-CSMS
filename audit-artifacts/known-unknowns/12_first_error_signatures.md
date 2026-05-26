# First Error Signatures

Generated: 2026-05-25 15:18:23
Repo: tcmegahan/Crown2026

## Run 26377474508
- Workflow: Tests
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26377474508
- Branch: main
- SHA: 7af6c4917cd820d0402b0a98442b1e4986c6cd1d
- Status/Conclusion: completed/failure
- First failing job: pytest
- First failing job databaseId: 77640256111
- First failing step: Run tests
- Raw log: audit-artifacts\known-unknowns\workflow-logs\run_26377474508_job_77640256111_raw.log
- Signature extract: audit-artifacts\known-unknowns\workflow-logs\run_26377474508_job_77640256111_signature.txt

- Signature preview (first 80 lines):
===== MATCH: line 474 =====
pytest	UNKNOWN STEP	2026-05-25T01:00:42.6826497Z ........................................................................ [ 93%]
pytest	UNKNOWN STEP	2026-05-25T01:00:44.8147367Z ........................................................................ [ 95%]
pytest	UNKNOWN STEP	2026-05-25T01:01:20.8911600Z ........................................................................ [ 98%]
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1739321Z ..........................................................               [100%]
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1740175Z =================================== FAILURES ===================================
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1740957Z ____________________ test_billing_run_summary_gross_aid_net ____________________
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1741534Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1741799Z     def test_billing_run_summary_gross_aid_net():
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1742448Z         school = School.objects.create(name="Test School")
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1743218Z         hh = Household.objects.create(school_id=school.id, name="Household")
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1743890Z     
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1745065Z         run = BillingRun.objects.create(school_id=school.id, term="2026-FALL", run_type="TUITION", description="Run", amount_per_student=Decimal("0.00"))
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1746614Z         inv = Invoice.objects.create(school_id=school.id, billing_run=run, household=hh, total_amount=Decimal("1000.00"))

===== MATCH: line 501 =====
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1757442Z >       assert resp.status_code == 200
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1757960Z E       assert 403 == 200
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1758591Z E        +  where 403 = <Response status_code=403, "application/json">.status_code
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1759169Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1759511Z billing/tests/test_billing_summary_api.py:45: AssertionError
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1760314Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1761560Z [24/May/2026 20:48:09,163] WARNING django.request: Forbidden: /api/v1/billing/runs/752b75f2-59ec-480d-9317-9254feab3969/summary/
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1762836Z __ BillingInstallmentPlansRbacTests.test_non_staff_can_post_installment_plan ___
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1763471Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1764358Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_non_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1765349Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1765651Z     def test_non_staff_can_post_installment_plan(self):
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1766179Z         """

===== MATCH: line 523 =====
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1771677Z             HTTP_X_SCHOOL_ID=str(self.school.id),
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1772169Z         )
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1772513Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1772952Z             resp.status_code, (401, 403, 500),
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1773705Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1774536Z         )
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1775348Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776085Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776438Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1777261Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1778250Z [24/May/2026 20:50:18,954] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1779369Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1780046Z 

===== MATCH: line 525 =====
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1772513Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1772952Z             resp.status_code, (401, 403, 500),
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1773705Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1774536Z         )
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1775348Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776085Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776438Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1777261Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1778250Z [24/May/2026 20:50:18,954] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1779369Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1780046Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1780844Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1781824Z 

===== MATCH: line 527 =====
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1773705Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1774536Z         )
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1775348Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776085Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1776438Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1777261Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1778250Z [24/May/2026 20:50:18,954] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1779369Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1780046Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1780844Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1781824Z 
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1782084Z     def test_staff_can_post_installment_plan(self):
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1783064Z         """Staff: same as non-staff ΓÇö endpoint is not staff-gated."""

===== MATCH: line 545 =====
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1786335Z             HTTP_X_SCHOOL_ID=str(self.school.id),
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1786842Z         )
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1787200Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T01:01:45.1787830Z             resp.status_code, (401, 403, 500),

## Run 26377212304
- Workflow: Proof Ceremony
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26377212304
- Branch: stage2-slice11-billing-role-guard
- SHA: 6f75892aa31cf8e6a8eab6d18fa18ba5bf03a1ca
- Status/Conclusion: completed/failure
- First failing job: proof-ceremony
- First failing job databaseId: 77640175706
- First failing step: CrownMagus III: Mutation + Audit + Idempotency Proof
- Raw log: audit-artifacts\known-unknowns\workflow-logs\run_26377212304_job_77640175706_raw.log
- Signature extract: audit-artifacts\known-unknowns\workflow-logs\run_26377212304_job_77640175706_signature.txt

- Signature preview (first 80 lines):
===== MATCH: line 537 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:44:59.8454016Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib
proof-ceremony	UNKNOWN STEP	2026-05-25T00:44:59.8454298Z ##[endgroup]
proof-ceremony	UNKNOWN STEP	2026-05-25T00:44:59.9241930Z 3.12.13 (main, Mar  4 2026, 02:26:36) [GCC 13.3.0]
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2308427Z psycopg: 3.3.2
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2540418Z Traceback (most recent call last):
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2547077Z   File "<string>", line 1, in <module>
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2547691Z ModuleNotFoundError: No module named 'psycopg2'
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2578906Z ##[group]Run cd backend
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2579054Z [36;1mcd backend[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2579193Z [36;1mpython manage.py migrate --noinput[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2609662Z shell: /usr/bin/bash -e {0}
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2609851Z env:
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2610020Z   DJANGO_SETTINGS_MODULE: crown_api.settings

===== MATCH: line 539 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:44:59.9241930Z 3.12.13 (main, Mar  4 2026, 02:26:36) [GCC 13.3.0]
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2308427Z psycopg: 3.3.2
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2540418Z Traceback (most recent call last):
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2547077Z   File "<string>", line 1, in <module>
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2547691Z ModuleNotFoundError: No module named 'psycopg2'
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2578906Z ##[group]Run cd backend
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2579054Z [36;1mcd backend[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2579193Z [36;1mpython manage.py migrate --noinput[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2609662Z shell: /usr/bin/bash -e {0}
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2609851Z env:
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2610020Z   DJANGO_SETTINGS_MODULE: crown_api.settings
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2610255Z   DJANGO_SECRET_KEY: ci-test-secret-key
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:01.2610763Z   DATABASE_URL: ***localhost:5432/crown_test

===== MATCH: line 702 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:37.4915329Z   Applying onboarding.0004_solomonaudience_solomoncategory_solomontopic_and_more... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:38.3627498Z   Applying outreach.0001_initial_outreach... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:38.5741407Z   Applying payments.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:38.6352686Z   Applying payments.0002_providerdispute_providerpayoutbatch_and_more... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:39.8904856Z   Applying payments.0003_savedpaymentmethod_paymentsupportexception_and_more... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:40.3648149Z   Applying payments.0004_bankstatementimport_bankstatemententry_and_more... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:40.3767772Z   Applying pdhub.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:40.4824840Z   Applying platform_ops.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:40.8413216Z   Applying promotion_wizard.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:40.9581160Z   Applying reenrollment.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:41.2237784Z   Applying room_setup_wizard.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:41.2293569Z   Applying safety.0001_initial... OK
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:41.3656419Z   Applying scheduling_wizard.0001_initial... OK

===== MATCH: line 774 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175143Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175362Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175560Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175721Z ##[endgroup]
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3267271Z ##[group]Run curl --max-time 30 -f -sf http://127.0.0.1:8000/health/ | tee proof_health.json || (echo "Health check FAILED"; exit 1)
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3267874Z [36;1mcurl --max-time 30 -f -sf http://127.0.0.1:8000/health/ | tee proof_health.json || (echo "Health check FAILED"; exit 1)[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268216Z [36;1mecho ""[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268443Z [36;1mecho "--- build_sha in health response ---"[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268657Z [36;1mpython3 -c "[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268845Z [36;1mimport json, sys[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269050Z [36;1mtry:[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269291Z [36;1m    d = json.load(open('proof_health.json'))[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269501Z [36;1m    sha = d.get('build_sha', 'MISSING')[0m

===== MATCH: line 775 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175362Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175560Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib
proof-ceremony	UNKNOWN STEP	2026-05-25T00:45:59.3175721Z ##[endgroup]
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3267271Z ##[group]Run curl --max-time 30 -f -sf http://127.0.0.1:8000/health/ | tee proof_health.json || (echo "Health check FAILED"; exit 1)
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3267874Z [36;1mcurl --max-time 30 -f -sf http://127.0.0.1:8000/health/ | tee proof_health.json || (echo "Health check FAILED"; exit 1)[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268216Z [36;1mecho ""[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268443Z [36;1mecho "--- build_sha in health response ---"[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268657Z [36;1mpython3 -c "[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3268845Z [36;1mimport json, sys[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269050Z [36;1mtry:[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269291Z [36;1m    d = json.load(open('proof_health.json'))[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269501Z [36;1m    sha = d.get('build_sha', 'MISSING')[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269748Z [36;1m    status = d.get('status', 'MISSING')[0m

===== MATCH: line 788 =====
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3269984Z [36;1m    print(f'build_sha={sha}')[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3270210Z [36;1m    print(f'status={status}')[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3270528Z [36;1m    if sha == 'MISSING':[0m
proof-ceremony	UNKNOWN STEP	2026-05-25T00:46:09.3270733Z [36;1m        sys.exit(1)[0m

## Run 26377212325
- Workflow: Tests
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26377212325
- Branch: stage2-slice11-billing-role-guard
- SHA: 6f75892aa31cf8e6a8eab6d18fa18ba5bf03a1ca
- Status/Conclusion: completed/failure
- First failing job: pytest
- First failing job databaseId: 77639496456
- First failing step: Run tests
- Raw log: audit-artifacts\known-unknowns\workflow-logs\run_26377212325_job_77639496456_raw.log
- Signature extract: audit-artifacts\known-unknowns\workflow-logs\run_26377212325_job_77639496456_signature.txt

- Signature preview (first 80 lines):
===== MATCH: line 490 =====
pytest	UNKNOWN STEP	2026-05-25T00:48:49.4717243Z ........................................................................ [ 93%]
pytest	UNKNOWN STEP	2026-05-25T00:48:51.2007104Z ........................................................................ [ 95%]
pytest	UNKNOWN STEP	2026-05-25T00:49:14.6939472Z ........................................................................ [ 98%]
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3504215Z ..........................................................               [100%]
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3505244Z =================================== FAILURES ===================================
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3509966Z ____________________ test_billing_run_summary_gross_aid_net ____________________
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3510424Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3510607Z     def test_billing_run_summary_gross_aid_net():
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3511133Z         school = School.objects.create(name="Test School")
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3511780Z         hh = Household.objects.create(school_id=school.id, name="Household")
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3512678Z     
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3513528Z         run = BillingRun.objects.create(school_id=school.id, term="2026-FALL", run_type="TUITION", description="Run", amount_per_student=Decimal("0.00"))
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3514896Z         inv = Invoice.objects.create(school_id=school.id, billing_run=run, household=hh, total_amount=Decimal("1000.00"))

===== MATCH: line 517 =====
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3524559Z >       assert resp.status_code == 200
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3524936Z E       assert 403 == 200
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3525428Z E        +  where 403 = <Response status_code=403, "application/json">.status_code
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3525884Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3526126Z billing/tests/test_billing_summary_api.py:45: AssertionError
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3526780Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3527859Z [24/May/2026 20:36:40,196] WARNING django.request: Forbidden: /api/v1/billing/runs/3ac0b566-7509-4300-a0cf-ae3facf25a9a/summary/
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3529164Z __ BillingInstallmentPlansRbacTests.test_non_staff_can_post_installment_plan ___
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3529706Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3530389Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_non_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3531229Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3531427Z     def test_non_staff_can_post_installment_plan(self):
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3532049Z         """

===== MATCH: line 539 =====
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3536810Z             HTTP_X_SCHOOL_ID=str(self.school.id),
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3537221Z         )
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3537485Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3537846Z             resp.status_code, (401, 403, 500),
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3538506Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539129Z         )
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539831Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540554Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540806Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3541461Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3542494Z [24/May/2026 20:38:51,748] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543433Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543979Z 

===== MATCH: line 541 =====
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3537485Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3537846Z             resp.status_code, (401, 403, 500),
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3538506Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539129Z         )
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539831Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540554Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540806Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3541461Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3542494Z [24/May/2026 20:38:51,748] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543433Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543979Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3544653Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3545470Z 

===== MATCH: line 543 =====
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3538506Z             msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539129Z         )
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3539831Z E       AssertionError: 403 unexpectedly found in (401, 403, 500) : Non-staff installment plan POST unexpectedly blocked: 403.
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540554Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3540806Z crown_api/tests/test_rbac_matrix_writes.py:181: AssertionError
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3541461Z ----------------------------- Captured stderr call -----------------------------
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3542494Z [24/May/2026 20:38:51,748] WARNING django.request: Forbidden: /api/v1/billing/installment-plans/
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543433Z ____ BillingInstallmentPlansRbacTests.test_staff_can_post_installment_plan _____
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3543979Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3544653Z self = <crown_api.tests.test_rbac_matrix_writes.BillingInstallmentPlansRbacTests testMethod=test_staff_can_post_installment_plan>
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3545470Z 
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3545656Z     def test_staff_can_post_installment_plan(self):
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3546517Z         """Staff: same as non-staff ΓÇö endpoint is not staff-gated."""

===== MATCH: line 561 =====
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3549148Z             HTTP_X_SCHOOL_ID=str(self.school.id),
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3549607Z         )
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3549897Z >       self.assertNotIn(
pytest	UNKNOWN STEP	2026-05-25T00:49:31.3550472Z             resp.status_code, (401, 403, 500),

## Run 26389898494
- Workflow: prod-integrity-proof
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26389898494
- Branch: main
- SHA: 7af6c4917cd820d0402b0a98442b1e4986c6cd1d
- Status/Conclusion: completed/failure
- First failing job: prove
- First failing job databaseId: 77676846712
- First failing step: Assert deployed SHA matches expected
- Raw log: audit-artifacts\known-unknowns\workflow-logs\run_26389898494_job_77676846712_raw.log
- Signature extract: audit-artifacts\known-unknowns\workflow-logs\run_26389898494_job_77676846712_signature.txt

- Signature preview (first 80 lines):
===== MATCH: line 109 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.4737339Z [36;1mfi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4737505Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4737691Z [36;1m# Pull defaults from JSON[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4737966Z [36;1mdefault_tag="$(jq -r '.tag' "$FILE")"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4738326Z [36;1mdefault_expected_sha="$(jq -r '.expected_sha' "$FILE")"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4738721Z [36;1mdefault_health_url="$(jq -r '.health_url' "$FILE")"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739018Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739210Z [36;1m# Manual inputs (may be empty)[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739464Z [36;1min_tag=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739716Z [36;1min_expected_sha=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739967Z [36;1min_health_url=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740453Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740934Z [36;1m# Resolve final values (manual overrides only if non-empty)[0m

===== MATCH: line 114 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.4738721Z [36;1mdefault_health_url="$(jq -r '.health_url' "$FILE")"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739018Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739210Z [36;1m# Manual inputs (may be empty)[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739464Z [36;1min_tag=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739716Z [36;1min_expected_sha=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739967Z [36;1min_health_url=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740453Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740934Z [36;1m# Resolve final values (manual overrides only if non-empty)[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741294Z [36;1mtag="$default_tag"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741548Z [36;1mexpected_sha="$default_expected_sha"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741837Z [36;1mhealth_url="$default_health_url"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742088Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742307Z [36;1mif [[ -n "${in_tag:-}" ]]; then tag="$in_tag"; fi[0m

===== MATCH: line 119 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.4739967Z [36;1min_health_url=""[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740453Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4740934Z [36;1m# Resolve final values (manual overrides only if non-empty)[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741294Z [36;1mtag="$default_tag"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741548Z [36;1mexpected_sha="$default_expected_sha"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741837Z [36;1mhealth_url="$default_health_url"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742088Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742307Z [36;1mif [[ -n "${in_tag:-}" ]]; then tag="$in_tag"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742712Z [36;1mif [[ -n "${in_expected_sha:-}" ]]; then expected_sha="$in_expected_sha"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743168Z [36;1mif [[ -n "${in_health_url:-}" ]]; then health_url="$in_health_url"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743524Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743715Z [36;1mecho "tag=$tag" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4744055Z [36;1mecho "expected_sha=$expected_sha" >> "$GITHUB_OUTPUT"[0m

===== MATCH: line 123 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741548Z [36;1mexpected_sha="$default_expected_sha"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4741837Z [36;1mhealth_url="$default_health_url"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742088Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742307Z [36;1mif [[ -n "${in_tag:-}" ]]; then tag="$in_tag"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742712Z [36;1mif [[ -n "${in_expected_sha:-}" ]]; then expected_sha="$in_expected_sha"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743168Z [36;1mif [[ -n "${in_health_url:-}" ]]; then health_url="$in_health_url"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743524Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743715Z [36;1mecho "tag=$tag" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4744055Z [36;1mecho "expected_sha=$expected_sha" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4744428Z [36;1mecho "health_url=$health_url" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4783819Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
prove	UNKNOWN STEP	2026-05-25T07:55:03.4784204Z ##[endgroup]
prove	UNKNOWN STEP	2026-05-25T07:55:03.4991033Z ##[group]Run set -euo pipefail

===== MATCH: line 127 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.4742712Z [36;1mif [[ -n "${in_expected_sha:-}" ]]; then expected_sha="$in_expected_sha"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743168Z [36;1mif [[ -n "${in_health_url:-}" ]]; then health_url="$in_health_url"; fi[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743524Z [36;1m[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4743715Z [36;1mecho "tag=$tag" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4744055Z [36;1mecho "expected_sha=$expected_sha" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4744428Z [36;1mecho "health_url=$health_url" >> "$GITHUB_OUTPUT"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4783819Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
prove	UNKNOWN STEP	2026-05-25T07:55:03.4784204Z ##[endgroup]
prove	UNKNOWN STEP	2026-05-25T07:55:03.4991033Z ##[group]Run set -euo pipefail
prove	UNKNOWN STEP	2026-05-25T07:55:03.4991386Z [36;1mset -euo pipefail[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4991847Z [36;1murl="https://crown-api-prod.azurewebsites.net/api/health/"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4992222Z [36;1mecho "Hitting: $url"[0m
prove	UNKNOWN STEP	2026-05-25T07:55:03.4992500Z [36;1mbody="$(curl --max-time 30 -f -sSfL "$url")"[0m

===== MATCH: line 143 =====
prove	UNKNOWN STEP	2026-05-25T07:55:03.5025523Z ##[endgroup]
prove	UNKNOWN STEP	2026-05-25T07:55:03.5077650Z Hitting: https://crown-api-prod.azurewebsites.net/api/health/
prove	UNKNOWN STEP	2026-05-25T07:55:04.6461347Z ##[group]Run set -euo pipefail
prove	UNKNOWN STEP	2026-05-25T07:55:04.6461723Z [36;1mset -euo pipefail[0m

## Run 26287002027
- Workflow: Tests
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26287002027
- Branch: admissions-followups-20260522
- SHA: 82c2b0f38baa3ff44c1df1d9ede72bf21120a4a6
- Status/Conclusion: completed/failure
- First failing job: pytest
- First failing job databaseId: 77377075574
- First failing step: Run tests
- Raw log: audit-artifacts\known-unknowns\workflow-logs\run_26287002027_job_77377075574_raw.log
- Signature extract: audit-artifacts\known-unknowns\workflow-logs\run_26287002027_job_77377075574_signature.txt

- Signature preview (first 80 lines):
===== MATCH: line 490 =====
pytest	Run tests	2026-05-22T12:26:37.2847742Z ........................................................................ [ 94%]
pytest	Run tests	2026-05-22T12:26:46.7524209Z ........................................................................ [ 96%]
pytest	Run tests	2026-05-22T12:27:06.3230507Z ........................................................................ [ 99%]
pytest	Run tests	2026-05-22T12:27:14.7639476Z ..............................                                           [100%]
pytest	Run tests	2026-05-22T12:27:14.7640093Z =================================== FAILURES ===================================
pytest	Run tests	2026-05-22T12:27:14.7640835Z _ TestWizardCreateSession.test_all_wizards_create_session (wizard='enrollment_conversion') _
pytest	Run tests	2026-05-22T12:27:14.7641400Z 
pytest	Run tests	2026-05-22T12:27:14.7641845Z self = <tests.test_wizard_contract.TestWizardCreateSession testMethod=test_all_wizards_create_session>
pytest	Run tests	2026-05-22T12:27:14.7642447Z 
pytest	Run tests	2026-05-22T12:27:14.7642599Z     def test_all_wizards_create_session(self):
pytest	Run tests	2026-05-22T12:27:14.7643088Z         for description, url in WIZARD_ENDPOINTS:
pytest	Run tests	2026-05-22T12:27:14.7643517Z             with self.subTest(wizard=description):
pytest	Run tests	2026-05-22T12:27:14.7643969Z >               self._assert_201(description, url)

===== MATCH: line 504 =====
pytest	Run tests	2026-05-22T12:27:14.7644396Z tests/test_wizard_contract.py:157: 
pytest	Run tests	2026-05-22T12:27:14.7644835Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pytest	Run tests	2026-05-22T12:27:14.7645350Z tests/test_wizard_contract.py:145: in _assert_201
pytest	Run tests	2026-05-22T12:27:14.7645769Z     self.assertEqual(
pytest	Run tests	2026-05-22T12:27:14.7646740Z E   AssertionError: 403 != 201 : enrollment_conversion (/api/v1/enrollment-conversion-wizard/sessions/): expected 201, got 403. Body: {'detail': 'Permission denied.'}
pytest	Run tests	2026-05-22T12:27:14.7647659Z _ TestWizardTenantIsolation.test_all_wizards_isolate_tenants (wizard='enrollment_conversion') _
pytest	Run tests	2026-05-22T12:27:14.7648021Z 
pytest	Run tests	2026-05-22T12:27:14.7648323Z self = <tests.test_wizard_contract.TestWizardTenantIsolation testMethod=test_all_wizards_isolate_tenants>
pytest	Run tests	2026-05-22T12:27:14.7649015Z 
pytest	Run tests	2026-05-22T12:27:14.7649130Z     def test_all_wizards_isolate_tenants(self):
pytest	Run tests	2026-05-22T12:27:14.7649774Z         for description, url in WIZARD_ENDPOINTS:
pytest	Run tests	2026-05-22T12:27:14.7650079Z             with self.subTest(wizard=description):
pytest	Run tests	2026-05-22T12:27:14.7650454Z >               self._assert_tenant_isolation(description, url)

===== MATCH: line 517 =====
pytest	Run tests	2026-05-22T12:27:14.7650738Z 
pytest	Run tests	2026-05-22T12:27:14.7650834Z tests/test_wizard_contract.py:194: 
pytest	Run tests	2026-05-22T12:27:14.7651128Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pytest	Run tests	2026-05-22T12:27:14.7651501Z tests/test_wizard_contract.py:179: in _assert_tenant_isolation
pytest	Run tests	2026-05-22T12:27:14.7651987Z     self.assertEqual(r.status_code, 201, f"{description}: session creation failed {r.status_code}")
pytest	Run tests	2026-05-22T12:27:14.7652523Z E   AssertionError: 403 != 201 : enrollment_conversion: session creation failed 403
pytest	Run tests	2026-05-22T12:27:14.7652929Z =============================== warnings summary ===============================
pytest	Run tests	2026-05-22T12:27:14.7653514Z backend/crown_api/exports/tests/test_exports_jwt_auth.py: 1 warning
pytest	Run tests	2026-05-22T12:27:14.7653952Z backend/onboarding/tests/test_parent_enrollment_guidance.py: 8 warnings
pytest	Run tests	2026-05-22T12:27:14.7654335Z backend/onboarding/tests/test_views.py: 23 warnings
pytest	Run tests	2026-05-22T12:27:14.7654672Z backend/reenrollment/tests/test_views.py: 27 warnings
pytest	Run tests	2026-05-22T12:27:14.7654993Z backend/tests/test_ensure_ci_user_api.py: 2 warnings
pytest	Run tests	2026-05-22T12:27:14.7655912Z   /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/jwt/api_jwt.py:147: InsecureKeyLengthWarning: The HMAC key is 18 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2.

===== MATCH: line 518 =====
pytest	Run tests	2026-05-22T12:27:14.7650834Z tests/test_wizard_contract.py:194: 
pytest	Run tests	2026-05-22T12:27:14.7651128Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pytest	Run tests	2026-05-22T12:27:14.7651501Z tests/test_wizard_contract.py:179: in _assert_tenant_isolation
pytest	Run tests	2026-05-22T12:27:14.7651987Z     self.assertEqual(r.status_code, 201, f"{description}: session creation failed {r.status_code}")
pytest	Run tests	2026-05-22T12:27:14.7652523Z E   AssertionError: 403 != 201 : enrollment_conversion: session creation failed 403
pytest	Run tests	2026-05-22T12:27:14.7652929Z =============================== warnings summary ===============================
pytest	Run tests	2026-05-22T12:27:14.7653514Z backend/crown_api/exports/tests/test_exports_jwt_auth.py: 1 warning
pytest	Run tests	2026-05-22T12:27:14.7653952Z backend/onboarding/tests/test_parent_enrollment_guidance.py: 8 warnings
pytest	Run tests	2026-05-22T12:27:14.7654335Z backend/onboarding/tests/test_views.py: 23 warnings
pytest	Run tests	2026-05-22T12:27:14.7654672Z backend/reenrollment/tests/test_views.py: 27 warnings
pytest	Run tests	2026-05-22T12:27:14.7654993Z backend/tests/test_ensure_ci_user_api.py: 2 warnings
pytest	Run tests	2026-05-22T12:27:14.7655912Z   /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/jwt/api_jwt.py:147: InsecureKeyLengthWarning: The HMAC key is 18 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2.
pytest	Run tests	2026-05-22T12:27:14.7656798Z     return self._jws.encode(

===== MATCH: line 551 =====
pytest	Run tests	2026-05-22T12:27:14.7667751Z SKIPPED [1] billing/tests/test_lane2_billing_smoke.py:25: DEMO school id not available (set settings.DEMO_SCHOOL_ID or env CROWN_DEMO_SCHOOL_ID)
pytest	Run tests	2026-05-22T12:27:14.7668826Z SKIPPED [1] billing/tests/test_lane2_payment_endpoints.py:13: DEMO school id not available (set settings.DEMO_SCHOOL_ID or env CROWN_DEMO_SCHOOL_ID)
pytest	Run tests	2026-05-22T12:27:14.7669645Z SKIPPED [1] classroom/tests/test_classroom_api.py:12: No school in database
pytest	Run tests	2026-05-22T12:27:14.7670089Z SKIPPED [1] classroom/tests/test_classroom_api.py:30: No school in database
pytest	Run tests	2026-05-22T12:27:14.7671282Z SUBFAILED(wizard='enrollment_conversion') tests/test_wizard_contract.py::TestWizardCreateSession::test_all_wizards_create_session - AssertionError: 403 != 201 : enrollment_conversion (/api/v1/enrollment-conversion-wizard/sessions/): expected 201, got 403. Body: {'detail': 'Permission denied.'}
pytest	Run tests	2026-05-22T12:27:14.7672902Z SUBFAILED(wizard='enrollment_conversion') tests/test_wizard_contract.py::TestWizardTenantIsolation::test_all_wizards_isolate_tenants - AssertionError: 403 != 201 : enrollment_conversion: session creation failed 403
pytest	Run tests	2026-05-22T12:27:14.7673972Z 2 failed, 3030 passed, 9 skipped, 122 warnings, 86 subtests passed in 865.93s (0:14:25)
pytest	Run tests	2026-05-22T12:27:16.1371037Z ##[error]Process completed with exit code 1.
pytest	Post Run actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11	∩╗┐2026-05-22T12:27:16.1484069Z Post job cleanup.
pytest	Post Run actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11	2026-05-22T12:27:16.2276594Z [command]/usr/bin/git version
pytest	Post Run actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11	2026-05-22T12:27:16.2314622Z git version 2.54.0
pytest	Post Run actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11	2026-05-22T12:27:16.2356856Z Temporarily overriding HOME='/home/runner/work/_temp/7ded0d89-b05c-473f-92d8-e938d7356926' before making global git config changes
pytest	Post Run actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11	2026-05-22T12:27:16.2358075Z Adding repository directory to the temporary git global config as a safe directory

===== MATCH: line 552 =====
pytest	Run tests	2026-05-22T12:27:14.7668826Z SKIPPED [1] billing/tests/test_lane2_payment_endpoints.py:13: DEMO school id not available (set settings.DEMO_SCHOOL_ID or env CROWN_DEMO_SCHOOL_ID)
pytest	Run tests	2026-05-22T12:27:14.7669645Z SKIPPED [1] classroom/tests/test_classroom_api.py:12: No school in database
pytest	Run tests	2026-05-22T12:27:14.7670089Z SKIPPED [1] classroom/tests/test_classroom_api.py:30: No school in database
pytest	Run tests	2026-05-22T12:27:14.7671282Z SUBFAILED(wizard='enrollment_conversion') tests/test_wizard_contract.py::TestWizardCreateSession::test_all_wizards_create_session - AssertionError: 403 != 201 : enrollment_conversion (/api/v1/enrollment-conversion-wizard/sessions/): expected 201, got 403. Body: {'detail': 'Permission denied.'}

