from households.scoping import get_request_school_id


def school_id_from_request(request, required: bool = True) -> int:
    """
    Thin wrapper around the canonical tenant resolver.
    All views in finance_setup use this — never inline get_request_school_id.
    """
    return get_request_school_id(request, required=required)
