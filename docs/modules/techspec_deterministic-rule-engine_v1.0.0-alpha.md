# DeterministicRuleEngine  
Module Technical Specification  
模块技术规范（确定性规则引擎）  
Version: v1.0.0-alpha  
Schema Standard: JSON Schema Draft 2020-12  
Dictionary: `dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.yaml`  

---

## 1. Module Identity  
## 1. 模块标识

- module_name: `DeterministicRuleEngine`
- module_type: `Code`
- upstream: `BlockExtractor`
- downstream:
  - `SeverityMapper`
  - `GuardrailAggregator`

中文说明：  
本模块由代码实现，负责“结构/格式/关系”的确定性校验。  
给定同样的输入，输出必须完全一致（可回归、可复现）。

---

## 2. Purpose  
## 2. 模块目标

This module performs deterministic validations on the BlockExtractor output:

- Mandatory field existence checks（必填字段存在性检查）
- Format / pattern validation（格式与形态校验，regex 驱动）
- Relationship integrity checks（主体关系闭合校验）

中文说明：  
本模块只做“看得到/匹配得到”的确定性判断，不做语义推断，不做外部真实性核验。

---

## 3. Scope (Must / Must Not)  
## 3. 范围定义（必须 / 禁止）

### 3.1 Must Do / 必须执行
- Consume BlockExtractor output (`raw_text_lines`, `blocks`)
- Use YAML dictionary configuration for:
  - keywords/intents
  - regex patterns
  - thresholds
- Emit only deterministic risk objects
- Bind evidence to original extracted text
- Ensure reproducibility: same input => same output

### 3.2 Must Not / 严禁行为
- Must not call LLM or use probabilistic reasoning
- Must not modify original text (`text_raw`, `raw_text_lines.text`)
- Must not perform semantic risk detection (claims, exaggeration, contradiction reasoning)
- Must not output legal conclusions or remediation suggestions

---

## 4. Inputs  
## 4. 输入

### 4.1 Required Inputs
- `coordinate_system`
- `image_size`
- `raw_text_lines[]`
- `blocks[]`

### 4.2 Matching Text Construction (For Matching Only)
The engine may construct a `match_text` for matching, but must not alter evidence.

Allowed normalization (matching only):
- fullwidth → halfwidth
- collapse whitespace
- lowercase for matching

中文说明：  
归一化仅用于“匹配”，证据片段必须来自原文，不得用归一化后的字符串作为证据输出。

---

## 5. Outputs  
## 5. 输出

The module outputs a single JSON object containing deterministic risk list.

### 5.1 detection_method
All risks emitted by this module MUST set:

- `detection_method = "rule_guardrail"`

### 5.2 Evidence Requirements
- Missing-type risks: `raw_snippet = "N/A"`
- All other risks: `raw_snippet` must be an exact substring from:
  - some `raw_text_lines.text`, or
  - some `blocks.text_raw`

Evidence must include `block_id` when snippet is not `N/A`.

中文说明：  
缺失项没有可引用原文，统一用 `"N/A"`；  
格式/关系类必须提供原文片段。

---

## 6. Risk Taxonomy (Deterministic Only)  
## 6. 风险分类（仅确定性）

This module can emit risks under three categories:

1) `missing_*` — mandatory field missing signals  
2) `format_*` — format/pattern anomalies (shape only)  
3) `relationship_*` — relationship integrity signals

中文说明：  
语义风险（宣称夸大、功效暗示、适用人群等）不属于本模块。

---

## 7. Rule Groups and Definitions  
## 7. 规则组与定义

All rules must be deterministic and based on:
- intent keyword matches
- regex matches
- simple counts / thresholds

Rule definitions reference dictionary keys from:  
`dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.yaml`

---

### 7.1 Mandatory Existence Checks (`missing_*`)  
### 7.1 必填字段存在性（missing_*）

#### R-MISS-001 missing_net_content
- risk_type: `missing_net_content`
- trigger (any_of):
  - intent: `net_content_intent`
  - regex: `net_content_value`
  - regex: `net_content_multi`
