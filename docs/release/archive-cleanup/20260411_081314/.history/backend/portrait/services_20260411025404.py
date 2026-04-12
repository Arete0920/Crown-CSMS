from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.db import transaction
from django.db.models import Avg, Count

from core.tenant_models import tenant_context

from .models import AdmissionsPoGRecord, PoGDomainScore, RECOMMENDATION_CHOICES


RECOMMENDATION_LABELS = {
    "strong_accept": "Strong Accept — Exemplary Mission Alignment",
    "accept": "Accept — Good Mission Alignment",
    "accept_review": "Accept with Review — Partial Alignment",
    "hold": "Hold — Needs Admissions Committee Review",
    "decline": "Decline — Mission Misalignment Concern",
}


@dataclass(frozen=True)
class DomainResult:
    domain_id: str
    domain_name: str
    score: Optional[int]
    weight: Decimal
    weighted_contribution: Decimal
    weight_percentage: float
    is_faith_anchor: bool
    faith_gate_triggered: bool


@dataclass(frozen=True)
class EngineResult:
    composite_score: Decimal
    composite_percentage: Decimal
    recommendation: str
    recommendation_label: str
    faith_gate_triggered: bool
    faith_gate_domain: Optional[str]
    is_complete: bool
    scored_count: int
    required_count: int
    domain_results: list[DomainResult]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "composite_score": str(self.composite_score),
            "composite_percentage": str(self.composite_percentage),
            "recommendation": self.recommendation,
            "recommendation_label": self.recommendation_label,
            "faith_gate_triggered": self.faith_gate_triggered,
            "faith_gate_domain": self.faith_gate_domain,
            "is_complete": self.is_complete,
            "scored_count": self.scored_count,
            "required_count": self.required_count,
            "domain_results": [
                {
                    "domain_id": row.domain_id,
                    "domain_name": row.domain_name,
                    "score": row.score,
                    "weight": str(row.weight),
                    "weighted_contribution": str(row.weighted_contribution),
                    "weight_percentage": row.weight_percentage,
                    "is_faith_anchor": row.is_faith_anchor,
                    "faith_gate_triggered": row.faith_gate_triggered,
                }
                for row in self.domain_results
            ],
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _build_domain_result(domain, row, config) -> tuple[DomainResult, Decimal, int, bool, list[str], Optional[str]]:
    score = getattr(row, "score", None) if row else None
    weighted = Decimal("0.0000")
    warnings: list[str] = []
    domain_gate = False
    faith_gate_domain = None

    if score is not None:
        weighted = (Decimal(str(score)) * domain.weight).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    if (
        domain.is_faith_anchor
        and config.require_faith_formation_minimum
        and score is not None
        and score < config.faith_minimum_score
    ):
        domain_gate = True
        faith_gate_domain = domain.name
        warnings.append(
            f"Faith gate triggered: '{domain.name}' scored {score} (minimum {config.faith_minimum_score})."
        )

    return (
        DomainResult(
            domain_id=str(domain.id),
            domain_name=domain.name,
            score=score,
            weight=domain.weight,
            weighted_contribution=weighted,
            weight_percentage=float(domain.weight * 100),
            is_faith_anchor=domain.is_faith_anchor,
            faith_gate_triggered=domain_gate,
        ),
        weighted,
        int(score is not None),
        domain_gate,
        warnings,
        faith_gate_domain,
    )


