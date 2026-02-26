# Food Label Risk Scan System — System TechSpec
**System Version:** v1.0.0-alpha  
**Schema Standard:** JSON Schema Draft 2020-12  
**Dictionary Format:** JSON  
**Source of Truth:** This repository (GitHub)

---

## 1. Purpose & Scope (Alpha)

### 1.1 Goal
Scan food label images (single or multiple pages) and produce:
1) Replayable, reviewable text extraction and block structure  
2) Deterministic structural/format/relationship findings (stable, reproducible)  
3) High-recall semantic risk candidates (LLM; variance allowed)  
4) Deterministic severity assignment (0 variance)  
5) Guardrail validation + dedup + final output assembly

### 1.2 Alpha Non-Goals
- No legal/compliance conclusion (no “compliant/illegal”)
- No remediation guidance or operational instructions
- No external authenticity verification (no database lookup, no lab-test assumption)
- No bbox-level fine-grained OCR accuracy guarantee beyond best effort
- No final “structured field extraction” beyond blocks (Stage Alpha)

---

## 2. Global Constraints (MUST)

1) **No legal conclusion**: never output “违法/合规/违规” as a conclusion.
2) **No remediation**: never provide “how to fix” instructions.
3) **Evidence fidelity**: any evidence snippet MUST be an exact substring from extracted raw text (except missing-type rules which use `"N/A"`).
4) **No hallucinated text**: no words that do not exist in the image extraction.
5) **Separation of concerns**:
   - LLM modules do not assign severity.
   - Deterministic modules do not perform semantic risk discovery.
6) **Versioned outputs**: each module output MUST include required version metadata.

---

## 3. Architecture Overview

## Implementation Notes (Dify Integration) — Non-normative

The current reference implementation uses **Dify** as the workflow/orchestration framework.
This section documents integration notes only and does not change any normative contracts.

### Module-to-Workflow Mapping (reference)
- BlockExtractor: Dify LLM node
- DeterministicRuleEngine: Dify Code node (deterministic execution)
- SemanticRiskDetector: Dify LLM node
- SeverityMapper: Dify Code node (deterministic mapping)
- GuardrailAggregator: Dify Code node (validation + dedup + assembly)

### Data Passing
Artifacts are passed between nodes as JSON variables:
- Block extraction artifact (raw_text_lines + blocks)
- Deterministic risk list
- Semantic risk list
- Severity mapping artifact

Dictionaries (intents/regex/thresholds, severity mapping) are injected as configuration constants.
All evidence snippets must remain exact substrings of extracted raw text.

### Portability
System contracts, schemas, and module responsibilities are framework-agnostic.
The workflow engine may be replaced in future versions without changing module naming or data contracts.

### 3.1 Modules (Responsibility Names — no “Layer” naming)
- **BlockExtractor** (LLM)
- **DeterministicRuleEngine** (Code)
- **SemanticRiskDetector** (LLM)
- **SeverityMapper** (Code)
- **GuardrailAggregator** (Code)

### 3.2 Execution Order (current v1.0.0-alpha)
1) BlockExtractor  
2) DeterministicRuleEngine  
3) SemanticRiskDetector  
4) SeverityMapper  
5) GuardrailAggregator

> Execution order may change in future versions. Module names remain stable.

---

## 4. Data Contracts (System-Level)

### 4.1 Global Object Model (high-level)
- **BlockExtractionArtifact**: raw_text_lines + blocks
- **DeterministicRiskListArtifact**: deterministic findings
- **SemanticRiskListArtifact**: semantic findings (no severity)
- **SeverityMappingArtifact**: risk_type → severity results
- **FinalOutputArtifact**: validated, deduplicated final_risk_list

### 4.2 Central Schemas
All schema definitions are centralized in `schemas/`:
- `schemas/block.schema.json`
- `schemas/risk-object.schema.json`
- `schemas/system-output.schema.json`

Schema versioning:
- Each schema file MUST declare `$schema` = Draft 2020-12
- Each schema MUST carry a `schema_version` field (string) or embed it via `$id`

---

## 5. System Input Contract

### 5.1 System Input (concept)
The system accepts one or more images, in order.

