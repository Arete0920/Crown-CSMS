param(
    [string]$RepoRoot = ".",
    [string]$OutDir = "audit-artifacts/forensic-process-module-wiring",
    [switch]$RunTests,
    [switch]$RunDjangoChecks
)

$ErrorActionPreference = "Continue"

$StartedAt = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoRoot = Resolve-Path $RepoRoot
$OutDirFull = Join-Path $RepoRoot $OutDir
New-Item -ItemType Directory -Force -Path $OutDirFull | Out-Null

$JsonOut = Join-Path $OutDirFull "crown_forensic_audit_$StartedAt.json"
$MdOut   = Join-Path $OutDirFull "crown_forensic_audit_$StartedAt.md"
$CsvOut  = Join-Path $OutDirFull "crown_forensic_audit_$StartedAt.csv"
$LogOut  = Join-Path $OutDirFull "crown_forensic_audit_$StartedAt.log"

Start-Transcript -Path $LogOut -Force | Out-Null

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "====================================================================="
    Write-Host $Title
    Write-Host "====================================================================="
}

function Test-File {
    param([string]$Path)
    return Test-Path -LiteralPath (Join-Path $RepoRoot $Path)
}

function Test-Any {
    param([string[]]$Paths)
    foreach ($p in $Paths) {
        if (Test-File $p) { return $true }
    }
    return $false
}

function Get-FileTextSafe {
    param([string]$Path)
    $Full = Join-Path $RepoRoot $Path
    if (!(Test-Path -LiteralPath $Full)) { return "" }
    try {
        return Get-Content -LiteralPath $Full -Raw -ErrorAction Stop
    } catch {
        return ""
    }
}

function Add-Finding {
    param(
        [string]$Process,
        [string]$Module,
        [string]$Layer,
        [string]$Check,
        [string]$Status,
        [string]$Evidence,
        [string]$Recommendation
    )

    $script:Findings += [pscustomobject]@{
        timestamp       = (Get-Date).ToString("s")
        process         = $Process
        module          = $Module
        layer           = $Layer
        check           = $Check
        status          = $Status
        evidence        = $Evidence
        recommendation  = $Recommendation
    }
}

function Status-FromBool {
    param([bool]$Value)
    if ($Value) { return "PASS" }
    return "FAIL"
}

function Find-FilesByName {
    param([string]$Name)
    Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq $Name -and
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\\.venv\\" -and
            $_.FullName -notmatch "\\venv\\" -and
            $_.FullName -notmatch "\\__pycache__\\"
        }
}

function Find-DirsByName {
    param([string]$Name)
    Get-ChildItem -Path $RepoRoot -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq $Name -and
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\\.venv\\" -and
            $_.FullName -notmatch "\\venv\\" -and
            $_.FullName -notmatch "\\__pycache__\\"
        }
}

