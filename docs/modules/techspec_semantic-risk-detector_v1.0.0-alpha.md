# SemanticRiskDetector — Module TechSpec（模块技术规范）

Module Name: `SemanticRiskDetector`
Module Type: LLM
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`SemanticRiskDetector`（SRD）负责“高召回语义风险发现”，并直接输出契约化 `semantic_risks_artifact`。

中文说明：
- SRD 专注语义候选发现与证据绑定。
- SRD 与 DRE 并行，不承担 DRE 的缺失/格式/关系规则职责。

---

## 2. In Scope / Out of Scope

### In Scope
- 高召回语义风险发现
- 证据绑定（`evidence.block_id` + `evidence.raw_snippet`）
- 输出标准 `risk_list[]`

### Out of Scope
- `missing_*` / `format_*` / `relationship_*` 规则判断
- 法律结论与整改建议
- 外部数据库核验

---

## 3. Input Contract / 输入契约

Required input:
- `block_extraction_artifact`

Runtime note:
- Prompt 使用唯一输入变量（Dify 节点变量注入）
- 避免重复注入同一大 JSON

---

## 4. Output Contract / 输出契约

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "SemanticRiskDetector",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "schema_version": "risk-object.schema.v1.0.0-alpha",
  "detection_method": "llm",
  "risk_list": [
    {
      "risk_type": "string",
      "detection_method": "llm",
      "evidence": {
        "block_id": "B0001",
        "raw_snippet": "string"
      },
      "risk_description": "string",
      "risk_logic": "string"
    }
  ]
}
```

Hard constraints:
- `risk_list` 可为空数组
- `raw_snippet` 必须来自上游原文子串
- 不得输出 `missing_*` / `format_*` / `relationship_*` 风险类型
- 不得输出法律结论、整改建议

---

## 5. Orchestration / 编排位置

- BlockExtractor 后并行分支：DRE + SRD
- SRD 输出直接进入 SeverityMapper（LLM）与 GuardrailAggregator

---

## 6. Runtime Baseline / 运行基线

- Prompt: `prompts/semantic-risk-detector/prompt_v1.1.0-alpha.txt`
- Model Config: `prompts/semantic-risk-detector/model_config_v1.0.0-alpha.json`
- Dify Node Name: `SEMANTIC RISK DETECTOR`

---

## 7. Validation Checklist / 校验清单

- 输出为单对象 JSON
- `risk_list` 为数组
- 每条风险包含 `risk_type/evidence/risk_description/risk_logic`
- 无 `severity` 字段
- 无 DRE-only 风险类型
