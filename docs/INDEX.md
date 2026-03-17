# Food Label Risk Scan System
Documentation Index
Version: v1.1.0

---

## 0. Source of Truth

This repository is the single source of truth for:
- Unified system specification
- Data contracts (schemas)
- Runtime dictionaries
- Prompt/model configs

---

## 1. Reading Order (Recommended)

1) Unified System Spec
2) Schemas
3) Runtime prompts/configs
4) Dictionaries

---

## 2. Unified System Specification

- `docs/system/techspec_system_v1.1.0.md`

> From v1.1.0 onward, independent module TechSpec files are removed.
> Module responsibilities are consolidated into the unified system spec.

---

## 3. Core Schemas

- `schemas/block.schema.json`
- `schemas/risk-object.schema.json`
- `schemas/system-output.schema.json`

---

## 4. Runtime Prompts & Configs

### BlockExtractor
- `prompts/block-extractor/prompt_v1.0.0-alpha.txt`
- `prompts/block-extractor/model_config_v1.0.0-alpha.json`

### SemanticRiskDetector
- `prompts/semantic-risk-detector/prompt_v1.0.0-alpha.txt`
- `prompts/semantic-risk-detector/prompt_v1.1.0-alpha.txt`
- `prompts/semantic-risk-detector/model_config_v1.0.0-alpha.json`

### SeverityMapper
- `prompts/severity-mapper/prompt_v1.0.0-alpha.txt`
- `prompts/severity-mapper/model_config_v1.0.0-alpha.json`

---

## 5. Dictionaries

### DeterministicRuleEngine
- `dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.json`
- `dicts/deterministic-rule-engine/dify_node_config_v1.0.0-alpha.json`

### Severity Mapping
- `dicts/severity-mapper/severity_mapping_v1.0.0-alpha.yaml`

---

## 6. Terminology

- `docs/system/terminology_v1.0.0-alpha.md`
