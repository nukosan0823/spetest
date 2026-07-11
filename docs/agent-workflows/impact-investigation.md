---
name: impact-investigation
version: 1.0.0
owner: risk-system-group
status: draft
riskLevel: high
allowedExecutionModes: [investigation_only]
---

# 影響調査Workflow

## 目的

変更要求に対し、要件・コード・データ・IF・ジョブ・実行実績・テスト・運用・セキュリティ・手動処理を横断して影響を特定し、監査可能な証拠パッケージと対応方針を作成します。

Task Skill `impact-analysis-readonly`は読み取り専用の分析だけを担当し、本WorkflowがInvestigationの作成・状態遷移・人間レビュー・保存を担当します。

## 入力

- 調査依頼と変更前後の内容
- 対象リポジトリ、基準ブランチ、commit SHA
- 関連するcapability、contract、job、table等の恒久ID
- 外部設計書・ジョブ定義・運用記録の参照先
- 希望する保証レベル: triage / standard / high_assurance

## 権限境界

- Execution Modeは`investigation_only`に固定します。
- 書き込み先は`investigations/INV-*/`だけです。
- 本体コード、`.agents/skills/`、`specs/`、`schemas/`、ジョブ定義、DB、外部システムを変更しません。
- 実装が必要と判明した場合も現タスク内では昇格せず、INVを閉じて別Featureを起票します。

## 標準フロー

### Phase 1: triage

1. INV番号を採番し、statusを`open`にします。
2. 依頼を変更原子`changeSeeds`へ分解します。
3. 対象・除外・保証レベル・必要な証拠源を確定します。
4. repository commitと各外部情報の取得日時を固定します。
5. statusを`triaged`へ遷移します。

曖昧な変更内容、参照権限不足、調査対象オーナー不明がある場合は、分析開始前に確認します。

### Phase 2: impact

1. statusを`analyzing`、`phases.impact.status`を`in_progress`にします。
2. `impact-analysis-readonly`を実行します。
3. 結果を`analysis.yml`として保存します。
4. validatorを実行し、構造・参照・網羅性・no-impact条件を確認します。
5. 影響経路図と人間向け要約を構造化データから生成します。
6. validation成功後、`phases.impact.status`を`done`にします。

### Phase 3: review

1. statusを`reviewing`にします。
2. capabilityオーナーが対象範囲、影響経路、unknown、conflictを確認します。
3. high_assuranceの場合は、業務・セキュリティ・データ等の該当オーナーを追加します。
4. `completeness: partial | blocked`の場合、原則として影響フェーズへ戻します。
5. 必須情報が取得不能なら`inconclusive`または`external_escalation_required`で閉じます。

### Phase 4: direction

影響なしの場合、`direction.status: not_required`と理由を記録します。

影響ありの場合は、評価基準、選択肢、採否、棄却理由、推奨案、confidenceを`direction.yml`へ記録します。`confidence: low`の案からFeatureを起票しません。

影響を認識しながら対応しない場合は、`noActionBasis: risk_accepted`と`riskAcceptedBy`を必須にします。

### Phase 5: close

1. resolutionを`no_action`、`follow_up_required`、`inconclusive`、`external_escalation_required`等から設定します。
2. 必要な後続作業を`recommendedFollowUps`へ記録します。
3. statusを`closed`へ遷移し、closedAt / closedByを記録します。
4. Feature等が後日作られた場合だけ`realizedBy`を追記します。

closed後、調査本文・証拠・scope・mode・結論を書き換えません。誤りや新条件による再調査は新INVを作成し、supersedes / supersededByで接続します。

## 成果物

```text
investigations/INV-<番号>/
├── manifest.yml
├── analysis.yml
├── evidence/
│   └── index.yml
├── direction.yml
└── report.md
```

- `manifest.yml`: 状態、分類、フェーズ、resolution、後続リンク
- `analysis.yml`: 変更原子、調査面、証拠、影響経路、網羅性、結論
- `evidence/index.yml`: 証拠のメタデータと外部保管先ポインタ
- `direction.yml`: 対応案比較。影響なしならnot_required
- `report.md`: 上記構造化データから生成する人間向け要約

## 完了基準

- 全changeSeedが解決済みまたはowner付きunknownになっている
- 全調査面がcompleted / not_applicable / blockedのいずれかで明示されている
- requiredな調査面がblockedならno impactで閉じていない
- factsと影響経路の全エッジに証拠がある
- completenessとresolutionが整合している
- high_assuranceの重大影響は独立した2種類以上の証拠で確認されている
- 「影響あり×対応しない」はriskAcceptedByが存在する
- validatorが成功している

<!-- ai-executable:begin -->
## AI実行手順
inputs:
  - 調査依頼と変更前後
  - 対象リポジトリと基準commit
steps:
  - Execution Modeをinvestigation_onlyに固定する
  - INVをtriageしchangeSeeds・scope・assuranceLevelを確定する
  - impact-analysis-readonlyで多面的な影響分析を実行する
  - analysis.ymlをvalidatorで検証する
  - 人間レビュー後にdirectionを実施またはnot_requiredとする
  - resolutionとrecommendedFollowUpsを記録してINVを閉じる
outputs:
  - investigations/INV-*/ 配下の証拠パッケージ
<!-- ai-executable:end -->
