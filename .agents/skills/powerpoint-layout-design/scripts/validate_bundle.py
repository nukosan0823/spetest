#!/usr/bin/env python3
"""PowerPointレイアウト・デザインSkillの構造と安全性を検査する。"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import unicodedata
import zipfile
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/content-and-story.md",
    "references/design-system.md",
    "references/layout-catalog.md",
    "references/charts-tables-images.md",
    "references/template-and-engine.md",
    "references/visual-qa.md",
    "references/security-and-sources.md",
    "assets/design-tokens.json",
    "assets/layout-contracts.json",
    "assets/layout-registry.json",
    "assets/slide-spec.schema.json",
    "assets/source-manifest.json",
    "assets/reference-layouts.pptx",
    "assets/layout-preview.png",
    "evals/trigger-queries.json",
    "evals/output-cases.json",
    "evals/layout-selection-cases.json",
    "evals/example-slide-spec.json",
    "scripts/build_layout_assets.py",
    "scripts/build_reference_deck.mjs",
    "scripts/create_layout_preview.py",
    "scripts/normalize_reference_pptx.py",
    "scripts/validate_bundle.py",
    "scripts/check_japanese_font.py",
    "scripts/validate_slide_spec.py",
]

ALLOWED_TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".mjs"}
ALLOWED_SUFFIXES = ALLOWED_TEXT_SUFFIXES | {".pptx", ".png"}
FORBIDDEN_CONTROLS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\ufeff",
}
SUSPICIOUS_TEXT_PATTERNS = [
    (re.compile(r"<\s*script\b", re.IGNORECASE), "scriptタグ"),
    (re.compile(r"javascript\s*:", re.IGNORECASE), "javascript URL"),
    (re.compile(r"data\s*:\s*text/html", re.IGNORECASE), "HTML data URL"),
    (re.compile(r"[A-Za-z0-9+/]{1000,}={0,2}"), "長い符号化文字列"),
]
HTML_COMMENT_PATTERN = re.compile(r"<!--([\s\S]*?)-->", re.IGNORECASE)
PROMPT_INJECTION_PATTERNS = [
    (
        re.compile(
            r"\b(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior|above)"
            r"\s+(?:instructions?|messages?)\b",
            re.IGNORECASE,
        ),
        "上位指示を無視させる英語表現",
    ),
    (
        re.compile(r"\b(?:reveal|print|dump)\s+(?:the\s+)?system\s+prompt\b", re.IGNORECASE),
        "システムプロンプト取得表現",
    ),
    (
        re.compile(r"(?:以前|上位|これまで)の.{0,24}指示.{0,16}無視"),
        "上位指示を無視させる日本語表現",
    ),
    (
        re.compile(
            r"(?:curl|wget)\b[^\n|]{0,240}\|\s*(?:ba)?sh\b",
            re.IGNORECASE,
        ),
        "外部取得したシェルの直接実行",
    ),
    (
        re.compile(r"\bInvoke-Expression\b|\biex\s*\(", re.IGNORECASE),
        "PowerShellの動的実行",
    ),
]
INJECTION_EXEMPT_PATHS = {
    "references/security-and-sources.md",
    "evals/trigger-queries.json",
    "evals/output-cases.json",
    "scripts/validate_bundle.py",
}
URL_ALLOWED_PATHS = {
    "references/security-and-sources.md",
    "assets/source-manifest.json",
}
PROVENANCE_ONLY_TERMS = [
    re.compile(r"\bbaoyu-skills\b", re.IGNORECASE),
    re.compile(r"\bMCK\b", re.IGNORECASE),
]


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def load_json(path: Path, validation: Validation):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        validation.error(f"{path.relative_to(ROOT)}: JSONを読み込めません: {exc}")
        return None


def validate_required_files(validation: Validation) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            validation.error(f"必須ファイルがありません: {relative}")


def validate_file_inventory(validation: Validation) -> None:
    actual_files: set[str] = set()
    for path in sorted(ROOT.rglob("*")):
        if path.is_symlink():
            validation.error(f"シンボリックリンクは禁止です: {path.relative_to(ROOT)}")
            continue
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            actual_files.add(relative)
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                validation.error(f"許可されていない形式です: {relative}")
    unexpected = actual_files - set(REQUIRED_FILES)
    if unexpected:
        validation.error(
            "マニフェスト外のファイルがあります: " + ", ".join(sorted(unexpected))
        )


def validate_skill_frontmatter(validation: Validation) -> None:
    path = ROOT / "SKILL.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        validation.error(f"SKILL.mdが500行を超えています: {len(lines)}行")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        validation.error("SKILL.mdのYAML frontmatterが不正です")
        return
    keys = []
    values = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            validation.error(f"frontmatterの形式が不正です: {line}")
            continue
        key, value = line.split(":", 1)
        keys.append(key.strip())
        values[key.strip()] = value.strip()
    if keys != ["name", "description"]:
        validation.error(f"frontmatterのキーはname、descriptionだけにします: {keys}")
    if values.get("name") != "powerpoint-layout-design":
        validation.error("frontmatterのnameがディレクトリ名と一致しません")
    if len(values.get("description", "")) < 30:
        validation.error("frontmatterのdescriptionが短すぎます")


def iter_text_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in ALLOWED_TEXT_SUFFIXES
        and "__pycache__" not in path.parts
    )


def validate_text_safety(validation: Validation) -> None:
    for path in iter_text_files():
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            validation.error(f"{relative}: UTF-8で読めません: {exc}")
            continue
        for index, char in enumerate(text):
            if char in FORBIDDEN_CONTROLS:
                validation.error(
                    f"{relative}: 不審な不可視・双方向制御文字 U+{ord(char):04X} "
                    f"(文字位置 {index})"
                )
            category = unicodedata.category(char)
            if category == "Cc" and char not in {"\n", "\r", "\t"}:
                validation.error(
                    f"{relative}: 制御文字 U+{ord(char):04X} (文字位置 {index})"
                )
        if relative.as_posix() != "scripts/validate_bundle.py":
            for pattern, label in SUSPICIOUS_TEXT_PATTERNS:
                if pattern.search(text):
                    validation.error(f"{relative}: {label}を検出しました")
            for comment in HTML_COMMENT_PATTERN.findall(text):
                if any(
                    pattern.search(comment)
                    for pattern, _label in PROMPT_INJECTION_PATTERNS
                ):
                    validation.error(
                        f"{relative}: HTMLコメント内に注入表現を検出しました"
                    )
                elif comment.strip():
                    validation.warning(
                        f"{relative}: HTMLコメントがあります。内容を確認してください"
                    )
        if relative.as_posix() not in INJECTION_EXEMPT_PATHS:
            for pattern, label in PROMPT_INJECTION_PATTERNS:
                if pattern.search(text):
                    validation.error(f"{relative}: {label}を検出しました")
        urls = re.findall(r"https?://[^\s<>\")\]]+", text)
        if urls and relative.as_posix() not in URL_ALLOWED_PATHS:
            validation.error(
                f"{relative}: 外部URLは安全性資料か由来マニフェストだけに記録します"
            )
        if relative.as_posix() != "assets/source-manifest.json":
            for pattern in PROVENANCE_ONLY_TERMS:
                if pattern.search(text):
                    validation.error(
                        f"{relative}: 外部由来の名称はsource-manifest.jsonだけに記録します"
                    )


def validate_markdown_links(validation: Validation) -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            clean = target.strip().split("#", 1)[0]
            if not clean or re.match(r"^[a-z][a-z0-9+.-]*://", clean, re.IGNORECASE):
                continue
            resolved = (path.parent / clean).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                validation.error(
                    f"{path.relative_to(ROOT)}: Skill外を指すリンクです: {target}"
                )
                continue
            if not resolved.exists():
                validation.error(
                    f"{path.relative_to(ROOT)}: 参照先がありません: {target}"
                )


def validate_registry(validation: Validation) -> None:
    path = ROOT / "assets/layout-registry.json"
    catalog_path = ROOT / "references/layout-catalog.md"
    data = load_json(path, validation)
    if not isinstance(data, dict):
        return
    families = data.get("families")
    layouts = data.get("layouts")
    if not isinstance(families, list) or not families:
        validation.error("layout-registry.jsonにfamiliesがありません")
        return
    if not isinstance(layouts, list) or not layouts:
        validation.error("layout-registry.jsonにlayoutsがありません")
        return
    family_ids: list[str] = []
    family_layout_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            validation.error(
                "layout-registry.jsonのfamilyがオブジェクトではありません"
            )
            continue
        family_id = family.get("id")
        if not isinstance(family_id, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", family_id
        ):
            validation.error(f"不正なファミリーIDです: {family_id!r}")
            continue
        family_ids.append(family_id)
        layout_ids = family.get("layoutIds")
        if not isinstance(layout_ids, list) or not layout_ids:
            validation.error(f"{family_id}: layoutIdsがありません")
        else:
            family_layout_ids.update(layout_ids)
        if family.get("contractId") != family_id:
            validation.error(f"{family_id}: contractIdをfamily IDと一致させます")
        if family.get("defaultLayoutId") not in set(layout_ids or []):
            validation.error(f"{family_id}: defaultLayoutIdがlayoutIdsにありません")
    if len(family_ids) != len(set(family_ids)):
        validation.error("ファミリーIDが重複しています")
    ids: list[str] = []
    for layout in layouts:
        if not isinstance(layout, dict):
            validation.error("layout-registry.jsonのlayoutがオブジェクトではありません")
            continue
        layout_id = layout.get("id")
        if not isinstance(layout_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", layout_id):
            validation.error(f"不正なレイアウトIDです: {layout_id!r}")
            continue
        ids.append(layout_id)
        if layout.get("familyId") not in set(family_ids):
            validation.error(
                f"{layout_id}: 未定義familyIdです: {layout.get('familyId')}"
            )
        if layout.get("contractId") != layout.get("familyId"):
            validation.error(f"{layout_id}: contractIdとfamilyIdが一致しません")
        if not layout.get("purpose"):
            validation.error(f"{layout_id}: purposeがありません")
        if not isinstance(layout.get("capacity"), dict) or not layout["capacity"]:
            validation.error(f"{layout_id}: capacityがありません")
        regions = layout.get("regions")
        if not isinstance(regions, list) or not regions:
            validation.error(f"{layout_id}: regionsがありません")
            continue
        region_ids = []
        for region in regions:
            region_id = region.get("id")
            region_ids.append(region_id)
            for key in ("x", "y", "width", "height"):
                value = region.get(key)
                if not isinstance(value, (int, float)):
                    validation.error(f"{layout_id}/{region_id}: {key}が数値ではありません")
                    continue
                if value < 0 or value > 1:
                    validation.error(f"{layout_id}/{region_id}: {key}が0〜1の範囲外です")
            if all(isinstance(region.get(key), (int, float)) for key in ("x", "y", "width", "height")):
                if region["x"] + region["width"] > 1.000001:
                    validation.error(f"{layout_id}/{region_id}: 右端がスライド外です")
                if region["y"] + region["height"] > 1.000001:
                    validation.error(f"{layout_id}/{region_id}: 下端がスライド外です")
        if len(region_ids) != len(set(region_ids)):
            validation.error(f"{layout_id}: region IDが重複しています")
    if len(ids) != len(set(ids)):
        validation.error("レイアウトIDが重複しています")
    if family_layout_ids != set(ids):
        validation.error(
            "families.layoutIdsとlayoutsが一致しません: "
            f"family_only={sorted(family_layout_ids - set(ids))}, "
            f"layout_only={sorted(set(ids) - family_layout_ids)}"
        )
    counts = data.get("counts")
    if not isinstance(counts, dict):
        validation.error("layout-registry.jsonにcountsがありません")
    else:
        if counts.get("families") != len(families):
            validation.error("counts.familiesと実件数が一致しません")
        if counts.get("layouts") != len(layouts):
            validation.error("counts.layoutsと実件数が一致しません")
    for layout in layouts:
        fallback = layout.get("fallback")
        if fallback and fallback not in ids:
            validation.error(f"{layout.get('id')}: fallbackが未定義です: {fallback}")
    if catalog_path.is_file():
        catalog = catalog_path.read_text(encoding="utf-8")
        catalog_ids = re.findall(r"^##\s+\d+\.\s+`([^`]+)`", catalog, re.MULTILINE)
        if set(catalog_ids) != set(family_ids):
            validation.error(
                "layout-catalog.mdとlayout-registry.jsonのfamily IDが"
                "一致しません: "
                f"catalog_only={sorted(set(catalog_ids) - set(family_ids))}, "
                f"registry_only={sorted(set(family_ids) - set(catalog_ids))}"
            )


def validate_layout_contracts(validation: Validation) -> None:
    registry_data = load_json(ROOT / "assets/layout-registry.json", validation)
    contracts_data = load_json(ROOT / "assets/layout-contracts.json", validation)
    if not isinstance(registry_data, dict) or not isinstance(contracts_data, dict):
        return
    layouts = registry_data.get("layouts", [])
    contracts = contracts_data.get("contracts")
    allowed_types = set(contracts_data.get("fieldTypes", []))
    if not isinstance(contracts, dict):
        validation.error("layout-contracts.jsonにcontractsがありません")
        return
    family_ids = {
        family.get("id")
        for family in registry_data.get("families", [])
        if isinstance(family, dict) and isinstance(family.get("id"), str)
    }
    if family_ids != set(contracts):
        validation.error(
            "layout-registry.jsonのfamilyとlayout-contracts.jsonのIDが"
            "一致しません: "
            f"registry_only={sorted(family_ids - set(contracts))}, "
            f"contracts_only={sorted(set(contracts) - family_ids)}"
        )
    for layout in layouts:
        if not isinstance(layout, dict):
            continue
        layout_id = layout["id"]
        contract_id = layout.get("contractId")
        if contract_id not in contracts:
            validation.error(
                f"{layout_id}: contractがありません: {contract_id}"
            )
            continue
        contract = contracts[contract_id]
        fields = contract.get("fields") if isinstance(contract, dict) else None
        if not isinstance(fields, dict) or not fields:
            validation.error(f"{layout_id}: field contractがありません")
            continue
        expected_fields = set(layout.get("required", [])) | set(
            layout.get("optional", [])
        )
        if expected_fields != set(fields):
            validation.error(
                f"{layout_id}: registryとcontractのfieldが一致しません: "
                f"registry_only={sorted(expected_fields - set(fields))}, "
                f"contract_only={sorted(set(fields) - expected_fields)}"
            )
        required_fields = {
            name
            for name, field in fields.items()
            if isinstance(field, dict) and field.get("required") is True
        }
        if required_fields != set(layout.get("required", [])):
            validation.error(
                f"{layout_id}: required fieldが一致しません: "
                f"registry={sorted(layout.get('required', []))}, "
                f"contract={sorted(required_fields)}"
            )
        region_ids = {
            region.get("id")
            for region in layout.get("regions", [])
            if isinstance(region, dict)
        }
        for field_name, field in fields.items():
            if not isinstance(field, dict):
                validation.error(f"{layout_id}/{field_name}: contractが不正です")
                continue
            if field.get("type") not in allowed_types:
                validation.error(
                    f"{layout_id}/{field_name}: 未定義のfield typeです: "
                    f"{field.get('type')}"
                )
            if field.get("type") in {"object", "object-list"}:
                required_keys = set(field.get("requiredKeys", []))
                allowed_keys = field.get("allowedKeys")
                value_types = field.get("valueTypesByKey")
                if not isinstance(allowed_keys, list) or not allowed_keys:
                    validation.error(
                        f"{layout_id}/{field_name}: allowedKeysがありません"
                    )
                elif not isinstance(value_types, dict) or not value_types:
                    validation.error(
                        f"{layout_id}/{field_name}: valueTypesByKeyがありません"
                    )
                else:
                    allowed_key_set = set(allowed_keys)
                    if required_keys - allowed_key_set:
                        validation.error(
                            f"{layout_id}/{field_name}: requiredKeysが"
                            "allowedKeysに含まれていません"
                        )
                    if allowed_key_set != set(value_types):
                        validation.error(
                            f"{layout_id}/{field_name}: allowedKeysと"
                            "valueTypesByKeyが一致しません"
                        )
            if field.get("region") not in region_ids:
                validation.error(
                    f"{layout_id}/{field_name}: regionがありません: "
                    f"{field.get('region')}"
                )
            for key, value in field.items():
                if key.startswith(("max", "min")) and isinstance(value, int) and value < 0:
                    validation.error(
                        f"{layout_id}/{field_name}: {key}は0以上にします"
                    )
        if "fallback" in layout:
            validation.error(
                f"{layout_id}: 自動fallbackは禁止です。overflowActionを使います"
            )

    common_title = registry_data.get("common", {}).get("title", {})
    capacity = common_title.get("capacity") if isinstance(common_title, dict) else None
    if not isinstance(capacity, dict) or capacity.get("maxLines") != 1:
        validation.error("common.titleの一行上限が定義されていません")

    if contracts_data.get("schemaVersion") == "2.0":
        example_path = ROOT / "evals/example-slide-spec.json"
        if example_path.is_file():
            example_data = load_json(example_path, validation)
            if isinstance(example_data, dict):
                if example_data.get("schemaVersion") != "2.0":
                    validation.error(
                        "example-slide-spec.jsonのschemaVersionは2.0にします"
                    )
                layouts_by_id = {
                    layout.get("id"): layout
                    for layout in layouts
                    if isinstance(layout, dict)
                    and isinstance(layout.get("id"), str)
                }
                slides = example_data.get("slides")
                if not isinstance(slides, list) or not slides:
                    validation.error(
                        "example-slide-spec.jsonにslidesがありません"
                    )
                else:
                    for index, slide in enumerate(slides):
                        if not isinstance(slide, dict):
                            validation.error(
                                f"example-slide-spec.json/slides[{index}]が"
                                "不正です"
                            )
                            continue
                        layout = layouts_by_id.get(slide.get("layoutId"))
                        if not isinstance(layout, dict):
                            validation.error(
                                "example-slide-spec.jsonに未定義layoutIdが"
                                f"あります: {slide.get('layoutId')}"
                            )
                            continue
                        contract = contracts.get(layout.get("contractId"))
                        if not isinstance(contract, dict):
                            validation.error(
                                "example-slide-spec.jsonのlayoutに契約が"
                                f"ありません: {slide.get('layoutId')}"
                            )
                            continue
                        fields = slide.get("fields")
                        if not isinstance(fields, dict):
                            validation.error(
                                f"example-slide-spec.json/slides[{index}]に"
                                "fieldsがありません"
                            )
                            continue
                        contract_fields = contract.get("fields", {})
                        expected_fields = set(contract_fields) - {"title"}
                        unknown_fields = set(fields) - expected_fields
                        if unknown_fields:
                            validation.error(
                                f"example-slide-spec.json/slides[{index}]に"
                                "未定義fieldがあります: "
                                f"{sorted(unknown_fields)}"
                            )
                        required_fields = {
                            name
                            for name, field in contract_fields.items()
                            if name != "title"
                            and isinstance(field, dict)
                            and field.get("required") is True
                        }
                        missing_fields = required_fields - set(fields)
                        if missing_fields:
                            validation.error(
                                f"example-slide-spec.json/slides[{index}]に"
                                "必須fieldがありません: "
                                f"{sorted(missing_fields)}"
                            )
        return

    capacity_bindings = [
        ("cover-minimal", "titleChars", "title", "maxChars"),
        ("cover-minimal", "titleLines", "title", "maxLines"),
        ("cover-minimal", "subtitleChars", "subtitle", "maxChars"),
        ("cover-minimal", "subtitleLines", "subtitle", "maxLines"),
        ("cover-minimal", "metadataItems", "metadata", "maxItems"),
        ("section-divider", "titleChars", "title", "maxChars"),
        ("section-divider", "titleLines", "title", "maxLines"),
        ("section-divider", "questionChars", "question", "maxChars"),
        ("section-divider", "questionLines", "question", "maxLines"),
        ("executive-summary", "recommendationChars", "recommendation", "maxChars"),
        ("executive-summary", "evidenceItems", "evidence", "maxItems"),
        ("executive-summary", "evidenceCharsEach", "evidence", "maxCharsEach"),
        ("executive-summary", "actionItems", "action", "maxItems"),
        ("key-message", "messageChars", "message", "maxChars"),
        ("key-message", "supportChars", "support", "maxChars"),
        ("kpi-trend", "kpiItems", "kpis", "maxItems"),
        ("kpi-trend", "timePoints", "chart", "maxPoints"),
        ("kpi-trend", "series", "chart", "maxSeries"),
        ("kpi-trend", "annotations", "annotation", "maxItems"),
        ("chart-insight", "series", "chart", "maxSeries"),
        ("chart-insight", "linePoints", "chart", "maxPoints"),
        ("chart-insight", "insightItems", "insight", "maxItems"),
        ("comparison", "options", "options", "maxItems"),
        ("comparison", "criteria", "criteria", "maxItems"),
        ("comparison", "cellChars", "options", "maxCharsPerValue"),
        ("before-after", "comparisonItems", "before", "maxItems"),
        ("before-after", "comparisonItems", "after", "maxItems"),
        ("before-after", "charsEachSide", "before", "maxTotalChars"),
        ("before-after", "charsEachSide", "after", "maxTotalChars"),
        ("before-after", "effects", "effect", "maxItems"),
        ("process", "steps", "steps", "maxItems"),
        ("timeline-roadmap", "periods", "timeAxis", "maxItems"),
        ("timeline-roadmap", "workstreams", "workstreams", "maxItems"),
        ("timeline-roadmap", "milestones", "milestones", "maxItems"),
        ("matrix-2x2", "items", "items", "maxItems"),
        ("matrix-2x2", "quadrantChars", "axisLabels", "maxCharsPerValue"),
        ("table-insight", "rows", "table", "maxRows"),
        ("table-insight", "columns", "table", "maxColumns"),
        ("table-insight", "insightItems", "insight", "maxItems"),
        ("decision-action", "decisions", "decision", "maxItems"),
        ("decision-action", "actions", "actions", "maxItems"),
        ("appendix-reference", "detailItems", "detail", "maxItems"),
        ("appendix-reference", "noteItems", "sources", "maxItems"),
    ]
    registry_by_id = {
        layout.get("id"): layout
        for layout in layouts
        if isinstance(layout, dict) and isinstance(layout.get("id"), str)
    }
    for layout_id, capacity_key, field_name, contract_key in capacity_bindings:
        registry_value = (
            registry_by_id.get(layout_id, {})
            .get("capacity", {})
            .get(capacity_key)
        )
        contract_value = (
            contracts.get(layout_id, {})
            .get("fields", {})
            .get(field_name, {})
            .get(contract_key)
        )
        if registry_value != contract_value:
            validation.error(
                f"{layout_id}: capacity.{capacity_key}と"
                f"{field_name}.{contract_key}が一致しません: "
                f"registry={registry_value}, contract={contract_value}"
            )
    process_capacity = registry_by_id.get("process", {}).get("capacity", {})
    process_step_limits = (
        contracts.get("process", {})
        .get("fields", {})
        .get("steps", {})
        .get("maxCharsByKey", {})
    )
    for capacity_key, field_key in (
        ("stepTitleChars", "title"),
        ("stepBodyChars", "body"),
    ):
        if process_capacity.get(capacity_key) != process_step_limits.get(field_key):
            validation.error(
                f"process: capacity.{capacity_key}と"
                f"steps.maxCharsByKey.{field_key}が一致しません"
            )
    chart_capacity = registry_by_id.get("chart-insight", {}).get("capacity", {})
    chart_limits = (
        contracts.get("chart-insight", {})
        .get("fields", {})
        .get("chart", {})
        .get("maxPointsByType", {})
    )
    if chart_capacity.get("barCategories") != chart_limits.get("bar"):
        validation.error(
            "chart-insight: capacity.barCategoriesと"
            "chart.maxPointsByType.barが一致しません"
        )
    appendix_capacity = registry_by_id.get("appendix-reference", {}).get(
        "capacity", {}
    )
    appendix_detail_limits = (
        contracts.get("appendix-reference", {})
        .get("fields", {})
        .get("detail", {})
        .get("maxCharsByKey", {})
    )
    for capacity_key, field_key in (
        ("detailHeadingChars", "heading"),
        ("detailBodyChars", "body"),
    ):
        if appendix_capacity.get(capacity_key) != appendix_detail_limits.get(field_key):
            validation.error(
                f"appendix-reference: capacity.{capacity_key}と"
                f"detail.maxCharsByKey.{field_key}が一致しません"
            )

    example_path = ROOT / "evals/example-slide-spec.json"
    if example_path.is_file():
        example_data = load_json(example_path, validation)
        if isinstance(example_data, dict):
            slides = example_data.get("slides")
            if not isinstance(slides, list) or not slides:
                validation.error("example-slide-spec.jsonにslidesがありません")
            else:
                for index, slide in enumerate(slides):
                    if not isinstance(slide, dict):
                        validation.error(
                            f"example-slide-spec.json/slides[{index}]が不正です"
                        )
                        continue
                    layout_id = slide.get("layoutId")
                    contract = contracts.get(layout_id)
                    if not isinstance(contract, dict):
                        validation.error(
                            "example-slide-spec.jsonに未定義layoutIdがあります: "
                            f"{layout_id}"
                        )
                        continue
                    fields = slide.get("fields")
                    if not isinstance(fields, dict):
                        validation.error(
                            f"example-slide-spec.json/slides[{index}]にfieldsがありません"
                        )
                        continue
                    expected_fields = set(contract.get("fields", {})) - {"title"}
                    unknown_fields = set(fields) - expected_fields
                    if unknown_fields:
                        validation.error(
                            f"example-slide-spec.json/slides[{index}]に"
                            f"未定義fieldがあります: {sorted(unknown_fields)}"
                        )
                    required_fields = {
                        name
                        for name, field in contract.get("fields", {}).items()
                        if name != "title"
                        and isinstance(field, dict)
                        and field.get("required") is True
                    }
                    missing_fields = required_fields - set(fields)
                    if missing_fields:
                        validation.error(
                            f"example-slide-spec.json/slides[{index}]に"
                            f"必須fieldがありません: {sorted(missing_fields)}"
                        )


def validate_design_tokens(validation: Validation) -> None:
    tokens = load_json(ROOT / "assets/design-tokens.json", validation)
    registry = load_json(ROOT / "assets/layout-registry.json", validation)
    if not isinstance(tokens, dict) or not isinstance(registry, dict):
        return
    canvas = tokens.get("canvas", {})
    grid = tokens.get("grid", {})
    try:
        expected_content = (
            grid["columns"] * grid["columnWidth"]
            + (grid["columns"] - 1) * grid["gutter"]
        )
        if abs(expected_content - grid["contentWidth"]) > 0.01:
            validation.error(
                "design-tokens.jsonの列幅、ガター、contentWidthが一致しません: "
                f"calculated={expected_content:.4f}, "
                f"declared={grid['contentWidth']}"
            )
        safe_bottom_ratio = 1 - canvas["safeArea"]["bottom"] / canvas["height"]
        footer = registry["common"]["footer"]
        if footer["y"] + footer["height"] > safe_bottom_ratio + 0.00001:
            validation.error("common.footerが下側セーフエリアを超えています")
    except (KeyError, TypeError, ZeroDivisionError) as exc:
        validation.error(f"design tokenの構造が不正です: {exc}")


def validate_evals(validation: Validation) -> None:
    trigger_data = load_json(ROOT / "evals/trigger-queries.json", validation)
    if isinstance(trigger_data, list):
        ids = []
        positive = 0
        negative = 0
        for item in trigger_data:
            if not isinstance(item, dict):
                validation.error("trigger-queries.jsonの項目がオブジェクトではありません")
                continue
            ids.append(item.get("id"))
            if not isinstance(item.get("query"), str) or not item["query"].strip():
                validation.error(f"{item.get('id')}: queryがありません")
            if item.get("should_trigger") is True:
                positive += 1
            elif item.get("should_trigger") is False:
                negative += 1
            else:
                validation.error(f"{item.get('id')}: should_triggerが真偽値ではありません")
        if len(ids) != len(set(ids)):
            validation.error("trigger-queries.jsonのIDが重複しています")
        if positive < 10 or negative < 8:
            validation.error(
                f"トリガー評価が不足しています: positive={positive}, negative={negative}"
            )
    output_data = load_json(ROOT / "evals/output-cases.json", validation)
    if isinstance(output_data, list):
        ids = []
        for item in output_data:
            if not isinstance(item, dict):
                validation.error("output-cases.jsonの項目がオブジェクトではありません")
                continue
            ids.append(item.get("id"))
            if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
                validation.error(f"{item.get('id')}: promptがありません")
            assertions = item.get("assertions")
            if not isinstance(assertions, list) or len(assertions) < 3:
                validation.error(f"{item.get('id')}: assertionsが3件未満です")
        if len(ids) != len(set(ids)):
            validation.error("output-cases.jsonのIDが重複しています")
        if len(output_data) < 8:
            validation.error(f"出力評価ケースが不足しています: {len(output_data)}")
    selection_data = load_json(
        ROOT / "evals/layout-selection-cases.json", validation
    )
    registry_data = load_json(
        ROOT / "assets/layout-registry.json", validation
    )
    if isinstance(selection_data, list) and isinstance(registry_data, dict):
        family_ids = {
            item.get("id")
            for item in registry_data.get("families", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        layout_ids = {
            item.get("id")
            for item in registry_data.get("layouts", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        covered_families: set[str] = set()
        eval_ids: list[str] = []
        for item in selection_data:
            if not isinstance(item, dict):
                validation.error(
                    "layout-selection-cases.jsonの項目が"
                    "オブジェクトではありません"
                )
                continue
            eval_ids.append(item.get("id"))
            family_id = item.get("expectedFamilyId")
            if family_id not in family_ids:
                validation.error(
                    f"{item.get('id')}: expectedFamilyIdが未定義です: "
                    f"{family_id}"
                )
            else:
                covered_families.add(family_id)
            allowed = item.get("allowedLayoutIds")
            if not isinstance(allowed, list) or not allowed:
                validation.error(
                    f"{item.get('id')}: allowedLayoutIdsがありません"
                )
            else:
                unknown = set(allowed) - layout_ids
                if unknown:
                    validation.error(
                        f"{item.get('id')}: 未定義layoutIdがあります: "
                        f"{sorted(unknown)}"
                    )
            if not isinstance(item.get("prompt"), str) or not item[
                "prompt"
            ].strip():
                validation.error(f"{item.get('id')}: promptがありません")
        if len(eval_ids) != len(set(eval_ids)):
            validation.error("layout-selection-cases.jsonのIDが重複しています")
        if covered_families != family_ids:
            validation.error(
                "layout-selection-cases.jsonが全familyを網羅していません: "
                f"{sorted(family_ids - covered_families)}"
            )


def validate_png(validation: Validation) -> None:
    path = ROOT / "assets/layout-preview.png"
    if not path.is_file():
        return
    try:
        payload = path.read_bytes()
        if payload[:8] != b"\x89PNG\r\n\x1a\n":
            validation.error("layout-preview.pngのPNGシグネチャが不正です")
            return
        offset = 8
        width = 0
        height = 0
        chunk_types: list[bytes] = []
        found_iend = False
        while offset < len(payload):
            if offset + 12 > len(payload):
                validation.error("layout-preview.pngのチャンクが途中で切れています")
                return
            length = struct.unpack(">I", payload[offset : offset + 4])[0]
            chunk_type = payload[offset + 4 : offset + 8]
            chunk_end = offset + 12 + length
            if chunk_end > len(payload):
                validation.error("layout-preview.pngのチャンク長が不正です")
                return
            chunk_data = payload[offset + 8 : offset + 8 + length]
            stored_crc = struct.unpack(
                ">I", payload[offset + 8 + length : chunk_end]
            )[0]
            calculated_crc = zlib.crc32(chunk_type)
            calculated_crc = zlib.crc32(chunk_data, calculated_crc) & 0xFFFFFFFF
            if stored_crc != calculated_crc:
                validation.error(
                    f"layout-preview.pngのCRCが不正です: {chunk_type!r}"
                )
            chunk_types.append(chunk_type)
            if chunk_type == b"IHDR":
                if len(chunk_data) != 13:
                    validation.error("layout-preview.pngのIHDRが不正です")
                    return
                width, height = struct.unpack(">II", chunk_data[:8])
            if chunk_type in {b"tEXt", b"zTXt", b"iTXt"}:
                text_payload = chunk_data.decode("utf-8", errors="ignore")
                for pattern, label in PROMPT_INJECTION_PATTERNS:
                    if pattern.search(text_payload):
                        validation.error(
                            f"layout-preview.pngのテキストチャンクに{label}があります"
                        )
            offset = chunk_end
            if chunk_type == b"IEND":
                found_iend = True
                break
        if chunk_types.count(b"IHDR") != 1 or not found_iend:
            validation.error("layout-preview.pngの必須チャンクが不正です")
        if offset != len(payload):
            validation.error("layout-preview.pngのIEND後に追記データがあります")
        if width < 800 or height < 450:
            validation.error(
                f"layout-preview.pngの解像度が低すぎます: {width}x{height}"
            )
        if width * height > 25_000_000:
            validation.error(
                f"layout-preview.pngの画素数が大きすぎます: {width}x{height}"
            )
    except (OSError, struct.error, zlib.error) as exc:
        validation.error(f"layout-preview.pngを検査できません: {exc}")


def validate_pptx(validation: Validation) -> None:
    path = ROOT / "assets/reference-layouts.pptx"
    if not path.is_file():
        return
    registry = load_json(ROOT / "assets/layout-registry.json", validation)
    expected_slides = (
        registry.get("counts", {}).get("layouts")
        if isinstance(registry, dict)
        else None
    )
    if not isinstance(expected_slides, int) or expected_slides < 1:
        validation.error(
            "reference-layouts.pptxの期待ページ数を解決できません"
        )
        return
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            duplicates = [
                name for name, count in Counter(names).items() if count > 1
            ]
            if duplicates:
                validation.error(
                    "reference-layouts.pptxに重複ZIP名があります: "
                    + ", ".join(sorted(duplicates))
                )
            total_uncompressed = 0
            for info in infos:
                pure_name = PurePosixPath(info.filename)
                if pure_name.is_absolute() or ".." in pure_name.parts:
                    validation.error(
                        f"reference-layouts.pptxに経路逸脱があります: {info.filename}"
                    )
                if info.flag_bits & 0x1:
                    validation.error(
                        f"reference-layouts.pptxに暗号化エントリがあります: "
                        f"{info.filename}"
                    )
                total_uncompressed += info.file_size
                if info.file_size > 20_000_000:
                    validation.error(
                        f"reference-layouts.pptxのエントリが大きすぎます: "
                        f"{info.filename}"
                    )
                if (
                    info.compress_size > 0
                    and info.file_size / info.compress_size > 200
                ):
                    validation.error(
                        f"reference-layouts.pptxの圧縮率が不審です: {info.filename}"
                    )
            if total_uncompressed > 50_000_000:
                validation.error(
                    "reference-layouts.pptxの展開後サイズが大きすぎます"
                )
            bad_crc = archive.testzip()
            if bad_crc:
                validation.error(
                    f"reference-layouts.pptxのCRCが不正です: {bad_crc}"
                )
            if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
                validation.error("reference-layouts.pptxのPPTX構造が不正です")
                return
            content_types = archive.read("[Content_Types].xml").decode(
                "utf-8-sig", errors="replace"
            )
            if re.search(
                r"macroEnabled|vbaProject|application/vnd\.ms-office\.activeX",
                content_types,
                re.IGNORECASE,
            ):
                validation.error(
                    "reference-layouts.pptxにマクロ有効Content-Typeがあります"
                )
            forbidden = [
                name
                for name in names
                if "vbaProject" in name
                or name.startswith("ppt/embeddings/")
                or name.startswith("ppt/activeX/")
                or name.startswith("ppt/comments/")
                or name.startswith("ppt/externalLinks/")
                or name.startswith("customUI/")
            ]
            if forbidden:
                validation.error(
                    "reference-layouts.pptxに禁止された埋め込みがあります: "
                    + ", ".join(forbidden)
                )
            all_xml_text: list[str] = []
            xml_names = [
                name
                for name in names
                if name.endswith((".xml", ".rels"))
                and (name.startswith("ppt/") or name.startswith("docProps/"))
            ]
            pptx_patterns = PROMPT_INJECTION_PATTERNS + SUSPICIOUS_TEXT_PATTERNS[:3]
            for xml_name in xml_names:
                try:
                    xml_text = archive.read(xml_name).decode("utf-8-sig")
                except UnicodeError as exc:
                    validation.error(f"{xml_name}: UTF-8で読めません: {exc}")
                    continue
                all_xml_text.append(xml_text)
                for char in xml_text:
                    if char in FORBIDDEN_CONTROLS:
                        validation.error(
                            f"reference-layouts.pptx/{xml_name}: "
                            f"不可視・双方向制御文字 U+{ord(char):04X}"
                        )
                for pattern, label in pptx_patterns:
                    if pattern.search(xml_text):
                        validation.error(
                            f"reference-layouts.pptx/{xml_name}: {label}を検出しました"
                        )
                try:
                    xml_root = ElementTree.fromstring(
                        archive.read(xml_name).decode("utf-8-sig")
                    )
                except (ElementTree.ParseError, UnicodeError):
                    continue
                for element in xml_root.iter():
                    if element.attrib.get("hidden", "").lower() in {"1", "true"}:
                        validation.error(
                            f"reference-layouts.pptxに非表示要素があります: {xml_name}"
                        )
            slide_names = [
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
            if len(slide_names) != expected_slides:
                validation.error(
                    "reference-layouts.pptxのページ数がlayout-registry.jsonと"
                    f"一致しません: expected={expected_slides}, "
                    f"actual={len(slide_names)}"
                )
            for slide_name in slide_names:
                try:
                    slide_root = ElementTree.fromstring(archive.read(slide_name))
                except ElementTree.ParseError as exc:
                    validation.error(f"{slide_name}: XMLが不正です: {exc}")
                    continue
                if slide_root.attrib.get("show", "").lower() in {"0", "false"}:
                    validation.error(f"非表示スライドがあります: {slide_name}")
                names_in_slide: list[str] = []
                ids_in_slide: list[str] = []
                for element in slide_root.iter():
                    if element.tag.endswith("}cNvPr"):
                        shape_name = element.attrib.get("name", "")
                        shape_id = element.attrib.get("id", "")
                        if not shape_name:
                            validation.error(
                                f"reference-layouts.pptxに無名図形があります: "
                                f"{slide_name}"
                            )
                        names_in_slide.append(shape_name)
                        if not re.fullmatch(r"[1-9]\d*", shape_id):
                            validation.error(
                                f"reference-layouts.pptxに不正な図形IDがあります: "
                                f"{slide_name}: {shape_id!r}"
                            )
                        ids_in_slide.append(shape_id)
                duplicate_shape_names = [
                    shape_name
                    for shape_name, count in Counter(names_in_slide).items()
                    if shape_name and count > 1
                ]
                if duplicate_shape_names:
                    validation.error(
                        f"reference-layouts.pptxに重複図形名があります: "
                        f"{slide_name}: {duplicate_shape_names}"
                    )
                duplicate_shape_ids = [
                    shape_id
                    for shape_id, count in Counter(ids_in_slide).items()
                    if shape_id and count > 1
                ]
                if duplicate_shape_ids:
                    validation.error(
                        f"reference-layouts.pptxに重複図形IDがあります: "
                        f"{slide_name}: {duplicate_shape_ids}"
                    )
                valid_shape_ids = set(ids_in_slide)
                for element in slide_root.iter():
                    if element.tag.endswith(("}stCxn", "}endCxn")):
                        target_id = element.attrib.get("id", "")
                        if target_id not in valid_shape_ids:
                            validation.error(
                                "reference-layouts.pptxのコネクター参照先が"
                                f"存在しません: {slide_name}: {target_id}"
                            )
            for rel_name in [name for name in names if name.endswith(".rels")]:
                try:
                    root = ElementTree.fromstring(archive.read(rel_name))
                except ElementTree.ParseError as exc:
                    validation.error(f"{rel_name}: XMLが不正です: {exc}")
                    continue
                for relationship in root:
                    if relationship.attrib.get("TargetMode") == "External":
                        validation.error(
                            f"reference-layouts.pptxに外部参照があります: {rel_name}"
                        )
                    relationship_type = relationship.attrib.get("Type", "").lower()
                    if any(
                        token in relationship_type
                        for token in (
                            "oleobject",
                            "vbaproject",
                            "externaldata",
                            "externallink",
                            "activex",
                        )
                    ) or relationship_type.endswith("/package"):
                        validation.error(
                            f"reference-layouts.pptxに禁止Relationshipがあります: "
                            f"{rel_name}"
                        )
            joined_xml = "\n".join(all_xml_text)
            if "Yu Gothic" not in joined_xml:
                validation.error(
                    "reference-layouts.pptxに日本語用のYu Gothic指定がありません"
                )
            for forbidden_metadata in ("Walnut Exporter", "Noto Sans JP"):
                if forbidden_metadata in joined_xml:
                    validation.error(
                        "reference-layouts.pptxに不要な生成・一時環境情報があります: "
                        f"{forbidden_metadata}"
                    )
            if "docProps/core.xml" in names:
                core_text = archive.read("docProps/core.xml").decode(
                    "utf-8-sig", errors="replace"
                )
                if (
                    "<dc:creator>powerpoint-layout-design</dc:creator>"
                    not in core_text
                    or "<lastModifiedBy>powerpoint-layout-design</lastModifiedBy>"
                    not in core_text
                ):
                    validation.error(
                        "reference-layouts.pptxの作成者メタデータが固定されていません"
                    )
            if "docProps/app.xml" in names:
                app_text = archive.read("docProps/app.xml").decode(
                    "utf-8-sig", errors="replace"
                )
                for expected_metadata in (
                    "<ap:Application>powerpoint-layout-design</ap:Application>",
                    f"<ap:Slides>{expected_slides}</ap:Slides>",
                    f"<ap:Notes>{expected_slides}</ap:Notes>",
                    "<ap:HiddenSlides>0</ap:HiddenSlides>",
                ):
                    if expected_metadata not in app_text:
                        validation.error(
                            "reference-layouts.pptxの拡張メタデータが不正です: "
                            f"{expected_metadata}"
                        )
    except (OSError, zipfile.BadZipFile) as exc:
        validation.error(f"reference-layouts.pptxを検査できません: {exc}")


def validate_manifest(validation: Validation) -> None:
    data = load_json(ROOT / "assets/source-manifest.json", validation)
    if not isinstance(data, dict):
        return
    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("method") != "clean-room":
        validation.error("source-manifest.jsonにclean-room由来が記録されていません")
    elif not provenance.get("statement"):
        validation.error("source-manifest.jsonにclean-roomの説明がありません")
    external_sources = (
        provenance.get("externalInspiration", [])
        if isinstance(provenance, dict)
        else []
    )
    if not isinstance(external_sources, list) or len(external_sources) != 1:
        validation.error(
            "source-manifest.jsonの外部参考元は識別した1件だけにします"
        )
    else:
        source = external_sources[0]
        if not isinstance(source, dict):
            validation.error("source-manifest.jsonの外部参考元が不正です")
        else:
            if not re.fullmatch(r"[0-9a-f]{40}", str(source.get("commit", ""))):
                validation.error(
                    "source-manifest.jsonの外部参考元コミットが固定されていません"
                )
            if source.get("license") != "Apache-2.0":
                validation.error(
                    "source-manifest.jsonの外部参考元ライセンスが不正です"
                )
            if not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", str(source.get("observedAt", ""))
            ):
                validation.error(
                    "source-manifest.jsonの外部参考元確認日が不正です"
                )
    assets = data.get("assets")
    if not isinstance(assets, list):
        validation.error("source-manifest.jsonにassetsがありません")
        return
    manifest_paths = {item.get("path") for item in assets if isinstance(item, dict)}
    expected = {
        "design-tokens.json",
        "layout-contracts.json",
        "layout-registry.json",
        "slide-spec.schema.json",
        "reference-layouts.pptx",
        "layout-preview.png",
    }
    if expected != manifest_paths:
        validation.error(
            "source-manifest.jsonの資産一覧が一致しません: "
            f"missing={sorted(expected - manifest_paths)}, "
            f"unexpected={sorted(manifest_paths - expected)}"
        )
    integrity = data.get("integrity")
    if not isinstance(integrity, dict):
        validation.error("source-manifest.jsonにintegrityがありません")
        return
    if integrity.get("algorithm") != "SHA-256":
        validation.error("source-manifest.jsonのハッシュ方式はSHA-256にします")
    hashes = integrity.get("files")
    if not isinstance(hashes, dict):
        validation.error("source-manifest.jsonにファイルハッシュがありません")
        return
    expected_hash_paths = set(REQUIRED_FILES) - {"assets/source-manifest.json"}
    actual_hash_paths = set(hashes)
    if expected_hash_paths != actual_hash_paths:
        validation.error(
            "source-manifest.jsonのハッシュ対象が一致しません: "
            f"missing={sorted(expected_hash_paths - actual_hash_paths)}, "
            f"unexpected={sorted(actual_hash_paths - expected_hash_paths)}"
        )
    for relative in sorted(expected_hash_paths & actual_hash_paths):
        expected_digest = hashes.get(relative)
        if not isinstance(expected_digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected_digest
        ):
            validation.error(
                f"source-manifest.jsonのSHA-256形式が不正です: {relative}"
            )
            continue
        try:
            actual_digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        except OSError as exc:
            validation.error(f"{relative}のSHA-256を計算できません: {exc}")
            continue
        if actual_digest != expected_digest:
            validation.error(
                f"source-manifest.jsonのSHA-256が一致しません: {relative}"
            )


def main() -> int:
    validation = Validation()
    validate_required_files(validation)
    validate_file_inventory(validation)
    validate_skill_frontmatter(validation)
    validate_text_safety(validation)
    validate_markdown_links(validation)
    validate_registry(validation)
    validate_layout_contracts(validation)
    validate_design_tokens(validation)
    validate_evals(validation)
    validate_png(validation)
    validate_pptx(validation)
    validate_manifest(validation)

    for message in validation.warnings:
        print(f"警告: {message}")
    for message in validation.errors:
        print(f"エラー: {message}")

    text_count = len(iter_text_files())
    layout_count = 0
    registry = ROOT / "assets/layout-registry.json"
    if registry.is_file():
        try:
            layout_count = len(json.loads(registry.read_text(encoding="utf-8"))["layouts"])
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError):
            pass
    print(
        f"検査結果: text_files={text_count}, layouts={layout_count}, "
        f"warnings={len(validation.warnings)}, errors={len(validation.errors)}"
    )
    return 1 if validation.errors else 0


if __name__ == "__main__":
    sys.exit(main())
