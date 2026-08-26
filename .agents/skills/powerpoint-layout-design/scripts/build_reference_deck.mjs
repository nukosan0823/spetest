#!/usr/bin/env node
/**
 * 40ファミリー・62レイアウトの編集可能な参照PPTXと検査用画像を生成する。
 * 表示データはすべて架空であり、外部アセットを使わない。
 */

import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { pathToFileURL } from "node:url";

async function loadArtifactTool() {
  try {
    return await import("@oai/artifact-tool");
  } catch (error) {
    if (error?.code !== "ERR_MODULE_NOT_FOUND") throw error;
    const requireFromWorkingDirectory = createRequire(
      path.join(process.cwd(), "package.json"),
    );
    const resolved = requireFromWorkingDirectory.resolve("@oai/artifact-tool");
    return import(pathToFileURL(resolved).href);
  }
}

const { Presentation, PresentationFile } = await loadArtifactTool();

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(SCRIPT_DIR, "..");
const ASSET_DIR = path.join(SKILL_DIR, "assets");
const REGISTRY_PATH = path.join(ASSET_DIR, "layout-registry.json");
const OUTPUT_PPTX = path.join(ASSET_DIR, "reference-layouts.pptx");
const OUTPUT_PREVIEW = path.join(ASSET_DIR, "layout-preview.png");
const renderArgIndex = process.argv.indexOf("--render-dir");
const RENDER_DIR =
  renderArgIndex >= 0 && process.argv[renderArgIndex + 1]
    ? path.resolve(process.argv[renderArgIndex + 1])
    : path.resolve(SKILL_DIR, ".reference-render");

const W = 1280;
const H = 720;
const FONT = "Yu Gothic";
const C = {
  bg: "#F7F8FA",
  surface: "#FFFFFF",
  ink: "#17324D",
  body: "#2E3B47",
  muted: "#697786",
  faint: "#EEF2F6",
  rule: "#DCE2E8",
  accent: "#2F6BFF",
  accentDark: "#1D4ED8",
  accentSoft: "#EAF0FF",
  teal: "#00A6A6",
  tealSoft: "#E2F7F6",
  warning: "#F4A340",
  warningSoft: "#FFF2DB",
  danger: "#D94A4A",
  dangerSoft: "#FCE8E8",
  positive: "#23856D",
  positiveSoft: "#E4F3EE",
  white: "#FFFFFF",
};

let shapeSequence = 0;

function nextName(prefix) {
  shapeSequence += 1;
  return `${prefix}-${String(shapeSequence).padStart(4, "0")}`;
}

function px(n) {
  return Math.round(n * 100) / 100;
}

function rect(slide, position, fill, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "rect",
    name: nextName(options.name ?? "shape"),
    position,
    fill,
    line: {
      style: "solid",
      fill: options.lineFill ?? "none",
      width: options.lineWidth ?? 0,
    },
    ...(options.borderRadius ? { borderRadius: options.borderRadius } : {}),
  });
}

function rule(slide, left, top, width, color = C.rule, height = 1) {
  return rect(
    slide,
    { left, top, width, height },
    color,
    { name: "rule" },
  );
}

function text(slide, value, position, options = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    name: nextName(options.name ?? "text"),
    position,
    fill: options.fill ?? "none",
    line: {
      style: "solid",
      fill: options.lineFill ?? "none",
      width: options.lineWidth ?? 0,
    },
  });
  box.text = String(value);
  box.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 22,
    color: options.color ?? C.body,
    bold: options.bold ?? false,
    alignment: options.align ?? "left",
    verticalAlignment: options.vertical ?? "top",
    lineSpacing: options.lineSpacing ?? 1.2,
    autoFit: "none",
    wrap: "square",
    insets: options.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

function title(slide, value) {
  text(slide, value, { left: 72, top: 44, width: 1136, height: 66 }, {
    fontSize: 47,
    bold: true,
    color: C.ink,
    vertical: "middle",
    name: "title",
  });
  rule(slide, 72, 119, 1136, C.rule, 1);
}

function label(slide, value, left, top, color = C.accent) {
  text(slide, value, { left, top, width: 250, height: 24 }, {
    fontSize: 14,
    bold: true,
    color,
    name: "label",
  });
}

function footer(slide, layout, index) {
  rule(slide, 72, 664, 1136, C.rule, 1);
  text(
    slide,
    `${layout.id}  |  ${layout.category}  |  架空データ`,
    { left: 72, top: 672, width: 850, height: 22 },
    { fontSize: 13, color: C.muted, vertical: "middle", name: "footer" },
  );
  text(
    slide,
    String(index + 1).padStart(2, "0"),
    { left: 1132, top: 672, width: 76, height: 22 },
    {
      fontSize: 13,
      color: C.muted,
      align: "right",
      vertical: "middle",
      name: "page-number",
    },
  );
}

function base(slide, layout, index, titleText) {
  slide.background.fill = C.bg;
  shapeSequence = index * 1000;
  label(slide, "POWERPOINT LAYOUT SYSTEM", 72, 20);
  text(
    slide,
    layout.nameJa,
    { left: 1030, top: 20, width: 178, height: 24 },
    { fontSize: 13, color: C.muted, align: "right", name: "layout-name" },
  );
  title(slide, titleText);
  footer(slide, layout, index);
  slide.speakerNotes.textFrame.setText(
    "[Sources]\n- 架空の例示データ。外部資料・外部画像は使用していない。",
  );
  slide.speakerNotes.setVisible(true);
}

function panel(slide, left, top, width, height, options = {}) {
  return rect(
    slide,
    { left, top, width, height },
    options.fill ?? C.surface,
    {
      name: options.name ?? "panel",
      lineFill: options.lineFill ?? C.rule,
      lineWidth: options.lineWidth ?? 1,
      geometry: options.geometry ?? "rect",
      borderRadius: options.borderRadius,
    },
  );
}

function bulletList(slide, items, position, options = {}) {
  const gap = options.gap ?? 14;
  const itemHeight = options.itemHeight ?? 44;
  items.forEach((item, i) => {
    const top = position.top + i * (itemHeight + gap);
    rect(
      slide,
      { left: position.left, top: top + 11, width: 7, height: 7 },
      options.dotColor ?? C.accent,
      { name: "bullet" },
    );
    text(
      slide,
      item,
      {
        left: position.left + 20,
        top,
        width: position.width - 20,
        height: itemHeight,
      },
      {
        fontSize: options.fontSize ?? 22,
        color: options.color ?? C.body,
        bold: options.bold ?? false,
        vertical: "middle",
        name: "bullet-text",
      },
    );
  });
}

function metric(slide, labelText, valueText, left, top, width, options = {}) {
  panel(slide, left, top, width, options.height ?? 160, {
    fill: options.fill ?? C.surface,
    lineFill: options.lineFill ?? C.rule,
    name: "metric-panel",
  });
  text(
    slide,
    labelText,
    { left: left + 18, top: top + 18, width: width - 36, height: 28 },
    { fontSize: 16, color: C.muted, bold: true, name: "metric-label" },
  );
  text(
    slide,
    valueText,
    { left: left + 18, top: top + 52, width: width - 36, height: 66 },
    {
      fontSize: options.valueSize ?? 46,
      color: options.color ?? C.accent,
      bold: true,
      vertical: "middle",
      name: "metric-value",
    },
  );
  if (options.note) {
    text(
      slide,
      options.note,
      { left: left + 18, top: top + 122, width: width - 36, height: 24 },
      { fontSize: 14, color: C.muted, name: "metric-note" },
    );
  }
}

function callout(slide, value, left, top, width, options = {}) {
  panel(slide, left, top, width, options.height ?? 72, {
    fill: options.fill ?? C.accentSoft,
    lineFill: options.lineFill ?? "none",
    name: "callout",
  });
  text(
    slide,
    value,
    {
      left: left + 18,
      top: top + 10,
      width: width - 36,
      height: (options.height ?? 72) - 20,
    },
    {
      fontSize: options.fontSize ?? 20,
      bold: options.bold ?? true,
      color: options.color ?? C.ink,
      vertical: "middle",
      name: "callout-text",
    },
  );
}

function heading(slide, value, left, top, width, color = C.ink) {
  text(slide, value, { left, top, width, height: 34 }, {
    fontSize: 20,
    bold: true,
    color,
    vertical: "middle",
    name: "section-heading",
  });
}

function statusColor(status) {
  if (status === "red" || status === "遅延" || status === "要対応") return C.danger;
  if (status === "amber" || status === "注意" || status === "確認中") return C.warning;
  return C.positive;
}

function imagePlaceholder(slide, left, top, width, height, number) {
  panel(slide, left, top, width, height, {
    fill: number % 2 ? C.ink : C.accentDark,
    lineFill: "none",
    name: "image-placeholder",
  });
  rect(
    slide,
    { left: left + width * 0.08, top: top + height * 0.14, width: width * 0.30, height: height * 0.52 },
    number % 2 ? C.accent : C.teal,
    { name: "image-accent" },
  );
  rect(
    slide,
    { left: left + width * 0.48, top: top + height * 0.28, width: width * 0.42, height: height * 0.12 },
    C.white,
    { name: "image-rule" },
  );
  rect(
    slide,
    { left: left + width * 0.48, top: top + height * 0.47, width: width * 0.28, height: height * 0.08 },
    number % 2 ? C.teal : C.warning,
    { name: "image-rule" },
  );
  text(
    slide,
    `VISUAL ${String(number).padStart(2, "0")}`,
    { left: left + width * 0.48, top: top + height * 0.64, width: width * 0.38, height: 32 },
    { fontSize: 18, bold: true, color: C.white, name: "image-label" },
  );
}

function chartCommon(position) {
  return {
    position,
    chartFill: C.bg,
    plotAreaFill: C.bg,
    plotAreaLine: { style: "solid", fill: "none", width: 0 },
    hasLegend: false,
  };
}

function addBarChart(slide, position, horizontal = true, stacked = false) {
  slide.charts.add("bar", {
    ...chartCommon(position),
    categories: ["手作業", "内部確認", "例外対応", "承認"],
    series: stacked
      ? [
          { name: "自動", values: [6, 4, 3, 2], fill: C.accent },
          { name: "人", values: [8, 7, 5, 3], fill: C.teal },
        ]
      : [{ name: "時間", values: [18, 10, 7, 4], fill: C.accent }],
    barOptions: {
      direction: horizontal ? "bar" : "column",
      grouping: stacked ? "stacked" : "clustered",
      gapWidth: 55,
    },
    xAxis: {
      visible: true,
      textStyle: { fill: C.muted, fontSize: 12 },
      majorGridlines: { style: "solid", fill: C.rule, width: 1 },
      line: { style: "solid", fill: C.rule, width: 1 },
    },
    yAxis: {
      visible: true,
      textStyle: { fill: C.body, fontSize: 13 },
      line: { style: "solid", fill: C.rule, width: 1 },
    },
    dataLabels: {
      showValue: !stacked,
      position: "outEnd",
      textStyle: { fill: C.ink, fontSize: 12, bold: true },
    },
    ...(stacked
      ? { legend: { position: "bottom", overlay: false, textStyle: { fill: C.muted, fontSize: 12 } }, hasLegend: true }
      : {}),
  });
}

