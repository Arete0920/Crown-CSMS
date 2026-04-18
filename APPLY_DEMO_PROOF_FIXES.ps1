$ErrorActionPreference = "Stop"

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path ".").Path + "\" + $Path, $Content.Replace("`r`n", "`n").Replace("`n", [Environment]::NewLine), $utf8NoBom)
    Write-Host "[OK] wrote $Path" -ForegroundColor Green
}

$loadHeritageDemo = @'
import os
from typing import Iterable, Optional, Tuple

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify


def has_field(model, field_name: str) -> bool:
    return any(f.name == field_name for f in model._meta.get_fields())


def resolve_model(candidates: Iterable[Tuple[str, str]]):
    for app_label, model_name in candidates:
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            continue
    return None


def first_existing_attr(obj, names, default=None):
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


class Command(BaseCommand):
    help = "Loads Heritage Christian Academy demo identities and baseline school-scoped data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset demo account passwords even if the users already exist.",
        )

    def _pick_school_model(self):
        return resolve_model(
            [
                ("schools", "School"),
                ("tenants", "Tenant"),
                ("core", "School"),
                ("core", "Tenant"),
            ]
        )

    def _pick_student_model(self):
        return resolve_model(
            [
                ("students", "Student"),
                ("sis", "Student"),
                ("core", "Student"),
            ]
        )

    def _pick_application_model(self):
        return resolve_model(
            [
                ("admissions", "Application"),
                ("admissions", "AdmissionApplication"),
            ]
        )

    def _pick_invoice_model(self):
        return resolve_model(
            [
                ("billing", "Invoice"),
                ("finance", "Invoice"),
            ]
        )

    def _pick_attendance_model(self):
        return resolve_model(
            [
                ("attendance", "AttendanceRecord"),
                ("attendance", "Attendance"),
            ]
        )

    def _set_schoolish_fields(self, instance, school_name: str, school_slug: str, school_domain: str):
        if has_field(instance.__class__, "name"):
            instance.name = school_name
        if has_field(instance.__class__, "slug"):
            instance.slug = school_slug
        if has_field(instance.__class__, "domain"):
            instance.domain = school_domain
        if has_field(instance.__class__, "is_active"):
            instance.is_active = True
        if has_field(instance.__class__, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = timezone.now()

    def _link_user_to_school(self, user, school, role: Optional[str] = None):
        updated = False

        if hasattr(user, "profile") and user.profile is not None:
            profile = user.profile
            if has_field(profile.__class__, "school"):
                profile.school = school
                updated = True
            elif has_field(profile.__class__, "tenant"):
                profile.tenant = school
                updated = True

            if role and has_field(profile.__class__, "role"):
                profile.role = role
                updated = True

            if updated:
                profile.save()

        if has_field(user.__class__, "school"):
            user.school = school
            updated = True
        elif has_field(user.__class__, "tenant"):
            user.tenant = school
            updated = True

        if role and has_field(user.__class__, "role"):
            user.role = role
            updated = True

        if updated:
            user.save()

    def _create_or_update_user(self, school, email, password, first_name, last_name, is_staff=False, role=None, reset_passwords=False):
        User = get_user_model()

        lookup = {"email": email} if has_field(User, "email") else {"username": email}
        defaults = {}

        if has_field(User, "first_name"):
            defaults["first_name"] = first_name
        if has_field(User, "last_name"):
            defaults["last_name"] = last_name
        if has_field(User, "is_staff"):
            defaults["is_staff"] = is_staff
        if has_field(User, "is_active"):
            defaults["is_active"] = True
        if has_field(User, "username") and "username" not in lookup:
            defaults["username"] = email

        user, created = User.objects.get_or_create(**lookup, defaults=defaults)

        changed = False
        for key, value in defaults.items():
            if getattr(user, key, None) != value:
                setattr(user, key, value)
                changed = True

        if created or reset_passwords or not user.check_password(password):
            user.set_password(password)
            changed = True

        if changed:
            user.save()

        self._link_user_to_school(user, school, role=role)

        self.stdout.write(self.style.SUCCESS(f"User ready: {email}"))
        return user

    def _try_seed_students(self, school):
        Student = self._pick_student_model()
        if Student is None:
            self.stdout.write(self.style.WARNING("Student model not found. Skipping student seed."))
            return 0

        created_count = 0
        demo_students = [
            ("Grace", "Anderson", "11"),
            ("Micah", "Bennett", "10"),
            ("Abigail", "Carter", "9"),
            ("Noah", "Dawson", "8"),
            ("Hannah", "Ellis", "7"),
            ("Caleb", "Foster", "6"),
            ("Sarah", "Garrett", "5"),
            ("Joshua", "Hayes", "4"),
            ("Lydia", "Irwin", "3"),
            ("Ethan", "Jones", "2"),
            ("Emma", "King", "1"),
            ("Daniel", "Lewis", "K"),
        ]

        school_field = "school" if has_field(Student, "school") else "tenant" if has_field(Student, "tenant") else None
        if school_field is None:
            self.stdout.write(self.style.WARNING("Student model has no school/tenant field. Skipping student seed."))
            return 0

        for first_name, last_name, grade_level in demo_students:
            lookup = {"first_name": first_name, "last_name": last_name, school_field: school}
            defaults = {}

            if has_field(Student, "grade_level"):
                defaults["grade_level"] = grade_level
            elif has_field(Student, "grade"):
                defaults["grade"] = grade_level

            if has_field(Student, "status"):
                defaults["status"] = "active"

            try:
                _, created = Student.objects.get_or_create(**lookup, defaults=defaults)
                if created:
                    created_count += 1
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Student seed skipped for {first_name} {last_name}: {exc}"))

        return created_count

    def _try_seed_applications(self, school):
        Application = self._pick_application_model()
        if Application is None:
            self.stdout.write(self.style.WARNING("Admissions application model not found. Skipping application seed."))
            return 0

        school_field = "school" if has_field(Application, "school") else "tenant" if has_field(Application, "tenant") else None
        if school_field is None:
            self.stdout.write(self.style.WARNING("Application model has no school/tenant field. Skipping application seed."))
            return 0

        created_count = 0
        applicants = [
            ("Olivia", "Moore", "6", "parent1@heritage.demo"),
            ("Benjamin", "Parker", "3", "parent2@heritage.demo"),
            ("Charlotte", "Reed", "8", "parent3@heritage.demo"),
            ("James", "Scott", "1", "parent4@heritage.demo"),
            ("Ella", "Turner", "K", "parent5@heritage.demo"),
        ]

        for first_name, last_name, grade_applying, parent_email in applicants:
            lookup = {"first_name": first_name, "last_name": last_name, school_field: school}
            defaults = {}

            if has_field(Application, "grade_applying"):
                defaults["grade_applying"] = grade_applying
            elif has_field(Application, "grade"):
                defaults["grade"] = grade_applying

            if has_field(Application, "school_year"):
                defaults["school_year"] = 2026
            if has_field(Application, "parent_email"):
                defaults["parent_email"] = parent_email
            if has_field(Application, "status"):
                defaults["status"] = "in_review"

            try:
                _, created = Application.objects.get_or_create(**lookup, defaults=defaults)
                if created:
                    created_count += 1
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Application seed skipped for {first_name} {last_name}: {exc}"))

        return created_count

    def _school_lookup(self, SchoolModel, school_name: str, school_slug: str, school_domain: str):
        if has_field(SchoolModel, "slug"):
            return {"slug": school_slug}
        if has_field(SchoolModel, "domain"):
            return {"domain": school_domain}
        if has_field(SchoolModel, "name"):
            return {"name": school_name}
        raise CommandError(f"Unable to identify lookup field for {SchoolModel.__name__}")

    @transaction.atomic
    def handle(self, *args, **options):
        reset_passwords = options["reset_passwords"]

        school_name = "Heritage Christian Academy"
        school_slug = slugify(school_name)
        school_domain = "heritage.demo.crown2026.local"

        admin_password = os.getenv("CROWN_DEMO_ADMIN_PASSWORD", "Admin2026!")
        principal_password = os.getenv("CROWN_DEMO_PRINCIPAL_PASSWORD", "Principal2026!")
        teacher_password = os.getenv("CROWN_DEMO_TEACHER_PASSWORD", "Teacher2026!")
        parent_password = os.getenv("CROWN_DEMO_PARENT_PASSWORD", "Parent2026!")
        student_password = os.getenv("CROWN_DEMO_STUDENT_PASSWORD", "Student2026!")
        playwright_password = os.getenv("CROWN_DEMO_PLAYWRIGHT_PASSWORD", "PlaywrightDemo1!")

        SchoolModel = self._pick_school_model()
        if SchoolModel is None:
            raise CommandError("No School/Tenant model found. Expected schools.School or tenants.Tenant.")

        lookup = self._school_lookup(SchoolModel, school_name, school_slug, school_domain)
        school, created = SchoolModel.objects.get_or_create(**lookup)
        self._set_schoolish_fields(school, school_name, school_slug, school_domain)
        school.save()

        self.stdout.write(self.style.SUCCESS(
            f"School ready: {first_existing_attr(school, ['name', 'slug', 'domain'], school_name)} "
            f"{'(created)' if created else '(existing)'}"
        ))

        self._create_or_update_user(
            school=school,
            email="admin@heritage.demo",
            password=admin_password,
            first_name="Administrator",
            last_name="Admin",
            is_staff=True,
            role="school_admin",
            reset_passwords=reset_passwords,
        )
        self._create_or_update_user(
            school=school,
            email="principal@heritage.demo",
            password=principal_password,
            first_name="Principal",
            last_name="User",
            is_staff=True,
            role="principal",
            reset_passwords=reset_passwords,
        )
        self._create_or_update_user(
            school=school,
            email="teacher@heritage.demo",
            password=teacher_password,
            first_name="Teacher",
            last_name="Smith",
            is_staff=True,
            role="teacher",
            reset_passwords=reset_passwords,
        )
        self._create_or_update_user(
            school=school,
            email="parent@heritage.demo",
            password=parent_password,
            first_name="Parent",
            last_name="Johnson",
            is_staff=False,
            role="parent",
            reset_passwords=reset_passwords,
        )
        self._create_or_update_user(
            school=school,
            email="student@heritage.demo",
            password=student_password,
            first_name="Student",
            last_name="Johnson",
            is_staff=False,
            role="student",
            reset_passwords=reset_passwords,
        )

        self._create_or_update_user(
            school=school,
            email="playwright@crown-demo.local",
            password=playwright_password,
            first_name="Demo",
            last_name="Director",
            is_staff=True,
            role="director",
            reset_passwords=reset_passwords,
        )

        student_count = self._try_seed_students(school)
        application_count = self._try_seed_applications(school)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Heritage Christian Academy demo scaffold loaded."))
        self.stdout.write(self.style.SUCCESS(f"Students created: {student_count}"))
        self.stdout.write(self.style.SUCCESS(f"Applications created: {application_count}"))
        self.stdout.write("")
        self.stdout.write("Demo credentials:")
        self.stdout.write(f"  admin@heritage.demo / {admin_password}")
        self.stdout.write(f"  principal@heritage.demo / {principal_password}")
        self.stdout.write(f"  teacher@heritage.demo / {teacher_password}")
        self.stdout.write(f"  parent@heritage.demo / {parent_password}")
        self.stdout.write(f"  student@heritage.demo / {student_password}")
        self.stdout.write(f"  playwright@crown-demo.local / {playwright_password}")
        self.stdout.write("")
        self.stdout.write("Note: this command creates baseline school, user, student, and admissions scaffolding.")
        self.stdout.write("Use existing billing/attendance/analytics seed paths next if those modules require richer domain fixtures.")
'@

$coreMgmtInit = @'
'@

$demoBanner = @'
import React from "react";

export default function DemoModeBanner() {
  const enabled =
    import.meta.env.VITE_DEMO_MODE === "1" ||
    import.meta.env.VITE_DEMO_MODE === "true";

  if (!enabled) return null;

  return (
    <div
      style={{
        width: "100%",
        background: "linear-gradient(90deg, #7c3aed 0%, #1d4ed8 100%)",
        color: "#ffffff",
        padding: "10px 16px",
        fontSize: "14px",
        fontWeight: 600,
        letterSpacing: "0.2px",
        borderBottom: "1px solid rgba(255,255,255,0.18)",
        position: "sticky",
        top: 0,
        zIndex: 1000,
      }}
    >
      Demo - Heritage Christian Academy - For demonstration purposes only
    </div>
  );
}
'@

$metricBadge = @'
import React from "react";

type Provenance = "live" | "seeded" | "mock";

export default function MetricProvenanceBadge({
  provenance = "live",
}: {
  provenance?: Provenance;
}) {
  const map: Record<Provenance, { label: string; bg: string; fg: string }> = {
    live:   { label: "Live",        bg: "#dcfce7", fg: "#166534" },
    seeded: { label: "Demo Seeded", bg: "#fef3c7", fg: "#92400e" },
    mock:   { label: "Mock",        bg: "#fee2e2", fg: "#991b1b" },
  };

  const item = map[provenance];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        background: item.bg,
        color: item.fg,
      }}
    >
      {item.label}
    </span>
  );
}
'@

