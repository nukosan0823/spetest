# Java, Spring, and Maven investigation playbook

## Search order

1. Pin the repository commit and identify modules and build roots.
2. Search exact class, method, field, annotation, bean, property, table, column, endpoint, topic, and job names.
3. Search aliases, constants, serialized names, SQL fragments, legacy names, and configuration keys.
4. Use language-aware symbol references and type hierarchy when available.
5. Trace callers and callees, then trace values across readers, processors, writers, controllers, services, repositories, mappers, and serializers.
6. Inspect tests and runtime evidence independently.

Use `rg` for candidate discovery. Prefer structural tooling for overloaded methods, interfaces, inheritance, and cross-module references.

## Spring-specific surfaces

Inspect:

- component scanning and conditional beans;
- `@Configuration`, `@Bean`, `@Profile`, `@Conditional*`, and property binding;
- dependency injection by interface, qualifier, primary bean, and collection;
- controller routes, filters, interceptors, exception handlers, and validation;
- Spring Data repository methods, native queries, specifications, and converters;
- Jackson/JAXB annotations, custom serializers, field aliases, and unknown-field handling;
- scheduled methods, event listeners, message listeners, and transaction boundaries;
- reflection, `Class.forName`, `ServiceLoader`, expression language, and configuration-selected implementations;
- generated sources and annotation processors.

## Maven and dependency changes

Read-only commands commonly include:

```bash
mvn -q -DskipTests dependency:tree
mvn -q help:effective-pom
mvn -q -DskipTests test-compile
```

Do not assume a POM declaration represents the resolved dependency. Record the resolved tree and active profiles. Check dependency management, exclusions, optional scope, plugins, BOMs, shaded artifacts, and runtime container-provided libraries.

For broad or high-assurance Java analysis, use a call-graph or data-flow engine such as CodeQL when available. Record model gaps for application frameworks, reflection, and generated code.

## Tests and coverage

Map affected symbols and behaviors to:

- JUnit unit and parameterized tests;
- Spring slice and context tests;
- integration and contract tests;
- batch restart and reconciliation tests;
- serialized compatibility fixtures.

Coverage proves that a test executed a probe in a particular run; it does not prove the behavior is asserted or that unexecuted paths are unused. Treat coverage as runtime evidence with a stated test set and commit.

## Required output notes

For every Java impact path, record the fully qualified symbol where possible, module, source path, commit, relation type, and whether dispatch is statically resolved, framework-resolved, or dynamic.
