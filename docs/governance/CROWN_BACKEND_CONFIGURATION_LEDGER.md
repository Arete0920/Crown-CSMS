# CROWN Backend Configuration Ledger

**Document ID:** CROWN-GOV-007  
**Status:** ACTIVE — Stage 1 Census in Progress  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Repository evidence SHA:** `fc4d6907a079efb3f8aedbd041c11d8f01a218f4`  
**Verification date:** 2026-07-24  
**Controlling issue:** #1587

## Purpose

Record the exact configured Django application, middleware and top-level URL population at the evidence SHA. Configuration presence proves only that Django is instructed to load or route the item. It does not prove migrations, business correctness, tenant safety, permission safety, frontend reachability, deployed availability or production authorization.

## Verified counts

| Configuration surface | Exact count | Source |
|---|---:|---|
| Explicit `INSTALLED_APPS` entries | 67 | `backend/crown_api/settings.py` |
| Registry-derived wizard apps | 28 | `backend/crown_api/wizard_registry.py` |
| Total configured Django apps | 95 | `67 + 28` |
| Middleware components | 18 | `backend/crown_api/settings.py` |
| Always-registered root URL patterns | 73 | `backend/crown_api/urls.py` |
| Optional root URL patterns | 1 | `release_closeout.urls`, only when importable |
| Always-registered patterns inside `api_v1_urls` | 47 | `backend/crown_api/api_v1_urls.py` |
| Optional `api_v1_urls` patterns | 1 | `crm_marketing.api.urls`, only when importable |

No exact duplicate app-config string was identified during the row-by-row comparison of the 67 explicit entries and 28 wizard registry entries. Django app-label uniqueness and runtime loading remain separate executable checks.

## Explicit `INSTALLED_APPS` ledger

| # | Configured entry | Configuration class |
|---:|---|---|
| 1 | `django.contrib.admin` | Django framework |
| 2 | `django.contrib.auth` | Django framework |
| 3 | `django.contrib.contenttypes` | Django framework |
| 4 | `django.contrib.sessions` | Django framework |
| 5 | `django.contrib.messages` | Django framework |
| 6 | `django.contrib.staticfiles` | Django framework |
| 7 | `corsheaders` | Third-party |
| 8 | `rest_framework` | Third-party |
| 9 | `drf_spectacular` | Third-party |
| 10 | `drf_spectacular_sidecar` | Third-party |
| 11 | `crown_api` | Project explicit |
| 12 | `crown_api.exports` | Project explicit |
| 13 | `core` | Project explicit |
| 14 | `sandbox_demo.apps.SandboxDemoConfig` | Project explicit |
| 15 | `curriculum` | Project explicit |
| 16 | `apps.compliance.apps.ComplianceConfig` | Project explicit |
| 17 | `apps.accounting.apps.AccountingConfig` | Project explicit |
| 18 | `finance.apps.FinanceConfig` | Project explicit |
| 19 | `aid.apps.AidConfig` | Project explicit |
| 20 | `admissions.apps.AdmissionsConfig` | Project explicit |
| 21 | `households` | Project explicit |
| 22 | `applications` | Project explicit |
| 23 | `learning_continuity.apps.LearningContinuityConfig` | Project explicit |
| 24 | `ledger.apps.LedgerConfig` | Project explicit |
| 25 | `journal` | Project explicit |
| 26 | `integrations` | Project explicit |
| 27 | `financial_aid.apps.FinancialAidConfig` | Project explicit |
| 28 | `academics` | Project explicit |
| 29 | `academics_ro` | Project explicit |
| 30 | `curricula` | Project explicit |
| 31 | `classroom` | Project explicit |
| 32 | `gradebook` | Project explicit |
| 33 | `billing` | Project explicit |
| 34 | `audit` | Project explicit |
| 35 | `solomon` | Project explicit |
| 36 | `discipline` | Project explicit |
| 37 | `servicehours` | Project explicit |
| 38 | `comms` | Project explicit |
| 39 | `student_records.apps.StudentRecordsConfig` | Project explicit |
| 40 | `student360` | Project explicit |
| 41 | `parent360` | Project explicit |
| 42 | `executive360` | Project explicit |
| 43 | `graduation` | Project explicit |
| 44 | `hr.apps.HrConfig` | Project explicit |
| 45 | `advancement.apps.AdvancementConfig` | Project explicit |
| 46 | `pdhub.apps.PdhubConfig` | Project explicit |
| 47 | `safety.apps.SafetyConfig` | Project explicit |
| 48 | `integrations_real.apps.IntegrationsRealConfig` | Project explicit |
| 49 | `spiritual_life.apps.SpiritualLifeConfig` | Project explicit |
| 50 | `portrait.apps.PortraitConfig` | Project explicit |
| 51 | `outreach.apps.OutreachConfig` | Project explicit |
| 52 | `athletics.apps.AthleticsConfig` | Project explicit |
| 53 | `facops.apps.FacopsConfig` | Project explicit |
| 54 | `transportation.apps.TransportationConfig` | Project explicit |
| 55 | `msauth.apps.MsauthConfig` | Project explicit |
| 56 | `board_oversight` | Project explicit |
| 57 | `tenants.apps.TenantsConfig` | Project explicit |
| 58 | `platform_ops.apps.PlatformOpsConfig` | Project explicit |
| 59 | `payments.apps.PaymentsConfig` | Project explicit |
| 60 | `subscriptions.apps.SubscriptionsConfig` | Project explicit |
| 61 | `signals` | Project explicit |
| 62 | `aftercare` | Project explicit |
| 63 | `summer_camp` | Project explicit |
| 64 | `home_academy.apps.HomeAcademyConfig` | Project explicit |
| 65 | `finance_setup.apps.FinanceSetupConfig` | Project explicit |
| 66 | `support.apps.SupportConfig` | Project explicit |
| 67 | `analytics.apps.AnalyticsConfig` | Project explicit |

