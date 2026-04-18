"""
Scoring Engine — takes parsed brief answers and produces brand scores,
RAG status, and industry benchmarks.

Uses rule-based heuristics to score each dimension based on the quality
and specificity of the client's answers.
"""

# ---- Keyword signals for scoring quality of answers ----

# Signals that indicate vagueness / low quality
VAGUE_SIGNALS = [
    "not sure", "don't know", "haven't thought", "maybe", "i guess",
    "nothing", "none", "n/a", "na", "no", "nope", "not really",
    "haven't", "don't have", "no idea", "unsure", "tbd",
    "working on it", "need to", "haven't done", "not yet",
]

# Signals that indicate specificity / high quality
STRONG_SIGNALS = [
    "documented", "brand guidelines", "style guide", "tone of voice document",
    "brand book", "consistency", "defined", "clear", "specific",
    "target audience", "persona", "ideal client", "niche",
    "unique selling", "differentiat", "speciali",
    "google business", "claimed", "verified", "optimised", "optimized",
    "press", "featured in", "mentioned in", "published",
    "directory", "listed on", "appear on", "appear in",
    "ai", "chatgpt", "discoverable",
]

# Industry benchmark ranges: {sector_keyword: {dimension: (low, high)}}
INDUSTRY_BENCHMARKS = {
    "professional services": {"clarity": (6.5, 7.5), "consistency": (6.0, 7.0), "visibility": (5.5, 6.5)},
    "law": {"clarity": (6.5, 7.5), "consistency": (6.0, 7.0), "visibility": (5.5, 6.5)},
    "accountancy": {"clarity": (6.5, 7.5), "consistency": (6.0, 7.0), "visibility": (5.5, 6.5)},
    "consultancy": {"clarity": (6.5, 7.5), "consistency": (6.0, 7.0), "visibility": (5.5, 6.5)},
    "consulting": {"clarity": (6.5, 7.5), "consistency": (6.0, 7.0), "visibility": (5.5, 6.5)},
    "retail": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "food": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "drink": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "coffee": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "restaurant": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "hospitality": {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.0, 6.0)},
    "saas": {"clarity": (7.0, 8.0), "consistency": (6.5, 7.5), "visibility": (6.5, 7.5)},
    "tech": {"clarity": (7.0, 8.0), "consistency": (6.5, 7.5), "visibility": (6.5, 7.5)},
    "software": {"clarity": (7.0, 8.0), "consistency": (6.5, 7.5), "visibility": (6.5, 7.5)},
    "trades": {"clarity": (5.0, 6.0), "consistency": (4.5, 5.5), "visibility": (5.5, 6.5)},
    "plumbing": {"clarity": (5.0, 6.0), "consistency": (4.5, 5.5), "visibility": (5.5, 6.5)},
    "construction": {"clarity": (5.0, 6.0), "consistency": (4.5, 5.5), "visibility": (5.5, 6.5)},
    "electrical": {"clarity": (5.0, 6.0), "consistency": (4.5, 5.5), "visibility": (5.5, 6.5)},
    "creative": {"clarity": (6.5, 7.5), "consistency": (7.0, 8.0), "visibility": (6.0, 7.0)},
    "agency": {"clarity": (6.5, 7.5), "consistency": (7.0, 8.0), "visibility": (6.0, 7.0)},
    "design": {"clarity": (6.5, 7.5), "consistency": (7.0, 8.0), "visibility": (6.0, 7.0)},
    "marketing": {"clarity": (6.5, 7.5), "consistency": (7.0, 8.0), "visibility": (6.0, 7.0)},
}

# Default benchmarks for sectors that don't match
DEFAULT_BENCHMARKS = {"clarity": (6.0, 7.0), "consistency": (5.5, 6.5), "visibility": (5.5, 6.5)}


def _answer_quality(answer):
    """
    Score the quality of a single answer on a 0-3 scale:
    0 = missing/blank, 1 = vague, 2 = decent, 3 = specific/detailed
    """
    if not answer or answer.strip() == "" or answer.lower().strip() in ("", "nan"):
        return 0
    
    answer_lower = answer.lower().strip()
    
    # Check for vague signals
    for signal in VAGUE_SIGNALS:
        if signal in answer_lower:
            return 1
    
    # Check for strong signals
    has_strong = any(s in answer_lower for s in STRONG_SIGNALS)
    
    # Length-based heuristic: longer, more detailed answers tend to be better
    word_count = len(answer.split())
    
    if has_strong and word_count >= 10:
        return 3
    elif word_count >= 15 or has_strong:
        return 3
    elif word_count >= 5:
        return 2
    else:
        return 1


def score_clarity(answers):
    """
    Score Brand Clarity (Q8-Q12) out of 10.
    Q8: one-line description, Q9: problem solved, Q10: ideal customer,
    Q11: differentiator (critical), Q12: documented mission
    """
    q8 = _answer_quality(answers.get("Q8", ""))
    q9 = _answer_quality(answers.get("Q9", ""))
    q10 = _answer_quality(answers.get("Q10", ""))
    q11 = _answer_quality(answers.get("Q11", ""))
    q12 = _answer_quality(answers.get("Q12", ""))
    
    # Base score from answer qualities (max 15 raw → normalise to 10)
    raw = q8 + q9 + q10 + q11 + q12  # max 15
    score = round((raw / 15) * 10)
    
    # Rule: if Q11 (differentiator) is vague (quality ≤ 1), cap at 5
    if q11 <= 1:
        score = min(score, 5)
    
    return max(0, min(10, score))