function Convert-ToRelPath {
    param([string]$FullName)
    $root = "$RepoRoot".TrimEnd('\','/')
    return $FullName.Replace($root, "").TrimStart('\','/')
}

function Test-TextContains {
    param(
        [string]$Text,
        [string[]]$Needles
    )
    foreach ($needle in $Needles) {
        if ($Text -match [regex]::Escape($needle)) { return $true }
    }
    return $false
}

function Find-TextInRepo {
    param([string[]]$Patterns)

    $hits = @()
    $files = Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\\.venv\\" -and
            $_.FullName -notmatch "\\venv\\" -and
            $_.FullName -notmatch "\\__pycache__\\" -and
            $_.Extension -in @(".py", ".html", ".js", ".ts", ".tsx", ".jsx", ".css", ".md", ".txt", ".yml", ".yaml", ".json", ".env", ".toml", ".ini")
        }

    foreach ($file in $files) {
        $text = ""
        try { $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop } catch { continue }
        foreach ($pattern in $Patterns) {
            if ($text -match $pattern) {
                $hits += Convert-ToRelPath $file.FullName
                break
            }
        }
    }

    return $hits | Sort-Object -Unique
}

function Invoke-CommandCapture {
    param(
        [string]$Command,
        [string]$Label
    )

    $OutFile = Join-Path $OutDirFull "$($Label)_$StartedAt.txt"

    try {
        Write-Host "Running: $Command"
        Push-Location $RepoRoot
        cmd.exe /c "$Command" > $OutFile 2>&1
        $ExitCode = $LASTEXITCODE
        Pop-Location

        return [pscustomobject]@{
            label = $Label
            command = $Command
            exit_code = $ExitCode
            output_file = $OutFile.Replace("$RepoRoot", "").TrimStart('\','/')
        }
    } catch {
        try { Pop-Location } catch {}
        "ERROR: $($_.Exception.Message)" | Out-File -FilePath $OutFile -Encoding UTF8
        return [pscustomobject]@{
            label = $Label
            command = $Command
            exit_code = 999
            output_file = $OutFile.Replace("$RepoRoot", "").TrimStart('\','/')
        }
    }
}

$Findings = @()
$CommandResults = @()

Write-Section "CROWN Forensic Audit Started"
Write-Host "Repo root: $RepoRoot"
Write-Host "Output:    $OutDirFull"

# ---------------------------------------------------------------------
# Repository baseline
# ---------------------------------------------------------------------

Write-Section "Repository Baseline"

$ManagePy = Find-FilesByName "manage.py" | Select-Object -First 1
$SettingsFiles = Find-FilesByName "settings.py"
$RootUrlsFiles = Find-FilesByName "urls.py"
$Requirements = Find-FilesByName "requirements.txt"
$PyProject = Find-FilesByName "pyproject.toml"

Add-Finding "Repository Baseline" "repo" "structure" "manage.py exists" `
    (Status-FromBool ($null -ne $ManagePy)) `
    ($(if ($ManagePy) { Convert-ToRelPath $ManagePy.FullName } else { "manage.py not found" })) `
    "If FAIL, confirm this is the Django project root or run from the correct repository root."

Add-Finding "Repository Baseline" "repo" "structure" "settings.py exists" `
    (Status-FromBool (($SettingsFiles | Measure-Object).Count -gt 0)) `
    ($(($SettingsFiles | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "If FAIL, locate Django settings and ensure project layout is complete."

Add-Finding "Repository Baseline" "repo" "structure" "urls.py exists" `
    (Status-FromBool (($RootUrlsFiles | Measure-Object).Count -gt 0)) `
    ($(($RootUrlsFiles | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "If FAIL, root and app URL wiring cannot be verified."

Add-Finding "Repository Baseline" "repo" "dependencies" "requirements or pyproject exists" `
    (Status-FromBool (($Requirements | Measure-Object).Count -gt 0 -or ($PyProject | Measure-Object).Count -gt 0)) `
    ("requirements.txt: " + (($Requirements | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ") + " | pyproject.toml: " + (($PyProject | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "If FAIL, add dependency manifest for repeatable audit and deployment."

# ---------------------------------------------------------------------
# Discover candidate Django apps/modules
# ---------------------------------------------------------------------

Write-Section "Discovering Django Modules"

$CandidateModules = @()

$AppConfigFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -Filter "apps.py" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\" -and
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\venv\\" -and
        $_.FullName -notmatch "\\__pycache__\\"
    }

foreach ($appsPy in $AppConfigFiles) {
    $dir = Split-Path $appsPy.FullName -Parent
    $name = Split-Path $dir -Leaf
    $rel = Convert-ToRelPath $dir
    $CandidateModules += [pscustomobject]@{
        name = $name
        path = $rel
    }
}

$CandidateModules = $CandidateModules | Sort-Object name -Unique

if (($CandidateModules | Measure-Object).Count -eq 0) {
    Add-Finding "Module Discovery" "repo" "discovery" "Django apps discovered via apps.py" "FAIL" "No apps.py files found." "Confirm repository root and Django project layout."
} else {
    Add-Finding "Module Discovery" "repo" "discovery" "Django apps discovered via apps.py" "PASS" (($CandidateModules | ForEach-Object { "$($_.name)=$($_.path)" }) -join "; ") "Continue with module-by-module checks."
}

# ---------------------------------------------------------------------
# Expected CROWN process map
# ---------------------------------------------------------------------

$ExpectedProcesses = @(
    [pscustomobject]@{
        process = "Authentication and Access Control"
        expected_modules = @("accounts", "users", "authentication", "auth", "schools")
        keywords = @("login", "logout", "password", "permission", "role", "group", "user")
    },
    [pscustomobject]@{
        process = "School Administration"
        expected_modules = @("schools", "admin", "organization", "campus")
        keywords = @("school", "campus", "administrator", "organization")
    },
    [pscustomobject]@{
        process = "Student Management"
        expected_modules = @("students", "enrollment", "admissions")
        keywords = @("student", "enrollment", "admission", "grade")
    },
    [pscustomobject]@{
        process = "Parent / Guardian Portal"
        expected_modules = @("parents", "guardians", "families", "portal")
        keywords = @("parent", "guardian", "family", "portal")
    },
    [pscustomobject]@{
        process = "Teacher / Staff Workflow"
        expected_modules = @("teachers", "staff", "faculty", "classes")
        keywords = @("teacher", "staff", "faculty", "classroom")
    },
    [pscustomobject]@{
        process = "Attendance"
        expected_modules = @("attendance", "classes", "students")
        keywords = @("attendance", "absence", "present", "tardy")
    },
    [pscustomobject]@{
        process = "Billing / Tuition"
        expected_modules = @("billing", "payments", "tuition", "invoices")
        keywords = @("billing", "payment", "tuition", "invoice", "stripe")
    },
    [pscustomobject]@{
        process = "Communications"
        expected_modules = @("communications", "messages", "notifications", "email")
        keywords = @("message", "notification", "email", "communication")
    },
    [pscustomobject]@{
        process = "Documents and File Uploads"
        expected_modules = @("documents", "files", "uploads", "media")
        keywords = @("document", "upload", "file", "media")
    },
    [pscustomobject]@{
        process = "Audit / Evidence / Compliance"
        expected_modules = @("audit", "evidence", "compliance", "logs")
        keywords = @("audit", "evidence", "compliance", "log")
    },
    [pscustomobject]@{
        process = "Runtime / Deployment"
        expected_modules = @("deployment", "config", "settings")
        keywords = @("gunicorn", "wsgi", "asgi", "whitenoise", "static", "collectstatic")
    },
    [pscustomobject]@{
        process = "Security Hardening"
        expected_modules = @("security", "settings", "middleware", "accounts")
        keywords = @("csrf", "secure_ssl_redirect", "x_frame_options", "secure_hsts", "allowed_hosts")
    }
)

# ---------------------------------------------------------------------
# Module-by-module component inspection
# ---------------------------------------------------------------------

Write-Section "Module Component and Wiring Inspection"

$ComponentNames = @(
    "models.py",
    "views.py",
    "urls.py",
    "forms.py",
    "serializers.py",
    "admin.py",
    "tests.py",
    "apps.py",
    "permissions.py",
    "services.py",
    "signals.py"
)

foreach ($module in $CandidateModules) {
    foreach ($component in $ComponentNames) {
        $rel = Join-Path $module.path $component
        $exists = Test-File $rel
        # Sprint G: also accept a tests/ package directory as satisfying the tests.py check
        if (-not $exists -and $component -eq "tests.py") {
            $testsDir = Join-Path $module.path "tests"
            if (Test-File $testsDir) {
                $exists = $true
                $rel = $testsDir
            }
        }
        Add-Finding "Module Component Inventory" $module.name "component" "$component exists" `
            (Status-FromBool $exists) `
            ($(if ($exists) { $rel } else { "$rel missing" })) `
            ($(if ($exists) { "Review implementation depth and tests." } else { "Create or justify absence of this component." }))
    }

    $templatesDir = Join-Path $module.path "templates"
    $staticDir = Join-Path $module.path "static"
    $migrationsDir = Join-Path $module.path "migrations"

    # Sprint H: templates are optional for API-only modules; missing = UNKNOWN, not FAIL
    Add-Finding "Module Component Inventory" $module.name "component" "templates directory exists" `
        ($(if (Test-File $templatesDir) { "PASS" } else { "UNKNOWN" })) `
        ($(if (Test-File $templatesDir) { $templatesDir } else { "$templatesDir missing or not required (API-only modules do not need templates)" })) `
        "If module renders HTML, templates must exist and be route-tested. API-only modules may omit this."

    Add-Finding "Module Component Inventory" $module.name "component" "static directory exists" `
        ($(if (Test-File $staticDir) { "PASS" } else { "UNKNOWN" })) `
        ($(if (Test-File $staticDir) { $staticDir } else { "$staticDir missing or not required" })) `
        "Static files are optional unless the module owns UI assets."

    Add-Finding "Module Component Inventory" $module.name "component" "migrations directory exists" `
        (Status-FromBool (Test-File $migrationsDir)) `
        ($(if (Test-File $migrationsDir) { $migrationsDir } else { "$migrationsDir missing" })) `
        "If module has models, migrations must exist and apply cleanly."
}

# ---------------------------------------------------------------------
# URL wiring inspection
# ---------------------------------------------------------------------

Write-Section "URL Wiring Inspection"

$AllUrlsText = ""
$AllUrlsEvidence = @()

foreach ($urls in $RootUrlsFiles) {
    $rel = Convert-ToRelPath $urls.FullName
    $txt = Get-Content -LiteralPath $urls.FullName -Raw -ErrorAction SilentlyContinue
    $AllUrlsText += "`n# FILE: $rel`n$txt"
    $AllUrlsEvidence += $rel
}

foreach ($module in $CandidateModules) {
    $moduleUrls = Join-Path $module.path "urls.py"
    $hasModuleUrls = Test-File $moduleUrls

    Add-Finding "URL Wiring" $module.name "wiring" "module urls.py exists" `
        (Status-FromBool $hasModuleUrls) `
        ($(if ($hasModuleUrls) { $moduleUrls } else { "$moduleUrls missing" })) `
        "Add module urls.py if the module exposes browser/API routes."

    if ($hasModuleUrls) {
        $wired = $AllUrlsText -match [regex]::Escape($module.name) -or $AllUrlsText -match [regex]::Escape($module.path.Replace("\", ".").Replace("/", "."))
        Add-Finding "URL Wiring" $module.name "wiring" "module appears included in root URL config" `
            (Status-FromBool $wired) `
            ($(if ($wired) { "Root URL files mention module. Root URL files: " + ($AllUrlsEvidence -join "; ") } else { "No root urls.py reference found for $($module.name). Root URL files: " + ($AllUrlsEvidence -join "; ") })) `
            "Wire module routes in project urls.py using include()."
    }
}

