CROWN HERITAGE LOCAL DEMO
Updated November 2, 2026 — five-module refresh pending full acceptance

START ON A DEMO COMPUTER
1. Install Python 3.12 and Node.js 24 with npm if missing.
   Tested runtime: Python 3.12 and Node.js 24.
   Python downloads: https://www.python.org/downloads/
   Node downloads: https://nodejs.org/en/download
2. Extract the downloaded ZIP completely into a normal writable folder.
3. Double-click Start-Heritage.cmd in the extracted CROWN folder.
   Do not use Start-Heritage-Demo.cmd in this outer source archive.
4. Keep the startup window open. First setup requires internet and can take
   several minutes while it downloads source/dependencies and creates the database.
5. The browser opens http://localhost:4173/sandbox. Select a role; no password
   is required. If the browser does not open, enter that URL on this computer.

This is a laptop/desktop demo. localhost refers to the computer running it;
opening that address on a phone will not reach the demo laptop.
The starter downloads the immutable source revision declared in
HERITAGE-SALES-MANIFEST.json. Use only the released ZIP whose manifest
revision matches the final certified source revision. Never change the
revision locally or redistribute an outdated starter.
Azure, Microsoft sign-in, and cloud database credentials are unnecessary.
Payments in the demonstrated flow are local manual demo entries; no external
payment is processed. Internet is required for initial installation.
Full offline operation of every integration has not been verified.

FIVE-MODULE RELEASE SCOPE AND VERIFICATION (NOVEMBER 2)
The immutable source pin for this candidate is
a1bf22fc1e520eba149ce943edcd747dbf75c1e5.
Verify that HERITAGE-SALES-MANIFEST.json has this exact source_sha before
using a candidate. This identifies the application source, not PR head.
Unmerged Camp PR #611 and Diadem pickup PR #612 are NOT included and cannot
be demonstrated as implemented features. A dashboard route alone does not
constitute full workflow acceptance. No real family/childcare records.

The canonical Windows GitHub Actions job must pass a STRICT five-module
fictional-data preflight, verify ZIP and source-download identity, and pass
the existing browser buyer rehearsal before its distributable ZIP artifact
is accepted. The preflight checks routes and synthetic record availability;
it does NOT prove five-module browser completion, permission boundaries,
persisted edits or safe failure behavior. Those workflows require separate
browser tests and actual laptop rehearsal. Until both pass, label this ZIP
a CANDIDATE, not a certified interactive five-module demonstration.

For a reproducible strict check after starter extraction and first source
download, open PowerShell in the extracted Heritage-<12-character SHA> source
folder (not the parent folder containing Start-Heritage.cmd):
  py -3.12 scripts/demo/start_heritage_local.py --prepare-only --five-module-preflight
The command must exit 0; save its output. If it fails, NO-GO. This does
not replace a real browser workflow rehearsal. Perform it in the isolated
fictional Heritage database only; do not alter a real school database.
Then run Start-Heritage.cmd from the parent starter folder, or run
  py -3.12 scripts/demo/start_heritage_local.py
from the source folder. Confirm http://localhost:4173/sandbox and inspect
the actual workflows with authorized personas, save/reload and denial tests.

The release acceptance checklist is: Diadem Daycare center/room setup and
custody checks; Extended Care AM/PM enrollment and attendance; Summer Camp
session, registration and saved state; Jireh Financial Aid application,
recommendation and persisted state; Jireh SGO organization/case visibility
and denied unauthorized operations. Do NOT claim SGO family submission or
processor case-management workflows without actual implementation and tests.
A functional gap in any module blocks the FULL five-module certification;
it must be disclosed instead of being represented by a dashboard tour.

STOP AND RESTART
Press Ctrl+C in the startup window to stop both servers. Saved fictional data
remains for the next session. Start again using the same Start-Heritage.cmd.
Only one demo should be running. Ports 8000 and 4173 must be available.
For a fresh rehearsal, extract this ZIP into a new folder and use a private
browser window. Preserve the old folder if its saved records are needed.
Avoid resetting during a presentation.

FIVE-MODULE FUNCTIONAL REHEARSAL (45 MINUTES; CANDIDATE ONLY)
These are required acceptance checks, not claims that all workflows exist.
Use only fictional Heritage data, document exact role and visible URL,
and record the outcome. Do not bypass a missing control or permission gate.