The 67 explicit entries comprise six Django framework apps, four third-party apps and 57 project-controlled explicit entries.

## Registry-derived wizard app ledger

| Overall # | Wizard # | Configured app | Registry title |
|---:|---:|---|---|
| 68 | 1 | `onboarding.apps.OnboardingConfig` | Student Onboarding |
| 69 | 2 | `reenrollment.apps.ReenrollmentConfig` | Re-enrollment |
| 70 | 3 | `billing_wizard.apps.BillingWizardConfig` | Billing Setup |
| 71 | 4 | `financial_aid_wizard.apps.FinancialAidWizardConfig` | Financial Aid Setup |
| 72 | 5 | `scheduling_wizard.apps.SchedulingWizardConfig` | Scheduling Setup |
| 73 | 6 | `comms_wizard.apps.CommsWizardConfig` | Communications Campaign |
| 74 | 7 | `section_assign_wizard.apps.SectionAssignWizardConfig` | Section Assignments |
| 75 | 8 | `bell_schedule_wizard.apps.BellScheduleWizardConfig` | Bell Schedule |
| 76 | 9 | `gradebook_setup_wizard.apps.GradebookSetupWizardConfig` | Gradebook Setup |
| 77 | 10 | `attendance_rules_wizard.apps.AttendanceRulesWizardConfig` | Attendance Rules |
| 78 | 11 | `enrollment_conversion_wizard.apps.EnrollmentConversionWizardConfig` | Enrollment Conversion |
| 79 | 12 | `invoice_run_wizard.apps.InvoiceRunWizardConfig` | Invoice Run |
| 80 | 13 | `staff_onboarding_wizard.apps.StaffOnboardingWizardConfig` | Staff Onboarding |
| 81 | 14 | `fee_schedule_wizard.apps.FeeScheduleWizardConfig` | Fee Schedule Setup |
| 82 | 15 | `academic_year_wizard.apps.AcademicYearWizardConfig` | Academic Year Rollover |
| 83 | 16 | `enrollment_period_wizard.apps.EnrollmentPeriodWizardConfig` | Enrollment Period Setup |
| 84 | 17 | `grade_scale_wizard.apps.GradeScaleWizardConfig` | Grade Scale Setup |
| 85 | 18 | `term_structure_wizard.apps.TermStructureWizardConfig` | Term Structure Setup |
| 86 | 19 | `section_scheduler_wizard.apps.SectionSchedulerWizardConfig` | Section Scheduler Seed |
| 87 | 20 | `staff_setup_wizard.apps.StaffSetupWizardConfig` | Staff & Roles Setup |
| 88 | 21 | `course_catalog_wizard.apps.CourseCatalogWizardConfig` | Course Catalog Setup |
| 89 | 22 | `room_setup_wizard.apps.RoomSetupWizardConfig` | Rooms Setup |
| 90 | 23 | `promotion_wizard.apps.PromotionWizardConfig` | Promotion Map Setup |
| 91 | 24 | `student_import_wizard.apps.StudentImportWizardConfig` | Student Import |
| 92 | 25 | `guardian_household_wizard.apps.GuardianHouseholdWizardConfig` | Guardian & Household Setup |
| 93 | 26 | `section_staffing_wizard.apps.SectionStaffingWizardConfig` | Section Staffing |
| 94 | 27 | `attendance_codes_wizard.apps.AttendanceCodesWizardConfig` | Attendance Codes Setup |
| 95 | 28 | `grade_weights_wizard.apps.GradeWeightsWizardConfig` | Grade Weights & Categories |

