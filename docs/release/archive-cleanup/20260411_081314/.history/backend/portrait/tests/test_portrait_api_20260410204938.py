from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserRole
from portrait.models import PoGDomain, PoGRubricLevel, PortraitConfig


pytestmark = pytest.mark.django_db


class TestPortraitApi:
    def _client(self, *, with_edit: bool = True):
        school = School.objects.create(name="Heritage Admissions Academy")

        view_permission, _ = CrownPermission.objects.get_or_create(
            code="admissions.view",
            defaults={"description": "View admissions pipeline and applicants"},
        )
        RolePermission.objects.get_or_create(role_code="ADMISSIONS_MANAGER", permission=view_permission)

        if with_edit:
            edit_permission, _ = CrownPermission.objects.get_or_create(
                code="admissions.edit",
                defaults={"description": "Advance, waitlist, or deny applicants"},
            )
            RolePermission.objects.get_or_create(role_code="ADMISSIONS_MANAGER", permission=edit_permission)

        user = get_user_model().objects.create_user(
            username=f"portrait-user-{school.id}",
            password="pass1234",
            email=f"portrait-{school.id}@example.com",
            school=school,
        )
        UserRole.objects.get_or_create(user=user, school=school, role_code="ADMISSIONS_MANAGER")

        client = APIClient()
        client.force_authenticate(user=user)
        return client, school

    def _config(self, school: School) -> PortraitConfig:
        config = PortraitConfig.objects.create(
            school=school,
            name="Admissions Portrait Rubric",
            version="2026.1",
            is_active=True,
            preamble="Mission-fit review",
        )
        domain_specs = [
            ("Faith Formation", Decimal("0.5000"), True),
            ("Character & Leadership", Decimal("0.5000"), False),
        ]
        for index, (name, weight, is_faith_anchor) in enumerate(domain_specs):
            domain = PoGDomain.objects.create(
                school=school,
                config=config,
                name=name,
                domain_type="custom",
                description=f"Assess {name.lower()} alignment",
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
        return config

    def test_portrait_summary_returns_live_counts_and_record_list(self):
        client, school = self._client()
        self._config(school)

        create_response = client.post(
            "/api/v1/portrait/records/",
            {"applicant_id": "A1001", "context": "interview"},
            format="json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert create_response.status_code == 201

        record_payload = create_response.json()
        record_id = record_payload["id"]
        scores = [
            {
                "domain": str(score["domain"]),
                "score": 4 if score.get("is_faith_anchor") else 5,
                "notes": "Admissions committee evidence logged.",
            }
            for score in record_payload["domain_scores"]
        ]

        score_response = client.post(
            f"/api/v1/portrait/records/{record_id}/score-batch/",
            {"scores": scores, "run_engine": True},
            format="json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert score_response.status_code == 200
        assert score_response.json()["record"]["recommendation"] == "strong_accept"

        summary_response = client.get(
            "/api/v1/portrait/records/summary/?limit=5",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert summary_response.status_code == 200
        payload = summary_response.json()
        assert payload["source"] == "live_db"
        assert payload["total_records"] == 1
        assert payload["completed_records"] == 1
        assert payload["recent_records"][0]["applicant_id"] == "A1001"
        assert any(item["code"] == "strong_accept" and item["count"] == 1 for item in payload["recommendation_breakdown"])

        list_response = client.get(
            "/api/v1/portrait/records/?recommendation=strong_accept",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

    def test_portrait_create_requires_edit_permission(self):
        client, school = self._client(with_edit=False)
        self._config(school)

        create_response = client.post(
            "/api/v1/portrait/records/",
            {"applicant_id": "A2002", "context": "application"},
            format="json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert create_response.status_code == 403

        summary_response = client.get(
            "/api/v1/portrait/records/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert summary_response.status_code == 200

    def test_portrait_create_rejects_foreign_school_config(self):
        client, school = self._client()
        other_school = School.objects.create(name="Second Heritage Academy")
        foreign_config = self._config(other_school)

        create_response = client.post(
            "/api/v1/portrait/records/",
            {
                "applicant_id": "A3003",
                "context": "application",
                "config": foreign_config.id,
            },
            format="json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )

        assert create_response.status_code == 400
        assert "config" in create_response.json()
