# Evidence, confidence, completeness, and no-impact gate

## Evidence classes

| Class | Examples | Principal limitation |
|---|---|---|
| `declaration` | Approved requirement, contract, schema, scheduler definition | May differ from deployed behavior |
| `structural` | Source, symbol reference, call/data-flow graph, database dependency, dbt DAG | Dynamic behavior may be unresolved |
| `runtime` | Trace, log, query/access history, job execution, coverage | Limited to the observation window and exercised paths |
| `historical` | Git history, incident, prior investigation | May be stale and does not prove current causality |
| `human` | Owner or steward confirmation | Requires named authority, timestamp, and precise scope |

Every evidence item records source, locator, pinned snapshot or window, observation time, method, and limitations.

## Findings

- A `fact` is directly supported by cited evidence at the pinned baseline.
- An `assumption` states a provisional interpretation and includes a validation owner.
- An `unknown` states what cannot be established, its owner, and due date.
- A `conflict` preserves inconsistent sources and identifies the decision owner.
- An `impact` links a change seed to a consequence through evidence-backed graph edges.

Do not promote an assumption to fact because it appears likely.

## Confidence

- `high`: independent sources agree and material dynamic boundaries are resolved.
- `medium`: direct evidence exists but an independent source or owner confirmation is missing.
- `low`: only weak or historical evidence exists, or material conflict remains.

Confidence applies to a statement or impact. It does not indicate investigation coverage.

## Completeness

- `complete`: all required lenses completed, all frontiers closed, and material conflicts resolved.
- `partial`: useful analysis exists but at least one relevant path, source, or confirmation remains.
- `blocked`: a required source, permission, system, or owner prevents material analysis.

Do not use percentages unless the denominator is a controlled inventory. `90% complete` is meaningless when unknown assets may exist.

## Strict no-impact gate

`no_impact_confirmed` is a positive, evidence-backed claim. It requires all of the following:

1. assurance level is `standard` or `high_assurance`, not `triage`;
2. baseline commit and source snapshots are pinned;
3. every known lens is represented;
4. every required lens is `completed` with evidence;
5. no required lens is `blocked`;
6. every change seed was resolved and expanded using applicable propagation rules;
7. no confirmed, potential, or unknown impact remains;
8. `openFrontiers` and `unresolvedConflicts` are empty;
9. aliases, legacy names, serialized names, physical names, and dynamic boundaries were considered;
10. runtime non-observation is not used as the sole proof;
11. external consumers are confirmed or isolated through a versioned boundary;
12. high-assurance analysis has at least two independent evidence classes and the required human review.

If any condition fails, return `inconclusive` or `external_escalation_required` and create a recommended follow-up.

## Prior investigation reuse

A prior investigation may provide aliases, candidate assets, known owners, useful queries, and previously observed risks. It must not supply current facts unless its evidence is re-executed or independently shown to match the current baseline.

Record reused items as historical evidence and cite the current evidence that revalidated them.
