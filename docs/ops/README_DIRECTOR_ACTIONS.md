# Director Actions API - README

## Overview

The Director Actions API provides a unified REST endpoint (`POST /api/director/actions/`) for executing director/Head of School administrative actions in the Crown system. The initial implementation supports posting accepted financial aid awards to the ledger.

## Quick Links

- **API Documentation:** [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md)
- **Implementation Summary:** [IMPLEMENTATION_SUMMARY.md](../status/IMPLEMENTATION_SUMMARY.md)
- **Integration Guide:** [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Testing Checklist:** [CHECKLIST.md](CHECKLIST.md)
- **Code Examples:** [curl_examples_director_actions.sh](curl_examples_director_actions.sh)

## What's Included

### 1. Backend Implementation
- **View Function:** `director_actions()` in `backend/crown_api/director_views.py`
- **URL Routing:** `POST /api/director/actions/` in `backend/crown_api/api_urls.py`
- **Features:**
  - Director authentication requirement
  - POST_ACCEPTED_AWARDS action implementation
  - School validation
  - Atomic transaction handling
  - Comprehensive error tracking

### 2. Documentation
- Comprehensive API reference with request/response examples
- Implementation details and architecture
- Integration guide with code examples
- Testing checklist and deployment guide

### 3. Testing & Examples
- Automated test script (`test_director_actions.py`)
- cURL examples for API testing
- Python, JavaScript, and Vue code samples

## Quick Start

### 1. Verify Implementation

```bash
# Check endpoint is registered
grep -r "director/actions" backend/crown_api/
```

### 2. Run Tests

```bash
# Run automated tests
python test_director_actions.py
```

### 3. Test with cURL

```bash
# Get your auth token first
TOKEN="your_token_here"

# Post awards to ledger
curl -X POST "http://localhost:8000/api/director/actions/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "ids": ["award-uuid-1", "award-uuid-2"]
  }'
```

## API Usage

### Request Format
```json
{
  "action": "POST_ACCEPTED_AWARDS",
  "school_id": "uuid (optional)",
  "year_id": "uuid (optional)",
  "ids": ["award-uuid-1", "award-uuid-2"]
}
```

### Response Format
```json
{
  "action": "POST_ACCEPTED_AWARDS",
  "posted_count": 2,
  "total_requested": 3,
  "errors": [
    {
      "award_id": "uuid",
      "error": "Award does not belong to specified school"
    }
  ]
}
```

### Status Codes
- **200** - OK (check posted_count and errors)
- **400** - Bad Request (missing fields or unknown action)
- **403** - Forbidden (not authorized)
- **500** - Server Error

## Implementation Details

### Files Modified
1. `backend/crown_api/director_views.py` - Added view function
2. `backend/crown_api/api_urls.py` - Added URL pattern

### Files Created
1. `docs/DIRECTOR_ACTIONS_API.md` - API documentation
2. `IMPLEMENTATION_SUMMARY.md` - Technical summary
3. `INTEGRATION_GUIDE.md` - Integration instructions
4. `CHECKLIST.md` - Verification checklist
5. `test_director_actions.py` - Test script
6. `curl_examples_director_actions.sh` - cURL examples

## Key Features

✅ **Secure** - Director authentication required
✅ **Atomic** - All-or-nothing transaction handling
✅ **Robust** - Per-award error tracking
✅ **Extensible** - Easy to add new actions
✅ **Tested** - Comprehensive test suite
✅ **Documented** - Multiple guides and examples

## Architecture

```
POST /api/director/actions/
  ↓
crown_director_allowed() [Authentication Check]
  ↓
Validate Required Fields (action, ids)
  ↓
Dispatch to Action Handler
  ├─ POST_ACCEPTED_AWARDS
  │   ├─ Fetch Award by ID
  │   ├─ Verify School Ownership
  │   ├─ Post to Ledger
  │   └─ Track Result
  └─ [Future Actions]
  ↓
Return Summary Response
  ├─ posted_count
  ├─ total_requested
  └─ errors (if any)
```

## Supported Actions

### POST_ACCEPTED_AWARDS
Post accepted financial aid awards to the ledger, making them effective for students' accounts.

**Parameters:**
- `ids` (required) - Array of award UUIDs
- `school_id` (optional) - Validate school ownership
- `year_id` (optional) - Academic year context

**Returns:**
- `posted_count` - Number successfully posted
- `total_requested` - Total requested
- `errors` - Any per-award errors

## Future Actions

The architecture supports adding more actions:
- `POST_PENDING_AWARDS` - Post provisional awards
- `REJECT_AWARDS` - Reject and update ledger
- `CANCEL_AWARDS` - Cancel posted awards
- `POST_CORRECTIONS` - Award adjustments
- `VALIDATE_AWARDS` - Pre-posting validation

## Integration Steps

1. **Verify Implementation** - Run tests to ensure everything works
2. **Create Frontend Component** - Add UI for posting awards
3. **Add to Dashboard** - Integrate with director dashboard
4. **Test End-to-End** - Test full workflow
5. **Deploy** - Follow deployment checklist
6. **Monitor** - Watch logs for issues

## Testing

### Automated Tests
```bash
python test_director_actions.py
```

### Manual Testing
See [curl_examples_director_actions.sh](curl_examples_director_actions.sh) for cURL examples.

### Test Scenarios
- ✅ Unauthorized access (403)
- ✅ Missing authentication
- ✅ Missing required fields (400)
- ✅ Unknown actions (400)
- ✅ Non-existent awards
- ✅ School validation
- ✅ Successful posting
- ✅ Transaction atomicity

## Troubleshooting

### 403 Unauthorized
**Problem:** User doesn't have director privileges
**Solution:** Verify user's school role or superuser status

### 400 Bad Request
**Problem:** Missing `action` or `ids` field
**Solution:** Ensure request body includes both fields

### Award not found
**Problem:** Award UUID doesn't exist
**Solution:** Verify award UUID is correct and exists in database

### Award doesn't belong to school
**Problem:** Award's school doesn't match provided school_id
**Solution:** Remove school_id validation or use correct school

## Performance

- Efficient for small batches (10-20 awards)
- For large batches (100+), process in smaller chunks
- Atomic transactions ensure consistency
- Database indexes on StudentAid.id recommended

## Security

- ✅ Director authentication required
- ✅ School ownership validation
- ✅ SQL injection prevention (Django ORM)
- ✅ Atomic transactions prevent partial updates
- ✅ Per-award error isolation

## Related Endpoints

- `GET /api/director/dashboard/` - Director dashboard
- `GET /api/director/aid/summary/` - Financial aid summary
- `GET /api/director/finance/summary/` - Finance summary
- `GET /api/director/priority/` - Priority worklist

## Questions?

Refer to the documentation files:
- [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md) - Complete API reference
- [IMPLEMENTATION_SUMMARY.md](../status/IMPLEMENTATION_SUMMARY.md) - Technical details
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - How to integrate
- [test_director_actions.py](test_director_actions.py) - Working examples

## Status

✅ **Implementation Complete**
- ✅ Backend endpoint created
- ✅ URL routing configured
- ✅ Authentication integrated
- ✅ Error handling implemented
- ✅ Tests written
- ✅ Documentation complete
- ⏳ **Frontend integration** (next step)
- ⏳ **Dashboard UI** (next step)
- ⏳ **Production deployment** (next step)

## Support

For issues or questions:
1. Check [CHECKLIST.md](CHECKLIST.md) for verification
2. Review [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for integration help
3. Run [test_director_actions.py](test_director_actions.py) to test functionality
4. Consult [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md) for API details
