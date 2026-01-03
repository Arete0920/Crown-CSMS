# cURL Examples for Director Actions API

# Base URL (adjust to your environment)
BASE_URL="http://localhost:8000/api"

# 1. POST accepted awards to ledger (requires authentication)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "school_id": "school-uuid-here",
    "year_id": "year-uuid-here",
    "ids": [
      "award-uuid-1",
      "award-uuid-2"
    ]
  }'

# 2. POST single award (minimal)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "ids": ["award-uuid"]
  }'

# 3. Test without authentication (should get 403)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "ids": ["award-uuid"]
  }'

# 4. Test with missing action field (should get 400)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "ids": ["award-uuid"]
  }'

# 5. Test with empty ids (should get 400)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "action": "POST_ACCEPTED_AWARDS",
    "ids": []
  }'

# 6. Test with unknown action (should get 400)
curl -X POST "${BASE_URL}/director/actions/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "action": "UNKNOWN_ACTION",
    "ids": ["award-uuid"]
  }'

# Notes:
# - Replace YOUR_AUTH_TOKEN_HERE with an actual Token from your database
# - Replace award-uuid-* with actual StudentAid UUID values
# - Replace school-uuid-here and year-uuid-here with actual UUID values
# - The endpoint returns:
#   {
#     "action": "POST_ACCEPTED_AWARDS",
#     "posted_count": number,
#     "total_requested": number,
#     "errors": null or array of error objects
#   }
