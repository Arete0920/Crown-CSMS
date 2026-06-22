# CROWN Sandbox Demo Data Policy - 2026-06-22

**Status**: Sandbox data governance and labeling

## Demo data principles

1. **All data is clearly non-production**
   - Demo records include "Sandbox," "Test," or "Demo" labels
   - Timestamps show sandbox creation dates
   - No real student/family/staff personal information

2. **Data sources**
   - Seed fixtures (backend/fixtures/sandbox_*.json)
   - Test factories (backend/tests/factories.py)
   - Database seeding script (backend/scripts/seed_sandbox.sh)

3. **Data retention**
   - Sandbox resets nightly (scheduled task)
   - All demo data recreated from fixtures
   - No persistent state except configuration

## Sandbox dataset contents

### Schools (2 demo schools)
- Heritage Christian Academy (test school, ~200 students)
- Sunrise Prep Charter (test school, ~150 students)
- All data fabricated, no real addresses/contacts

### User accounts (40+ demo users)
- Admin staff (3 accounts)
- Teachers (8 accounts)
- Parents (15 accounts)
- Students (20 accounts)
- All passwords: demo/sandbox only, not production-capable

### Operational data
- Academic calendar: Spring 2025 (demo semester)
- Grades: Fabricated but realistic distribution
- Attendance: Randomly generated patterns
- Billing: Sample invoices, no real payment processing

### Financial data
- Sample tuition amounts: $15,000 - $20,000/year (fictional)
- No actual credit card data stored
- Payment gateway: Sandbox/test mode only
- Ledger entries: Educational examples only

### Third-party integrations
- Zoom: Sandbox API credentials (demo accounts)
- Google Classroom: Test dataset (no real classes)
- Mailchimp: Sandbox list (no real emails sent)
- SchoolZone: Integrated with real sandbox data

## Data labeling

All sandbox records include metadata:

```json
{
  "school_id": "test_school_001",
  "is_sandbox": true,
  "sandbox_created_date": "2026-06-22T07:01:14Z",
  "sandbox_renewal_date": "2026-06-23T00:00:00Z",
  "data_source": "fixture",
  "do_not_export": true
}
```

## Export restrictions

✓ Export function refuses to include records marked `do_not_export: true`  
✓ Report generation shows "SANDBOX DATA - FOR DEMO ONLY" watermark  
✓ Email exports blocked to external domains  
✓ API exports require explicit sandbox flag confirmation  

## Data privacy

- No real Social Security numbers (use 000-00-0000 format)
- No real phone numbers (use 555-XXXX pattern)
- No real email addresses (use sandbox@example.com pattern)
- No real household addresses (use 123 Main St patterns)
- All test user pictures are stock photos

## Known demo data limitations

- Limited scale (400 total records vs. production's 100K+)
- No multi-year historical data (current school year only)
- No integration webhooks (Zoom, Google don't send real events)
- Reports reflect demo data patterns, not production behavior

## Compliance

✓ FERPA-compliant: No real student data  
✓ GDPR-compliant: All data fictional  
✓ PCI-DSS: No real payment card data  
✓ SOC2-aligned: Audit trails on all administrative actions  

## Next validation

After merge: Confirm sandbox data reset mechanism works on deployed instance.
