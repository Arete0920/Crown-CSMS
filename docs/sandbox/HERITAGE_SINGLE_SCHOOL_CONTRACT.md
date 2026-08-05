# Heritage Single-School Sandbox Contract

The CROWN demonstration sandbox exposes exactly one school: **Heritage Christian Academy**.

## Invariants

- The frontend sandbox school catalog contains one entry with key `heritage-core`.
- The backend sandbox catalog contains one entry with key `heritage-core`.
- Unknown, stale, or legacy school identifiers normalize to Heritage Christian Academy.
- No Trinity, Grace Covenant, Bethlehem, Good Shepherd, Emmanuel, Cedar Ridge, or other sandbox school is exposed.
- Persona switching changes role context only; it does not change the sandbox school.
- The Heritage sandbox remains demo-data-only and tenant-scoped.

Automated frontend and backend tests enforce this contract.
