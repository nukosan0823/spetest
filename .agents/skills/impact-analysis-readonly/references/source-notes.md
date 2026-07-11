# Method provenance and authoritative source notes

Read this file when reviewing why the method exists, validating product-specific limitations, or updating the Skill. Operational analysis must still use the versions actually deployed by the organization.

## Change impact and traceability

- Gentili, Çarka, and Falessi, *A Systematic Mapping Study on Impact Analysis* (ICSOFT 2024): characterizes impact-analysis sources and targets across requirements, design, code, and tests, and identifies under-studied late-to-early trace paths. <https://doi.org/10.5220/0012758200003753>
- Lelovic et al., *Change impact analysis in microservice systems: A systematic literature review* (Journal of Systems and Software, 2025): reports that many approaches measure only one impact aspect and highlights the need for broader effects and validation. <https://doi.org/10.1016/j.jss.2024.112241>
- Tian et al., *The Impact of Traceability on Software Maintenance and Evolution: A Mapping Study*: finds change management to be the most commonly supported maintenance activity while link quality and maintenance cost remain major challenges. <https://arxiv.org/abs/2108.02133>

## Agent Skill structure

- Agent Skills specification: standard front matter, progressive disclosure, and optional `scripts/`, `references/`, and `assets/`. <https://agentskills.io/specification>
- Agent Skills creator guidance: concise procedures, conditional references, explicit checklists, validation loops, and eval-driven iteration. <https://agentskills.io/skill-creation/best-practices>

## Code and dependency analysis

- CodeQL Java/Kotlin call graph: <https://codeql.github.com/docs/codeql-language-guides/navigating-the-call-graph/>
- CodeQL Java/Kotlin data flow: <https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-java/>
- GitHub dependency graph detection and known manifest/build-resolution boundaries: <https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph-data>

## Data and batch analysis

- Oracle `ALL_DEPENDENCIES`: <https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_DEPENDENCIES.html>
- Snowflake object dependencies and documented limitations: <https://docs.snowflake.com/en/user-guide/object-dependencies>
- Snowflake access history and column lineage: <https://docs.snowflake.com/en/user-guide/access-history>
- dbt manifest artifact, including `parent_map` and `child_map`: <https://docs.getdbt.com/reference/artifacts/manifest-json>
- dbt state selection and downstream selection behavior: <https://docs.getdbt.com/reference/node-selection/methods>
- Spring Batch metadata schema: <https://docs.spring.io/spring-batch/reference/schema-appendix.html>

## Security impact

- NIST SP 800-128 defines security impact analysis as part of documented configuration change control and calls for evaluation before approval plus assessment after implementation. <https://doi.org/10.6028/NIST.SP.800-128>

These sources justify a multi-artifact, multi-evidence method. They do not prove that a particular repository, catalog, or runtime source is complete.
