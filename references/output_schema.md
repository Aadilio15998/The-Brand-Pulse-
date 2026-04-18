# Output JSON Schema

The `generate_scorecard.py` script reads a JSON file with this exact shape:

```json
{
  "business_name": "Harrow & Field Coffee Roasters",
  "industry": "Specialty Coffee Roastery",
  "audit_date": "18 April 2026",
  "scores": {
    "clarity": 5,
    "consistency": 3,
    "visibility": 4
  },
  "industry_benchmarks": {
    "clarity": 6.5,
    "consistency": 6.0,
    "visibility": 5.5
  },
  "diagnoses": {
    "clarity": "2–3 sentence diagnosis in plain English...",
    "consistency": "2–3 sentence diagnosis in plain English...",
    "visibility": "2–3 sentence diagnosis in plain English..."
  },
  "recommendations": [
    {
      "title": "Write a one-page positioning document",
      "timeframe": "2 weeks",
      "effort": "Low — one working session",
      "detail": "2–4 sentences of specific, actionable guidance..."
    },
    {
      "title": "Fix your Google Business Profile this week",
      "timeframe": "1 hour",
      "effort": "Tiny — free and immediate",
      "detail": "2–4 sentences..."
    },
    {
      "title": "Pick one consistent visual system and retire the old one",
      "timeframe": "6 weeks",
      "effort": "Medium — one freelance brief, ~£800–£1,500",
      "detail": "2–4 sentences..."
    }
  ],
  "industry_context": "One paragraph (3–5 sentences) on what strong brands in this sector do that this business is not yet doing."
}
```

## Field rules

- **scores**: Integers 0–10. Decimals will break the layout.
- **industry_benchmarks**: Floats 0–10. One decimal place is fine.
- **audit_date**: Human-readable format ("18 April 2026"), not ISO.
- **business_name**: Will auto-truncate with an ellipsis if it exceeds card width.
- **diagnoses**: 2–3 sentences per dimension. Cards auto-size, so longer text is fine, but keep it tight.
- **recommendations**: Always exactly 3. Order matters — index 0 is priority #1.
- **recommendations[i].effort**: For paid items, include a £ range. For DIY items, describe the time/lift.
- **industry_context**: Plain prose, no lists. Around 60–80 words works best.

## Writing the JSON

Always write to `/home/claude/scoring.json` (or similar tmp path), then pass that path to the generator. Don't try to inline the JSON on the command line — it will break on quotes and em-dashes.

```python
import json
with open("/home/claude/scoring.json", "w") as f:
    json.dump(scoring, f, indent=2, ensure_ascii=False)
```

Then:
```bash
python3 scripts/generate_scorecard.py /home/claude/scoring.json /mnt/user-data/outputs/brand_pulse_scorecard.pdf
```
