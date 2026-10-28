# Survey Intelligence — Administrator UX, Research Quality and Action Acceptance

**Status:** Acceptance specification; implementation and current-head evidence not implied.
**Tracking:** Issue #204 SI-P03, SI-P06, SI-P07.
**Scope:** Adult anonymous pilot first; confidential/identified/student flows explicitly out of scope.

## The product journey

### Administrator: school-scoped survey lifecycle

1. School administrator signs into the existing CROWN school tenant and receives an explicit survey.view or survey.edit permission.
2. Create survey wizard accepts instrument purpose, audience, meaningful short name and original author-approved question version; saves DRAFT, not an active survey.
3. Builder displays choice/scale anchors, optional question handling, preview on mobile, accessible labels, high contrast and keyboard navigation.
4. Publishing requires distinct approve permission, approved respondent notice, configured retention, availability window and reviewable complete snapshot. Publication creates immutable version, not an in-place edit of answers or questions.
5. Distribution produces an expiring, revocable audience-appropriate invitation method; respondent and support staff see the intended notice and a skip/exit option.
6. Status screen distinguishes eligible invitations, deliveries, opens, completed submissions, closed/revoked state, and counts with unknown denominators. It must not conflate invitations with individual respondents for truly anonymous surveys.
7. School owner closes collection; reports reflect a provenance-bearing publication version and data window. Confidential/raw exports stay unavailable in the first pilot.
8. Aggregate finding is converted into a school-owned improvement action requiring human approval, responsible party, milestone, baseline, follow-up and a review decision.
9. Re-open/edit behavior never rewrites an already answered instrument; future versions require distinct approval and comparison analysis.
10. Errors show actionable messages without displaying sensitive details or confirming another tenant's resource identifiers.

### Respondent: mobile-first adult anonymous journey

1. Access authorized active URL during collection window; expired/revoked/unpublished link produces a neutral unavailable screen.
2. Show school purpose, voluntary participation, intended privacy mode, respondent notice and school contact before any answer entry.
3. Answer supported question types with clear 1–5 scale endpoints and optional skip. The UI must not force skipped optional responses or imply non-applicable = neutral.
4. Accessible progress, focus management, error summary, keyboard-only navigation, responsive single-column view, screen-reader question labels, reduced-motion handling.
5. Server independently validates type, length, key, publication version, school, expiry and authorization; no browser-only security reliance.
6. Successful submit returns non-identifying confirmation, not any raw respondent ID or school-wide report.
7. Network retry/double-tap behavior must follow proven idempotency rules and not create duplicate answers.
8. Users may leave without submission; no partial data is saved without an explicitly approved partial-response design.

## Minimum executable acceptance cases

| Case | Expected behavior | Required proof |
| --- | --- | --- |
| ADM-01 School admin creates draft | Only authorized school draft and its questions persist; no publication | API + DB + UI/E2E |
| ADM-02 Non-editor writes | 403 and zero writes | Role-negative API |
| ADM-03 Cross-school UUID read/write | 403/404 and no foreign data/side effect | Two-tenant API and query log |
| ADM-04 Invalid schema/oversize request | 400, atomic no-write | Input limit and DB tests |
| ADM-05 Saved draft replacement | Current school editor, matching revision, atomic replacement; retained question keys preserve identity/server tags | API + DB; UI acceptance separate |
| ADM-06 Stale or simultaneous editors | Missing revision 428; changed revision 412; exactly one concurrent matching-revision writer succeeds | API + PostgreSQL lock tests |
| PUB-01 Version approval | Matching immutable snapshot, hash, notice, signer and timestamp | Migration + service + DB tests |
| PUB-02 Published question edit | Denied or new version; old report unchanged | Version contract regression |
| PUB-03 Unapproved/minor/protected survey | Publish denied unless separate approval path satisfied | Negative API/evidence |
| RSP-01 Correct adult response | Exactly one response/typed answers bound to version | API+DB+browser |
| RSP-02 Invalid choice/NaN/unexpected field | 400 and no partial persistence | Negative tests |
| RSP-03 Expired/revoked link | No form display or writes | Browser/API |
| RSP-04 Repeat submit and rapid retries | Idempotent per approved policy | Concurrency, load and retry proof |
| RSP-05 Anonymous data-flow | No identifier or reconstructable answers-to-invite trail in app/proxy/logs | Threat-model test plus infra log audit |
| REP-01 Fewer than 10 valid submissions | Entire aggregate suppressed; no raw identity | Report/API test |
| REP-02 Any small nonempty bucket | Suppress whole distribution; prevent deduction across views | Small-cell, complementary attacks |
| REP-03 One missing answer | Question denominator reflects answered_count; nonresponse visible | Statistical unit test |
| REP-04 Two incomparable instrument versions | Comparison unavailable with explanation | Version drift test |
| REP-05 Unentitled consumer or role | No API/report access even by direct URL | Entitlement + RBAC negative |
| REP-06 No identified/financial/spiritual student profiling | No individual inference, no disclosure to guidance service | E2E data-flow audit |
| ACT-01 Improvement initiated | Recorded approved finding, owner, baseline and due date | API+UI+audit |
| ACT-02 Follow-up | New evidence linked but prior source/report preserved | Version + audit |
| DEP-01 Staging acceptance | Recorded exact SHA, migration checks, incident/rollback practice | Environment packet |

