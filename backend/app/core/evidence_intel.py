"""
Evidence Intelligence — M3.2.

Turns normalized EvidenceRecords into: computed business metrics,
evidence-weighted confidence, contradictions (founder belief vs business
reality), revenue drivers, data quality, and missing-evidence guidance.

Contract: pure functions, deterministic, every output carries its basis.
Founder answers are HYPOTHESES; evidence confirms or contradicts them.
Contradictions compare — they never accuse, and (in M3.2) they inform the
founder rather than silently rewriting scores. Causal integration is M3.3.
"""
from collections import Counter, defaultdict
from typing import Optional

from backend.app.core.engine import DIMENSIONS, QUESTIONS, _num


# ---------------------------------------------------------------------------
# 1. Metrics computed from evidence records
# ---------------------------------------------------------------------------

def compute_metrics(records_by_kind: dict[str, list[dict]]) -> dict:
    """records_by_kind: {"invoices": [normalized rec...], "leads": [...], ...}
    Every metric includes its basis (how it was computed, from how many rows)."""
    m = {}

    inv = records_by_kind.get("invoices", []) + records_by_kind.get("transactions", [])
    inv_amt = [r for r in inv if isinstance(r.get("amount"), (int, float))]
    if inv_amt:
        total = sum(r["amount"] for r in inv_amt)
        m["avg_order_value"] = {
            "value": round(total / len(inv_amt)),
            "basis": f"Mean of {len(inv_amt)} invoice/transaction amounts.",
        }
        # Discount rate where both amount and discount are present
        disc = [(r["discount"], r["amount"]) for r in inv_amt
                if isinstance(r.get("discount"), (int, float)) and r["amount"]]
        if disc:
            pct = 100 * sum(d for d, a in disc) / sum(a + d for d, a in disc)
            m["avg_discount_pct"] = {
                "value": round(pct, 1),
                "basis": f"Total discount ÷ gross value across {len(disc)} invoices with discount data.",
            }
        # Monthly revenue where dates exist
        by_month = defaultdict(float)
        for r in inv_amt:
            d = r.get("date")
            if d:
                by_month[d[:7]] += r["amount"]
        if by_month:
            m["avg_monthly_revenue"] = {
                "value": round(sum(by_month.values()) / len(by_month)),
                "basis": f"Revenue summed per month across {len(by_month)} month(s) of invoice dates.",
            }
        # Repeat customer rate from invoice customer names
        custs = Counter(r["customer"].strip().lower() for r in inv if r.get("customer"))
        if len(custs) >= 3:
            repeat = sum(1 for c in custs.values() if c > 1)
            m["repeat_customer_rate"] = {
                "value": round(100 * repeat / len(custs), 1),
                "basis": f"{repeat} of {len(custs)} distinct customers appear on more than one invoice.",
            }

        # --- Metrics that a rich, multi-month dataset unlocks ---
        # Customer revenue concentration (share from top ~20% of accounts).
        cust_rev = {}
        for r in inv_amt:
            c = (r.get("customer") or "").strip().lower()
            if c:
                cust_rev[c] = cust_rev.get(c, 0) + r["amount"]
        if len(cust_rev) >= 5:
            ranked = sorted(cust_rev.values(), reverse=True)
            top_n = max(1, round(len(ranked) * 0.2))
            share = 100 * sum(ranked[:top_n]) / sum(ranked)
            m["revenue_concentration_pct"] = {
                "value": round(share, 1),
                "basis": f"Top {top_n} of {len(cust_rev)} customers ({round(100*top_n/len(cust_rev))}%) account for this share of revenue.",
            }

        # Revenue trend: compare first vs last third of the months present.
        if len(by_month) >= 4:
            months = sorted(by_month)
            third = max(1, len(months) // 3)
            early = sum(by_month[k] for k in months[:third]) / third
            late = sum(by_month[k] for k in months[-third:]) / third
            if early > 0:
                chg = 100 * (late - early) / early
                m["revenue_trend_pct"] = {
                    "value": round(chg, 1),
                    "basis": f"Average monthly revenue in the last {third} month(s) vs the first {third}, across {len(months)} months of data.",
                }

        # Seasonality: peak vs trough month.
        if len(by_month) >= 6:
            vals = sorted(by_month.items(), key=lambda kv: kv[1])
            low_k, low_v = vals[0]
            high_k, high_v = vals[-1]
            if low_v > 0:
                m["seasonality_swing_pct"] = {
                    "value": round(100 * (high_v - low_v) / low_v, 1),
                    "basis": f"Best month ({high_k}) vs weakest ({low_k}) across {len(by_month)} months of invoices.",
                }

        # Dormant accounts: customers with no invoice in the most recent 90 days
        # of the dataset's own timeline (not wall-clock — respects the file).
        dated = [r for r in inv_amt if r.get("date")]
        if len(cust_rev) >= 5 and len(dated) >= 10:
            latest = max(r["date"] for r in dated)
            from datetime import date as _d
            try:
                ly, lm, ld = (int(x) for x in latest.split("-"))
                cutoff_ord = _d(ly, lm, ld).toordinal() - 90
                last_seen = {}
                for r in dated:
                    c = (r.get("customer") or "").strip().lower()
                    if c:
                        last_seen[c] = max(last_seen.get(c, ""), r["date"])
                dormant = 0
                for c, dt in last_seen.items():
                    y, mo, dd = (int(x) for x in dt.split("-"))
                    if _d(y, mo, dd).toordinal() < cutoff_ord:
                        dormant += 1
                if last_seen:
                    m["dormant_customer_pct"] = {
                        "value": round(100 * dormant / len(last_seen), 1),
                        "basis": f"{dormant} of {len(last_seen)} customers have no invoice in the last 90 days of your data (latest: {latest}).",
                    }
            except (ValueError, AttributeError):
                pass


    leads = records_by_kind.get("leads", [])
    if leads:
        m["lead_count"] = {"value": len(leads), "basis": f"{len(leads)} lead records uploaded."}
        srcs = Counter(r["source"].strip() for r in leads if r.get("source"))
        if srcs:
            top, cnt = srcs.most_common(1)[0]
            m["top_lead_source"] = {
                "value": top,
                "basis": f"{cnt} of {sum(srcs.values())} leads with a source came from {top}.",
            }
        statuses = [r["status"].strip().lower() for r in leads if r.get("status")]
        if statuses:
            won_words = ("won", "customer", "closed won", "converted", "paid", "qualified")
            lost_words = ("lost", "closed lost", "dead", "disqualified")
            won = sum(1 for s in statuses if any(w in s for w in won_words))
            decided = won + sum(1 for s in statuses if any(w in s for w in lost_words))
            if decided >= 3:
                m["lead_conversion_pct"] = {
                    "value": round(100 * won / decided, 1),
                    "basis": f"{won} of {decided} decided leads (won/lost statuses) converted. Open leads excluded.",
                }
    return m


# ---------------------------------------------------------------------------
# 2. Contradiction Engine — belief vs evidence, with cross-examination
# ---------------------------------------------------------------------------

def detect_contradictions(answers: dict, metrics: dict) -> list[dict]:
    out = []

    def add(belief_q, belief_val, metric_key, explanation, question, severity="notable"):
        mv = metrics[metric_key]
        out.append({
            "belief": {"question": belief_q, "answer": belief_val},
            "evidence": {"metric": metric_key, "value": mv["value"], "basis": mv["basis"]},
            "severity": severity,
            "explanation": explanation,
            "follow_up_question": question,
        })

    # Pricing belief vs actual discounting
    pc = answers.get("pricing_confidence")
    disc_ans = answers.get("discounting")
    if "avg_discount_pct" in metrics:
        d = metrics["avg_discount_pct"]["value"]
        if d >= 15 and pc in ("About right", "Premium and defensible"):
            add("Honest read on your pricing", pc, "avg_discount_pct",
                f"You assessed pricing as \"{pc}\", but invoices show an average discount of {d}%. "
                "A list price that routinely gives back {:.0f}% is not the real price.".format(d),
                f"Invoices show ~{d}% average discounting despite pricing being rated \"{pc}\". "
                "Is this driven by enterprise negotiation, promotions, a few large accounts, or outdated list prices?",
                severity="significant" if d >= 25 else "notable")
        if d >= 15 and disc_ans == "Rarely":
            add("How often do you discount to close?", disc_ans, "avg_discount_pct",
                f"You answered that discounting is rare, but the invoice data shows {d}% average discount.",
                "The invoices disagree with the memory here — could a specific customer segment or "
                "salesperson account for most of the discounting?")

    # Retention belief vs invoice repeat rate
    stated_rr = _num(answers, "repeat_rate")
    if stated_rr is not None and "repeat_customer_rate" in metrics:
        actual = metrics["repeat_customer_rate"]["value"]
        if abs(stated_rr - actual) >= 20:
            direction = "lower" if actual < stated_rr else "higher"
            add("% of customers who buy again / renew", f"{int(stated_rr)}%", "repeat_customer_rate",
                f"You estimated {int(stated_rr)}% repeat rate; invoices show {actual}% of customers "
                f"actually purchased more than once — significantly {direction} than perceived.",
                f"The gap between perceived ({int(stated_rr)}%) and measured ({actual}%) repeat rate is large. "
                "Could one-time project customers be inflating the perception, or is the invoice period too short?",
                severity="significant")

    # Stated revenue vs invoice-computed revenue
    stated_rev = _num(answers, "monthly_revenue")
    if stated_rev and "avg_monthly_revenue" in metrics:
        actual = metrics["avg_monthly_revenue"]["value"]
        if stated_rev > 0 and abs(actual - stated_rev) / stated_rev >= 0.3:
            direction = "below" if actual < stated_rev else "above"
            add("Average monthly revenue (₹)", f"₹{int(stated_rev):,}", "avg_monthly_revenue",
                f"Stated revenue is ₹{int(stated_rev):,}/mo; invoices average ₹{actual:,}/mo — "
                f"{abs(actual - stated_rev) / stated_rev:.0%} {direction} the stated figure.",
                "Does the uploaded invoice data cover all revenue streams, or is part of the business "
                "(cash, another entity, other products) not in this export?")

    # Stated deal value vs computed AOV
    stated_adv = _num(answers, "avg_deal_value")
    if stated_adv and "avg_order_value" in metrics:
        actual = metrics["avg_order_value"]["value"]
        if stated_adv > 0 and abs(actual - stated_adv) / stated_adv >= 0.4:
            add("Average deal / order value (₹)", f"₹{int(stated_adv):,}", "avg_order_value",
                f"Stated average deal value is ₹{int(stated_adv):,}; invoices compute ₹{actual:,}.",
                "Is the mental 'average deal' anchored on the memorable large deals rather than the median invoice?")

    return out


# ---------------------------------------------------------------------------
# 3. Evidence-weighted confidence
# ---------------------------------------------------------------------------

# Which evidence kinds strengthen which dimensions
_DIM_EVIDENCE = {
    "demand":            ["leads"],
    "qualification":     ["leads"],
    "conversion":        ["leads", "invoices"],
    "pricing":           ["invoices", "transactions"],
    "retention":         ["invoices", "transactions"],
    "founder_dependency": [],   # only observable via questionnaire today
}

QUESTIONNAIRE_CEILING = 0.4  # a self-reported answer is a hypothesis, capped at 40%


def evidence_confidence(answers: dict, kinds_present: dict[str, int],
                        quality_by_kind: dict[str, float]) -> dict:
    """kinds_present: {"invoices": row_count, ...} for confirmed datasets.
    quality_by_kind: {"invoices": 0.96, ...} data-quality multipliers.
    Per dimension: questionnaire coverage contributes up to 40%; matching
    evidence kinds contribute the remaining 60%, scaled by data quality."""
    per_dim, breakdown_sources = {}, {}

    q_total = len(QUESTIONS)
    q_answered = sum(1 for q in QUESTIONS if answers.get(q["id"]) not in (None, ""))
    breakdown_sources["Questionnaire"] = {
        "coverage_pct": round(100 * q_answered / q_total),
        "weight": f"caps at {int(QUESTIONNAIRE_CEILING * 100)}% — self-reported answers are hypotheses",
    }

    for key, meta in DIMENSIONS.items():
        fields = meta["fields"]
        q_cov = sum(1 for f in fields if answers.get(f) not in (None, "")) / len(fields) if fields else 0
        conf = q_cov * QUESTIONNAIRE_CEILING

        useful = _DIM_EVIDENCE.get(key, [])
        if useful:
            have = [k for k in useful if kinds_present.get(k)]
            if have:
                avg_quality = sum(quality_by_kind.get(k, 0.8) for k in have) / len(have)
                conf += (len(have) / len(useful)) * (1 - QUESTIONNAIRE_CEILING) * avg_quality
        else:
            # No evidence kind can verify this dimension yet — questionnaire
            # coverage counts fully, honestly noted.
            conf = q_cov * 0.7

        per_dim[key] = round(min(conf, 1.0), 2)

    for kind, rows in kinds_present.items():
        q = quality_by_kind.get(kind, None)
        breakdown_sources[kind.capitalize()] = {
            "coverage_pct": 100,
            "rows": rows,
            "quality_pct": round(q * 100) if q is not None else None,
        }
    for kind in ("invoices", "leads"):
        if kind not in kinds_present:
            breakdown_sources[kind.capitalize()] = {"coverage_pct": 0, "missing": True}

    overall = round(sum(per_dim.values()) / len(per_dim), 2)
    return {
        "overall": overall,
        "per_dimension": per_dim,
        "sources": breakdown_sources,
        "method": ("Self-reported audit answers cap at "
                   f"{int(QUESTIONNAIRE_CEILING * 100)}% confidence per dimension; uploaded evidence "
                   "supplies the remainder, scaled by measured data quality. Confidence rises as "
                   "evidence arrives — it is computed, never asserted."),
    }


def missing_evidence(kinds_present: dict[str, int]) -> list[dict]:
    """What evidence would most improve each dimension, concretely."""
    suggestions = {
        "demand": ("leads", "A lead/enquiry export (CRM, WhatsApp list, or spreadsheet) would verify lead volume and sources."),
        "qualification": ("leads", "Lead statuses (qualified/lost) would measure how much time goes to wrong-fit leads."),
        "conversion": ("leads", "Lead outcomes plus invoices would compute the real close rate instead of the remembered one."),
        "pricing": ("invoices", "Invoices with discount columns would measure real pricing behavior."),
        "retention": ("invoices", "12+ months of invoices would measure the true repeat-purchase rate."),
        "founder_dependency": (None, "No uploadable evidence verifies this yet — call/meeting data arrives in a later milestone."),
    }
    out = []
    for key, meta in DIMENSIONS.items():
        kind, tip = suggestions[key]
        covered = bool(kind and kinds_present.get(kind))
        out.append({
            "dimension": meta["label"],
            "evidence_kind": kind,
            "covered": covered,
            "suggestion": None if covered else tip,
        })
    return out


# ---------------------------------------------------------------------------
# 4. Data quality
# ---------------------------------------------------------------------------

def data_quality(records: list[dict], kind: str) -> dict:
    """Score 0-1 with named reasons. Poor quality lowers confidence upstream."""
    if not records:
        return {"score": 0.0, "reasons": ["No records."]}
    n = len(records)
    reasons, penalty = [], 0.0

    if kind in ("invoices", "transactions"):
        blank_amt = sum(1 for r in records if r.get("amount") in (None, ""))
        blank_date = sum(1 for r in records if not r.get("date"))
        if blank_amt / n > 0.05:
            penalty += min(0.3, blank_amt / n)
            reasons.append(f"{blank_amt} of {n} rows missing a valid amount.")
        if blank_date / n > 0.05:
            penalty += min(0.2, blank_date / n)
            reasons.append(f"{blank_date} of {n} rows missing a parseable date.")
        custs = [r["customer"].strip().lower() for r in records if r.get("customer")]
        if custs:
            near_dupes = len(custs) - len({c.replace(" ", "").replace(".", "") for c in custs})
            if near_dupes > 0 and len(set(custs)) > 2:
                penalty += min(0.15, near_dupes / n)
                reasons.append(f"~{near_dupes} customer names look like duplicates with inconsistent spelling.")
    if kind == "leads":
        no_status = sum(1 for r in records if not r.get("status"))
        no_source = sum(1 for r in records if not r.get("source"))
        if no_status / n > 0.2:
            penalty += min(0.25, no_status / n)
            reasons.append(f"{no_status} of {n} leads have no status/stage.")
        if no_source / n > 0.2:
            penalty += min(0.2, no_source / n)
            reasons.append(f"{no_source} of {n} leads have no source.")

    score = round(max(0.2, 1.0 - penalty), 2)
    if not reasons:
        reasons.append("No significant quality issues detected.")
    return {"score": score, "reasons": reasons}


# ---------------------------------------------------------------------------
# 5. Revenue drivers — what's WORKING, from evidence
# ---------------------------------------------------------------------------

def detect_drivers(metrics: dict) -> list[dict]:
    out = []
    if "top_lead_source" in metrics:
        out.append({"label": "Highest-volume channel",
                    "value": metrics["top_lead_source"]["value"],
                    "basis": metrics["top_lead_source"]["basis"]})
    if "avg_order_value" in metrics:
        out.append({"label": "Average order value",
                    "value": f"₹{metrics['avg_order_value']['value']:,}",
                    "basis": metrics["avg_order_value"]["basis"]})
    rr = metrics.get("repeat_customer_rate")
    if rr and rr["value"] >= 50:
        out.append({"label": "Repeat purchase strength",
                    "value": f"{rr['value']}% of customers buy again",
                    "basis": rr["basis"]})
    conv = metrics.get("lead_conversion_pct")
    if conv and conv["value"] >= 30:
        out.append({"label": "Strong close rate on decided leads",
                    "value": f"{conv['value']}%",
                    "basis": conv["basis"]})
    return out
