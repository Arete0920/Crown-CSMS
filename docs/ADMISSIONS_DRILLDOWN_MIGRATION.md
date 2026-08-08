# Admissions Drilldown Response Compatibility

**Current authority date:** 2026-08-08  
**Canonical endpoint:** `/api/v1/admissions/drilldown/`  
**Compatibility alias:** `/api/admissions/drilldown/`

## Current contract

`results` is the canonical collection key for new clients.

`rows` remains a supported compatibility alias and currently contains the same page payload as `results`. The previously documented June 1, 2026 removal date was not executed and is superseded by this document.

Do not remove `rows` as a handoff/hygiene change. Removal requires a separately versioned client-retirement change with repository search, frontend migration, contract tests, and exact-head CI proof showing no supported consumer still depends on it.

## Historical response-header note

The current runtime may still emit the historical `X-Deprecated-Field` header containing the old June 1, 2026 sunset text. That date is no longer authoritative. Clients must treat the header as a deprecation indicator only, not as an active removal schedule. The response-body compatibility contract in this document governs until the runtime header is changed in a separately verified implementation edit.

## Client guidance

Preferred:

```javascript
fetch('/api/v1/admissions/drilldown/?stage=inquiry')
  .then((res) => res.json())
  .then((data) => {
    data.results.forEach((applicant) => {
      // process applicant
    });
  });
```

Compatibility:

```javascript
const applicants = data.results ?? data.rows ?? [];
```

## Response shape

```json
{
  "academic_year": "2026-2027",
  "stage": null,
  "source": null,
  "total": 94,
  "limit": 25,
  "offset": 0,
  "results": [],
  "rows": []
}
```

`results` and `rows` must remain identical while the compatibility alias is supported.

## Governance

- `results`: canonical.
- `rows`: compatibility alias.
- No fixed removal date is currently authorized.
- A future removal must update runtime behavior, frontend consumers, API-contract documentation, and tests in the same reviewed change.