function addLineChart(slide, position, compact = false) {
  slide.charts.add("line", {
    ...chartCommon(position),
    categories: compact ? ["1", "2", "3", "4", "5", "6"] : ["2月", "3月", "4月", "5月", "6月", "7月"],
    series: [
      {
        name: "平均日数",
        values: [5.0, 4.7, 4.4, 4.0, 3.7, 3.2],
        line: { style: "solid", fill: C.accent, width: 3 },
        marker: { symbol: "circle", size: 5 },
      },
    ],
    xAxis: {
      textStyle: { fill: C.muted, fontSize: compact ? 9 : 12 },
      line: { style: "solid", fill: C.rule, width: 1 },
    },
    yAxis: {
      min: 0,
      max: 6,
      textStyle: { fill: C.muted, fontSize: compact ? 9 : 12 },
      majorGridlines: { style: "solid", fill: C.rule, width: 1 },
      line: { style: "solid", fill: C.rule, width: 1 },
    },
  });
}

function addDonut(slide, position) {
  slide.charts.add("doughnut", {
    ...chartCommon(position),
    categories: ["自動処理", "人による確認", "例外対応"],
    series: [
      {
        name: "構成比",
        values: [58, 30, 12],
        points: [
          { idx: 0, fill: C.accent },
          { idx: 1, fill: C.teal },
          { idx: 2, fill: C.warning },
        ],
      },
    ],
    doughnutOptions: { holeSize: 64, firstSliceAngle: 270 },
    dataLabels: {
      showPercent: true,
      showCategoryName: true,
      position: "outEnd",
      textStyle: { fill: C.body, fontSize: 12 },
    },
  });
}

function addWaterfall(slide, position) {
  const chartLeft = position.left + 40;
  const chartTop = position.top + 28;
  const chartWidth = position.width - 60;
  const chartHeight = position.height - 72;
  const bottom = chartTop + chartHeight;
  const maxValue = 110;
  const yOf = (value) => bottom - (value / maxValue) * chartHeight;
  const categories = ["現状", "自動化", "標準化", "例外増", "改善後"];
  const bars = [
    { start: 0, end: 100, label: "100", fill: C.accent },
    { start: 100, end: 68, label: "−32", fill: C.teal },
    { start: 68, end: 47, label: "−21", fill: C.teal },
    { start: 47, end: 55, label: "+8", fill: C.warning },
    { start: 0, end: 55, label: "55", fill: C.accentDark },
  ];
  const step = chartWidth / categories.length;
  const barWidth = 60;

  for (let tick = 0; tick <= 100; tick += 20) {
    const y = yOf(tick);
    rule(slide, chartLeft, y, chartWidth, C.rule, 1);
    text(slide, String(tick), { left: chartLeft - 38, top: y - 10, width: 30, height: 20 }, {
      fontSize: 11,
      color: C.muted,
      align: "right",
      name: "waterfall-axis-label",
    });
  }

  bars.forEach((bar, i) => {
    const x = chartLeft + i * step + (step - barWidth) / 2;
    const top = yOf(Math.max(bar.start, bar.end));
    const height = Math.max(4, Math.abs(yOf(bar.start) - yOf(bar.end)));
    if (i > 0 && i < bars.length - 1) {
      const previousLevel = bars[i - 1].end;
      rule(slide, x - (step - barWidth), yOf(previousLevel), step - barWidth, C.muted, 1);
    }
    rect(slide, { left: x, top, width: barWidth, height }, bar.fill, {
      name: "waterfall-bar",
    });
    text(slide, bar.label, { left: x - 20, top: top - 24, width: barWidth + 40, height: 20 }, {
      fontSize: 12,
      bold: true,
      color: C.ink,
      align: "center",
      name: "waterfall-value",
    });
    text(slide, categories[i], {
      left: chartLeft + i * step,
      top: bottom + 10,
      width: step,
      height: 22,
    }, {
      fontSize: 12,
      color: C.body,
      align: "center",
      name: "waterfall-category",
    });
  });
}

function addScatter(slide, position) {
  slide.charts.add("scatter", {
    ...chartCommon(position),
    series: [
      {
        name: "施策",
        xValues: [2, 4, 5, 7, 8, 9],
        values: [4, 8, 3, 7, 6, 9],
        marker: { symbol: "circle", size: 9 },
        fill: C.accent,
      },
    ],
    scatterOptions: { style: "marker", varyColors: false },
    xAxis: {
      min: 0,
      max: 10,
      title: "実行容易性",
      textStyle: { fill: C.muted, fontSize: 11 },
      majorGridlines: { style: "solid", fill: C.rule, width: 1 },
    },
    yAxis: {
      min: 0,
      max: 10,
      title: "期待効果",
      textStyle: { fill: C.muted, fontSize: 11 },
      majorGridlines: { style: "solid", fill: C.rule, width: 1 },
    },
  });
}

function addTable(slide, values, position, options = {}) {
  const table = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: position.left,
    top: position.top,
    width: position.width,
    height: position.height,
    values,
  });
  table.borders.assign({ style: "solid", fill: C.rule, width: 1 });
  for (let c = 0; c < values[0].length; c += 1) {
    const cell = table.getCell(0, c);
    cell.fill = C.ink;
    cell.text.style = {
      typeface: FONT,
      fontSize: options.headerSize ?? 15,
      bold: true,
      color: C.white,
      alignment: c === 0 ? "left" : "center",
      verticalAlignment: "middle",
    };
  }
  for (let r = 1; r < values.length; r += 1) {
    for (let c = 0; c < values[r].length; c += 1) {
      const cell = table.getCell(r, c);
      cell.fill = r % 2 ? C.surface : C.faint;
      cell.text.style = {
        typeface: FONT,
        fontSize: options.bodySize ?? 14,
        color: C.body,
        alignment: c === 0 ? "left" : "center",
        verticalAlignment: "middle",
      };
    }
  }
  return table;
}

function drawCover(slide, layout, index) {
  slide.background.fill = C.bg;
  shapeSequence = index * 1000;
  if (layout.id === "cover-visual") {
    imagePlaceholder(slide, 704, 0, 576, 720, 1);
    rect(slide, { left: 0, top: 0, width: 760, height: 720 }, C.bg, { name: "cover-field" });
  } else {
    rect(slide, { left: 918, top: 0, width: 362, height: 720 }, C.ink, { name: "cover-rail" });
    rect(slide, { left: 918, top: 0, width: 7, height: 720 }, C.accent, { name: "cover-accent" });
    text(slide, "62", { left: 982, top: 164, width: 220, height: 110 }, {
      fontSize: 76,
      bold: true,
      color: C.white,
      align: "center",
      vertical: "middle",
      name: "layout-count",
    });
    text(slide, "LAYOUTS", { left: 982, top: 270, width: 220, height: 32 }, {
      fontSize: 16,
      bold: true,
      color: C.white,
      align: "center",
      name: "layout-label",
    });
  }
  label(slide, "REFERENCE DECK / 16:9", 72, 44);
  text(slide, "日本語PowerPoint\n汎用レイアウト集", { left: 72, top: 190, width: 640, height: 170 }, {
    fontSize: 68,
    bold: true,
    color: C.ink,
    lineSpacing: 1.05,
    vertical: "middle",
    name: "cover-title",
  });
  text(slide, "40ファミリー・62レイアウトを、意味構造と容量契約で選択する", {
    left: 72, top: 390, width: 620, height: 76,
  }, { fontSize: 23, color: C.body, lineSpacing: 1.35, name: "cover-subtitle" });
  rule(slide, 72, 542, 620, C.rule, 1);
  text(slide, "2026年7月  |  clean-room original", { left: 72, top: 566, width: 620, height: 30 }, {
    fontSize: 15, color: C.muted, name: "cover-meta",
  });
  text(slide, layout.id, { left: 72, top: 652, width: 400, height: 24 }, {
    fontSize: 13, color: C.muted, name: "cover-layout-id",
  });
  slide.speakerNotes.textFrame.setText("[Sources]\n- 架空の例示データ。外部資料・外部画像は使用していない。");
  slide.speakerNotes.setVisible(true);
}

function drawAgenda(slide, layout, index) {
  base(slide, layout, index, "四つの論点から試行導入の妥当性を確認する");
  const items = [
    ["01", "背景と課題", "なぜ今、変更が必要か"],
    ["02", "解決の仕組み", "何を標準化するか"],
    ["03", "効果とリスク", "何を検証するか"],
    ["04", "実行計画", "何を決めるか"],
  ];
  items.forEach((item, i) => {
    const y = 164 + i * 112;
    text(slide, item[0], { left: 96, top: y, width: 88, height: 62 }, {
      fontSize: 30, bold: true, color: i === 0 ? C.accent : C.muted, vertical: "middle", name: "agenda-number",
    });
    text(slide, item[1], { left: 206, top: y, width: 300, height: 62 }, {
      fontSize: 26, bold: true, color: C.ink, vertical: "middle", name: "agenda-title",
    });
    text(slide, item[2], { left: 566, top: y, width: 540, height: 62 }, {
      fontSize: 20, color: C.body, vertical: "middle", name: "agenda-description",
    });
    if (i < items.length - 1) rule(slide, 96, y + 78, 1010, C.rule, 1);
  });
}

function drawSection(slide, layout, index) {
  slide.background.fill = C.ink;
  shapeSequence = index * 1000;
  text(slide, "02", { left: 72, top: 180, width: 220, height: 120 }, {
    fontSize: 92, bold: true, color: "#295073", name: "section-number",
  });
  text(slide, "解決の仕組み", { left: 390, top: 236, width: 720, height: 90 }, {
    fontSize: 54, bold: true, color: C.white, vertical: "middle", name: "section-title",
  });
  rule(slide, 390, 350, 180, C.accent, 5);
  text(slide, "どの責任境界なら、速度と統制を両立できるか", {
    left: 390, top: 385, width: 680, height: 96,
  }, { fontSize: 26, color: "#D8E4EF", name: "section-question" });
  text(slide, layout.id, { left: 72, top: 666, width: 360, height: 24 }, {
    fontSize: 13, color: "#9DB3C8", name: "section-layout-id",
  });
  text(slide, String(index + 1).padStart(2, "0"), { left: 1132, top: 666, width: 76, height: 24 }, {
    fontSize: 13, color: "#9DB3C8", align: "right", name: "section-page",
  });
  slide.speakerNotes.textFrame.setText("[Sources]\n- 架空の例示データ。外部資料・外部画像は使用していない。");
  slide.speakerNotes.setVisible(true);
}

function drawExecutiveSummary(slide, layout, index) {
  base(slide, layout, index, "二部門で試行し、統制確認後に対象を拡大する");
  callout(slide, "推奨：対象を限定し、再現率と証跡品質を基準に段階導入する", 72, 146, 1136, {
    height: 84, fill: C.accentSoft, fontSize: 22,
  });
  const evidence = [
    ["01", "母集団の可視化", "抜け漏れを機械的に検知"],
    ["02", "統制の維持", "承認前に根拠を表示"],
    ["03", "小さく検証", "対象と期間を限定"],
  ];
  evidence.forEach((item, i) => {
    const y = 286 + i * 88;
    text(slide, item[0], { left: 84, top: y, width: 50, height: 40 }, {
      fontSize: 17, bold: true, color: C.accent, vertical: "middle", name: "evidence-number",
    });
    text(slide, item[1], { left: 148, top: y, width: 250, height: 40 }, {
      fontSize: 21, bold: true, color: C.ink, vertical: "middle", name: "evidence-title",
    });
    text(slide, item[2], { left: 410, top: y, width: 310, height: 40 }, {
      fontSize: 18, color: C.body, vertical: "middle", name: "evidence-body",
    });
    if (i < 2) rule(slide, 84, y + 56, 636, C.rule, 1);
  });
  panel(slide, 786, 286, 382, 254, { fill: C.ink, lineFill: "none", name: "decision-panel" });
  label(slide, "承認いただきたいこと", 816, 314, "#BFD1E1");
  text(slide, "試行導入を\n8月に開始する", { left: 816, top: 364, width: 300, height: 96 }, {
    fontSize: 34, bold: true, color: C.white, lineSpacing: 1.1, name: "decision",
  });
  text(slide, "対象：2部門 / 期間：6週間", { left: 816, top: 492, width: 300, height: 28 }, {
    fontSize: 16, color: "#BFD1E1", name: "decision-meta",
  });
}

