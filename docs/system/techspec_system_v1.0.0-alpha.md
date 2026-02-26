# Food Label Risk Scan System

System Technical Specification
Version: v1.0.0-alpha
Schema Standard: JSON Schema Draft 2020-12

---

## 1. System Overview

The Food Label Risk Scan System is a modular architecture designed to:

* Extract structured textual blocks from food label images
* Detect structural and semantic risk signals
* Enforce deterministic guardrails
* Produce reproducible, auditable risk outputs

This system follows a **modular responsibility architecture**.
Each module has a strictly defined boundary and must not override another module’s responsibility.

This repository is the single source of truth.

See also:
`docs/system/terminology_v1.0.0-alpha.md`

---

## 2. Architectural Principles

### 2.1 Determinism First

All structural, format, and relationship validations must be handled by deterministic logic.

LLM modules are reserved for:

* Text extraction
* Semantic interpretation
* High-recall discovery

Deterministic logic must never depend on probabilistic LLM reasoning.

---

### 2.2 Single Source of Data Contracts

All JSON structures must comply with schemas defined in:

* `schemas/block.schema.json`
* `schemas/risk-object.schema.json`
* `schemas/system-output.schema.json`

No module may redefine schema fields locally.

Schema standard: JSON Schema Draft 2020-12.

---

### 2.3 Closed Risk Registry

All `risk_type` values must be defined in:

`docs/registry/risk_type_registry_v1.0.0-alpha.md`

No undocumented risk_type may be emitted.

---

## 3. Execution Order (Current Architecture)

1. BlockExtractor
2. DeterministicRuleEngine
3. SemanticRiskDetector
4. SeverityMapper
5. GuardrailAggregator

Execution order may evolve in future versions,
but module names remain stable.

---

## 4. Module Responsibilities

### 4.1 BlockExtractor (LLM)

Input:

* Food label images

Output:

* raw_text_lines
* structured blocks

Responsibilities:

* OCR-based text recognition
* Block grouping
* Structured JSON output

Must NOT:

* Detect risks
* Assign severity
* Perform compliance judgments

---

### 4.2 DeterministicRuleEngine (Code)

Input:

* BlockExtractor output

Responsibilities:

* Mandatory field existence checks
* Format validation (regex-based)
* Structural relationship validation
* Deterministic rule execution

Output:

* Risk objects
* detection_method = "rule_guardrail"

Must:

* Use YAML dictionary configuration
* Use regex for pattern validation
* Not rely on LLM reasoning

Dictionary source:
`dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.yaml`

---

### 4.3 SemanticRiskDetector (LLM)

Input:

* Image
* Structured blocks

Responsibilities:

* Semantic claim detection
* Contradiction detection (within image only)
* High-recall risk identification

Must NOT:

* Assign severity
* Perform deterministic field checks
* Override DeterministicRuleEngine results

---

### 4.4 SeverityMapper (Code)

Input:

* risk_type
* detection_method

Responsibilities:

* Map risk_type → severity
* Enforce severity constraints
* Ensure closed severity enumeration

Severity mapping dictionary:
`dicts/severity-mapper/severity_mapping_v1.0.0-alpha.yaml`

Severity Enum:

* low
* medium
* high
* critical

---

### 4.5 GuardrailAggregator (Code)

Responsibilities:

* Schema validation (Draft 2020-12 compliant)
* Risk deduplication
* Fingerprint generation
* Final risk list assembly
* Output normalization

Must:

* Reject schema violations
* Reject unknown risk_type
* Reject invalid severity values

---

## 5. System Input Contract

Defined in:

`schemas/system-output.schema.json` (input section)

Minimal logical structure:

* system_version: string
* request_id: string
* images: array

  * source_page: integer
  * image_url: string (optional)
  * image_base64: string (optional)

---

## 6. System Output Contract

Final output must comply with:

`schemas/system-output.schema.json`

Core output sections:

* block_extraction
* deterministic_risks
* semantic_risks
* severity_mapping
* final_risk_list

Each risk object must comply with:

`schemas/risk-object.schema.json`

---

## 7. Versioning Policy

System version: v1.0.0-alpha

Each module must include:

* module_name
* module_version
* spec_version
* dict_version (if applicable)

Breaking change rules:

| Change Type         | Required Action              |
| ------------------- | ---------------------------- |
| Schema change       | MAJOR version bump           |
| New risk_type       | Registry update + MINOR bump |
| Regex change        | dict_version bump            |
| Prompt modification | module_version bump          |

---

## 8. Deterministic Rule Policy

All pattern validation must:

* Use YAML-based configuration
* Use regex for:

  * Standard codes
  * License numbers
  * Net content formats
  * Date formats
* Avoid heuristic guessing

Weak/Strong trigger logic must be explicitly defined in dictionary configuration.

---

## 9. Governance Constraints

The system must never:

* Output legal conclusions
* Use the terms “compliant” or “illegal”
* Provide remediation instructions
* Perform external authenticity verification (Alpha scope)

All logic must be reproducible.

---

## 10. Audit & Reproducibility

Each system execution must be reproducible using:

* system_version
* module versions
* dict_version
* prompt version
* input images

Deterministic modules must produce identical output given identical input.

LLM modules may vary but must bind evidence to original text snippets.

---

## 11. Future Extension Areas (Non-Binding)

* Multi-model voting
* OCR confidence arbitration
* Cross-page contradiction detection
* Risk confidence scoring
* Statistical calibration layer

These are not included in v1.0.0-alpha.

---

End of System Technical Specification

---
