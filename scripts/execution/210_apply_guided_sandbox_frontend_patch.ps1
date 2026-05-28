<#
.SYNOPSIS
  Applies the CROWN Guided Proof Sandbox frontend wiring patch.

.DESCRIPTION
  Idempotently wires the /sandbox route and adds minimal LoginPage query-param handling
  for sandbox experience, guidance, role, school, and tour context.

  This script is intentionally text-patch based so the connector can stage safe,
  reviewable work without blindly rewriting large established frontend files.

.REQUIREMENTS
  Run from the repository root.
#>

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$routerPath = Join-Path $repoRoot "frontend/dashboards/src/routes/router.jsx"
$loginPath = Join-Path $repoRoot "frontend/dashboards/src/pages/LoginPage.jsx"

if (-not (Test-Path $routerPath)) { throw "Missing router file: $routerPath" }
if (-not (Test-Path $loginPath)) { throw "Missing login file: $loginPath" }

$router = Get-Content $routerPath -Raw

if ($router -notmatch 'SandboxLandingPage') {
  $router = $router -replace 'import LoginPage from "\.\./pages/LoginPage\.jsx";', 'import LoginPage from "../pages/LoginPage.jsx";' + "`r`n" + 'import SandboxLandingPage from "../pages/SandboxLandingPage.jsx";'
}

if ($router -notmatch "path: '/sandbox'") {
  $routeBlock = @"
  {
    path: '/sandbox',
    element: <SandboxLandingPage />,
  },
"@
  $router = $router -replace "(export const router = createBrowserRouter\(\[\s*)", "`$1$routeBlock"
}

Set-Content -Path $routerPath -Value $router -NoNewline

$login = Get-Content $loginPath -Raw

if ($login -notmatch 'getSandboxPersona') {
  $login = $login -replace 'import CrownLogo from "\.\./components/brand/CrownLogo";', 'import CrownLogo from "../components/brand/CrownLogo";' + "`r`n" + 'import { getSandboxPersona, getSandboxSchool } from "../sandbox/sandboxExperience";'
}

if ($login -notmatch 'function getSandboxQueryContext') {
  $helper = @'
function getSandboxQueryContext() {
  if (typeof globalThis === "undefined" || !globalThis.location) {
    return { mode: "", experience: "school", guidance: "guided", role: "", school: "", tour: "" };
  }

  const params = new URLSearchParams(globalThis.location.search || "");
  return {
    mode: params.get("mode") || "",
    experience: params.get("experience") || "school",
    guidance: params.get("guidance") || "guided",
    role: params.get("role") || "",
    school: params.get("school") || "",
    tour: params.get("tour") || "",
  };
}

'@
  $login = $login -replace '(async function fetchSandboxCredentials\(\) \{)', ($helper + '$1')
}

if ($login -notmatch 'const sandboxQuery = useMemo') {
  $login = $login -replace 'export default function LoginPage\(\) \{\s*const roles = useMemo\(\(\) => \(IS_SANDBOX \? SANDBOX_ROLES : PROD_ROLES\), \[\]\);', @'
export default function LoginPage() {
  const sandboxQuery = useMemo(() => getSandboxQueryContext(), []);
  const requestedPersona = useMemo(() => getSandboxPersona(sandboxQuery.role), [sandboxQuery.role]);
  const requestedSchool = useMemo(() => getSandboxSchool(sandboxQuery.school || requestedPersona.defaultSchoolId), [sandboxQuery.school, requestedPersona.defaultSchoolId]);
  const roles = useMemo(() => (IS_SANDBOX ? SANDBOX_ROLES : PROD_ROLES), []);
'@
}

$login = $login -replace 'const \[selectedSchoolId, setSelectedSchoolId\] = useState\(DEMO_SCHOOL\);', 'const [selectedSchoolId, setSelectedSchoolId] = useState(IS_SANDBOX ? requestedSchool.id : DEMO_SCHOOL);'
$login = $login -replace 'const \[selectedRole, setSelectedRole\] = useState\(roles\[0\]\?\.value \|\| "school_admin"\);', 'const [selectedRole, setSelectedRole] = useState(IS_SANDBOX ? requestedPersona.value : (roles[0]?.value || "school_admin"));'

if ($login -notmatch 'setEmail\(requestedPersona.email') {
  $login = $login -replace 'fetchSandboxCredentials\(\)\.then\(\(credentials\) => \{\s*setEmail\(credentials\.email\);\s*setPassword\(credentials\.password\);\s*\}\);', @'
fetchSandboxCredentials().then((credentials) => {
      setEmail(requestedPersona.email || credentials.email);
      setPassword(requestedPersona.password || credentials.password);
      setSelectedRole(requestedPersona.value || selectedRole);
      setSelectedSchoolId(requestedSchool.id || selectedSchoolId);
    });
'@
}

if ($login -notmatch 'sandboxQuery.experience') {
  $login = $login -replace 'localStorage\.setItem\("crown\.demo\.role", role\.value\);', @'
localStorage.setItem("crown.demo.role", role.value);
        localStorage.setItem("crown.demo.experience", sandboxQuery.experience);
        localStorage.setItem("crown.demo.guidance", sandboxQuery.guidance);
        localStorage.setItem("crown.demo.school", selectedSchoolId);
        localStorage.setItem("crown.demo.tour", sandboxQuery.tour || requestedPersona.tourTitle || "Guided proof path");
'@
}

if ($login -notmatch 'Demo path:') {
  $login = $login -replace '\{IS_SANDBOX && \(\s*<div className="warning-banner">Use demo data only\. Do not enter real school records\.</div>\s*\)\}', @'
{IS_SANDBOX && (
              <div className="warning-banner">
                Use demo data only. Do not enter real school records.
                {sandboxQuery.experience && <><br />Demo path: {sandboxQuery.experience} / {sandboxQuery.guidance}</>}
              </div>
            )}
'@
}

Set-Content -Path $loginPath -Value $login -NoNewline

Write-Host "Applied guided sandbox frontend patch. Run frontend tests before merge."
