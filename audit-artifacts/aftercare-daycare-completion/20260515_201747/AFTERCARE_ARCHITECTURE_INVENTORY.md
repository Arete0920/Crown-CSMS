# Aftercare / Daycare Architecture Inventory

Generated: 2026-05-15T20:19:21.6484290-04:00
Branch: feature/aftercare-daycare-completion-20260515_201747
Base HEAD: efb4f846bc5a743c88be6e4914aeb89e1f4d88a3

## Decision
Use the existing aftercare module as the Daycare / Aftercare / Extended Care module.

Do not create a duplicate backend app named daycare.

## Required existing architecture surfaces

| Surface | Expected Path | Status |
|---|---|---|
| Backend app | backend/aftercare | TBD |
| Models | backend/aftercare/models.py | TBD |
| API | backend/aftercare/api.py | TBD |
| URLs | backend/aftercare/urls.py | TBD |
| Services | backend/aftercare/services.py | TBD |
| Wizard API | backend/aftercare/wizard_api.py | TBD |
| Migrations | backend/aftercare/migrations | TBD |
| Frontend API | frontend/dashboards/src/api/aftercareApi.js | TBD |
| Roster page | frontend/dashboards/src/pages/AftercareRosterPage.jsx | TBD |
| Setup wizard | frontend/dashboards/src/pages/wizards/AftercareSetupWizard.jsx | TBD |
| Board card | frontend/dashboards/src/components/board/AftercareBoardCard.jsx | TBD |


## File Existence Check

- [PASS] backend\aftercare
- [PASS] backend\aftercare\models.py
- [PASS] backend\aftercare\api.py
- [PASS] backend\aftercare\urls.py
- [PASS] backend\aftercare\services.py
- [PASS] backend\aftercare\wizard_api.py
- [PASS] backend\aftercare\migrations
- [PASS] frontend\dashboards\src\api\aftercareApi.js
- [PASS] frontend\dashboards\src\pages\AftercareRosterPage.jsx
- [PASS] frontend\dashboards\src\pages\wizards\AftercareSetupWizard.jsx
- [PASS] frontend\dashboards\src\components\board\AftercareBoardCard.jsx