function drawClosing(slide, layout, index) {
  base(slide, layout, index, "試行の承認後、三つの準備を直ちに開始する");
  text(slide, "小さく始め、測定し、統制を確認してから広げる", {
    left: 128, top: 180, width: 1024, height: 110,
  }, { fontSize: 42, bold: true, color: C.ink, align: "center", vertical: "middle", name: "resolution" });
  const actions = [
    ["01", "対象案件を確定", "企画部 / 8月5日"],
    ["02", "評価手順を固定", "品質管理 / 8月8日"],
    ["03", "試行環境を準備", "開発部 / 8月12日"],
  ];
  actions.forEach((item, i) => {
    const x = 104 + i * 362;
    panel(slide, x, 352, 320, 170, { fill: i === 0 ? C.accentSoft : C.surface, name: "action-panel" });
    text(slide, item[0], { left: x + 20, top: 374, width: 60, height: 32 }, {
      fontSize: 18, bold: true, color: C.accent, name: "action-number",
    });
    text(slide, item[1], { left: x + 20, top: 420, width: 280, height: 46 }, {
      fontSize: 23, bold: true, color: C.ink, name: "action-title",
    });
    text(slide, item[2], { left: x + 20, top: 480, width: 280, height: 28 }, {
      fontSize: 15, color: C.muted, name: "action-meta",
    });
  });
}

function drawAppendix(slide, layout, index) {
  if (layout.id === "appendix-title") {
    slide.background.fill = C.bg;
    shapeSequence = index * 1000;
    label(slide, "APPENDIX", 72, 52);
    text(slide, "付録：定義と計算条件", { left: 128, top: 250, width: 1024, height: 100 }, {
      fontSize: 54, bold: true, color: C.ink, align: "center", vertical: "middle", name: "appendix-title",
    });
    rule(slide, 480, 382, 320, C.accent, 4);
    text(slide, "本編の判断を補う参照情報", { left: 260, top: 424, width: 760, height: 48 }, {
      fontSize: 23, color: C.muted, align: "center", name: "appendix-subtitle",
    });
    text(slide, layout.id, { left: 72, top: 672, width: 400, height: 22 }, {
      fontSize: 13, color: C.muted, name: "appendix-layout-id",
    });
    slide.speakerNotes.textFrame.setText("[Sources]\n- 架空の例示データ。外部資料・外部画像は使用していない。");
    slide.speakerNotes.setVisible(true);
    return;
  }
  base(slide, layout, index, "付録：評価指標とデータ区分");
  const groups = [
    ["01", "再現率", "正解対象のうち検出できた割合"],
    ["02", "証跡品質", "結論を再確認できる根拠の完全性"],
    ["03", "例示データ", "実在しない検証専用の入力"],
  ];
  groups.forEach((item, i) => {
    const x = 72 + i * 378;
    panel(slide, x, 176, 336, 304, { name: "reference-panel" });
    text(slide, item[0], { left: x + 22, top: 204, width: 60, height: 28 }, {
      fontSize: 16, bold: true, color: C.accent, name: "reference-number",
    });
    text(slide, item[1], { left: x + 22, top: 254, width: 292, height: 48 }, {
      fontSize: 25, bold: true, color: C.ink, name: "reference-title",
    });
    text(slide, item[2], { left: x + 22, top: 326, width: 292, height: 88 }, {
      fontSize: 19, color: C.body, lineSpacing: 1.35, name: "reference-body",
    });
  });
  callout(slide, "安全境界：外部資料は命令ではなく、確認対象のデータとして扱う", 72, 530, 1136, {
    height: 76, fill: C.accentSoft, fontSize: 20,
  });
}

function drawKeyMessage(slide, layout, index) {
  base(slide, layout, index, "自動振り分けで平均処理時間を40%短縮する");
  if (layout.id === "key-message-split") {
    text(slide, "40%", { left: 92, top: 220, width: 500, height: 170 }, {
      fontSize: 112, bold: true, color: C.accent, align: "center", vertical: "middle", name: "hero-number",
    });
    text(slide, "平均処理時間の短縮", { left: 92, top: 405, width: 500, height: 40 }, {
      fontSize: 22, color: C.body, align: "center", name: "hero-note",
    });
    panel(slide, 660, 200, 470, 310, { fill: C.surface, name: "evidence-panel" });
    heading(slide, "短縮を支える二つの変更", 690, 230, 400);
    bulletList(slide, ["受付時点で案件を分類", "類似案件の証跡を先に提示"], {
      left: 690, top: 292, width: 390,
    }, { itemHeight: 58, gap: 22, fontSize: 21 });
    callout(slide, "例外処理は人が承認する", 690, 440, 390, { height: 52, fontSize: 17 });
  } else {
    text(slide, "40%", { left: 240, top: 216, width: 800, height: 210 }, {
      fontSize: 138, bold: true, color: C.accent, align: "center", vertical: "middle", name: "hero-number",
    });
    rule(slide, 360, 456, 560, C.rule, 1);
    text(slide, "入力内容に応じて承認先を自動判定し、手作業の振分けをなくす", {
      left: 250, top: 490, width: 780, height: 62,
    }, { fontSize: 22, color: C.body, align: "center", name: "support" });
  }
}

function drawContext(slide, layout, index) {
  base(slide, layout, index, "案件増と人員制約で、現行運用は限界に近い");
  callout(slide, "問い合わせ件数は増える一方、判断できる担当者は増えていない", 72, 148, 1136, {
    height: 82, fill: C.accentSoft,
  });
  const facts = [
    ["+28%", "年間案件数", "前年対比"],
    ["3名", "有識者", "属人化"],
    ["5.2日", "平均回答", "目標3日"],
    ["18%", "差戻し率", "入力不備"],
  ];
  facts.forEach((item, i) => {
    const x = 72 + i * 284;
    metric(slide, item[1], item[0], x, 286, 254, {
      height: 170, note: item[2], color: i === 2 ? C.warning : C.accent,
    });
  });
  callout(slide, "示唆：受付、証跡提示、承認を分離し、担当者は判断へ集中する", 72, 520, 1136, {
    height: 72, fill: C.ink, color: C.white, fontSize: 20,
  });
}

function drawProblem(slide, layout, index) {
  base(slide, layout, index, "影響調査の長期化は、役割の混在が原因である");
  callout(slide, "問題：同じ担当者が探索から承認まで抱え、待ち時間が連鎖する", 72, 148, 1136, {
    height: 74, fill: C.dangerSoft, color: C.ink,
  });
  const columns = [
    ["観測事象", ["回答が遅い", "調査範囲が揺れる", "再確認が増える"], C.muted],
    ["主要原因", ["母集団が未定義", "根拠形式が不統一", "責任境界が曖昧"], C.accent],
    ["業務影響", ["案件判断が遅延", "手戻りが発生", "監査説明が困難"], C.danger],
  ];
  columns.forEach((column, i) => {
    const x = 72 + i * 378;
    panel(slide, x, 278, 336, 262, { fill: C.surface, name: "cause-panel" });
    rect(slide, { left: x, top: 278, width: 8, height: 262 }, column[2], { name: "cause-accent" });
    heading(slide, column[0], x + 28, 302, 280);
    bulletList(slide, column[1], { left: x + 28, top: 354, width: 274 }, {
      itemHeight: 36, gap: 12, fontSize: 18, dotColor: column[2],
    });
  });
}

function drawObjective(slide, layout, index) {
  base(slide, layout, index, "対象と完了条件を固定し、試行を評価可能にする");
  callout(slide, "目的：影響調査の再現率と証跡品質を、限定範囲で検証する", 72, 148, 1136, {
    height: 76,
  });
  const blocks = [
    ["対象", ["バッチジョブ", "主要IF", "変更案件20件"], C.accentSoft, C.accent],
    ["対象外", ["本番自動承認", "顧客データ", "全社展開"], C.faint, C.muted],
    ["成功条件", ["再現率95%以上", "重大欠落0件", "工数30%削減"], C.positiveSoft, C.positive],
  ];
  const widths = [420, 310, 342];
  let x = 72;
  blocks.forEach((block, i) => {
    panel(slide, x, 278, widths[i], 282, { fill: block[2], lineFill: "none", name: "scope-panel" });
    heading(slide, block[0], x + 24, 306, widths[i] - 48, block[3]);
    bulletList(slide, block[1], { left: x + 24, top: 362, width: widths[i] - 48 }, {
      itemHeight: 38, gap: 14, fontSize: 19, dotColor: block[3],
    });
    x += widths[i] + 32;
  });
}

function drawTwoColumn(slide, layout, index) {
  base(slide, layout, index, "AIは探索を広げ、人は根拠と判断を担う");
  const asymmetric = layout.id === "two-column-asymmetric";
  const leftW = asymmetric ? 700 : 540;
  const rightX = asymmetric ? 814 : 668;
  const rightW = asymmetric ? 394 : 540;
  panel(slide, 72, 160, leftW, 420, { fill: C.surface, name: "left-column" });
  panel(slide, rightX, 160, rightW, 420, { fill: asymmetric ? C.ink : C.surface, name: "right-column" });
  heading(slide, "AIが担うこと", 100, 190, leftW - 56, C.accent);
  bulletList(slide, ["母集団を広く列挙", "依存関係を照合", "根拠候補を整形", "未確認事項を明示"], {
    left: 100, top: 250, width: leftW - 56,
  }, { itemHeight: 40, gap: 14, fontSize: 20 });
  heading(slide, "人が担うこと", rightX + 28, 190, rightW - 56, asymmetric ? C.white : C.ink);
  bulletList(slide, ["前提の確認", "影響の判断", "最終承認"], {
    left: rightX + 28, top: 250, width: rightW - 56,
  }, {
    itemHeight: 42,
    gap: 16,
    fontSize: 20,
    color: asymmetric ? C.white : C.body,
    dotColor: asymmetric ? C.teal : C.accent,
  });
  callout(slide, "境界を分けることで、速度と統制を両立する", 72, 602, 1136, {
    height: 48, fill: C.accentSoft, fontSize: 18,
  });
}

