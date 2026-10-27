# Automatic request audit privacy

Scope: `audit.AuditLog` records written by `AuditMiddleware` and the early
director-action denial path, plus route labels in the application-owned
`crown.request` structured logs and `crown.performance` slow-request warnings. This application control does not configure
infrastructure, telemetry providers, access logs, deployment or legal compliance.

## Stored request evidence

State-changing HTTP requests record the actor identifier when available, method,
server-defined route template, response status and the model's creation timestamp.
For example, a resolved password-reset URL is represented by its configured
`/accounts/reset/<uidb64>/<token>/` template, not the actual user identifier or
reset token. Unresolved paths use the fixed `/<unresolved>` marker. Static routes
keep their existing path labels; regex registrations retain their server-defined
pattern syntax. Early director denials retain only exact,
hardcoded API aliases; arbitrary prefixes are never copied into audit records.

Automatic request audit rows do not copy query strings, request/response bodies,
authorization headers, cookies, exception messages or stack traces. The route
label is bounded by the existing 255-character model field. GET, HEAD and OPTIONS
do not create these automatic request rows.

Domain-specific audit events remain responsible for object identifiers, school
attribution, permission decisions and sensitive-access history. A route template
is not proof that a particular business change succeeded, and this change does
not make the audit table immutable or provide cross-school read authorization.
The same safe route label is used by the application-owned general request and
slow-request loggers after downstream URL resolution. Unresolved or early
responses use the fixed marker. Response content, status, correlation-ID behavior,
timing headers and slow-request thresholds are preserved. This does not sanitize
caller-supplied correlation identifiers or configure framework, proxy, access,
APM or other domain logs; those retain separate contracts and require review.

## Persistence failures

An audit storage failure emits an ERROR from `audit.request_logging`, with
`audit_event=request_audit_write_failed`, the exception class and the method.
Original exception text and tracebacks are withheld because they can contain
SQL parameters, URL values or credentials. The existing application response is
preserved. This signal does not mean an audit row was saved, that a completed
business write was rolled back, or that an external alert was delivered.
Critical transactional/domain auditing remains separately required.

## Historical evidence and rollout

Historical rows are not rewritten or deleted. Any review of credential-bearing
historical audit paths must use restricted access and the applicable retention
and legal-hold process. Never copy those raw values into public reports.

Before deployed acceptance, verify route-template and denial behavior with
synthetic data and verify the actual audit-failure signal reaches the responsible
operator. Source tests are not proof of live logging, incident response, adopted
privacy policy or regulatory compliance.

Rollback: revert this application-only change through the normal release
process; preserve existing audit evidence. No schema migration is introduced.