def _compute_composite_percentage(*, composite_score, scored_count, required_count, active_domains, domain_scores):
    if scored_count == 0:
        return Decimal("0.00"), []

    if scored_count == required_count:
        percentage = ((composite_score / Decimal("5")) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return percentage, []

    scored_weight_total = sum(
        (d.weight for d in active_domains if getattr(domain_scores.get(str(d.id)), "score", None) is not None),
        Decimal("0.0000"),
    )
    if scored_weight_total <= 0:
        return Decimal("0.00"), []

    percentage = ((composite_score / (Decimal("5") * scored_weight_total)) * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    warning = (
        f"Score is partial ({scored_count}/{required_count} domains). Percentage is scaled to scored domains only."
    )
    return percentage, [warning]


class WeightEngine:
    def __init__(self, record):
        self.record = record
        self.config = record.config

    @transaction.atomic
    def compute(self) -> EngineResult:
        errors = validate_config(self.config)
        if errors:
            raise ValueError(f"PoG config is invalid: {'; '.join(errors)}")

        domain_scores = {
            str(ds.domain_id): ds
            for ds in self.record.domain_scores.select_related("domain").all()
        }
        result = self._compute_internal(domain_scores)

        self.record.composite_score = result.composite_score
        self.record.composite_percentage = result.composite_percentage
        self.record.recommendation = result.recommendation
        self.record.faith_gate_triggered = result.faith_gate_triggered
        self.record.is_complete = result.is_complete
        self.record.save(
            update_fields=[
                "composite_score",
                "composite_percentage",
                "recommendation",
                "faith_gate_triggered",
                "is_complete",
                "updated_at",
            ]
        )
        return result

    def dry_run(self, domain_score_map: dict) -> EngineResult:
        class _PreviewScore:
            def __init__(self, domain, score):
                self.domain = domain
                self.domain_id = str(domain.id)
                self.score = score

        active_domains = {str(d.id): d for d in self.config.domains.filter(is_active=True)}
        preview_rows = {
            str(domain_id): _PreviewScore(active_domains[str(domain_id)], score)
            for domain_id, score in domain_score_map.items()
            if str(domain_id) in active_domains
        }
        return self._compute_internal(preview_rows)

    def _compute_internal(self, domain_scores: dict) -> EngineResult:
        config = self.config
        active_domains = list(config.domains.filter(is_active=True).order_by("order"))
        required_count = len(active_domains)
        scored_count = 0
        composite_score = Decimal("0.0000")
        faith_gate_triggered = False
        faith_gate_domain = None
        warnings: list[str] = []
        errors: list[str] = []
        results: list[DomainResult] = []

        for domain in active_domains:
            result, weighted, score_increment, domain_gate, domain_warnings, domain_gate_name = _build_domain_result(
                domain,
                domain_scores.get(str(domain.id)),
                config,
            )
            results.append(result)
            composite_score += weighted
            scored_count += score_increment
            warnings.extend(domain_warnings)
            faith_gate_triggered = faith_gate_triggered or domain_gate
            if faith_gate_domain is None and domain_gate_name is not None:
                faith_gate_domain = domain_gate_name

        is_complete = scored_count == required_count
        composite_percentage, percentage_warnings = _compute_composite_percentage(
            composite_score=composite_score,
            scored_count=scored_count,
            required_count=required_count,
            active_domains=active_domains,
            domain_scores=domain_scores,
        )
        warnings.extend(percentage_warnings)

        recommendation = self._derive_recommendation(
            composite_percentage=composite_percentage,
            faith_gate=faith_gate_triggered,
            is_complete=is_complete,
        )

        return EngineResult(
            composite_score=composite_score.quantize(Decimal("0.0001")),
            composite_percentage=composite_percentage,
            recommendation=recommendation,
            recommendation_label=RECOMMENDATION_LABELS[recommendation],
            faith_gate_triggered=faith_gate_triggered,
            faith_gate_domain=faith_gate_domain,
            is_complete=is_complete,
            scored_count=scored_count,
            required_count=required_count,
            domain_results=results,
            warnings=warnings,
            errors=errors,
        )

    def _derive_recommendation(self, composite_percentage: Decimal, faith_gate: bool, is_complete: bool) -> str:
        if not is_complete:
            return "hold"
        if faith_gate:
            return "hold"
        if composite_percentage >= self.config.threshold_strong_accept:
            return "strong_accept"
        if composite_percentage >= self.config.threshold_accept:
            return "accept"
        if composite_percentage >= self.config.threshold_accept_review:
            return "accept_review"
        if composite_percentage >= self.config.threshold_hold:
            return "hold"
        return "decline"


def validate_config(config) -> list[str]:
    errors: list[str] = []
    active_domains = list(config.domains.filter(is_active=True))

    if not active_domains:
        return ["Config has no active domains."]

    total_weight = sum((d.weight for d in active_domains), Decimal("0.0000"))
    if abs(total_weight - Decimal("1.0000")) > Decimal("0.0100"):
        errors.append(
            f"Active domain weights sum to {total_weight:.4f} — must equal 1.0000 (±0.01 tolerance)."
        )

    for domain in active_domains:
        level_count = domain.rubric_levels.count()
        if level_count != 5:
            errors.append(
                f"Domain '{domain.name}' has {level_count} rubric levels — exactly 5 required."
            )

    try:
        config.clean()
    except Exception as exc:
        errors.append(str(exc))

    return errors


def initialize_domain_scores(record):
    created = []
    for domain in record.config.domains.filter(is_active=True).order_by("order"):
        ds, _ = PoGDomainScore.objects.get_or_create(
            record=record,
            domain=domain,
            defaults={"school": record.school, "notes": ""},
        )
        created.append(ds)
    return created


def normalize_weights(domain_weights: dict) -> dict:
    decimal_map = {str(key): Decimal(str(value)) for key, value in domain_weights.items()}
    total = sum(decimal_map.values(), Decimal("0.0000"))
    if total == 0:
        raise ValueError("Cannot normalize weights — total is zero.")

    normalized = {
        key: (value / total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        for key, value in decimal_map.items()
    }
    drift = Decimal("1.0000") - sum(normalized.values(), Decimal("0.0000"))
    if drift != 0 and normalized:
        first_key = next(iter(normalized))
        normalized[first_key] = (normalized[first_key] + drift).quantize(Decimal("0.0001"))
    return normalized


def _resolve_school_instance(school):
    if hasattr(school, "id"):
        return school

    from core.models import School

    return School._default_manager.get(pk=school)


def _build_recommendation_breakdown(records):
    return [
        {
            "code": code,
            "label": label,
            "count": records.filter(recommendation=code).count(),
        }
        for code, label in RECOMMENDATION_CHOICES
    ]


def _build_top_domains(school):
    return [
        {
            "name": row["domain__name"],
            "average_score": round(float(row["avg_score"]), 2),
            "count": row["count"],
        }
        for row in PoGDomainScore.objects.filter(record__school=school, score__isnull=False)
        .values("domain__name")
        .annotate(avg_score=Avg("score"), count=Count("id"))
        .order_by("-avg_score", "domain__name")[:5]
    ]


def _build_portrait_alerts(*, total_records, incomplete_records, faith_gate_count, avg_percentage):
    alerts = []
    if incomplete_records:
        alerts.append(
            {
                "title": f"{incomplete_records} portrait review(s) still need domain scoring completion.",
                "level": "Medium",
                "secondary": "Finish pending rubric scores before final admissions committee review.",
            }
        )
    if faith_gate_count:
        alerts.append(
            {
                "title": f"{faith_gate_count} applicant(s) triggered the faith-formation gate.",
                "level": "High",
                "secondary": "Admissions and discipleship leaders should review covenant alignment notes.",
            }
        )
    if total_records and avg_percentage is not None and float(avg_percentage) < 65:
        alerts.append(
            {
                "title": "Average portrait alignment is below the normal acceptance threshold.",
                "level": "Medium",
                "secondary": "Review interview calibration and mission-fit evidence for the current cohort.",
            }
        )
    if alerts:
        return alerts
    return [
        {
            "title": "No portrait review blockers are currently flagged.",
            "level": "Low",
            "secondary": "Scoring coverage and mission-fit review are stable right now.",
        }
    ]


def _serialize_recent_record(record) -> dict:
    return {
        "id": str(record.id),
        "applicant_id": record.applicant_id,
        "context": record.context,
        "recommendation": record.recommendation or "pending",
        "recommendation_label": RECOMMENDATION_LABELS.get(record.recommendation or "", "Pending review"),
        "composite_percentage": float(record.composite_percentage) if record.composite_percentage is not None else None,
        "is_complete": record.is_complete,
        "faith_gate_triggered": record.faith_gate_triggered,
        "scored_at": record.scored_at.isoformat() if record.scored_at else None,
    }


def _needs_review_queue(record) -> bool:
    return (
        not record.is_complete
        or record.faith_gate_triggered
        or (record.recommendation or "") in {"hold", "accept_review"}
    )


def build_portrait_record_summary(school, *, limit: int = 6) -> dict:
    school = _resolve_school_instance(school)

    with tenant_context(school):
        records = AdmissionsPoGRecord.objects.filter(school=school).select_related("config", "scored_by")
        total_records = records.count()
        completed_records = records.filter(is_complete=True).count()
        incomplete_records = max(total_records - completed_records, 0)
        faith_gate_count = records.filter(faith_gate_triggered=True).count()
        avg_percentage = records.exclude(composite_percentage__isnull=True).aggregate(avg=Avg("composite_percentage"))["avg"]
        completion_pct = round((completed_records / total_records) * 100, 1) if total_records else 0.0
        recommendation_breakdown = _build_recommendation_breakdown(records)
        top_domains = _build_top_domains(school)
        recent_records = []
        review_queue = []

        for record in records.order_by("-scored_at", "-created_at")[: max(1, limit)]:
            item = _serialize_recent_record(record)
            recent_records.append(item)
            if _needs_review_queue(record):
                review_queue.append(
                    {
                        "label": f"Applicant {record.applicant_id} • {item['recommendation_label']}",
                        "secondary": f"{record.scored_domains_count}/{record.required_domains_count} domains scored",
                    }
                )

    alerts = _build_portrait_alerts(
        total_records=total_records,
        incomplete_records=incomplete_records,
        faith_gate_count=faith_gate_count,
        avg_percentage=avg_percentage,
    )

    return {
        "total_records": total_records,
        "completed_records": completed_records,
        "completion_pct": completion_pct,
        "faith_gate_count": faith_gate_count,
        "average_composite_percentage": round(float(avg_percentage), 2) if avg_percentage is not None else None,
        "recommendation_breakdown": recommendation_breakdown,
        "top_domains": top_domains,
        "recent_records": recent_records,
        "review_queue": review_queue,
        "alerts": alerts,
        "source": "live_db",
    }
