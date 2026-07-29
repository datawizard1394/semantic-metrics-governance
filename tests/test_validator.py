from __future__ import annotations

import unittest

from semantic_metrics.catalog import Catalog
from semantic_metrics.validator import validate_catalog

from helpers import cloned_catalog_dict


class CatalogValidationTests(unittest.TestCase):
    def test_example_catalog_is_valid_and_explicitly_synthetic(self) -> None:
        catalog = Catalog.from_dict(cloned_catalog_dict())
        self.assertEqual(validate_catalog(catalog), ())
        self.assertTrue(catalog.synthetic)
        self.assertFalse(catalog.production_deployment)

    def test_unknown_allowed_dimension_is_rejected(self) -> None:
        raw = cloned_catalog_dict()
        raw["metrics"]["gross_revenue"]["allowed_dimensions"].append("unknown")
        issues = validate_catalog(Catalog.from_dict(raw))
        self.assertIn("unknown_dimension", {issue.code for issue in issues})

    def test_non_entity_primary_grain_is_rejected(self) -> None:
        raw = cloned_catalog_dict()
        raw["models"]["orders"]["dimensions"]["order_id"]["is_entity"] = False
        issues = validate_catalog(Catalog.from_dict(raw))
        self.assertIn("invalid_grain", {issue.code for issue in issues})

    def test_unsafe_sql_expression_is_rejected(self) -> None:
        raw = cloned_catalog_dict()
        raw["models"]["orders"]["measures"]["gross_revenue_amount"][
            "expression"
        ] = "amount); DROP TABLE users;--"
        issues = validate_catalog(Catalog.from_dict(raw))
        self.assertIn("unsafe_expression", {issue.code for issue in issues})

    def test_ratio_measure_must_exist_on_same_model(self) -> None:
        raw = cloned_catalog_dict()
        raw["metrics"]["average_order_value"]["denominator"] = "missing"
        issues = validate_catalog(Catalog.from_dict(raw))
        self.assertIn("unknown_measure", {issue.code for issue in issues})

    def test_demo_cannot_claim_production_deployment(self) -> None:
        raw = cloned_catalog_dict()
        raw["metadata"]["production_deployment"] = True
        issues = validate_catalog(Catalog.from_dict(raw))
        self.assertIn("demo_provenance", {issue.code for issue in issues})


if __name__ == "__main__":
    unittest.main()

