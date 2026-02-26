# Terminology / 术语对照表  
Version: v1.0.0-alpha  

---

## 1. Modules / 模块

| English (Module Name) | 中文名称 | Notes |
|---|---|---|
| BlockExtractor | 分块提取器（文本识读与分块模块） | LLM module. Extracts `raw_text_lines` and `blocks`. |
| DeterministicRuleEngine | 确定性规则引擎 | Code module. Runs deterministic checks (missing/format/relationship). |
| SemanticRiskDetector | 语义风险检测器（高召回语义发现） | LLM module. Semantic discovery only, no severity. |
| SeverityMapper | 严重程度映射器 | Code module. Maps `risk_type` → `severity` deterministically. |
| GuardrailAggregator | 守卫聚合器（校验与汇总模块） | Code module. Validates schema/enums, dedup, fingerprint, final output. |

---

## 2. Core Concepts / 核心概念

| English | 中文 | Notes |
|---|---|---|
| Block | 文本块/语义块 | A grouped region of text on the label image. |
| raw_text_lines | 原始文本行 | Line-level extracted text, strictly faithful to image. |
| blocks | 分块结果 | Structured blocks containing grouped lines. |
| block_type | 块类型 | Enum defining functional area (ingredient/nutrition/etc.). |
| bbox | 外接框 | Bounding box of a line/block (normalized coordinates). |
| normalized coordinates | 归一化坐标 | (x,y,w,h) all in 0~1 relative to image size. |
| evidence | 证据 | References block_id and raw snippet from original text. |
| raw_snippet | 原文片段（逐字） | Must be an exact substring from image text extraction. |
| missing check | 缺失项检查 | Deterministic existence checks (e.g., net content missing). |
| format validation | 格式校验 | Deterministic string/pattern checks (e.g., unit case). |
| relationship validation | 关系校验 | Deterministic field-combination integrity checks. |
| strong trigger | 强触发 | Strong context patterns implying relationship mode. |
| weak trigger | 弱触发 | Ambiguous context patterns, lower severity / softer risk type. |

---

## 3. Risk Output / 风险输出相关

| English | 中文 | Notes |
|---|---|---|
| risk_type | 风险类型 | Must be registered in Risk Type Registry. |
| Risk Type Registry | 风险类型注册表 | Closed set of risk types + metadata. |
| RiskObject | 风险对象 | Standard risk record in final output. |
| detection_method | 检测方式 | Enum: `rule_guardrail` or `llm` (alpha baseline). |
| rule_guardrail | 确定性规则检测 | Produced by DeterministicRuleEngine. |
| llm | LLM 检测 | Produced by LLM modules (semantic discovery). |
| severity | 严重程度 | Enum: low / medium / high / critical. |
| severity mapping | 严重程度映射 | Deterministic mapping from risk_type. |
| fingerprint | 指纹 | Stable ID for dedup/traceability (hash-based). |
| deduplication | 去重 | Merge risks with same fingerprint or same dedup key. |

---

## 4. Governance / 治理与版本

| English | 中文 | Notes |
|---|---|---|
| Source of Truth | 单一事实源 | This repo is the only authoritative spec source. |
| schema | 数据契约/结构定义 | JSON Schema Draft 2020-12 is used. |
| dict / dictionary | 字典配置 | YAML config for keywords/regex/thresholds/mapping. |
| spec_version | 规范版本 | Version of spec document governing the module/system. |
| module_version | 模块版本 | Version of implementation/prompt for a module. |
| dict_version | 字典版本 | Version of YAML dict used by deterministic modules. |
| breaking change | 破坏性变更 | Requires MAJOR version bump. |

---

## 5. Canonical Naming Rules / 命名规范摘要

- Module names are **English** and stable (no layer numbering).
- JSON fields and schema keys are **English**.
- `risk_type` and `block_type` must use `snake_case`.
- Dictionaries are stored as **YAML** and versioned.
- Schemas follow **JSON Schema Draft 2020-12**.

---

End of Terminology
