from __future__ import annotations

import unittest
from datetime import date

from semantic_metrics.catalog import Catalog
from semantic_metrics.compiler import QueryRequest, SqlCompiler


class SqlCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compiler = SqlCompiler(Catalog.load("examples/catalog.json"))

    def test_simple_metric_compiles_deterministically(self) -> None:
        request = QueryRequest(
            metric="gross_revenue",
            dimensions=("country", "channel"),
            grain="day",
            start=date(2026, 1, 1),
            end=date(2026, 2, 1),
        )
        first = self.compiler.compile(request)
        second = self.compiler.compile(request)
        self.assertEqual(first, second)
        self.assertIn("SUM(order_amount) AS gross_revenue", first)
        self.assertIn("GROUP BY DATE_TRUNC('day', ordered_at), country_code, sales_channel", first)
        self.assertIn("ORDER BY metric_time, country, channel;", first)

    def test_ratio_metric_uses_null_safe_denominator(self) -> None:
        sql = self.compiler.compile(
            QueryRequest(
                metric="average_order_value",
                dimensions=("country",),
                grain="week",
                start=date(2026, 1, 1),
                end=date(2026, 3, 1),
            )
        )
        self.assertIn("1.0 * SUM(order_amount)", sql)
        self.assertIn("NULLIF(COUNT(DISTINCT order_id), 0)", sql)

    def test_disallowed_dimension_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "not allowed"):
            self.compiler.compile(
                QueryRequest(
                    metric="gross_revenue",
                    dimensions=("customer_id",),
                    grain="day",
                    start=date(2026, 1, 1),
                    end=date(2026, 2, 1),
                )
            )

    def test_disallowed_grain_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "not allowed"):
            self.compiler.compile(
                QueryRequest(
                    metric="gross_revenue",
                    dimensions=(),
                    grain="hour",
                    start=date(2026, 1, 1),
                    end=date(2026, 2, 1),
                )
            )

    def test_invalid_date_window_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "start must be earlier"):
            QueryRequest(
                metric="gross_revenue",
                dimensions=(),
                grain="day",
                start=date(2026, 2, 1),
                end=date(2026, 1, 1),
            )

    def test_duplicate_dimensions_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            QueryRequest(
                metric="gross_revenue",
                dimensions=("country", "country"),
                grain="day",
                start=date(2026, 1, 1),
                end=date(2026, 2, 1),
            )


if __name__ == "__main__":
    unittest.main()

