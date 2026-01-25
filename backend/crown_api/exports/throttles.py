from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class ExportUserMinuteThrottle(UserRateThrottle):
    scope = "exports_user_minute"


class ExportUserHourThrottle(UserRateThrottle):
    scope = "exports_user_hour"


class ExportIPMinuteThrottle(SimpleRateThrottle):
    """Per-IP throttle that applies to authenticated and anonymous users."""

    scope = "exports_ip_minute"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}
