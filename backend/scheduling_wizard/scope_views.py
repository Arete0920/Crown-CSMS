from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import Term
from core.models import AcademicYear
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id


@api_view(["GET"])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([CrownModulePermission("scheduling.view")])
def scope_options(request):
    school_id = get_request_school_id(request)
    years = AcademicYear.objects.filter(school_id=school_id).order_by("-start_date", "name")
    terms = Term.objects.filter(school_id=school_id).select_related("academic_year").order_by(
        "-academic_year__start_date", "ordering", "code"
    )
    return Response(
        {
            "academic_years": [
                {
                    "academic_year_id": str(year.id),
                    "name": year.name,
                    "start_date": year.start_date,
                    "end_date": year.end_date,
                    "is_current": year.is_current,
                }
                for year in years
            ],
            "terms": [
                {
                    "term_id": str(term.id),
                    "academic_year_id": str(term.academic_year_id),
                    "code": term.code,
                    "name": term.name,
                    "active": term.active,
                }
                for term in terms
            ],
        }
    )