# ---------------------------------------------------------------------
# settings.py wiring inspection
# ---------------------------------------------------------------------

Write-Section "Settings Wiring Inspection"

$SettingsCombined = ""
$SettingsEvidence = @()

foreach ($settings in $SettingsFiles) {
    $rel = Convert-ToRelPath $settings.FullName
    $txt = Get-Content -LiteralPath $settings.FullName -Raw -ErrorAction SilentlyContinue
    $SettingsCombined += "`n# FILE: $rel`n$txt"
    $SettingsEvidence += $rel
}

# Also include wizard_registry.py — it is the single source of truth for
# wizard app registration (INSTALLED_APPS += WIZARD_INSTALLED_APPS in settings).
$WizardRegistryPaths = @(
    (Join-Path $RepoRoot "backend/crown_api/wizard_registry.py"),
    (Join-Path $RepoRoot "crown_api/wizard_registry.py")
)
foreach ($wrPath in $WizardRegistryPaths) {
    if (Test-Path $wrPath) {
        $rel = Convert-ToRelPath $wrPath
        $txt = Get-Content -LiteralPath $wrPath -Raw -ErrorAction SilentlyContinue
        $SettingsCombined += "`n# FILE: $rel`n$txt"
        $SettingsEvidence += "$rel (wizard_registry)"
    }
}

