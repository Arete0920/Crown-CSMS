CROWN HERITAGE LOCAL DEMO
Updated November 4, 2026 - source/operator guidance; release NOT certified

START ON A DEMO COMPUTER
1. Install Python 3.12 and Node.js 24 with npm if missing.
   Tested runtime: Python 3.12 and Node.js 24.
   Python downloads: https://www.python.org/downloads/
   Node downloads: https://nodejs.org/en/download
2. Extract the downloaded ZIP completely into a normal writable folder.
3. Double-click Start-Heritage.cmd in the extracted CROWN folder for a BASIC
   historical sales demo. This default basic source pin is NOT the current
   five-module integration. For five modules use a reviewed candidate with
   five_module_candidate=true in HERITAGE-SALES-MANIFEST.json, or the
   explicit local source-checkout command below.
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

FIVE-MODULE SOURCE AND VERIFICATION
The accepted main branch contains Camp #611, Diadem #612, Extended Care
#613, Jireh SGO family/processor #616/#622 and parent Financial Aid #620.
The joined Windows candidate is coordinated through issue #617 and PR #615.
Confirm the current GitHub merge/source status before presenting.

A route or merged feature is not proof of an operational demonstration.
Use a source-matched ZIP manifest and completed Windows browser evidence,
then independently verify the owner's physical laptop and staff roles.
The starter remains UNCERTIFIED until a separate release decision. No real
children/families, SGO scholarships, funds, payment provider or Azure access.

For an exact reviewed integrated Git checkout, from the repository root:
  git rev-parse HEAD
  py -3.12 scripts/demo/start_heritage_local.py --five-module-demo
This explicit mode seeds guarded fictional data, runs the STRICT source/data
preflight and starts only the loopback services after all gates pass.
The ordinary Start-Heritage.cmd/basic launcher may not enable SGO intake.

For a non-browser preflight on a FRESH isolated checkout:
  py -3.12 scripts/demo/start_heritage_local.py --prepare-only --five-module-preflight
Do not execute both modes successively on an in-use fictional database:
five-module seeding may regenerate local SGO account credentials.
Do not remove failed gates, fake tenant/guardian permission or replace
blocked custody/health records with invented clearance.

STOP AND RESTART
Press Ctrl+C to stop both servers. Preserve fictional audit and custody
records, and use a fresh isolated folder for a new source revision.
Ports 8000 and 4173 must be free. Do not rerun explicit SGO seeding in the
middle of a presentation: it can invalidate earlier local credentials.

FIVE-MODULE FUNCTIONAL REHEARSAL (45 MINUTES; CANDIDATE ONLY)
This is an OWNER LAPTOP acceptance script, not a claim that the owner has
already manually completed the workflows. Use synthetic Heritage data.

1. Diadem Daycare (10 min)
   Visit /diadem/daycare/setup as an authorized director, then
   /diadem/daycare as a specifically authorized DAYCARE_STAFF identity.
   Verify guardian identity, persisted one-time custody release, audit,
   and revoked/expired/foreign-school denial. The basic /sandbox role
   selector does NOT issue DAYCARE_STAFF access. A separately verified
   local-only presenter handoff is REQUIRED; never grant this to an admin.

2. Extended Care / Beforecare / Aftercare (9 min)
   Inspect /before-care/dashboard and /after-care/dashboard and rosters.
   Verify separate AM/PM staff sessions, authorized custody changes,
   independent GET after POST, reload and stale/foreign-school denial.

3. Summer Camp (8 min)
   Visit /summer-camp-dashboard/setup and /summer-camp-dashboard/roster.
   Save and read back setup and fictional registration; prove blocked
   check-in remains blocked pending health/guardian/staff clearance.

4. Jireh Financial Aid (9 min)
   Under a fictional parent open /parent/financial-aid and submit;
   confirm the exact authorized saved application GET and reload.
   Under approved school role inspect /financial-aid. No award posting
   or disbursement is implied by an offered synthetic sample.

5. Jireh SGO (9 min)
   Arete processes applications FOR existing independent partner SGOs.
   Use /jireh-sgo/sign-in and private local fictional credentials from
   .local-backups/heritage-demo/sgo-credentials.txt, NOT /sandbox.
   Show family consent/POST/GET, delegated processor correction,
   family resubmission, saved revision and cross-SGO denial.
   Never describe Arete as holding funds or deciding scholarship awards.

If a required live operation, role boundary, or saved-record verification
fails on the laptop, do NOT substitute a dashboard tour. Release stays NO-GO.

SCHOOL PROFILE
Heritage Christian Academy; PK-12; school year 2026-2027.
Seed counts, scenario records and displayed aggregates can differ between
source revisions and after demo transactions. Verify them in the isolated
local database; do not promise fixed enrollment or tuition totals.

VERIFICATION STATUS - ENGINEERING, NOT RELEASE
Current integrated-source CI/Windows browser evidence is tracked in #617,
including actual protected role, custody, data and responsive tests.
A new source commit requires fresh exact-head checks; historical successes
do not certify a later ZIP or a physical Windows laptop.
Outstanding buyer-release acceptance includes a usable local Diadem
presenter entry, visual/navigation consistency, exact SHA package audit,
owner-operated full walkthrough and final release signoff.
No Azure/production/real-school/payment certification is implied.

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
