# Batch, scheduler, and contract investigation playbook

## Batch and orchestration

For every affected job inspect:

- trigger, calendar, business date, timezone, and cutoff;
- predecessor and successor dependencies, including negative or completion conditions;
- job and step parameters, late binding, partitioning, parallelism, and remote workers;
- input and output datasets, files, tables, topics, and control records;
- restartability, checkpoint, idempotency, skip/retry, compensation, rerun, and rollback;
- expected duration, critical path, resource contention, SLA, monitoring, and alerts;
- manual handoffs and reconciliation.

Compare the declared orchestration graph with a fresh scheduler export. A repository definition alone is not proof of the deployed schedule.

For Spring Batch, inspect Job/Step definitions and JobRepository execution metadata. History shows observed parameters, statuses, timings, and restarts; it does not prove all configured paths have run.

## Contract types

Treat these as contracts even when no formal schema exists:

- REST, SOAP, RPC, and internal service APIs;
- CSV, fixed-width, XML, JSON, Excel, and binary files;
- database tables/views shared across ownership boundaries;
- message topics, queues, event envelopes, headers, ordering, and delivery semantics;
- scheduler parameters, exit codes, completion files, and naming conventions.

## Compatibility checks

Check both producer and consumer behavior for:

- addition, removal, rename, reorder, type and precision changes;
- optional-to-required and required-to-optional changes;
- default and null semantics;
- enumeration expansion or contraction;
- timezone, encoding, locale, delimiter, quoting, and line-ending changes;
- unknown-field handling and positional parsing;
- version negotiation and mixed-version deployment windows;
- retry, duplicate, ordering, and idempotency semantics.

An additive field can still be breaking for fixed-width, positional, closed-schema, snapshot, or strict-validation consumers.

## Consumer verification

Derive known consumers from declared contracts, code, job I/O, data lineage, runtime observation, and owner inventories. Do not maintain a hand-written downstream list as the only source.

For external consumers record:

- organization and owner;
- contract/version they confirmed;
- confirmation timestamp and evidence reference;
- unconfirmed assumptions and due date.

Unconfirmed external consumers force `potential` or `unknown` impact unless a versioned isolation boundary is independently verified.