foreach ($module in $CandidateModules) {
    $installed = $SettingsCombined -match [regex]::Escape($module.name) -or $SettingsCombined -match [regex]::Escape($module.path.Replace("\", ".").Replace("/", "."))
    Add-Finding "Settings Wiring" $module.name "wiring" "module appears in settings / INSTALLED_APPS" `
        (Status-FromBool $installed) `
        ($(if ($installed) { "settings mention $($module.name). Settings files: " + ($SettingsEvidence -join "; ") } else { "settings do not mention $($module.name). Settings files: " + ($SettingsEvidence -join "; ") })) `
        "If this is a Django app, add AppConfig to INSTALLED_APPS."
}

# ---------------------------------------------------------------------
# Process coverage inspection
# ---------------------------------------------------------------------

Write-Section "Process Coverage Inspection"

foreach ($proc in $ExpectedProcesses) {
    $matchingModules = @()

    foreach ($module in $CandidateModules) {
        if ($proc.expected_modules -contains $module.name) {
            $matchingModules += $module.name
        }
    }

    if (($matchingModules | Measure-Object).Count -eq 0) {
        $patternList = $proc.keywords | ForEach-Object { [regex]::Escape($_) }
        $hits = Find-TextInRepo $patternList
        if (($hits | Measure-Object).Count -gt 0) {
            Add-Finding $proc.process "repo" "process" "process keyword coverage exists" `
                "UNKNOWN" `
                ("No expected module name found, but keyword hits exist: " + (($hits | Select-Object -First 20) -join "; ")) `
                "Manually map these files to a responsible module and verify end-to-end wiring."
        } else {
            Add-Finding $proc.process "repo" "process" "process implementation evidence exists" `
                "FAIL" `
                ("No expected modules found: " + ($proc.expected_modules -join ", ") + ". No keyword hits found.") `
                "Create/identify owning module and produce route/runtime/test evidence."
        }
    } else {
        Add-Finding $proc.process ($matchingModules -join ", ") "process" "expected module coverage exists" `
            "PASS" `
            ("Matching modules: " + ($matchingModules -join ", ")) `
            "Continue to component, route, permission, runtime, and test proof."
    }
}

# ---------------------------------------------------------------------
# Security setting inspection
# ---------------------------------------------------------------------

Write-Section "Security Setting Inspection"

$SecurityChecks = @(
    [pscustomobject]@{ name = "DEBUG disabled or environment-controlled"; patterns = @("DEBUG = False", "DEBUG=False", "os.environ.get('DEBUG'", 'env("DEBUG"', 'config("DEBUG"') },
    [pscustomobject]@{ name = "ALLOWED_HOSTS configured"; patterns = @("ALLOWED_HOSTS") },
    [pscustomobject]@{ name = "CSRF trusted origins configured"; patterns = @("CSRF_TRUSTED_ORIGINS") },
    [pscustomobject]@{ name = "SECURE_SSL_REDIRECT configured"; patterns = @("SECURE_SSL_REDIRECT") },
    [pscustomobject]@{ name = "SESSION_COOKIE_SECURE configured"; patterns = @("SESSION_COOKIE_SECURE") },
    [pscustomobject]@{ name = "CSRF_COOKIE_SECURE configured"; patterns = @("CSRF_COOKIE_SECURE") },
    [pscustomobject]@{ name = "SECURE_HSTS_SECONDS configured"; patterns = @("SECURE_HSTS_SECONDS") },
    [pscustomobject]@{ name = "X_FRAME_OPTIONS configured"; patterns = @("X_FRAME_OPTIONS") }
)

foreach ($check in $SecurityChecks) {
    $found = $false
    foreach ($p in $check.patterns) {
        if ($SettingsCombined -match [regex]::Escape($p)) {
            $found = $true
            break
        }
    }

    Add-Finding "Security Hardening" "settings" "security" $check.name `
        (Status-FromBool $found) `
        ($(if ($found) { "Found in settings files: " + ($SettingsEvidence -join "; ") } else { "Not found in settings files: " + ($SettingsEvidence -join "; ") })) `
        "Set explicitly for production or document environment-based configuration."
}

# ---------------------------------------------------------------------
# Admin registration inspection
# ---------------------------------------------------------------------

Write-Section "Admin Registration Inspection"

foreach ($module in $CandidateModules) {
    $modelsPath = Join-Path $module.path "models.py"
    $adminPath = Join-Path $module.path "admin.py"

    $modelsText = Get-FileTextSafe $modelsPath
    $adminText = Get-FileTextSafe $adminPath

    $hasModels = $modelsText -match "class\s+\w+\(.*models\.Model"
    $hasAdminRegister = $adminText -match "admin\.site\.register" -or $adminText -match "@admin\.register"

    if ($hasModels) {
        Add-Finding "Admin Registration" $module.name "wiring" "models registered in admin where applicable" `
            (Status-FromBool $hasAdminRegister) `
            ($(if ($hasAdminRegister) { "$adminPath contains admin registration." } else { "$modelsPath has models but $adminPath lacks registration evidence." })) `
            "Register operational models in admin or document why admin access is intentionally unavailable."
    } else {
        Add-Finding "Admin Registration" $module.name "wiring" "models registered in admin where applicable" `
            "NOT APPLICABLE" `
            "$modelsPath has no obvious models.Model class." `
            "No action if module has no database models."
    }
}

# ---------------------------------------------------------------------
# Template/view wiring inspection
# ---------------------------------------------------------------------

Write-Section "Template and View Wiring Inspection"

foreach ($module in $CandidateModules) {
    $viewsPath = Join-Path $module.path "views.py"
    $viewsText = Get-FileTextSafe $viewsPath

    $usesRender = $viewsText -match "render\s*\("
    $usesTemplateView = $viewsText -match "TemplateView"
    $usesDRF = $viewsText -match "APIView|ViewSet|ModelViewSet|GenericAPIView|serializer_class"

    $templateDir = Join-Path $RepoRoot (Join-Path $module.path "templates")
    $templateCount = 0
    if (Test-Path -LiteralPath $templateDir) {
        $templateCount = (Get-ChildItem -LiteralPath $templateDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    }

    if ($usesRender -or $usesTemplateView) {
        Add-Finding "Template Wiring" $module.name "wiring" "HTML views have templates" `
            (Status-FromBool ($templateCount -gt 0)) `
            "views.py uses render/template pattern; template count: $templateCount" `
            "Add templates and route tests for each HTML view."
    } elseif ($usesDRF) {
        Add-Finding "Template Wiring" $module.name "wiring" "API views identified" `
            "NOT APPLICABLE" `
            "views.py appears API-oriented; template count: $templateCount" `
            "Verify serializers, permissions, API routes, and API tests instead."
    } else {
        Add-Finding "Template Wiring" $module.name "wiring" "view/template relationship identifiable" `
            "UNKNOWN" `
            "No obvious render, TemplateView, or DRF pattern in $viewsPath." `
            "Manually inspect views and confirm whether module is route-bearing."
    }
}

