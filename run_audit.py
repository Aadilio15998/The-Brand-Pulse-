#!/usr/bin/env python3
"""
Brand Pulse Audit — Main Pipeline

Usage:
    python run_audit.py <brief.csv> <output.pdf>
    python run_audit.py sample_briefs/harrow_field_long.csv output/scorecard.pdf

Pipeline:
    1. Parse the client brief CSV
    2. Score the brand (clarity, consistency, visibility)
    3. Generate diagnoses, recommendations, and industry context
    4. Assemble the scoring JSON
    5. Generate the branded 4-page PDF
"""
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.parse_brief import parse, get_answer
from scripts.score_brand import score_brand
from scripts.write_content import write_diagnoses, write_recommendations, write_industry_context
from scripts.generate_scorecard import build_pdf


def run_audit(csv_path, output_path, chart_dir=None):
    """
    Run the full Brand Pulse audit pipeline.
    
    Args:
        csv_path: Path to the client brief CSV
        output_path: Path for the output PDF
        chart_dir: Directory for intermediate chart images (default: /tmp/bp_charts)
    
    Returns:
        str: Path to the generated PDF
    """
    if chart_dir is None:
        chart_dir = os.path.join(os.path.dirname(output_path), ".bp_charts")
    
    # --- Step 1: Parse the brief ---
    print(f"📋 Parsing brief: {csv_path}")
    parsed = parse(csv_path)
    
    print(f"   Shape detected: {parsed['shape']}")
    print(f"   Questions found: {len(parsed['answers'])}/26")
    
    if parsed["critical_missing"]:
        print(f"   ⚠️  Critical questions missing: Q{', Q'.join(str(q) for q in parsed['critical_missing'])}")
        print("   Proceeding with conservative scoring for missing data...")
    
    if parsed["missing"]:
        print(f"   ℹ️  Optional questions missing: Q{', Q'.join(str(q) for q in parsed['missing'])}")
    
    # --- Step 2: Score the brand ---
    print("\n📊 Scoring brand dimensions...")
    scoring = score_brand(parsed)
    
    print(f"   Clarity:     {scoring['scores']['clarity']}/10")
    print(f"   Consistency: {scoring['scores']['consistency']}/10")
    print(f"   Visibility:  {scoring['scores']['visibility']}/10")
    print(f"   Total:       {scoring['total']}/30 → {scoring['rag_status']} ({scoring['rag_label']})")
    
    # --- Step 3: Generate content ---
    print("\n✍️  Writing diagnoses and recommendations...")
    answers = parsed["answers"]
    
    diagnoses = write_diagnoses(scoring, answers)
    recommendations = write_recommendations(scoring, answers)
    industry_context = write_industry_context(scoring["industry"])
    
    print(f"   Diagnoses: {len(diagnoses)} dimensions covered")
    print(f"   Recommendations: {len(recommendations)} priorities set")
    
    # --- Step 4: Assemble JSON ---
    print("\n📦 Assembling scoring data...")
    
    audit_date = datetime.now().strftime("%-d %B %Y")
    
    scoring_data = {
        "business_name": scoring["business_name"],
        "industry": scoring["industry"],
        "audit_date": audit_date,
        "scores": scoring["scores"],
        "industry_benchmarks": scoring["industry_benchmarks"],
        "diagnoses": diagnoses,
        "recommendations": recommendations,
        "industry_context": industry_context,
    }
    
    # Save JSON alongside the PDF for reference
    json_path = output_path.replace(".pdf", ".json")
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(scoring_data, f, indent=2, ensure_ascii=False)
    print(f"   JSON saved: {json_path}")
    
    # --- Step 5: Generate PDF ---
    print("\n🎨 Generating branded PDF scorecard...")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    result_path = build_pdf(scoring_data, output_path, chart_dir)
    
    pdf_size = os.path.getsize(result_path)
    print(f"\n✅ Scorecard generated: {result_path} ({pdf_size:,} bytes)")
    
    return result_path, scoring_data


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_audit.py <brief.csv> [output.pdf]")
        print()
        print("Arguments:")
        print("  brief.csv   Path to the client brief CSV (Typeform export)")
        print("  output.pdf  Path for the output PDF (default: output/scorecard.pdf)")
        print()
        print("Example:")
        print("  python run_audit.py sample_briefs/harrow_field_long.csv output/scorecard.pdf")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else "output/scorecard.pdf"
    
    if not os.path.exists(csv_path):
        print(f"❌ Brief not found: {csv_path}")
        sys.exit(1)
    
    run_audit(csv_path, output_path)


if __name__ == "__main__":
    main()
