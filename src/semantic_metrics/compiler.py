"""Deterministic SQL compilation from validated semantic contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .catalog import Catalog, Measure, Metric
from .validator import require_valid_catalog


@dataclass(frozen=True, slots=True)
class QueryRequest:
    metric: str
    dimensions: tuple[str, ...]
    grain: str
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("start must be earlier than end")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("requested dimensions must be unique")


class SqlCompiler:
    def __init__(self, catalog: Catalog) -> None:
        require_valid_catalog(catalog)
        self.catalog = catalog

    def compile(self, request: QueryRequest) -> str:
        metric = self.catalog.metrics.get(request.metric)
        if metric is None:
            raise ValueError(f"unknown metric: {request.metric!r}")
        if request.grain not in metric.allowed_time_grains:
            raise ValueError(
                f"grain {request.grain!r} is not allowed for metric {metric.name!r}"
            )
        disallowed = sorted(set(request.dimensions) - set(metric.allowed_dimensions))
        if disallowed:
            raise ValueError(
                f"dimensions not allowed for metric {metric.name!r}: {', '.join(disallowed)}"
            )

        model = self.catalog.models[metric.model]
        time_expression = model.dimensions[metric.time_dimension].expression
        time_bucket = f"DATE_TRUNC('{request.grain}', {time_expression})"
        dimension_items = [
            (model.dimensions[name].expression, name) for name in request.dimensions
        ]
        metric_expression = self._metric_expression(metric)

        select_items = [f"  {time_bucket} AS metric_time"]
        select_items.extend(
            f"  {expression} AS {alias}" for expression, alias in dimension_items
        )
        select_items.append(f"  {metric_expression} AS {metric.name}")

        group_expressions = [time_bucket]
        group_expressions.extend(expression for expression, _ in dimension_items)
        order_aliases = ["metric_time"]
        order_aliases.extend(alias for _, alias in dimension_items)
        start = request.start.isoformat()
        end = request.end.isoformat()

        return "\n".join(
            [
                f"-- synthetic semantic catalog: {self.catalog.name}",
                f"-- metric contract: {metric.name} ({metric.certification})",
                "SELECT",
                ",\n".join(select_items),
                f"FROM {model.relation}",
                f"WHERE {time_expression} >= TIMESTAMP '{start} 00:00:00'",
                f"  AND {time_expression} < TIMESTAMP '{end} 00:00:00'",
                f"GROUP BY {', '.join(group_expressions)}",
                f"ORDER BY {', '.join(order_aliases)};",
            ]
        )

    def _metric_expression(self, metric: Metric) -> str:
        model = self.catalog.models[metric.model]
        if metric.metric_type == "simple":
            if metric.measure is None:  # protected by catalog validation
                raise RuntimeError("validated simple metric has no measure")
            return self._aggregate(model.measures[metric.measure])
        if metric.numerator is None or metric.denominator is None:
            raise RuntimeError("validated ratio metric has incomplete measures")
        numerator = self._aggregate(model.measures[metric.numerator])
        denominator = self._aggregate(model.measures[metric.denominator])
        return f"(1.0 * {numerator}) / NULLIF({denominator}, 0)"

    @staticmethod
    def _aggregate(measure: Measure) -> str:
        if measure.aggregation == "count_distinct":
            return f"COUNT(DISTINCT {measure.expression})"
        return f"{measure.aggregation.upper()}({measure.expression})"

