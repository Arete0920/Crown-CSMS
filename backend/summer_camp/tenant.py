from households.scoping import get_request_school_id


def school_id_from_request(request, required: bool = True):
    return get_request_school_id(request, required=required)
