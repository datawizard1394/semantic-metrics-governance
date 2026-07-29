# Semantic catalog change runbook

> This runbook describes a production-minded review process for the synthetic
> demo. No production metric registry or warehouse is connected.

## Safe change sequence

1. Identify the accountable metric and model owners.
2. State whether the change alters definition, grain, allowed dimensions, time
   behavior, or only documentation.
3. Run catalog validation and the full test suite.
4. Run impact analysis from every changed model, dimension, or measure node.
5. Compare compiled SQL before and after for representative requests.
6. For a definition change, create a new version or parallel metric; do not silently
   rewrite a certified historical meaning.
7. Announce affected consumers, migration date, and rollback plan.
8. Promote certification only after reconciliation evidence and steward approval.

## Commands

```bash
make check

PYTHONPATH=src python -m semantic_metrics \
  --catalog examples/catalog.json validate

PYTHONPATH=src python -m semantic_metrics \
  --catalog examples/catalog.json impact \
  --node measure.orders.gross_revenue_amount
```

## Review gates

- [ ] Description defines inclusions, exclusions, unit, and aggregation
- [ ] Primary grain is unchanged or explicitly migrated
- [ ] Owner is accountable and available
- [ ] Dimensions are necessary, safe, and cardinality-aware
- [ ] Timezone, calendar, and late-arriving-data behavior is documented
- [ ] Ratio denominator handles zero
- [ ] Lineage impact has been reviewed
- [ ] Generated SQL diff matches the stated intent
- [ ] Downstream owners have a migration window
- [ ] Rollback or coexistence strategy is tested

## Incident: two consumers disagree

1. Capture catalog version, metric request, compiled SQL, time range, and dimensions.
2. Confirm both consumers used the same certification and catalog version.
3. Compare timezone, filters, grain, source freshness, and late-data cutoffs.
4. Reproduce with the smallest synthetic or approved reference fixture.
5. If the contract is ambiguous, downgrade certification and stop new adoption.
6. Correct via a versioned definition; preserve the old result for audit.

## Deprecation

Mark a metric `deprecated`, name its successor, inventory impacted nodes, and keep
both definitions during the migration window. Removal should be blocked while
known consumers remain.

## Production signals

Monitor validation failures, rejected query requests, compile latency, cache hit
rate, warehouse cost/latency, result reconciliation deltas, deprecated metric use,
and catalog versions observed by clients.

