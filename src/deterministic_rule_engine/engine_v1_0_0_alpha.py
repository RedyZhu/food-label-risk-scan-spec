#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeterministicRuleEngine v1.0.0-alpha
Schema Standard: JSON Schema Draft 2020-12

Reads:
- BlockExtractor output JSON (raw_text_lines, blocks)
- YAML dict: dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.yaml

Emits:
- Deterministic risk_list with detection_method = "rule_guardrail"
- No severity assignment (handled by SeverityMapper)

Usage (CLI):
  python engine_v1_0_0_alpha.py --dict ../../dicts/deterministic-rule-engine/patterns_v1.0.0-alpha.yaml \
      --input block_extractor_output.json > deterministic_risks.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml


# -----------------------------
# Constants
# -----------------------------
SYSTEM_VERSION = "v1.0.0-alpha"
MODULE_NAME = "DeterministicRuleEngine"
MODULE_VERSION = "v1.0.0-alpha"
SPEC_VERSION = "v1.0.0-alpha"
SCHEMA_VERSION = "draft-2020-12"
DETECTION_METHOD = "rule_guardrail"


# -----------------------------
# Helpers: normalization (match only)
# -----------------------------
_FULLWIDTH_MAP = {  # minimal common fullwidth conversions
    ord("："): ":",
    ord("（"): "(",
    ord("）"): ")",
    ord("，"): ",",
    ord("。"): ".",
    ord("；"): ";",
    ord("【"): "[",
    ord("】"): "]",
    ord("％"): "%",
    ord("＋"): "+",
    ord("－"): "-",
    ord("／"): "/",
    ord("×"): "×",  # keep multiplication symbol
}

def _to_halfwidth(s: str) -> str:
    # Convert some common punctuation; leave letters/digits untouched.
    return s.translate(_FULLWIDTH_MAP)

def normalize_for_match(s: str, cfg: Dict[str, Any]) -> str:
    if s is None:
        return ""
    out = s
    norm_cfg = cfg.get("matching", {}).get("normalization", {})
    if norm_cfg.get("fullwidth_to_halfwidth", False):
        out = _to_halfwidth(out)
    if norm_cfg.get("collapse_whitespace", False):
        out = re.sub(r"\s+", " ", out).strip()
    if norm_cfg.get("lowercase_for_match", False):
        out = out.lower()
    return out

def normalize_for_dedup_key(snippet: str) -> str:
    s = snippet.strip()
    s = re.sub(r"\s+", " ", s)
    # ASCII lowercase only (safe)
    s = "".join(ch.lower() if "A" <= ch <= "Z" else ch for ch in s)
    return s


# -----------------------------
# Data extraction
# -----------------------------
@dataclass(frozen=True)
class Line:
    line_id: str
    text: str
    source_page: int

@dataclass(frozen=True)
class Block:
    block_id: str
    block_type: str
    text_raw: str
    source_page: int


def load_block_extractor_output(data: Dict[str, Any]) -> Tuple[List[Line], List[Block]]:
    raw_lines = []
    for item in data.get("raw_text_lines", []) or []:
        raw_lines.append(
            Line(
                line_id=str(item.get("line_id", "")),
                text=str(item.get("text", "")),
                source_page=int(item.get("source_page", 1) or 1),
            )
        )

    blocks = []
    for b in data.get("blocks", []) or []:
        blocks.append(
            Block(
                block_id=str(b.get("block_id", "")),
                block_type=str(b.get("block_type", "")),
                text_raw=str(b.get("text_raw", "")),
                source_page=int(b.get("source_page", 1) or 1),
            )
        )

    return raw_lines, blocks


def build_scopes(lines: List[Line], blocks: List[Block]) -> Dict[str, Any]:
    """
    Build matching scopes:
    - global_text_raw: concatenation of all block text_raw
    - page_text_raw: per-page concatenation
    - block_text_raw: per-block
    - index maps for evidence picking
    """
    # Original texts (not normalized) for evidence picking
    global_text_raw = "\n".join([b.text_raw for b in blocks if b.text_raw])

    page_text_raw: Dict[int, str] = {}
    for b in blocks:
        if b.source_page not in page_text_raw:
            page_text_raw[b.source_page] = ""
        if b.text_raw:
            page_text_raw[b.source_page] += (b.text_raw + "\n")

    block_text_raw: Dict[str, str] = {b.block_id: b.text_raw for b in blocks}

    # Also keep line texts for evidence (optional)
    line_text_by_id: Dict[str, str] = {ln.line_id: ln.text for ln in lines}

    # Block list by type
    blocks_by_type: Dict[str, List[Block]] = {}
    for b in blocks:
        blocks_by_type.setdefault(b.block_type, []).append(b)

    return {
        "global_text_raw": global_text_raw,
        "page_text_raw": page_text_raw,
        "block_text_raw": block_text_raw,
        "line_text_by_id": line_text_by_id,
        "blocks": blocks,
        "blocks_by_type": blocks_by_type,
    }


