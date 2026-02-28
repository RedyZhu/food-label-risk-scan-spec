# DeterministicRuleEngine — Module TechSpec（模块技术规范）
Version: v1.0.0-alpha
Module Name: `DeterministicRuleEngine`
Module Type: `Code`
System Version: `v1.0.0-alpha`
Schema Standard: JSON Schema Draft 2020-12

---

## 1. Purpose / 模块目标

`DeterministicRuleEngine` consumes BlockExtractor artifacts and emits deterministic risk findings for:

- mandatory presence checks (`missing_*`)
- format/pattern checks (`format_*`)
- relationship integrity checks (`relationship_*` / ambiguous entrust context)

The module is strictly deterministic: same input + same dictionary => same output.

中文说明：
- 本模块读取 BlockExtractor 输出，产出“可复现、可回归”的确定性风险结果。
- 只覆盖三类规则：缺失项、格式项、关系项。
- 在相同输入与相同字典版本下，输出必须完全一致。

---

## 2. Scope and Boundaries / 范围与边界

### 2.1 Must do / 必须执行

- Read `raw_text_lines` and `blocks` from BlockExtractor output.
- Use dictionary-configured intents / regex / thresholds.
- Emit only rule-based risks with `detection_method = "rule_guardrail"`.
- Keep evidence snippets as exact substrings from extracted text (except missing risks using `"N/A"`).
- Include module metadata fields in output.

中文说明：
- 必须使用字典驱动（关键词、正则、阈值）执行规则。
- 非缺失类风险必须绑定原文证据片段（逐字子串），不得改写。
- 输出必须包含版本元数据，保证追踪与审计。

### 2.2 Must not do / 严禁行为

- No semantic risk discovery.
- No severity assignment.
- No legal/compliance conclusion.
- No remediation suggestion.
- No hallucinated evidence text.

中文说明：
- 不做语义推断，不做严重程度映射，不做法务结论。
- 不得输出整改建议，不得编造证据文本。

---

## 3. Input Contract / 输入契约

Input is a JSON object containing at least:

- `raw_text_lines[]`
  - `line_id: string`
  - `text: string`
  - `source_page: integer`
- `blocks[]`
  - `block_id: string`
  - `block_type: string`
  - `text_raw: string`
  - `source_page: integer`

The engine builds deterministic match scopes:

- global concatenated text
- per-page concatenated text
- per-block text

Normalization is only for matching (optional, dictionary-driven):

- fullwidth punctuation normalization
- whitespace collapsing
- lowercase matching

中文说明：
- 输入以 `raw_text_lines` 与 `blocks` 为准。
- 可做归一化仅限“匹配阶段”；证据输出必须来自原始文本。
- 建议按全局、分页、分块三个作用域执行匹配，保证规则稳定。

---

## 4. Dictionary Contract / 字典契约

Dictionary contains:

- `dict_version`
- `intents` (intent keyword groups)
- `regex` (named patterns with optional flags)
- `thresholds` (rule thresholds)

Reference dictionary path:

- `dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.json`

> Note: dictionary schema should be versioned and kept consistent with implementation parser.

中文说明：
- 字典是规则行为的唯一可配置来源。
- 字典结构若调整，必须同步升级 `dict_version` 与实现解析器。

---

## 5. Output Contract / 输出契约

The module outputs a JSON object:

```json
{
  "system_version": "v1.0.0-alpha",
  "module_name": "DeterministicRuleEngine",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "dict_version": "v1.0.0-alpha",
  "schema_version": "draft-2020-12",
  "detection_method": "rule_guardrail",
  "risk_list": []
}
```

Each risk object includes:

- `risk_type`
- `detection_method` (`rule_guardrail`)
- `evidence.block_id`
- `evidence.raw_snippet`
- `risk_description`
- `risk_logic`

Evidence rule:

- `missing_*`: `block_id = "N/A"`, `raw_snippet = "N/A"`
- others: snippet must be exact substring in extracted raw text

中文说明：
- 缺失类风险因无证据文本，统一使用 `N/A`。
- 其余风险必须带 `block_id` + `raw_snippet`，并严格逐字匹配上游抽取文本。

---

## 6. Rule Groups / 规则分组

### 6.1 Missing checks / 缺失项规则

- `missing_net_content`
- `missing_product_name`
- `missing_ingredient_list`
- `missing_manufacturer_info`
- `missing_date_shelf_life`
- `missing_standard_code`
- `missing_production_license`

### 6.2 Format checks / 格式项规则

- `format_unit_case_inconsistent`
- `format_net_content_pattern_unusual`
- `format_standard_code_pattern_unusual`
- `format_license_code_pattern_unusual`

### 6.3 Relationship checks / 关系项规则

- `incomplete_entrust_relationship`
- `entrusted_context_ambiguous`

中文说明：
- 分组遵循“结构可见性优先”原则，不引入语义推断。
- 风险类型命名保持 `snake_case`，并与注册表保持一致。

---

## 7. Determinism and Deduplication / 确定性与去重

- Rule evaluation order is fixed: missing -> format -> relationship.
- Dedup is deterministic:
  - For `raw_snippet = "N/A"`: dedup key = `risk_type`
  - Otherwise: dedup key = `risk_type + normalized(raw_snippet)`

中文说明：
- 规则执行顺序固定，避免同输入出现顺序漂移。
- 去重策略对同类重复证据稳定收敛，保证输出可比对。

---

## 8. Error Handling / 异常处理

- Invalid dictionary shape should raise parsing/configuration errors.
- Runtime should not silently invent defaults that alter risk semantics.
- Upstream malformed input should be handled predictably and surfaced via execution failure or upstream guardrails.

中文说明：
- 字典结构错误应显式报错，不得静默吞错。
- 不允许通过隐式默认值改变风险判定语义。

---

## 9. CLI Reference / 命令行示例

```bash
python src/deterministic_rule_engine/engine_v1_0_0_alpha.py \
  --dict dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.json \
  --input <block_extractor_output.json>
```

中文说明：
- CLI 仅用于离线验证与回归，不改变模块契约。

---

## 10. Versioning / 版本策略

- `module_version`: implementation version
- `spec_version`: this spec version
- `dict_version`: dictionary version used in current run

Breaking changes require version bump and synchronized update of:

- this techspec
- dictionary file(s)
- downstream contract expectations

中文说明：
- 发生破坏性变更时，必须同步更新规范、字典、下游预期，避免联调偏差。

---

## 11. Dify Patterns Node Baseline / Dify 字典节点基线

Reference node config:

- `dicts/deterministic-rule-engine/dify_node_config_v1.0.0-alpha.json`

Baseline (current):

- node_name: `DRE Patterns Dictionary`
- node_type: `Code`
- input_params: none
- output_mode: default
- output_key: `output`
- output_type: `string` (Dify transformed content)

中文说明：
- 该节点仅负责输出规则字典，不依赖上游业务输入参数。
- Dify Code 节点默认输出变量通常为 `output`（字符串）。
- 下游 DeterministicRuleEngine 节点需按 JSON 解析后再作为 patterns 配置使用。
