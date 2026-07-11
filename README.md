# spetest

AI横断のSkills / Workflows設計を検証するためのパイロットリポジトリです。

## 現在のパイロット

- Task Skill: `.agents/skills/impact-analysis-readonly/`
- Workflow正本: `docs/agent-workflows/impact-investigation.md`
- 影響分析データ契約: `schemas/impact-analysis.schema.yml`
- Skill eval: `tools/ai-harness/skill-evals/impact-analysis-readonly/`

影響調査は、単純な全文検索ではなく、変更原子の正規化、多面的な探索、依存経路の証拠化、網羅性ゲートを通して実施します。Task Skillは読み取り専用であり、調査成果物の保存とライフサイクル管理はWorkflow側の責務です。

## ローカル検証

Python 3.11以降を前提とします。

```bash
python -m pip install -r tools/requirements.txt
python .agents/skills/impact-analysis-readonly/scripts/validate_impact_analysis.py \
  tools/ai-harness/skill-evals/impact-analysis-readonly/fixtures/valid-analysis.yml
python .agents/skills/impact-analysis-readonly/scripts/build_impact_graph.py \
  tools/ai-harness/skill-evals/impact-analysis-readonly/fixtures/valid-analysis.yml
python tools/ai-harness/skill-evals/impact-analysis-readonly/run_mechanical_checks.py
```

負例は検証失敗が正常です。

```bash
python .agents/skills/impact-analysis-readonly/scripts/validate_impact_analysis.py \
  tools/ai-harness/skill-evals/impact-analysis-readonly/fixtures/invalid-no-impact.yml
```