function drawQuote(slide, layout, index) {
  base(slide, layout, index, "利用部門は、速さより判断根拠を求めている");
  panel(slide, 72, 170, 650, 360, { fill: C.ink, lineFill: "none", name: "quote-panel" });
  text(slide, "“", { left: 102, top: 180, width: 92, height: 92 }, {
    fontSize: 90, bold: true, color: C.accent, name: "quote-mark",
  });
  text(slide, "早い回答だけでなく、\nなぜ影響がないと言えるのかを\n確認できる状態にしてほしい。", {
    left: 132, top: 260, width: 540, height: 180,
  }, { fontSize: 30, bold: true, color: C.white, lineSpacing: 1.25, name: "quote" });
  text(slide, "利用部門ヒアリング（架空）", { left: 132, top: 470, width: 500, height: 28 }, {
    fontSize: 15, color: "#BFD1E1", name: "quote-attribution",
  });
  heading(slide, "要件への意味", 786, 200, 350, C.accent);
  bulletList(slide, ["結論と根拠を同じ画面に出す", "未確認事項を隠さない", "承認履歴を残す"], {
    left: 786, top: 264, width: 350,
  }, { itemHeight: 46, gap: 18, fontSize: 20 });
}

function drawCaseStudy(slide, layout, index) {
  base(slide, layout, index, "受付標準化だけで処理時間を32%短縮できた");
  const blocks = [
    ["01", "状況", "受付内容が自由記述で、担当振分けに時間を要していた"],
    ["02", "実施", "入力項目を標準化し、類似案件の証跡候補を提示した"],
    ["03", "結果", "平均処理時間を5.0日から3.4日へ短縮した"],
  ];
  blocks.forEach((block, i) => {
    const x = 72 + i * 378;
    panel(slide, x, 176, 336, 330, { fill: i === 2 ? C.accentSoft : C.surface, name: "case-panel" });
    text(slide, block[0], { left: x + 24, top: 200, width: 60, height: 30 }, {
      fontSize: 16, bold: true, color: C.accent, name: "case-number",
    });
    text(slide, block[1], { left: x + 24, top: 252, width: 280, height: 48 }, {
      fontSize: 26, bold: true, color: C.ink, name: "case-heading",
    });
    text(slide, block[2], { left: x + 24, top: 324, width: 288, height: 130 }, {
      fontSize: 20, color: C.body, lineSpacing: 1.35, name: "case-body",
    });
  });
  callout(slide, "教訓：AI導入前に、入力と判断条件を標準化する", 72, 548, 1136, {
    height: 62, fill: C.ink, color: C.white, fontSize: 19,
  });
}

function drawComparison(slide, layout, index) {
  base(slide, layout, index, "案Bは初期費用が高いが、運用負荷を抑える");
  if (layout.id === "comparison-side-by-side") {
    const cards = [
      ["案A", "現行拡張", ["初期費用：低", "期間：2か月", "運用負荷：高"], false],
      ["案B", "段階導入", ["初期費用：中", "期間：3か月", "運用負荷：低"], true],
      ["案C", "全面刷新", ["初期費用：高", "期間：8か月", "運用負荷：中"], false],
    ];
    cards.forEach((card, i) => {
      const x = 72 + i * 378;
      panel(slide, x, 170, 336, 356, {
        fill: card[3] ? C.accentSoft : C.surface,
        lineFill: card[3] ? C.accent : C.rule,
        lineWidth: card[3] ? 2 : 1,
        name: "comparison-card",
      });
      label(slide, card[0], x + 24, 196, card[3] ? C.accent : C.muted);
      text(slide, card[1], { left: x + 24, top: 240, width: 288, height: 48 }, {
        fontSize: 27, bold: true, color: C.ink, name: "option-title",
      });
      bulletList(slide, card[2], { left: x + 24, top: 318, width: 288 }, {
        itemHeight: 38, gap: 15, fontSize: 18,
      });
    });
  } else {
    addTable(slide, [
      ["評価軸", "案A", "案B", "案C"],
      ["初期費用", "低", "中", "高"],
      ["導入期間", "2か月", "3か月", "8か月"],
      ["運用負荷", "高", "低", "中"],
      ["拡張性", "中", "高", "高"],
      ["移行リスク", "低", "低", "高"],
    ], { left: 72, top: 164, width: 1136, height: 354 }, { bodySize: 16 });
  }
  callout(slide, "推奨：案B。段階導入で統制を維持しながら効果を検証する", 72, 556, 1136, {
    height: 62, fill: C.ink, color: C.white, fontSize: 19,
  });
}

function drawBeforeAfter(slide, layout, index) {
  base(slide, layout, index, "受付から承認までを一つの流れへ統合する");
  panel(slide, 72, 176, 470, 356, { fill: C.surface, name: "before-panel" });
  panel(slide, 738, 176, 470, 356, { fill: C.accentSoft, lineFill: C.accent, lineWidth: 2, name: "after-panel" });
  label(slide, "BEFORE / 現状", 98, 200, C.muted);
  label(slide, "AFTER / 改善", 764, 200, C.accent);
  bulletList(slide, ["メールで受付", "担当者が手動振分け", "進捗は個別に確認", "例外処理の記録が分散"], {
    left: 108, top: 260, width: 390,
  }, { itemHeight: 38, gap: 14, fontSize: 19, dotColor: C.muted });
  bulletList(slide, ["共通フォームで受付", "条件により自動振分け", "状態を一画面で追跡", "例外と承認履歴を保存"], {
    left: 774, top: 260, width: 390,
  }, { itemHeight: 38, gap: 14, fontSize: 19, dotColor: C.accent });
  rect(slide, { left: 602, top: 312, width: 76, height: 76 }, C.ink, { geometry: "ellipse", name: "transition" });
  text(slide, "→", { left: 602, top: 312, width: 76, height: 76 }, {
    fontSize: 36, bold: true, color: C.white, align: "center", vertical: "middle", name: "transition-arrow",
  });
  callout(slide, "効果：待ち時間を減らし、監査可能性を高める", 304, 568, 672, {
    height: 52, fill: C.ink, color: C.white, fontSize: 18,
  });
}

function drawProsCons(slide, layout, index) {
  base(slide, layout, index, "段階導入には、評価条件の固定が前提となる");
  panel(slide, 72, 176, 540, 354, { fill: C.positiveSoft, lineFill: "none", name: "pros-panel" });
  panel(slide, 668, 176, 540, 354, { fill: C.dangerSoft, lineFill: "none", name: "cons-panel" });
  heading(slide, "利点", 104, 204, 460, C.positive);
  heading(slide, "懸念", 700, 204, 460, C.danger);
  bulletList(slide, ["初期リスクを限定", "実データで効果を測定", "利用部門の学習を反映"], {
    left: 104, top: 270, width: 460,
  }, { itemHeight: 46, gap: 18, fontSize: 21, dotColor: C.positive });
  bulletList(slide, ["対象外へ効果を一般化できない", "暫定運用が二重化", "評価設計に手間が必要"], {
    left: 700, top: 270, width: 460,
  }, { itemHeight: 46, gap: 18, fontSize: 21, dotColor: C.danger });
  callout(slide, "成立条件：再現率、証跡品質、運用工数の判定基準を開始前に固定する", 72, 560, 1136, {
    height: 62, fill: C.ink, color: C.white, fontSize: 19,
  });
}

function drawScorecard(slide, layout, index) {
  base(slide, layout, index, "品質は合格だが、例外処理は追加改善が必要だ");
  const rows = [
    ["評価項目", "スコア", "状態", "根拠"],
    ["再現率", "96", "合格", "正解対象25件中24件"],
    ["証跡品質", "92", "合格", "重大な根拠欠落0件"],
    ["処理時間", "88", "合格", "平均40%短縮"],
    ["例外処理", "68", "要改善", "手動確認が多い"],
    ["操作性", "84", "合格", "利用者8名が評価"],
  ];
  addTable(slide, rows, { left: 72, top: 160, width: 1136, height: 382 }, { bodySize: 15 });
  callout(slide, "総括：例外処理を改善してから対象部門を拡大する", 72, 570, 1136, {
    height: 52, fill: C.accentSoft, fontSize: 18,
  });
}

function drawSwot(slide, layout, index) {
  base(slide, layout, index, "運用知識を活かし、属人化と外部変化に備える");
  const blocks = [
    ["S / 強み", ["豊富な運用知識", "既存証跡が蓄積"], C.accentSoft, C.accent],
    ["W / 弱み", ["担当者へ依存", "資料形式が不統一"], C.faint, C.muted],
    ["O / 機会", ["生成AIの高度化", "標準化需要の増加"], C.positiveSoft, C.positive],
    ["T / 脅威", ["規制変更の増加", "人材確保の難化"], C.warningSoft, C.warning],
  ];
  blocks.forEach((block, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 72 + col * 568;
    const y = 162 + row * 226;
    panel(slide, x, y, 536, 194, { fill: block[2], lineFill: "none", name: "swot-panel" });
    heading(slide, block[0], x + 24, y + 20, 480, block[3]);
    bulletList(slide, block[1], { left: x + 24, top: y + 74, width: 480 }, {
      itemHeight: 34, gap: 8, fontSize: 18, dotColor: block[3],
    });
  });
}

function drawDecisionTree(slide, layout, index) {
  base(slide, layout, index, "影響度と復旧見込みで対応レベルを判定する");
  rule(slide, 640, 210, 1, C.rule, 86);
  rule(slide, 304, 296, 672, C.rule, 1);
  rule(slide, 304, 296, 1, C.rule, 62);
  rule(slide, 640, 296, 1, C.rule, 62);
  rule(slide, 976, 296, 1, C.rule, 62);
  callout(slide, "業務停止を伴うか", 466, 150, 348, { height: 72, fill: C.ink, color: C.white, fontSize: 22 });
  const nodes = [
    [150, "停止あり", "復旧4時間超", C.dangerSoft, C.danger, "レベル3"],
    [486, "停止あり", "復旧4時間以内", C.warningSoft, C.warning, "レベル2"],
    [822, "停止なし", "代替手段あり", C.positiveSoft, C.positive, "レベル1"],
  ];
  nodes.forEach((node) => {
    panel(slide, node[0], 358, 308, 170, { fill: node[3], lineFill: "none", name: "decision-node" });
    text(slide, node[1], { left: node[0] + 20, top: 382, width: 268, height: 32 }, {
      fontSize: 17, color: C.muted, name: "decision-condition",
    });
    text(slide, node[2], { left: node[0] + 20, top: 426, width: 268, height: 38 }, {
      fontSize: 20, bold: true, color: C.ink, name: "decision-detail",
    });
    text(slide, node[5], { left: node[0] + 20, top: 480, width: 268, height: 32 }, {
      fontSize: 20, bold: true, color: node[4], name: "decision-outcome",
    });
  });
}

function drawDecisionAction(slide, layout, index) {
  base(slide, layout, index, "8月の試行開始と評価条件の承認をお願いしたい");
  panel(slide, 72, 150, 1136, 108, { fill: C.ink, lineFill: "none", name: "decision-banner" });
  label(slide, "求める決定", 96, 172, "#BFD1E1");
  text(slide, "2部門・6週間の試行導入を承認する", { left: 96, top: 206, width: 1000, height: 36 }, {
    fontSize: 25, bold: true, color: C.white, name: "decision-text",
  });
  heading(slide, "判定条件", 72, 302, 360, C.ink);
  bulletList(slide, ["重大な根拠欠落0件", "再現率95%以上", "例外率10%以下"], {
    left: 72, top: 354, width: 360,
  }, { itemHeight: 38, gap: 14, fontSize: 18, dotColor: C.warning });
  addTable(slide, [
    ["期限", "アクション", "担当"],
    ["8/05", "対象案件を確定", "企画部"],
    ["8/12", "試行環境を準備", "開発部"],
    ["8/19", "利用者研修を実施", "各部門"],
    ["8/26", "試行を開始", "プロジェクト"],
  ], { left: 494, top: 302, width: 714, height: 246 }, { bodySize: 14 });
  callout(slide, "最終決定：全社展開の判断は試行終了後に実施する", 72, 580, 1136, {
    height: 44, fill: C.warningSoft, fontSize: 17,
  });
}

