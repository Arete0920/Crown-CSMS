# DIRECTOR ROUTER IMPLEMENTATION

**Date:** 2026-01-04  
**Pattern:** Unified Dashboard with Persona-Based Filtering

---

## Answer to "Which admissions URL is live?"

### Before (WRONG):
- ✅ `/director/` - Unified dashboard (correct)
- ❌ `/admissions/` - Separate admissions dashboard (incorrect, leftover from mistake)
- ❌ `/api/director/priority/` - Had admissions data but wrong route structure

### After (CORRECT):
- ✅ `/director/` - **ONLY** director URL (unified, persona-agnostic)
- ✅ Persona routing happens **INSIDE** the same page via JavaScript filtering
- ✅ All directors use the same APIs: `/api/director/*`

**There is NO `/director/aid/` or `/director/admissions/`** - intentionally.

---

## Architecture: Unified Dashboard Pattern

### Key Principle
**One page, one set of APIs, persona-based highlighting.**

```
┌─────────────────────────────────────────────┐
│  /director/ (SINGLE PAGE)                   │
├─────────────────────────────────────────────┤
│                                             │
│  Router detects user's role:               │
│  ├─ Aid Director → Highlight Aid items     │
│  ├─ Admissions Director → Highlight Adm    │
│  ├─ Finance Director → Highlight Finance   │
│  ├─ Registrar → Highlight Registrar        │
│  └─ Head of School → Show all equally      │
│                                             │
│  Same APIs for all:                        │
│  ├─ /api/director/dashboard/               │
│  ├─ /api/director/priority/                │
│  ├─ /api/director/timeline/                │
│  └─ /api/director/actions/                 │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Director Router Components

### 1. `director_router.py` (NEW)

**Location:** `backend/crown_api/director_router.py`

**Functions:**

#### `get_director_persona(user)`
Determines user's primary director role.

**Returns:** `'aid' | 'admissions' | 'finance' | 'registrar' | 'head' | None`

**Priority order (if user has multiple roles):**
1. Head of School (highest - sees everything)
2. Aid Director
3. Admissions Director
4. Finance Director
5. Registrar

#### `get_director_filter_config(persona)`
Returns UI filter configuration for a persona.

**Config includes:**
- `highlight_types`: Which worklist item types to emphasize
- `primary_sections`: Which sections to show prominently
- `secondary_sections`: Which related sections to show
- `title`: Page title for this persona

**Example for Admissions Director:**
```python
{
    'persona': 'admissions',
    'highlight_types': [
        'ADMISSIONS_APPLICATION_NEEDS_INFO',
        'ADMISSIONS_APPLICATION_UNDER_REVIEW',
    ],
    'primary_sections': ['admissions'],
    'secondary_sections': ['registrar'],
    'title': 'Admissions Director Dashboard',
}
```

#### `route_director_view(request)`
Main routing function called by page view.

**Returns:**
```python
{
    'persona': 'admissions',
    'config': {...},
    'route': '/director/',  # Always the same
    'api_endpoints': {
        'dashboard': '/api/director/dashboard/',
        'priority': '/api/director/priority/',
        'timeline': '/api/director/timeline/',
        'actions': '/api/director/actions/',
    }
}
```

---

### 2. `views.py` (UPDATED)

**Location:** `backend/crown_api/views.py`

**Changes:**
- Added import: `from crown_api.director_router import route_director_view`
- Updated `director_dashboard_page(request)` to use router
- Passes persona context to template

**Context passed to template:**
```python
{
    'persona': 'admissions',
    'page_title': 'Admissions Director Dashboard',
    'filter_config': {...},
    'api_endpoints': {...},
}
```

---

### 3. Removed Files (Cleanup)

**Deleted:**
- `admissions/urls.py` - Leftover from incorrect separate dashboard approach
- `admissions/views.py` - Leftover from incorrect separate dashboard approach

**Removed from `crown_api/urls.py`:**
- `path('admissions/', include('admissions.urls'))` - No longer needed

---

## How It Works

### Server-Side (Django)

1. User navigates to `/director/`
2. `director_dashboard_page(request)` runs
3. Router calls `get_director_persona(request.user)`
   - Queries `UserRole` table
   - Returns `'admissions'` for Admissions Director
4. Router calls `get_director_filter_config('admissions')`
   - Returns config for highlighting admissions items
5. Context passed to template:
   ```python
   {
       'persona': 'admissions',
       'page_title': 'Admissions Director Dashboard',
       'filter_config': {
           'highlight_types': ['ADMISSIONS_APPLICATION_*'],
           'primary_sections': ['admissions'],
       },
       'api_endpoints': {...}
   }
   ```

### Client-Side (JavaScript - Future Enhancement)

Template receives context and can:
1. Set page title: `<h1>{{ page_title }}</h1>`
2. Pass filter config to JavaScript:
   ```javascript
   const filterConfig = {{ filter_config|json_script:"filter-config" }};
   
   // When rendering worklist:
   items.forEach(item => {
       if (filterConfig.highlight_types.includes(item.type)) {
           // Add visual emphasis (bold, colored, larger)
       }
   });
   ```
3. Show/hide sections:
   ```javascript
   if (filterConfig.primary_sections.includes('admissions')) {
       document.querySelector('.admissions-section').classList.add('primary');
   }
   ```

---

## Benefits of This Pattern

### 1. **Single Source of Truth**
- One page to maintain
- One set of APIs
- One JavaScript codebase

### 2. **Flexible**
- Add new director types without creating new pages
- Head of School sees everything
- Multi-role users work seamlessly

### 3. **Consistent UX**
- All directors learn one interface
- No confusion about "which page do I go to?"
- Shared navigation patterns

### 4. **Maintainable**
- Bug fixes apply to all directors
- New features available to all instantly
- No code duplication

---

## Adding a New Director Type

To add a new director type (e.g., HR Director):

### Step 1: Add Role to Router

**File:** `crown_api/director_router.py`

```python
# In get_director_persona():
role_mapping = {
    'ROLE_HEAD_OF_SCHOOL': 'head',
    'ROLE_AID_DIRECTOR': 'aid',
    'ROLE_ADMISSIONS_DIRECTOR': 'admissions',
    'ROLE_HR_DIRECTOR': 'hr',  # ← ADD THIS
    'ROLE_FINANCE_DIRECTOR': 'finance',
    'ROLE_REGISTRAR': 'registrar',
}

