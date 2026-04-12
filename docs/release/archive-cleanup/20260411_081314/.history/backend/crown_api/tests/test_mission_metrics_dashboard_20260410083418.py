from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import CrownPermission, Family, RolePermission, School, Student, UserRole
from portrait.models import AdmissionsPoGRecord, PoGDomain, PoGRubricLevel, PortraitConfig
from servicehours.models import ServiceEntry
from spiritual_life.models import ChapelAttendance, ChapelEvent


pytestmark = pytest.mark.django_db


class TestMissionMetricsDashboard:
    def _client(self, *, role_code: str = "CHAPLAIN", permissions: tuple[str, ...] = ("spiritual_life.view",)):
        school = School.objects.create(name="Mission Metrics Academy")

        for code in permissions:
            permission, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": code})
            RolePermission.objects.get_or_create(role_code=role_code, permission=permission)

        user = get_user_model().objects.create_user(
            username=f"mission-user-{school.id}",
            password="pass1234",
            email=f"mission-{school.id}@example.com",
            school=school,
        )
        UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)

        client = APIClient()
        client.force_authenticate(user=user)
        return client, school

    def _seed_portrait_record(self, school: School):
        config = PortraitConfig.objects.create(
            school=school,
            name="Mission Review Rubric",
            version="2026.1",
            is_active=True,
        )
        for index, (name, weight, is_faith_anchor) in enumerate(
            [
                ("Faith Formation", Decimal("0.5000"), True),
                ("Community Mission", Decimal("0.5000"), False),
            ]
        ):
            domain = PoGDomain.objects.create(
                school=school,
                config=config,
                name=name,
                domain_type="custom",
                description=name,
                weight=weight,
                is_faith_anchor=is_faith_anchor,
                order=index,
            )
            for level in range(1, 6):
                PoGRubricLevel.objects.create(
                    school=school,
                    domain=domain,
                    level=level,
                    label=f"Level {level}",
                    descriptor=f"Descriptor {level}",
                )

        record = AdmissionsPoGRecord.objects.create(
            school=school,
            applicant_id="MM-100",
            config=config,
            context="interview",
        )
        for domain in config.domains.all():
            record.domain_scores.create(
                school=school,
                domain=domain,
                score=4 if domain.is_faith_anchor else 5,
                notes="Mission evidence captured.",
            )
        record.composite_percentage = Decimal("90.00")
        record.recommendation = "strong_accept"
        record.is_complete = True
        record.save(update_fields=["composite_percentage", "recommendation", "is_complete", "updated_at"])

    def _seed_live_data(self, school: School):
        family = Family.objects.create(school=school, family_name="Mission Family")
        student = Student.objects.create(
            school=school,
            family=family,
            student_number="MIS-001",
            first_name="Hope",
            last_name="Harper",
            dob=date(2012, 5, 1),
        )
        chapel = ChapelEvent.objects.create(school=school, title="Weekly Chapel", event_date=date(2026, 5, 1))
        ChapelAttendance.objects.create(school=school, event=chapel, student=student, status="present")
        ServiceEntry.objects.create(
            school=school,
            student=student,
            date=date(2026, 5, 2),
            hours=Decimal("2.00"),
            category="Outreach",
            organization="Food Pantry",
            status="approved",
        )
        ServiceEntry.objects.create(
            school=school,
            student=student,
            date=date(2026, 5, 3),
            hours=Decimal("1.50"),
            category="Mentoring",
            organization="Neighborhood Center",
            status="pending",
        )
        self._seed_portrait_record(school)

    def test_portrait_service_dashboard_summary_is_live(self):
        client, school = self._client()
        self._seed_live_data(school)

        response = client.get(
            "/api/v1/dashboards/portrait-service/summary",
            HTTP_X_SCHOOL_ID=str(school.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["dashboard_key"] == "portrait-service"
        assert payload["meta"]["served_from"] == "live_db"
        assert any(item["label"] == "Mission readiness" for item in payload["metrics"])
        assert payload["detail_metrics"]["approved_service_hours"] == 2.0
        assert payload["detail_metrics"]["pending_service_hours"] == 1.5
        assert payload["detail_metrics"]["portrait_completion_pct"] == 100.0
        assert payload["detail_metrics"]["mission_readiness_pct"] > 0
        assert payload["detail_metrics"]["student_leadership"]["participation_count"] >= 1
        assert payload["detail_metrics"]["student_leadership"]["solomon_article_slugs"]

    def test_portrait_service_dashboard_denies_without_permission(self):
        client, school = self._client(role_code="DENY_ROLE", permissions=tuple())

        response = client.get(
            "/api/v1/dashboards/portrait-service/summary",
            HTTP_X_SCHOOL_ID=str(school.id),
        )

        assert response.status_code == 403