function drawKpi(slide, layout, index) {
  base(slide, layout, index, "処理時間は改善し、目標3.0日に近づいている");
  if (layout.id === "kpi-trend") {
    metric(slide, "平均処理時間", "3.2日", 72, 166, 220, { height: 132, note: "目標まで0.2日" });
    metric(slide, "期限内完了率", "91%", 72, 316, 220, { height: 132, note: "前年差+6pt", color: C.teal });
    metric(slide, "例外率", "6%", 72, 466, 220, { height: 132, note: "基準内", color: C.warning });
    addLineChart(slide, { left: 350, top: 176, width: 858, height: 340 });
    callout(slide, "速度と品質が同時に改善し、試行目標の範囲に入った", 350, 536, 858, {
      height: 56, fill: C.accentSoft, fontSize: 18,
    });
    return;
  }
  const values = layout.id === "kpi-two"
    ? [["平均処理時間", "3.2日", "-40%"], ["期限内完了率", "91%", "+6pt"]]
    : [["平均処理時間", "3.2日", "-40%"], ["期限内完了率", "91%", "+6pt"], ["例外率", "6%", "基準内"]];
  const width = layout.id === "kpi-two" ? 500 : 340;
  const gap = layout.id === "kpi-two" ? 72 : 40;
  const start = layout.id === "kpi-two" ? 104 : 72;
  values.forEach((item, i) => {
    metric(slide, item[0], item[1], start + i * (width + gap), 230, width, {
      height: 230,
      note: item[2],
      valueSize: 64,
      color: i === 1 ? C.teal : i === 2 ? C.warning : C.accent,
    });
  });
  callout(slide, "主要指標はいずれも試行継続の基準を満たす", 240, 520, 800, {
    height: 62, fill: C.ink, color: C.white, fontSize: 19,
  });
}

function drawChart(slide, layout, index) {
  const titles = {
    "chart-insight": "手作業の振分けが処理時間の最大要因である",
    "chart-insight-line": "処理時間は六か月連続で改善している",
    "chart-insight-stacked": "自動処理の拡大により、人の確認時間が半減した",
    "chart-insight-waterfall": "標準化と自動化で総工数を45%削減できる",
    "chart-insight-donut": "自動処理が全体の58%を占めるまで拡大した",
    "chart-insight-scatter": "効果が高く実行しやすい施策から着手する",
  };
  base(slide, layout, index, titles[layout.id]);
  const position = { left: 72, top: 170, width: 820, height: 392 };
  if (layout.id === "chart-insight-line") addLineChart(slide, position);
  else if (layout.id === "chart-insight-stacked") addBarChart(slide, position, false, true);
  else if (layout.id === "chart-insight-waterfall") addWaterfall(slide, position);
  else if (layout.id === "chart-insight-donut") addDonut(slide, position);
  else if (layout.id === "chart-insight-scatter") addScatter(slide, position);
  else addBarChart(slide, position, true, false);
  heading(slide, "読み取るべきこと", 946, 182, 250, C.accent);
  text(slide, layout.id === "chart-insight-scatter" ? "1. 入力標準化\n2. 自動振分け" : "主要な変化を\n一つに絞る", {
    left: 946, top: 236, width: 240, height: 96,
  }, { fontSize: 25, bold: true, color: C.ink, lineSpacing: 1.25, name: "chart-insight" });
  bulletList(slide, ["比較軸を固定", "例示値を明示"], { left: 946, top: 370, width: 240 }, {
    itemHeight: 34, gap: 10, fontSize: 16,
  });
}

function drawTableInsight(slide, layout, index) {
  base(slide, layout, index, "案Bは総費用を抑えつつ、運用工数を半減できる");
  addTable(slide, [
    ["項目", "案A", "案B", "案C"],
    ["初期費用", "800万円", "1,200万円", "2,000万円"],
    ["年間運用費", "600万円", "300万円", "240万円"],
    ["導入期間", "2か月", "3か月", "8か月"],
    ["運用工数", "100%", "50%", "40%"],
    ["3年総費用", "2,600万円", "2,100万円", "2,720万円"],
  ], { left: 72, top: 166, width: 850, height: 366 }, { bodySize: 15 });
  heading(slide, "読み取るべきこと", 972, 182, 220, C.accent);
  text(slide, "-500万円", { left: 972, top: 246, width: 220, height: 72 }, {
    fontSize: 42, bold: true, color: C.accent, name: "table-delta",
  });
  text(slide, "案Aに対する\n3年間の差", { left: 972, top: 326, width: 220, height: 64 }, {
    fontSize: 18, color: C.body, lineSpacing: 1.3, name: "table-note",
  });
  bulletList(slide, ["運用工数は50%へ", "全面刷新より短期間"], { left: 972, top: 438, width: 220 }, {
    itemHeight: 30, gap: 8, fontSize: 14,
  });
}

function drawSmallMultiples(slide, layout, index) {
  base(slide, layout, index, "全部門で改善したが、部門Cは鈍化している");
  const names = ["部門A", "部門B", "部門C", "部門D"];
  names.forEach((name, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 72 + col * 568;
    const y = 158 + row * 212;
    panel(slide, x, y, 536, 184, { fill: C.surface, name: "small-chart-panel" });
    heading(slide, name, x + 18, y + 14, 130, i === 2 ? C.warning : C.ink);
    addLineChart(slide, { left: x + 120, top: y + 18, width: 392, height: 142 }, true);
  });
  callout(slide, "部門Cは例外案件が多く、入力標準化を先に行う", 72, 596, 1136, {
    height: 44, fill: C.warningSoft, fontSize: 17,
  });
}

function drawProgress(slide, layout, index) {
  base(slide, layout, index, "試行準備は82%まで進み、教育だけが遅れる");
  const rows = [
    ["対象案件", 100, 100, "完了"],
    ["評価手順", 92, 100, "順調"],
    ["試行環境", 84, 100, "順調"],
    ["利用者教育", 58, 100, "遅延"],
    ["監査確認", 76, 100, "注意"],
  ];
  rows.forEach((row, i) => {
    const y = 170 + i * 82;
    text(slide, row[0], { left: 72, top: y, width: 190, height: 36 }, {
      fontSize: 19, bold: true, color: C.ink, vertical: "middle", name: "progress-label",
    });
    rect(slide, { left: 286, top: y + 9, width: 720, height: 20 }, C.rule, { name: "progress-track" });
    rect(slide, { left: 286, top: y + 9, width: 720 * row[1] / row[2], height: 20 }, statusColor(row[3]), { name: "progress-value" });
    text(slide, `${row[1]}%`, { left: 1028, top: y, width: 80, height: 36 }, {
      fontSize: 19, bold: true, color: statusColor(row[3]), align: "right", vertical: "middle", name: "progress-percent",
    });
    text(slide, row[3], { left: 1122, top: y, width: 86, height: 36 }, {
      fontSize: 15, color: C.muted, align: "right", vertical: "middle", name: "progress-status",
    });
  });
}

function drawPareto(slide, layout, index) {
  base(slide, layout, index, "上位三要因が問い合わせ時間の81%を占める");
  addBarChart(slide, { left: 72, top: 174, width: 820, height: 386 }, false, false);
  rule(slide, 700, 198, 1, C.warning, 320);
  heading(slide, "重点対象", 946, 190, 230, C.warning);
  text(slide, "81%", { left: 946, top: 248, width: 230, height: 86 }, {
    fontSize: 58, bold: true, color: C.warning, name: "pareto-number",
  });
  text(slide, "上位三要因の累積比率", { left: 946, top: 338, width: 230, height: 52 }, {
    fontSize: 17, color: C.body, name: "pareto-note",
  });
  bulletList(slide, ["受付不備", "担当不明", "根拠不足"], { left: 946, top: 430, width: 230 }, {
    itemHeight: 28, gap: 8, fontSize: 15, dotColor: C.warning,
  });
}

function drawMatrix(slide, layout, index) {
  base(slide, layout, index, "効果が高く実行しやすい施策から着手する");
  const left = 104, top = 168, size = 430;
  panel(slide, left, top, size, size, { fill: C.surface, name: "matrix-frame" });
  rect(slide, { left: left + size / 2, top, width: size / 2, height: size / 2 }, C.accentSoft, { name: "matrix-focus" });
  rule(slide, left + size / 2, top, 1, C.rule, size);
  rule(slide, left, top + size / 2, size, C.rule, 1);
  text(slide, "低", { left: left - 46, top: top + size - 22, width: 38, height: 22 }, { fontSize: 13, color: C.muted, align: "right", name: "axis-low" });
  text(slide, "高", { left: left - 46, top, width: 38, height: 22 }, { fontSize: 13, color: C.muted, align: "right", name: "axis-high" });
  text(slide, "低", { left, top: top + size + 8, width: 38, height: 22 }, { fontSize: 13, color: C.muted, name: "axis-low" });
  text(slide, "高", { left: left + size - 38, top: top + size + 8, width: 38, height: 22 }, { fontSize: 13, color: C.muted, align: "right", name: "axis-high" });
  const dots = [
    [0.72, 0.78, "入力標準化", C.accent],
    [0.82, 0.63, "自動振分け", C.accent],
    [0.36, 0.68, "全文検索", C.warning],
    [0.62, 0.34, "画面刷新", C.teal],
    [0.28, 0.28, "帳票統合", C.muted],
  ];
  dots.forEach((dot) => {
    const x = left + dot[0] * size;
    const y = top + (1 - dot[1]) * size;
    rect(slide, { left: x - 8, top: y - 8, width: 16, height: 16 }, dot[3], { geometry: "ellipse", name: "matrix-dot" });
    text(slide, dot[2], { left: x + 12, top: y - 11, width: 110, height: 24 }, {
      fontSize: 13, color: C.body, name: "matrix-label",
    });
  });
  heading(slide, "優先順位", 650, 210, 480, C.accent);
  text(slide, "1. 入力標準化\n2. 自動振分け", { left: 650, top: 272, width: 440, height: 112 }, {
    fontSize: 30, bold: true, color: C.ink, lineSpacing: 1.4, name: "matrix-priority",
  });
  text(slide, "効果と実行容易性を同じ尺度で評価し、右上の施策から着手する。", {
    left: 650, top: 430, width: 450, height: 92,
  }, { fontSize: 20, color: C.body, lineSpacing: 1.35, name: "matrix-explanation" });
}