def score_consistency(answers):
    """
    Score Brand Consistency (Q13-Q17) out of 10.
    Q13: touchpoints, Q14: visual consistency, Q15: brand voice,
    Q16: guidelines exist, Q17: who creates content
    """
    q13 = _answer_quality(answers.get("Q13", ""))
    q14 = _answer_quality(answers.get("Q14", ""))
    q15 = _answer_quality(answers.get("Q15", ""))
    q16 = _answer_quality(answers.get("Q16", ""))
    q17 = _answer_quality(answers.get("Q17", ""))
    
    raw = q13 + q14 + q15 + q16 + q17  # max 15
    score = round((raw / 15) * 10)
    
    # If no guidelines (Q16 is vague/missing), consistency shouldn't be high
    if q16 <= 1 and score > 6:
        score = 6
    
    return max(0, min(10, score))


def score_visibility(answers):
    """
    Score Brand Visibility (Q18-Q22) out of 10.
    Q18: how customers find them, Q19: Google Business Profile,
    Q20: AI discoverability, Q21: directories, Q22: press mentions
    """
    q18 = _answer_quality(answers.get("Q18", ""))
    q19 = _answer_quality(answers.get("Q19", ""))
    q20 = _answer_quality(answers.get("Q20", ""))
    q21 = _answer_quality(answers.get("Q21", ""))
    q22 = _answer_quality(answers.get("Q22", ""))
    
    raw = q18 + q19 + q20 + q21 + q22  # max 15
    score = round((raw / 15) * 10)
    
    return max(0, min(10, score))


def rag_status(total):
    """Return RAG status based on total score out of 30."""
    if total >= 24:
        return "GREEN", "Strong foundations"
    elif total >= 15:
        return "AMBER", "Gaps identified"
    else:
        return "RED", "Urgent action needed"


def get_industry_benchmarks(industry):
    """Look up industry benchmarks, returning midpoint of typical range."""
    industry_lower = industry.lower().strip()
    
    for sector_key, benchmarks in INDUSTRY_BENCHMARKS.items():
        if sector_key in industry_lower:
            return {
                dim: round((lo + hi) / 2, 1)
                for dim, (lo, hi) in benchmarks.items()
            }
    
    # Default benchmarks
    return {
        dim: round((lo + hi) / 2, 1)
        for dim, (lo, hi) in DEFAULT_BENCHMARKS.items()
    }


def score_brand(parsed_brief):
    """
    Main scoring function. Takes a parsed brief dict and returns full scoring data.
    
    Args:
        parsed_brief: dict from parse_brief.parse() with 'answers' key
    
    Returns:
        dict with scores, benchmarks, RAG status, and metadata
    """
    answers = parsed_brief["answers"]
    
    clarity = score_clarity(answers)
    consistency = score_consistency(answers)
    visibility = score_visibility(answers)
    total = clarity + consistency + visibility
    
    status, status_label = rag_status(total)
    
    industry = answers.get("Q4", "General")
    benchmarks = get_industry_benchmarks(industry)
    
    return {
        "scores": {
            "clarity": clarity,
            "consistency": consistency,
            "visibility": visibility,
        },
        "total": total,
        "rag_status": status,
        "rag_label": status_label,
        "industry_benchmarks": benchmarks,
        "business_name": answers.get("Q1", "Unknown Business"),
        "industry": industry,
        "arr_range": answers.get("Q7", "Unknown"),
    }


if __name__ == "__main__":
    # Quick test with dummy data
    test_answers = {
        "Q1": "Harrow & Field Coffee Roasters",
        "Q4": "Specialty Coffee Roastery",
        "Q7": "£100k–£250k",
        "Q8": "We roast specialty coffee and sell it direct to consumers and cafés across the South West.",
        "Q9": "People want better coffee but don't know where to start — we make specialty accessible.",
        "Q10": "Home coffee enthusiasts aged 28–45, typically urban professionals who care about quality and provenance.",
        "Q11": "Not sure what makes us different really",
        "Q12": "No documented mission statement",
        "Q13": "Website, Instagram, local markets, a few wholesale accounts",
        "Q14": "Mostly consistent but we have two logos from different eras",
        "Q15": "Casual, friendly, knowledgeable — but it's not written down",
        "Q16": "No formal guidelines",
        "Q17": "I (founder) do everything — social, website, packaging",
        "Q18": "Instagram mostly, some word of mouth, local markets",
        "Q19": "We have a Google Business Profile but haven't updated it in months",
        "Q20": "No idea if AI tools mention us",
        "Q21": "Listed on a couple of coffee directories",
        "Q22": "One local newspaper mention last year",
        "Q23": "About £200/month on Instagram ads",
    }
    
    result = score_brand({"answers": test_answers})
    print(f"Business: {result['business_name']}")
    print(f"Clarity: {result['scores']['clarity']}/10")
    print(f"Consistency: {result['scores']['consistency']}/10")
    print(f"Visibility: {result['scores']['visibility']}/10")
    print(f"Total: {result['total']}/30 → {result['rag_status']} ({result['rag_label']})")
    print(f"Benchmarks: {result['industry_benchmarks']}")
