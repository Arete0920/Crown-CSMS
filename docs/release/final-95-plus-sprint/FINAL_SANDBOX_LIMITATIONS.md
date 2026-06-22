# CROWN Sandbox Known Limitations - 2026-06-22

**Status**: Explicit documentation of sandbox-specific constraints

## Performance and scale limitations

| Constraint | Sandbox | Production | Impact |
|-----------|---------|------------|--------|
| Concurrent users | Limited QA scale | Higher scale target | QA testing only |
| Database size | Limited sandbox dataset | Production-sized dataset required | No multi-year history |
| File storage | Limited sandbox storage | Production storage required | Limited media/reports |
| API rate limits | Sandbox-dependent | Production controls required | Load testing requires a separate load environment |
| Batch job execution | Bounded sandbox execution | Production sizing required | Large exports require production-like verification |

## Feature limitations

### Third-party integrations (demo/stub mode only)
- Zoom: sandbox accounts or stub behavior only
- Google Classroom: no real class roster sync claimed here
- Schoology: integration stubbed with mock data where present
- Skyward: no live SIS sync claimed here
- PowerSchool: no live data exchange claimed here
- Clever: no automated roster import claimed here
- Follett Destiny: disabled or sandbox-only where present

### Payment processing
- Stripe: sandbox/test mode only where configured
- No real credit card charges
- Test card numbers only where test processor is enabled
- Payment reconciliation is not claimed as real-time production behavior

### Communication channels
- Email: sandbox/demo behavior only
- SMS: disabled or sandbox-only where configured
- Zoom: sandbox meeting links only where configured
- Slack: no production integration claimed here

### Reporting
- Reports use fabricated or sandbox-marked data
- Export formats are sandbox-marked where generated
- Dashboard metrics reflect demo patterns unless backed by live/snapshot services
- No ad-hoc SQL querying

### Accounting/Financial
- Ledger entries are sandbox-marked where generated
- No real revenue recognition
- Financial reports are educational examples unless separately certified
- Year-end close and tax reporting are not production-certified by this packet

## Module status

| Module | Sandbox status | Notes |
|--------|----------------|-------|
| Admissions | Candidate | Public workflow evidence exists; deployed sandbox verification required |
| Academics | Candidate | Classroom workflow evidence exists; deployed sandbox verification required |
| Attendance | Candidate | Internal dashboard scope certified; deployed sandbox verification required |
| Billing/Aid | Candidate | Invoicing visible-state evidence is sandbox-only |
| Communications | Candidate | Internal dashboard scope certified; channel delivery sandbox-only |
| Registrar | Candidate | Internal dashboard scope certified; deployed sandbox verification required |
| HR | Partial | Staffing module available; payroll remains stub/limited |
| Accounting | Candidate | Ledger uses sandbox markers; production accounting not certified here |
| Sports/Athletics | Candidate | Athletics dashboard evidence is in Batch 5 proof lane |
| Summer Camp | Candidate | Batch 5 proof lane evidence exists; final CI/main verification required |
| Extended Care | Candidate | Batch 5 proof lane evidence exists; final CI/main verification required |
| Dashboard analytics | Candidate | 34/40 certified on main; final six in PR #1153 pending merge and main verification |

## Infrastructure limitations

- Single-server sandbox deployment unless separately configured
- CDN, backup redundancy, and disaster recovery are not certified by this packet
- Database backups and reset behavior require environment-specific verification

## Data limitations

- No multi-year historical production data
- No incremental sync from production
- No real-time webhooks claimed here
- Student/family data is fabricated or sandbox-marked
- Cross-school data visibility is expected to be blocked, but deployed sandbox verification is still required

## Not recommended for

- Load testing
- Production-grade customer operations
- Integration testing with live third-party APIs
- Multi-month regression testing
- Staff training with real student or family data

## Recommended uses

- Feature development and local testing
- QA regression testing
- API contract validation
- UI/UX acceptance testing
- Security vulnerability assessment
- Deployment procedure validation
- Staff familiarization with sandbox UI/UX