$frontendWiringCheck = @'
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$src = Join-Path $RepoRoot "frontend\dashboards\src"
$out = Join-Path $RepoRoot "artifacts\demo-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

if (-not (Test-Path $src)) {
    throw "Missing frontend source path: $src"
}

$files = Get-ChildItem $src -Recurse -File | Where-Object {
    $_.Extension -in ".js", ".jsx", ".ts", ".tsx"
}

$routeDefPatterns = @(
    'path\s*:\s*["''](?<route>/[^"''\s]+)["'']',
    '<Route[^>]*\spath=["''](?<route>/[^"''\s]+)["'']'
)

$routeRefPatterns = @(
    '<Link[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    '<NavLink[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    'navigate\(\s*["''](?<route>/[^"''\s]+)["'']',
    'router\.push\(\s*["''](?<route>/[^"''\s]+)["'']',
    'href=\{?["''](?<route>/[^"''\s]+)["'']\}?'
)

function Normalize-Route([string]$route) {
    if ([string]::IsNullOrWhiteSpace($route)) { return $null }
    if ($route -match '^(https?:)?//') { return $null }
    if (-not $route.StartsWith('/')) { return $null }

    $route = $route.Split('?')[0].Split('#')[0]

    if ($route.Length -gt 1 -and $route.EndsWith('/')) {
        $route = $route.TrimEnd('/')
    }

    return $route
}

function Route-ToRegex([string]$route) {
    if ($route -eq "/") { return '^/$' }

    $escaped = [regex]::Escape($route)
    $escaped = $escaped -replace '\\:[A-Za-z0-9_]+', '[^/]+'
    $escaped = $escaped -replace '\\\*', '.*'
    return "^$escaped/?$"
}

$routeDefs = New-Object System.Collections.Generic.HashSet[string]
$routeRefs = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw

    foreach ($pattern in $routeDefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) { [void]$routeDefs.Add($route) }
        }
    }

    foreach ($pattern in $routeRefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) {
                $routeRefs.Add([pscustomobject]@{
                    File  = $file.FullName.Replace($RepoRoot, "").TrimStart("\")
                    Route = $route
                })
            }
        }
    }
}

