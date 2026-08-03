"""Runtime wrappers for canonical admissions API responses.

Keep the large admissions implementation in applications.views_admissions as the
single behavior source. This wrapper adds explicit provenance only after the
canonical authenticated summary view succeeds.
"""

from applications.views_admissions import admissions_summary as canonical_admissions_summary


def admissions_summary(request, *args, **kwargs):
    response = canonical_admissions_summary(request, *args, **kwargs)
    if 200 <= int(getattr(response, "status_code", 0) or 0) < 300:
        data = getattr(response, "data", None)
        if isinstance(data, dict):
            meta = data.setdefault("meta", {})
            if isinstance(meta, dict):
                meta["served_from"] = "live_db"
                meta["source"] = "applications"
    return response
