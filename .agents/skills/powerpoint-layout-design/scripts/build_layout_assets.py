#!/usr/bin/env python3
"""汎用レイアウトのレジストリ、契約、カタログ、評価入力を生成する。"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
REFERENCES = ROOT / "references"
EVALS = ROOT / "evals"


def region(region_id: str, x: float, y: float, width: float, height: float) -> dict:
    return {
        "id": region_id,
        "x": round(x, 5),
        "y": round(y, 5),
        "width": round(width, 5),
        "height": round(height, 5),
    }


def text(
    region_id: str,
    *,
    required: bool = False,
    max_chars: int = 60,
    max_lines: int = 2,
) -> dict:
    return {
        "type": "string",
        "required": required,
        "region": region_id,
        "maxChars": max_chars,
        "maxLines": max_lines,
    }


def text_list(
    region_id: str,
    *,
    required: bool = False,
    min_items: int = 0,
    max_items: int = 4,
    max_chars: int = 40,
    max_total_chars: int | None = None,
) -> dict:
    value = {
        "type": "string-list",
        "required": required,
        "region": region_id,
        "minItems": min_items,
        "maxItems": max_items,
        "maxCharsEach": max_chars,
    }
    if max_total_chars is not None:
        value["maxTotalChars"] = max_total_chars
    return value


def object_field(
    region_id: str,
    *,
    required: bool = False,
    required_keys: tuple[str, ...],
    value_types: dict[str, str],
    max_chars: int = 36,
) -> dict:
    return {
        "type": "object",
        "required": required,
        "region": region_id,
        "requiredKeys": list(required_keys),
        "allowedKeys": list(value_types),
        "valueTypesByKey": value_types,
        "maxCharsPerValue": max_chars,
    }


def object_list(
    region_id: str,
    *,
    required: bool = False,
    min_items: int = 0,
    max_items: int = 5,
    required_keys: tuple[str, ...],
    value_types: dict[str, str],
    max_chars: int = 36,
    max_chars_by_key: dict[str, int] | None = None,
) -> dict:
    value = {
        "type": "object-list",
        "required": required,
        "region": region_id,
        "minItems": min_items,
        "maxItems": max_items,
        "requiredKeys": list(required_keys),
        "allowedKeys": list(value_types),
        "valueTypesByKey": value_types,
        "maxCharsPerValue": max_chars,
    }
    if max_chars_by_key:
        value["maxCharsByKey"] = max_chars_by_key
    return value


def chart_field(
    region_id: str,
    *,
    required: bool = False,
    chart_types: tuple[str, ...],
    max_series: int = 4,
    max_points: int = 12,
) -> dict:
    return {
        "type": "chart",
        "required": required,
        "region": region_id,
        "requiredKeys": ["type", "categories", "series"],
        "allowedKeys": ["type", "categories", "series", "unit", "baseline"],
        "allowedChartTypes": list(chart_types),
        "maxSeries": max_series,
        "maxPoints": max_points,
        "maxPointsByType": {
            "bar": 8,
            "stacked-bar": 8,
            "stacked-column": 8,
            "donut": 6,
            "waterfall": 8,
            "scatter": 12,
            "pareto": 10,
        },
    }


def chart_list(
    region_id: str,
    *,
    required: bool = False,
    min_items: int = 2,
    max_items: int = 4,
    chart_types: tuple[str, ...] = ("line", "bar", "area"),
) -> dict:
    return {
        "type": "chart-list",
        "required": required,
        "region": region_id,
        "minItems": min_items,
        "maxItems": max_items,
        "allowedChartTypes": list(chart_types),
        "maxSeries": 2,
        "maxPoints": 8,
    }


def table_field(
    region_id: str,
    *,
    required: bool = False,
    max_rows: int = 8,
    max_columns: int = 6,
    max_chars: int = 24,
) -> dict:
    return {
        "type": "table",
        "required": required,
        "region": region_id,
        "requiredKeys": ["headers", "values"],
        "allowedKeys": ["headers", "values", "highlightRows", "highlightColumns"],
        "maxRows": max_rows,
        "maxColumns": max_columns,
        "maxCharsPerCell": max_chars,
    }


def media_field(region_id: str, *, required: bool = False) -> dict:
    return {
        "type": "media",
        "required": required,
        "region": region_id,
    }


def media_list(
    region_id: str,
    *,
    required: bool = False,
    min_items: int = 1,
    max_items: int = 4,
) -> dict:
    return {
        "type": "media-list",
        "required": required,
        "region": region_id,
        "minItems": min_items,
        "maxItems": max_items,
    }


def title_contract(max_chars: int = 32) -> dict:
    return text("title", required=True, max_chars=max_chars, max_lines=1)


def variant(
    variant_id: str,
    name_ja: str,
    silhouette: str,
    regions: list[dict],
    *,
    density: str = "standard",
    fixed_chart_type: str | None = None,
) -> dict:
    value = {
        "id": variant_id,
        "nameJa": name_ja,
        "silhouette": silhouette,
        "density": density,
        "regions": regions,
    }
    if fixed_chart_type:
        value["fixedChartType"] = fixed_chart_type
    return value


def standard_regions(*body: str) -> list[dict]:
    regions = [
        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
    ]
    count = max(1, len(body))
    gap = 0.02
    width = (0.8875 - gap * (count - 1)) / count
    for index, item in enumerate(body):
        regions.append(
            region(item, 0.05625 + index * (width + gap), 0.20556, width, 0.64722)
        )
    return regions


def family(
    family_id: str,
    name_ja: str,
    category: str,
    purpose: str,
    use_when: str,
    avoid_when: str,
    contract_fields: dict,
    variants: list[dict],
    selection_example: str,
) -> dict:
    return {
        "id": family_id,
        "nameJa": name_ja,
        "category": category,
        "purpose": purpose,
        "useWhen": use_when,
        "avoidWhen": avoid_when,
        "selectionExample": selection_example,
        "contract": {"fields": contract_fields},
        "variants": variants,
    }


def build_families() -> list[dict]:
    families: list[dict] = []

    families.append(
        family(
            "cover",
            "表紙",
            "structure",
            "資料名、目的、日付、発表者を最小限で示す",
            "資料の開始で、期待する読み方を一目で伝える",
            "目次、免責、長い概要まで表紙へ載せる場合",
            {
                "title": text("title", required=True, max_chars=26, max_lines=2),
                "subtitle": text("subtitle", max_chars=48, max_lines=2),
                "metadata": text_list("metadata", max_items=3, max_chars=30),
                "visual": media_field("visual"),
            },
            [
                variant(
                    "cover-minimal",
                    "最小表紙",
                    "left-title-accent-rail",
                    [
                        region("title", 0.05625, 0.22, 0.57, 0.23),
                        region("subtitle", 0.05625, 0.47, 0.55, 0.11),
                        region("metadata", 0.05625, 0.80, 0.55, 0.08),
                        region("visual", 0.70, 0.10, 0.24375, 0.78),
                    ],
                    density="sparse",
                ),
                variant(
                    "cover-visual",
                    "ビジュアル表紙",
                    "image-field-with-title-overlay",
                    [
                        region("title", 0.05625, 0.21, 0.48, 0.25),
                        region("subtitle", 0.05625, 0.48, 0.45, 0.12),
                        region("metadata", 0.05625, 0.80, 0.44, 0.08),
                        region("visual", 0.55, 0.0, 0.45, 1.0),
                    ],
                    density="sparse",
                ),
            ],
            "新基盤構想を経営会議へ提案する資料の表紙",
        )
    )

    families.append(
        family(
            "agenda",
            "アジェンダ",
            "structure",
            "資料の論理順序と現在位置を示す",
            "四章以上の資料、または読み手が参照しながら読む資料",
            "短い資料でページを増やすだけになる場合",
            {
                "title": title_contract(),
                "items": object_list(
                    "items",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("number", "title"),
                    value_types={
                        "number": "scalar",
                        "title": "string",
                        "description": "string",
                        "status": "string",
                    },
                    max_chars=38,
                    max_chars_by_key={"title": 18, "description": 36},
                ),
            },
            [
                variant(
                    "agenda-overview",
                    "全体アジェンダ",
                    "numbered-stacked-agenda",
                    standard_regions("items"),
                )
            ],
            "全五章の企画提案資料で、章構成を最初に示す",
        )
    )

    families.append(
        family(
            "section-divider",
            "章区切り",
            "structure",
            "論理段階を切り替え、この章で答える問いを示す",
            "長い資料で読み手の認知を切り替える",
            "各ページの前に区切りを置く場合",
            {
                "title": text("title", required=True, max_chars=22, max_lines=1),
                "sectionNumber": text(
                    "sectionNumber", required=True, max_chars=6, max_lines=1
                ),
                "question": text("question", max_chars=48, max_lines=2),
            },
            [
                variant(
                    "section-divider",
                    "章区切り",
                    "dark-field-number-and-question",
                    [
                        region("sectionNumber", 0.05625, 0.24, 0.18, 0.08),
                        region("title", 0.31, 0.30, 0.56, 0.14),
                        region("question", 0.31, 0.48, 0.52, 0.12),
                    ],
                    density="sparse",
                )
            ],
            "分析結果から実行計画へ話題を切り替える",
        )
    )

    families.append(
        family(
            "executive-summary",
            "エグゼクティブサマリー",
            "structure",
            "結論、根拠、求める判断を一枚で示す",
            "詳細を読まない意思決定者にも要点を伝える",
            "後続ページの見出しだけを再掲する場合",
            {
                "title": title_contract(),
                "recommendation": text(
                    "recommendation", required=True, max_chars=72, max_lines=2
                ),
                "evidence": text_list(
                    "evidence",
                    required=True,
                    min_items=2,
                    max_items=3,
                    max_chars=45,
                ),
                "action": text_list(
                    "action",
                    required=True,
                    min_items=1,
                    max_items=2,
                    max_chars=42,
                ),
            },
            [
                variant(
                    "executive-summary",
                    "要約と判断",
                    "recommendation-evidence-decision",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("recommendation", 0.05625, 0.20, 0.8875, 0.13),
                        region("evidence", 0.05625, 0.38, 0.60, 0.42),
                        region("action", 0.69688, 0.38, 0.24687, 0.42),
                    ],
                )
            ],
            "試行導入の結論、三つの根拠、承認事項を一枚で示す",
        )
    )

    families.append(
        family(
            "closing",
            "クロージング",
            "structure",
            "資料冒頭の問いを解決し、次の行動を確定する",
            "提案、報告、研修を意図した結論で閉じる",
            "意味のない謝辞だけで終わる場合",
            {
                "title": title_contract(),
                "resolution": text(
                    "resolution", required=True, max_chars=72, max_lines=2
                ),
                "actions": object_list(
                    "actions",
                    required=True,
                    min_items=1,
                    max_items=3,
                    required_keys=("action",),
                    value_types={
                        "action": "string",
                        "owner": "string",
                        "due": "string",
                    },
                    max_chars=38,
                ),
                "contact": text("contact", max_chars=48, max_lines=1),
            },
            [
                variant(
                    "closing-resolution",
                    "結論と次の一手",
                    "large-resolution-and-actions",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("resolution", 0.10, 0.25, 0.80, 0.20),
                        region("actions", 0.10, 0.53, 0.80, 0.20),
                        region("contact", 0.10, 0.82, 0.80, 0.05),
                    ],
                    density="sparse",
                )
            ],
            "承認後の三つの着手事項で提案資料を閉じる",
        )
    )

    families.append(
        family(
            "appendix",
            "付録",
            "structure",
            "本編を補う詳細、定義、出典を整理する",
            "本編の判断には不要だが参照価値がある情報",
            "主要結論を付録へ隠す場合",
            {
                "title": text("title", required=True, max_chars=34, max_lines=1),
                "detail": text_list(
                    "detail",
                    required=True,
                    min_items=1,
                    max_items=8,
                    max_chars=72,
                ),
                "sources": text_list("sources", max_items=6, max_chars=90),
            },
            [
                variant(
                    "appendix-title",
                    "付録区切り",
                    "appendix-divider",
                    [
                        region("title", 0.10, 0.33, 0.80, 0.15),
                        region("detail", 0.10, 0.54, 0.80, 0.15),
                        region("sources", 0.10, 0.80, 0.80, 0.06),
                    ],
                    density="sparse",
                ),
                variant(
                    "appendix-reference",
                    "付録詳細",
                    "reference-list",
                    standard_regions("detail", "sources"),
                    density="dense",
                ),
            ],
            "用語定義と計算条件を本編から分離する",
        )
    )

    families.append(
        family(
            "key-message",
            "キーメッセージ",
            "narrative",
            "一つの数値、結論、原則を強く記憶させる",
            "複雑な説明の前後で意味を統合する",
            "大きな数字を複数並べる場合",
            {
                "title": title_contract(),
                "message": text("message", required=True, max_chars=24, max_lines=2),
                "support": text("support", max_chars=72, max_lines=2),
                "evidence": text_list("evidence", max_items=2, max_chars=36),
            },
            [
                variant(
                    "key-message",
                    "中央メッセージ",
                    "centered-single-message",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("message", 0.10, 0.28, 0.80, 0.22),
                        region("support", 0.16, 0.55, 0.68, 0.10),
                        region("evidence", 0.25, 0.72, 0.50, 0.08),
                    ],
                    density="sparse",
                ),
                variant(
                    "key-message-split",
                    "メッセージと根拠",
                    "message-left-evidence-right",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("message", 0.05625, 0.27, 0.43, 0.24),
                        region("support", 0.05625, 0.55, 0.43, 0.14),
                        region("evidence", 0.56, 0.27, 0.38375, 0.42),
                    ],
                ),
            ],
            "平均処理時間40%短縮という主要効果を記憶させる",
        )
    )

    families.append(
        family(
            "context-background",
            "背景と前提",
            "narrative",
            "判断に必要な状況、変化、制約を簡潔に共有する",
            "読み手が同じ前提を持っていない場合",
            "一般論を長く並べる場合",
            {
                "title": title_contract(),
                "lead": text("lead", required=True, max_chars=72, max_lines=2),
                "facts": object_list(
                    "facts",
                    required=True,
                    min_items=2,
                    max_items=4,
                    required_keys=("label", "value"),
                    value_types={
                        "label": "string",
                        "value": "scalar",
                        "detail": "string",
                    },
                    max_chars=38,
                ),
                "implication": text(
                    "implication", required=True, max_chars=64, max_lines=2
                ),
            },
            [
                variant(
                    "context-background",
                    "背景と変化",
                    "lead-facts-implication",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("lead", 0.05625, 0.20, 0.8875, 0.12),
                        region("facts", 0.05625, 0.38, 0.8875, 0.30),
                        region("implication", 0.05625, 0.74, 0.8875, 0.10),
                    ],
                )
            ],
            "案件数増加と人員制約を示し、自動化検討の必要性につなげる",
        )
    )

    families.append(
        family(
            "problem-definition",
            "課題定義",
            "narrative",
            "観測事象、原因、影響を分けて問題を定義する",
            "解決策を議論する前に問題の境界を合意する",
            "原因を確認せず症状だけを並べる場合",
            {
                "title": title_contract(),
                "problem": text("problem", required=True, max_chars=70, max_lines=2),
                "symptoms": text_list(
                    "symptoms",
                    required=True,
                    min_items=2,
                    max_items=4,
                    max_chars=36,
                ),
                "causes": text_list(
                    "causes",
                    required=True,
                    min_items=1,
                    max_items=3,
                    max_chars=38,
                ),
                "impact": text("impact", required=True, max_chars=58, max_lines=2),
            },
            [
                variant(
                    "problem-definition",
                    "症状・原因・影響",
                    "problem-causal-chain",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("problem", 0.05625, 0.20, 0.8875, 0.12),
                        region("symptoms", 0.05625, 0.38, 0.27, 0.32),
                        region("causes", 0.365, 0.38, 0.27, 0.32),
                        region("impact", 0.67625, 0.38, 0.2675, 0.32),
                    ],
                )
            ],
            "影響調査の長期化を症状、原因、業務影響に分ける",
        )
    )

    families.append(
        family(
            "objective-scope",
            "目的とスコープ",
            "narrative",
            "達成目標、対象、対象外、成功条件を固定する",
            "プロジェクト開始、提案、調査計画",
            "対象外を曖昧にしたまま合意を求める場合",
            {
                "title": title_contract(),
                "objective": text(
                    "objective", required=True, max_chars=64, max_lines=2
                ),
                "inScope": text_list(
                    "inScope",
                    required=True,
                    min_items=1,
                    max_items=4,
                    max_chars=34,
                ),
                "outOfScope": text_list(
                    "outOfScope", min_items=1, max_items=4, max_chars=34
                ),
                "successMetrics": text_list(
                    "successMetrics",
                    required=True,
                    min_items=1,
                    max_items=3,
                    max_chars=34,
                ),
            },
            [
                variant(
                    "objective-scope",
                    "目的・対象・成功条件",
                    "objective-scope-boundary",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("objective", 0.05625, 0.20, 0.8875, 0.12),
                        region("inScope", 0.05625, 0.39, 0.36, 0.34),
                        region("outOfScope", 0.44, 0.39, 0.27, 0.34),
                        region("successMetrics", 0.735, 0.39, 0.20875, 0.34),
                    ],
                )
            ],
            "対象システム、対象外、完了条件を一枚で合意する",
        )
    )

    families.append(
        family(
            "two-column-explanation",
            "二列説明",
            "narrative",
            "二つの観点、主張と根拠、概念と具体例を並べる",
            "二つの情報群を同時に参照する必要がある",
            "三つ以上の同格要素を無理に二列へ入れる場合",
            {
                "title": title_contract(),
                "leftHeading": text(
                    "leftHeading", required=True, max_chars=18, max_lines=1
                ),
                "leftItems": text_list(
                    "leftItems",
                    required=True,
                    min_items=2,
                    max_items=5,
                    max_chars=38,
                ),
                "rightHeading": text(
                    "rightHeading", required=True, max_chars=18, max_lines=1
                ),
                "rightItems": text_list(
                    "rightItems",
                    required=True,
                    min_items=2,
                    max_items=5,
                    max_chars=38,
                ),
                "takeaway": text("takeaway", max_chars=58, max_lines=2),
            },
            [
                variant(
                    "two-column-balanced",
                    "均等二列",
                    "balanced-two-column",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("leftHeading", 0.05625, 0.22, 0.42, 0.06),
                        region("leftItems", 0.05625, 0.31, 0.42, 0.39),
                        region("rightHeading", 0.52375, 0.22, 0.42, 0.06),
                        region("rightItems", 0.52375, 0.31, 0.42, 0.39),
                        region("takeaway", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                ),
                variant(
                    "two-column-asymmetric",
                    "主従二列",
                    "asymmetric-two-column",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("leftHeading", 0.05625, 0.22, 0.55, 0.06),
                        region("leftItems", 0.05625, 0.31, 0.55, 0.39),
                        region("rightHeading", 0.65, 0.22, 0.29375, 0.06),
                        region("rightItems", 0.65, 0.31, 0.29375, 0.39),
                        region("takeaway", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                ),
            ],
            "設計原則と実装上の注意を二列で説明する",
        )
    )

    families.append(
        family(
            "quote-evidence",
            "引用と意味",
            "narrative",
            "短い引用や一次情報を示し、その意味を説明する",
            "発言、規程、顧客の声が判断根拠になる",
            "出典が確認できない引用を演出に使う場合",
            {
                "title": title_contract(),
                "quote": text("quote", required=True, max_chars=90, max_lines=4),
                "attribution": text(
                    "attribution", required=True, max_chars=42, max_lines=1
                ),
                "implication": text(
                    "implication", required=True, max_chars=64, max_lines=2
                ),
            },
            [
                variant(
                    "quote-evidence",
                    "引用と示唆",
                    "quote-left-implication-right",
                    standard_regions("quote", "implication")
                    + [region("attribution", 0.05625, 0.73, 0.42, 0.06)],
                )
            ],
            "利用部門の発言を示し、要件への影響を説明する",
        )
    )

    families.append(
        family(
            "case-study",
            "ケーススタディ",
            "narrative",
            "状況、実施、結果を一つの事例として示す",
            "再現可能な実績や教訓を説明する",
            "架空の成果を実績として見せる場合",
            {
                "title": title_contract(),
                "situation": text(
                    "situation", required=True, max_chars=58, max_lines=2
                ),
                "action": text_list(
                    "action",
                    required=True,
                    min_items=2,
                    max_items=4,
                    max_chars=38,
                ),
                "result": object_list(
                    "result",
                    required=True,
                    min_items=1,
                    max_items=3,
                    required_keys=("label", "value"),
                    value_types={
                        "label": "string",
                        "value": "scalar",
                        "detail": "string",
                    },
                    max_chars=34,
                ),
                "lesson": text("lesson", max_chars=56, max_lines=2),
            },
            [
                variant(
                    "case-study",
                    "状況・実施・結果",
                    "case-study-three-stage",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("situation", 0.05625, 0.22, 0.26, 0.40),
                        region("action", 0.37, 0.22, 0.27, 0.40),
                        region("result", 0.69, 0.22, 0.25375, 0.40),
                        region("lesson", 0.05625, 0.73, 0.8875, 0.10),
                    ],
                )
            ],
            "試行導入の状況、対応、改善結果、教訓を示す",
        )
    )

    families.append(
        family(
            "comparison",
            "選択肢比較",
            "comparison",
            "複数案を同じ評価軸で比較し、推奨理由を明示する",
            "二つまたは三つの案から選ぶ",
            "案ごとに評価軸や説明量が異なる場合",
            {
                "title": title_contract(),
                "criteria": text_list(
                    "criteria",
                    required=True,
                    min_items=3,
                    max_items=5,
                    max_chars=22,
                ),
                "options": object_list(
                    "options",
                    required=True,
                    min_items=2,
                    max_items=3,
                    required_keys=("name", "values"),
                    value_types={
                        "name": "string",
                        "values": "string-list",
                        "recommended": "boolean",
                    },
                    max_chars=28,
                ),
                "recommendation": text(
                    "recommendation", required=True, max_chars=64, max_lines=2
                ),
            },
            [
                variant(
                    "comparison",
                    "評価表比較",
                    "criteria-table-comparison",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("criteria", 0.05625, 0.22, 0.20, 0.43),
                        region("options", 0.27, 0.22, 0.67375, 0.43),
                        region("recommendation", 0.05625, 0.73, 0.8875, 0.11),
                    ],
                    density="dense",
                ),
                variant(
                    "comparison-side-by-side",
                    "並列比較",
                    "side-by-side-options",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("criteria", 0.05625, 0.74, 0.8875, 0.05),
                        region("options", 0.05625, 0.22, 0.8875, 0.45),
                        region("recommendation", 0.05625, 0.81, 0.8875, 0.06),
                    ],
                ),
            ],
            "三つの導入案を費用、期間、運用負荷で比較する",
        )
    )

    families.append(
        family(
            "before-after",
            "変更前後",
            "comparison",
            "変更前後を同じ観点で比較し、効果を示す",
            "構造、体験、プロセスの改善を示す",
            "左右で比較軸や粒度が異なる場合",
            {
                "title": title_contract(),
                "before": text_list(
                    "before",
                    required=True,
                    min_items=2,
                    max_items=4,
                    max_chars=36,
                    max_total_chars=120,
                ),
                "after": text_list(
                    "after",
                    required=True,
                    min_items=2,
                    max_items=4,
                    max_chars=36,
                    max_total_chars=120,
                ),
                "effect": text_list(
                    "effect",
                    required=True,
                    min_items=1,
                    max_items=3,
                    max_chars=36,
                ),
            },
            [
                variant(
                    "before-after",
                    "Before / After",
                    "balanced-before-after",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("before", 0.05625, 0.23, 0.39, 0.43),
                        region("after", 0.55375, 0.23, 0.39, 0.43),
                        region("effect", 0.05625, 0.74, 0.8875, 0.10),
                    ],
                )
            ],
            "個別受付から一元受付への変更と効果を比較する",
        )
    )

    families.append(
        family(
            "pros-cons",
            "利点と懸念",
            "comparison",
            "一つの案の利点、懸念、成立条件を同じ強さで示す",
            "採用可否をバランスよく議論する",
            "利点だけを強調する営業資料にする場合",
            {
                "title": title_contract(),
                "pros": text_list(
                    "pros",
                    required=True,
                    min_items=2,
                    max_items=5,
                    max_chars=38,
                ),
                "cons": text_list(
                    "cons",
                    required=True,
                    min_items=2,
                    max_items=5,
                    max_chars=38,
                ),
                "condition": text(
                    "condition", required=True, max_chars=64, max_lines=2
                ),
            },
            [
                variant(
                    "pros-cons",
                    "利点・懸念・条件",
                    "pros-cons-condition",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("pros", 0.05625, 0.22, 0.42, 0.43),
                        region("cons", 0.52375, 0.22, 0.42, 0.43),
                        region("condition", 0.05625, 0.73, 0.8875, 0.11),
                    ],
                )
            ],
            "自動化案の利点、懸念、導入条件を整理する",
        )
    )

    families.append(
        family(
            "scorecard",
            "スコアカード",
            "comparison",
            "評価項目ごとの達成度と根拠を一覧化する",
            "同じ基準で複数対象を評価する",
            "根拠のない点数だけを並べる場合",
            {
                "title": title_contract(),
                "items": object_list(
                    "items",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("criterion", "score", "status"),
                    value_types={
                        "criterion": "string",
                        "score": "number",
                        "status": "string",
                        "evidence": "string",
                    },
                    max_chars=34,
                ),
                "summary": text("summary", required=True, max_chars=64, max_lines=2),
            },
            [
                variant(
                    "scorecard",
                    "評価スコア",
                    "criteria-score-evidence",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("items", 0.05625, 0.21, 0.8875, 0.50),
                        region("summary", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                    density="dense",
                )
            ],
            "試行結果を精度、速度、運用性で評価する",
        )
    )

    families.append(
        family(
            "swot",
            "SWOT",
            "comparison",
            "内部要因と外部要因を四象限で整理する",
            "戦略議論で強み、弱み、機会、脅威を区別する",
            "単なる四分類として使い、戦略へ接続しない場合",
            {
                "title": title_contract(),
                "strengths": text_list(
                    "strengths", required=True, min_items=1, max_items=4, max_chars=34
                ),
                "weaknesses": text_list(
                    "weaknesses", required=True, min_items=1, max_items=4, max_chars=34
                ),
                "opportunities": text_list(
                    "opportunities",
                    required=True,
                    min_items=1,
                    max_items=4,
                    max_chars=34,
                ),
                "threats": text_list(
                    "threats", required=True, min_items=1, max_items=4, max_chars=34
                ),
            },
            [
                variant(
                    "swot",
                    "SWOT四象限",
                    "swot-four-quadrant",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("strengths", 0.05625, 0.22, 0.42, 0.27),
                        region("weaknesses", 0.52375, 0.22, 0.42, 0.27),
                        region("opportunities", 0.05625, 0.54, 0.42, 0.27),
                        region("threats", 0.52375, 0.54, 0.42, 0.27),
                    ],
                )
            ],
            "社内基盤の強み、弱み、外部機会、脅威を整理する",
        )
    )

    families.append(
        family(
            "decision-tree",
            "判断ツリー",
            "comparison",
            "条件分岐と最終判断を追跡可能にする",
            "複数条件で対応が変わる",
            "分岐が多すぎて一枚で読めない場合",
            {
                "title": title_contract(),
                "nodes": object_list(
                    "nodes",
                    required=True,
                    min_items=3,
                    max_items=9,
                    required_keys=("id", "label"),
                    value_types={
                        "id": "string",
                        "label": "string",
                        "parentId": "string",
                        "branch": "string",
                        "outcome": "string",
                    },
                    max_chars=28,
                ),
                "rule": text("rule", max_chars=58, max_lines=2),
            },
            [
                variant(
                    "decision-tree",
                    "判断分岐",
                    "top-down-decision-tree",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("nodes", 0.05625, 0.22, 0.8875, 0.50),
                        region("rule", 0.05625, 0.77, 0.8875, 0.08),
                    ],
                )
            ],
            "障害影響と復旧見込みから対応レベルを判定する",
        )
    )

    families.append(
        family(
            "decision-action",
            "意思決定とアクション",
            "comparison",
            "求める決定、条件、担当、期限を明確にする",
            "会議で承認または方針決定を求める",
            "曖昧な確認依頼だけを書く場合",
            {
                "title": title_contract(),
                "decision": text_list(
                    "decision",
                    required=True,
                    min_items=1,
                    max_items=3,
                    max_chars=44,
                ),
                "criteria": text_list(
                    "criteria",
                    required=True,
                    min_items=1,
                    max_items=4,
                    max_chars=36,
                ),
                "actions": object_list(
                    "actions",
                    required=True,
                    min_items=1,
                    max_items=5,
                    required_keys=("action", "owner", "due"),
                    value_types={
                        "action": "string",
                        "owner": "string",
                        "due": "string",
                        "status": "string",
                    },
                    max_chars=34,
                ),
            },
            [
                variant(
                    "decision-action",
                    "決定事項と実行",
                    "decision-banner-action-list",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("decision", 0.05625, 0.20, 0.8875, 0.14),
                        region("criteria", 0.05625, 0.41, 0.34, 0.30),
                        region("actions", 0.44, 0.41, 0.50375, 0.30),
                    ],
                )
            ],
            "試行導入の承認、停止条件、担当と期限を示す",
        )
    )

    families.append(
        family(
            "kpi",
            "KPI",
            "data",
            "主要指標の現在値、変化、目標差を示す",
            "二つまたは三つの重要指標を短時間で確認する",
            "多数の指標をダッシュボード化する場合",
            {
                "title": title_contract(),
                "kpis": object_list(
                    "kpis",
                    required=True,
                    min_items=2,
                    max_items=3,
                    required_keys=("label", "value"),
                    value_types={
                        "label": "string",
                        "value": "scalar",
                        "delta": "scalar",
                        "unit": "string",
                        "status": "string",
                    },
                    max_chars=26,
                ),
                "chart": chart_field(
                    "chart",
                    chart_types=("line", "bar", "area"),
                    max_series=3,
                    max_points=18,
                ),
                "insight": text("insight", max_chars=60, max_lines=2),
            },
            [
                variant(
                    "kpi-trend",
                    "KPIと推移",
                    "kpi-rail-and-trend",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("kpis", 0.05625, 0.22, 0.19, 0.48),
                        region("chart", 0.29, 0.22, 0.65375, 0.48),
                        region("insight", 0.29, 0.75, 0.65375, 0.08),
                    ],
                ),
                variant(
                    "kpi-two",
                    "二つのKPI",
                    "two-large-kpis",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("kpis", 0.10, 0.28, 0.80, 0.30),
                        region("chart", 0.10, 0.63, 0.80, 0.10),
                        region("insight", 0.10, 0.78, 0.80, 0.08),
                    ],
                    density="sparse",
                ),
                variant(
                    "kpi-three",
                    "三つのKPI",
                    "three-large-kpis",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("kpis", 0.05625, 0.25, 0.8875, 0.34),
                        region("chart", 0.05625, 0.64, 0.8875, 0.08),
                        region("insight", 0.05625, 0.77, 0.8875, 0.08),
                    ],
                    density="sparse",
                ),
            ],
            "処理時間、精度、工数の現在値と目標差を示す",
        )
    )

    chart_types = (
        "bar",
        "line",
        "area",
        "stacked-bar",
        "stacked-column",
        "donut",
        "waterfall",
        "scatter",
    )
    chart_regions = [
        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
        region("chart", 0.05625, 0.22, 0.67, 0.52),
        region("insight", 0.77, 0.22, 0.17375, 0.34),
        region("annotation", 0.77, 0.62, 0.17375, 0.12),
    ]
    families.append(
        family(
            "chart-insight",
            "チャートと示唆",
            "data",
            "一つのチャートを主要証拠として結論を説明する",
            "比較、推移、構成、変化、相関を示す",
            "複数チャートを同じ強さで並べる場合",
            {
                "title": title_contract(),
                "chart": chart_field(
                    "chart",
                    required=True,
                    chart_types=chart_types,
                    max_series=4,
                    max_points=18,
                ),
                "insight": text_list(
                    "insight",
                    required=True,
                    min_items=1,
                    max_items=2,
                    max_chars=44,
                ),
                "annotation": text_list(
                    "annotation", max_items=2, max_chars=34
                ),
            },
            [
                variant(
                    "chart-insight",
                    "横棒",
                    "chart-left-insight-right",
                    chart_regions,
                    fixed_chart_type="bar",
                ),
                variant(
                    "chart-insight-line",
                    "折れ線",
                    "chart-left-insight-right",
                    chart_regions,
                    fixed_chart_type="line",
                ),
                variant(
                    "chart-insight-stacked",
                    "積み上げ",
                    "chart-left-insight-right",
                    chart_regions,
                    fixed_chart_type="stacked-column",
                ),
                variant(
                    "chart-insight-waterfall",
                    "ウォーターフォール",
                    "chart-left-insight-right",
                    chart_regions,
                    fixed_chart_type="waterfall",
                ),
                variant(
                    "chart-insight-donut",
                    "構成比",
                    "donut-left-insight-right",
                    chart_regions,
                    fixed_chart_type="donut",
                ),
                variant(
                    "chart-insight-scatter",
                    "散布図",
                    "scatter-left-insight-right",
                    chart_regions,
                    fixed_chart_type="scatter",
                ),
            ],
            "作業区分別の処理時間を横棒で比較し、主要因を説明する",
        )
    )

    families.append(
        family(
            "table-insight",
            "表と示唆",
            "data",
            "正確な値や条件を参照させ、重要な差を説明する",
            "比較表、条件表、詳細数値",
            "大きな表を縮小して一枚へ押し込む場合",
            {
                "title": title_contract(),
                "table": table_field(
                    "table", required=True, max_rows=8, max_columns=6
                ),
                "insight": text_list(
                    "insight",
                    required=True,
                    min_items=1,
                    max_items=2,
                    max_chars=44,
                ),
            },
            [
                variant(
                    "table-insight",
                    "表と示唆",
                    "table-left-insight-right",
                    standard_regions("table", "insight"),
                    density="dense",
                )
            ],
            "三案の費用、期間、運用工数を正確に比較する",
        )
    )

    families.append(
        family(
            "small-multiples",
            "小型複数チャート",
            "data",
            "同じ尺度の小型チャートを並べ、パターン差を比較する",
            "部門別、地域別、商品別の同型データ",
            "尺度や期間が異なるチャートを並べる場合",
            {
                "title": title_contract(),
                "charts": chart_list(
                    "charts",
                    required=True,
                    min_items=2,
                    max_items=4,
                    chart_types=("line", "bar", "area"),
                ),
                "insight": text(
                    "insight", required=True, max_chars=60, max_lines=2
                ),
            },
            [
                variant(
                    "small-multiples",
                    "同型チャート比較",
                    "two-by-two-small-multiples",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("charts", 0.05625, 0.21, 0.8875, 0.52),
                        region("insight", 0.05625, 0.78, 0.8875, 0.08),
                    ],
                )
            ],
            "四部門の月次推移を同じ尺度で比較する",
        )
    )

    families.append(
        family(
            "progress",
            "進捗バー",
            "data",
            "複数項目の現在値と目標を同じ尺度で示す",
            "目標達成率、成熟度、完了率",
            "単位や尺度が異なる項目を混在させる場合",
            {
                "title": title_contract(),
                "items": object_list(
                    "items",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("label", "value", "target"),
                    value_types={
                        "label": "string",
                        "value": "number",
                        "target": "number",
                        "status": "string",
                    },
                    max_chars=26,
                ),
                "insight": text("insight", max_chars=58, max_lines=2),
            },
            [
                variant(
                    "progress-bars",
                    "目標対比バー",
                    "horizontal-progress-bars",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("items", 0.05625, 0.22, 0.8875, 0.48),
                        region("insight", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                )
            ],
            "移行準備の項目別完了率と目標を示す",
        )
    )

    families.append(
        family(
            "pareto",
            "パレート",
            "data",
            "寄与度を降順に並べ、重点対象を特定する",
            "少数要因が全体の大半を占めるか確認する",
            "カテゴリの順序に意味があり並べ替えられない場合",
            {
                "title": title_contract(),
                "chart": chart_field(
                    "chart",
                    required=True,
                    chart_types=("pareto",),
                    max_series=2,
                    max_points=10,
                ),
                "threshold": text(
                    "threshold", required=True, max_chars=42, max_lines=1
                ),
                "insight": text("insight", required=True, max_chars=58, max_lines=2),
            },
            [
                variant(
                    "pareto",
                    "寄与度分析",
                    "pareto-chart-and-threshold",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("chart", 0.05625, 0.22, 0.67, 0.52),
                        region("threshold", 0.77, 0.25, 0.17375, 0.12),
                        region("insight", 0.77, 0.45, 0.17375, 0.22),
                    ],
                )
            ],
            "問い合わせ時間の80%を占める上位三要因を特定する",
        )
    )

    families.append(
        family(
            "matrix-2x2",
            "2×2マトリクス",
            "data",
            "二つの独立した軸で項目を分類し、優先領域を示す",
            "優先順位、ポートフォリオ、リスク分類",
            "軸が曖昧または相互依存する場合",
            {
                "title": title_contract(),
                "axisLabels": object_field(
                    "axisLabels",
                    required=True,
                    required_keys=("xLow", "xHigh", "yLow", "yHigh"),
                    value_types={
                        "xLow": "string",
                        "xHigh": "string",
                        "yLow": "string",
                        "yHigh": "string",
                    },
                    max_chars=18,
                ),
                "items": object_list(
                    "items",
                    required=True,
                    min_items=4,
                    max_items=12,
                    required_keys=("label", "x", "y"),
                    value_types={
                        "label": "string",
                        "x": "number",
                        "y": "number",
                        "status": "string",
                    },
                    max_chars=22,
                ),
                "focus": text_list("focus", max_items=2, max_chars=34),
            },
            [
                variant(
                    "matrix-2x2",
                    "2×2分類",
                    "matrix-left-insight-right",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("axisLabels", 0.05625, 0.22, 0.57, 0.52),
                        region("items", 0.05625, 0.22, 0.57, 0.52),
                        region("focus", 0.68, 0.26, 0.26375, 0.36),
                    ],
                )
            ],
            "効果と実行容易性で施策の着手順を決める",
        )
    )

    families.append(
        family(
            "process",
            "プロセス",
            "process",
            "順序、責任、入力、出力を示す",
            "三から六段階の直線的または部門横断の流れ",
            "複雑な分岐や循環を一列で表す場合",
            {
                "title": title_contract(),
                "steps": object_list(
                    "steps",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("title",),
                    value_types={
                        "title": "string",
                        "description": "string",
                        "owner": "string",
                        "duration": "string",
                        "output": "string",
                        "lane": "string",
                    },
                    max_chars=35,
                    max_chars_by_key={"title": 15, "description": 35},
                ),
                "rule": text("rule", max_chars=58, max_lines=2),
            },
            [
                variant(
                    "process",
                    "横型プロセス",
                    "horizontal-steps",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("steps", 0.05625, 0.27, 0.8875, 0.37),
                        region("rule", 0.05625, 0.74, 0.8875, 0.09),
                    ],
                ),
                variant(
                    "process-vertical",
                    "縦型プロセス",
                    "vertical-steps",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("steps", 0.12, 0.20, 0.48, 0.57),
                        region("rule", 0.67, 0.30, 0.27375, 0.25),
                    ],
                ),
                variant(
                    "process-swimlane",
                    "スイムレーン",
                    "swimlane-process",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("steps", 0.05625, 0.22, 0.8875, 0.51),
                        region("rule", 0.05625, 0.78, 0.8875, 0.07),
                    ],
                    density="dense",
                ),
            ],
            "受付から承認までを担当別スイムレーンで示す",
        )
    )

    families.append(
        family(
            "cycle",
            "循環",
            "process",
            "繰り返し改善する活動とフィードバックを示す",
            "開始点を固定しない反復プロセス",
            "一方向の工程を装飾目的で円環にする場合",
            {
                "title": title_contract(),
                "steps": object_list(
                    "steps",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("title",),
                    value_types={"title": "string", "description": "string"},
                    max_chars=34,
                ),
                "center": text("center", required=True, max_chars=26, max_lines=2),
                "learning": text("learning", max_chars=58, max_lines=2),
            },
            [
                variant(
                    "cycle",
                    "改善サイクル",
                    "radial-cycle",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("steps", 0.12, 0.22, 0.55, 0.54),
                        region("center", 0.30, 0.41, 0.19, 0.14),
                        region("learning", 0.72, 0.34, 0.22375, 0.25),
                    ],
                )
            ],
            "調査、実行、検証、改善を継続的に回す",
        )
    )

    families.append(
        family(
            "value-chain",
            "バリューチェーン",
            "process",
            "価値が段階的に付加される流れと支援要素を示す",
            "業務機能や能力の連鎖を説明する",
            "単なる時間順プロセスを表す場合",
            {
                "title": title_contract(),
                "stages": object_list(
                    "stages",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("title", "value"),
                    value_types={
                        "title": "string",
                        "value": "string",
                        "owner": "string",
                    },
                    max_chars=30,
                ),
                "enablers": text_list(
                    "enablers", min_items=1, max_items=4, max_chars=28
                ),
                "outcome": text("outcome", required=True, max_chars=54, max_lines=2),
            },
            [
                variant(
                    "value-chain",
                    "価値連鎖",
                    "stages-with-enablers",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("stages", 0.05625, 0.25, 0.8875, 0.28),
                        region("enablers", 0.05625, 0.60, 0.8875, 0.10),
                        region("outcome", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                )
            ],
            "データ収集から意思決定までの価値連鎖を示す",
        )
    )

    families.append(
        family(
            "timeline-roadmap",
            "タイムラインと計画",
            "process",
            "時間順の計画、節目、依存関係を示す",
            "ロードマップ、マイルストーン、簡易ガント",
            "詳細タスクをすべて一枚へ載せる場合",
            {
                "title": title_contract(),
                "timeAxis": text_list(
                    "timeAxis",
                    required=True,
                    min_items=3,
                    max_items=8,
                    max_chars=14,
                ),
                "workstreams": object_list(
                    "workstreams",
                    required=True,
                    min_items=1,
                    max_items=5,
                    required_keys=("name", "start", "end"),
                    value_types={
                        "name": "string",
                        "start": "number",
                        "end": "number",
                        "owner": "string",
                        "status": "string",
                    },
                    max_chars=24,
                ),
                "milestones": object_list(
                    "milestones",
                    min_items=1,
                    max_items=8,
                    required_keys=("label", "position"),
                    value_types={
                        "label": "string",
                        "position": "number",
                        "status": "string",
                    },
                    max_chars=24,
                ),
                "decisionPoint": text(
                    "decisionPoint", max_chars=52, max_lines=2
                ),
            },
            [
                variant(
                    "timeline-roadmap",
                    "ロードマップ",
                    "workstream-roadmap",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("timeAxis", 0.23, 0.20, 0.71375, 0.07),
                        region("workstreams", 0.05625, 0.28, 0.8875, 0.42),
                        region("milestones", 0.05625, 0.28, 0.8875, 0.42),
                        region("decisionPoint", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                ),
                variant(
                    "timeline-milestones",
                    "マイルストーン",
                    "single-line-milestones",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("timeAxis", 0.05625, 0.36, 0.8875, 0.08),
                        region("workstreams", 0.05625, 0.47, 0.8875, 0.10),
                        region("milestones", 0.05625, 0.27, 0.8875, 0.32),
                        region("decisionPoint", 0.05625, 0.72, 0.8875, 0.10),
                    ],
                    density="sparse",
                ),
                variant(
                    "timeline-gantt",
                    "簡易ガント",
                    "compact-gantt",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("timeAxis", 0.25, 0.20, 0.69375, 0.07),
                        region("workstreams", 0.05625, 0.28, 0.8875, 0.46),
                        region("milestones", 0.05625, 0.28, 0.8875, 0.46),
                        region("decisionPoint", 0.05625, 0.78, 0.8875, 0.07),
                    ],
                    density="dense",
                ),
            ],
            "要件、構築、試行の三段階と承認点を示す",
        )
    )

    families.append(
        family(
            "hierarchy-pyramid",
            "階層・ピラミッド",
            "process",
            "上位概念と下位要素の階層を示す",
            "戦略、能力、原則の優先階層",
            "時系列や因果関係を表す場合",
            {
                "title": title_contract(),
                "levels": object_list(
                    "levels",
                    required=True,
                    min_items=3,
                    max_items=5,
                    required_keys=("level", "title"),
                    value_types={
                        "level": "scalar",
                        "title": "string",
                        "detail": "string",
                    },
                    max_chars=34,
                ),
                "foundation": text("foundation", max_chars=48, max_lines=2),
            },
            [
                variant(
                    "hierarchy-pyramid",
                    "階層ピラミッド",
                    "layered-pyramid",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("levels", 0.12, 0.22, 0.58, 0.52),
                        region("foundation", 0.75, 0.35, 0.19375, 0.22),
                    ],
                )
            ],
            "目的、原則、標準、実装の階層を示す",
        )
    )

    families.append(
        family(
            "funnel",
            "ファネル",
            "process",
            "段階ごとの絞り込みと残存量を示す",
            "候補選定、案件選別、対象縮小",
            "値が減少しない段階や循環を表す場合",
            {
                "title": title_contract(),
                "stages": object_list(
                    "stages",
                    required=True,
                    min_items=3,
                    max_items=6,
                    required_keys=("label", "value"),
                    value_types={
                        "label": "string",
                        "value": "number",
                        "description": "string",
                    },
                    max_chars=30,
                ),
                "conversion": text("conversion", max_chars=48, max_lines=2),
            },
            [
                variant(
                    "funnel",
                    "絞り込みファネル",
                    "centered-funnel",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("stages", 0.16, 0.22, 0.55, 0.52),
                        region("conversion", 0.76, 0.34, 0.18375, 0.24),
                    ],
                )
            ],
            "候補案件から試行対象までの絞り込みを示す",
        )
    )

    families.append(
        family(
            "architecture",
            "システム構成",
            "technical",
            "主要コンポーネント、境界、責務、接続を示す",
            "システム全体像または層構造を説明する",
            "詳細な物理構成や全通信を一枚へ詰める場合",
            {
                "title": title_contract(),
                "nodes": object_list(
                    "nodes",
                    required=True,
                    min_items=3,
                    max_items=12,
                    required_keys=("id", "label", "layer"),
                    value_types={
                        "id": "string",
                        "label": "string",
                        "layer": "string",
                        "type": "string",
                        "detail": "string",
                    },
                    max_chars=28,
                ),
                "connections": object_list(
                    "connections",
                    required=True,
                    min_items=2,
                    max_items=14,
                    required_keys=("from", "to"),
                    value_types={
                        "from": "string",
                        "to": "string",
                        "label": "string",
                        "direction": "string",
                    },
                    max_chars=22,
                ),
                "insight": text("insight", required=True, max_chars=58, max_lines=2),
            },
            [
                variant(
                    "architecture-layered",
                    "層別アーキテクチャ",
                    "layered-architecture",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("nodes", 0.05625, 0.22, 0.70, 0.50),
                        region("connections", 0.05625, 0.22, 0.70, 0.50),
                        region("insight", 0.80, 0.30, 0.14375, 0.28),
                    ],
                    density="dense",
                ),
                variant(
                    "architecture-system-context",
                    "システムコンテキスト",
                    "system-context-map",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("nodes", 0.10, 0.22, 0.62, 0.52),
                        region("connections", 0.10, 0.22, 0.62, 0.52),
                        region("insight", 0.77, 0.31, 0.17375, 0.26),
                    ],
                ),
            ],
            "上流、統合基盤、下流利用の責務境界を示す",
        )
    )

    families.append(
        family(
            "data-flow-lineage",
            "データフロー",
            "technical",
            "データの発生、変換、保存、利用を追跡可能にする",
            "データリネージ、インターフェース、処理経路",
            "アプリ構成図とデータの流れを混在させる場合",
            {
                "title": title_contract(),
                "nodes": object_list(
                    "nodes",
                    required=True,
                    min_items=3,
                    max_items=10,
                    required_keys=("id", "label", "stage"),
                    value_types={
                        "id": "string",
                        "label": "string",
                        "stage": "string",
                        "system": "string",
                    },
                    max_chars=26,
                ),
                "flows": object_list(
                    "flows",
                    required=True,
                    min_items=2,
                    max_items=12,
                    required_keys=("from", "to", "data"),
                    value_types={
                        "from": "string",
                        "to": "string",
                        "data": "string",
                        "frequency": "string",
                    },
                    max_chars=24,
                ),
                "control": text_list("control", max_items=3, max_chars=32),
            },
            [
                variant(
                    "data-flow-lineage",
                    "データリネージ",
                    "left-to-right-data-flow",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("nodes", 0.05625, 0.24, 0.8875, 0.39),
                        region("flows", 0.05625, 0.24, 0.8875, 0.39),
                        region("control", 0.05625, 0.72, 0.8875, 0.12),
                    ],
                    density="dense",
                )
            ],
            "上流取引からリスク集計、レポートまでの流れを示す",
        )
    )

    families.append(
        family(
            "dependency-map",
            "依存関係",
            "technical",
            "コンポーネント間の依存と変更波及を示す",
            "影響調査、移行計画、障害分析",
            "方向性のない関係を大量に線で結ぶ場合",
            {
                "title": title_contract(),
                "items": object_list(
                    "items",
                    required=True,
                    min_items=4,
                    max_items=12,
                    required_keys=("id", "label", "group"),
                    value_types={
                        "id": "string",
                        "label": "string",
                        "group": "string",
                        "status": "string",
                    },
                    max_chars=24,
                ),
                "dependencies": object_list(
                    "dependencies",
                    required=True,
                    min_items=3,
                    max_items=16,
                    required_keys=("from", "to"),
                    value_types={
                        "from": "string",
                        "to": "string",
                        "type": "string",
                    },
                    max_chars=18,
                ),
                "focus": text("focus", required=True, max_chars=58, max_lines=2),
            },
            [
                variant(
                    "dependency-map",
                    "依存関係マップ",
                    "hub-and-dependency-map",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("items", 0.05625, 0.22, 0.68, 0.51),
                        region("dependencies", 0.05625, 0.22, 0.68, 0.51),
                        region("focus", 0.79, 0.32, 0.15375, 0.25),
                    ],
                    density="dense",
                )
            ],
            "項目変更がジョブ、IF、帳票へ波及する関係を示す",
        )
    )

    families.append(
        family(
            "stakeholder-raci",
            "関係者と責任",
            "governance",
            "関係者の関心、影響力、役割、責任分担を示す",
            "合意形成または実行責任を明確にする",
            "氏名だけを並べ、役割を示さない場合",
            {
                "title": title_contract(),
                "stakeholders": object_list(
                    "stakeholders",
                    required=True,
                    min_items=3,
                    max_items=10,
                    required_keys=("name", "role"),
                    value_types={
                        "name": "string",
                        "role": "string",
                        "influence": "number",
                        "interest": "number",
                        "responsibility": "string",
                    },
                    max_chars=30,
                ),
                "matrix": table_field("matrix", max_rows=8, max_columns=7),
                "engagement": text(
                    "engagement", required=True, max_chars=58, max_lines=2
                ),
            },
            [
                variant(
                    "stakeholder-map",
                    "ステークホルダーマップ",
                    "influence-interest-map",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("stakeholders", 0.05625, 0.22, 0.60, 0.50),
                        region("matrix", 0.05625, 0.22, 0.60, 0.50),
                        region("engagement", 0.71, 0.32, 0.23375, 0.25),
                    ],
                ),
                variant(
                    "raci",
                    "RACI",
                    "raci-table",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("stakeholders", 0.05625, 0.21, 0.22, 0.48),
                        region("matrix", 0.30, 0.21, 0.64375, 0.48),
                        region("engagement", 0.05625, 0.76, 0.8875, 0.09),
                    ],
                    density="dense",
                ),
            ],
            "社員、協力会社、利用部門の責任分担をRACIで示す",
        )
    )

    families.append(
        family(
            "risk-status",
            "リスクと状態",
            "governance",
            "リスクの大きさ、状態、担当、対応を示す",
            "プロジェクト報告、移行判定、統制確認",
            "根拠のない色だけで状態を示す場合",
            {
                "title": title_contract(),
                "risks": object_list(
                    "risks",
                    required=True,
                    min_items=3,
                    max_items=10,
                    required_keys=("risk", "status"),
                    value_types={
                        "risk": "string",
                        "likelihood": "number",
                        "impact": "number",
                        "status": "string",
                        "owner": "string",
                        "response": "string",
                    },
                    max_chars=32,
                ),
                "summary": text("summary", required=True, max_chars=58, max_lines=2),
            },
            [
                variant(
                    "risk-matrix",
                    "リスクマトリクス",
                    "likelihood-impact-matrix",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("risks", 0.05625, 0.22, 0.62, 0.51),
                        region("summary", 0.73, 0.33, 0.21375, 0.24),
                    ],
                ),
                variant(
                    "rag-status",
                    "RAGステータス",
                    "rag-status-list",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("risks", 0.05625, 0.21, 0.8875, 0.50),
                        region("summary", 0.05625, 0.77, 0.8875, 0.08),
                    ],
                    density="dense",
                ),
            ],
            "移行リスクを発生可能性と影響度で評価する",
        )
    )

    families.append(
        family(
            "visual-story",
            "画像中心",
            "visual",
            "画像を主要な証拠または状況説明として使う",
            "現場、製品、画面、成果物を具体的に見せる",
            "意味のない装飾写真で空白を埋める場合",
            {
                "title": title_contract(),
                "visuals": media_list(
                    "visuals", required=True, min_items=1, max_items=4
                ),
                "headline": text(
                    "headline", required=True, max_chars=46, max_lines=2
                ),
                "body": text("body", max_chars=90, max_lines=4),
                "captions": text_list("captions", max_items=4, max_chars=28),
            },
            [
                variant(
                    "image-left",
                    "画像左",
                    "image-left-content-right",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("visuals", 0.05625, 0.21, 0.52, 0.58),
                        region("headline", 0.62, 0.27, 0.32375, 0.15),
                        region("body", 0.62, 0.47, 0.32375, 0.24),
                        region("captions", 0.05625, 0.81, 0.52, 0.05),
                    ],
                ),
                variant(
                    "image-right",
                    "画像右",
                    "content-left-image-right",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("visuals", 0.42375, 0.21, 0.52, 0.58),
                        region("headline", 0.05625, 0.27, 0.32375, 0.15),
                        region("body", 0.05625, 0.47, 0.32375, 0.24),
                        region("captions", 0.42375, 0.81, 0.52, 0.05),
                    ],
                ),
                variant(
                    "image-hero",
                    "全面ビジュアル",
                    "hero-image-overlay",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("visuals", 0.05625, 0.19, 0.8875, 0.64),
                        region("headline", 0.10, 0.52, 0.56, 0.15),
                        region("body", 0.10, 0.69, 0.56, 0.10),
                        region("captions", 0.72, 0.78, 0.18, 0.04),
                    ],
                    density="sparse",
                ),
                variant(
                    "image-gallery",
                    "画像ギャラリー",
                    "three-image-gallery",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("visuals", 0.05625, 0.22, 0.8875, 0.42),
                        region("headline", 0.05625, 0.70, 0.8875, 0.08),
                        region("body", 0.05625, 0.78, 0.8875, 0.06),
                        region("captions", 0.05625, 0.65, 0.8875, 0.04),
                    ],
                ),
            ],
            "現行画面と改善後の利用場面を画像で具体化する",
        )
    )

    families.append(
        family(
            "issue-action-log",
            "課題と対応",
            "governance",
            "課題、状態、担当、期限、対応を一枚で管理する",
            "会議で重要課題を追跡する",
            "全チケットを一覧化して可読性を失う場合",
            {
                "title": title_contract(),
                "issues": object_list(
                    "issues",
                    required=True,
                    min_items=3,
                    max_items=8,
                    required_keys=("issue", "status", "owner", "due", "action"),
                    value_types={
                        "issue": "string",
                        "status": "string",
                        "owner": "string",
                        "due": "string",
                        "action": "string",
                    },
                    max_chars=30,
                ),
                "escalation": text(
                    "escalation", required=True, max_chars=56, max_lines=2
                ),
            },
            [
                variant(
                    "issue-action-log",
                    "重要課題一覧",
                    "issue-action-table",
                    [
                        region("title", 0.05625, 0.06667, 0.8875, 0.08333),
                        region("issues", 0.05625, 0.21, 0.8875, 0.51),
                        region("escalation", 0.05625, 0.78, 0.8875, 0.08),
                    ],
                    density="dense",
                )
            ],
            "重要課題の状態、担当、期限、エスカレーションを示す",
        )
    )

    return families


def build_registry(families: list[dict]) -> dict:
    layouts = []
    family_summaries = []
    order = 1
    for item in families:
        fields = item["contract"]["fields"]
        required = [
            name for name, field in fields.items() if field.get("required") is True
        ]
        optional = [name for name in fields if name not in required]
        variant_ids = []
        for item_variant in item["variants"]:
            variant_ids.append(item_variant["id"])
            layouts.append(
                {
                    "id": item_variant["id"],
                    "familyId": item["id"],
                    "contractId": item["id"],
                    "nameJa": item_variant["nameJa"],
                    "category": item["category"],
                    "purpose": item["purpose"],
                    "useWhen": item["useWhen"],
                    "avoidWhen": item["avoidWhen"],
                    "silhouette": item_variant["silhouette"],
                    "density": item_variant["density"],
                    "required": required,
                    "optional": optional,
                    "capacity": {
                        "titleChars": fields["title"].get("maxChars", 32),
                        "primaryFields": max(1, len(fields) - 1),
                    },
                    "regions": item_variant["regions"],
                    "overflowAction": (
                        "本文を短くする、ページを分ける、詳細を付録へ移す。"
                        "自動縮小や自動レイアウト変更は行わない"
                    ),
                    "previewOrder": order,
                    **(
                        {"fixedChartType": item_variant["fixedChartType"]}
                        if "fixedChartType" in item_variant
                        else {}
                    ),
                }
            )
            order += 1
        family_summaries.append(
            {
                "id": item["id"],
                "nameJa": item["nameJa"],
                "category": item["category"],
                "purpose": item["purpose"],
                "useWhen": item["useWhen"],
                "avoidWhen": item["avoidWhen"],
                "contractId": item["id"],
                "defaultLayoutId": variant_ids[0],
                "layoutIds": variant_ids,
            }
        )

    return {
        "schemaVersion": "2.0",
        "coordinateSystem": {
            "origin": "top-left",
            "unit": "ratio",
            "range": [0, 1],
            "note": "x、y、width、heightをスライド幅・高さへ乗算する",
        },
        "counts": {
            "families": len(family_summaries),
            "layouts": len(layouts),
        },
        "selectionPolicy": {
            "selectionOrder": [
                "communication-job",
                "content-relationship",
                "family-capacity",
                "visual-variation",
            ],
            "automaticFallback": False,
            "adjacentSilhouetteRule": (
                "同じsilhouetteを三ページ以上連続させない。ただし意味構造を"
                "変えてまで見た目を変えない"
            ),
            "note": (
                "最初にfamilyIdを決め、次に内容量と前後ページを見てlayoutIdを選ぶ。"
                "容量超過時は内容を削る、分割する、付録へ移す"
            ),
        },
        "renderingPolicy": {
            "regionOrder": (
                "regions配列の順に描画し、線や接続はノードより先に描画する"
            ),
            "defaultInnerPaddingPx": 16,
            "textAutoFit": "none",
            "overflowOrder": [
                "remove-nonessential-content",
                "move-detail-to-appendix",
                "split-slide",
                "choose-layout-manually",
            ],
            "measurement": (
                "文字数上限は一次ゲート。実フォントで計測し、全ページを"
                "レンダリングして最終判定する"
            ),
        },
        "common": {
            "safeArea": {
                "x": 0.05625,
                "y": 0.06667,
                "width": 0.8875,
                "height": 0.875,
            },
            "title": {
                "x": 0.05625,
                "y": 0.06667,
                "width": 0.8875,
                "height": 0.08333,
                "capacity": {"maxChars": 32, "maxLines": 1},
            },
            "content": {
                "x": 0.05625,
                "y": 0.19028,
                "width": 0.8875,
                "height": 0.68611,
            },
            "footer": {
                "x": 0.05625,
                "y": 0.89722,
                "width": 0.8875,
                "height": 0.04444,
            },
        },
        "families": family_summaries,
        "layouts": layouts,
    }


def build_contracts(families: list[dict]) -> dict:
    return {
        "schemaVersion": "2.0",
        "purpose": (
            "レイアウトファミリーごとの入力型、必須項目、容量を"
            "社内アダプターへ渡す実装契約"
        ),
        "measurementPolicy": {
            "characterCount": "Unicodeコードポイント数を一次ゲートに使う",
            "lineCount": (
                "明示改行を数え、自動折返しは実フォント計測と"
                "レンダリングで判定する"
            ),
            "finalGate": (
                "文字数検査に合格しても、自動縮小を使わず"
                "全ページをレンダリングして確認する"
            ),
        },
        "fieldTypes": [
            "string",
            "string-list",
            "object",
            "object-list",
            "chart",
            "chart-list",
            "table",
            "media",
            "media-list",
        ],
        "contracts": {
            item["id"]: item["contract"]
            for item in families
        },
    }


def build_catalog(families: list[dict]) -> str:
    lines = [
        "# レイアウト・カタログ",
        "",
        "`assets/layout-registry.json` の40ファミリーと各バリエーションに対応する。",
        "最初に内容の関係からファミリーを選び、その後に情報量と前後ページを見て",
        "具体的なレイアウトIDを選ぶ。",
        "",
        "## 選択手順",
        "",
        "1. 読み手に何を理解、判断、実行してほしいかを一文で定義する。",
        "2. 内容の関係を、構造、物語、比較、データ、プロセス、技術、統制、画像から選ぶ。",
        "3. 該当ファミリーの `useWhen` と `avoidWhen` を確認する。",
        "4. 必須フィールドと容量を `layout-contracts.json` で確認する。",
        "5. 情報量と前後ページのシルエットから具体的なレイアウトIDを選ぶ。",
        "6. 容量超過時は削る、分ける、付録へ移す。自動縮小は使わない。",
        "",
        "## 一覧",
        "",
        "| 分類 | ファミリー | 主なレイアウトID | 用途 |",
        "|---|---|---|---|",
    ]
    for item in families:
        variant_ids = "、".join(f"`{value['id']}`" for value in item["variants"])
        lines.append(
            f"| {item['category']} | `{item['id']}` | {variant_ids} | "
            f"{item['purpose']} |"
        )
    lines.extend(
        [
            "",
            "## 共通ルール",
            "",
            "- ページタイトルは原則として上部左揃え、一行にする。",
            "- 同じレイアウトIDでは余白、順序、色の意味を変えない。",
            "- 同じシルエットを三ページ以上続けない。",
            "- 見た目を変えるためだけに意味構造を変えない。",
            "- 図の接続線はノードより先に生成し、線を背面へ置く。",
            "- 例示データは明示し、事実として扱わない。",
            "",
        ]
    )
    for index, item in enumerate(families, start=1):
        lines.extend(
            [
                f"## {index}. `{item['id']}` — {item['nameJa']}",
                "",
                f"- 目的: {item['purpose']}",
                f"- 使う: {item['useWhen']}",
                f"- 避ける: {item['avoidWhen']}",
                "- レイアウト: "
                + "、".join(
                    f"`{value['id']}`（{value['nameJa']}）"
                    for value in item["variants"]
                ),
                f"- 選択例: {item['selectionExample']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_selection_evals(families: list[dict]) -> list[dict]:
    return [
        {
            "id": f"select-{index:02d}",
            "prompt": item["selectionExample"],
            "expectedFamilyId": item["id"],
            "allowedLayoutIds": [value["id"] for value in item["variants"]],
            "mustExplain": [
                "内容の関係",
                "容量",
                "前後ページとのシルエット",
            ],
        }
        for index, item in enumerate(families, start=1)
    ]


def build_example_spec() -> dict:
    return {
        "schemaVersion": "2.0",
        "brief": {
            "audience": "経営会議メンバー",
            "purpose": "影響調査自動化の試行導入について判断してもらう",
            "expectedAction": "二部門で六週間の試行を承認する",
            "usage": "projection",
            "aspectRatio": "16:9",
        },
        "slides": [
            {
                "number": 1,
                "role": "導入",
                "layoutId": "cover-minimal",
                "actionTitle": "影響調査自動化の試行導入",
                "fields": {
                    "subtitle": "判断速度と統制を両立する実行案",
                    "metadata": ["経営会議", "2026年7月", "企画部"],
                },
                "evidence": [],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "判断事項の全体像を示す",
            },
            {
                "number": 2,
                "role": "構成",
                "layoutId": "agenda-overview",
                "actionTitle": "四つの論点から試行導入の妥当性を確認する",
                "fields": {
                    "items": [
                        {"number": 1, "title": "背景", "description": "現在の制約"},
                        {"number": 2, "title": "解決案", "description": "仕組みと統制"},
                        {"number": 3, "title": "検証", "description": "効果とリスク"},
                        {"number": 4, "title": "判断", "description": "実行条件"},
                    ]
                },
                "evidence": [],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "結論を先に示す",
            },
            {
                "number": 3,
                "role": "要約",
                "layoutId": "executive-summary",
                "actionTitle": "二部門で六週間試行し、統制指標を確認してから拡大する",
                "fields": {
                    "recommendation": "対象を限定し、再現率と証跡品質を基準に段階導入する",
                    "evidence": [
                        "探索と照合を分離できる",
                        "差分を機械的に記録できる",
                        "承認前に人が確認できる",
                    ],
                    "action": ["試行開始を承認", "終了判定条件を合意"],
                },
                "evidence": ["例示条件"],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "試行プロセスを具体化する",
            },
            {
                "number": 4,
                "role": "プロセス",
                "layoutId": "process-swimlane",
                "actionTitle": "申請から承認までを三者の責任で管理する",
                "fields": {
                    "steps": [
                        {"title": "申請", "owner": "依頼部門", "lane": "利用部門"},
                        {"title": "列挙", "owner": "AI", "lane": "自動処理"},
                        {"title": "照合", "owner": "AI", "lane": "自動処理"},
                        {"title": "確認", "owner": "担当者", "lane": "IT部門"},
                        {"title": "承認", "owner": "責任者", "lane": "IT部門"},
                    ],
                    "rule": "承認前に根拠と未確認事項を必ず表示する",
                },
                "evidence": ["例示フロー"],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "技術構成へ接続する",
            },
            {
                "number": 5,
                "role": "構成",
                "layoutId": "architecture-layered",
                "actionTitle": "調査エンジンと証跡保管を分離して統制する",
                "fields": {
                    "nodes": [
                        {"id": "source", "label": "ソース", "layer": "入力"},
                        {"id": "catalog", "label": "カタログ", "layer": "知識"},
                        {"id": "engine", "label": "調査エンジン", "layer": "処理"},
                        {"id": "evidence", "label": "証跡", "layer": "出力"},
                    ],
                    "connections": [
                        {"from": "source", "to": "engine", "label": "解析"},
                        {"from": "catalog", "to": "engine", "label": "照合"},
                        {"from": "engine", "to": "evidence", "label": "記録"},
                    ],
                    "insight": "入力と出力を固定し、推論だけを交換可能にする",
                },
                "evidence": ["例示構成"],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "リスクを評価する",
            },
            {
                "number": 6,
                "role": "リスク",
                "layoutId": "risk-matrix",
                "actionTitle": "分類誤りと根拠欠落を優先的に抑える",
                "fields": {
                    "risks": [
                        {
                            "risk": "分類誤り",
                            "likelihood": 4,
                            "impact": 5,
                            "status": "red",
                            "owner": "設計責任者",
                        },
                        {
                            "risk": "根拠欠落",
                            "likelihood": 3,
                            "impact": 5,
                            "status": "red",
                            "owner": "品質責任者",
                        },
                        {
                            "risk": "処理遅延",
                            "likelihood": 2,
                            "impact": 2,
                            "status": "green",
                            "owner": "運用担当",
                        },
                    ],
                    "summary": "高リスク二項目を試行終了条件へ組み込む",
                },
                "evidence": ["例示評価"],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "最終判断を求める",
            },
            {
                "number": 7,
                "role": "判断",
                "layoutId": "decision-action",
                "actionTitle": "試行開始と終了判定条件の承認をお願いしたい",
                "fields": {
                    "decision": ["二部門・六週間の試行を開始する"],
                    "criteria": ["再現率95%以上", "重大な根拠欠落0件"],
                    "actions": [
                        {
                            "action": "対象案件を確定",
                            "owner": "企画部",
                            "due": "8月5日",
                        },
                        {
                            "action": "評価手順を確定",
                            "owner": "品質管理",
                            "due": "8月8日",
                        },
                    ],
                },
                "evidence": ["例示計画"],
                "sources": [],
                "dataClassification": "illustrative",
                "nextRelation": "終了",
            },
        ],
    }


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    families = build_families()
    registry = build_registry(families)
    contracts = build_contracts(families)
    if registry["counts"] != {"families": 40, "layouts": 62}:
        raise RuntimeError(f"件数が想定外です: {registry['counts']}")
    write_json(ASSETS / "layout-registry.json", registry)
    write_json(ASSETS / "layout-contracts.json", contracts)
    write_json(EVALS / "layout-selection-cases.json", build_selection_evals(families))
    write_json(EVALS / "example-slide-spec.json", build_example_spec())
    (REFERENCES / "layout-catalog.md").write_text(
        build_catalog(families).rstrip() + "\n",
        encoding="utf-8",
    )
    print(
        "生成完了: "
        f"families={registry['counts']['families']}, "
        f"layouts={registry['counts']['layouts']}"
    )


if __name__ == "__main__":
    main()
