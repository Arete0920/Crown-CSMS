# CROWN Best-In-Industry Sandbox Runbook

## Operating position

CROWN uses a staged sandbox model:

1. **Heritage Christian Academy** is the flagship canonical demo.
2. Four secondary school scenarios can be used only after Heritage is complete/proven.
3. Daycare and camp remain available as guided tracks but should not be sold as complete until each track has the same seed/reset/proof gate.
4. External self-guided access requires invite links unless explicitly opened for internal review.

## Buyer-facing demo standard

The evaluator should never have to ask:

- Which login should I use?
- Which password should I enter?
- Which school should I pick?
- What should I click first?
- Is this real student data?

The sandbox must answer those automatically.

## Required proof before external access

Run:

```powershell
cd backend
python manage.py sandbox_seed_flagship --reset
python manage.py sandbox_proof_gate --strict
```

Required PASS conditions:

- Heritage school exists.
- 700 students exist.
- 286 families exist.
- 6 persona users exist.
- 6 persona roles exist.
- 700 enrollments exist.
- 700 student tuition records exist.
- Parent finance obligations and invoices exist.
- One-click session works for Head, Admissions, Finance, Teacher, Parent, Student.
- Privacy-safe feedback/event models migrate correctly.

## Invite creation

```powershell
cd backend
python manage.py sandbox_create_invite `
  --organization "Example Christian Academy" `
  --track school `
  --roles school_admin,admissions_director,finance_director,teacher,parent,student `
  --seed-packs heritage-core `
  --days 14 `
  --base-url https://app.example.org
```

## Prospect wording

Use this language:

> CROWN does not drop school leaders into an empty trial. We provide a guided proof environment using fictional Heritage Christian Academy data so each evaluator can inspect the platform from the role that matters to them.

## Hard rule

Do not send a broad self-guided sandbox to prospects until the proof gate passes with zero FAIL rows.
