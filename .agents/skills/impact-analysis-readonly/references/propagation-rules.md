# Change propagation rules

## Core distinction

A dependency says that two assets are related. An impact says that the proposed semantic delta can travel across that relation and change an observable outcome. Record both the edge and the propagation rationale.

## Canonical relation types

- Code: `calls`, `implements`, `extends`, `injects`, `loads-dynamically`, `configures`.
- Data: `reads`, `writes`, `derives`, `maps`, `filters`, `aggregates`, `persists`.
- Contract: `produces`, `consumes`, `serializes`, `deserializes`, `validates`.
- Batch: `scheduled-before`, `scheduled-after`, `triggers`, `waits-for`, `shares-cutoff`.
- Traceability: `implements-requirement`, `verified-by`, `governed-by`, `operated-by`.

## Expansion directions

For every seed, consider both:

- forward/downstream propagation: consumers, callers, derived data, reports, tests, operations;
- backward/upstream invalidation: prerequisites, assumed schema, business rules, data availability, security controls.

Do not stop at a repository or team boundary. Record it as an external frontier and assign an owner.

## Rules by semantic delta

| Change kind | Required edge expansion | Common stop mistakes |
|---|---|---|
| Field remove or rename | producers, serializers, consumers, mappings, validators, positional parsers, tests, reports | Stopping after compile references; ignoring files, SQL strings, and external consumers |
| Type, precision, scale, nullability | mappings, casts, validation, persistence, aggregation, serialization, comparison and rounding | Assuming an additive DDL change is behaviorally compatible |
| Field addition | positional readers, fixed-width layouts, `SELECT *`, schema validation, snapshots and exports | Treating every addition as non-breaking |
| Calculation or business rule | callers, stored outputs, aggregates, reconciliations, reports, limits, regulatory results and backfills | Following code callers but not data already materialized |
| Table or view change | SQL readers/writers, procedures, triggers, synonyms, lineage, jobs, reports, grants and policies | Trusting one catalog despite dynamic SQL or external objects |
| Schedule or cutoff change | predecessors, successors, calendars, data-ready assumptions, retries, restarts, SLAs and manual operations | Checking only the edited job |
| Configuration default | all profiles, overrides, deployment environments, conditional code paths and monitoring | Reading the default without resolved environment values |
| Dependency upgrade | direct API usage, transitive dependency resolution, runtime/JDK compatibility, configuration, serialization and security advisories | Inspecting only the declared dependency version |
| Authorization or policy change | identities, service accounts, roles, callers, data paths, audit logs and failure handling | Treating successful compile as security compatibility |

## Frontier termination

An expansion frontier may stop only with one of these recorded reasons:

- `semantic_terminal`: the target cannot propagate the specified change further, with rationale;
- `verified_isolation`: an adapter or contract absorbs the delta, with tests or structural evidence;
- `explicit_scope_boundary`: excluded by an authorized scope decision, not because it is inconvenient;
- `external_boundary`: another owner or system must confirm it;
- `unresolved_dynamic_boundary`: reflection, generated code, dynamic SQL, runtime routing, or manual behavior cannot be resolved;
- `duplicate_path`: the same node and semantic state were already expanded.

`external_boundary` and `unresolved_dynamic_boundary` remain open frontiers until confirmed or accepted as unknown. They cannot support complete no-impact analysis.

## Controlling false positives

- Deduplicate by stable asset ID, not display name.
- Record direct and transitive impacts separately.
- Do not propagate through an edge when the target does not observe the changed property; record the stop rationale.
- Use runtime frequency only for prioritization, not for removing structurally valid paths.
- Treat historical co-change as weak candidate evidence, never as a causal edge by itself.
