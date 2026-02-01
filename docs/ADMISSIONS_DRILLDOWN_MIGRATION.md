# Admissions API Migration Guide: `rows` → `results`

## Summary

The Admissions Drilldown endpoint (`/api/v1/admissions/drilldown/`) is deprecating the `rows` response key in favor of `results`. Both keys currently return identical data, but `rows` will be removed on **2026-06-01**.

## Timeline

- **Now**: Both `rows` and `results` keys present in response
- **2026-06-01**: `rows` key removed, only `results` remains

## Migration Steps

### 1. Update Client Code

**Before:**
```javascript
fetch('/api/v1/admissions/drilldown/?bucket=status&stage=all')
  .then(res => res.json())
  .then(data => {
    data.rows.forEach(applicant => {
      // process applicant
    });
  });
```

**After:**
```javascript
fetch('/api/v1/admissions/drilldown/?bucket=status&stage=all')
  .then(res => res.json())
  .then(data => {
    data.results.forEach(applicant => {
      // process applicant
    });
  });
```

### 2. Check for Deprecation Header

The API now returns a response header:
```
X-Deprecated-Field: rows; use results instead; sunset 2026-06-01
```

Clients should log this header and plan migration accordingly.

### 3. Verify Compatibility

Both keys return **identical data structures**:
```json
{
  "total": 94,
  "limit": 50,
  "offset": 0,
  "academic_year": "2026-2027",
  "rows": [/* ... */],     // DEPRECATED
  "results": [/* ... */]   // USE THIS
}
```

### 4. PowerShell Example

**Before:**
```powershell
$drill.rows | Select-Object -First 10
```

**After:**
```powershell
$drill.results | Select-Object -First 10
```

## Rationale

- **Consistency**: `results` aligns with REST API conventions
- **Clarity**: `results` is more explicit than `rows`
- **Contract Hardening**: Clean separation of legacy vs. current API

## Contact

Questions? See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) or file an issue.
