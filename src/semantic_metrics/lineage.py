"""Deterministic lineage graph and downstream impact traversal."""

from __future__ import annotations

import re
from collections import defaultdict, deque

from .catalog import Catalog
from .validator import require_valid_catalog


class LineageGraph:
    def __init__(self, catalog: Catalog) -> None:
        require_valid_catalog(catalog)
        self.catalog = catalog
        self.edges = self._build_edges()

    def _build_edges(self) -> tuple[tuple[str, str], ...]:
        edges: set[tuple[str, str]] = set()
        for model_name, model in self.catalog.models.items():
            model_node = f"model.{model_name}"
            for dimension_name in model.dimensions:
                edges.add((model_node, f"dimension.{model_name}.{dimension_name}"))
            for measure_name in model.measures:
                edges.add((model_node, f"measure.{model_name}.{measure_name}"))
        for metric_name, metric in self.catalog.metrics.items():
            metric_node = f"metric.{metric_name}"
            measure_names = (
                (metric.measure,)
                if metric.metric_type == "simple"
                else (metric.numerator, metric.denominator)
            )
            for measure_name in measure_names:
                if measure_name:
                    edges.add((f"measure.{metric.model}.{measure_name}", metric_node))
            for dimension_name in (
                metric.time_dimension,
                *metric.allowed_dimensions,
            ):
                edges.add(
                    (f"dimension.{metric.model}.{dimension_name}", metric_node)
                )
        return tuple(sorted(edges))

    def impact(self, node: str) -> tuple[str, ...]:
        adjacency: dict[str, list[str]] = defaultdict(list)
        nodes: set[str] = set()
        for upstream, downstream in self.edges:
            adjacency[upstream].append(downstream)
            nodes.update((upstream, downstream))
        if node not in nodes:
            raise ValueError(f"unknown lineage node: {node!r}")
        visited: set[str] = set()
        queue: deque[str] = deque(sorted(adjacency[node]))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(sorted(adjacency[current]))
        return tuple(sorted(visited))

    def to_dict(self) -> dict[str, object]:
        nodes = sorted({node for edge in self.edges for node in edge})
        return {
            "nodes": nodes,
            "edges": [
                {"upstream": upstream, "downstream": downstream}
                for upstream, downstream in self.edges
            ],
        }

    def to_mermaid(self) -> str:
        nodes = sorted({node for edge in self.edges for node in edge})

        def node_id(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9_]", "_", value)

        lines = ["flowchart LR"]
        for node in nodes:
            lines.append(f'    {node_id(node)}["{node}"]')
        for upstream, downstream in self.edges:
            lines.append(f"    {node_id(upstream)} --> {node_id(downstream)}")
        return "\n".join(lines)

