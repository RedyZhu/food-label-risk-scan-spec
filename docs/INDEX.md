# Food Label Risk Scan System
Documentation Index
Version: v1.0.0-alpha

---

## 0. Source of Truth

This repository is the **single source of truth** for:

- System architecture
- Module responsibilities
- Data contracts (schemas)
- Risk type registry
- Deterministic rule definitions
- LLM prompt versions

All specifications here are version-controlled.
No external document (Google Docs, etc.) overrides this repository.

---

## 1. Reading Order (Recommended)

If you are new to this system, read in the following order:

1️⃣ System Overview
2️⃣ Data Schemas
3️⃣ Risk Type Registry
4️⃣ Module Specifications
5️⃣ Dictionaries & Pattern Definitions

---

## 2. System-Level Specification

- System TechSpec
  `docs/system/techspec_system_v1.0.0-alpha.md`

This document defines:

- Overall architecture
- Execution order
- Global constraints
- System input/output contracts
- Versioning policy

---

## 3. Core Data Contracts (Schemas)

All modules must strictly follow these schemas.

- Block Schema
  `schemas/block.schema.json`

- Risk Object Schema
  `schemas/risk-object.schema.json`

- System Output Schema
  `schemas/system-output.schema.json`

⚠ Schema definitions are centralized here.
Modules must reference them instead of redefining fields.

---

## 4. Module Specifications

Each module has its own TechSpec document.

### 4.1 BlockExtractor
- Spec
  `docs/modules/techspec_block-extractor_v1.0.0-alpha.md`
- Prompt
  `prompts/block-extractor/prompt_v1.0.0-alpha.txt`
- Dify Runtime Model Config
  `prompts/block-extractor/model_config_v1.0.0-alpha.json`

Responsibility:
- OCR-based text extraction
- Block grouping
- Structured output
- No risk detection

---

### 4.2 DeterministicRuleEngine
- Spec
  `docs/modules/techspec_deterministic-rule-engine_v1.0.0-alpha.md`
- Patterns / Regex Dictionary
  `dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.json`
- Dify Node Config (Patterns Injector)
  `dicts/deterministic-rule-engine/dify_node_config_v1.0.0-alpha.json`
- Code
  `src/deterministic_rule_engine/engine_v1_0_0_alpha.py`

Responsibility:
- Mandatory field checks
- Format validation
- Structural relationship validation
- Deterministic rule execution
- Output detection_method = rule_guardrail

---

### 4.3 SemanticRiskDetector
- Spec
  `docs/modules/techspec_semantic-risk-detector_v1.0.0-alpha.md`
- Prompt
  `prompts/semantic-risk-detector/prompt_v1.0.0-alpha.txt`

Responsibility:
- High-recall semantic risk discovery
- Claim analysis
- Contradiction detection (within image only)
- No severity assignment

---

### 4.4 SeverityMapper
- Spec
  `docs/modules/techspec_severity-mapper_v1.0.0-alpha.md`
- Severity Mapping Dictionary
  `dicts/severity-mapper/severity_mapping_v1.0.0-alpha.json`
- Code
  `src/severity_mapper/mapper_v1_0_0_alpha.py`

Responsibility:
- Map risk_type → severity
- Enforce severity constraints
- Deterministic mapping only

---

### 4.5 GuardrailAggregator
- Spec
  `docs/modules/techspec_guardrail-aggregator_v1.0.0-alpha.md`
- Code
  `src/guardrail_aggregator/aggregator_v1_0_0_alpha.py`

Responsibility:
- Schema validation
- Risk deduplication
- Fingerprint generation
- Final output assembly

---

## 5. Risk Type Registry

- Registry Document
  `docs/registry/risk_type_registry_v1.0.0-alpha.md`

This document defines:

- risk_type (closed set)
- category
- detection_method
- allowed severity range
- version introduced

No new risk_type may be added without updating this registry.

---

## 6. Dictionaries & Pattern Definitions

All configurable rule components are defined separately from code.

### DeterministicRuleEngine Patterns
- `dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.json`

Includes:
- Intent keywords
- Regex patterns
- Threshold definitions
- Strong/weak trigger classification

### Severity Mapping Rules
- `dicts/severity-mapper/severity_mapping_v1.0.0-alpha.json`

Includes:
- risk_type → severity mapping
- detection_method overrides
- severity constraints

---

## 7. Versioning Strategy

Each module has independent versioning.

System Version: `v1.0.0-alpha`

Each module output must include:
- system_version
- module_name
- module_version
- spec_version
- dict_version (if applicable)

Breaking changes require:
- MAJOR version increment
- Schema update
- Change log update

---

## 8. Change Log

- `docs/changelog/changelog_v1.md`

All architectural, schema, or rule changes must be recorded.

---

## 9. Governance Principles

1. Schemas are centralized.
2. risk_type is a closed registry.
3. Deterministic logic must not depend on LLM output.
4. Prompts must be versioned.
5. Dictionary updates must bump dict_version.
6. No module may redefine another module’s responsibility.

---

End of INDEX
