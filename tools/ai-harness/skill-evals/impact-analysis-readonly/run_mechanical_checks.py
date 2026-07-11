#!/usr/bin/env python3
"""Run deterministic checks for the impact-analysis Skill package."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / ".agents/skills/impact-analysis-readonly"
VALIDATOR = SKILL / "scripts/validate_impact_analysis.py"
GRAPH = SKILL / "scripts/build_impact_graph.py"
FIXTURES = ROOT / "tools/ai-harness/skill-evals/impact-analysis-readonly/fixtures"


def run(command: list[str], expected: int = 0) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != expected:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise AssertionError(f"expected exit {expected}, got {completed.returncode}: {' '.join(command)}")


def validate_skill_frontmatter() -> None:
    skill_file = SKILL / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    if len(text.splitlines()) > 500:
        raise AssertionError("SKILL.md exceeds 500 lines")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise AssertionError("SKILL.md front matter is missing")
    frontmatter = yaml.safe_load(parts[1])
    if frontmatter.get("name") != SKILL.name:
        raise AssertionError("Skill name must match its directory")
    if not frontmatter.get("description"):
        raise AssertionError("Skill description is required")
    metadata = frontmatter.get("metadata", {})
    if not isinstance(metadata, dict) or any(not isinstance(value, str) for value in metadata.values()):
        raise AssertionError("Skill metadata must be a string-to-string mapping")


def parse_sources() -> None:
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for pattern in ("*.yml", "*.yaml"):
        for path in ROOT.rglob(pattern):
            yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    validate_skill_frontmatter()
    parse_sources()
    run([sys.executable, str(VALIDATOR), str(FIXTURES / "valid-analysis.yml"), "--strict"])
    run([sys.executable, str(VALIDATOR), str(FIXTURES / "invalid-no-impact.yml")], expected=1)
    run([sys.executable, str(GRAPH), str(FIXTURES / "valid-analysis.yml")])
    print("MECHANICAL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
