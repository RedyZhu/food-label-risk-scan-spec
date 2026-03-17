# Food Label Risk Scan System — Unified TechSpec
**System Version:** v1.1.0
**Schema Standard:** JSON Schema Draft 2020-12
**Source of Truth:** This repository

---

## 1. Purpose & Scope

### 1.1 Goal
Given one or more food-label images, produce a replayable and auditable final artifact with:
1) Text blocks (`raw_text_lines` + `blocks`)
2) Deterministic risks (rule-based)
3) Semantic risks (LLM-based)
4) Per-risk severity mapping
5) Guardrail validation, dedup, and final assembly

### 1.2 Non-Goals
- No legal verdict (no "违法/合规" conclusions)
- No remediation suggestions
- No external authenticity verification

---

## 2. Global Constraints (MUST)

1. **Evidence fidelity**: for non-missing risks, `evidence.raw_snippet` MUST be exact substring of upstream extracted text.
2. **No hallucinated text**: all evidence must come from extraction artifacts.
3. **Separation of concerns**:
   - Semantic risk discovery is only in SemanticRiskDetector.
   - Severity assignment is only in SeverityMapper.
   - Final governance (dedup/validation/final merge) is only in GuardrailAggregator.
4. **Versioned artifacts**: all module outputs include version metadata.
5. **Schema-first contracts**: runtime artifacts must satisfy centralized schemas in `schemas/`.

---

## 3. End-to-End Pipeline (Unified)

### 3.1 Runtime Stages
1. **BlockExtractor (LLM)**
2. **Parallel risk detection branches**
   - DeterministicRuleEngine (Code)
   - SemanticRiskDetector (LLM)
3. **SeverityMapper (LLM)**
4. **GuardrailAggregator (Code)**

### 3.2 Stage Responsibilities

#### BlockExtractor
- Input: ordered images
- Output: `BlockExtractionArtifact`
- Owns: OCR text structuring only
- Does NOT: create risks / assign severity

#### DeterministicRuleEngine
- Input: `BlockExtractionArtifact` + deterministic dictionary
- Output: `DeterministicRiskListArtifact`
- Owns: mandatory checks, format/relationship deterministic checks
- Does NOT: semantic discovery / severity assignment

#### SemanticRiskDetector
- Input: `BlockExtractionArtifact`
- Output: `SemanticRiskListArtifact`
- Owns: high-recall semantic risk discovery
- Does NOT: deterministic mandatory checks / severity assignment

#### SeverityMapper
- Input: deterministic + semantic risk artifacts (+ optional mapping dict)
- Output: `SeverityMappingArtifact`
- Owns: per-risk severity assignment
- MUST output stable matching anchors per item:
  - `source_module`
  - `source_risk_index`
  - `detection_method`
  - `evidence.block_id`
  - `evidence.raw_snippet`
  - optional `fingerprint`

#### GuardrailAggregator
- Input: block artifact + two risk artifacts + severity artifact
- Output: `FinalOutputArtifact`
- Owns:
  - structural validation
  - evidence binding validation
  - severity backfill and conflict handling
  - fingerprint governance + dedup + final assembly

---

## 4. Data Contracts

### 4.1 Canonical Artifacts
- `BlockExtractionArtifact`
- `DeterministicRiskListArtifact`
- `SemanticRiskListArtifact`
- `SeverityMappingArtifact`
- `FinalOutputArtifact`

### 4.2 Central Schemas
- `schemas/block.schema.json`
- `schemas/risk-object.schema.json`
- `schemas/system-output.schema.json`

### 4.3 Matching & Linkage Policy
Severity backfill match priority:
1. `source_module + source_risk_index`
2. `fingerprint` (if available)
3. `risk_type + detection_method + evidence.block_id + normalized(evidence.raw_snippet)`
4. `risk_type` (weak fallback; must log warning)

### 4.4 Fingerprint Policy
- Canonical generation point: **GuardrailAggregator**.
- Upstream modules MAY provide fingerprint; if present, GuardrailAggregator validates format.
- If absent, GuardrailAggregator generates deterministically.

---

## 5. Input/Output (System)

### 5.1 System Input (concept)
- One or more images with stable page order (`source_page` ascending from 1).

### 5.2 System Output (concept)
- A single final JSON assembled by GuardrailAggregator, including:
  - `final_risk_list`
  - `errors`
  - required version metadata

---

## 6. Failure & Degradation Policy

1. If one detection branch fails, the other may continue; GuardrailAggregator records branch errors.
2. If `severity_mapping_artifact` is missing/invalid:
   - record structured error
   - apply configured policy (abort or degrade to fixed fallback)
3. If required upstream fields are missing, modules must emit `INVALID_UPSTREAM_INPUT` with explicit `missing_fields`.

---

## 7. Dify Integration Notes (Non-Normative)

- Recommended node display names (uppercase with spaces):
  - `BLOCK EXTRACTOR`
  - `DETERMINISTIC RULE ENGINE`
  - `SEMANTIC RISK DETECTOR`
  - `SEVERITY MAPPER`
  - `GUARDRAIL AGGREGATOR`
- Artifacts should be passed as parsed JSON objects (not string-wrapped JSON text).

---

## 8. Versioning

- This unified specification is `v1.1.0`.
- Independent module TechSpec documents are removed in v1.1.0 to avoid contract divergence.
- Contract changes must be reflected in:
  1) this file,
  2) `schemas/`,
  3) relevant prompts/dicts.