function drawProcess(slide, layout, index) {
  base(slide, layout, index, "五つの判断点を一方向のプロセスで管理する");
  const steps = [
    ["01", "受付", "申請内容を登録"],
    ["02", "分類", "条件で対象を判定"],
    ["03", "確認", "不足情報を補完"],
    ["04", "承認", "権限者が判断"],
    ["05", "記録", "結果と根拠を保存"],
  ];
  if (layout.id === "process-vertical") {
    steps.forEach((step, i) => {
      const y = 154 + i * 92;
      if (i < steps.length - 1) rule(slide, 170, y + 60, 1, C.rule, 34);
      rect(slide, { left: 144, top: y, width: 54, height: 54 }, i === 1 ? C.accent : C.ink, { geometry: "ellipse", name: "step-number" });
      text(slide, step[0], { left: 144, top: y, width: 54, height: 54 }, {
        fontSize: 14, bold: true, color: C.white, align: "center", vertical: "middle", name: "step-number-text",
      });
      text(slide, step[1], { left: 228, top: y, width: 180, height: 54 }, {
        fontSize: 23, bold: true, color: C.ink, vertical: "middle", name: "step-title",
      });
      text(slide, step[2], { left: 424, top: y, width: 360, height: 54 }, {
        fontSize: 18, color: C.body, vertical: "middle", name: "step-body",
      });
    });
    callout(slide, "原則：各段階で担当と完了条件を明示する", 850, 246, 300, {
      height: 126, fill: C.accentSoft, fontSize: 20,
    });
    return;
  }
  if (layout.id === "process-swimlane") {
    const lanes = ["利用部門", "自動処理", "IT部門"];
    lanes.forEach((lane, i) => {
      const y = 162 + i * 126;
      panel(slide, 72, y, 1136, 104, { fill: i % 2 ? C.faint : C.surface, name: "lane" });
      text(slide, lane, { left: 88, top: y, width: 146, height: 104 }, {
        fontSize: 18, bold: true, color: C.ink, vertical: "middle", name: "lane-label",
      });
    });
    const laneIndex = [0, 1, 1, 2, 2];
    steps.forEach((step, i) => {
      const x = 270 + i * 180;
      const y = 181 + laneIndex[i] * 126;
      if (i < steps.length - 1) rule(slide, x + 138, y + 32, 42, C.rule, 2);
      panel(slide, x, y, 138, 66, { fill: i === 1 ? C.accentSoft : C.surface, lineFill: i === 1 ? C.accent : C.rule, name: "lane-step" });
      text(slide, step[1], { left: x + 10, top: y + 9, width: 118, height: 28 }, {
        fontSize: 18, bold: true, color: C.ink, align: "center", name: "lane-step-title",
      });
      text(slide, step[0], { left: x + 10, top: y + 39, width: 118, height: 20 }, {
        fontSize: 12, color: C.muted, align: "center", name: "lane-step-number",
      });
    });
    callout(slide, "承認前に根拠と未確認事項を表示する", 72, 566, 1136, {
      height: 46, fill: C.accentSoft, fontSize: 17,
    });
    return;
  }
  steps.forEach((step, i) => {
    const x = 72 + i * 228;
    if (i < steps.length - 1) rule(slide, x + 188, 324, 40, C.rule, 2);
    panel(slide, x, 246, 188, 160, { fill: i === 1 ? C.accentSoft : C.surface, lineFill: i === 1 ? C.accent : C.rule, name: "process-step" });
    label(slide, step[0], x + 16, 264, i === 1 ? C.accent : C.muted);
    text(slide, step[1], { left: x + 16, top: 310, width: 156, height: 38 }, {
      fontSize: 23, bold: true, color: C.ink, name: "process-title",
    });
    text(slide, step[2], { left: x + 16, top: 360, width: 156, height: 34 }, {
      fontSize: 14, color: C.body, name: "process-body",
    });
  });
  callout(slide, "原則：一つの方向に読み、途中で責任を曖昧にしない", 72, 500, 1136, {
    height: 58, fill: C.accentSoft, fontSize: 18,
  });
}

function drawCycle(slide, layout, index) {
  base(slide, layout, index, "調査・実行・検証・改善を学習サイクルで回す");
  const cx = 430, cy = 370, radius = 180;
  const steps = [
    ["調査", -90, C.accent],
    ["実行", 0, C.teal],
    ["検証", 90, C.warning],
    ["改善", 180, C.positive],
  ];
  [
    ["↘", 498, 238],
    ["↙", 498, 456],
    ["↖", 284, 456],
    ["↗", 284, 238],
  ].forEach(([arrow, left, top]) => {
    text(slide, arrow, { left, top, width: 48, height: 48 }, {
      fontSize: 34,
      bold: true,
      color: C.muted,
      align: "center",
      vertical: "middle",
      name: "cycle-arrow",
    });
  });
  steps.forEach((step) => {
    const angle = step[1] * Math.PI / 180;
    const x = cx + Math.cos(angle) * radius - 70;
    const y = cy + Math.sin(angle) * radius - 42;
    rect(slide, { left: x, top: y, width: 140, height: 84 }, step[2], { geometry: "roundRect", borderRadius: "rounded-xl", name: "cycle-step" });
    text(slide, step[0], { left: x, top: y, width: 140, height: 84 }, {
      fontSize: 23, bold: true, color: C.white, align: "center", vertical: "middle", name: "cycle-step-text",
    });
  });
  rect(slide, { left: cx - 76, top: cy - 76, width: 152, height: 152 }, C.ink, { geometry: "ellipse", name: "cycle-center" });
  text(slide, "証跡から\n学習する", { left: cx - 76, top: cy - 76, width: 152, height: 152 }, {
    fontSize: 22, bold: true, color: C.white, align: "center", vertical: "middle", lineSpacing: 1.2, name: "cycle-center-text",
  });
  callout(slide, "改善点は次回の入力規則と評価条件へ反映する", 790, 276, 370, {
    height: 160, fill: C.accentSoft, fontSize: 21,
  });
}

function drawValueChain(slide, layout, index) {
  base(slide, layout, index, "データ収集から判断まで価値と統制を付加する");
  const stages = [
    ["収集", "対象を揃える"],
    ["標準化", "形式を統一"],
    ["解析", "関係を抽出"],
    ["照合", "根拠を確認"],
    ["判断", "責任者が承認"],
  ];
  stages.forEach((stage, i) => {
    const x = 72 + i * 228;
    if (i < stages.length - 1) rule(slide, x + 190, 305, 38, C.rule, 2);
    panel(slide, x, 226, 190, 158, { fill: i === 4 ? C.accentSoft : C.surface, lineFill: i === 4 ? C.accent : C.rule, name: "value-stage" });
    text(slide, stage[0], { left: x + 18, top: 254, width: 154, height: 42 }, {
      fontSize: 24, bold: true, color: C.ink, align: "center", name: "value-title",
    });
    text(slide, stage[1], { left: x + 18, top: 316, width: 154, height: 40 }, {
      fontSize: 16, color: C.body, align: "center", name: "value-body",
    });
  });
  heading(slide, "共通の支援要素", 72, 450, 220, C.muted);
  ["語彙", "権限", "品質規則", "監査証跡"].forEach((item, i) => {
    callout(slide, item, 310 + i * 220, 440, 190, { height: 58, fill: C.faint, fontSize: 17 });
  });
  callout(slide, "成果：再現可能な判断", 310, 536, 850, { height: 58, fill: C.ink, color: C.white, fontSize: 20 });
}

function drawTimeline(slide, layout, index) {
  const titles = {
    "timeline-roadmap": "10月試行には8月中の要件確定が必要だ",
    "timeline-milestones": "四つの節目で試行の継続可否を判断する",
    "timeline-gantt": "三つの作業系列を並行し、10月開始へつなげる",
  };
  base(slide, layout, index, titles[layout.id]);
  if (layout.id === "timeline-milestones") {
    rule(slide, 130, 350, 1020, C.rule, 3);
    const milestones = [
      ["8/08", "要件確定"],
      ["8/29", "設計承認"],
      ["9/19", "検証完了"],
      ["10/01", "試行開始"],
    ];
    milestones.forEach((m, i) => {
      const x = 130 + i * 340;
      rect(slide, { left: x - 12, top: 338, width: 24, height: 24 }, i === 3 ? C.warning : C.accent, { geometry: "ellipse", name: "milestone" });
      text(slide, m[0], { left: x - 70, top: 270, width: 140, height: 30 }, {
        fontSize: 17, bold: true, color: i === 3 ? C.warning : C.accent, align: "center", name: "milestone-date",
      });
      text(slide, m[1], { left: x - 100, top: 384, width: 200, height: 46 }, {
        fontSize: 19, bold: true, color: C.ink, align: "center", name: "milestone-label",
      });
    });
    callout(slide, "各節目で品質基準を満たさなければ、次工程へ進めない", 230, 506, 820, {
      height: 66, fill: C.accentSoft, fontSize: 19,
    });
    return;
  }
  const periods = ["8月", "9月", "10月", "11月"];
  periods.forEach((period, i) => {
    text(slide, period, { left: 298 + i * 208, top: 150, width: 190, height: 28 }, {
      fontSize: 15, bold: true, color: C.muted, align: "center", name: "period",
    });
    rule(slide, 298 + i * 208, 188, 1, C.rule, 358);
  });
  const rows = [
    ["要件・設計", 0.0, 1.0, C.accent],
    ["構築・検証", 0.55, 2.0, C.teal],
    ["試行・評価", 1.4, 3.3, C.warning],
  ];
  rows.forEach((row, i) => {
    const y = 246 + i * 102;
    text(slide, row[0], { left: 72, top: y, width: 190, height: 36 }, {
      fontSize: 18, bold: true, color: C.ink, vertical: "middle", name: "roadmap-row",
    });
    rect(slide, { left: 308 + row[1] * 208, top: y, width: (row[2] - row[1]) * 208, height: 34 }, row[3], { name: "roadmap-bar" });
  });
  callout(slide, "意思決定点：8月30日までに設計承認を完了する", 72, 572, 1136, {
    height: 48, fill: C.warningSoft, fontSize: 17,
  });
}

function drawHierarchy(slide, layout, index) {
  base(slide, layout, index, "目的から実装を四層に分け、判断を一貫させる");
  const levels = [
    ["目的", "迅速で説明可能な影響調査", 460, C.ink],
    ["原則", "探索と照合を分離", 600, C.accentDark],
    ["標準", "入力・証跡・判定条件", 760, C.accent],
    ["実装", "カタログ・検査・承認", 920, C.teal],
  ];
  levels.forEach((level, i) => {
    const y = 176 + i * 96;
    const x = 72 + (1136 - level[2]) / 2;
    rect(slide, { left: x, top: y, width: level[2], height: 70 }, level[3], { name: "pyramid-level" });
    text(slide, level[0], { left: x + 20, top: y, width: 110, height: 70 }, {
      fontSize: 19, bold: true, color: C.white, vertical: "middle", name: "pyramid-label",
    });
    text(slide, level[1], { left: x + 150, top: y, width: level[2] - 180, height: 70 }, {
      fontSize: 20, bold: true, color: C.white, align: "center", vertical: "middle", name: "pyramid-body",
    });
  });
  callout(slide, "土台：共通語彙と責任分担", 270, 574, 740, { height: 44, fill: C.faint, fontSize: 17 });
}

