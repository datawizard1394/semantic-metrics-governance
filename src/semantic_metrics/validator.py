"""Cross-reference, grain, ownership, and identifier contract validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .catalog import Catalog

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RELATION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,2}$")
ALLOWED_TYPES = {"string", "integer", "decimal", "boolean", "date", "timestamp"}
ALLOWED_AGGREGATIONS = {"sum", "count", "count_distinct", "avg", "min", "max"}
ALLOWED_GRAINS = {"day", "week", "month"}
ALLOWED_CERTIFICATIONS = {"experimental", "verified", "deprecated"}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class ContractValidationError(ValueError):
    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__(f"catalog has {len(issues)} contract validation issue(s)")


def _required(
    value: str,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if not value.strip():
        issues.append(ValidationIssue("required", path, "value is required"))


def validate_catalog(catalog: Catalog) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    _required(catalog.catalog_version, "catalog_version", issues)
    _required(catalog.name, "metadata.name", issues)
    _required(catalog.owner, "metadata.owner", issues)
    if not catalog.synthetic:
        issues.append(
            ValidationIssue(
                "demo_provenance",
                "metadata.synthetic",
                "this repository accepts synthetic demo catalogs only",
            )
        )
    if catalog.production_deployment:
        issues.append(
            ValidationIssue(
                "demo_provenance",
                "metadata.production_deployment",
                "must remain false for this portfolio demo",
            )
        )
    if not catalog.models:
        issues.append(ValidationIssue("required", "models", "at least one model is required"))
    if not catalog.metrics:
        issues.append(ValidationIssue("required", "metrics", "at least one metric is required"))

    for model_name, model in sorted(catalog.models.items()):
        path = f"models.{model_name}"
        if not IDENTIFIER.fullmatch(model_name):
            issues.append(ValidationIssue("unsafe_identifier", path, "invalid model identifier"))
        _required(model.description, f"{path}.description", issues)
        _required(model.owner, f"{path}.owner", issues)
        if not RELATION.fullmatch(model.relation):
            issues.append(
                ValidationIssue(
                    "unsafe_relation",
                    f"{path}.relation",
                    "relation must be a two- or three-part SQL identifier",
                )
            )
        if not model.primary_grain:
            issues.append(
                ValidationIssue("grain_required", f"{path}.primary_grain", "grain is required")
            )
        if len(set(model.primary_grain)) != len(model.primary_grain):
            issues.append(
                ValidationIssue(
                    "duplicate_grain",
                    f"{path}.primary_grain",
                    "grain dimensions must be unique",
                )
            )
        for grain_dimension in model.primary_grain:
            if grain_dimension not in model.dimensions:
                issues.append(
                    ValidationIssue(
                        "unknown_dimension",
                        f"{path}.primary_grain",
                        f"{grain_dimension!r} is not a model dimension",
                    )
                )
            elif not model.dimensions[grain_dimension].is_entity:
                issues.append(
                    ValidationIssue(
                        "invalid_grain",
                        f"{path}.primary_grain",
                        f"{grain_dimension!r} must be marked is_entity",
                    )
                )

        for dimension_name, dimension in sorted(model.dimensions.items()):
            dimension_path = f"{path}.dimensions.{dimension_name}"
            if not IDENTIFIER.fullmatch(dimension_name):
                issues.append(
                    ValidationIssue("unsafe_identifier", dimension_path, "invalid identifier")
                )
            if not IDENTIFIER.fullmatch(dimension.expression):
                issues.append(
                    ValidationIssue(
                        "unsafe_expression",
                        f"{dimension_path}.expression",
                        "demo expressions must be a single SQL identifier",
                    )
                )
            if dimension.data_type not in ALLOWED_TYPES:
                issues.append(
                    ValidationIssue(
                        "invalid_type",
                        f"{dimension_path}.type",
                        f"expected one of {sorted(ALLOWED_TYPES)}",
                    )
                )

        for measure_name, measure in sorted(model.measures.items()):
            measure_path = f"{path}.measures.{measure_name}"
            if not IDENTIFIER.fullmatch(measure_name):
                issues.append(
                    ValidationIssue("unsafe_identifier", measure_path, "invalid identifier")
                )
            if measure.aggregation not in ALLOWED_AGGREGATIONS:
                issues.append(
                    ValidationIssue(
                        "invalid_aggregation",
                        f"{measure_path}.aggregation",
                        f"expected one of {sorted(ALLOWED_AGGREGATIONS)}",
                    )
                )
            if not IDENTIFIER.fullmatch(measure.expression):
                issues.append(
                    ValidationIssue(
                        "unsafe_expression",
                        f"{measure_path}.expression",
                        "demo expressions must be a single SQL identifier",
                    )
                )

    for metric_name, metric in sorted(catalog.metrics.items()):
        path = f"metrics.{metric_name}"
        if not IDENTIFIER.fullmatch(metric_name):
            issues.append(ValidationIssue("unsafe_identifier", path, "invalid metric identifier"))
        _required(metric.description, f"{path}.description", issues)
        _required(metric.owner, f"{path}.owner", issues)
        model = catalog.models.get(metric.model)
        if model is None:
            issues.append(
                ValidationIssue(
                    "unknown_model",
                    f"{path}.model",
                    f"{metric.model!r} does not exist",
                )
            )
            continue
        if metric.metric_type not in {"simple", "ratio"}:
            issues.append(
                ValidationIssue(
                    "invalid_metric_type",
                    f"{path}.type",
                    "expected 'simple' or 'ratio'",
                )
            )
        if metric.metric_type == "simple":
            if not metric.measure or metric.measure not in model.measures:
                issues.append(
                    ValidationIssue(
                        "unknown_measure",
                        f"{path}.measure",
                        f"{metric.measure!r} does not exist on model {model.name!r}",
                    )
                )
            if metric.numerator or metric.denominator:
                issues.append(
                    ValidationIssue(
                        "ambiguous_definition",
                        path,
                        "simple metrics cannot define numerator or denominator",
                    )
                )
        if metric.metric_type == "ratio":
            for field_name, reference in (
                ("numerator", metric.numerator),
                ("denominator", metric.denominator),
            ):
                if not reference or reference not in model.measures:
                    issues.append(
                        ValidationIssue(
                            "unknown_measure",
                            f"{path}.{field_name}",
                            f"{reference!r} does not exist on model {model.name!r}",
                        )
                    )
            if metric.measure:
                issues.append(
                    ValidationIssue(
                        "ambiguous_definition",
                        path,
                        "ratio metrics cannot define measure",
                    )
                )
        if metric.time_dimension not in model.dimensions:
            issues.append(
                ValidationIssue(
                    "unknown_dimension",
                    f"{path}.time_dimension",
                    f"{metric.time_dimension!r} does not exist on model {model.name!r}",
                )
            )
        elif model.dimensions[metric.time_dimension].data_type not in {"date", "timestamp"}:
            issues.append(
                ValidationIssue(
                    "invalid_time_dimension",
                    f"{path}.time_dimension",
                    "time dimension must have date or timestamp type",
                )
            )
        if not metric.allowed_time_grains:
            issues.append(
                ValidationIssue(
                    "grain_required",
                    f"{path}.allowed_time_grains",
                    "at least one time grain is required",
                )
            )
        for grain in metric.allowed_time_grains:
            if grain not in ALLOWED_GRAINS:
                issues.append(
                    ValidationIssue(
                        "invalid_time_grain",
                        f"{path}.allowed_time_grains",
                        f"{grain!r} is not supported",
                    )
                )
        if len(set(metric.allowed_dimensions)) != len(metric.allowed_dimensions):
            issues.append(
                ValidationIssue(
                    "duplicate_dimension",
                    f"{path}.allowed_dimensions",
                    "allowed dimensions must be unique",
                )
            )
        for dimension in metric.allowed_dimensions:
            if dimension not in model.dimensions:
                issues.append(
                    ValidationIssue(
                        "unknown_dimension",
                        f"{path}.allowed_dimensions",
                        f"{dimension!r} does not exist on model {model.name!r}",
                    )
                )
        if metric.certification not in ALLOWED_CERTIFICATIONS:
            issues.append(
                ValidationIssue(
                    "invalid_certification",
                    f"{path}.certification",
                    f"expected one of {sorted(ALLOWED_CERTIFICATIONS)}",
                )
            )
    return tuple(issues)


def require_valid_catalog(catalog: Catalog) -> None:
    issues = validate_catalog(catalog)
    if issues:
        raise ContractValidationError(issues)

