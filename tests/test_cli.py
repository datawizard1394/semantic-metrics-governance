from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from semantic_metrics.cli import main


class CliTests(unittest.TestCase):
    def test_validate_reports_provenance(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--catalog", "examples/catalog.json", "validate"])
        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["valid"])
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["production_deployment"])

    def test_compile_command_outputs_sql(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "--catalog",
                    "examples/catalog.json",
                    "compile",
                    "--metric",
                    "order_count",
                    "--grain",
                    "month",
                    "--start",
                    "2026-01-01",
                    "--end",
                    "2026-04-01",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn("COUNT(DISTINCT order_id) AS order_count", output.getvalue())


if __name__ == "__main__":
    unittest.main()