# In get_director_filter_config():
elif persona == 'hr':
    return {
        'persona': 'hr',
        'highlight_types': [
            'HR_EMPLOYEE_NEEDS_ONBOARDING',
            'HR_CERTIFICATION_EXPIRING',
        ],
        'primary_sections': ['hr'],
        'secondary_sections': ['finance'],  # HR cares about payroll
        'title': 'HR Director Dashboard',
    }
```

### Step 2: Add HR Data to director_views.py

Follow the same clone pattern:
1. Add HR models import
2. Add HR priority queries
3. Add HR scoring logic
4. Merge HR items into worklist
5. Add HR section to API response

### Step 3: Test

```python
# Check router
from crown_api.director_router import get_director_persona
persona = get_director_persona(user)
assert persona == 'hr'

# Check API
response = requests.get('/api/director/priority/')
assert 'hr' in response.json()
```

**No URL changes needed.** `/director/` already works for all personas.

---

## Testing the Router

### Test Persona Detection

```python
from django.test import RequestFactory
from crown_api.director_router import get_director_persona, route_director_view
from core.models import UserAccount, UserRole

# Create test user with Admissions Director role
user = UserAccount.objects.get(email='admin@example.com')
UserRole.objects.create(user_account=user, role_code='ROLE_ADMISSIONS_DIRECTOR')

# Test routing
factory = RequestFactory()
request = factory.get('/director/')
request.user = user

persona = get_director_persona(user)
assert persona == 'admissions'

routing = route_director_view(request)
assert routing['persona'] == 'admissions'
assert routing['config']['title'] == 'Admissions Director Dashboard'
assert 'ADMISSIONS_APPLICATION_NEEDS_INFO' in routing['config']['highlight_types']
```

### Test Page Load

```bash
# Start server
python manage.py runserver

# Visit as Admissions Director
curl http://127.0.0.1:8000/director/

# Should see: "Admissions Director Dashboard" in title
```

---

## Migration Path

### Before (Wrong)
```
Aid Director → /director/aid/ ❌ (doesn't exist)
Admissions Director → /admissions/ ❌ (wrong pattern)
Finance Director → /director/finance/ ❌ (doesn't exist)
```

### After (Correct)
```
Aid Director → /director/ ✅ (shows aid-focused view)
Admissions Director → /director/ ✅ (shows admissions-focused view)
Finance Director → /director/ ✅ (shows finance-focused view)
Head of School → /director/ ✅ (shows unified view)
```

**All personas use `/director/`** - the router handles the rest.

---

## Why Not Separate URLs?

### Option A: Separate URLs (NOT CHOSEN)
```
/director/aid/
/director/admissions/
/director/finance/
```

**Problems:**
- ❌ Code duplication (3+ templates, 3+ API sets)
- ❌ Multi-role users confused ("which page?")
- ❌ Head of School can't see everything in one place
- ❌ Maintenance nightmare (bug fixes × number of directors)

### Option B: Unified URL (CHOSEN)
```
/director/ (with routing)
```

**Advantages:**
- ✅ One page, one codebase
- ✅ Multi-role users seamless
- ✅ Head of School sees everything
- ✅ Easy to add new director types
- ✅ Consistent UX

---

## Files Modified

```
backend/
├── crown_api/
│   ├── director_router.py          ← NEW (routing logic)
│   ├── views.py                    ← UPDATED (uses router)
│   └── urls.py                     ← CLEANED (removed /admissions/)
└── admissions/
    ├── urls.py                     ← DELETED (incorrect pattern)
    └── views.py                    ← DELETED (incorrect pattern)
```

---

## Git Commands

```bash
# Remove incorrect files
git rm admissions/urls.py admissions/views.py

# Add new router
git add crown_api/director_router.py

# Update views
git add crown_api/views.py crown_api/urls.py

# Commit
git commit -m "Implement Director Router (unified dashboard pattern)

- Create director_router.py with persona detection
- Update views.py to use router for context
- Remove incorrect /admissions/ route
- All directors now use /director/ with persona-based filtering"
```

---

**Maintained by:** Crown 2026 Team  
**Pattern:** Unified Dashboard with Persona-Based Filtering  
**Live URL:** `/director/` (single, persona-agnostic)