$criticalRoutes = @(
    "/login",
    "/admin",
    "/admissions",
    "/finance",
    "/billing",
    "/financial-aid",
    "/academics",
    "/communications",
    "/board/executive"
)

foreach ($r in $criticalRoutes) { [void]$routeDefs.Add($r) }

$compiledDefs = $routeDefs | ForEach-Object {
    [pscustomobject]@{
        Route = $_
        Regex = Route-ToRegex $_
    }
}

$missing = foreach ($ref in $routeRefs) {
    $matched = $false
    foreach ($def in $compiledDefs) {
        if ($ref.Route -match $def.Regex) {
            $matched = $true
            break
        }
    }

    if (-not $matched) {
        [pscustomobject]@{
            Route = $ref.Route
            File  = $ref.File
            Problem = "Link target not matched by any declared route"
        }
    }
}

$declaredRoutesPath = Join-Path $out "declared-routes.txt"
$routeDefs | Sort-Object | Set-Content $declaredRoutesPath

$refsPath = Join-Path $out "route-references.csv"
$routeRefs | Sort-Object Route, File | Export-Csv $refsPath -NoTypeInformation

$missingPath = Join-Path $out "missing-routes.csv"
$missing | Sort-Object Route, File | Export-Csv $missingPath -NoTypeInformation

