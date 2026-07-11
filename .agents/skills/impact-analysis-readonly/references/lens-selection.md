# Lens selection and assurance levels

## Purpose

Select the minimum sufficient investigation scope without silently omitting a relevant surface. Every analysis must contain one `lensCoverage` entry for each known lens.

## Assurance levels

| Level | Use | Permitted conclusion |
|---|---|---|
| `triage` | Rapidly identify likely scope and missing sources | `impacts_identified`, `inconclusive`, or escalation; never `no_impact_confirmed` |
| `standard` | Normal pre-change analysis with all applicable lenses | Any conclusion if the completeness gate passes |
| `high_assurance` | Breaking contracts, shared assets, security, regulated calculations, destructive data changes, critical schedules, or multi-capability changes | Any conclusion after independent evidence and human review requirements are met |

Escalate to `high_assurance` when any of the following applies:

- a field, endpoint, topic, table, or file contract is removed, renamed, narrowed, or changes meaning;
- a regulatory, accounting, risk, valuation, limit, rounding, currency, or date rule changes;
- a shared library, platform capability, authentication mechanism, permission, masking policy, or audit control changes;
- data is deleted, backfilled, recomputed, re-keyed, or migrated;
- a cutoff, business date, critical-path schedule, restart rule, or recovery behavior changes;
- more than one capability or external organization is potentially affected;
- evidence conflicts or the current catalog is incomplete.

## Known lenses

| Lens | Inspect | Typical evidence |
|---|---|---|
| `business` | Requirements, domain rules, regulation, acceptance criteria | Approved specifications, source regulations, owner confirmation |
| `code` | Symbols, callers, data flow, inheritance, DI, reflection, generated code | Source at commit, language-aware references, call/data-flow query |
| `configuration` | Profiles, flags, environment variables, build and runtime settings | Versioned configuration, deployment descriptors, resolved build data |
| `data` | Tables, columns, views, procedures, triggers, lineage, semantics | SQL definitions, catalogs, dbt manifest, Snowflake/Oracle metadata |
| `contract` | API, file, message, schema, producer and consumer obligations | Versioned contract, schema diff, consumer inventory |
| `batch` | Jobs, steps, predecessor/successor, calendar, restart and cutoff | Scheduler export, Spring Batch definition, execution metadata |
| `runtime` | Observed calls, queries, job executions, volumes and errors | Traces, logs, access history, job history with observation window |
| `test` | Requirement, code, contract and job coverage | Test source, test reports, coverage data, trace links |
| `operations` | Monitoring, alerting, runbooks, recovery, SLA and capacity | Runbooks, alerts, dashboards, incident records |
| `security` | Identity, authorization, secrets, sensitive data, audit controls | Policy definitions, threat model, access and masking policies |
| `manual` | EUCs, reconciliations, manual reports and undocumented coordination | Owner-confirmed procedure, controlled inventory, ticket history |

## Change-kind selection matrix

`R` means required by default; `C` means conditional; `-` means normally not required but still needs a `not_applicable` reason.

| Change kind | business | code | configuration | data | contract | batch | runtime | test | operations | security | manual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Business or regulatory rule | R | R | C | R | C | C | C | R | R | C | C |
| Java implementation | C | R | R | C | C | C | C | R | C | C | - |
| Shared library or dependency | C | R | R | C | C | C | R | R | R | R | - |
| Table, column, or data semantics | R | R | C | R | R | R | R | R | R | C | R |
| API, file, or message contract | R | R | C | R | R | C | R | R | R | R | C |
| Job, schedule, or cutoff | R | C | R | R | C | R | R | R | R | C | R |
| Authentication or authorization | C | R | R | C | R | C | R | R | R | R | C |
| Documentation-only correction | R | C | - | C | C | - | - | R | - | - | - |

Adjust the matrix only with a recorded rationale. A missing source does not make a lens non-applicable.

## Lens completion rules

- `completed`: the required searches and cross-checks were performed; include `evidenceRefs`.
- `not_applicable`: the lens cannot carry or observe the specified change; include a concrete reason.
- `blocked`: the lens is relevant but unavailable; include reason, owner, and due date.

Any required `blocked` lens forces completeness to `blocked` or `partial` and forbids `no_impact_confirmed`.
