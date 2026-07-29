# Contributing

Keep every example synthetic and every capability claim reproducible.

For semantic changes:

1. update the contract and its description;
2. run downstream impact analysis;
3. add or update tests for validation and generated SQL;
4. document any compatibility break;
5. run `make check` and `make demo`.

Do not add credentials, real customer definitions, production claims, or arbitrary
SQL fragments. A relationship feature must define cardinality and fanout behavior
before it can be accepted.

