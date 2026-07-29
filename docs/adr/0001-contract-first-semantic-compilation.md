# ADR 0001: Contract-first deterministic metric compilation

- **Status:** Accepted for this synthetic demo
- **Date:** 2026-07-28
- **Scope:** Offline portfolio reference, not a production semantic service

## Context

Metric inconsistency commonly enters through implicit grain, ad hoc SQL, unrestricted
dimensions, and joins whose cardinality is not modeled. A dashboard label alone
cannot establish a trustworthy definition.

This demo needs to make the semantic contract auditable without requiring a
warehouse, vendor framework, or network access.

## Decision

1. Store model, grain, dimension, measure, metric, ownership, and certification
   metadata in one versioned catalog.
2. Validate the entire catalog before any query compilation.
3. Treat dimensions and time grains as an explicit metric allow-list.
4. Support simple aggregates and same-model ratios only.
5. Restrict demo expressions to single validated SQL identifiers and relations to
   two- or three-part identifiers.
6. Parse date bounds into typed values before deterministic SQL rendering.
7. Build lineage from contract references and use graph traversal for impact analysis.
8. Enforce `synthetic=true` and `production_deployment=false` as catalog invariants.

## Consequences

### Positive

- The compiler fails before emitting ambiguous or unapproved queries.
- SQL output is stable enough for code review, caching, and snapshot comparison.
- Metric-to-measure and metric-to-dimension impact is inspectable.
- The repository remains runnable offline.

### Negative

- Rich SQL expressions, filters, calendars, and dialect-specific behavior are omitted.
- Single-model metrics avoid cross-model fanout rather than modeling it.
- Static JSON lacks an approval workflow and runtime access enforcement.
- Compiled SQL is unverified against a real engine.

## Alternatives considered

### Accept arbitrary SQL metric expressions

Rejected because string validation is not a SQL parser and arbitrary fragments
would undermine the compiler safety boundary.

### Permit every model dimension by default

Rejected. It increases cardinality, cost, and privacy risk and makes semantic
compatibility implicit.

### Add joins immediately

Deferred until relationships can declare join keys, direction, cardinality,
temporal semantics, and fanout protections. A plausible-looking join compiler
without those contracts would be misleading.

### Execute against an embedded database

Not required for the initial objective. Compiler and governance behavior can be
tested offline. Engine conformance fixtures are a production follow-up.

## Production follow-up

- Version every contract and expose compatibility/diff checks.
- Add relationship contracts with one-to-one/one-to-many enforcement.
- Compile through a SQL AST and test supported warehouse dialects.
- Separate definition approval from query authorization.
- Add row/column policies and privacy classification propagation.
- Reconcile certified metrics against controlled reference queries and datasets.
- Emit query, catalog version, owner, and certification telemetry.

