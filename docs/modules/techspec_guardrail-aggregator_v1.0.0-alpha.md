# GuardrailAggregator — Module TechSpec（模块技术规范）

Module Name: `GuardrailAggregator`
Module Type: Code (deterministic)
Version: `v1.0.0-alpha`

---

## 1. Purpose / 模块目标

`GuardrailAggregator` 是全链路最后一道确定性治理闸门。
它负责把多分支产物做统一校验、去重、合并，并输出最终对外交付对象。

中文说明：
- 本模块不“发现新风险”，只做治理与汇总。
- 必须保持同输入同输出（0 方差），用于审计与回放。

---

## 2. Upstream Inputs / 上游输入

Required inputs:
- `block_extraction_artifact`
- `deterministic_risks_artifact`（DRE 输出，可为空）
- `semantic_risks_artifact`（语义分支输出，可为空）
- `severity_mapping_artifact`（SeverityMapper 输出，可为空）

Optional inputs:
- `errors[]`（上游节点错误列表，可为空）
- `request_id`（若编排层传入）

Input assumptions:
- 输入 JSON 可解析。
- 风险对象至少包含：`risk_type`、`detection_method`、`evidence`。
- 当某分支失败时，允许进入降级汇总路径，但必须在 `errors` 留痕。
- `severity_mapping_artifact` 可缺失；但若存在，必须是合法对象。

---

## 3. Core Responsibilities / 核心职责

### 3.1 Structural Validation / 结构校验
- 校验 artifact 顶层字段是否完整（module/version/spec/schema 等）。
- 校验 `risk_list` / `severity_list` 的数组结构合法性。

### 3.2 Enum & Policy Validation / 枚举与策略校验
- 校验 `detection_method` 是否属于允许集合。
- 校验 `severity` 是否属于 `low|medium|high|critical`。
- 对不合法枚举值写入 `errors`，按策略剔除或降级。

### 3.3 Evidence Binding Validation / 证据绑定校验
- 非 `missing_*` 风险：`evidence.raw_snippet` 必须是 `raw_text_lines` 或 `blocks.text_raw` 的逐字子串。
- `missing_*` 风险：允许 `raw_snippet = "N/A"`。
- 无 `block_id` 或证据无法回放时，必须记录错误。

### 3.4 Fingerprint & Dedup / 指纹与去重
- 对风险对象生成稳定指纹（推荐：`risk_type + detection_method + block_id + normalized_snippet`）。
- 同指纹只保留一条。
- 若同一风险出现冲突等级，按确定性规则处理（默认保留较高等级并写入错误日志）。

### 3.5 Merge & Final Assembly / 合并与最终组装
- 合并 DRE + SRD 风险。
- 按 `severity_mapping_artifact` 回填等级（若存在）。
- 生成 `final_risk_list`、汇总 `errors`、输出最终工件。


### 3.6 Severity Artifact Handling / Severity 工件处理规则

GuardrailAggregator 对 `severity_mapping_artifact` 采用“优先消费 + 严格校验 + 可降级”策略：

1) **Artifact 缺失**
- 记录错误：`SEVERITY_ARTIFACT_MISSING`。
- 若策略要求必须分级：终止最终输出。
- 若允许降级：继续输出，但 `final_risk_list` 中 `severity` 置为 `unknown`（或按固定 fallback），并写入错误上下文。

2) **Artifact 存在但结构非法**（如 `severity_list` 非数组、字段缺失）
- 记录错误：`SEVERITY_ARTIFACT_INVALID`。
- 不信任该 artifact 内容，按缺失策略处理（同上）。

3) **Artifact 内有输入错误记录**（如 `INVALID_UPSTREAM_INPUT`）
- 将该错误透传到最终 `errors`。
- 对受影响 risk 不做静默映射，按降级策略处理。

4) **正常映射场景**
- 以 `risk_type` 为主键做回填。
- 若同一 `risk_type` 出现多个 `severity`，按固定优先级处理并记录冲突：
  `critical > high > medium > low`。

5) **未命中映射场景**
- 记录错误：`SEVERITY_NOT_MAPPED`，并包含 `risk_type`。
- 按策略执行：终止 / 固定 fallback（必须在实现中固定）。

---

## 4. Output Contract / 输出契约

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "GuardrailAggregator",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "final_risk_list": [
    {
      "risk_type": "string",
      "detection_method": "rule_guardrail|llm",
      "severity": "low|medium|high|critical|unknown",
      "evidence": {
        "block_id": "B0001",
        "raw_snippet": "string"
      },
      "risk_description": "string",
      "risk_logic": "string",
      "fingerprint": "sha256:string"
    }
  ],
  "errors": [
    {
      "error_code": "string",
      "module_name": "string",
      "message": "string",
      "severity": "info|warn|error",
      "context": {}
    }
  ]
}
```

Output guarantees:
- `final_risk_list` 可为空但必须是数组。
- 每条最终风险应可追溯来源与证据。
- 即使分支失败，`errors` 必须结构化记录。

---

## 5. Determinism Rules / 确定性规则

- 同一输入多次执行，输出顺序与内容必须一致。
- 去重与冲突处理策略必须固定，不得依赖随机行为。
- 不允许调用 LLM 或外部不稳定服务。

---

## 6. Out of Scope / 非职责范围

- 不新增风险类型。
- 不重新解释语义、不过度改写上游 `risk_description` / `risk_logic`。
- 不自行计算或重判 severity（仅消费 SeverityMapper 输出）。
- 不输出法律结论或整改建议。

---

## 7. Orchestration Position / 编排位置

建议编排：
1) BlockExtractor
2) DRE + SRD（并行）
3) SeverityMapper
4) GuardrailAggregator（最终汇总）

说明：
- GuardrailAggregator 是统一收口节点。
- 该节点输出即系统最终风险清单来源。

---

## 8. Failure & Degradation Policy / 失败与降级策略

- DRE 失败：保留 SRD 分支结果并记录错误。
- SRD 失败：保留 DRE 分支结果并记录错误。
- SeverityMapper 失败或 severity artifact 非法：若业务要求“必须分级”，则终止；否则按固定降级策略输出并写入错误。
- GuardrailAggregator 自身失败：终止最终输出。

---

## 9. Validation Checklist / 校验清单

- 输入 JSON 可解析。
- 证据子串校验通过率可统计。
- 去重前后数量变化可解释。
- 输出不含非法枚举。
- `final_risk_list` 与 `errors` 都是数组。
- 重放同输入结果一致。
