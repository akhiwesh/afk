from backend.app.knowledge_engine.kb_runtime import priority_adjunct_config


def test_priority_adjunct_loads_from_kb():
    cfg = priority_adjunct_config()
    assert cfg["pricing_discount_threshold_pct"] == 5.0
    assert cfg["pricing_discount_slope"] == 2.0
    assert cfg["retention_repeat_gap_pp"] == 20.0
    assert cfg.get("kb_object") == "AFK-PRI-0001"