- logic:
  - If none matched across all pages/blocks => trigger missing
- evidence:
  - block_id: `"N/A"`
  - raw_snippet: `"N/A"`

中文说明：  
“净含量/规格”的存在性兜底，允许通过“关键词”或“数值+单位形态”命中。

---

#### R-MISS-002 missing_product_name
- risk_type: `missing_product_name`
- trigger:
  - no `title` block found OR all title blocks have extremely short `text_raw` (<= 2 visible chars)
- evidence:
  - `"N/A"`

中文说明：  
这是结构性兜底规则，不做“品名是否正确”的判断。

---

#### R-MISS-003 missing_ingredient_list
- risk_type: `missing_ingredient_list`
- trigger (any_of):
  - intent: `ingredient_intent`
  - any block_type == `ingredient`
- logic:
  - If neither matched => missing
- evidence:
  - `"N/A"`

---

#### R-MISS-004 missing_manufacturer_info
- risk_type: `missing_manufacturer_info`
- trigger (any_of):
  - intent: `producer_intent`
  - any block_type == `producer`
- evidence:
  - `"N/A"`

---

#### R-MISS-005 missing_date_shelf_life
- risk_type: `missing_date_shelf_life`
- trigger (any_of):
  - intent: `date_shelf_life_intent`
  - regex: `date_ymd_numeric`
  - regex: `date_ymd_cn`
  - any block_type == `date_shelf_life`
- evidence:
  - `"N/A"`

---

#### R-MISS-006 missing_standard_code
- risk_type: `missing_standard_code`
- trigger (any_of):
  - intent: `standard_label_intent`
  - regex: `standard_code`
  - any block_type == `standard`
- logic:
  - If none matched => missing
- evidence:
  - `"N/A"`

---

#### R-MISS-007 missing_production_license
- risk_type: `missing_production_license`
- trigger (any_of):
  - intent: `license_label_intent`
  - regex: `sc_code`
  - any block_type == `license`
- evidence:
  - `"N/A"`

---

### 7.2 Format / Pattern Validation (`format_*`)  
### 7.2 格式与形态校验（format_*）

Format checks must:
- not correct text
- not assume compliance requirements
- only report observed pattern anomalies

All format risks MUST include:
- evidence.block_id
- evidence.raw_snippet (original substring)

---

#### R-FMT-001 format_unit_case_inconsistent
- risk_type: `format_unit_case_inconsistent`
- detection: per page OR per block (implementation choice must be consistent)
- trigger examples:
  - `unit_ml_upper` and `unit_ml_mixed` both appear in same scope
  - `unit_l_upper` and `unit_l_lower` both appear in same scope
- evidence:
  - pick the snippet containing the “non-primary form” within that scope (prefer shorter)
  - block_id must point to the block containing that snippet

中文说明：  
仅报告“同域混用”这一现象，不判断哪个写法是对的。

---

#### R-FMT-002 format_net_content_pattern_unusual
- risk_type: `format_net_content_pattern_unusual`
- trigger:
  - intent `net_content_intent` matched
  - but neither `net_content_value` nor `net_content_multi` matched in the same scope (page recommended)
- evidence:
  - snippet containing the label keyword (e.g., "净含量")
  - block_id of that snippet

中文说明：  
用于捕捉“净含量标签出现但值缺失/形态无法识别”的情况。  
它与 `missing_net_content` 不冲突：前者是“存在但不完整”，后者是“完全没看到”。

---

#### R-FMT-003 format_standard_code_pattern_unusual
- risk_type: `format_standard_code_pattern_unusual`
- trigger:
  - intent `standard_label_intent` matched
  - but regex `standard_code` not matched in same scope
- evidence:
  - snippet containing label keyword (e.g., "执行标准")
  - block_id of that snippet

---

#### R-FMT-004 format_license_code_pattern_unusual
- risk_type: `format_license_code_pattern_unusual`
- trigger:
  - intent `license_label_intent` matched
  - but regex `sc_code` not matched in same scope
