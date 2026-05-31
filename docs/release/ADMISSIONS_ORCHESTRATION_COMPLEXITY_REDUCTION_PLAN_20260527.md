# Admissions Orchestration Complexity Reduction Plan - 2026-05-27

## 1) Current working status
- `python manage.py check`: green
- `python manage.py makemigrations applications --check --dry-run`: green
- Targeted admissions/billing suite: green (`26` tests)
- Public surface policy gate: green

## 2) Complexity issue
- `backend/applications/views_admissions.py` contains large orchestration functions that combine validation, persistence, side effects, and response shaping.
- Current behavior is functional and gate-green, but change risk is elevated due to concentration of responsibilities.

## 3) Refactor boundaries
- Checklist resolution service
- Submit orchestration service
- Enrollment contract state service
- CRM adapter/fallback service

## 4) Non-negotiable rules
- No behavior change without tests.
- Preserve public endpoint policy matrix alignment.
- Preserve tenant resolution semantics.
- Preserve checklist access key behavior.
- Preserve targeted admissions/billing tests.

## 5) Recommended future slices
- Slice A: extract checklist resolution helper/service.
- Slice B: extract CRM optional adapter and add explicit fallback tests.
- Slice C: extract enrollment contract state mutation service.
- Slice D: add abuse-control tests for public checklist hub/upload.

This document is a planning artifact only. No broad runtime refactor is included in this release push slice.