Recommended input shape (implementation may wrap differently):
```json
{
  "system_version": "1.0.0-alpha",
  "request_id": "string",
  "images": [
    {
      "source_page": 1,
      "image_url": "string (optional)",
      "image_base64": "string (optional)"
    }
  ],
  "metadata": {
    "product_id": "string (optional)",
    "channel": "string (optional)"
  }
}
````

**MUST**

* Each image has a stable `source_page` starting from 1.
* The scan is processed in `source_page` order.

---

## 6. System Output Contract

### 6.1 Output (concept)

Final output is a single JSON object assembled by GuardrailAggregator.

Recommended system output shape:

```json
{
  "system_version": "1.0.0-alpha",
  "request_id": "string",
  "artifacts": {
    "block_extraction": {},
    "deterministic_risks": {},
    "semantic_risks": {},
    "severity_mapping": {},
    "guardrail_summary": {}
  },
  "final_risk_list": [],
  "errors": []
}
```

### 6.2 Required Module Metadata (MUST)

Each module artifact MUST include:

* `system_version`
* `module_name` (one of the stable names)
* `module_version`
* `spec_version`
* `dict_version` (only if that module depends on dict/config)
* `schema_version` (the schema version used for validation)

---

## 7. Module Boundaries (MUST)

### 7.1 BlockExtractor (LLM)

**Does**

* OCR-like extraction into `raw_text_lines`
* Grouping into `blocks`
* Provides normalized coordinates (as per module spec)

**Does NOT**

* Output risks
* Output severity
* Judge missing items
* Correct or rewrite text

### 7.2 DeterministicRuleEngine (Code)

**Does**

* Mandatory field presence checks (missing_*)
* Format/pattern validation (format_*)
* Relationship closure checks (relationship_*), including “weak trigger ambiguous” policy

**Does NOT**

* Semantic risk discovery
* Severity assignment

**Output requirement**

* `detection_method` must be `"rule_guardrail"`

**Dict dependency**

* Uses JSON dictionaries for intents/regex/thresholds.

### 7.3 SemanticRiskDetector (LLM)

**Does**

* High-recall semantic discovery (claims, contradictions within-image, ingredient boundary signals, etc.)
* Must bind evidence to `block_id` and `raw_snippet`

**Does NOT**

* Missing checks
* Format checks
* Relationship checks
* Severity assignment

### 7.4 SeverityMapper (Code)

**Does**

* Deterministically map `risk_type` (+ optional sub-tags) to severity enum
* Enforces “critical whitelist” policy (if adopted)

**Does NOT**

* Read image
* Re-interpret text semantically

**Dict dependency**

* Uses a JSON mapping dictionary.

### 7.5 GuardrailAggregator (Code)

**Does**

* Schema validation
* Enum validation
* Evidence binding validation
* Fingerprint generation
* Deduplication & merge
* Assemble `final_risk_list`

**Does NOT**

* Discover new risks
* Alter evidence snippets

---

## 8. Evidence Policy (MUST)

### 8.1 Evidence Fields

All risks must include:

* `evidence.block_id`
* `evidence.raw_snippet`

### 8.2 Snippet Rules

* For **missing_*** risks: `raw_snippet` must be `"N/A"`.
* For all other risks: `raw_snippet` must be an **exact substring** from `blocks[].text_raw` (or directly from `raw_text_lines[].text`) with no rewriting.

---

## 9. Severity Policy (MUST)

Severity enum:

* `low | medium | high | critical`

**MUST**

* Severity is assigned only by SeverityMapper (deterministic).
* LLM modules must not output severity.

(If you adopt a “critical whitelist” policy, it must live in SeverityMapper dict/spec, not in prompts.)

---

## 10. Deduplication & Fingerprint Policy

### 10.1 Dedup Key (recommended)

GuardrailAggregator generates a stable fingerprint for each risk.

Recommended fingerprint inputs:

* `risk_type`
* `detection_method`
* `evidence.block_id`
* normalized(`evidence.raw_snippet`)  *(missing uses "N/A")*

Hash:

* `sha256` over the concatenated canonical string

### 10.2 Merge Rule (recommended)

* If two risks share the same fingerprint → keep one.
* If they share same `risk_type` + same snippet but different severity → keep the **higher** severity (should not happen if SeverityMapper is deterministic; treat as error if occurs).

---

## 11. Error Handling (MUST)

### 11.1 Error Object

System output `errors[]` should contain structured errors:

* `error_code`
* `module_name`
* `message`
* `severity` (info/warn/error)
* `context` (optional)

### 11.2 Failure Strategy (Alpha)

* If BlockExtractor fails → abort (cannot proceed)
* If DeterministicRuleEngine fails → proceed with semantic only, mark error
* If SemanticRiskDetector fails → proceed with deterministic only, mark error
* If SeverityMapper fails → abort final output (severity is required)
* If GuardrailAggregator fails → abort final output

---

## 12. Versioning & Change Control

### 12.1 SemVer

* Breaking contract change → bump MAJOR
* Backward-compatible addition → bump MINOR
* Fix/typo/threshold adjustment → bump PATCH
* Stage suffix used in Alpha: `-alpha` (and optional `.N`)

### 12.2 Required Change Log

All breaking changes require:

* Schema update
* Module spec update
* `docs/changelog/changelog_v1.md` entry
* Risk type registry update if applicable

---

## 13. Repository Artifacts & Naming (Normative)

Canonical repository structure:

* `docs/system/` system-level techspec
* `docs/modules/` per-module techspec
* `docs/registry/` risk type registry
* `schemas/` JSON Schemas (Draft 2020-12)
* `dicts/` JSON dictionaries (intents/regex/thresholds/mappings)
* `prompts/` LLM prompts (versioned)
* `src/` deterministic code modules (versioned)
* `tests/` golden cases and unit tests

> Dict format is JSON for all modules that use configurable patterns/mappings.

---

End of System TechSpec

```