# ---------------------------------------------------------------------
# Permission/authentication inspection
# ---------------------------------------------------------------------

Write-Section "Permission and Authentication Inspection"

foreach ($module in $CandidateModules) {
    $viewsPath = Join-Path $module.path "views.py"
    $viewsText = Get-FileTextSafe $viewsPath

    $hasProtectedEvidence =
        $viewsText -match "LoginRequiredMixin" -or
        $viewsText -match "@login_required" -or
        $viewsText -match "permission_required" -or
        $viewsText -match "PermissionRequiredMixin" -or
        $viewsText -match "IsAuthenticated" -or
        $viewsText -match "permission_classes"

    $hasViews = (Test-File $viewsPath) -and ($viewsText.Trim().Length -gt 0)

    if ($hasViews) {
        Add-Finding "Access Control" $module.name "security" "views expose permission/authentication evidence" `
            (Status-FromBool $hasProtectedEvidence) `
            ($(if ($hasProtectedEvidence) { "$viewsPath contains auth/permission indicators." } else { "$viewsPath exists but no obvious auth/permission indicators found." })) `
            "Apply explicit auth/permission controls to all non-public views and APIs."
    } else {
        Add-Finding "Access Control" $module.name "security" "views expose permission/authentication evidence" `
            "NOT APPLICABLE" `
            "$viewsPath missing or empty." `
            "No action if module has no exposed routes."
    }
}

