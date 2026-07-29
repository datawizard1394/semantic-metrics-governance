"""Typed catalog loader for models, dimensions, measures, and metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Dimension:
    name: str
    expression: str
    data_type: str
    is_entity: bool


@dataclass(frozen=True, slots=True)
class Measure:
    name: str
    aggregation: str
    expression: str


@dataclass(frozen=True, slots=True)
class Model:
    name: str
    description: str
    relation: str
    owner: str
    primary_grain: tuple[str, ...]
    dimensions: dict[str, Dimension]
    measures: dict[str, Measure]


@dataclass(frozen=True, slots=True)
class Metric:
    name: str
    description: str
    owner: str
    model: str
    metric_type: str
    measure: str | None
    numerator: str | None
    denominator: str | None
    time_dimension: str
    allowed_time_grains: tuple[str, ...]
    allowed_dimensions: tuple[str, ...]
    certification: str


@dataclass(frozen=True, slots=True)
class Catalog:
    catalog_version: str
    name: str
    owner: str
    synthetic: bool
    production_deployment: bool
    models: dict[str, Model]
    metrics: dict[str, Metric]

    @classmethod
    def load(cls, path: str | Path) -> Catalog:
        with Path(path).open(encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("catalog root must be a JSON object")
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Catalog:
        metadata = raw.get("metadata", {})
        models: dict[str, Model] = {}
        for model_name, model_raw in raw.get("models", {}).items():
            dimensions = {
                name: Dimension(
                    name=name,
                    expression=str(item.get("expression", "")),
                    data_type=str(item.get("type", "")),
                    is_entity=bool(item.get("is_entity", False)),
                )
                for name, item in model_raw.get("dimensions", {}).items()
            }
            measures = {
                name: Measure(
                    name=name,
                    aggregation=str(item.get("aggregation", "")),
                    expression=str(item.get("expression", "")),
                )
                for name, item in model_raw.get("measures", {}).items()
            }
            models[model_name] = Model(
                name=model_name,
                description=str(model_raw.get("description", "")),
                relation=str(model_raw.get("relation", "")),
                owner=str(model_raw.get("owner", "")),
                primary_grain=tuple(model_raw.get("primary_grain", [])),
                dimensions=dimensions,
                measures=measures,
            )

        metrics = {
            name: Metric(
                name=name,
                description=str(item.get("description", "")),
                owner=str(item.get("owner", "")),
                model=str(item.get("model", "")),
                metric_type=str(item.get("type", "")),
                measure=item.get("measure"),
                numerator=item.get("numerator"),
                denominator=item.get("denominator"),
                time_dimension=str(item.get("time_dimension", "")),
                allowed_time_grains=tuple(item.get("allowed_time_grains", [])),
                allowed_dimensions=tuple(item.get("allowed_dimensions", [])),
                certification=str(item.get("certification", "")),
            )
            for name, item in raw.get("metrics", {}).items()
        }
        return cls(
            catalog_version=str(raw.get("catalog_version", "")),
            name=str(metadata.get("name", "")),
            owner=str(metadata.get("owner", "")),
            synthetic=bool(metadata.get("synthetic", False)),
            production_deployment=bool(metadata.get("production_deployment", False)),
            models=models,
            metrics=metrics,
        )

