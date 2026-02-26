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