$summaryPath = Join-Path $out "wiring-summary.md"
@"
# Frontend Wiring Summary

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $src

## Counts
- Declared routes: $($routeDefs.Count)
- Route references: $($routeRefs.Count)
- Missing route matches: $(@($missing).Count)

## Critical routes
$($criticalRoutes | ForEach-Object { "- $_" } | Out-String)

## Output files
- declared-routes.txt
- route-references.csv
- missing-routes.csv
"@ | Set-Content $summaryPath

if (@($missing).Count -gt 0) {
    Write-Host "FAIL: missing route matches found. See $missingPath" -ForegroundColor Red
    exit 1
}

Write-Host "PASS: frontend wiring check clean." -ForegroundColor Green
exit 0
'@

$playwrightDemoSmoke = @'
import { test, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.DEMO_BASE_URL || "http://localhost:3000";
const DEMO_EMAIL = process.env.DEMO_EMAIL || "playwright@crown-demo.local";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || "PlaywrightDemo1!";

const routes = [
  { name: "admin", path: "/admin" },
  { name: "admissions", path: "/admissions" },
  { name: "finance", path: "/finance" },
  { name: "billing", path: "/billing" },
  { name: "financial-aid", path: "/financial-aid" },
  { name: "academics", path: "/academics" },
  { name: "communications", path: "/communications" },
  { name: "board-executive", path: "/board/executive" },
];

const artifactsDir = path.resolve(process.cwd(), "artifacts", "demo-proof", "playwright");

async function assertPageHealthy(page: Page, routeName: string) {
  await page.waitForLoadState("domcontentloaded");

  const body = await page.locator("body").innerText();

  expect(body, `${routeName}: should not show application error`).not.toMatch(/Application Error/i);
  expect(body, `${routeName}: should not show debug overlay`).not.toMatch(/DevJwtPanel/i);
  expect(body, `${routeName}: should not show 404`).not.toMatch(/\b404\b|Not Found/i);
  expect(body, `${routeName}: should not show auth failure`).not.toMatch(/\b401\b|Unauthorized|Invalid credentials/i);

  await page.screenshot({
    path: path.join(artifactsDir, `${routeName}.png`),
    fullPage: true,
  });
}

async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });

  const email = page.locator('input[type="email"], input[name="email"]').first();
  const password = page.locator('input[type="password"], input[name="password"]').first();
  const submit = page.getByRole("button", { name: /sign in|log in|login|continue/i }).first();

  await expect(email).toBeVisible({ timeout: 15000 });
  await expect(password).toBeVisible({ timeout: 15000 });

  await email.fill(DEMO_EMAIL);
  await password.fill(DEMO_PASSWORD);
  await submit.click();

  await expect(page).toHaveURL(/\/admin(?:[/?#]|$)/, { timeout: 15000 });
  await assertPageHealthy(page, "post-login-admin");
}

function countNumericTokens(text: string): number {
  return (text.match(/\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%?\b/g) || []).length;
}

test.beforeAll(() => {
  fs.mkdirSync(artifactsDir, { recursive: true });
});

test("login works and lands on admin", async ({ page }) => {
  await login(page);

  const text = await page.locator("body").innerText();
  expect(text).toMatch(/Enrollment|Attendance|Financial|Alert|Billing|Admissions/i);
  expect(countNumericTokens(text)).toBeGreaterThan(10);
});

for (const route of routes) {
  test(`route smoke: ${route.path}`, async ({ page }) => {
    await login(page);
    const response = await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "domcontentloaded" });

    expect(response, `${route.path}: response should exist`).not.toBeNull();
    expect(response!.status(), `${route.path}: status should be < 400`).toBeLessThan(400);

    await assertPageHealthy(page, route.name);

    const text = await page.locator("body").innerText();

    if (route.path === "/admin") {
      expect(text).toMatch(/Enrollment|Attendance|Financial|Alert/i);
      expect(countNumericTokens(text)).toBeGreaterThan(10);
    }

    if (route.path === "/finance" || route.path === "/billing") {
      expect(text).toMatch(/\$|Balance|Invoice|Revenue|Outstanding/i);
    }

    if (route.path === "/academics") {
      expect(text).toMatch(/Grade|Academic|Course|Section|Attendance/i);
    }

    if (route.path === "/board/executive") {
      expect(text).toMatch(/Board|Enrollment|Financial|KPI|Operational/i);
    }
  });
}
'@

