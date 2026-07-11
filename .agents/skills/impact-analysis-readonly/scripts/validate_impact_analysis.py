#!/usr/bin/env python3
"""Validate a structured impact-analysis artifact without modifying it."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - environment diagnostic
    print("ERROR: PyYAML is required. Install tools/requirements.txt", file=sys.stderr)
    raise SystemExit(2)


KNOWN_LENSES = {
    "business",
    "code",
    "configuration",
    "data",
    "contract",
    "batch",
    "runtime",
    "test",
    "operations",
    "security",
    "manual",
}
EVIDENCE_CLASSES = {"declaration", "structural", "runtime", "historical", "human"}
IMPACT_OUTCOMES = {
    "impacts_identified",
    "no_impact_confirmed",
    "inconclusive",
    "external_escalation_required",
}
INCOMPLETE_OUTCOMES = {"inconclusive", "external_escalation_required"}
ID_PATTERNS = {
    "changeSeeds": re.compile(r"^CHG-[0-9]{3,}$"),
    "evidence": re.compile(r"^EV-[0-9]{3,}$"),
    "nodes": re.compile(r"^NODE-[A-Za-z0-9_.:-]+$"),
    "edges": re.compile(r"^EDGE-[0-9]{3,}$"),
    "impacts": re.compile(r"^IMP-[0-9]{3,}$"),
}


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def index_by_id(items: Iterable[Any], path: str, result: Validation) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(items):
        if not isinstance(item, dict):
            result.error(f"{path}[{position}] must be a mapping")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            result.error(f"{path}[{position}].id is required")
            continue
        if item_id in indexed:
            result.error(f"duplicate ID {item_id} in {path}")
        indexed[item_id] = item
    return indexed


def require_keys(mapping: Any, keys: Iterable[str], path: str, result: Validation) -> None:
    if not isinstance(mapping, dict):
        result.error(f"{path} must be a mapping")
        return
    for key in keys:
        if key not in mapping:
            result.error(f"{path}.{key} is required")


def check_refs(refs: Any, valid: set[str], path: str, result: Validation, *, nonempty: bool = False) -> None:
    if not isinstance(refs, list):
        result.error(f"{path} must be a list")
        return
    if nonempty and not refs:
        result.error(f"{path} must not be empty")
    for ref in refs:
        if ref not in valid:
            result.error(f"{path} references unknown ID {ref!r}")


def validate_document(doc: Any) -> Validation:
    result = Validation()
    if not isinstance(doc, dict):
        result.error("document root must be a mapping")
        return result

    require_keys(
        doc,
        [
            "schemaVersion",
            "investigation",
            "baseline",
            "changeSeeds",
            "scope",
            "lensCoverage",
            "evidence",
            "graph",
            "impacts",
            "findings",
            "requiredTests",
            "recommendedFollowUps",
            "completeness",
            "conclusion",
        ],
        "root",
        result,
    )

    investigation = doc.get("investigation", {})
    require_keys(investigation, ["id", "title", "mode", "assuranceLevel"], "investigation", result)
    if investigation.get("mode") not in {"read_only", "investigation_only"}:
        result.error("investigation.mode must be read_only or investigation_only")
    assurance = investigation.get("assuranceLevel")
    if assurance not in {"triage", "standard", "high_assurance"}:
        result.error("investigation.assuranceLevel has an invalid value")

    baseline = doc.get("baseline", {})
    require_keys(baseline, ["repositoryCommit", "branch", "observedAt", "sources"], "baseline", result)
    commit = baseline.get("repositoryCommit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit):
        result.error("baseline.repositoryCommit must be a 7-64 character hexadecimal commit SHA")
    if not as_list(baseline.get("sources")):
        result.error("baseline.sources must contain at least one pinned source")
    for i, source in enumerate(as_list(baseline.get("sources"))):
        require_keys(source, ["kind", "snapshot", "capturedAt"], f"baseline.sources[{i}]", result)

    seed_index = index_by_id(as_list(doc.get("changeSeeds")), "changeSeeds", result)
    evidence_index = index_by_id(as_list(doc.get("evidence")), "evidence", result)
    graph = doc.get("graph", {})
    require_keys(graph, ["nodes", "edges"], "graph", result)
    node_index = index_by_id(as_list(graph.get("nodes")), "graph.nodes", result)
    edge_index = index_by_id(as_list(graph.get("edges")), "graph.edges", result)
    impact_index = index_by_id(as_list(doc.get("impacts")), "impacts", result)

    for collection, indexed in (
        ("changeSeeds", seed_index),
        ("evidence", evidence_index),
        ("nodes", node_index),
        ("edges", edge_index),
        ("impacts", impact_index),
    ):
        pattern = ID_PATTERNS[collection]
        for item_id in indexed:
            if not pattern.fullmatch(item_id):
                result.error(f"{collection} ID {item_id!r} does not match {pattern.pattern}")

    if not seed_index:
        result.error("changeSeeds must contain at least one seed")
    for seed_id, seed in seed_index.items():
        require_keys(seed, ["kind", "target"], f"changeSeed[{seed_id}]", result)

    scope = doc.get("scope", {})
    require_keys(scope, ["included", "excluded"], "scope", result)
    if not isinstance(scope.get("included"), list):
        result.error("scope.included must be a list")
    if not isinstance(scope.get("excluded"), list):
        result.error("scope.excluded must be a list")
    for i, exclusion in enumerate(as_list(scope.get("excluded"))):
        require_keys(exclusion, ["target", "reason"], f"scope.excluded[{i}]", result)

    for evidence_id, evidence in evidence_index.items():
        require_keys(
            evidence,
            ["class", "source", "locator", "snapshot", "observedAt", "method", "limitations"],
            f"evidence[{evidence_id}]",
            result,
        )
        if evidence.get("class") not in EVIDENCE_CLASSES:
            result.error(f"evidence[{evidence_id}].class is invalid")

    for node_id, node in node_index.items():
        require_keys(node, ["type", "label"], f"node[{node_id}]", result)

    for edge_id, edge in edge_index.items():
        require_keys(edge, ["source", "target", "relation", "evidenceRefs", "confidence"], f"edge[{edge_id}]", result)
        if edge.get("source") not in node_index:
            result.error(f"edge[{edge_id}].source references unknown node {edge.get('source')!r}")
        if edge.get("target") not in node_index:
            result.error(f"edge[{edge_id}].target references unknown node {edge.get('target')!r}")
        check_refs(edge.get("evidenceRefs"), set(evidence_index), f"edge[{edge_id}].evidenceRefs", result, nonempty=True)
        if edge.get("confidence") not in {"high", "medium", "low"}:
            result.error(f"edge[{edge_id}].confidence is invalid")

    for impact_id, impact in impact_index.items():
        require_keys(
            impact,
            ["seedRefs", "pathEdgeRefs", "target", "status", "consequence", "severity", "confidence", "evidenceRefs"],
            f"impact[{impact_id}]",
            result,
        )
        check_refs(impact.get("seedRefs"), set(seed_index), f"impact[{impact_id}].seedRefs", result, nonempty=True)
        check_refs(impact.get("pathEdgeRefs"), set(edge_index), f"impact[{impact_id}].pathEdgeRefs", result, nonempty=True)
        check_refs(impact.get("evidenceRefs"), set(evidence_index), f"impact[{impact_id}].evidenceRefs", result, nonempty=True)
        if impact.get("status") not in {"confirmed", "potential", "unknown"}:
            result.error(f"impact[{impact_id}].status is invalid")
        if impact.get("severity") not in {"critical", "high", "medium", "low"}:
            result.error(f"impact[{impact_id}].severity is invalid")
        if impact.get("confidence") not in {"high", "medium", "low"}:
            result.error(f"impact[{impact_id}].confidence is invalid")

        if assurance == "high_assurance" and impact.get("severity") in {"critical", "high"}:
            refs = set(as_list(impact.get("evidenceRefs")))
            for edge_ref in as_list(impact.get("pathEdgeRefs")):
                refs.update(as_list(edge_index.get(edge_ref, {}).get("evidenceRefs")))
            classes = {evidence_index[ref].get("class") for ref in refs if ref in evidence_index}
            if len(classes) < 2:
                result.error(
                    f"impact[{impact_id}] is {impact.get('severity')} in high_assurance analysis but has fewer than two evidence classes"
                )

    lenses = as_list(doc.get("lensCoverage"))
    lens_names = [lens.get("lens") for lens in lenses if isinstance(lens, dict)]
    duplicates = [name for name, count in Counter(lens_names).items() if count > 1]
    if duplicates:
        result.error(f"duplicate lensCoverage entries: {', '.join(sorted(map(str, duplicates)))}")
    missing_lenses = KNOWN_LENSES - set(lens_names)
    extra_lenses = set(lens_names) - KNOWN_LENSES
    if missing_lenses:
        result.error(f"missing lensCoverage entries: {', '.join(sorted(missing_lenses))}")
    if extra_lenses:
        result.error(f"unknown lensCoverage entries: {', '.join(sorted(map(str, extra_lenses)))}")

    required_blocked = False
    required_incomplete = False
    for i, lens in enumerate(lenses):
        require_keys(lens, ["lens", "required", "status", "evidenceRefs", "reason"], f"lensCoverage[{i}]", result)
        status = lens.get("status")
        required = lens.get("required") is True
        if status not in {"completed", "not_applicable", "blocked"}:
            result.error(f"lensCoverage[{i}].status is invalid")
        check_refs(lens.get("evidenceRefs"), set(evidence_index), f"lensCoverage[{i}].evidenceRefs", result)
        if status == "completed" and required and not as_list(lens.get("evidenceRefs")):
            result.error(f"required completed lens {lens.get('lens')} needs evidenceRefs")
        if status == "not_applicable" and not lens.get("reason"):
            result.error(f"not_applicable lens {lens.get('lens')} needs a reason")
        if status == "blocked":
            require_keys(lens, ["owner", "dueAt"], f"lensCoverage[{i}]", result)
            if required:
                required_blocked = True
        if required and status != "completed":
            required_incomplete = True

    findings = doc.get("findings", {})
    require_keys(findings, ["facts", "assumptions", "unknowns", "conflicts"], "findings", result)
    for i, fact in enumerate(as_list(findings.get("facts"))):
        require_keys(fact, ["id", "statement", "evidenceRefs"], f"findings.facts[{i}]", result)
        check_refs(fact.get("evidenceRefs"), set(evidence_index), f"findings.facts[{i}].evidenceRefs", result, nonempty=True)
    for i, assumption in enumerate(as_list(findings.get("assumptions"))):
        require_keys(assumption, ["id", "statement", "needsValidation", "validationOwner"], f"findings.assumptions[{i}]", result)
        if assumption.get("needsValidation") is not True:
            result.error(f"findings.assumptions[{i}].needsValidation must be true")
    for i, unknown in enumerate(as_list(findings.get("unknowns"))):
        require_keys(unknown, ["id", "statement", "owner", "dueAt"], f"findings.unknowns[{i}]", result)
    for i, conflict in enumerate(as_list(findings.get("conflicts"))):
        require_keys(conflict, ["id", "statement", "evidenceRefs", "owner"], f"findings.conflicts[{i}]", result)
        check_refs(conflict.get("evidenceRefs"), set(evidence_index), f"findings.conflicts[{i}].evidenceRefs", result, nonempty=True)

    if not isinstance(doc.get("requiredTests"), list):
        result.error("requiredTests must be a list")
    if not isinstance(doc.get("recommendedFollowUps"), list):
        result.error("recommendedFollowUps must be a list")

    completeness = doc.get("completeness", {})
    require_keys(completeness, ["status", "openFrontiers", "unresolvedConflicts"], "completeness", result)
    completeness_status = completeness.get("status")
    if completeness_status not in {"complete", "partial", "blocked"}:
        result.error("completeness.status is invalid")
    if completeness_status == "complete":
        if required_incomplete:
            result.error("completeness cannot be complete while a required lens is incomplete")
        if as_list(completeness.get("openFrontiers")):
            result.error("completeness cannot be complete with openFrontiers")
        if as_list(completeness.get("unresolvedConflicts")):
            result.error("completeness cannot be complete with unresolvedConflicts")
        if as_list(findings.get("conflicts")):
            result.error("completeness cannot be complete while findings.conflicts is non-empty")
    if required_blocked and completeness_status != "blocked":
        result.warn("a required lens is blocked; completeness.status should normally be blocked")

    conclusion = doc.get("conclusion", {})
    require_keys(conclusion, ["outcome", "summary", "confidence"], "conclusion", result)
    outcome = conclusion.get("outcome")
    if outcome not in IMPACT_OUTCOMES:
        result.error("conclusion.outcome is invalid")
    if conclusion.get("confidence") not in {"high", "medium", "low"}:
        result.error("conclusion.confidence is invalid")
    if completeness_status != "complete" and outcome not in INCOMPLETE_OUTCOMES:
        result.error("an incomplete analysis must conclude inconclusive or external_escalation_required")
    if outcome == "impacts_identified" and not impact_index:
        result.error("impacts_identified requires at least one impact")

    if outcome == "no_impact_confirmed":
        if assurance == "triage":
            result.error("triage analysis cannot conclude no_impact_confirmed")
        if completeness_status != "complete":
            result.error("no_impact_confirmed requires completeness.status=complete")
        if impact_index:
            result.error("no_impact_confirmed cannot contain confirmed, potential, or unknown impacts")
        if as_list(findings.get("assumptions")):
            result.error("no_impact_confirmed cannot contain unvalidated assumptions")
        if as_list(findings.get("unknowns")):
            result.error("no_impact_confirmed cannot contain unknowns")
        if as_list(findings.get("conflicts")):
            result.error("no_impact_confirmed cannot contain conflicts")
        if required_incomplete or required_blocked:
            result.error("no_impact_confirmed requires every required lens to be completed")
        if as_list(completeness.get("openFrontiers")) or as_list(completeness.get("unresolvedConflicts")):
            result.error("no_impact_confirmed cannot have open frontiers or unresolved conflicts")
        evidence_classes = {item.get("class") for item in evidence_index.values()}
        minimum_classes = 2 if assurance == "high_assurance" else 1
        if len(evidence_classes) < minimum_classes:
            result.error(f"no_impact_confirmed at {assurance} requires at least {minimum_classes} evidence class(es)")
        if not evidence_classes.intersection({"declaration", "structural"}):
            result.error("no_impact_confirmed requires declaration or structural evidence; historical/runtime evidence alone is insufficient")
        if assurance == "high_assurance" and "human" not in evidence_classes:
            result.error("high_assurance no_impact_confirmed requires human owner-review evidence")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path, help="Path to impact analysis YAML")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with args.analysis.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read {args.analysis}: {exc}", file=sys.stderr)
        return 2

    result = validate_document(document)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    failed = bool(result.errors or (args.strict and result.warnings))
    if failed:
        print(f"INVALID: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
        return 1
    print(f"VALID: 0 errors, {len(result.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