function drawFunnel(slide, layout, index) {
  base(slide, layout, index, "候補100件から試行対象20件を透明に選ぶ");
  const stages = [
    ["候補案件", "100", 760, C.ink],
    ["条件合致", "62", 620, C.accentDark],
    ["データ準備済", "38", 500, C.accent],
    ["試行対象", "20", 380, C.teal],
  ];
  stages.forEach((stage, i) => {
    const x = 120 + (760 - stage[2]) / 2;
    const y = 166 + i * 98;
    rect(slide, { left: x, top: y, width: stage[2], height: 74 }, stage[3], { name: "funnel-stage" });
    text(slide, stage[0], { left: x + 24, top: y, width: stage[2] - 140, height: 74 }, {
      fontSize: 20, bold: true, color: C.white, vertical: "middle", name: "funnel-label",
    });
    text(slide, stage[1], { left: x + stage[2] - 110, top: y, width: 86, height: 74 }, {
      fontSize: 30, bold: true, color: C.white, align: "right", vertical: "middle", name: "funnel-value",
    });
  });
  heading(slide, "選定条件", 930, 214, 240, C.accent);
  bulletList(slide, ["主要業務を含む", "正解結果がある", "機密情報を除外"], { left: 930, top: 272, width: 240 }, {
    itemHeight: 34, gap: 10, fontSize: 15,
  });
}

function drawArchitecture(slide, layout, index) {
  base(slide, layout, index, layout.id === "architecture-layered"
    ? "調査と証跡保管を分離し、統制点を明確にする"
    : "対象システムを中心に、境界を明確にする");
  if (layout.id === "architecture-system-context") {
    const nodes = [
      [530, 286, 250, 134, "影響調査基盤", C.ink, C.white],
      [120, 210, 210, 100, "上流システム", C.surface, C.ink],
      [120, 420, 210, 100, "設計書・定義", C.surface, C.ink],
      [950, 210, 210, 100, "開発担当", C.surface, C.ink],
      [950, 420, 210, 100, "承認者", C.surface, C.ink],
    ];
    rule(slide, 330, 260, 200, C.rule, 2);
    rule(slide, 330, 470, 200, C.rule, 2);
    rule(slide, 780, 260, 170, C.rule, 2);
    rule(slide, 780, 470, 170, C.rule, 2);
    nodes.forEach((node) => {
      panel(slide, node[0], node[1], node[2], node[3], { fill: node[5], lineFill: node[5] === C.surface ? C.rule : "none", name: "architecture-node" });
      text(slide, node[4], { left: node[0] + 14, top: node[1], width: node[2] - 28, height: node[3] }, {
        fontSize: 21, bold: true, color: node[6], align: "center", vertical: "middle", name: "architecture-label",
      });
    });
    callout(slide, "外部システムへ直接変更を加えず、参照と証跡出力に限定する", 370, 560, 570, {
      height: 54, fill: C.accentSoft, fontSize: 18,
    });
    return;
  }
  const layers = [
    ["利用", ["調査画面", "承認画面"], C.accentSoft],
    ["処理", ["探索エンジン", "照合エンジン"], C.tealSoft],
    ["知識", ["カタログ", "評価ルール"], C.warningSoft],
    ["保管", ["ソース", "証跡"], C.faint],
  ];
  layers.forEach((layer, i) => {
    const y = 156 + i * 102;
    panel(slide, 72, y, 900, 78, { fill: layer[2], lineFill: "none", name: "architecture-layer" });
    text(slide, layer[0], { left: 94, top: y, width: 120, height: 78 }, {
      fontSize: 18, bold: true, color: C.ink, vertical: "middle", name: "layer-label",
    });
    layer[1].forEach((item, j) => {
      panel(slide, 270 + j * 318, y + 12, 280, 54, { fill: C.surface, name: "layer-node" });
      text(slide, item, { left: 286 + j * 318, top: y + 12, width: 248, height: 54 }, {
        fontSize: 19, bold: true, color: C.ink, align: "center", vertical: "middle", name: "layer-node-label",
      });
    });
  });
  heading(slide, "統制点", 1018, 184, 190, C.accent);
  bulletList(slide, ["入力を固定", "根拠を保存", "人が承認"], { left: 1018, top: 242, width: 190 }, {
    itemHeight: 34, gap: 12, fontSize: 16,
  });
}

function drawDataFlow(slide, layout, index) {
  base(slide, layout, index, "上流取引からレポートまで変換と責任を追跡する");
  const nodes = [
    [72, "取引", "発生"],
    [294, "受信", "整形"],
    [516, "集計", "変換"],
    [738, "リスク", "算出"],
    [960, "レポート", "利用"],
  ];
  nodes.forEach((node, i) => {
    if (i < nodes.length - 1) rule(slide, node[0] + 170, 334, 52, C.rule, 3);
  });
  nodes.forEach((node, i) => {
    panel(slide, node[0], 246, 170, 176, { fill: i === 2 ? C.accentSoft : C.surface, lineFill: i === 2 ? C.accent : C.rule, name: "data-node" });
    label(slide, `0${i + 1}`, node[0] + 18, 266, i === 2 ? C.accent : C.muted);
    text(slide, node[1], { left: node[0] + 18, top: 310, width: 134, height: 40 }, {
      fontSize: 23, bold: true, color: C.ink, align: "center", name: "data-title",
    });
    text(slide, node[2], { left: node[0] + 18, top: 366, width: 134, height: 28 }, {
      fontSize: 15, color: C.muted, align: "center", name: "data-stage",
    });
  });
  callout(slide, "統制：各境界で件数、時点、データ区分を記録する", 200, 508, 880, {
    height: 70, fill: C.ink, color: C.white, fontSize: 20,
  });
}

function drawDependency(slide, layout, index) {
  base(slide, layout, index, "項目変更は三つのジョブと二つのIFへ波及する");
  const center = [536, 286, 208, 116, "項目A\n桁拡張"];
  const nodes = [
    [100, 178, 220, 84, "上流IF"],
    [100, 442, 220, 84, "マスタ"],
    [910, 152, 220, 84, "計算ジョブ"],
    [910, 304, 220, 84, "帳票ジョブ"],
    [910, 456, 220, 84, "下流IF"],
  ];
  nodes.forEach((node) => {
    rule(slide, node[0] < center[0] ? node[0] + node[2] : center[0] + center[2], node[1] + 42, Math.abs(node[0] - center[0]) - 12, C.rule, 2);
  });
  panel(slide, center[0], center[1], center[2], center[3], { fill: C.accent, lineFill: "none", name: "dependency-center" });
  text(slide, center[4], { left: center[0], top: center[1], width: center[2], height: center[3] }, {
    fontSize: 24, bold: true, color: C.white, align: "center", vertical: "middle", lineSpacing: 1.15, name: "dependency-center-text",
  });
  nodes.forEach((node, i) => {
    panel(slide, node[0], node[1], node[2], node[3], { fill: C.surface, name: "dependency-node" });
    text(slide, node[4], { left: node[0] + 14, top: node[1], width: node[2] - 28, height: node[3] }, {
      fontSize: 20, bold: true, color: C.ink, align: "center", vertical: "middle", name: "dependency-node-text",
    });
    if (i >= 2) rect(slide, { left: node[0] + 192, top: node[1] + 12, width: 12, height: 12 }, i === 3 ? C.warning : C.danger, { geometry: "ellipse", name: "dependency-status" });
  });
  callout(slide, "重点：帳票ジョブは固定長出力のため、個別確認が必要", 380, 552, 520, {
    height: 54, fill: C.warningSoft, fontSize: 18,
  });
}

function drawStakeholder(slide, layout, index) {
  base(slide, layout, index, layout.id === "raci"
    ? "社員が最終責任を持ち、AIと協力会社が支援する"
    : "影響力と関心が高い二者を早期に巻き込む");
  if (layout.id === "raci") {
    addTable(slide, [
      ["活動", "社員", "協力会社", "AI", "利用部門"],
      ["対象定義", "A", "C", "I", "C"],
      ["母集団列挙", "A", "R", "R", "I"],
      ["根拠確認", "A", "R", "C", "C"],
      ["最終承認", "A/R", "I", "I", "C"],
    ], { left: 260, top: 166, width: 948, height: 348 }, { bodySize: 16 });
    heading(slide, "凡例", 72, 184, 150, C.accent);
    bulletList(slide, ["R：実行", "A：最終責任", "C：協議", "I：共有"], { left: 72, top: 236, width: 150 }, {
      itemHeight: 30, gap: 8, fontSize: 15,
    });
    callout(slide, "AIへ最終承認を割り当てない", 72, 540, 1136, { height: 56, fill: C.dangerSoft, fontSize: 18 });
    return;
  }
  const left = 110, top = 168, size = 430;
  panel(slide, left, top, size, size, { fill: C.surface, name: "stakeholder-matrix" });
  rule(slide, left + size / 2, top, 1, C.rule, size);
  rule(slide, left, top + size / 2, size, C.rule, 1);
  const people = [
    [0.78, 0.82, "業務責任者", C.accent],
    [0.70, 0.62, "IT責任者", C.accent],
    [0.42, 0.76, "監査部", C.warning],
    [0.34, 0.42, "利用者", C.teal],
    [0.68, 0.30, "協力会社", C.muted],
  ];
  people.forEach((person) => {
    const x = left + person[0] * size;
    const y = top + (1 - person[1]) * size;
    rect(slide, { left: x - 8, top: y - 8, width: 16, height: 16 }, person[3], { geometry: "ellipse", name: "stakeholder-dot" });
    text(slide, person[2], { left: x + 12, top: y - 12, width: 120, height: 24 }, { fontSize: 13, color: C.body, name: "stakeholder-label" });
  });
  heading(slide, "関与方針", 650, 212, 480, C.accent);
  bulletList(slide, ["業務責任者：週次で判断", "IT責任者：設計を承認", "監査部：開始前に統制確認"], {
    left: 650, top: 276, width: 480,
  }, { itemHeight: 46, gap: 18, fontSize: 20 });
}

function drawRisk(slide, layout, index) {
  base(slide, layout, index, layout.id === "risk-matrix"
    ? "分類誤りと根拠欠落を優先的に抑える"
    : "高リスク二項目を移行判定までに解消する");
  if (layout.id === "rag-status") {
    const risks = [
      ["分類誤り", "赤", "設計責任者", "評価条件を追加"],
      ["根拠欠落", "赤", "品質責任者", "必須証跡を固定"],
      ["処理遅延", "黄", "運用担当", "監視を追加"],
      ["権限設定", "緑", "基盤担当", "確認済み"],
      ["教育不足", "黄", "利用部門", "研修を前倒し"],
    ];
    risks.forEach((risk, i) => {
      const y = 164 + i * 76;
      panel(slide, 72, y, 1136, 58, { fill: i % 2 ? C.faint : C.surface, lineFill: "none", name: "rag-row" });
      const color = risk[1] === "赤" ? C.danger : risk[1] === "黄" ? C.warning : C.positive;
      rect(slide, { left: 94, top: y + 19, width: 20, height: 20 }, color, { geometry: "ellipse", name: "rag-dot" });
      text(slide, risk[0], { left: 140, top: y, width: 260, height: 58 }, { fontSize: 19, bold: true, color: C.ink, vertical: "middle", name: "rag-risk" });
      text(slide, risk[2], { left: 450, top: y, width: 220, height: 58 }, { fontSize: 16, color: C.body, vertical: "middle", name: "rag-owner" });
      text(slide, risk[3], { left: 720, top: y, width: 430, height: 58 }, { fontSize: 16, color: C.body, vertical: "middle", name: "rag-response" });
    });
    callout(slide, "赤二項目が解消するまで本番移行しない", 72, 570, 1136, { height: 50, fill: C.dangerSoft, fontSize: 18 });
    return;
  }
  const left = 102, top = 160, cell = 86;
  for (let y = 0; y < 5; y += 1) {
    for (let x = 0; x < 5; x += 1) {
      const score = (x + 1) * (5 - y);
      const fill = score >= 15 ? C.dangerSoft : score >= 8 ? C.warningSoft : C.positiveSoft;
      panel(slide, left + x * cell, top + y * cell, cell, cell, { fill, lineFill: C.white, lineWidth: 2, name: "risk-cell" });
    }
  }
  const dots = [
    [3.5, 0.5, "分類誤り", C.danger],
    [2.5, 0.5, "根拠欠落", C.danger],
    [1.5, 3.5, "処理遅延", C.positive],
    [2.5, 2.5, "教育不足", C.warning],
  ];
  dots.forEach((dot) => {
    const x = left + dot[0] * cell;
    const y = top + dot[1] * cell;
    rect(slide, { left: x - 9, top: y - 9, width: 18, height: 18 }, dot[3], { geometry: "ellipse", name: "risk-dot" });
    text(slide, dot[2], { left: x + 14, top: y - 12, width: 120, height: 24 }, { fontSize: 12, color: C.body, name: "risk-label" });
  });
  heading(slide, "優先対応", 650, 204, 480, C.danger);
  bulletList(slide, ["分類誤り：判定規則を追加", "根拠欠落：必須証跡を固定"], {
    left: 650, top: 270, width: 480,
  }, { itemHeight: 48, gap: 22, fontSize: 20, dotColor: C.danger });
  callout(slide, "高リスク二項目を試行終了条件へ組み込む", 650, 436, 480, { height: 92, fill: C.dangerSoft, fontSize: 20 });
}