$runDemoProof = @'
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

$out = Join-Path $repoRoot "artifacts\demo-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Invoke-Checked([scriptblock]$block, [string]$failMessage) {
    try {
        & $block
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw $failMessage
        }
    } catch {
        Write-Host "FAIL: $failMessage" -ForegroundColor Red
        throw
    }
}

Write-Step "Python / Django sanity"
Invoke-Checked { python --version | Tee-Object -FilePath (Join-Path $out "python-version.txt") } "python not available"
Invoke-Checked { python manage.py check 2>&1 | Tee-Object -FilePath (Join-Path $out "django-check.txt") } "django check failed"
Invoke-Checked { python manage.py showmigrations 2>&1 | Tee-Object -FilePath (Join-Path $out "django-migrations.txt") } "showmigrations failed"

Write-Step "Frontend route wiring"
Invoke-Checked { powershell -ExecutionPolicy Bypass -File .\tools\demo\check_frontend_wiring.ps1 } "frontend wiring check failed"

Write-Step "Health check (accept either canonical health path for now)"
$healthCandidates = @(
    "http://127.0.0.1:8000/api/health/",
    "http://127.0.0.1:8000/api/system/health/",
    "https://crown-api-prod.azurewebsites.net/api/health/"
)

$healthOk = $false
$healthLog = Join-Path $out "health-check.txt"
"" | Set-Content $healthLog