The source comments skip historical display numbers 19 and then label the final entries 20 through 29. The executable list itself contains 28 entries. This ledger uses sequential executable positions 1 through 28 and does not treat comment numbering as an additional wizard.

## Middleware ledger

| Order | Middleware |
|---:|---|
| 1 | `core.middleware.DemoWriteBlockMiddleware` |
| 2 | `crown_api.middleware.api_exceptions.ApiExceptionMiddleware` |
| 3 | `crown_api.middleware.performance.PerformanceMiddleware` |
| 4 | `crown_api.middleware.api_version.APIVersionMiddleware` |
| 5 | `corsheaders.middleware.CorsMiddleware` |
| 6 | `django.middleware.security.SecurityMiddleware` |
| 7 | `django.contrib.sessions.middleware.SessionMiddleware` |
| 8 | `django.middleware.common.CommonMiddleware` |
| 9 | `django.middleware.csrf.CsrfViewMiddleware` |
| 10 | `django.contrib.auth.middleware.AuthenticationMiddleware` |
| 11 | `core.observability.middleware.RequestCorrelationMiddleware` |
| 12 | `core.middleware.TenantIsolationMiddleware` |
| 13 | `crown_api.auth_middleware.JwtAuthMiddleware` |
| 14 | `core.tenant_header_middleware.TenantHeaderRequiredMiddleware` |
| 15 | `crown_api.tenant_middleware.TenantContextMiddleware` |
| 16 | `audit.middleware.AuditMiddleware` |
| 17 | `django.contrib.messages.middleware.MessageMiddleware` |
| 18 | `django.middleware.clickjacking.XFrameOptionsMiddleware` |

Three separate tenant-related middleware components are active at positions 12, 14 and 15. Their coexistence is configuration fact; consolidated behavior and ordering correctness remain open evidence requirements.

## Root URL population

`backend/crown_api/urls.py` defines:

- 44 explicit patterns inside the initial `urlpatterns` list;
- 28 registry-expanded wizard patterns;
- one subsequently appended Django admin pattern;
- one optional `release_closeout.urls` include when the module is importable.

This yields 73 always-registered top-level patterns and up to 74 when the optional closeout package is present.

## Canonical API-v1 population

`backend/crown_api/api_v1_urls.py` defines 47 always-registered patterns and conditionally inserts one CRM Marketing pattern when `crm_marketing.api.urls` is importable.

The same URLConf is included under both root prefixes:

- `/api/v1/` — canonical;
- `/api/` — compatibility alias.

Therefore, the 47 always-registered API-v1 patterns are exposed through both prefix families unless an earlier root pattern wins Django's first-match resolution. The optional CRM pattern is likewise dual-prefixed when installed.

## Accuracy boundaries and next verification

This ledger verifies configuration strings and configured pattern counts at the evidence SHA. The following remain unresolved:

1. whether every configured app imports and migrates successfully in every supported environment;
2. exact model, migration, service, serializer, command, signal, task and URL leaves for each project app;
3. canonical ownership for overlapping packages such as `curriculum`/`curricula`, `finance`/`aid`/`financial_aid`, `integrations`/`integrations_real`, and `core`/`households`;
4. tenant, permission, audit and entitlement behavior for every route;
5. optional-package presence by deployment environment;
6. runtime parity between canonical `/api/v1/` paths and `/api/` compatibility aliases.