1. Diadem Daycare (10 min)
   Visit /diadem/daycare/setup and /diadem/daycare. Under an authorized
   director persona, inspect site and room setup; create or change only
   disposable synthetic configuration, then reload and verify stored state.
   Inspect actual roster and custody controls and expected denial cases.
   Pickup review and audited release changes from draft PR #612 are NOT
   present in this pinned release; do not demonstrate them as available.

2. Extended Care / Beforecare / Aftercare (9 min)
   Visit /before-care/dashboard and /after-care/dashboard and their roster
   pages. Verify separately scoped AM and PM enrollment, attendance, roles,
   saved/reloaded changes, stale-action rejection and forbidden-role denial.
   Do not claim draft PR #613 staff-isolation hardening is included.

3. Summer Camp (8 min)
   Visit /summer-camp-dashboard/setup and /summer-camp-dashboard/roster.
   Check school-scoped sessions and synthetic registrations, perform an
   authorized existing action if available, verify reload and a denied
   cross-school or unauthorized action. Draft PR #611 workflows are NOT
   included; a read-only tour cannot pass an interactive workflow gate.

4. Jireh Financial Aid (9 min)
   Visit /parent/financial-aid and /financial-aid with appropriate separate
   roles. Verify available family preparation, application, student-specific
   recommendation and award state; exercise an authorized save/reload, input
   validation and role denial. Do not claim that any award was actually paid.

5. Jireh SGO (9 min)
   Visit /jireh-sgo. Verify school/organization membership, program
   visibility and noncash application aggregates; verify unauthorized access
   is denied. At this pinned source, family-facing SGO intake and delegated
   processor case management are NOT demonstrated as complete. These are
   outstanding functional gaps and block full five-module certification.

Use /sandbox to change demo personas. Some dashboard cards may display
explicitly labeled examples or fallback summaries, not persisted records.
A route loading successfully does not satisfy save/reload or authorization.
Stop the presentation as a full functional certification if a required flow
is unavailable; disclose the scope instead of improvising a dashboard tour.

SCHOOL PROFILE
Heritage Christian Academy; PK-12; school year 2026-2027.
Seed counts, scenario records and displayed aggregates can differ between
source revisions and after demo transactions. Verify them in the isolated
local database; do not promise fixed enrollment or tuition totals.

VERIFICATION STATUS — NOVEMBER 2 CANDIDATE
The earlier October 15 Heritage distribution had historical test evidence
for a broader school buyer walkthrough. That evidence belongs to the older
source revision; none of its numeric pass counts certifies this new pin,
the five-module workflows, or the owner's physical Windows laptop.
For this candidate, accept only current exact-head Windows CI evidence,
a passing strict local five-module preflight, package/download identity
verification, and separately evidenced real-browser five-module actions.
No production, Azure, payment or real-school certification is claimed.

LIMITS
Native Windows/macOS execution still needs a check on the actual demo computer.
Azure remains unresolved. Wider modules, board/Jireh journeys, external services,
and full-product release certification were not established by this rehearsal.
The sales ZIP is a local demonstration starter, not an Azure deployment.
Prior historical proof does not certify the final shipped revision.
Use the matching final Windows CI artifact and the owner laptop rehearsal
before authorizing independent sales demonstrations.

SALES HANDOFF CONTROL
1. Inspect HERITAGE-SALES-MANIFEST.json; confirm its source_sha matches the
   released certification/approval record before distributing the package.
2. Extract the ZIP and run Start-Heritage.cmd on the actual Windows laptop.
3. Rehearse all five module workflows with saved/reloaded changes where
   implemented, expected role denials, and an explicit record of gaps.
4. Keep the laptop local; do not share localhost via port-forwarding or expose
   the open-session local sandbox on the public internet.
5. Give sales staff this README and the five-module acceptance evidence.
   The older buyer presenter script is supplemental historical material only.
6. If startup, a protected route, seed integrity, or role denial fails: NO-GO.
   Record the build SHA and failure; never bypass authorization to present.
7. The Windows runner proves CI execution, not the physical sales laptops.