foreach ($url in $healthCandidates) {
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 15
        "PASS $url => $($resp | ConvertTo-Json -Depth 10 -Compress)" | Add-Content $healthLog
        $healthOk = $true
        break
    } catch {
        "FAIL $url => $($_ | Out-String)" | Add-Content $healthLog
    }
}

if (-not $healthOk) {
    throw "No health endpoint responded successfully. See $healthLog"
}

Write-Step "Playwright demo smoke"
$env:DEMO_BASE_URL = if ($env:DEMO_BASE_URL) { $env:DEMO_BASE_URL } else { "http://localhost:3000" }
$env:DEMO_EMAIL    = if ($env:DEMO_EMAIL)    { $env:DEMO_EMAIL }    else { "playwright@crown-demo.local" }
$env:DEMO_PASSWORD = if ($env:DEMO_PASSWORD) { $env:DEMO_PASSWORD } else { "PlaywrightDemo1!" }

Push-Location frontend\dashboards
Invoke-Checked { npx playwright test tests/demo-smoke.spec.ts --reporter=line } "Playwright demo smoke failed"
Pop-Location

Write-Step "Proof gate complete"
@"
PASS

Artifacts:
- $out\python-version.txt
- $out\django-check.txt
- $out\django-migrations.txt
- $out\health-check.txt
- $out\wiring-summary.md
- $out\missing-routes.csv
- $repoRoot\frontend\dashboards\artifacts\demo-proof\playwright
"@ | Set-Content (Join-Path $out "PROOF_GATE_RESULT.txt")

