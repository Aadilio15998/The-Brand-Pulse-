"""
Content Writer — generates diagnoses, recommendations, and industry context
from scored brand data and parsed brief answers.

Uses template-based generation with client-specific language injection.
"""

# ---- Diagnosis templates ----
# Structure: what's working → the gap → the business consequence

CLARITY_TEMPLATES = {
    "high": (  # 8-10
        "You've built a clear positioning that your customers can immediately understand — "
        "your description of what you do is sharp and your ideal customer is well-defined. "
        "The foundation is strong; the next step is making sure that clarity carries through "
        "every touchpoint consistently."
    ),
    "mid": (  # 5-7
        "You have a reasonable sense of what your business does and who it's for, but "
        "there are gaps — particularly around what makes you genuinely different from "
        "competitors. Without a sharper differentiator, potential customers have no reason "
        "to choose you over the alternative, and your marketing will always feel generic."
    ),
    "low": (  # 2-4
        "Right now it's hard to tell what your business truly stands for. Your positioning "
        "is vague, your ideal customer isn't clearly defined, and there's no documented "
        "differentiator. This means every pound you spend on marketing is working harder "
        "than it needs to — you're shouting without a clear message."
    ),
    "critical": (  # 0-1
        "Your brand has no clear positioning at all. Without knowing who you serve, what "
        "problem you solve, and why you're different, every other investment — website, "
        "social media, advertising — is money going nowhere. This is the single most "
        "important thing to fix."
    ),
}

CONSISTENCY_TEMPLATES = {
    "high": (
        "Your brand looks and sounds like one business everywhere it appears — visuals are "
        "cohesive, your voice is distinct, and you have guidelines keeping it all together. "
        "This kind of consistency builds trust fast, and customers notice it even if they "
        "can't articulate why."
    ),
    "mid": (
        "You're mostly consistent, but without formal brand guidelines, there are cracks — "
        "your visual identity or voice shifts depending on who's creating the content or "
        "which platform it's on. Over time, this erodes trust and makes your business feel "
        "less established than it actually is."
    ),
    "low": (
        "Your brand feels fragmented — it looks and sounds different depending on where "
        "someone encounters it. Without guidelines or a consistent visual system, every "
        "new piece of content risks confusing your audience about who you are. This makes "
        "it much harder to build the recognition that drives repeat business."
    ),
    "critical": (
        "There is no consistent brand to speak of. Your business looks and sounds completely "
        "different across every channel. Customers can't build familiarity or trust when the "
        "brand they see on Instagram bears no resemblance to your website or packaging."
    ),
}

VISIBILITY_TEMPLATES = {
    "high": (
        "You're genuinely visible — customers can find you through multiple channels, your "
        "Google presence is active, and you've even got some press coverage. The challenge "
        "now is sustaining this and making sure AI-powered tools can surface your business "
        "as the landscape shifts."
    ),
    "mid": (
        "You're visible on one or two channels, but there are real gaps — particularly "
        "around search, directories, or AI discoverability. In a world where buyers "
        "increasingly find businesses through Google, AI assistants, and industry listings, "
        "those blind spots are costing you customers you'll never even know about."
    ),
    "low": (
        "Your business is genuinely hard to find online. You're relying on word of mouth "
        "and perhaps one social channel, but you're invisible on Google, absent from "
        "directories, and completely undiscoverable by AI tools. Every day this continues, "
        "potential customers who are actively looking for what you offer are finding your "
        "competitors instead."
    ),
    "critical": (
        "You are essentially invisible online. No meaningful search presence, no directory "
        "listings, no AI discoverability. If someone doesn't already know your name, they "
        "will not find you. This is fixable, and some of the highest-impact fixes take less "
        "than an hour."
    ),
}


def _score_tier(score):
    """Map a 0-10 score to a template tier."""
    if score >= 8:
        return "high"
    elif score >= 5:
        return "mid"
    elif score >= 2:
        return "low"
    else:
        return "critical"


def _personalise_diagnosis(template, answers, dimension):
    """
    Inject client-specific language into a diagnosis template.
    Looks for relevant client quotes to make the diagnosis sharper.
    """
    diagnosis = template
    
    # Try to inject client's own words where relevant
    if dimension == "clarity":
        q11 = answers.get("Q11", "")
        if q11 and len(q11) > 5 and "not sure" not in q11.lower():
            pass  # Differentiator is specific enough — template stands
        elif q11:
            # Client's own vague words make the point
            diagnosis = diagnosis.replace(
                "what makes you genuinely different",
                f"what makes you different — you said \"{q11.strip()}\""
            )
    
    elif dimension == "consistency":
        q16 = answers.get("Q16", "")
        if q16 and any(neg in q16.lower() for neg in ["no", "don't", "haven't", "not"]):
            pass  # Template already addresses lack of guidelines
    
    elif dimension == "visibility":
        q18 = answers.get("Q18", "")
        if q18 and len(q18) > 3:
            # Reference their actual channels
            diagnosis = diagnosis.replace(
                "one or two channels",
                f"channels like {q18.strip()}"
            ).replace(
                "one social channel",
                q18.strip()
            )
    
    return diagnosis


