# Heritage Realism Pack

## Purpose

Single canonical seed command that populates Heritage demo school with realistic linked data across all roles, making the demo feel like a live school rather than empty CRUD screens.

## How to Run

From `backend/` directory:

```bash
python manage.py seed_heritage_realism_pack
```

### Options

- `--no-comms` - Skip seeding communications threads (faster runs)
- `--no-finance-scripts` - Skip extra finance realism scripts (faster runs)

For full realism (recommended for investor-preview sandbox sessions), run without options.

## What It Seeds

The realism pack creates a deterministic, internally consistent data set across all major systems:

### People & Roles
- **1 School**: Crown Demo Christian Academy (Heritage)
- **Admin users**: Principal, Admissions Director, Finance Director
- **Teachers**: 6-10 (elementary + secondary mix)
- **Parents**: 20-40 households
- **Students**: 80-150 (enough for dashboards without feeling fake)

### Finance & Financial Aid
- Tuition obligations for every student
- 30-50 payments posted (mix: on-time, late, partial)
- 15-25 aid awards (full/partial scholarships)
- Edge cases:
  - 2 unpaid families
  - 2 overpaid/credit families
  - 2 mid-year starts (prorated tuition)

### Academics & Scheduling
- **Sections**: 12+ (mix of full and small classes)
- **Gradebook**: 6+ active assignments with scores
- **Attendance**: 3+ days populated with absences/tardies

### Student Life
- **Discipline**: 6-12 incidents across different severities
- **Activities**: 6-10 clubs
- **Athletics**: 2-3 sports with scheduled events

### Communications
- **Message threads**: 20-40 across:
  - teacher ↔ parent
  - finance ↔ parent
  - admin ↔ staff
- **Tension threads** (demo realism):
  - Missing assignment follow-ups
  - Payment plan questions
  - Attendance concerns
  - Discipline follow-ups

## Integration

This command is automatically called by:
- `tools/dev_scripts/lockdown_run.ps1` (used by `demo_one_click.ps1`)

For manual dev/test workflows, run directly from backend.

## Gold Click-Path Records

For Feb 16 demo, these are known-good navigation targets:

1. **Student**: Check `seed_admissions_demo` output for primary student names
2. **Parent**: Find households with multiple students and recent messages
3. **Payment**: Look for families with "partial paid" status
4. **Gradebook section**: Find sections with 15-25 students and 6+ assignments
5. **Message thread**: Search for threads tagged "urgent" or "payment plan"

_(Exact record IDs are deterministic; see individual seed command outputs for keys.)_

## Idempotency

Safe to rerun. The underlying seed commands either:
- Wipe demo tenant data cleanly, or
- Upsert deterministically using fixed UUIDs/names

No manual cleanup required between runs.

## Execution Order

The pack runs seeds in dependency order to prevent orphaned data:

1. `seed_demo_school` - Core school + academic year
2. `seed_admissions_demo` - Applications baseline
3. `seed_households.py` - Real households + guardians
4. `seed_scheduling.py` - Sections (must exist before gradebook)
5. `seed_academics_demo` - Academic structure
6. `seed_curricula_demo` - Curriculum data
7. `seed_gradebook_demo` - Assignments + scores
8. `seed_category_weights` - Grade calculation metadata
9. `seed_billing_demo` - Invoices + obligations
10. `seed_finance.py` - Payment realism (credits, edge cases)
11. `seed_comms.py` - Message threads (demo differentiator)
12. `reset_demo_passwords` - Ensure predictable logins

## Troubleshooting

**Command not found**: Ensure you're in `backend/` directory and Django is loaded.

**Script missing errors**: Check that `backend/scripts/` contains all referenced `.py` files.

**Timeout during comms seed**: Use `--no-comms` flag for faster runs during development.

**Data looks incomplete**: Run without any flags; the optional skips reduce realism.
