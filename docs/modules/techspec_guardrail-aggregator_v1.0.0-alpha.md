# GuardrailAggregator — Module TechSpec（模块技术规范）

Module Name: `GuardrailAggregator`  
Module Type: Code (deterministic)  
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`GuardrailAggregator` 负责对多分支结果做“守卫式治理”：校验、去重、合并、组装最终输出。

中文说明：
- 这是最终出站前的质量闸门。
- 必须为确定性代码节点，保证输出可重复。

---

## 2. Input Contract / 输入契约

Required inputs:
- `block_extraction_artifact`
- `deterministic_risks_artifact`（可为空）
- `semantic_risks_artifact`（来自 SemanticRiskFormatter，可为空）
- `severity_mapping_artifact`（可为空）

Optional input:
- `errors[]`（上游节点异常记录）

---

## 3. Core Functions / 核心功能

1. Schema validation
   - 校验各 artifact 是否满足约定结构。
2. Enum validation
   - 校验 `detection_method`、`severity` 等枚举值。
3. Evidence binding validation
   - 校验 `evidence.raw_snippet` 是否为上游抽取文本子串。
4. Fingerprint generation
   - 对风险对象生成稳定指纹（用于去重和追踪）。
5. Dedup & merge
   - 合并 DRE/SRD 风险，去掉重复项。
6. Final assembly
   - 组装 `final_risk_list` 和 `errors`。

---

## 4. Output Contract / 输出契约

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "GuardrailAggregator",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "final_risk_list": [],
  "errors": []
}
```

Output guarantees:
- `final_risk_list` 中每条风险结构完整。
- 合并后风险可追溯到来源分支。
- 当某分支失败时仍可产出降级结果，并在 `errors` 中记录。

---

## 5. Responsibilities / 职责边界

### Does
- 汇总 DRE + SRD + SeverityMapper 输出
- 执行治理规则（校验/去重/合并）
- 形成对外最终风险结果

### Does NOT
- 不发现新风险
- 不重新判定 severity
- 不改写上游 evidence 文本

---

## 6. Why Code Node / 为什么必须是 Code 节点

- 涉及校验、去重、指纹、组装等强一致性逻辑。
- 必须保证同输入同输出，不允许 LLM 漂移。

结论：`GuardrailAggregator` 在 v1.0.0-alpha 必须走 **Code**，不走 LLM。

---

## 7. Orchestration / 编排位置

- DRE 与 SRD 并行完成后，先经 SeverityMapper（等级映射），
- 再统一进入 GuardrailAggregator 进行最终汇总。

即：**DRE/SRD 最终汇总节点是 GuardrailAggregator**。

---

## 8. Validation Checklist / 校验清单

- 多分支输入可为空但结构合法
- 去重前后数量变化可解释
- `final_risk_list` 不含无效 evidence
- 错误分支信息进入 `errors`
- 重复执行结果稳定一致
