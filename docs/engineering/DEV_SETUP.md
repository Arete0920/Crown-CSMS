# CROWN Engineering Setup and Execution Guide

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Purpose:** Tool-neutral source of truth for repository setup and controlled execution

## 1. Operating model

CROWN engineering is vendor-neutral and editor-neutral.

The authoritative chain is:

```text
Founder/Product Owner direction
  -> GitHub repository, branch, pull request and issue state
  -> GitHub Actions validation and evidence
  -> approved deployment workflows
  -> deployed runtime and operational evidence
```

GitHub is the source of truth for accepted source, history, pull requests, workflow results and release evidence. Local editors, terminals, development assistants and automation utilities are optional implementation aids. They are not product, architecture, security, compliance or release authorities.

The GitHub connector is the primary interaction path when it supports the required repository action. Local execution is used only when a task genuinely requires a local runtime, browser, secret-bearing environment, command not exposed by the connector, or detailed artifact inspection.

No paid coding-assistant subscription or specific editor is required.

## 2. Repository access

Access requires the appropriate repository permissions.

```bash
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026
```

Work from an isolated branch or worktree. Do not commit directly to `main`.

## 3. Optional local workspace

Use any suitable editor or development environment capable of working with Python, Node.js, Git and the repository structure.

Examples include command-line tools and mainstream integrated development environments. No editor-specific output is accepted as release evidence unless it is retained and independently reconciled with GitHub, CI or deployed-runtime evidence.

Before local work, record:

- repository;
- branch;
- HEAD SHA;
- exact objective;
- allowed files;
- prohibited files;
- validation commands;
- rollback or reversion approach.

## 4. Python environment

Use a repository-root `.venv`.

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

## 5. Frontend dependencies

```bash
cd frontend/dashboards
npm ci
cd ../..
```

Use the Node and npm versions required by the current package and CI configuration. Do not upgrade dependencies as part of unrelated work.

## 6. Local configuration and secrets

Use only local placeholder or approved development values.

Never commit:

- passwords, API keys or tokens;
- production environment files;
- production database dumps;
- real student, family, staff, financial, health or school data;
- tenant secrets;
- private certificates or keys;
- confidential communications;
- payment-provider credentials.

Where the local secrets template is present:

Linux or macOS:

```bash
cp local.secrets.example local.secrets
```

Windows PowerShell:

```powershell
Copy-Item local.secrets.example local.secrets
```

Payment processing remains disabled and outside the active implementation lane until the Founder/Product Owner selects a provider, a commercial agreement is signed and a bounded implementation plan is authorized.

## 7. Backend verification

```bash
python backend/manage.py check
pytest backend -m "not integration and not slow"
```

Run focused tests before broad suites.

Do not create or apply new migrations unless the approved work explicitly includes migration changes. Production migration authority is controlled separately from ordinary web startup and must follow the exact-SHA migration workflow.

For an approved local development database only:

```bash
python backend/manage.py migrate
```

## 8. Start the backend

```bash
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

Verify:

```bash
curl -i http://127.0.0.1:8000/health/
```

Windows PowerShell may use `Invoke-RestMethod` or `curl.exe` explicitly.

Expected: HTTP 200, a JSON response and no traceback.

## 9. Start the frontend

In a second terminal:

```bash
cd frontend/dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

Verify:

```bash
curl -i http://127.0.0.1:3000/
```

Expected: HTTP 200.

## 10. Frontend verification

```bash
cd frontend/dashboards
npm run lint
npm run test:unit
npm run test:contracts
npm run build
```

Accessibility release check:

```bash
npm run test:release:a11y
```

Browser and route checks must identify whether they prove scaffold, local, preview, sandbox or deployed-runtime behavior. Local success does not substitute for authenticated exact-SHA deployed-runtime evidence.

## 11. Controlled change workflow

1. Inspect live GitHub state and the current controlling issue or packet.
2. Create or use one isolated branch for one bounded purpose.
3. Declare the exact allowed change surface and exclusions.
4. Inspect source before editing.
5. Make only the approved change.
6. Run focused validation, then required broad validation.
7. Inspect the final diff file by file.
8. Push the isolated branch.
9. Open a draft pull request.
10. Allow required checks to settle on the unchanged head.
11. Resolve actionable review findings.
12. Merge only when repository policy and evidence requirements are satisfied.
13. Deploy only through approved GitHub workflows.
14. Capture post-deploy identity and runtime evidence where applicable.

Do not use broad copy-and-paste changes, hidden destructive scripts or unreviewed generated output.

## 12. Pull-request closeout

Every pull request must identify:

- purpose and bounded scope;
- base and head SHA;
- files changed and intentionally excluded;
- validation performed;
- known failures, limitations or unknowns;
- security, tenant, compliance, migration and data implications where relevant;
- independent-review status where required;
- rollback or reversion approach;
- release claims explicitly not made.

Pending, failed, cancelled, stale or action-required checks do not constitute PASS.

## 13. Human accountability and tool attribution

CROWN is founder-directed, collaboratively developed, human-reviewed and human-accepted.

Development tools, automation services, editors and assistants may support implementation. They do not own requirements, approve architecture, accept security risk, certify compliance or authorize release.

Normal engineering and customer-facing documentation should describe the verified engineering process and evidence rather than emphasizing a particular tool or vendor. Historical tool references may remain where needed for provenance, licensing, security review or incident reconstruction.

## 14. Future transferability verification

Clean-room successor or ownership-transfer execution is not an active authorized lane at this time. Any future exercise must be opened explicitly by the Founder/Product Owner after the business direction and scope are established.

The repository should nevertheless remain reproducible and documented. No current document may claim that a successor, buyer or new owner has been selected, approved or scheduled.

A future authorized transferability exercise may verify that a qualified engineer can clone, configure, test, modify, deploy, operate, roll back and recover CROWN without undocumented founder-only assumptions. Until that exercise is authorized and completed, it remains a proposal rather than a release claim.

## 15. Authority boundary

This guide does not certify pilot, production, legal compliance, payment processing, transferability or release approval. Use `docs/CURRENT_RELEASE_STATUS.md` and current live GitHub and runtime evidence for release authority.
