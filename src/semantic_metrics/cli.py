"""CLI for validation, SQL compilation, lineage, and impact analysis."""

from __future__ import annotations

import argparse
import json
from datetime import date

from .catalog import Catalog
from .compiler import QueryRequest, SqlCompiler
from .lineage import LineageGraph
from .validator import validate_catalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and compile a synthetic semantic-metric catalog."
    )
    parser.add_argument("--catalog", default="examples/catalog.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Validate every contract and reference")

    compile_parser = subparsers.add_parser("compile", help="Compile one metric query")
    compile_parser.add_argument("--metric", required=True)
    compile_parser.add_argument(
        "--dimension",
        action="append",
        default=[],
        help="Repeat for each requested dimension",
    )
    compile_parser.add_argument("--grain", required=True)
    compile_parser.add_argument("--start", required=True)
    compile_parser.add_argument("--end", required=True)

    lineage_parser = subparsers.add_parser("lineage", help="Render the lineage graph")
    lineage_parser.add_argument("--format", choices=("json", "mermaid"), default="json")

    impact_parser = subparsers.add_parser(
        "impact", help="List all downstream nodes for one lineage node"
    )
    impact_parser.add_argument("--node", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    catalog = Catalog.load(args.catalog)

    if args.command == "validate":
        issues = validate_catalog(catalog)
        result = {
            "catalog": catalog.name,
            "valid": not issues,
            "issue_count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
            "synthetic": catalog.synthetic,
            "production_deployment": catalog.production_deployment,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not issues else 1

    if args.command == "compile":
        request = QueryRequest(
            metric=args.metric,
            dimensions=tuple(args.dimension),
            grain=args.grain,
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
        )
        print(SqlCompiler(catalog).compile(request))
        return 0

    graph = LineageGraph(catalog)
    if args.command == "lineage":
        if args.format == "mermaid":
            print(graph.to_mermaid())
        else:
            print(json.dumps(graph.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "impact":
        impacted = graph.impact(args.node)
        print(
            json.dumps(
                {
                    "source": args.node,
                    "impacted": list(impacted),
                    "impact_count": len(impacted),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    raise RuntimeError(f"unsupported command: {args.command}")  # pragma: no cover

