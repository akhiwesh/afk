"""Phase B step 1 — attach AFK-DET-* rule IDs to engine findings for scientific versioning."""

RULE_PACK_ID = "kb-det-v1"

# (dimension_key, penalty, primary_evidence_field_id) -> detection_rule_id
_EXACT_RULE_MAP: dict[tuple[str, int, str], str] = {
    # demand
    ("demand", 25, "lead_sources_count"): "AFK-DET-0002",
    ("demand", 20, "marketing_active"): "AFK-DET-0003",
    ("demand", 12, "marketing_active"): "AFK-DET-0004",
    # qualification
    ("qualification", 30, "qualification_process"): "AFK-DET-0005",
    ("qualification", 25, "pct_leads_worth_it"): "AFK-DET-0006",
    # conversion
    ("conversion", 22, "conversion_close_rate"): "AFK-DET-0007",
    ("conversion", 20, "conversion_followups"): "AFK-DET-0008",
    ("conversion", 18, "conversion_owner"): "AFK-DET-0009",
    ("conversion", 15, "conversion_process"): "AFK-DET-0010",
    ("conversion", 10, "conversion_cycle_days"): "AFK-DET-0023",
    # pricing
    ("pricing", 25, "pricing_confidence"): "AFK-DET-0011",
    ("pricing", 20, "pricing_confidence"): "AFK-DET-0012",
    ("pricing", 15, "last_price_change"): "AFK-DET-0013",
    ("pricing", 20, "discounting"): "AFK-DET-0014",
    # retention
    ("retention", 30, "repeat_rate"): "AFK-DET-0015",
    ("retention", 20, "churn_reason_known"): "AFK-DET-0016",
    ("retention", 15, "retention_process"): "AFK-DET-0017",
    # founder_dependency
    ("founder_dependency", 25, "founder_in_every_sale"): "AFK-DET-0018",
    ("founder_dependency", 15, "documented_sales_process"): "AFK-DET-0019",
}

_BAND_RULE_MAP: dict[tuple[str, str], str] = {
    ("demand", "leads_per_month"): "AFK-DET-0001",
    ("qualification", "pct_leads_worth_it"): "AFK-DET-0006",
    ("conversion", "conversion_close_rate"): "AFK-DET-0007",
    ("retention", "repeat_rate"): "AFK-DET-0015",
}


def annotate_findings(findings: list[dict], dim_key: str) -> list[dict]:
    """Mutates findings in place with rule_id when KB mapping is unambiguous."""
    for f in findings:
        evidence = f.get("evidence") or []
        primary = evidence[0]["id"] if evidence else ""
        pen = f.get("penalty", 0)
        exact = _EXACT_RULE_MAP.get((dim_key, pen, primary))
        if exact:
            f["rule_id"] = exact
            f["rule_pack"] = RULE_PACK_ID
            continue
        band = _BAND_RULE_MAP.get((dim_key, primary))
        if band:
            f["rule_id"] = band
            f["rule_pack"] = RULE_PACK_ID
    return findings


def annotate_diagnosis_dimensions(dimensions: list[dict]) -> list[dict]:
    for d in dimensions:
        annotate_findings(d.get("findings") or [], d.get("key", ""))
    return dimensions


def mapped_rule_ids() -> frozenset[str]:
    """All AFK-DET-* IDs the kb-det-v1 pack can emit."""
    return frozenset(_EXACT_RULE_MAP.values()) | frozenset(_BAND_RULE_MAP.values())


def exact_map_penalties() -> dict[str, int]:
    """rule_id -> penalty for unambiguous exact-map entries (parity vs KB)."""
    out: dict[str, int] = {}
    for (_dim, penalty, _field), rid in _EXACT_RULE_MAP.items():
        out[rid] = penalty
    return out