def write_diagnoses(scoring_data, answers):
    """
    Generate diagnoses for all three dimensions.
    
    Returns:
        dict with clarity, consistency, visibility diagnosis strings
    """
    scores = scoring_data["scores"]
    
    diagnoses = {}
    for dim in ["clarity", "consistency", "visibility"]:
        tier = _score_tier(scores[dim])
        templates = {
            "clarity": CLARITY_TEMPLATES,
            "consistency": CONSISTENCY_TEMPLATES,
            "visibility": VISIBILITY_TEMPLATES,
        }[dim]
        template = templates[tier]
        diagnoses[dim] = _personalise_diagnosis(template, answers, dim)
    
    return diagnoses


# ---- Recommendation generation ----

# ARR-calibrated effort levels
ARR_EFFORT = {
    "micro": {  # <£100k
        "low": "Free — one focused afternoon",
        "medium": "Low — £100–£300 for a freelance brief",
        "high": "Medium — £500–£1,000 for a specialist",
    },
    "small": {  # £100k–£250k
        "low": "Free — a few hours of focused work",
        "medium": "Low — £200–£500 for a freelance brief",
        "high": "Medium — £800–£1,500 for a specialist",
    },
    "medium": {  # £250k–£1M
        "low": "Minimal — internal time only",
        "medium": "Medium — £500–£2,000 for freelance work",
        "high": "Moderate — £2,000–£5,000 for agency support",
    },
    "large": {  # £1M+
        "low": "Minimal — internal time only",
        "medium": "Medium — £1,000–£3,000 for specialist engagement",
        "high": "Moderate — £3,000–£8,000 for agency project",
    },
}

# Recommendation templates by dimension and priority
RECOMMENDATION_TEMPLATES = {
    "clarity": {
        "title": "Write a one-page positioning document this week",
        "timeframe": "1 week",
        "effort_level": "low",
        "detail": (
            "Sit down for one focused session and answer four questions on a single page: "
            "What do we do? Who is it for? What problem do we solve? Why us and not someone else? "
            "This document becomes the filter for every marketing decision you make. Without it, "
            "every campaign, social post, and sales conversation starts from scratch."
        ),
    },
    "consistency": {
        "title": "Create a simple brand guidelines document",
        "timeframe": "2–3 weeks",
        "effort_level": "medium",
        "detail": (
            "Commission a one-page brand guidelines sheet covering your logo usage, "
            "colour palette, fonts, and three words that describe your tone of voice. "
            "Share it with anyone who creates content for your business. This stops the "
            "drift that makes your brand feel amateur and builds the recognition that keeps "
            "customers coming back."
        ),
    },
    "visibility_google": {
        "title": "Fix your Google Business Profile this week",
        "timeframe": "1 hour",
        "effort_level": "low",
        "detail": (
            "Claim or update your Google Business Profile with accurate hours, fresh photos, "
            "a compelling description, and your correct categories. This is the single fastest "
            "way to appear in local search — and it's completely free. Most SMEs in your sector "
            "haven't done this properly, so just completing it puts you ahead."
        ),
    },
    "visibility_ai": {
        "title": "Make your business discoverable by AI tools",
        "timeframe": "2–4 weeks",
        "effort_level": "medium",
        "detail": (
            "AI assistants like ChatGPT and Google's AI Overview pull from structured web content. "
            "Add a clear FAQ page to your website, ensure your business is listed in key industry "
            "directories, and write a concise 'About' page that answers the questions your "
            "customers actually ask. This positions you for the next wave of discovery."
        ),
    },
    "visibility_press": {
        "title": "Get featured in one industry directory and one local publication",
        "timeframe": "4–6 weeks",
        "effort_level": "medium",
        "detail": (
            "Identify the top two directories in your sector and submit a listing. Then pitch "
            "a short story to your local newspaper or trade publication — a founder profile, "
            "a milestone, or a community angle. Even one mention builds credibility and creates "
            "a backlink that helps your search ranking."
        ),
    },
    "consistency_visual": {
        "title": "Pick one visual system and retire the old one",
        "timeframe": "6 weeks",
        "effort_level": "high",
        "detail": (
            "If you have multiple logos, colour schemes, or visual identities floating around, "
            "pick the strongest one and systematically replace the rest. Update your website, "
            "social profiles, email signature, and packaging. A single visual identity doubles "
            "the speed at which people recognise and remember your brand."
        ),
    },
}