**A passing backend test or generic health check is not equivalent to these tests passing.**

## Saved draft API contract

`GET /api/v1/survey-intelligence/surveys/{id}/` returns the current definition,
an opaque `revision`, and a matching quoted HTTP `ETag`. Creation and library
entries expose the same revision. This is a content/write revision, not an
approval, publication version, entitlement or credential.

An editor replaces a saved draft with `PUT` to that detail route, the exact
quoted `If-Match` value from the last read, and only `name`, `purpose` and
`questions`, using the existing bounded draft validator. A missing condition
returns 428; a stale, wildcard, weak or otherwise nonmatching condition returns
412. The caller must reload and reconcile its edits; an automatic overwrite or
blind retry is not permitted. A successful replacement returns a fresh revision,
including when submitted content is unchanged. A timeout requires a readback
before deciding whether another write is appropriate.

The existing active-school and `survey.edit` permission checks apply. A draft
that is active, closed, archived, public-enabled, anonymous-enabled, previously
published or response-bearing is ineligible (409). No school, status, audience,
public flag, tag, publication or response field is writable through this API.
Retained question keys preserve their row identity and server-owned strategic
tags; omitted keys are removed only from an eligible draft. Definition and
question writes roll back together on storage failure.

Replacement and the canonical publication service take the same survey-row
lock. PostgreSQL acceptance must prove competing editors and both edit/publish
commit orderings, including an observed database lock wait. SQLite unit tests
alone do not establish that concurrency result. These API cases do not complete
the saved-edit UI, hosted browser journey, publication/distribution workflow,
research review or pilot acceptance.

## Statistical and research rules

- Unit of analysis must be explicit: completed response, answered question, household when lawfully identified, or eligible invitation. Do not mix units in a chart.
- Invitation response rate is calculated as valid unique completions divided by eligible delivered invitations, only where both can be measured reliably and privacy policy permits. If no reliable denominator, show **response count only**, not a fabricated percentage or 0%.
- When different surveys are open simultaneously, keep survey/publication cohorts separate by school, audience, approved dates and version.
- For each item show the entire ordinal frequency distribution where safe. A scale mean may be included only with a clear ordinal limitation and no causal or clinical claim; pilot defaults to distributions.
- Describe missingness: optional skips do not count as neutral; answered_count is the denominator for each question when reportable.
- Pilot threshold of 10 valid total responses and minimum 5 in each visible nonempty bucket is a **provisional engineering suppression rule**, not proof against inference attacks. Restrict complementary, overlapping, geographic, grade, demographic, export, cached and time-difference views.
- No cross-school benchmarks or respondent-level retention predictions. No inferential statistical claims until question reliability, sample frame, response bias, effect size and comparability are independently assessed.
- Never compare modified question prompts or scale anchors across versions without a reviewed comparability record. Separate operational enrollment facts from survey perceptions.
- Exclude unreviewed free-text answers and protected fields from aggregate reports.
- Include generation time, source publication hash, school, window, measured denominator, report privacy mode, suppression flags and limitations before presenting data as decision support.

## Improvement action object and leadership workflow

| Field | Required semantics |
| --- | --- |
| school_id | Canonical tenant; no cross-school links |
| source_report_id | Approved aggregate report, immutable publication/version and provenance |
| finding_summary | Human-authored statement of supported evidence and uncertainty |
| desired_outcome | Specific school-operational objective, not individual faith/character scoring |
| baseline | Correctly labeled survey distribution or operational KPI and data window |
| action_owner | School-authorized staff member, with role and accountability |
| due_date/review_date | Review checkpoint and expected follow-up survey or KPI source |
| approved_by / approved_at | Explicit human decision and audit evidence |
| action_steps | Concrete tasks; owner controls subsequent changes |
| outcome | Observed results, date and limitations, separated from forecast/hypothesis |
| status | Draft, approved, in progress, review due, completed, canceled; transitions audited |

**Illustrative school-owned action:** Finding: some respondents report difficulty locating admissions process information. Objective: make the instructions easier to find and understand. Actions: redesign admission steps page, ask three adults to test comprehension, reassess the same question after a suitable period. Do not assert improvement until comparable follow-up evidence exists.

### Leadership sign-off

- School survey sponsor approves purpose, action plan, measurement, owner and follow-up.
- Product feature prevents automated adverse student decisions, financial awards, enrollment denials, or private staff scoring.
- Kingdom Path may use purpose-approved aggregate admissions context; Compass may use governed institutional aggregates. Neither owns Core identity or unrestricted raw responses.
- An action can close as administratively completed without claiming a causal effect; outcomes require a separate evidence decision.

## Completion record (to be filled after live exercise)

Case IDs executed: NOT VERIFIED.
Test SHA/environment: NOT VERIFIED.
School pilot acceptance: NOT VERIFIED.
Accessibility assessment: NOT VERIFIED.
Privacy/IP sign-off: NOT VERIFIED.

A spec is complete when reviewable and placed under change control; runtime acceptance remains separate.