- evidence:
  - snippet containing label keyword (e.g., "SC")
  - block_id of that snippet

---

### 7.3 Relationship Integrity Checks (`relationship_*`)  
### 7.3 主体关系闭合校验（relationship_*）

Relationship checks validate completeness of field combinations.
They do not determine truth; only structure.

All relationship risks MUST include evidence snippet.

---

#### R-REL-001 incomplete_entrust_relationship (Strong Trigger)
- risk_type: `incomplete_entrust_relationship`
- trigger:
  - intent `entrusted_party_strong_intent` matched
  - and intent `principal_party_intent` NOT matched (global scope)
- evidence:
  - snippet containing a strong entrusted phrase (e.g., "受委托生产企业")
  - block_id containing that snippet

中文说明：  
强触发代表“明显进入委托语境”，但没有看到委托方要素，因此输出“关系未闭合线索”。

---

#### R-REL-002 entrusted_context_ambiguous (Weak Trigger, Safer)
- risk_type: `entrusted_context_ambiguous`
- trigger (all_of):
  - NOT matched: `entrusted_party_strong_intent`
  - matched: `entrusted_party_weak_intent`
  - weak intent occurrence count <= `entrust_weak_trigger_max_count`
  - same block matched `producer_intent` keyword hits >= `producer_context_keyword_min_hits_for_weak_entrust`
  - and NOT matched: `principal_party_intent` (global)
- evidence:
  - snippet containing weak phrase (e.g., "受托生产商")
  - block_id of that snippet

中文说明：  
这是为降低误伤的“软提示”。  
常见场景：把“生产商”误写为“受托生产商”。  
此时不直接输出强关系异常，而输出 ambiguous 线索。

---

## 8. Evidence Picking Policy  
## 8. 证据选取策略

### 8.1 Missing Risks
- evidence.block_id = `"N/A"`
- evidence.raw_snippet = `"N/A"`

### 8.2 Non-missing Risks
- evidence.raw_snippet must be a contiguous substring of original text
- choose the shortest snippet that still contains:
  - the trigger keyword OR
  - the trigger pattern
- evidence.block_id must refer to block containing snippet

中文说明：  
证据要短、准、可定位。不要输出整段长文。

---

## 9. Deduplication Keys (Within This Module)  
## 9. 模块内去重规则

To avoid repeated detections, the module must deduplicate by:

- missing_* : `risk_type`
- others    : `risk_type + normalized(raw_snippet)`

Normalization for dedup key only:
- trim whitespace
- collapse whitespace
- lowercase (ASCII only)

中文说明：  
同一条证据不要重复输出多次。

---

## 10. Minimal Output JSON Structure  
## 10. 最小输出结构

The module must output one JSON object:

{
  "system_version": "v1.0.0-alpha",
  "module_name": "DeterministicRuleEngine",
  "module_version": "v1.0.0-alpha",
  "spec_version": "v1.0.0-alpha",
  "dict_version": "v1.0.0-alpha",
  "schema_version": "draft-2020-12",
  "detection_method": "rule_guardrail",
  "risk_list": [
    {
      "risk_type": "missing_net_content",
      "detection_method": "rule_guardrail",
      "evidence": { "block_id": "N/A", "raw_snippet": "N/A" },
      "risk_description": "Net content field not observed",
      "risk_logic": "No net content intent or value pattern was detected in the extracted text"
    }
  ]
}

中文说明：  
severity 不在本模块输出（由 SeverityMapper 决定）。  
如需 hint，可在后续版本新增 `severity_hint`，但 alpha 不建议。

---

## 11. Error Handling  
## 11. 异常处理

- If input schema is invalid:
  - emit an error record (recommended) OR return empty risk_list (alpha fallback)
- If dictionary missing:
  - fail fast (recommended), do not guess
- If no blocks/lines:
  - risk_list may contain only missing_* detections (if matching scope is empty)

中文说明：  
规则引擎不做“猜测”。字典缺失必须报错或直接中断。

---

End of DeterministicRuleEngine TechSpec
