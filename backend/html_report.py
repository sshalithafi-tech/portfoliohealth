"""
HTML report builder.

Reads the static template at /app/portfoliohealth-report.html and injects a
backend-computed REPORT_DATA object so the standalone report can be served
per-assessment.

Single public function:
    build_html_report(assessment: dict) -> str
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "portfoliohealth-report.html"

LEVEL_NAME_TO_INDEX = {
    "ad hoc": 1,
    "developing": 2,
    "aware": 2,
    "defined": 3,
    "managed": 4,
    "predictive": 5,
    "optimising": 5,
    "optimizing": 5,
}


def _level_index_from_name(name: Any) -> int:
    if not isinstance(name, str):
        return 1
    return LEVEL_NAME_TO_INDEX.get(name.strip().lower(), 1)


def _level_name_from_score(score: float) -> str:
    if score < 2:
        return "AD HOC"
    if score < 3:
        return "DEVELOPING"
    if score < 4:
        return "DEFINED"
    if score < 4.5:
        return "MANAGED"
    return "PREDICTIVE"


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _split_actions(text: Any) -> List[str]:
    """Roadmap actions are stored as free prose; split into bullets."""
    if not text:
        return []
    if isinstance(text, list):
        return [str(t).strip() for t in text if str(t).strip()]
    s = str(text).strip()
    parts = [p.strip(" -—•·\t") for p in re.split(r"(?:\r?\n+|(?<=[.!?])\s+(?=[A-Z]))", s) if p.strip()]
    return [p for p in parts if len(p) > 8][:4]


def _evidence_bullets(report: Dict[str, Any], pillar: str, fallback: str) -> List[str]:
    """Try multiple report fields to surface 3-4 specific evidence bullets per pillar."""
    bullets: List[str] = []
    summaries = report.get("dimension_summaries") or {}
    interp = report.get("pillar_interpretations") or {}
    findings = report.get("key_findings") or []
    gaps = report.get("critical_gaps") or []

    summary_text = summaries.get(pillar)
    if isinstance(summary_text, str) and summary_text.strip():
        bullets.append(summary_text.strip())

    interp_text = interp.get(pillar)
    if isinstance(interp_text, str) and interp_text.strip():
        bullets.append(interp_text.strip())

    pillar_lower = pillar.lower()
    for src in (findings, gaps):
        if isinstance(src, list):
            for item in src:
                s = str(item).strip()
                if s and pillar_lower in s.lower() and s not in bullets:
                    bullets.append(s)
                if len(bullets) >= 4:
                    break

    if not bullets:
        bullets.append(fallback)
    return bullets[:4]


def _confidence_for_pillar(report: Dict[str, Any], pillar: str) -> Dict[str, int]:
    """Map the assessment_reliability tone → strong/inferred/assumed split."""
    rel = (report.get("assessment_reliability") or {})
    confidence = (rel.get("confidence") or "").strip().lower()
    base = {
        "high":   {"strong": 80, "inferred": 15, "assumed": 5},
        "medium": {"strong": 60, "inferred": 30, "assumed": 10},
        "low":    {"strong": 40, "inferred": 40, "assumed": 20},
    }.get(confidence, {"strong": 60, "inferred": 30, "assumed": 10})
    return dict(base)


def _bottleneck_pillar(report: Dict[str, Any]) -> Optional[str]:
    name = report.get("bottleneck_pillar")
    if isinstance(name, str) and name.strip():
        return name.strip().upper()
    return None


def _is_bottleneck_capped(report: Dict[str, Any], scores: Dict[str, float], bottleneck: Optional[str]) -> bool:
    if not bottleneck:
        return False
    overall = scores.get("overall", 0.0)
    bn_score = scores.get(bottleneck.lower(), 0.0)
    return (overall - bn_score) >= 1.0


def _phase_actions(roadmap: Dict[str, Any], phase_key: str, default: List[str]) -> List[str]:
    phase = (roadmap or {}).get(phase_key) or {}
    actions = phase.get("actions")
    parts = _split_actions(actions)
    return parts or default


def _projected_phase1(scores: Dict[str, float], bottleneck: Optional[str]) -> float:
    if not bottleneck:
        return min(5.0, scores.get("overall", 0.0) + 0.5)
    fixed = dict(scores)
    fixed[bottleneck.lower()] = max(3.0, fixed.get(bottleneck.lower(), 0.0))
    pillars = ["people", "process", "data", "technology"]
    return round(sum(fixed.get(p, 0.0) for p in pillars) / 4, 2)


def _build_report_data(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """Map the stored assessment + report → the JS REPORT_DATA contract."""
    report = (assessment.get("report") or {})
    raw_scores = (report.get("scores") or assessment.get("scores") or {})

    scores = {
        "people":     _to_float(raw_scores.get("people")),
        "process":    _to_float(raw_scores.get("process")),
        "data":       _to_float(raw_scores.get("data")),
        "technology": _to_float(raw_scores.get("technology")),
        "overall":    _to_float(raw_scores.get("overall")),
    }

    level_names_raw = (report.get("level_names") or {})

    def _clean_level(name: Any) -> str:
        if not isinstance(name, str):
            return ""
        s = re.sub(r"^LEVEL\s+[\d\-–]+\s*:?\s*", "", name.strip(), flags=re.IGNORECASE)
        return s.upper().strip()

    levels = {}
    for k in ("people", "process", "data", "technology", "overall"):
        nm = _clean_level(level_names_raw.get(k))
        if nm:
            levels[k] = nm
        else:
            levels[k] = _level_name_from_score(scores[k])

    bottleneck = _bottleneck_pillar(report)
    bottleneck_capped = _is_bottleneck_capped(report, scores, bottleneck)

    completed_at = assessment.get("completed_at") or assessment.get("created_at")
    if hasattr(completed_at, "strftime"):
        date_str = completed_at.strftime("%B %Y")
    elif isinstance(completed_at, str):
        date_str = completed_at[:10]
    else:
        date_str = ""

    business_model_raw = (assessment.get("business_model") or report.get("business_model") or "").strip()
    bm_map = {
        "ETO": "ETO", "CTO": "CTO", "CETO": "CETO",
        "STANDARD": "STD", "STANDARD/BULK": "STD", "BULK": "STD", "STD": "STD",
        "MTO": "ETO",  # closest analogue
    }
    business_model = bm_map.get(business_model_raw.upper()) if business_model_raw else None

    pillars_kpi = []
    for letter, key in (("P", "people"), ("P", "process"), ("D", "data"), ("T", "technology")):
        sc = scores[key]
        pillars_kpi.append({
            "key": key,
            "letter": letter,
            "name": key.capitalize(),
            "score": sc,
            "level": _level_index_from_name(levels[key]) or _level_index_from_name(_level_name_from_score(sc)),
        })

    fallbacks = {
        "people":     "Roles, accountability, and decision-making capability across the portfolio function.",
        "process":    "Formal review cycles, change control, and decision traceability across the product lifecycle.",
        "data":       "Product master data, profitability data quality, and the ability to assemble decision-grade information.",
        "technology": "Tools and integrations actually used inside the portfolio decision room.",
    }
    evidence = {p: _evidence_bullets(report, p, fallbacks[p]) for p in fallbacks}

    confidence = {p: _confidence_for_pillar(report, p) for p in fallbacks}

    roadmap_obj = report.get("roadmap") or {}
    score_now = scores["overall"]
    score_phase1 = _projected_phase1(scores, bottleneck)
    score_phase3 = min(5.0, max(score_phase1 + 0.8, 4.0))

    p1_default = ["Resolve the highest-leverage bottleneck constraint with a named accountable owner."]
    p2_default = ["Establish recurring portfolio review cadence with documented retirement and reallocation criteria."]
    p3_default = ["Reach Managed/Predictive maturity: integrated dashboards, predictive analytics and consolidated governance."]

    roadmap = {
        "score_now": round(score_now, 2),
        "score_phase1": round(score_phase1, 2),
        "score_phase3": round(score_phase3, 2),
        "phase1_actions": _phase_actions(roadmap_obj, "immediate", p1_default),
        "phase2_actions": _phase_actions(roadmap_obj, "short_term", p2_default),
        "phase3_actions": _phase_actions(roadmap_obj, "strategic",   p3_default),
    }

    data = {
        "company": assessment.get("company_name") or "Organisation",
        "industry": assessment.get("company_industry") or "—",
        "business_model": business_model,
        "size": assessment.get("company_size") or "—",
        "role": assessment.get("respondent_role") or assessment.get("respondent_name") or "—",
        "date": date_str or "",
        "scores": scores,
        "levels": levels,
        "bottleneck": bottleneck,
        "bottleneck_capped": bool(bottleneck_capped),
        "evidence": evidence,
        "confidence": confidence,
        "roadmap": roadmap,
        "kpi": {
            "overall": {
                "score": scores["overall"],
                "level_name": levels["overall"],
                "level_index": _level_index_from_name(levels["overall"]) or _level_index_from_name(_level_name_from_score(scores["overall"])),
            },
            "pillars": pillars_kpi,
        },
    }
    return data


_TEMPLATE_CACHE: Optional[str] = None


def _load_template() -> str:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        _TEMPLATE_CACHE = TEMPLATE_PATH.read_text(encoding="utf-8")
    return _TEMPLATE_CACHE


# Replaces the entire window.REPORT_DATA = { ... }; block (non-greedy across newlines)
_DATA_BLOCK_RE = re.compile(
    r"window\.REPORT_DATA\s*=\s*\{.*?\};",
    re.DOTALL,
)


def build_html_report(assessment: Dict[str, Any]) -> str:
    """Render the standalone HTML report with REPORT_DATA injected."""
    template = _load_template()
    data = _build_report_data(assessment)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    replacement = f"window.REPORT_DATA = {payload};"
    rendered, n = _DATA_BLOCK_RE.subn(replacement, template, count=1)
    if n == 0:
        # Fallback: inject before </head> so charts still get data
        rendered = template.replace(
            "</head>",
            f"<script>{replacement}</script>\n</head>",
            1,
        )

    # Replace the static <title> with company + date for browser tab and exports
    company = data.get("company") or "Assessment"
    date = data.get("date") or ""
    new_title = f"<title>PPDT Report — {company}{(' — ' + date) if date else ''}</title>"
    rendered = re.sub(r"<title>[^<]*</title>", new_title, rendered, count=1)

    return rendered
