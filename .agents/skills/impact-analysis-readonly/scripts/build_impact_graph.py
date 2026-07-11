#!/usr/bin/env python3
"""Render an impact-analysis graph to Mermaid or JSON on stdout."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment diagnostic
    print("ERROR: PyYAML is required. Install tools/requirements.txt", file=sys.stderr)
    raise SystemExit(2)


def safe_label(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ")
    text = text.replace('"', "'").replace("`", "'")
    for unsafe in ("[", "]", "{", "}", "|", "<", ">"):
        text = text.replace(unsafe, " ")
    return re.sub(r"\s+", " ", text).strip()


def mermaid_id(value: str, position: int) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not clean or clean[0].isdigit():
        clean = f"N_{clean}"
    return f"{clean}_{position}"


def load_graph(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    graph = document.get("graph", {}) if isinstance(document, dict) else {}
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("graph.nodes and graph.edges must be lists")
    return nodes, edges


def render_mermaid(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    ordered_nodes = sorted(nodes, key=lambda item: str(item.get("id", "")))
    ordered_edges = sorted(edges, key=lambda item: str(item.get("id", "")))
    aliases = {str(node.get("id")): mermaid_id(str(node.get("id")), i) for i, node in enumerate(ordered_nodes, 1)}
    lines = ["flowchart TD"]
    for node in ordered_nodes:
        node_id = str(node.get("id"))
        label = safe_label(node.get("label", node_id))
        node_type = safe_label(node.get("type", "asset"))
        lines.append(f'  {aliases[node_id]}["{label} ({node_type})"]')
    for edge in ordered_edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        if source not in aliases or target not in aliases:
            raise ValueError(f"edge {edge.get('id')} references an unknown node")
        relation = safe_label(edge.get("relation", "depends"))
        lines.append(f"  {aliases[source]} -->|{relation}| {aliases[target]}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path, help="Path to impact analysis YAML")
    parser.add_argument("--format", choices=("mermaid", "json"), default="mermaid")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        nodes, edges = load_graph(args.analysis)
        if args.format == "json":
            print(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_mermaid(nodes, edges))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