# ---------------------------------------------------------------------
# Tests inspection
# ---------------------------------------------------------------------

Write-Section "Test Coverage Inspection"

$TestFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\" -and
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\venv\\" -and
        $_.FullName -notmatch "\\__pycache__\\" -and
        ($_.Name -eq "tests.py" -or $_.Name -match "^test_.*\.py$" -or $_.FullName -match "\\tests\\")
    }

Add-Finding "Automated Tests" "repo" "tests" "test files exist" `
    (Status-FromBool (($TestFiles | Measure-Object).Count -gt 0)) `
    ($(($TestFiles | Select-Object -First 50 | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "Add route, permission, model, form, service, and smoke tests."

foreach ($module in $CandidateModules) {
    $moduleTestFiles = $TestFiles | Where-Object { (Convert-ToRelPath $_.FullName) -like "$($module.path)*" }
    Add-Finding "Automated Tests" $module.name "tests" "module-level tests exist" `
        (Status-FromBool (($moduleTestFiles | Measure-Object).Count -gt 0)) `
        ($(($moduleTestFiles | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
        "Add tests proving routes, permissions, forms/serializers, model behavior, and critical workflows."
}

# ---------------------------------------------------------------------
# Deployment/runtime asset inspection
# ---------------------------------------------------------------------

Write-Section "Deployment and Runtime Inspection"

$DeploymentFiles = @(
    "Procfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "render.yaml",
    "railway.json",
    "vercel.json",
    "fly.toml",
    ".github/workflows",
    "manage.py"
)

foreach ($df in $DeploymentFiles) {
    Add-Finding "Runtime / Deployment" "repo" "deployment" "$df exists" `
        ($(if (Test-File $df) { "PASS" } else { "UNKNOWN" })) `
        ($(if (Test-File $df) { $df } else { "$df not found or not applicable" })) `
        "If this deployment path is required, provide the file and runtime proof."
}

$WsgiFiles = Find-FilesByName "wsgi.py"
$AsgiFiles = Find-FilesByName "asgi.py"

Add-Finding "Runtime / Deployment" "repo" "deployment" "wsgi.py exists" `
    (Status-FromBool (($WsgiFiles | Measure-Object).Count -gt 0)) `
    ($(($WsgiFiles | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "Required for typical WSGI deployment."

Add-Finding "Runtime / Deployment" "repo" "deployment" "asgi.py exists" `
    ($(if (($AsgiFiles | Measure-Object).Count -gt 0) { "PASS" } else { "UNKNOWN" })) `
    ($(($AsgiFiles | ForEach-Object { Convert-ToRelPath $_.FullName }) -join "; ")) `
    "Required if ASGI/websockets/async deployment is used."

# ---------------------------------------------------------------------
# Optional command execution
# ---------------------------------------------------------------------

Write-Section "Optional Runtime Commands"

if ($RunDjangoChecks) {
    if ($ManagePy) {
        $CommandResults += Invoke-CommandCapture "python manage.py check --deploy" "django_check_deploy"
        $CommandResults += Invoke-CommandCapture "python manage.py showmigrations" "django_showmigrations"

        foreach ($cr in $CommandResults | Where-Object { $_.label -in @("django_check_deploy", "django_showmigrations") }) {
            Add-Finding "Runtime / Deployment" "django" "runtime command" "$($cr.command)" `
                ($(if ($cr.exit_code -eq 0) { "PASS" } else { "FAIL" })) `
                "Exit code $($cr.exit_code). Output: $($cr.output_file)" `
                "Open command output and remediate all warnings/errors before gate rerun."
        }
    } else {
        Add-Finding "Runtime / Deployment" "django" "runtime command" "Django checks skipped" `
            "FAIL" `
            "manage.py not found." `
            "Run script from Django repository root."
    }
} else {
    Add-Finding "Runtime / Deployment" "django" "runtime command" "Django checks skipped" `
        "UNKNOWN" `
        "Run script with -RunDjangoChecks to execute python manage.py check --deploy and showmigrations." `
        "Run: powershell -ExecutionPolicy Bypass -File scripts/execution/200_crown_forensic_process_module_wiring_audit.ps1 -RunDjangoChecks"
}

if ($RunTests) {
    if ($ManagePy) {
        $CommandResults += Invoke-CommandCapture "python manage.py test" "django_tests"

        foreach ($cr in $CommandResults | Where-Object { $_.label -eq "django_tests" }) {
            Add-Finding "Automated Tests" "django" "runtime command" "$($cr.command)" `
                ($(if ($cr.exit_code -eq 0) { "PASS" } else { "FAIL" })) `
                "Exit code $($cr.exit_code). Output: $($cr.output_file)" `
                "Fix failing tests or add missing tests before release gate."
        }
    } else {
        Add-Finding "Automated Tests" "django" "runtime command" "Django tests skipped" `
            "FAIL" `
            "manage.py not found." `
            "Run script from Django repository root."
    }
} else {
    Add-Finding "Automated Tests" "django" "runtime command" "Django tests skipped" `
        "UNKNOWN" `
        "Run script with -RunTests to execute python manage.py test." `
        "Run: powershell -ExecutionPolicy Bypass -File scripts/execution/200_crown_forensic_process_module_wiring_audit.ps1 -RunTests"
}

# ---------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------

Write-Section "Scoring"

$PassCount = ($Findings | Where-Object { $_.status -eq "PASS" } | Measure-Object).Count
$FailCount = ($Findings | Where-Object { $_.status -eq "FAIL" } | Measure-Object).Count
$UnknownCount = ($Findings | Where-Object { $_.status -eq "UNKNOWN" } | Measure-Object).Count
$NaCount = ($Findings | Where-Object { $_.status -eq "NOT APPLICABLE" } | Measure-Object).Count
$TotalScored = ($Findings | Where-Object { $_.status -ne "NOT APPLICABLE" } | Measure-Object).Count
$TotalAll = ($Findings | Measure-Object).Count

$GateDecision = "NO-GO"
if ($FailCount -eq 0 -and $UnknownCount -eq 0 -and $TotalScored -gt 0) {
    $GateDecision = "GO"
}

$Summary = [pscustomobject]@{
    audit_name = "CROWN Forensic Process Module Component Wiring Audit"
    started_at = $StartedAt
    repo_root = "$RepoRoot"
    output_directory = $OutDirFull
    total_findings = $TotalAll
    total_scored = $TotalScored
    pass = $PassCount
    fail = $FailCount
    unknown = $UnknownCount
    not_applicable = $NaCount
    gate_decision = $GateDecision
    decision_rule = "GO only if FAIL=0 and UNKNOWN=0 across all scored findings."
    command_results = $CommandResults
}

$Audit = [pscustomobject]@{
    summary = $Summary
    findings = $Findings
}

$Audit | ConvertTo-Json -Depth 8 | Out-File -FilePath $JsonOut -Encoding UTF8
$Findings | Export-Csv -Path $CsvOut -NoTypeInformation -Encoding UTF8

# ---------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------

$ByStatus = $Findings | Group-Object status | Sort-Object Name

$Md = @()
$Md += "# CROWN Forensic Process / Module / Component / Wiring Audit"
$Md += ""
$Md += "Generated: $StartedAt"
$Md += ""
$Md += "Repository: $RepoRoot"
$Md += ""
$Md += "## Gate Decision"
$Md += ""
$Md += "**$GateDecision**"
$Md += ""
$Md += "Decision rule: **GO only if FAIL=0 and UNKNOWN=0 across all scored findings.**"
$Md += ""
$Md += "## Score"
$Md += ""
$Md += "| Status | Count |"
$Md += "|---|---:|"
$Md += "| PASS | $PassCount |"
$Md += "| FAIL | $FailCount |"
$Md += "| UNKNOWN | $UnknownCount |"
$Md += "| NOT APPLICABLE | $NaCount |"
$Md += "| TOTAL FINDINGS | $TotalAll |"
$Md += "| TOTAL SCORED | $TotalScored |"
$Md += ""
$Md += "## Required Remediation Focus"
$Md += ""

$Critical = $Findings | Where-Object { $_.status -in @("FAIL", "UNKNOWN") } | Sort-Object process, module, layer, check

if (($Critical | Measure-Object).Count -eq 0) {
    $Md += "No FAIL or UNKNOWN findings."
} else {
    $Md += "| Status | Process | Module | Layer | Check | Evidence | Recommendation |"
    $Md += "|---|---|---|---|---|---|---|"
    foreach ($f in $Critical) {
        $ev = ($f.evidence -replace "\|", "/" -replace "`r?`n", " ").Trim()
        $rec = ($f.recommendation -replace "\|", "/" -replace "`r?`n", " ").Trim()
        $Md += "| $($f.status) | $($f.process) | $($f.module) | $($f.layer) | $($f.check) | $ev | $rec |"
    }
}

$Md += ""
$Md += "## Full Findings"
$Md += ""
$Md += "| Status | Process | Module | Layer | Check | Evidence | Recommendation |"
$Md += "|---|---|---|---|---|---|---|"

foreach ($f in ($Findings | Sort-Object process, module, layer, check)) {
    $ev = ($f.evidence -replace "\|", "/" -replace "`r?`n", " ").Trim()
    $rec = ($f.recommendation -replace "\|", "/" -replace "`r?`n", " ").Trim()
    $Md += "| $($f.status) | $($f.process) | $($f.module) | $($f.layer) | $($f.check) | $ev | $rec |"
}

$Md += ""
$Md += "## Artifacts"
$Md += ""
$Md += "- JSON: $JsonOut"
$Md += "- CSV: $CsvOut"
$Md += "- Log: $LogOut"

$Md -join "`n" | Out-File -FilePath $MdOut -Encoding UTF8

Write-Host ""
Write-Host "====================================================================="
Write-Host "CROWN FORENSIC AUDIT COMPLETE"
Write-Host "====================================================================="
Write-Host "Gate Decision: $GateDecision"
Write-Host "PASS:          $PassCount"
Write-Host "FAIL:          $FailCount"
Write-Host "UNKNOWN:       $UnknownCount"
Write-Host "N/A:           $NaCount"
Write-Host ""
Write-Host "Markdown: $MdOut"
Write-Host "JSON:     $JsonOut"
Write-Host "CSV:      $CsvOut"
Write-Host "Log:      $LogOut"
Write-Host ""

Stop-Transcript | Out-Null