def _detect_arr_tier(arr_text):
    """Map ARR range text to a tier for effort calibration."""
    arr_lower = str(arr_text).lower().replace(",", "").replace(" ", "")
    
    if any(x in arr_lower for x in ["1m", "1,000", "million", "£1m", "1000k"]):
        return "large"
    elif any(x in arr_lower for x in ["250k", "500k", "£250", "£500"]):
        return "medium"
    elif any(x in arr_lower for x in ["100k", "£100", "150k", "200k"]):
        return "small"
    else:
        return "micro"


def _get_effort(arr_tier, level):
    """Get effort description calibrated to ARR."""
    return ARR_EFFORT.get(arr_tier, ARR_EFFORT["small"]).get(level, "Low-cost")


def write_recommendations(scoring_data, answers):
    """
    Generate 3 prioritised recommendations.
    
    Priority rules:
    1. If Clarity is RED (≤4), fix Clarity first
    2. Otherwise, fix lowest-scoring dimension first
    3. Fill remaining by impact
    """
    scores = scoring_data["scores"]
    arr_tier = _detect_arr_tier(scoring_data.get("arr_range", ""))
    
    # Determine priority order
    dims_sorted = sorted(
        ["clarity", "consistency", "visibility"],
        key=lambda d: scores[d]
    )
    
    # Rule: if clarity ≤ 4, it goes first regardless
    if scores["clarity"] <= 4:
        dims_sorted.remove("clarity")
        dims_sorted.insert(0, "clarity")
    
    recommendations = []
    used_templates = set()
    
    for dim in dims_sorted:
        if len(recommendations) >= 3:
            break
        
        if dim == "clarity" and "clarity" not in used_templates:
            rec = RECOMMENDATION_TEMPLATES["clarity"].copy()
            rec["effort"] = _get_effort(arr_tier, rec.pop("effort_level"))
            recommendations.append(rec)
            used_templates.add("clarity")
        
        elif dim == "consistency" and "consistency" not in used_templates:
            # Choose between guidelines and visual based on scores
            q16_quality = len(answers.get("Q16", "")) > 5
            if not q16_quality:
                rec = RECOMMENDATION_TEMPLATES["consistency"].copy()
            else:
                rec = RECOMMENDATION_TEMPLATES["consistency_visual"].copy()
            rec["effort"] = _get_effort(arr_tier, rec.pop("effort_level"))
            recommendations.append(rec)
            used_templates.add("consistency")
        
        elif dim == "visibility" and "visibility" not in used_templates:
            # Choose the most impactful visibility fix
            q19 = answers.get("Q19", "").lower()
            q20 = answers.get("Q20", "").lower()
            
            if any(neg in q19 for neg in ["no", "don't", "haven't", "not"]) or len(q19) < 5:
                rec = RECOMMENDATION_TEMPLATES["visibility_google"].copy()
            elif any(neg in q20 for neg in ["no", "don't", "haven't", "not", "idea"]):
                rec = RECOMMENDATION_TEMPLATES["visibility_ai"].copy()
            else:
                rec = RECOMMENDATION_TEMPLATES["visibility_press"].copy()
            rec["effort"] = _get_effort(arr_tier, rec.pop("effort_level"))
            recommendations.append(rec)
            used_templates.add("visibility")
    
    # Fill remaining slots if we have fewer than 3
    backup_order = ["visibility_ai", "visibility_press", "visibility_google",
                     "consistency_visual", "consistency"]
    for template_key in backup_order:
        if len(recommendations) >= 3:
            break
        if template_key not in used_templates:
            rec = RECOMMENDATION_TEMPLATES[template_key].copy()
            rec["effort"] = _get_effort(arr_tier, rec.pop("effort_level"))
            recommendations.append(rec)
            used_templates.add(template_key)
    
    return recommendations[:3]


# ---- Industry context ----

