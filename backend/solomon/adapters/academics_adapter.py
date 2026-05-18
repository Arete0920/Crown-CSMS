"""Academics context adapter."""

from solomon.adapters.base import BaseSolomonAdapter, SolomonContextRequest, SolomonContextPayload


class AcademicsAdapter(BaseSolomonAdapter):
    """Adapter for academics module context."""

    def _resolve_context(
        self, req: SolomonContextRequest
    ) -> SolomonContextPayload:
        """
        Resolve context for academics routes.

        Matches:
        - module: "academics"
        - route: "/courses/enrollment", "/grades/report", etc.
        - audience: student, parent, faculty

        Returns:
            SolomonContextPayload with relevant resources, playbooks, guidance
        """
        # Validate request
        if req.module != "academics":
            return self._empty_payload()

        # Determine scope (default to school if not specified)
        scope = req.scope or "school"

        # Determine audience (default to student if not specified)
        audience_name = req.audience or "student"

        # Query visible context rules for this route
        try:
            context_rules = list(
                self.visible_context_rules(
                    req.request,
                    module=req.module,
                    route=req.route,
                    audience=audience_name,
                )
            )
        except Exception:
            context_rules = []

        # If no rules matched, return empty
        if not context_rules:
            return self._empty_payload()

        # Collect all audience IDs from matched rules
        audience_ids = set()
        for rule in context_rules:
            if hasattr(rule, "audience_id") and rule.audience_id:
                audience_ids.add(rule.audience_id)

        # Query resources and playbooks linked to these audiences
        resources = []
        playbooks = []

        try:
            if audience_ids:
                # Query resources visible to this audience
                all_resources = self.visible_resources(
                    req.request,
                    module=req.module,
                    route=req.route,
                    audience=audience_name,
                    scope=scope,
                )
                resources = [
                    {
                        "id": r.id,
                        "title": r.title,
                        "resource_type": r.resource_type,
                        "category": r.category.name if r.category else None,
                        "visibility": r.visibility,
                    }
                    for r in all_resources[:10]  # Limit to 10 results
                ]

                # Query playbooks visible to this audience
                all_playbooks = self.visible_playbooks(
                    req.request,
                    module=req.module,
                    route=req.route,
                    audience=audience_name,
                )
                playbooks = [
                    {
                        "id": p.id,
                        "title": p.title,
                        "summary": p.summary[:200] if p.summary else None,
                        "visibility": p.visibility,
                    }
                    for p in all_playbooks[:5]  # Limit to 5 results
                ]
        except Exception:
            # Fail-closed: if queries fail, return empty lists
            resources = []
            playbooks = []

        # Serialize context rules
        rules_data = []
        for rule in context_rules:
            try:
                rules_data.append(
                    {
                        "id": rule.id,
                        "route_path": rule.route_path,
                        "audience": rule.audience.name if rule.audience else None,
                        "context_key": rule.context_key[:500]
                        if rule.context_key
                        else None,
                        "is_active": rule.is_active,
                    }
                )
            except Exception:
                continue

        # Return resolved payload
        return self._resolved_payload(
            resources=resources,
            playbooks=playbooks,
            context_rules=rules_data,
            metadata={
                "module": req.module,
                "route": req.route,
                "audience": audience_name,
                "scope": scope,
                "matched_rules": len(rules_data),
            },
        )
