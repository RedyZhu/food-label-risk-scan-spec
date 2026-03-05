# SeverityMapper — Module TechSpec（模块技术规范）

Module Name: `SeverityMapper`
Module Type: LLM
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`SeverityMapper` 负责将上游风险对象映射到 `severity`，输出 `severity_mapping_artifact`。

中文说明：
- 当前阶段该节点采用 LLM。
- 该节点只做等级映射，不新增风险。

---

## 2. Input Contract / 输入契约

Required inputs:
- `deterministic_risks_artifact`
- `semantic_risks_artifact`
- `severity_mapping_dict`（可选，作为提示词内参考规则）

Input assumptions:
- 上游风险对象至少包含 `risk_type`、`detection_method`、`evidence`。
- 允许某个分支为空。

---

## 3. Output Contract / 输出契约

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "SeverityMapper",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "detection_method": "llm_mapping",
  "severity_list": [
    {
      "risk_type": "semantic_claim_exaggeration",
      "severity": "medium"
    }
  ]
}
```

Severity enum:
- `low`
- `medium`
- `high`
- `critical`

Hard constraints:
- `severity` 仅可取上述枚举。
- 不得改写上游 evidence 内容。
- 不得新增/删除上游风险对象，只做映射输出。

---

## 4. Responsibilities / 职责边界

### Does
- 基于风险类型与上下文给出 severity
- 输出可被 GuardrailAggregator 合并的 `severity_list`

### Does NOT
- 不发现新风险
- 不改写风险描述与证据
- 不输出法律结论

---

## 5. Why LLM (Current Stage) / 当前阶段为何采用 LLM

- 当前阶段优先验证等级策略与评估标准。
- 通过提示词快速迭代分级口径，后续可回切确定性映射。

---

## 6. Orchestration / 编排位置

Pipeline stage:
1) BlockExtractor
2) DRE + SRD（并行）
3) SeverityMapper（LLM）
4) GuardrailAggregator（Code）

---

## 7. Validation Checklist / 校验清单

- 输出 JSON 可解析
- `severity` 仅为合法枚举
- `risk_type` 与上游可对齐
- 同输入多次执行波动可观测（当前阶段允许）
