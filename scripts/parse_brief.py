"""
Brief Parser — reads a Typeform CSV export and returns a structured dict of 26 answers.

Handles both CSV shapes:
  - Shape A (Long): two columns — question, answer
  - Shape B (Wide): one column per question, one data row
"""
import pandas as pd
import re

# Canonical question labels for matching
QUESTION_KEYWORDS = {
    1: ["business name", "company name", "name of your business"],
    2: ["website", "url", "web address"],
    3: ["location", "city", "where are you based", "where is your business"],
    4: ["industry", "sector", "what sector", "what industry"],
    5: ["trading", "how long", "years in business", "how many years"],
    6: ["team size", "employees", "how many people", "team"],
    7: ["arr", "revenue", "annual revenue", "turnover"],
    8: ["one sentence", "one-sentence", "describe what you do", "what does your business do"],
    9: ["problem", "what problem", "pain point"],
    10: ["ideal customer", "target customer", "who is your ideal", "customer avatar"],
    11: ["differentiator", "different", "stand out", "unique", "what makes you"],
    12: ["mission", "vision", "documented mission", "purpose statement"],
    13: ["touchpoints", "channels", "active touchpoints", "where does your brand appear"],
    14: ["visual", "consistent visual", "look and feel", "visual identity"],
    15: ["brand voice", "tone of voice", "voice", "how would you describe your brand voice"],
    16: ["guidelines", "brand guidelines", "style guide"],
    17: ["content", "who creates", "content creation", "who manages"],
    18: ["find you", "discover", "how do customers find", "discovery"],
    19: ["google business", "google profile", "gbp", "google my business"],
    20: ["ai", "chatgpt", "ai discoverability", "ai tools", "discoverable by ai"],
    21: ["directories", "directory", "listings", "industry directories"],
    22: ["press", "media", "press mentions", "pr", "media coverage"],
    23: ["marketing spend", "monthly spend", "budget", "how much do you spend"],
    24: ["success", "what does success look like", "audit success", "what would success"],
    25: ["prior audit", "previous audit", "had an audit before", "brand audit before"],
    26: ["referral", "how did you hear", "how did you find", "referred"],
}

CRITICAL_QUESTIONS = [4, 7, 11]


def _detect_shape(df):
    """Determine if the CSV is long format (Shape A) or wide format (Shape B)."""
    if len(df.columns) == 2 and len(df) >= 20:
        return "long"
    if len(df.columns) >= 20 and len(df) <= 5:
        return "wide"
    # Heuristic: if more rows than columns, probably long
    if len(df) > len(df.columns):
        return "long"
    return "wide"


def _match_question_number(text):
    """Try to extract a question number from a column/question label."""
    text_lower = str(text).lower().strip()
    
    # Direct Q-number match: "Q1", "Q1 -", "Q1:", etc.
    q_match = re.match(r'q(\d+)\b', text_lower)
    if q_match:
        num = int(q_match.group(1))
        if 1 <= num <= 26:
            return num
    
    # Keyword matching
    for q_num, keywords in QUESTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return q_num
    
    return None


def _parse_long(df):
    """Parse Shape A: two-column format (question, answer)."""
    q_col = df.columns[0]
    a_col = df.columns[1]
    
    answers = {}
    for _, row in df.iterrows():
        q_text = str(row[q_col])
        q_num = _match_question_number(q_text)
        if q_num:
            answers[f"Q{q_num}"] = str(row[a_col]).strip() if pd.notna(row[a_col]) else ""
    
    return answers


def _parse_wide(df):
    """Parse Shape B: one-column-per-question format."""
    answers = {}
    row = df.iloc[0]  # Single submission = first data row
    
    for col in df.columns:
        q_num = _match_question_number(col)
        if q_num:
            answers[f"Q{q_num}"] = str(row[col]).strip() if pd.notna(row[col]) else ""
    
    return answers


def parse(csv_path):
    """
    Parse a Typeform brief CSV and return a structured dict.
    
    Returns:
        dict with keys:
            - 'answers': dict mapping Q1–Q26 to answer strings
            - 'missing': list of missing question numbers
            - 'critical_missing': list of missing critical questions (Q4, Q7, Q11)
            - 'shape': detected CSV shape ('long' or 'wide')
    """
    df = pd.read_csv(csv_path)
    shape = _detect_shape(df)
    
    if shape == "long":
        answers = _parse_long(df)
    else:
        answers = _parse_wide(df)
    
    # Identify missing questions
    all_questions = set(range(1, 27))
    found_questions = {int(k[1:]) for k in answers.keys()}
    missing = sorted(all_questions - found_questions)
    critical_missing = [q for q in CRITICAL_QUESTIONS if q in missing]
    
    return {
        "answers": answers,
        "missing": missing,
        "critical_missing": critical_missing,
        "shape": shape,
    }


def get_answer(parsed, q_num, default=""):
    """Helper to safely get an answer by question number."""
    return parsed["answers"].get(f"Q{q_num}", default)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python parse_brief.py <brief.csv>")
        sys.exit(1)
    
    result = parse(sys.argv[1])
    print(f"Shape detected: {result['shape']}")
    print(f"Questions found: {len(result['answers'])}/26")
    if result['missing']:
        print(f"Missing: Q{', Q'.join(str(q) for q in result['missing'])}")
    if result['critical_missing']:
        print(f"⚠️  CRITICAL MISSING: Q{', Q'.join(str(q) for q in result['critical_missing'])}")
    print()
    for key in sorted(result['answers'].keys(), key=lambda x: int(x[1:])):
        val = result['answers'][key]
        preview = val[:80] + "..." if len(val) > 80 else val
        print(f"  {key}: {preview}")
