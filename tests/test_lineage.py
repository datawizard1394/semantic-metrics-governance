from __future__ import annotations

import unittest

from semantic_metrics.catalog import Catalog
from semantic_metrics.lineage import LineageGraph


class LineageGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = LineageGraph(Catalog.load("examples/catalog.json"))

    def test_measure_impact_finds_dependent_metrics(self) -> None:
        impacted = self.graph.impact("measure.orders.gross_revenue_amount")
        self.assertEqual(
            impacted,
            ("metric.average_order_value", "metric.gross_revenue"),
        )

    def test_model_impact_transitively_finds_metrics(self) -> None:
        impacted = self.graph.impact("model.orders")
        self.assertIn("metric.order_count", impacted)
        self.assertIn("dimension.orders.country", impacted)
        self.assertIn("measure.orders.distinct_orders", impacted)

    def test_mermaid_render_is_deterministic(self) -> None:
        first = self.graph.to_mermaid()
        second = self.graph.to_mermaid()
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("flowchart LR"))
        self.assertIn("measure_orders_gross_revenue_amount --> metric_gross_revenue", first)

    def test_unknown_impact_node_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown lineage node"):
            self.graph.impact("metric.does_not_exist")


if __name__ == "__main__":
    unittest.main()

