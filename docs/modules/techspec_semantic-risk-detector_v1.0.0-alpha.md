# SemanticRiskDetector — Module TechSpec（模块技术规范）

Module Name: `SemanticRiskDetector`  
Module Type: LLM  
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`SemanticRiskDetector`（SRD）只负责“高召回语义风险发现”，输出**基础结构草稿**，供下游 Code 节点进行严格 JSON 化。

中文说明：
- SRD 专注“发现问题”。
- SRD 不承担最终契约化输出职责。

---

## 2. In Scope / Out of Scope

### In Scope
- 语义风险候选发现（高召回）
- 证据引用（`block_id` + `raw_snippet`）
- 基础草稿结构输出（可被后置节点规范化）

### Out of Scope
- 缺失项规则判断（`missing_*`）
- 格式规则判断（`format_*`）
- 关系闭合规则判断（`relationship_*`）
- 严重程度分级（`severity`）
- 最终 JSON 契约化输出（由 SemanticRiskFormatter 负责）
- 法律结论与整改建议

---

## 3. Input Contract / 输入契约

Required input:
- `block_extraction_artifact` (from BlockExtractor)

Runtime note:
- Prompt uses single Jinja expansion: `{{block_extraction_artifact}}`
- 避免同参数重复展开导致上下文膨胀

---

## 4. Output Contract / 输出契约（草稿）

SRD 输出为“草稿对象（draft）”，例如：

```json
{
  "findings": [
    {
      "risk_type_hint": "semantic_cross_language_inconsistency",
      "block_id": "B0008",
      "raw_snippet": "string",
      "risk_description": "string",
      "risk_logic": "string"
    }
  ]
}
```

Hard constraints:
- `findings` 可为空数组
- 每条 finding 必须尽量包含 `block_id` + `raw_snippet`
- 不输出 `severity`
- 不输出法律结论、整改建议

---

## 5. Downstream Handoff / 下游交接

SRD 输出交给 `SemanticRiskFormatter`（Code）进行：
- 字段标准化
- 风险类型归一
- 契约补齐（module/version/schema/detection_method）
- 严格 JSON 化

---

## 6. Discovery Framework / 发现框架

Recommended check groups:
1. Ingredient & population applicability semantics
2. Claim vs nutrition semantics
3. Advertisement-law-sensitive wording
4. Mandatory-label semantic clarity (without missing checks)
5. Cross-block contradiction / misleading expression
6. Cross-language consistency and translation drift
7. English-only key label information without Chinese counterpart

---

## 7. Orchestration / 编排位置

- BlockExtractor 后并行分支：DRE + SRD
- SRD 下游先进入 `SemanticRiskFormatter` 再进入 SeverityMapper/GuardrailAggregator

---

## 8. Dify Runtime Baseline / Dify 运行基线

Reference files:
- Prompt: `prompts/semantic-risk-detector/prompt_v1.0.0-alpha.txt`
- Model config: `prompts/semantic-risk-detector/model_config_v1.0.0-alpha.json`

Current baseline:
- model: `qwen3.5-plus`
- response format: `json_object`
- node display name: `SEMANTIC RISK DETECTOR`

---

## 9. Validation Checklist / 校验清单

- 单对象 JSON 输出
- `findings` 为数组
- 尽量包含 evidence
- 不输出 DRE-only 风险类型
- 不输出 severity / 法律结论 / 整改建议