Write-Host "PASS: demo proof gate is green." -ForegroundColor Green
'@

$startHeritageDemo = @'
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "==> Backend migrate + seed"
python manage.py migrate
python manage.py load_heritage_demo --reset-passwords

Write-Host "==> Starting backend on :8000"
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$repoRoot'; python manage.py runserver 8000"
)

Write-Host "==> Starting frontend in demo mode"
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "`$env:VITE_API_BASE='http://127.0.0.1:8000'; `$env:VITE_DEMO_MODE='1'; Set-Location '$repoRoot\frontend\dashboards'; npm run dev"
)

Start-Sleep -Seconds 6
Start-Process "http://localhost:3000/login"

Write-Host ""
Write-Host "Demo started."
Write-Host "Primary login: playwright@crown-demo.local / PlaywrightDemo1!"
'@

$readmeInstructions = @'
MANUAL PATCH REQUIRED

1. In your global frontend shell or root layout, import:
   import DemoModeBanner from "@/components/DemoModeBanner";

2. Render it at the top of the shell:
   <>
     <DemoModeBanner />
     {existingLayout}
   </>

3. Add MetricProvenanceBadge only to cards that are not fully live-backed yet.
'@

Write-Host "==> Writing demo proof files..." -ForegroundColor Cyan

Write-FileUtf8 "backend/core/management/__init__.py" $coreMgmtInit
Write-FileUtf8 "backend/core/management/commands/__init__.py" $coreMgmtInit
Write-FileUtf8 "backend/core/management/commands/load_heritage_demo.py" $loadHeritageDemo

Write-FileUtf8 "frontend/dashboards/src/components/DemoModeBanner.jsx" $demoBanner
Write-FileUtf8 "frontend/dashboards/src/components/MetricProvenanceBadge.tsx" $metricBadge

Write-FileUtf8 "tools/demo/check_frontend_wiring.ps1" $frontendWiringCheck
Write-FileUtf8 "frontend/dashboards/tests/demo-smoke.spec.ts" $playwrightDemoSmoke
Write-FileUtf8 "scripts/demo/run_demo_proof.ps1" $runDemoProof
Write-FileUtf8 "scripts/demo/start_heritage_demo.ps1" $startHeritageDemo
Write-FileUtf8 "DEMO_PATCH_INSTRUCTIONS.txt" $readmeInstructions

Write-Host ""
Write-Host "==> Files created. Next commands:" -ForegroundColor Yellow
Write-Host "git checkout -b demo/proof-gate-2026-04-10"
Write-Host "python manage.py migrate"
Write-Host "python manage.py load_heritage_demo --reset-passwords"
Write-Host ""
Write-Host "Frontend startup:" -ForegroundColor Yellow
Write-Host "cd frontend\dashboards"
Write-Host '$env:VITE_API_BASE="http://127.0.0.1:8000"'
Write-Host '$env:VITE_DEMO_MODE="1"'
Write-Host "npm install"
Write-Host "npm run dev"
Write-Host ""
Write-Host "Proof gate:" -ForegroundColor Yellow
Write-Host 'powershell -ExecutionPolicy Bypass -File .\scripts\demo\run_demo_proof.ps1'
Write-Host ""
Write-Host "Manual patch note: see DEMO_PATCH_INSTRUCTIONS.txt"
