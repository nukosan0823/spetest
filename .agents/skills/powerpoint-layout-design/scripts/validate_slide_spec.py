#!/usr/bin/env python3
"""スライド設計JSONをレイアウト契約に対して検査する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PATH = ROOT / "assets/layout-contracts.json"
SCHEMA_PATH = ROOT / "assets/slide-spec.schema.json"
ALLOWED_CLASSIFICATIONS = {"fact", "estimate", "illustrative", "mixed"}
ALLOWED_USAGE = {"projection", "pre-read", "handout", "print"}
ROOT_KEYS = {"schemaVersion", "brief", "slides"}
BRIEF_KEYS = {
    "audience",
    "purpose",
    "expectedAction",
    "usage",
    "aspectRatio",
}
SLIDE_KEYS = {
    "number",
    "role",
    "layoutId",
    "actionTitle",
    "fields",
    "evidence",
    "sources",
    "dataClassification",
    "nextRelation",
}


def char_count(value: str) -> int:
    return len(value)


def line_count(value: str) -> int:
    return value.count("\n") + 1


def is_empty(value) -> bool:
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def validate_allowed_keys(
    value: dict, allowed: set[str], location: str, errors: list[str]
) -> None:
    unknown = set(value) - allowed
    if unknown:
        errors.append(f"{location}: 未定義プロパティがあります: {sorted(unknown)}")


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: JSONを読み込めません: {exc}")
        return None


def validate_json_schema(
    value, schema: dict, location: str, errors: list[str]
) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{location}: JSON Schema上のオブジェクトではありません")
            return
        properties = schema.get("properties", {})
        for required_key in schema.get("required", []):
            if required_key not in value:
                errors.append(
                    f"{location}.{required_key}: JSON Schema上の必須項目です"
                )
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                errors.append(
                    f"{location}: JSON Schemaで許可されないプロパティがあります: "
                    f"{sorted(unknown)}"
                )
        for key, item in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                validate_json_schema(
                    item, child_schema, f"{location}.{key}", errors
                )
    elif schema_type == "array":
        if not isinstance(value, list):
            errors.append(f"{location}: JSON Schema上の配列ではありません")
            return
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(
                f"{location}: JSON Schemaの最小件数{min_items}を下回ります"
            )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate_json_schema(
                    item, item_schema, f"{location}[{index}]", errors
                )
    elif schema_type == "string":
        if not isinstance(value, str):
            errors.append(f"{location}: JSON Schema上の文字列ではありません")
            return
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(
                f"{location}: JSON Schemaの最小文字数{min_length}を下回ります"
            )
    elif schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{location}: JSON Schema上の整数ではありません")
            return
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(
                f"{location}: JSON Schemaの最小値{minimum}を下回ります"
            )
    if "const" in schema and value != schema["const"]:
        errors.append(
            f"{location}: JSON Schemaの固定値{schema['const']!r}と一致しません"
        )
    if "enum" in schema and value not in schema["enum"]:
        errors.append(
            f"{location}: JSON Schemaの選択肢にありません: {value!r}"
        )


def validate_string(value, contract, location: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{location}: 文字列ではありません")
        return
    if contract.get("required") is True and not value.strip():
        errors.append(f"{location}: 空文字列は使えません")
    max_chars = contract.get("maxChars")
    if isinstance(max_chars, int) and char_count(value) > max_chars:
        errors.append(
            f"{location}: {char_count(value)}文字で上限{max_chars}文字を超えています"
        )
    max_lines = contract.get("maxLines")
    if isinstance(max_lines, int) and line_count(value) > max_lines:
        errors.append(
            f"{location}: {line_count(value)}行で上限{max_lines}行を超えています"
        )


def validate_list(value, contract, location: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{location}: 配列ではありません")
        return
    if contract.get("required") is True and not value:
        errors.append(f"{location}: 必須配列を空にできません")
    min_items = contract.get("minItems")
    max_items = contract.get("maxItems")
    if isinstance(min_items, int) and len(value) < min_items:
        errors.append(f"{location}: {len(value)}件で下限{min_items}件を下回ります")
    if isinstance(max_items, int) and len(value) > max_items:
        errors.append(f"{location}: {len(value)}件で上限{max_items}件を超えています")


def validate_object(value, contract, location: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location}: オブジェクトではありません")
        return
    allowed_keys = contract.get("allowedKeys")
    if isinstance(allowed_keys, list):
        unknown = set(value) - set(allowed_keys)
        if unknown:
            errors.append(
                f"{location}: 未定義キーがあります: {sorted(unknown)}"
            )
    for key in contract.get("requiredKeys", []):
        if key not in value:
            errors.append(f"{location}: 必須キーがありません: {key}")
        elif is_empty(value[key]):
            errors.append(f"{location}.{key}: 必須値が空です")
    max_chars = contract.get("maxCharsPerValue")
    if isinstance(max_chars, int):
        for key, item in value.items():
            if isinstance(item, str) and char_count(item) > max_chars:
                errors.append(
                    f"{location}.{key}: {char_count(item)}文字で上限"
                    f"{max_chars}文字を超えています"
                )
            if isinstance(item, list):
                for index, nested in enumerate(item):
                    if isinstance(nested, str) and char_count(nested) > max_chars:
                        errors.append(
                            f"{location}.{key}[{index}]: {char_count(nested)}文字で"
                            f"上限{max_chars}文字を超えています"
                        )
    max_chars_by_key = contract.get("maxCharsByKey", {})
    if isinstance(max_chars_by_key, dict):
        for key, limit in max_chars_by_key.items():
            if key in value and isinstance(limit, int) and isinstance(value[key], str):
                if char_count(value[key]) > limit:
                    errors.append(
                        f"{location}.{key}: {char_count(value[key])}文字で"
                        f"上限{limit}文字を超えています"
                    )
    value_types_by_key = contract.get("valueTypesByKey", {})
    if isinstance(value_types_by_key, dict):
        for key, expected_type in value_types_by_key.items():
            if key not in value:
                continue
            item = value[key]
            valid = False
            if expected_type == "string":
                valid = isinstance(item, str)
            elif expected_type == "number":
                valid = (
                    isinstance(item, (int, float))
                    and not isinstance(item, bool)
                )
            elif expected_type == "boolean":
                valid = isinstance(item, bool)
            elif expected_type == "string-list":
                valid = isinstance(item, list) and all(
                    isinstance(nested, str) for nested in item
                )
            elif expected_type == "number-list":
                valid = isinstance(item, list) and all(
                    isinstance(nested, (int, float))
                    and not isinstance(nested, bool)
                    for nested in item
                )
            elif expected_type == "scalar":
                valid = (
                    isinstance(item, (str, int, float))
                    and not isinstance(item, bool)
                )
            if not valid:
                errors.append(
                    f"{location}.{key}: 契約型{expected_type}ではありません"
                )


def validate_field(value, contract, location: str, errors: list[str]) -> None:
    field_type = contract.get("type")
    if field_type == "string":
        validate_string(value, contract, location, errors)
    elif field_type == "string-list":
        validate_list(value, contract, location, errors)
        if isinstance(value, list):
            max_chars = contract.get("maxCharsEach")
            total_chars = 0
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{location}[{index}]: 文字列ではありません")
                elif isinstance(max_chars, int) and char_count(item) > max_chars:
                    errors.append(
                        f"{location}[{index}]: {char_count(item)}文字で上限"
                        f"{max_chars}文字を超えています"
                    )
                elif isinstance(item, str):
                    total_chars += char_count(item)
            max_total_chars = contract.get("maxTotalChars")
            if (
                isinstance(max_total_chars, int)
                and total_chars > max_total_chars
            ):
                errors.append(
                    f"{location}: 合計{total_chars}文字で上限"
                    f"{max_total_chars}文字を超えています"
                )
    elif field_type == "object":
        validate_object(value, contract, location, errors)
    elif field_type == "object-list":
        validate_list(value, contract, location, errors)
        if isinstance(value, list):
            for index, item in enumerate(value):
                validate_object(item, contract, f"{location}[{index}]", errors)
    elif field_type == "chart":
        validate_object(value, contract, location, errors)
        if isinstance(value, dict):
            chart_type = value.get("type")
            allowed_chart_types = contract.get("allowedChartTypes", [])
            if not isinstance(chart_type, str) or not chart_type:
                errors.append(f"{location}.type: チャート種別が必要です")
            elif allowed_chart_types and chart_type not in allowed_chart_types:
                errors.append(
                    f"{location}.type: 未対応のチャート種別です: {chart_type}"
                )
            categories = value.get("categories")
            if not isinstance(categories, list) or not categories:
                errors.append(f"{location}.categories: 空でない配列が必要です")
                categories = []
            else:
                for index, category in enumerate(categories):
                    if not isinstance(category, str) or not category.strip():
                        errors.append(
                            f"{location}.categories[{index}]: "
                            "空でない文字列が必要です"
                        )
            max_points = contract.get("maxPoints", 10**9)
            max_points_by_type = contract.get("maxPointsByType", {})
            if isinstance(chart_type, str) and isinstance(max_points_by_type, dict):
                max_points = max_points_by_type.get(chart_type, max_points)
            if isinstance(categories, list) and len(categories) > max_points:
                errors.append(
                    f"{location}.categories: データ点数が上限{max_points}を"
                    "超えています"
                )
            series = value.get("series")
            if not isinstance(series, list) or not series:
                errors.append(f"{location}.series: 空でない配列が必要です")
            else:
                if len(series) > contract.get("maxSeries", 10**9):
                    errors.append(f"{location}.series: 系列数が上限を超えています")
                for series_index, item in enumerate(series):
                    series_location = f"{location}.series[{series_index}]"
                    if not isinstance(item, dict):
                        errors.append(f"{series_location}: オブジェクトではありません")
                        continue
                    name = item.get("name")
                    values = item.get("values")
                    if not isinstance(name, str) or not name.strip():
                        errors.append(f"{series_location}.nameがありません")
                    if not isinstance(values, list) or not values:
                        errors.append(
                            f"{series_location}.values: 空でない配列が必要です"
                        )
                        continue
                    if categories and len(values) != len(categories):
                        errors.append(
                            f"{series_location}.values: categoriesと件数が"
                            "一致しません"
                        )
                    for value_index, point in enumerate(values):
                        if (
                            not isinstance(point, (int, float))
                            or isinstance(point, bool)
                        ):
                            errors.append(
                                f"{series_location}.values[{value_index}]: "
                                "数値ではありません"
                            )
    elif field_type == "table":
        validate_object(value, contract, location, errors)
        if isinstance(value, dict):
            headers = value.get("headers")
            if not isinstance(headers, list) or not headers:
                errors.append(f"{location}.headers: 空でない配列が必要です")
                headers = []
            else:
                if len(headers) > contract.get("maxColumns", 10**9):
                    errors.append(f"{location}.headers: 列数が上限を超えています")
                for column_index, header in enumerate(headers):
                    if not isinstance(header, str) or not header.strip():
                        errors.append(
                            f"{location}.headers[{column_index}]: "
                            "空でない文字列が必要です"
                        )
            rows = value.get("values")
            if not isinstance(rows, list):
                errors.append(f"{location}.values: 二次元配列が必要です")
            else:
                if len(rows) > contract.get("maxRows", 10**9):
                    errors.append(f"{location}: 行数が上限を超えています")
                for row_index, row in enumerate(rows):
                    if not isinstance(row, list):
                        errors.append(f"{location}.values[{row_index}]: 配列ではありません")
                        continue
                    if len(row) > contract.get("maxColumns", 10**9):
                        errors.append(
                            f"{location}.values[{row_index}]: 列数が上限を超えています"
                        )
                    if headers and len(row) != len(headers):
                        errors.append(
                            f"{location}.values[{row_index}]: headersと列数が"
                            "一致しません"
                        )
                    for column_index, cell in enumerate(row):
                        if isinstance(cell, (dict, list)) or cell is None:
                            errors.append(
                                f"{location}.values[{row_index}][{column_index}]: "
                                "セル値の型が不正です"
                            )
                        if char_count(str(cell)) > contract.get(
                            "maxCharsPerCell", 10**9
                        ):
                            errors.append(
                                f"{location}.values[{row_index}][{column_index}]: "
                                "セル文字数が上限を超えています"
                            )
    elif field_type == "media":
        if not isinstance(value, dict):
            errors.append(f"{location}: メディア記述オブジェクトではありません")
        else:
            if not value.get("path") and not value.get("assetId"):
                errors.append(
                    f"{location}: pathまたはassetIdのどちらかが必要です"
                )
            if "altText" in value and not isinstance(value["altText"], str):
                errors.append(f"{location}.altText: 文字列ではありません")
    else:
        errors.append(f"{location}: 未対応のfield typeです: {field_type}")


def validate_layout_invariants(
    layout_id: str, fields: dict, location: str, errors: list[str]
) -> None:
    if layout_id == "comparison":
        criteria = fields.get("criteria")
        options = fields.get("options")
        if isinstance(criteria, list) and isinstance(options, list):
            for index, option in enumerate(options):
                values = option.get("values") if isinstance(option, dict) else None
                if isinstance(values, list) and len(values) != len(criteria):
                    errors.append(
                        f"{location}.fields.options[{index}].values: "
                        "criteriaと件数が一致しません"
                    )
    elif layout_id == "before-after":
        before = fields.get("before")
        after = fields.get("after")
        if isinstance(before, list) and isinstance(after, list):
            if len(before) != len(after):
                errors.append(
                    f"{location}.fields: beforeとafterの件数が一致しません"
                )
    elif layout_id == "process":
        steps = fields.get("steps")
        if isinstance(steps, list):
            for field_name in ("owner", "duration", "output"):
                values = fields.get(field_name)
                if isinstance(values, list) and len(values) != len(steps):
                    errors.append(
                        f"{location}.fields.{field_name}: stepsと件数が"
                        "一致しません"
                    )
    elif layout_id == "matrix-2x2":
        items = fields.get("items")
        if isinstance(items, list):
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                for axis in ("x", "y"):
                    value = item.get(axis)
                    if (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not 0 <= value <= 1
                    ):
                        errors.append(
                            f"{location}.fields.items[{index}].{axis}: "
                            "0〜1の数値にします"
                        )


def validate_spec(spec_data, contracts_data, schema_data=None) -> list[str]:
    errors: list[str] = []
    if schema_data is None:
        schema_data = load_json(SCHEMA_PATH, errors)
    if isinstance(schema_data, dict):
        validate_json_schema(spec_data, schema_data, "root", errors)
    if not isinstance(spec_data, dict):
        return ["ルートがオブジェクトではありません"]
    validate_allowed_keys(spec_data, ROOT_KEYS, "root", errors)
    if spec_data.get("schemaVersion") != "1.0":
        errors.append("schemaVersionは1.0にします")
    brief = spec_data.get("brief")
    if not isinstance(brief, dict):
        errors.append("briefがありません")
    else:
        validate_allowed_keys(brief, BRIEF_KEYS, "brief", errors)
        for key in ("audience", "purpose", "expectedAction", "usage"):
            if key not in brief or is_empty(brief.get(key)):
                errors.append(f"brief.{key}がありません")
        for key in ("audience", "purpose", "expectedAction"):
            if key in brief and not isinstance(brief[key], str):
                errors.append(f"brief.{key}は文字列にします")
        if brief.get("usage") not in ALLOWED_USAGE:
            errors.append(f"brief.usageが不正です: {brief.get('usage')}")
        if "aspectRatio" in brief and not isinstance(brief["aspectRatio"], str):
            errors.append("brief.aspectRatioは文字列にします")
    contracts = contracts_data.get("contracts", {}) if isinstance(contracts_data, dict) else {}
    slides = spec_data.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("slidesがありません")
        return errors
    expected_number = 1
    for index, slide in enumerate(slides):
        location = f"slides[{index}]"
        if not isinstance(slide, dict):
            errors.append(f"{location}: オブジェクトではありません")
            continue
        validate_allowed_keys(slide, SLIDE_KEYS, location, errors)
        for required_key in (
            "number",
            "role",
            "layoutId",
            "actionTitle",
            "fields",
            "evidence",
            "dataClassification",
        ):
            if required_key not in slide:
                errors.append(f"{location}.{required_key}がありません")
        number = slide.get("number")
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or number != expected_number
        ):
            errors.append(
                f"{location}.number: {expected_number}からの連番になっていません"
            )
        expected_number += 1
        if not isinstance(slide.get("role"), str) or not slide.get("role", "").strip():
            errors.append(f"{location}.roleがありません")
        layout_id = slide.get("layoutId")
        contract = contracts.get(layout_id)
        if not isinstance(contract, dict):
            errors.append(f"{location}.layoutId: 未定義です: {layout_id}")
            continue
        title = slide.get("actionTitle")
        if not isinstance(title, str) or not title:
            errors.append(f"{location}.actionTitleがありません")
        else:
            validate_field(
                title,
                contract["fields"]["title"],
                f"{location}.actionTitle",
                errors,
            )
        fields = slide.get("fields")
        if not isinstance(fields, dict):
            errors.append(f"{location}.fieldsがありません")
            continue
        if "title" in fields:
            errors.append(
                f"{location}.fields.titleは使わずactionTitleへ一元化してください"
            )
        allowed_fields = set(contract["fields"]) - {"title"}
        unknown = set(fields) - allowed_fields
        if unknown:
            errors.append(
                f"{location}.fields: 未定義フィールドがあります: {sorted(unknown)}"
            )
        for field_name, field_contract in contract["fields"].items():
            if field_name == "title":
                continue
            if field_contract.get("required") and field_name not in fields:
                errors.append(
                    f"{location}.fields: 必須フィールドがありません: {field_name}"
                )
            if field_name in fields:
                validate_field(
                    fields[field_name],
                    field_contract,
                    f"{location}.fields.{field_name}",
                    errors,
                )
        validate_layout_invariants(layout_id, fields, location, errors)
        evidence = slide.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(item, str) for item in evidence
        ):
            errors.append(f"{location}.evidenceは文字列配列にします")
        sources = slide.get("sources", [])
        if not isinstance(sources, list) or any(
            not isinstance(item, str) for item in sources
        ):
            errors.append(f"{location}.sourcesは文字列配列にします")
        if slide.get("dataClassification") not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{location}.dataClassificationが不正です")
        if "nextRelation" in slide and not isinstance(slide["nextRelation"], str):
            errors.append(f"{location}.nextRelationは文字列にします")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_slide_spec.py <slide-spec.json>")
        return 2
    errors: list[str] = []
    spec_path = Path(sys.argv[1])
    spec_data = load_json(spec_path, errors)
    contracts_data = load_json(CONTRACTS_PATH, errors)
    schema_data = load_json(SCHEMA_PATH, errors)
    if not errors:
        errors.extend(validate_spec(spec_data, contracts_data, schema_data))
    for error in errors:
        print(f"エラー: {error}")
    if errors:
        print(f"検査結果: errors={len(errors)}")
        return 1
    print(
        f"検査結果: slides={len(spec_data['slides'])}, "
        f"layouts={len(contracts_data['contracts'])}, errors=0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
