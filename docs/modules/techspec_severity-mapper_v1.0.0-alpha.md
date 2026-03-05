# SeverityMapper — Module TechSpec（模块技术规范）

Module Name: `SeverityMapper`  
Module Type: Code (deterministic)  
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`SeverityMapper` 负责将上游风险对象中的 `risk_type` 映射为稳定的 `severity` 枚举。

中文说明：
- 该模块是确定性代码节点，不使用 LLM。
- 目标是把等级判断从语义发现中剥离，保证 0 方差。

---

## 2. Input Contract / 输入契约

Required inputs:
- `deterministic_risks_artifact`（来自 DRE）
- `semantic_risks_artifact`（来自 SemanticRiskFormatter）
- `severity_mapping_dict`（来自映射字典）

Dictionary reference:
- `dicts/severity-mapper/severity_mapping_v1.0.0-alpha.yaml`

Input assumptions:
- risk object 至少包含 `risk_type`、`detection_method`、`evidence`。
- 允许某一上游分支失败（如 SRD 空或异常），模块应对可用输入继续映射。

---

## 3. Output Contract / 输出契约

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "SeverityMapper",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "dict_version": "v1.0.0-alpha",
  "detection_method": "mapping",
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
- 相同 `risk_type` 必须得到稳定一致的等级。
- 未命中映射的 `risk_type` 必须按策略处理（默认降级为 `medium` 或标记待审），策略需固定。
- 不得改写上游 evidence 文本。

---

## 4. Responsibilities / 职责边界

### Does
- 根据字典进行 `risk_type -> severity` 确定性映射
- 输出可被 GuardrailAggregator 合并的等级信息
- 对未知 risk_type 采用固定 fallback 策略

### Does NOT
- 不发现新风险
- 不删除已有风险对象
- 不做语义重解释

---

## 5. Why Code Node / 为什么必须是 Code 节点

- 等级映射是规则字典驱动、可审计逻辑。
- 需要可重复、可回放、可追责，不应受 LLM 随机性影响。
- 与 DRE 一样属于确定性治理链路。

结论：`SeverityMapper` 在 v1.0.0-alpha 必须走 **Code**，不走 LLM。

---

## 6. Orchestration / 编排位置

Pipeline stage:
1) BlockExtractor
2) DRE + SRD（并行）
3) SeverityMapper（Code）
4) GuardrailAggregator（Code）

---

## 7. Validation Checklist / 校验清单

- 输入 artifact JSON 可解析
- `risk_type` 到 `severity` 映射成功率可统计
- 输出仅包含合法 severity 枚举
- 同输入重复执行结果一致