function drawVisual(slide, layout, index) {
  base(slide, layout, index, "現場操作を具体化し、改善後の利用像を共有する");
  if (layout.id === "image-left") {
    imagePlaceholder(slide, 72, 154, 650, 454, 1);
    heading(slide, "一つの画面で状態と根拠を確認する", 780, 220, 400, C.accent);
    text(slide, "一覧から案件を選び、調査結果、未確認事項、承認履歴を同じ文脈で確認する。", {
      left: 780, top: 286, width: 390, height: 132,
    }, { fontSize: 21, color: C.body, lineSpacing: 1.4, name: "visual-body" });
    bulletList(slide, ["視線移動を減らす", "根拠を隠さない"], { left: 780, top: 462, width: 380 }, {
      itemHeight: 34, gap: 12, fontSize: 17,
    });
  } else if (layout.id === "image-right") {
    heading(slide, "判断前に必要な情報だけを揃える", 72, 220, 410, C.accent);
    text(slide, "複数資料を開かず、影響候補と根拠を同じ画面で比較できる。", {
      left: 72, top: 286, width: 390, height: 132,
    }, { fontSize: 21, color: C.body, lineSpacing: 1.4, name: "visual-body" });
    bulletList(slide, ["入力を標準化", "差分を強調"], { left: 72, top: 462, width: 380 }, {
      itemHeight: 34, gap: 12, fontSize: 17,
    });
    imagePlaceholder(slide, 526, 154, 682, 454, 2);
  } else if (layout.id === "image-hero") {
    imagePlaceholder(slide, 72, 142, 1136, 486, 3);
    panel(slide, 110, 410, 650, 160, { fill: C.ink, lineFill: "none", name: "hero-overlay" });
    text(slide, "判断材料を、一つの視野へ", { left: 142, top: 440, width: 580, height: 56 }, {
      fontSize: 34, bold: true, color: C.white, name: "hero-headline",
    });
    text(slide, "影響、根拠、未確認事項を同時に確認する。", { left: 142, top: 510, width: 580, height: 34 }, {
      fontSize: 18, color: "#D8E4EF", name: "hero-body",
    });
  } else {
    [0, 1, 2].forEach((i) => imagePlaceholder(slide, 72 + i * 378, 176, 336, 300, i + 4));
    const captions = ["入力", "解析", "承認"];
    captions.forEach((caption, i) => {
      text(slide, caption, { left: 72 + i * 378, top: 492, width: 336, height: 34 }, {
        fontSize: 20, bold: true, color: C.ink, align: "center", name: "gallery-caption",
      });
    });
    callout(slide, "三つの場面を同じ粒度で並べ、体験全体を説明する", 210, 560, 860, {
      height: 54, fill: C.accentSoft, fontSize: 18,
    });
  }
}

function drawIssueLog(slide, layout, index) {
  base(slide, layout, index, "重要課題二件は期限超過の恐れがあり、要判断");
  addTable(slide, [
    ["課題", "状態", "担当", "期限", "対応"],
    ["評価データ不足", "要対応", "企画部", "8/05", "追加案件を選定"],
    ["権限設計未確定", "要対応", "基盤部", "8/08", "承認者を確定"],
    ["教育資料の遅延", "確認中", "利用部門", "8/12", "作成を前倒し"],
    ["監査観点の確認", "順調", "品質管理", "8/15", "レビュー予定"],
    ["試行環境の準備", "順調", "開発部", "8/18", "構築中"],
  ], { left: 72, top: 156, width: 1136, height: 370 }, { bodySize: 14 });
  callout(slide, "エスカレーション：8月8日までに権限設計が決まらなければ開始日を見直す", 72, 562, 1136, {
    height: 60, fill: C.warningSoft, fontSize: 18,
  });
}

function drawFamily(slide, layout, index) {
  switch (layout.familyId) {
    case "cover": return drawCover(slide, layout, index);
    case "agenda": return drawAgenda(slide, layout, index);
    case "section-divider": return drawSection(slide, layout, index);
    case "executive-summary": return drawExecutiveSummary(slide, layout, index);
    case "closing": return drawClosing(slide, layout, index);
    case "appendix": return drawAppendix(slide, layout, index);
    case "key-message": return drawKeyMessage(slide, layout, index);
    case "context-background": return drawContext(slide, layout, index);
    case "problem-definition": return drawProblem(slide, layout, index);
    case "objective-scope": return drawObjective(slide, layout, index);
    case "two-column-explanation": return drawTwoColumn(slide, layout, index);
    case "quote-evidence": return drawQuote(slide, layout, index);
    case "case-study": return drawCaseStudy(slide, layout, index);
    case "comparison": return drawComparison(slide, layout, index);
    case "before-after": return drawBeforeAfter(slide, layout, index);
    case "pros-cons": return drawProsCons(slide, layout, index);
    case "scorecard": return drawScorecard(slide, layout, index);
    case "swot": return drawSwot(slide, layout, index);
    case "decision-tree": return drawDecisionTree(slide, layout, index);
    case "decision-action": return drawDecisionAction(slide, layout, index);
    case "kpi": return drawKpi(slide, layout, index);
    case "chart-insight": return drawChart(slide, layout, index);
    case "table-insight": return drawTableInsight(slide, layout, index);
    case "small-multiples": return drawSmallMultiples(slide, layout, index);
    case "progress": return drawProgress(slide, layout, index);
    case "pareto": return drawPareto(slide, layout, index);
    case "matrix-2x2": return drawMatrix(slide, layout, index);
    case "process": return drawProcess(slide, layout, index);
    case "cycle": return drawCycle(slide, layout, index);
    case "value-chain": return drawValueChain(slide, layout, index);
    case "timeline-roadmap": return drawTimeline(slide, layout, index);
    case "hierarchy-pyramid": return drawHierarchy(slide, layout, index);
    case "funnel": return drawFunnel(slide, layout, index);
    case "architecture": return drawArchitecture(slide, layout, index);
    case "data-flow-lineage": return drawDataFlow(slide, layout, index);
    case "dependency-map": return drawDependency(slide, layout, index);
    case "stakeholder-raci": return drawStakeholder(slide, layout, index);
    case "risk-status": return drawRisk(slide, layout, index);
    case "visual-story": return drawVisual(slide, layout, index);
    case "issue-action-log": return drawIssueLog(slide, layout, index);
    default:
      throw new Error(`未実装familyId: ${layout.familyId}`);
  }
}

async function writeBlob(outputPath, blob) {
  await fs.writeFile(outputPath, new Uint8Array(await blob.arrayBuffer()));
}

function createPreview() {
  const helper = path.join(SCRIPT_DIR, "create_layout_preview.py");
  const args = [
    helper,
    "--input-dir",
    RENDER_DIR,
    "--output-file",
    OUTPUT_PREVIEW,
  ];
  const candidates = [process.env.PYTHON, "python3", "python"].filter(Boolean);
  let lastResult;
  for (const command of candidates) {
    const result = spawnSync(command, args, { encoding: "utf8" });
    lastResult = result;
    if (!result.error && result.status === 0) return;
    if (result.error?.code !== "ENOENT") break;
  }
  throw new Error(
    `プレビュー生成に失敗しました: ${lastResult?.stderr || lastResult?.error || "unknown error"}`,
  );
}

function normalizePptx(pptxPath, slideCount) {
  const helper = path.join(SCRIPT_DIR, "normalize_reference_pptx.py");
  const args = [helper, pptxPath, "--slides", String(slideCount)];
  const candidates = [process.env.PYTHON, "python3", "python"].filter(Boolean);
  let lastResult;
  for (const command of candidates) {
    const result = spawnSync(command, args, { encoding: "utf8" });
    lastResult = result;
    if (!result.error && result.status === 0) return;
    if (result.error?.code !== "ENOENT") break;
  }
  throw new Error(
    `PPTX正規化に失敗しました: ${lastResult?.stderr || lastResult?.error || "unknown error"}`,
  );
}

async function main() {
  const registry = JSON.parse(await fs.readFile(REGISTRY_PATH, "utf8"));
  const layouts = [...registry.layouts].sort(
    (a, b) => a.previewOrder - b.previewOrder,
  );
  if (layouts.length !== 62) {
    throw new Error(`layout件数が不正です: ${layouts.length}`);
  }
  await fs.mkdir(RENDER_DIR, { recursive: true });
  const presentation = Presentation.create({
    slideSize: { width: W, height: H },
  });
  layouts.forEach((layout, index) => {
    const slide = presentation.slides.add();
    drawFamily(slide, layout, index);
  });
  const inspect = await presentation.inspect({
    kind: "slide,textbox,shape,table,chart,notes",
    maxChars: 12000,
  });
  await fs.writeFile(path.join(RENDER_DIR, "presentation-inspect.ndjson"), inspect.ndjson);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlob(path.join(RENDER_DIR, `${stem}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(
      path.join(RENDER_DIR, `${stem}.layout.json`),
      await layout.text(),
    );
  }

  const pptx = await PresentationFile.exportPptx(presentation);
  const temporaryPptx = path.join(ASSET_DIR, ".reference-layouts.build.pptx");
  await fs.rm(temporaryPptx, { force: true });
  try {
    await pptx.save(temporaryPptx);
    normalizePptx(temporaryPptx, layouts.length);
    await fs.rename(temporaryPptx, OUTPUT_PPTX);
  } finally {
    await fs.rm(temporaryPptx, { force: true });
    await fs.rm(`${temporaryPptx}.inspect.ndjson`, { force: true });
    await fs.rm(`${OUTPUT_PPTX}.inspect.ndjson`, { force: true });
  }

  createPreview();
  console.log(
    `生成完了: slides=${layouts.length}, pptx=${OUTPUT_PPTX}, preview=${OUTPUT_PREVIEW}`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
