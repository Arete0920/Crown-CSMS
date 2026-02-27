from django.shortcuts import render
from crown_api.director_router import get_director_persona, get_director_filter_config
import logging

logger = logging.getLogger(__name__)

def director_dashboard_page(request, persona=None):
    """
    Serve the Director Dashboard HTML page with persona-based context.
    
    Supports both:
    - /director/  Auto-detect persona from user's role
    - /director/admissions/  Explicit persona from URL
    """
    # Use URL persona if provided, otherwise detect from user
    if not persona:
        persona = get_director_persona(request.user)
    
    filter_config = get_director_filter_config(persona)
    
    context = {
        'persona': persona,
        'page_title': filter_config['title'],
        'filter_config': filter_config,
        'api_endpoints': {
            'dashboard': '/api/director/dashboard/',
            'priority': '/api/director/priority/',
            'timeline': '/api/director/timeline/',
            'actions': '/api/director/actions/',
        }
    }
    
    return render(request, "director_dashboard.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

# Canonical director landing routes (LOCKED)
DIRECTOR_ROUTE_BY_PERSONA = {
    # Directors
    "financial_aid_director": "/director/aid/",
    "aid_director": "/director/aid/",
    "admissions_director": "/director/admissions/",
    "enrollment_director": "/director/admissions/",

    # Future examples (safe placeholders)
    "hr_director": "/director/hr/",
    "academics_director": "/director/academics/",
    "operations_director": "/director/operations/",
}

def _get_active_persona(request) -> str | None:
    """
    Determine active persona in a predictable, server-side way.
    Priority:
      1) Demo persona stored in session (if using demo-mode switcher)
      2) User profile fields (if implemented)
      3) Django groups (fallback)
    """
    # 1) Demo-mode session persona (common pattern)
    persona = request.session.get("active_persona") or request.session.get("demo_persona")
    if persona:
        return str(persona).strip().lower().replace(" ", "_")

    user = request.user

    # 2) Profile-based persona (if you have it)
    # Common names: user.profile.persona, user.persona, user.role, etc.
    for attr_path in ("persona", "role", "profile.persona", "profile.role"):
        try:
            obj = user
            for part in attr_path.split("."):
                obj = getattr(obj, part)
            if obj:
                return str(obj).strip().lower()
        except AttributeError:
            pass

    # 3) Group fallback (if you use Django groups)
    try:
        groups = list(user.groups.values_list("name", flat=True))
        # Normalize group names into persona keys
        normalized = [g.strip().lower().replace(" ", "_") for g in groups]
        for g in normalized:
            if g in DIRECTOR_ROUTE_BY_PERSONA:
                return g
    except Exception:
        logger.debug("persona from Django groups unavailable", exc_info=True)

    return None


@login_required
def director_router(request):
    """
    Single landing page for all directors.
    - If persona is recognized, redirect to /director/<persona>/
    - Otherwise deny or send to a neutral home page (choose one).
    """
    persona = _get_active_persona(request)

    if persona in DIRECTOR_ROUTE_BY_PERSONA:
        return redirect(DIRECTOR_ROUTE_BY_PERSONA[persona])

    # If the user is authenticated but not a director persona,
    # you can either:
    # A) send them to a generic dashboard/home
    # B) forbid access (strict)
    #
    # Choose B for security clarity:
    return HttpResponseForbidden("Director dashboard access not available for this persona.")
