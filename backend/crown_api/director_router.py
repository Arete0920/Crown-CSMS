"""
Director Router - Routes authenticated director personas to their primary dashboard view

This router determines which director "home" a user should see based on their role:
- Financial Aid Director → Aid-focused view
- Admissions Director → Admissions-focused view  
- Finance Director → Finance-focused view
- Registrar → Registrar-focused view
- Head of School → Full unified view (all directors)

Architecture: Unified Dashboard with Persona-Based Filtering
- All directors use the SAME page (/director/)
- All directors use the SAME APIs (/api/director/*)
- Router changes which data is HIGHLIGHTED/FILTERED, not which page loads
"""

from core.models import UserRole


def get_director_persona(user):
    """
    Determine the primary director persona for a user.
    
    Returns:
        str: Persona code ('aid', 'admissions', 'finance', 'registrar', 'head', None)
    """
    if not user or not user.is_authenticated:
        return None
    
    # Get user's roles
    user_roles = UserRole.objects.filter(user_account=user).values_list('role_code', flat=True)
    
    # Priority order (if user has multiple director roles)
    role_mapping = {
        'ROLE_HEAD_OF_SCHOOL': 'head',      # Highest priority - sees everything
        'ROLE_AID_DIRECTOR': 'aid',
        'ROLE_ADMISSIONS_DIRECTOR': 'admissions',
        'ROLE_FINANCE_DIRECTOR': 'finance',
        'ROLE_REGISTRAR': 'registrar',
    }
    
    # Return first matching role in priority order
    for role_code, persona in role_mapping.items():
        if role_code in user_roles:
            return persona
    
    return None


def get_director_filter_config(persona):
    """
    Get the UI filter configuration for a director persona.
    
    This determines:
    - Which worklist items to highlight
    - Which KPI cards to show prominently
    - Which sections to expand by default
    
    Args:
        persona (str): Persona code from get_director_persona()
        
    Returns:
        dict: Configuration for frontend filtering/highlighting
    """
    if persona == 'head':
        # Head of School sees everything equally
        return {
            'persona': 'head',
            'highlight_types': [],  # Show all equally
            'primary_sections': ['aid', 'admissions', 'finance', 'registrar'],
            'title': 'Head of School Dashboard',
        }
    
    elif persona == 'aid':
        return {
            'persona': 'aid',
            'highlight_types': [
                'AID_APPLICATION_NEEDS_INFO',
                'AID_APPLICATION_UNDER_REVIEW',
                'AID_AWARD_ACCEPTED_NOT_POSTED',
            ],
            'primary_sections': ['aid'],
            'secondary_sections': ['finance'],  # Aid directors care about ledger posting
            'title': 'Financial Aid Director Dashboard',
        }
    
    elif persona == 'admissions':
        return {
            'persona': 'admissions',
            'highlight_types': [
                'ADMISSIONS_APPLICATION_NEEDS_INFO',
                'ADMISSIONS_APPLICATION_UNDER_REVIEW',
            ],
            'primary_sections': ['admissions'],
            'secondary_sections': ['registrar'],  # Admissions directors care about enrollments
            'title': 'Admissions Director Dashboard',
        }
    
    elif persona == 'finance':
        return {
            'persona': 'finance',
            'highlight_types': [
                'FINANCE_BALANCE_DUE',
            ],
            'primary_sections': ['finance'],
            'secondary_sections': ['aid'],  # Finance directors care about aid awards
            'title': 'Finance Director Dashboard',
        }
    
    elif persona == 'registrar':
        return {
            'persona': 'registrar',
            'highlight_types': [
                'REGISTRAR_MISSING_GRADE',
            ],
            'primary_sections': ['registrar'],
            'secondary_sections': ['admissions'],  # Registrars care about new student enrollments
            'title': 'Registrar Dashboard',
        }
    
    else:
        # Default/unknown - show everything
        return {
            'persona': None,
            'highlight_types': [],
            'primary_sections': ['aid', 'admissions', 'finance', 'registrar'],
            'title': 'Director Dashboard',
        }


def route_director_view(request):
    """
    Determine routing configuration for director dashboard view.
    
    This is used by the page view to:
    1. Pass persona context to the template
    2. Let JavaScript know which sections to emphasize
    
    Returns:
        dict: Routing configuration
    """
    persona = get_director_persona(request.user)
    filter_config = get_director_filter_config(persona)
    
    return {
        'persona': persona,
        'config': filter_config,
        'route': '/director/',  # Always the same page (unified)
        'api_endpoints': {
            'dashboard': '/api/director/dashboard/',
            'priority': '/api/director/priority/',
            'timeline': '/api/director/timeline/',
            'actions': '/api/director/actions/',
        }
    }
