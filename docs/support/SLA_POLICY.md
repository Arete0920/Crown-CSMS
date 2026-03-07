# Crown Support SLA Policy

## Response Time Commitments

| Priority | Definition | First Response | Resolution Target |
|---|---|---|---|
| **Critical** | Platform down, all users affected, data at risk | 2 hours | 4 hours |
| **High** | Core workflow blocked for multiple users | 8 hours | 24 hours |
| **Medium** | Significant feature degraded, workaround exists | 24 hours | 72 hours |
| **Low** | Minor issue, cosmetic, enhancement request | 48 hours | 2 weeks |

*All times are calendar hours unless otherwise contracted.*

---

## Escalation Triggers

Tickets are automatically escalated (status → `escalated`) when:

| Priority | Escalated At |
|---|---|
| Critical | 2 hours with no resolution |
| High | 8 hours with no resolution |
| Medium | 24 hours with no resolution |
| Low | 48 hours with no resolution |

Escalation fires a `crown.support` WARNING log entry and, when integrated,
notifies the on-call engineer via Slack/PagerDuty.

---

## Submitting a Ticket

API:
```http
POST /api/v1/support/tickets/
{
  "title": "Billing run failed",
  "description": "The October billing run did not complete.",
  "priority": "high"
}
```

Response includes `sla_deadline` so clients can track their SLA window.

---

## Escalation Engine

Celery beat runs `support.tasks.escalate_overdue_tickets` hourly.
Manual trigger: `POST /api/v1/support/escalation/run/` (platform ops only).

---

## Contact

For Critical tickets outside normal hours, escalate directly to:
- Engineering on-call (configure in `CROWN_ONCALL_WEBHOOK` env var)
