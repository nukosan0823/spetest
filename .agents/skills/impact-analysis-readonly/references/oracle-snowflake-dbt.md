# Oracle, Snowflake, and dbt investigation playbook

## General data questions

For each changed table or column determine:

- semantic meaning and grain;
- producers and write modes;
- direct and transitive consumers;
- filters, joins, casts, rounding, defaults, null handling, and aggregation;
- materialized copies, extracts, reports, EUCs, and reconciliation processes;
- historical-data or backfill implications;
- privileges, row access, masking, tags, retention, and audit effects.

Do not equate DDL compatibility with business compatibility.

## Oracle

Use dictionary views as structural evidence, subject to privileges and feature coverage:

```sql
SELECT owner, name, type, referenced_owner, referenced_name, referenced_type
FROM all_dependencies
WHERE referenced_name = UPPER(:object_name);
```

Also inspect:

- `ALL_SOURCE` for PL/SQL and dynamic SQL fragments;
- views, materialized views, triggers, packages, functions, procedures, synonyms, sequences, and database links;
- constraints, indexes, grants, VPD/FGA/redaction policies where relevant;
- application SQL in Java, XML, scripts, scheduler commands, and external ETL tools.

`ALL_DEPENDENCIES` cannot replace source search for application-built or dynamic SQL. Record the connected schema, accessible owner range, database version, and observation time.

## Snowflake

Use complementary evidence:

- `ACCOUNT_USAGE.OBJECT_DEPENDENCIES` for supported structural relationships;
- Snowsight object and column lineage;
- `ACCOUNT_USAGE.ACCESS_HISTORY` for observed direct/base object and column access;
- task, stream, dynamic-table, view, UDF, procedure, policy, and sharing definitions;
- external ETL and consumer catalogs.

Record known limitations, including session-dependent resolution, object references hidden inside functions, external objects, data sharing boundaries, dropped objects, access-history retention, and periods with no execution.

Runtime absence means no observation in the selected window, not no consumer.

## dbt

Pin both the current and comparison `manifest.json` artifacts. Inspect:

- `nodes`, `sources`, `exposures`, `metrics`, `macros`, `parent_map`, and `child_map`;
- model contracts and column definitions;
- disabled nodes and environment-dependent variables;
- macros that change generated SQL;
- downstream models, tests, and exposures.

Useful read-only commands include:

```bash
dbt ls --select "state:modified+" --state path/to/previous-artifacts
dbt ls --select "model_name+"
dbt parse
```

Keep the previous manifest outside the current target directory because parsing can overwrite `target/manifest.json`.

## Cross-system closure

Data lineage inside one platform is not enterprise lineage. Continue from database objects to application jobs, file transfers, APIs, BI tools, reports, external consumers, and manual reconciliations. An unavailable consumer remains an external frontier.
