# SemanticRiskFormatter — Module TechSpec（模块技术规范）

Module Name: `SemanticRiskFormatter`  
Module Type: Code (deterministic)  
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`SemanticRiskFormatter` 负责把 SRD 草稿结果转换为严格契约化的 `semantic_risks_artifact`。

结论：该节点必须是 **Code**，不走 LLM。

---

## 2. Input Contract / 输入契约

Required inputs:
- `semantic_findings_draft`（来自 SRD）
- `block_extraction_artifact`（用于 evidence 二次校验）

---

## 3. Core Functions / 核心功能

1. Normalize
   - `risk_type_hint` 归一到标准 `risk_type`
2. Contract fill
   - 补齐 `system/module/spec/schema/detection_method`
3. Evidence guard
   - 校验 `block_id` 存在
   - 校验 `raw_snippet` 为上游文本子串
4. Drop invalid
   - 丢弃不满足最小约束项并记录错误

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
  "risk_list": []
}
```

---

## 5. Responsibilities / 职责边界

### Does
- SRD 草稿到正式 artifact 的严格转换
- 保证下游 SeverityMapper/GuardrailAggregator 可直接消费

### Does NOT
- 不发现新风险
- 不做 severity 映射

---

## 6. Orchestration / 编排位置

- SRD（LLM）后置节点
- 产出的 `semantic_risks_artifact` 进入 SeverityMapper 和 GuardrailAggregator