INDUSTRY_CONTEXT_TEMPLATES = {
    "food": (
        "The strongest independent food and drink brands in the UK have moved well beyond "
        "just having good products. They invest in storytelling — origin, process, people — "
        "and maintain a tight visual identity across packaging, social media, and their "
        "physical presence. Most importantly, the best performers have claimed and optimised "
        "their Google Business Profile, appear in at least two major food directories, and "
        "are beginning to think about AI discoverability as a real channel."
    ),
    "coffee": (
        "The best specialty coffee brands don't just sell beans — they sell an identity. "
        "They have precise positioning (single origin vs blend, home vs wholesale, ethical "
        "sourcing), consistent packaging and social presence, and they show up in Google "
        "Maps, specialty coffee directories, and increasingly in AI-powered recommendation "
        "tools. Those who invest in clear brand guidelines and a searchable web presence "
        "consistently outperform on customer retention and wholesale partner acquisition."
    ),
    "professional_services": (
        "Leading professional services firms build trust through relentless consistency — "
        "their website, proposals, LinkedIn presence, and client communications all speak "
        "with one voice and one visual identity. They publish thought leadership content "
        "that reinforces their positioning, maintain claimed and active Google Business "
        "Profiles, and appear in sector-specific directories. The firms that are pulling "
        "ahead are also ensuring their expertise is discoverable by AI assistants."
    ),
    "tech": (
        "The most successful B2B tech and SaaS brands invest heavily in clarity of positioning — "
        "they can articulate their ICP, differentiator, and value proposition in one sentence. "
        "Their visual identity is systematic (design systems, not just logos), and their "
        "content strategy is built around discoverability: SEO, structured data, directory "
        "listings, and AI-optimised FAQ pages. Consistency across product, website, and "
        "sales collateral is table stakes."
    ),
    "trades": (
        "The trades businesses winning the most work have figured out something their "
        "competitors haven't: online visibility matters as much as word of mouth. They have "
        "fully optimised Google Business Profiles with regular review responses, they appear "
        "in Checkatrade, Bark, and sector-specific directories, and their van livery matches "
        "their website. The gap between the best and the rest is widening fast — and it's "
        "almost entirely about being findable and looking professional."
    ),
    "creative": (
        "Top creative agencies and studios practice what they preach — their brand identity "
        "is immaculate, their portfolio is curated rather than comprehensive, and their "
        "positioning is razor-sharp (sector-specific, service-specific, or both). They "
        "maintain a consistent visual language across their website, case studies, social "
        "presence, and proposals. The best are also investing in content that makes them "
        "discoverable by AI-powered brief-matching tools."
    ),
    "default": (
        "The strongest brands in any sector share three traits: they can explain what they "
        "do and who it's for in one sentence, they look and sound the same everywhere a "
        "customer encounters them, and they're easy to find — through search, directories, "
        "and increasingly through AI-powered recommendations. SMEs that invest even modestly "
        "in these three areas consistently outperform on customer acquisition and retention."
    ),
}


def write_industry_context(industry):
    """Generate an industry context paragraph based on the client's sector."""
    industry_lower = industry.lower().strip()
    
    for key, template in INDUSTRY_CONTEXT_TEMPLATES.items():
        if key != "default" and key in industry_lower:
            return template
    
    # Check broader categories
    if any(w in industry_lower for w in ["food", "drink", "restaurant", "hospitality", "bakery"]):
        return INDUSTRY_CONTEXT_TEMPLATES["food"]
    if any(w in industry_lower for w in ["coffee", "roast", "café", "cafe"]):
        return INDUSTRY_CONTEXT_TEMPLATES["coffee"]
    if any(w in industry_lower for w in ["law", "account", "consult", "financial", "advisory"]):
        return INDUSTRY_CONTEXT_TEMPLATES["professional_services"]
    if any(w in industry_lower for w in ["saas", "software", "tech", "digital", "app"]):
        return INDUSTRY_CONTEXT_TEMPLATES["tech"]
    if any(w in industry_lower for w in ["plumb", "electri", "build", "construct", "trade"]):
        return INDUSTRY_CONTEXT_TEMPLATES["trades"]
    if any(w in industry_lower for w in ["creative", "agency", "design", "marketing", "media"]):
        return INDUSTRY_CONTEXT_TEMPLATES["creative"]
    
    return INDUSTRY_CONTEXT_TEMPLATES["default"]


if __name__ == "__main__":
    # Quick demonstration
    test_scoring = {
        "scores": {"clarity": 5, "consistency": 3, "visibility": 4},
        "arr_range": "£100k–£250k",
    }
    test_answers = {
        "Q11": "Not sure what makes us different really",
        "Q16": "No formal guidelines",
        "Q18": "Instagram mostly, some word of mouth",
        "Q19": "Haven't updated it in months",
        "Q20": "No idea if AI tools mention us",
    }
    
    diagnoses = write_diagnoses(test_scoring, test_answers)
    recs = write_recommendations(test_scoring, test_answers)
    context = write_industry_context("Specialty Coffee Roastery")
    
    print("=== DIAGNOSES ===")
    for dim, diag in diagnoses.items():
        print(f"\n{dim.upper()}: {diag}")
    
    print("\n=== RECOMMENDATIONS ===")
    for i, rec in enumerate(recs, 1):
        print(f"\n#{i}: {rec['title']}")
        print(f"   Timeframe: {rec['timeframe']}")
        print(f"   Effort: {rec['effort']}")
        print(f"   {rec['detail'][:100]}...")
    
    print(f"\n=== INDUSTRY CONTEXT ===\n{context}")
