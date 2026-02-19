from decimal import Decimal
from django.apps import apps
from django.db.models import Sum
from core.tenant_models import tenant_context
from .models import GraduationRule

class CreditAuditService:
    """
    v1 goal: demo-grade, stable.
    - Select active GraduationRule for current school.
    - Compute earned credits via best-effort introspection:
        * Try to find a model that links student->course and has credits
        * If not found, earned_credits=0 and status indicates why
    """

    # Common Student model labels we will try (in order)
    STUDENT_MODEL_CANDIDATES = [
        "core.Student",
        "students.Student",
        "academics.Student",
        "enrollment.Student",
    ]

    def _resolve_student_model(self):
        for label in self.STUDENT_MODEL_CANDIDATES:
            try:
                model = apps.get_model(label)
                if model is not None:
                    return model
            except Exception:
                continue
        return None

    def _get_active_rule(self, school):
        # TenantScopedModel will auto-scope, but we also filter explicitly for clarity.
        rule = GraduationRule.objects.filter(school=school, is_active=True).order_by("-created_at").first()
        if rule is None:
            # Fail-safe: if no rule exists, assume a common 24 credit requirement
            return {"name": "Default Graduation Policy", "required_total_credits": Decimal("24.00")}
        return {"name": rule.name, "required_total_credits": Decimal(str(rule.required_total_credits))}

    def _find_credit_source_model(self, StudentModel):
        """
        Find a plausible 'enrollment' model that:
          - has FK to student
          - has a numeric credits field OR a FK to course that has credits
        This avoids hard-binding to gradebook/academics schema for v1.
        """
        for model in apps.get_models():
            try:
                fields = {f.name: f for f in model._meta.get_fields() if hasattr(f, "name")}
                # Must have student FK
                student_fk = None
                for f in fields.values():
                    if getattr(f, "many_to_one", False) and getattr(f, "related_model", None) == StudentModel:
                        student_fk = f
                        break
                if student_fk is None:
                    continue

                # Prefer direct credits field
                credits_field = None
                for name, f in fields.items():
                    if name in ("credits", "credit_hours", "earned_credits"):
                        credits_field = name
                        break

                # Or course->credits
                course_fk = None
                for f in fields.values():
                    if getattr(f, "many_to_one", False) and getattr(f, "related_model", None) is not None:
                        if f.name in ("course", "classroom", "section"):
                            course_fk = f
                            break

                return {
                    "Model": model,
                    "student_field": student_fk.name,
                    "credits_field": credits_field,
                    "course_field": getattr(course_fk, "name", None),
                }
            except Exception:
                continue
        return None

    def _compute_earned_credits(self, student_obj, school):
        StudentModel = student_obj.__class__
        src = self._find_credit_source_model(StudentModel)
        if src is None:
            return Decimal("0.00"), "CREDIT_SOURCE_NOT_FOUND"

        Model = src["Model"]
        student_field = src["student_field"]
        credits_field = src["credits_field"]

        qs = Model.objects.filter(**{student_field: student_obj})

        # Tenant scope: if the model has school, filter it (extra safety)
        if hasattr(Model, "school_id"):
            qs = qs.filter(school=school)

        # Direct numeric credits
        if credits_field is not None and credits_field in [f.name for f in Model._meta.fields]:
            agg = qs.aggregate(total=Sum(credits_field))
            total = agg.get("total") or 0
            return Decimal(str(total)), "OK"

        # If we cannot find direct credits, do not guess. Return 0 with status.
        return Decimal("0.00"), "CREDITS_FIELD_NOT_FOUND"

    def audit(self, student_id, school):
        rule = self._get_active_rule(school)

        StudentModel = self._resolve_student_model()
        if StudentModel is None:
            return {
                "status": "STUDENT_MODEL_UNRESOLVED",
                "student_id": str(student_id),
                "rule": rule,
                "earned_credits": "0.00",
                "required_credits": str(rule["required_total_credits"]),
                "remaining_credits": str(rule["required_total_credits"]),
                "on_track": False,
                "notes": "No Student model found via known labels. Add your Student model label to CreditAuditService.STUDENT_MODEL_CANDIDATES.",
            }

        # We do not assume fields; we just test existence by PK
        student_obj = StudentModel.objects.filter(id=student_id).first()
        if student_obj is None:
            return {
                "status": "STUDENT_NOT_FOUND",
                "student_id": str(student_id),
                "rule": rule,
            }

        # Ensure tenant context for any auto-scoped reads
        with tenant_context(school):
            earned, earned_status = self._compute_earned_credits(student_obj, school)

        required = Decimal(str(rule["required_total_credits"]))
        remaining = required - earned
        if remaining < 0:
            remaining = Decimal("0.00")

        return {
            "status": "OK" if earned_status == "OK" else earned_status,
            "student_id": str(student_id),
            "rule": rule,
            "earned_credits": f"{earned:.2f}",
            "required_credits": f"{required:.2f}",
            "remaining_credits": f"{remaining:.2f}",
            "on_track": earned >= required,
        }
