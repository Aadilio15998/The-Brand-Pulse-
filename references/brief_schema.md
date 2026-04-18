# Brief Schema

The client brief comes from a 26-question Typeform. CSV exports arrive in one of two common shapes:

## Shape A — Long format (two columns)

```
question,answer
Q1 - Business name,Harrow & Field Coffee Roasters
Q2 - Website URL,www.harrowandfield.co.uk
...
```

Each row is one Q&A. Read it with pandas:
```python
import pandas as pd
df = pd.read_csv(path)
# Typical column names: 'question'/'answer', 'Question'/'Response', 'Field'/'Value'
answers = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
```

## Shape B — Wide format (one row per submission)

```
Q1 - Business name,Q2 - Website URL,Q3 - Location,...
Harrow & Field Coffee Roasters,www.harrowandfield.co.uk,"Bristol, UK",...
```

Each column is one question, one row per submission. For a single client, there's only one data row.
```python
import pandas as pd
df = pd.read_csv(path)
answers = df.iloc[0].to_dict()
```

## The 26 questions

### Section 1 — Business Details (context only, not scored)
- Q1: Business name
- Q2: Website URL
- Q3: Location
- Q4: Industry / sector **← required for benchmarking**
- Q5: Trading length
- Q6: Team size
- Q7: ARR range **← required for calibrating recommendations**

### Section 2 — Brand Clarity (Q8–Q12, scored out of 10)
- Q8: One-sentence description of what they do
- Q9: Problem they solve
- Q10: Ideal customer
- Q11: Differentiator **← required — if vague, clarity score caps at 5**
- Q12: Documented mission/vision

### Section 3 — Brand Consistency (Q13–Q17, scored out of 10)
- Q13: Active touchpoints
- Q14: Visual identity consistency
- Q15: Defined brand voice
- Q16: Brand guidelines exist
- Q17: Who creates content

### Section 4 — Brand Visibility (Q18–Q22, scored out of 10)
- Q18: Where customers find them
- Q19: Google Business Profile status
- Q20: AI tool discoverability
- Q21: Industry directory listings
- Q22: Press mentions (last 12 months)

### Section 4 (continued) — Context only
- Q23: Rough monthly marketing spend **← used for calibrating recommendation budgets**

### Section 5 — Final Context (not scored)
- Q24: Success definition for the audit
- Q25: Prior audit history
- Q26: Referral source

## Handling edge cases

- **Missing questions**: Note which are missing. Q4, Q7, and Q11 are critical — ask the user for these before scoring. Others can be estimated from adjacent answers.
- **Vague answers**: Answers like "not sure", "maybe", "haven't thought about it" are themselves scoring signals — they usually indicate low-to-mid scores on that dimension.
- **Contradictions**: If Q14 says "consistent" but Q16 says "no guidelines", trust the more specific answer (usually the one with evidence).
- **Column name variations**: Questions may be phrased differently in exports. Match by question number or by the first 3–4 keywords of the prompt, not by exact string.
