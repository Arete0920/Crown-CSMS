# Integration Guide: Director Actions API

## Quick Start

### 1. Verify Implementation
The endpoint is now available at:
```
POST /api/director/actions/
```

### 2. Basic Usage

```python
import requests

url = "http://localhost:8000/api/director/actions/"
headers = {
    "Authorization": f"Token {your_auth_token}",
    "Content-Type": "application/json"
}

payload = {
    "action": "POST_ACCEPTED_AWARDS",
    "ids": ["award-uuid-1", "award-uuid-2"]
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

if response.status_code == 200:
    print(f"Posted {result['posted_count']} awards")
    if result.get('errors'):
        print(f"Errors: {result['errors']}")
```

### 3. Frontend Integration

#### React Example
```javascript
async function postAwards(awardIds, authToken) {
  const response = await fetch('/api/director/actions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`
    },
    body: JSON.stringify({
      action: 'POST_ACCEPTED_AWARDS',
      ids: awardIds
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Usage
postAwards(['uuid1', 'uuid2'], token)
  .then(result => {
    console.log(`Posted ${result.posted_count} awards`);
    if (result.errors) {
      console.error('Some awards failed:', result.errors);
    }
  })
  .catch(error => console.error('Request failed:', error));
```

#### Vue Example
```vue
<template>
  <div class="director-actions">
    <button @click="postSelectedAwards" :disabled="!selectedAwards.length">
      Post Awards ({{ selectedAwards.length }})
    </button>
    <div v-if="result" class="result">
      <p>Posted: {{ result.posted_count }} / {{ result.total_requested }}</p>
      <div v-if="result.errors" class="errors">
        <p v-for="error in result.errors" :key="error.award_id">
          {{ error.award_id }}: {{ error.error }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedAwards: [],
      result: null
    };
  },
  methods: {
    async postSelectedAwards() {
      const response = await fetch('/api/director/actions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.$auth.token}`
        },
        body: JSON.stringify({
          action: 'POST_ACCEPTED_AWARDS',
          ids: this.selectedAwards
        })
      });
      this.result = await response.json();
    }
  }
};
</script>
```

## Integration Checklist

- [ ] Verify Django server is running
- [ ] Test endpoint with cURL examples
- [ ] Run test script: `python test_director_actions.py`
- [ ] Add endpoint to API documentation
- [ ] Create frontend component for posting awards
- [ ] Add to director dashboard UI
- [ ] Test with multiple awards
- [ ] Test error scenarios
- [ ] Monitor logs for issues
- [ ] Update permissions if needed

## Common Issues and Solutions

### Issue: 403 Unauthorized
**Cause:** User doesn't have director privileges
**Solution:** Verify user's school role is "DIRECTOR" or has superuser status

### Issue: 400 Missing required field
**Cause:** Missing `action` or `ids` in request
**Solution:** Ensure request body includes:
- `action`: "POST_ACCEPTED_AWARDS"
- `ids`: array of award UUIDs (at least one)

### Issue: Award not found
**Response:** Error in response array
**Solution:** Verify award UUID exists and is spelled correctly

### Issue: Award doesn't belong to school
**Response:** Error in response array
**Solution:** Verify `school_id` parameter matches the award's student's school

### Issue: Database lock/transaction timeout
**Cause:** Many awards or slow ledger posting
**Solution:**
- Post awards in batches (10-20 at a time)
- Check `post_award_to_ledger()` performance
- Verify database connection pool size

## Monitoring and Logging

### Enable Debug Logging

In `settings.py`, add:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'crown_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Monitor Request/Response
Add logging to `director_views.py`:
```python
import logging
logger = logging.getLogger(__name__)

def director_actions(request):
    logger.debug(f"Action request: {request.data}")
    # ... endpoint code ...
    logger.debug(f"Response: posted_count={posted_count}, errors={errors}")
```

## Performance Considerations

### Batch Processing
For large numbers of awards, process in batches:

```python
def post_awards_batch(award_ids, batch_size=20):
    results = []
    for i in range(0, len(award_ids), batch_size):
        batch = award_ids[i:i + batch_size]
        response = requests.post(
            '/api/director/actions/',
            json={'action': 'POST_ACCEPTED_AWARDS', 'ids': batch},
            headers=auth_headers
        )
        results.append(response.json())
    return results
```

### Database Optimization
- Ensure StudentAid table has index on `id`
- Verify `post_award_to_ledger()` is optimized
- Check database connection pool configuration

## Security Considerations

### Authentication
- All requests require director authentication
- Token-based authentication via Django REST Framework
- Verify tokens are not exposed in logs

### Authorization
- `crown_director_allowed()` check prevents unauthorized access
- School validation prevents cross-school access
- Consider audit logging for compliance

### Data Validation
- Award IDs are validated (UUID format)
- School ownership is verified
- SQL injection prevention via ORM

## Related Endpoints

- `GET /api/director/dashboard/` - Get director dashboard
- `GET /api/director/aid/summary/` - Get financial aid summary
- `GET /api/director/finance/summary/` - Get finance summary
- `GET /api/director/priority/` - Get priority worklist

## Support and Troubleshooting

### Test Endpoint
```bash
# Check if endpoint is accessible
curl -X OPTIONS http://localhost:8000/api/director/actions/

# Check with authentication
curl -X POST http://localhost:8000/api/director/actions/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "POST_ACCEPTED_AWARDS", "ids": []}'
```

### View Database State
```python
from crown_api.models import StudentAid

# Check award status
award = StudentAid.objects.get(id='...')
print(f"Status: {award.status}")
print(f"Student: {award.student.school_id}")
```

### Check Logs
```bash
# View Django logs (if configured)
tail -f logs/django.log

# Check for errors
grep -i "error\|exception" logs/django.log | tail -20
```

## Next Steps

1. **Frontend Development:** Create UI component for posting awards
2. **Dashboard Integration:** Add action button to director dashboard
3. **Bulk Operations:** Support more action types
4. **Notifications:** Add email/SMS notifications on completion
5. **Audit Trail:** Log all director actions for compliance
6. **Reporting:** Create reports on posted awards

## Questions?

Refer to:
- [docs/DIRECTOR_ACTIONS_API.md](docs/DIRECTOR_ACTIONS_API.md) - API documentation
- [test_director_actions.py](test_director_actions.py) - Working examples
- [curl_examples_director_actions.sh](curl_examples_director_actions.sh) - CLI examples
