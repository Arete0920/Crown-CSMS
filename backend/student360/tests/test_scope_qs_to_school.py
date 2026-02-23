"""
Stage 3 – Tenant & Security Seal
==================================
Unit tests for _scope_qs_to_school() helper in student360.api.views.

Pure unit tests: no DB, no Django models, no migrations.
Proves fail-closed behavior: ImproperlyConfigured raised if model is unscopable.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from student360.api.views import _scope_qs_to_school


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class DummyQS:
    """Minimal queryset double that records filter() calls."""
    def __init__(self):
        self.filters = []

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        return self


class DummySchool:
    def __init__(self, id_value="00000000-0000-0000-0000-000000000001"):
        self.id = id_value


class ModelWithSchoolId:
    __name__ = "ModelWithSchoolId"
    school_id = "field"


class ModelWithSchool:
    __name__ = "ModelWithSchool"
    school = "field"


class ModelWithBoth:
    """Has both school_id and school. school_id must take precedence."""
    __name__ = "ModelWithBoth"
    school_id = "field"
    school = "field"


class ModelWithoutSchoolScope:
    __name__ = "ModelWithoutSchoolScope"
    # no school_id, no school


# ---------------------------------------------------------------------------
# Tests: correct scoping applied
# ---------------------------------------------------------------------------

class TestScopeQsToSchool:

    def test_uses_school_id_when_present(self):
        qs = DummyQS()
        school = DummySchool("00000000-0000-0000-0000-000000000001")

        out = _scope_qs_to_school(qs, ModelWithSchoolId, school)

        assert out is qs
        assert qs.filters == [{"school_id": str(school.id)}]

    def test_uses_school_fk_when_no_school_id(self):
        qs = DummyQS()
        school = DummySchool("00000000-0000-0000-0000-000000000002")

        out = _scope_qs_to_school(qs, ModelWithSchool, school)

        assert out is qs
        assert qs.filters == [{"school": school}]

    def test_school_id_takes_precedence_over_school_fk(self):
        """When a model has both school_id and school, school_id wins."""
        qs = DummyQS()
        school = DummySchool("00000000-0000-0000-0000-000000000003")

        _scope_qs_to_school(qs, ModelWithBoth, school)

        # Must use school_id, not school FK
        assert qs.filters == [{"school_id": str(school.id)}]

    def test_school_id_value_is_string(self):
        """school_id filter value must be str(school.id), matching model field type."""
        qs = DummyQS()
        school = DummySchool("abc-123")

        _scope_qs_to_school(qs, ModelWithSchoolId, school)

        assert qs.filters[0]["school_id"] == "abc-123"
        assert isinstance(qs.filters[0]["school_id"], str)

    def test_school_fk_filter_value_is_school_object(self):
        """school FK filter value must be the school object itself."""
        qs = DummyQS()
        school = DummySchool("00000000-0000-0000-0000-000000000004")

        _scope_qs_to_school(qs, ModelWithSchool, school)

        assert qs.filters[0]["school"] is school


# ---------------------------------------------------------------------------
# Tests: fail-closed on unscopable model
# ---------------------------------------------------------------------------

class TestScopeQsToSchoolFailClosed:

    def test_raises_improperly_configured_if_unscopable(self):
        qs = DummyQS()
        school = DummySchool()

        with pytest.raises(ImproperlyConfigured):
            _scope_qs_to_school(qs, ModelWithoutSchoolScope, school)

    def test_error_message_contains_model_name(self):
        qs = DummyQS()
        school = DummySchool()

        with pytest.raises(ImproperlyConfigured) as exc:
            _scope_qs_to_school(qs, ModelWithoutSchoolScope, school)

        assert "ModelWithoutSchoolScope" in str(exc.value)

    def test_no_filter_applied_before_raise(self):
        """Queryset must not be partially filtered if scoping fails."""
        qs = DummyQS()
        school = DummySchool()

        with pytest.raises(ImproperlyConfigured):
            _scope_qs_to_school(qs, ModelWithoutSchoolScope, school)

        assert qs.filters == [], "No filter must be applied to qs when scoping fails"