# -----------------------------
# Dictionary loading
# -----------------------------
@dataclass
class RegexPattern:
    name: str
    pattern: str
    flags: int

def load_patterns(dict_path: str) -> Dict[str, Any]:
    with open(dict_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError("Patterns YAML is not a mapping/object.")
    return cfg

def compile_regexes(cfg: Dict[str, Any]) -> Dict[str, RegexPattern]:
    out: Dict[str, RegexPattern] = {}
    regex_cfg = cfg.get("regex", {}) or {}
    for name, meta in regex_cfg.items():
        pat = meta.get("pattern")
        if not pat:
            continue
        flags_list = meta.get("flags", []) or []
        flags = 0
        for flg in flags_list:
            if flg == "IGNORECASE":
                flags |= re.IGNORECASE
            elif flg == "MULTILINE":
                flags |= re.MULTILINE
            elif flg == "DOTALL":
                flags |= re.DOTALL
        out[name] = RegexPattern(name=name, pattern=pat, flags=flags)
    return out

def get_intent_keywords(cfg: Dict[str, Any], intent_name: str) -> List[str]:
    intents = cfg.get("intents", {}) or {}
    entry = intents.get(intent_name, {}) or {}
    kws = entry.get("keywords", []) or []
    # Keep as-is; matching uses normalized text
    return [str(k) for k in kws if str(k).strip()]


# -----------------------------
# Matching utilities
# -----------------------------
def intent_match_any(text_norm: str, keywords: List[str], cfg: Dict[str, Any]) -> bool:
    # keywords may include ASCII; normalize keyword similarly
    for kw in keywords:
        kw_norm = normalize_for_match(kw, cfg)
        if kw_norm and kw_norm in text_norm:
            return True
    return False

def regex_find_any(text: str, rx: RegexPattern) -> List[re.Match]:
    return list(re.finditer(rx.pattern, text, flags=rx.flags))


def pick_evidence_snippet_for_keyword(original_text: str, keyword: str, cfg: Dict[str, Any]) -> Optional[str]:
    """
    Evidence must be exact substring from original_text.
    We find first occurrence (case-sensitive search may fail), so we use a loose strategy:
    - Try exact keyword
    - Try case-insensitive by locating in normalized text and mapping back is hard -> fallback:
      search using regex IGNORECASE on original_text for the keyword literal.
    """
    if not original_text:
        return None
    # 1) Exact
    idx = original_text.find(keyword)
    if idx != -1:
        return keyword  # shortest exact
    # 2) Case-insensitive regex literal
    try:
        m = re.search(re.escape(keyword), original_text, flags=re.IGNORECASE)
        if m:
            return original_text[m.start():m.end()]
    except re.error:
        pass
    return None

def pick_evidence_snippet_for_regex(original_text: str, rx: RegexPattern) -> Optional[str]:
    if not original_text:
        return None
    ms = regex_find_any(original_text, rx)
    if not ms:
        return None
    m = ms[0]
    return original_text[m.start():m.end()]


# -----------------------------
# Risk object construction
# -----------------------------
def make_risk(
    risk_type: str,
    block_id: str,
    raw_snippet: str,
    risk_description: str,
    risk_logic: str,
) -> Dict[str, Any]:
    return {
        "risk_type": risk_type,
        "detection_method": DETECTION_METHOD,
        "evidence": {"block_id": block_id, "raw_snippet": raw_snippet},
        "risk_description": risk_description,
        "risk_logic": risk_logic,
    }


# -----------------------------
# Rule execution
# -----------------------------
def rule_missing(
    scopes: Dict[str, Any],
    cfg: Dict[str, Any],
    regexes: Dict[str, RegexPattern],
) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []

    blocks: List[Block] = scopes["blocks"]
    blocks_by_type: Dict[str, List[Block]] = scopes["blocks_by_type"]
    global_raw = scopes["global_text_raw"]
    global_norm = normalize_for_match(global_raw, cfg)

    def has_block_type(bt: str) -> bool:
        return len(blocks_by_type.get(bt, [])) > 0

    def has_intent(intent: str) -> bool:
        kws = get_intent_keywords(cfg, intent)
        return intent_match_any(global_norm, kws, cfg)

    def has_regex(rname: str) -> bool:
        rx = regexes.get(rname)
        if not rx:
            return False
        return len(regex_find_any(global_raw, rx)) > 0

    # missing_net_content
    if not (has_intent("net_content_intent") or has_regex("net_content_value") or has_regex("net_content_multi")):
        risks.append(make_risk(
            "missing_net_content", "N/A", "N/A",
            "Net content field not observed",
            "No net content intent keywords or value patterns were detected in the extracted text"
        ))

    # missing_product_name
    title_blocks = blocks_by_type.get("title", [])
    title_ok = False
    for b in title_blocks:
        # visible chars heuristic: strip whitespace/newlines
        txt = (b.text_raw or "").strip()
        if len(txt) > 2:
            title_ok = True
            break
    if not title_ok:
        risks.append(make_risk(
            "missing_product_name", "N/A", "N/A",
            "Product name (title) not observed",
            "No valid title block was detected or title content is extremely short"
        ))

    # missing_ingredient_list
    if not (has_intent("ingredient_intent") or has_block_type("ingredient")):
        risks.append(make_risk(
            "missing_ingredient_list", "N/A", "N/A",
            "Ingredient list not observed",
            "No ingredient intent keywords or ingredient block was detected"
        ))

    # missing_manufacturer_info
    if not (has_intent("producer_intent") or has_block_type("producer")):
        risks.append(make_risk(
            "missing_manufacturer_info", "N/A", "N/A",
            "Producer/manufacturer information not observed",
            "No producer intent keywords or producer block was detected"
        ))

    # missing_date_shelf_life
    if not (has_intent("date_shelf_life_intent") or has_block_type("date_shelf_life")
            or has_regex("date_ymd_numeric") or has_regex("date_ymd_cn")):
        risks.append(make_risk(
            "missing_date_shelf_life", "N/A", "N/A",
            "Date or shelf-life information not observed",
            "No date/shelf-life intent keywords or date patterns were detected"
        ))

    # missing_standard_code
    if not (has_intent("standard_label_intent") or has_block_type("standard") or has_regex("standard_code")):
        risks.append(make_risk(
            "missing_standard_code", "N/A", "N/A",
            "Standard code not observed",
            "No standard label intent keywords, standard block, or standard code pattern was detected"
        ))

    # missing_production_license
    if not (has_intent("license_label_intent") or has_block_type("license") or has_regex("sc_code")):
        risks.append(make_risk(
            "missing_production_license", "N/A", "N/A",
            "Production license (SC) not observed",
            "No license intent keywords, license block, or SC code pattern was detected"
        ))

    return risks


def rule_format(
    scopes: Dict[str, Any],
    cfg: Dict[str, Any],
    regexes: Dict[str, RegexPattern],
) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []
    blocks: List[Block] = scopes["blocks"]

    # We choose scope = page for some rules (consistent, deterministic)
    page_text_raw: Dict[int, str] = scopes["page_text_raw"]

    # 7.2.1 format_unit_case_inconsistent (page scope)
    # mL variants
    rx_ml_upper = regexes.get("unit_ml_upper")
    rx_ml_mixed = regexes.get("unit_ml_mixed")
    rx_l_upper = regexes.get("unit_l_upper")
    rx_l_lower = regexes.get("unit_l_lower")

    def find_block_containing_snippet(snippet: str, page: int) -> Optional[str]:
        # Deterministic: scan blocks in input order, same page, find first containing snippet
        for b in blocks:
            if b.source_page == page and b.text_raw and snippet in b.text_raw:
                return b.block_id
        return None

    for page, raw in page_text_raw.items():
        # mL
        has_upper = bool(rx_ml_upper and regex_find_any(raw, rx_ml_upper))
        has_mixed = bool(rx_ml_mixed and regex_find_any(raw, rx_ml_mixed))
        if has_upper and has_mixed:
            # evidence: prefer ML (non-primary) snippet
            snippet = pick_evidence_snippet_for_regex(raw, rx_ml_upper) if rx_ml_upper else "ML"
            if snippet:
                bid = find_block_containing_snippet(snippet, page) or "N/A"
                risks.append(make_risk(
                    "format_unit_case_inconsistent",
                    bid,
                    snippet,
                    "Unit casing appears inconsistent within the same page scope",
                    "Multiple casing variants for the same unit were detected in the same scope"
                ))

        # L vs l
        has_L = bool(rx_l_upper and regex_find_any(raw, rx_l_upper))
        has_l = bool(rx_l_lower and regex_find_any(raw, rx_l_lower))
        if has_L and has_l:
            snippet = pick_evidence_snippet_for_regex(raw, rx_l_lower) if rx_l_lower else "l"
            if snippet:
                bid = find_block_containing_snippet(snippet, page) or "N/A"
                risks.append(make_risk(
                    "format_unit_case_inconsistent",
                    bid,
                    snippet,
                    "Unit casing appears inconsistent within the same page scope",
                    "Both uppercase and lowercase variants of the same unit were detected in the same scope"
                ))

    # 7.2.2 format_net_content_pattern_unusual
    kws_net = get_intent_keywords(cfg, "net_content_intent")
    rx_net_value = regexes.get("net_content_value")
    rx_net_multi = regexes.get("net_content_multi")

    for page, raw in page_text_raw.items():
        raw_norm = normalize_for_match(raw, cfg)
        has_label = intent_match_any(raw_norm, kws_net, cfg)
        has_value = bool(rx_net_value and regex_find_any(raw, rx_net_value))
        has_multi = bool(rx_net_multi and regex_find_any(raw, rx_net_multi))
        if has_label and not (has_value or has_multi):
            # evidence: pick a label keyword snippet (exact substring if found)
            snippet = None
            for kw in kws_net:
                sn = pick_evidence_snippet_for_keyword(raw, kw, cfg)
                if sn:
                    snippet = sn
                    break
            if not snippet:
                snippet = "净含量"  # fallback (still likely appears; but keep deterministic)
            bid = find_block_containing_snippet(snippet, page) or "N/A"
            risks.append(make_risk(
                "format_net_content_pattern_unusual",
                bid,
                snippet,
                "Net content label observed but value pattern not detected",
                "Net content-related label keyword was detected, but no numeric value+unit pattern was matched in the same scope"
            ))

    # 7.2.3 format_standard_code_pattern_unusual
    kws_std = get_intent_keywords(cfg, "standard_label_intent")
    rx_std = regexes.get("standard_code")
    for page, raw in page_text_raw.items():
        raw_norm = normalize_for_match(raw, cfg)
        has_label = intent_match_any(raw_norm, kws_std, cfg)
        has_code = bool(rx_std and regex_find_any(raw, rx_std))
        if has_label and not has_code:
            snippet = None
            for kw in kws_std:
                sn = pick_evidence_snippet_for_keyword(raw, kw, cfg)
                if sn:
                    snippet = sn
                    break
            snippet = snippet or "执行标准"
            bid = find_block_containing_snippet(snippet, page) or "N/A"
            risks.append(make_risk(
                "format_standard_code_pattern_unusual",
                bid,
                snippet,
                "Standard label observed but standard code pattern not detected",
                "Standard-related label keyword was detected, but no standard-code-like token was matched in the same scope"
            ))

    # 7.2.4 format_license_code_pattern_unusual
    kws_lic = get_intent_keywords(cfg, "license_label_intent")
    rx_sc = regexes.get("sc_code")
    for page, raw in page_text_raw.items():
        raw_norm = normalize_for_match(raw, cfg)
        has_label = intent_match_any(raw_norm, kws_lic, cfg)
        has_sc = bool(rx_sc and regex_find_any(raw, rx_sc))
        if has_label and not has_sc:
            snippet = None
            for kw in kws_lic:
                sn = pick_evidence_snippet_for_keyword(raw, kw, cfg)
                if sn:
                    snippet = sn
                    break
            snippet = snippet or "SC"
            bid = find_block_containing_snippet(snippet, page) or "N/A"
            risks.append(make_risk(
                "format_license_code_pattern_unusual",
                bid,
                snippet,
                "License label observed but SC code pattern not detected",
                "License-related label keyword was detected, but no SC-code-like token was matched in the same scope"
            ))

    return risks


def rule_relationship(
    scopes: Dict[str, Any],
    cfg: Dict[str, Any],
    regexes: Dict[str, RegexPattern],
) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []
    blocks: List[Block] = scopes["blocks"]
    global_raw = scopes["global_text_raw"]
    global_norm = normalize_for_match(global_raw, cfg)

    # intents
    kws_principal = get_intent_keywords(cfg, "principal_party_intent")
    kws_strong = get_intent_keywords(cfg, "entrusted_party_strong_intent")
    kws_weak = get_intent_keywords(cfg, "entrusted_party_weak_intent")
    kws_producer = get_intent_keywords(cfg, "producer_intent")

    has_principal = intent_match_any(global_norm, kws_principal, cfg)
    has_strong = intent_match_any(global_norm, kws_strong, cfg)

    # Strong trigger: incomplete_entrust_relationship
    if has_strong and not has_principal:
        # pick evidence snippet: first strong keyword occurrence in original (block-level)
        snippet, bid = pick_first_keyword_evidence_in_blocks(blocks, kws_strong, cfg)
        snippet = snippet or kws_strong[0] if kws_strong else "受委托生产"
        bid = bid or "N/A"
        risks.append(make_risk(
            "incomplete_entrust_relationship",
            bid,
            snippet,
            "Entrust-production context observed but principal party not observed",
            "Strong entrust-production keywords were detected, but no principal-party keywords were detected in the extracted text"
        ))
        return risks  # if strong triggered, do not emit ambiguous in alpha (avoid double)

    # Weak trigger: entrusted_context_ambiguous (safer)
    if (not has_strong) and (not has_principal):
        thresholds = cfg.get("thresholds", {}) or {}
        weak_max = int(thresholds.get("entrust_weak_trigger_max_count", 1) or 1)
        prod_min = int(thresholds.get("producer_context_keyword_min_hits_for_weak_entrust", 1) or 1)

        # Count weak occurrences globally (match text norm)
        weak_count = 0
        for kw in kws_weak:
            kw_norm = normalize_for_match(kw, cfg)
            if kw_norm:
                weak_count += global_norm.count(kw_norm)

        if weak_count > 0 and weak_count <= weak_max:
            # Require producer context in same block as weak keyword
            for b in blocks:
                b_norm = normalize_for_match(b.text_raw, cfg)
                # block contains any weak kw?
                contains_weak = False
                for kw in kws_weak:
                    if normalize_for_match(kw, cfg) in b_norm:
                        contains_weak = True
                        break
                if not contains_weak:
                    continue
                # producer hits count
                hits = 0
                for kwp in kws_producer:
                    kwp_norm = normalize_for_match(kwp, cfg)
                    if kwp_norm and kwp_norm in b_norm:
                        hits += 1
                if hits >= prod_min:
                    # evidence: weak keyword snippet from original
                    snippet = None
                    for kw in kws_weak:
                        sn = pick_evidence_snippet_for_keyword(b.text_raw, kw, cfg)
                        if sn:
                            snippet = sn
                            break
                    snippet = snippet or kws_weak[0]
                    risks.append(make_risk(
                        "entrusted_context_ambiguous",
                        b.block_id,
                        snippet,
                        "Ambiguous entrust-production wording observed in producer context",
                        "Weak entrust keywords were detected in a producer-context block, while no principal-party keywords were detected; this is treated as an ambiguous relationship signal"
                    ))
                    break

    return risks


def pick_first_keyword_evidence_in_blocks(blocks: List[Block], keywords: List[str], cfg: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    for b in blocks:
        if not b.text_raw:
            continue
        for kw in keywords:
            sn = pick_evidence_snippet_for_keyword(b.text_raw, kw, cfg)
            if sn:
                return sn, b.block_id
    return None, None


# -----------------------------
# Deduplication
# -----------------------------
def deduplicate(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for r in risks:
        rt = r.get("risk_type", "")
        ev = r.get("evidence", {}) or {}
        sn = ev.get("raw_snippet", "")
        if sn == "N/A":
            key = rt
        else:
            key = rt + "||" + normalize_for_dedup_key(str(sn))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


# -----------------------------
# Engine
# -----------------------------
def run_engine(block_extractor_json: Dict[str, Any], patterns_cfg: Dict[str, Any]) -> Dict[str, Any]:
    lines, blocks = load_block_extractor_output(block_extractor_json)
    scopes = build_scopes(lines, blocks)
    regexes = compile_regexes(patterns_cfg)

    risks = []
    risks.extend(rule_missing(scopes, patterns_cfg, regexes))
    risks.extend(rule_format(scopes, patterns_cfg, regexes))
    risks.extend(rule_relationship(scopes, patterns_cfg, regexes))

    risks = deduplicate(risks)

    return {
        "system_version": SYSTEM_VERSION,
        "module_name": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "spec_version": SPEC_VERSION,
        "dict_version": str(patterns_cfg.get("dict_version", "v1.0.0-alpha")),
        "schema_version": SCHEMA_VERSION,
        "detection_method": DETECTION_METHOD,
        "risk_list": risks,
    }


# -----------------------------
# CLI
# -----------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dict", required=True, help="Path to patterns yaml")
    ap.add_argument("--input", required=True, help="Path to BlockExtractor output json")
    args = ap.parse_args()

    patterns_cfg = load_patterns(args.dict)
    with open(args.input, "r", encoding="utf-8") as f:
        be_json = json.load(f)

    out = run_engine(be_json, patterns_cfg)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
