# The Brand Pulse

**Strategic Intelligence for SMEs.** 

The Brand Pulse is an automated brand audit pipeline and interactive dashboard. It transforms raw client brief answers into a high-fidelity 4-page branded PDF scorecard and provides real-time analytics for brand consultants and business owners.

## 🚀 Key Features

- **⚡ Interactive Dashboard**: A "Clean Pulse" Streamlit application for real-time brand auditing and sector analytics.
- **📑 Branded PDF Deliverables**: Automated generation of 4-page strategic PDF scorecards with professional charts.
- **🔍 Strategic Scoring**: Rule-based evaluation of **Clarity**, **Consistency**, and **Visibility**.
- **🧠 Automated Strategist**: Dynamic generation of diagnoses and ARR-calibrated recommendations.
- **📊 Sector Intel**: Compare brand performance against a database of industry benchmarks.

## 🛠️ Installation

### Prerequisites
- Python 3.9+

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

## 🕹️ Usage

### 📊 Option 1: Interactive Dashboard (Recommended)
Launch the web interface to upload briefs, visualize results, and download PDFs:
```bash
streamlit run app.py
```

### ⚙️ Option 2: Command Line Auditor
Generate a scorecard directly from a CSV brief:
```bash
python3 run_audit.py <path_to_brief.csv> <output_path.pdf>
```

## 📁 Directory Structure

- `app.py`: The interactive Streamlit dashboard.
- `run_audit.py`: The core pipeline orchestrator.
- `scripts/`: Modular logic for parsing, scoring, content, and PDF production.
- `data/`: Historical audit data and benchmarks.
- `sample_briefs/`: Example client briefs (Typeform exports).
- `output/`: Automated storage for generated PDFs and JSON data.

## 📜 Project History
For a detailed look at the development stages and technical implementations, see [PROJECT_HISTORY.md](./PROJECT_HISTORY.md).

---
© 2026 The Brand Pulse • Strategic Intelligence for SMEs
