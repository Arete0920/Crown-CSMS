"""Integrated Summer Camp uses the existing Diadem commercial entitlement."""
from rest_framework import status
from rest_framework.response import Response
from subscriptions.gates import school_has_module

CAMP_COMPAT_MODULE_KEY = "little_lambs"

def camp_entitlement_error(school_id):
    """After canonical tenant resolution, reject absent/inactive Camp licenses."""
    if school_has_module(school_id, CAMP_COMPAT_MODULE_KEY):
        return None
    return Response(
        {"detail": "Summer Camp module is not enabled for this school.",
         "code": "MODULE_NOT_ENABLED"},
        status=status.HTTP_403_FORBIDDEN,
    )
