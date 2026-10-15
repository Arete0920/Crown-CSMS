CROWN HERITAGE LOCAL DEMO
Revised October 15, 2026

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

STOP AND RESTART
Press Ctrl+C in the startup window to stop both servers. Saved fictional data
remains for the next session. Start again using the same Start-Heritage.cmd.
Only one demo should be running. Ports 8000 and 4173 must be available.
For a fresh rehearsal, extract this ZIP into a new folder and use a private
browser window. Preserve the old folder if its saved records are needed.
Avoid resetting during a presentation.

DEMO RUN ORDER (ABOUT 40-50 MINUTES)
1. School Administrator: show Heritage context, dashboard, registrar,
   attendance, gradebook, communications, and an administrative exception action.
   Open classroom operations from the expandable section when needed.
2. Parent, seeded accepted Jordan Reed scenario: open Admissions Status and
   accept the demo enrollment agreement. Show the completed student handoff,
   family billing, attendance, progress, and communications. Do this before
   submitting a new application; admissions status follows the newest application.
3. Parent, new Avery Reed application: use the prefilled application wizard.
   Set the primary guardian email to parent.reed@heritage.example.org.
   Show draft saving, document-readiness acknowledgements, submission, and the
   exact persisted application in Admissions Status. The implemented document
   step is a readiness checklist; binary document upload is not claimed.
4. Admissions Director: review and accept the seeded Carter applicant; demonstrate
   canonical-ready conversion in the pipeline. This is a separate seeded scenario,
   not a claim that the new Avery application was approved in the previous step.
5. Finance Director: show the Reed family obligation, apply a manual demo payment,
   reload, and show reconciliation, allocation history, void handling, and refund
   controls. The action is idempotent; a completed payment remains completed.
6. Teacher: show assigned classes, record attendance, create/save/reopen a lesson
   plan, link a curriculum resource, and create persisted classwork. Open the
   classroom records section for assignments and feedback.
7. Student: show schedule, assignments, progress, attendance, communications,
   and Student Work. Demonstrate denial of administrative or finance access.

Use /sandbox to select the next persona. Role switching creates a fresh protected
demo session. Narrate the source labels on dashboards: some cards contain
explicitly labeled sample or fallback summaries alongside actual local records.

SCHOOL PROFILE
Heritage Christian Academy; PK-12; school year 2026-2027.
The baseline seed has 700 students. Scenario-specific records can increase live
counts. The baseline profile is not a promise that every displayed aggregate
equals 700 after transactions. Tuition installments run August through July.

VERIFICATION
The final runtime revision passed eight browser authority checks covering six
roles, 34 route visits, and mobile entry. Sixteen saved-action checks passed with
independent pristine fixtures, including reload persistence and role denials.
Fifty-two focused frontend checks, 55 Parent360 checks, 10 identity/seed/launcher
checks, and the five launcher checks passed. First creation from an empty SQLite
database and a manual demo payment passed. The pinned source download, extraction,
source identity, and repeat-install reuse were tested on Linux.

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
3. Demonstrate all six personas and at least one saved/reloaded school workflow.
4. Keep the laptop local; do not share localhost via port-forwarding or expose
   the open-session local sandbox on the public internet.
5. Give sales staff this README and the canonical buyer walkthrough script:
   docs/sandbox/CROWN_BUYER_DEMO_PRESENTER_SCRIPT_20260818.md.
6. If startup, a protected route, seed integrity, or role denial fails: NO-GO.
   Record the build SHA and failure; never bypass authorization to present.
7. The Windows runner proves CI execution, not the physical sales laptops.
