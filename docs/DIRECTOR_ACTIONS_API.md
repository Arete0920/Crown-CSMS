# Director Actions API Documentation

## Overview

The Director Actions API (`POST /api/director/actions/`) provides a unified endpoint for executing director/Head of School actions in the Crown system. The endpoint supports various administrative actions, with initial support for posting accepted awards to the ledger.

## Endpoint Details

**URL:** `POST /api/director/actions/`

**Authentication:** Required. Director access required (based on `crown_director_allowed()` check).

**Content-Type:** `application/json`

## Supported Actions

### 1. POST_ACCEPTED_AWARDS

Post accepted financial aid awards to the legacy aid ledger. When a unique, same-school family-to-household link exists, also project the award into Student Accounts as a **non-cash Credit**. Without a valid link, retain the legacy posting and record an auditable deferred-credit exception. This action never creates a cash Payment or sends money externally.

#### Request Payload

```json
{
  "action": "POST_ACCEPTED_AWARDS",
  "school_id": "uuid (required)",
  "year_id": "uuid (optional)",
  "ids": ["award-primary-key-1", "award-primary-key-2", ...]
}
```

**Required Fields:**
- `action`: Must be `"POST_ACCEPTED_AWARDS"`
- `ids`: Nonempty list of `AidAward` primary-key identifiers to post
- `school_id`: Explicit active school UUID; the authenticated director must be authorized for this school, and supplied tenant headers must agree

**Optional Fields:**
- `year_id`: When supplied, each award must belong to that academic year

#### Response

**Success (200):**
```json
{
  "action": "POST_ACCEPTED_AWARDS",
  "posted_count": 2,
  "total_requested": 3,
  "errors": [
    {
      "award_id": "uuid-that-failed",
      "error": "Award does not belong to specified school"
    }
  ]
}
```

**Missing Required Fields (400):**
```json
{
  "error": "Missing required field: ids"
}
```

**Unknown Action (400):**
```json
{
  "error": "Unknown action: INVALID_ACTION"
}
```

**Unauthorized (403):**
```json
{
  "error": "Unauthorized. Director access required."
}
```

**Server Error (500):**
```json
{
  "error": "Detailed error message"
}
```

## Implementation Details

### Location
- **View:** `crown_api/director_views.py` - `director_actions()` function
- **URLs:** `crown_api/api_urls.py` - `director/actions/` path

### Flow

1. **Authentication Check:** Verifies user has director privileges
2. **Validation:** Checks for required fields (`action`, `ids`)
3. **Action Dispatch:** Routes to appropriate handler based on action
4. **Processing:** For `POST_ACCEPTED_AWARDS`:
   - Iterates through requested award IDs
   - Verifies award exists and belongs to correct school
   - Posts the legacy award once; projects an idempotent non-cash Student Accounts Credit through the canonical verified family-to-household bridge, or records a deferred-credit audit
   - Rolls back each award's writes if its projection raises an error, while processing other requested awards independently
   - Tracks newly posted legacy awards and per-award errors; a valid retry can reconcile a previously deferred credit
5. **Response:** Returns summary with posted count and any errors

### Error Handling

- **Award not found:** Logged in errors array, continues processing
- **School mismatch:** Award skipped with error message
- **Ledger posting error:** Caught and returned in errors array
- **Transaction:** The batch is transaction-scoped with a nested atomic savepoint per award. An unexpected projection error rolls back that award's legacy posting and audit, and is returned in the errors array. A response with status 200 can still contain per-award errors; check `errors` and `posted_count` together.

## Usage Examples

### Python (requests library)

```python
import requests
import json

url = "http://localhost:8000/api/director/actions/"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

payload = {
    "action": "POST_ACCEPTED_AWARDS",
    "school_id": "school-uuid",
    "year_id": "year-uuid",
    "ids": ["award-uuid-1", "award-uuid-2"]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### JavaScript (fetch)

```javascript
const url = "http://localhost:8000/api/director/actions/";
const token = "YOUR_AUTH_TOKEN";

const payload = {
  action: "POST_ACCEPTED_AWARDS",
  school_id: "school-uuid",
  year_id: "year-uuid",
  ids: ["award-uuid-1", "award-uuid-2"]
};

const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify(payload)
});

const data = await response.json();
console.log(data);
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "school_id": "school-uuid",
    "year_id": "year-uuid",
    "ids": ["award-uuid-1", "award-uuid-2"]
  }'
```

## Future Enhancements

The endpoint architecture supports adding more actions as needed:

1. **POST_PENDING_AWARDS** - Post provisional awards
2. **REJECT_AWARDS** - Reject awards and update ledger
3. **CANCEL_AWARDS** - Cancel posted awards
4. **POST_CORRECTIONS** - Post award corrections/adjustments
5. **BULK_ACTIONS** - Multi-action operations

To add new actions:

1. Add action handler function in `director_views.py`
2. Add case to the action dispatch in `director_actions()`
3. Document the action in this file
4. Add tests

## Testing

Run the test script to verify the endpoint:

```bash
python test_director_actions.py
```

Test scenarios covered:
- Missing authentication (403)
- Missing required fields (400)
- Unknown action (400)
- Non-existent award (error in response)
- School mismatch validation
- Successful posting
- Transaction rollback on errors

## Related Functions

- `crown_director_allowed(request)` - Authorization check
- `post_award_to_ledger(award)` - Posts award to financial ledger
- `StudentAid` model - Award data structure
- `LedgerEntry` model - Ledger records

## Notes

- All operations are atomic (all-or-nothing per request)
- Errors don't stop processing of remaining awards
- School validation is optional but recommended
- The endpoint returns success (200) even with individual award errors
- Check `errors` array in response for details on any failed awards
