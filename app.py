import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import tempfile
from run_audit import run_audit

# --- BRAND TOKENS ---
C = {
    "bg":           "#0A0F1E",
    "surface":      "#111827",
    "card":         "#1A2235",
    "card_hover":   "#1E2A42",
    "border":       "rgba(255,255,255,0.07)",
    "primary":      "#6366F1",   # Indigo
    "coral":        "#FF6B6B",   # Brand coral
    "sage":         "#4ECDC4",   # Brand sage/teal
    "amber":        "#FFD93D",   # Brand amber
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "text":         "#F1F5F9",
    "text_muted":   "#64748B",
    "text_dim":     "#334155",
    "glow_indigo":  "rgba(99,102,241,0.15)",
    "glow_coral":   "rgba(255,107,107,0.15)",
    "glow_teal":    "rgba(78,205,196,0.15)",
}

DIM_COLORS = {
    "clarity":     C["coral"],
    "consistency": C["sage"],
    "visibility":  C["amber"],
}

DIM_ICONS = {
    "clarity":     "🎯",
    "consistency": "🔗",
    "visibility":  "📡",
}

def rag_color(score, out_of=30):
    pct = score / out_of
    if pct >= 0.8:  return C["success"], "GREEN", "Strong Foundations"
    if pct >= 0.5:  return C["warning"], "AMBER", "Gaps Identified"
    return C["danger"], "RED", "Urgent Action Needed"

st.set_page_config(
    page_title="The Brand Pulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');

* {{ font-family: 'Inter', sans-serif; }}

.stApp {{
    background: radial-gradient(ellipse at top left, #0D1B3E 0%, {C['bg']} 60%);
    color: {C['text']};
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0D1B3E 0%, {C['surface']} 100%) !important;
    border-right: 1px solid {C['border']};
}}
[data-testid="stSidebar"] .stMarkdown p {{
    color: {C['text_muted']};
}}

/* Metric cards */
div[data-testid="metric-container"] {{
    background: linear-gradient(135deg, {C['card']} 0%, rgba(26,34,53,0.8) 100%);
    padding: 20px 18px;
    border-radius: 16px;
    border: 1px solid {C['border']};
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease;
}}
[data-testid="stMetricValue"] {{
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: {C['text']} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {C['text_muted']} !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    background: transparent;
    border-bottom: 1px solid {C['border']};
    padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    height: 44px;
    background: transparent;
    border-radius: 10px 10px 0 0;
    color: {C['text_muted']};
    padding: 4px 22px;
    font-weight: 500;
    font-size: 0.875rem;
    border: none;
    transition: all 0.2s;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {C['text']};
    background: {C['card']};
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {C['primary']}, #818CF8) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.4);
}}

/* Buttons */
.stButton > button {{
    background: linear-gradient(135deg, {C['primary']}, #818CF8);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 0.875rem;
    width: 100%;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}}
.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.45);
}}

/* Download button */
.stDownloadButton > button {{
    background: linear-gradient(135deg, {C['coral']}, #FF8E53) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: 0 4px 16px rgba(255,107,107,0.35) !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    background: {C['card']};
    border: 1px dashed rgba(99,102,241,0.4);
    border-radius: 12px;
    padding: 8px;
}}

/* Expander */
.streamlit-expanderHeader {{
    background: {C['card']} !important;
    border-radius: 10px !important;
    border: 1px solid {C['border']} !important;
    color: {C['text']} !important;
    font-weight: 500 !important;
}}
.streamlit-expanderContent {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}}

/* Selectbox / Multiselect */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {{
    background: {C['card']} !important;
    border-radius: 8px !important;
}}

/* Info box */
.stAlert {{
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 12px !important;
    color: {C['text']} !important;
}}

/* Divider */
hr {{ border-color: {C['border']} !important; }}

/* Custom components */
.hero-title {{
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #fff 30%, {C['primary']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 0;
}}
.hero-subtitle {{
    color: {C['text_muted']};
    font-size: 0.95rem;
    font-weight: 400;
    letter-spacing: 0.04em;
    margin-top: 4px;
}}
.rag-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}
.metric-label {{
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {C['text_muted']};
    margin-bottom: 2px;
}}
.section-header {{
    font-size: 1rem;
    font-weight: 600;
    color: {C['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid {C['border']};
}}
.diag-card {{
    background: linear-gradient(135deg, {C['card']} 0%, rgba(26,34,53,0.6) 100%);
    padding: 20px;
    border-radius: 14px;
    border: 1px solid {C['border']};
    margin-bottom: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    position: relative;
    overflow: hidden;
}}
.diag-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}}
.rec-card {{
    background: linear-gradient(135deg, {C['card']} 0%, rgba(26,34,53,0.6) 100%);
    padding: 22px;
    border-radius: 14px;
    border: 1px solid {C['border']};
    margin-bottom: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}}
.rec-number {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 700;
    margin-right: 10px;
}}
.stat-pill {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 500;
    background: rgba(255,255,255,0.05);
    border: 1px solid {C['border']};
    color: {C['text_muted']};
    margin-right: 6px;
}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_historical_data():
    if os.path.exists("data/survey_results.csv"):
        return pd.read_csv("data/survey_results.csv")
    return pd.DataFrame()

hist_df = load_historical_data()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 16px 0 8px;">
        <div style="font-size:2.5rem;">⚡</div>
        <div style="font-size:1.1rem; font-weight:700; color:{C['text']}; letter-spacing:0.04em;">Brand Pulse</div>
        <div style="font-size:0.72rem; color:{C['text_muted']}; text-transform:uppercase; letter-spacing:0.1em;">Strategic Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='height:1px; background:{C['border']}; margin:12px 0;'></div>", unsafe_allow_html=True)

    st.markdown(f"<p class='section-header'>New Audit</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Typeform CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is not None:
        if st.button("⚡ Generate Strategic Pulse"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            output_pdf = "output/live_audit.pdf"
            with st.spinner("Analysing brand intelligence..."):
                pdf_path, results = run_audit(tmp_path, output_pdf)
                st.session_state['last_audit'] = results
                st.session_state['last_pdf'] = pdf_path
                st.success("Pulse analysis complete!")
            os.unlink(tmp_path)

    st.markdown(f"<div style='height:1px; background:{C['border']}; margin:16px 0;'></div>", unsafe_allow_html=True)

    if not hist_df.empty:
        st.markdown(f"<p class='section-header'>Historical Data</p>", unsafe_allow_html=True)
        wave = st.selectbox("Audit Wave", sorted(hist_df["wave"].dropna().unique()), label_visibility="visible")
        market = st.multiselect("Industry Sector", sorted(hist_df["market"].dropna().unique()))
        filtered = hist_df.query("wave == @wave").copy()
        if market:
            filtered = filtered[filtered["market"].isin(market)]

        st.markdown(f"""
        <div style="background:{C['card']}; border-radius:10px; border:1px solid {C['border']}; padding:14px; margin-top:12px;">
            <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:{C['text_muted']}; margin-bottom:8px;">Dataset</div>
            <div style="font-size:1.5rem; font-weight:700; color:{C['text']};">{len(filtered)}</div>
            <div style="font-size:0.75rem; color:{C['text_muted']};">audits in view</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        filtered = pd.DataFrame()

# --- DATA SOURCE ---
if 'last_audit' in st.session_state:
    data = st.session_state['last_audit']
    mode = "Live Audit"
    biz_name = data.get('business_name', 'Client')
    score_clarity      = data['scores']['clarity']
    score_consistency  = data['scores']['consistency']
    score_visibility   = data['scores']['visibility']
    total_score = score_clarity + score_consistency + score_visibility
else:
    mode = "Historical Overview"
    biz_name = None
    if not filtered.empty:
        total_score        = filtered["score"].mean()
        score_clarity      = filtered["clarity"].mean()
        score_consistency  = filtered["consistency"].mean()
        score_visibility   = filtered["visibility"].mean()
    else:
        total_score = score_clarity = score_consistency = score_visibility = 0

rag_col, rag_label, rag_desc = rag_color(total_score)

# --- HERO HEADER ---
h_left, h_right = st.columns([2, 1])
with h_left:
    st.markdown(f"""
    <div style="padding: 8px 0 4px;">
        <div class="hero-title">The Brand Pulse</div>
        <div class="hero-subtitle">Strategic Intelligence Dashboard &nbsp;·&nbsp; SME Brand & AI Readiness</div>
    </div>
    """, unsafe_allow_html=True)
with h_right:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center; height:100%; padding-top:12px;">
        <div style="text-align:right;">
            <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:{C['text_muted']}; margin-bottom:4px;">Mode</div>
            <div style="font-size:0.9rem; font-weight:600; color:{C['text']};">{mode}{f' — {biz_name}' if biz_name else ''}</div>
            <div style="margin-top:8px;">
                <span class="rag-badge" style="background:rgba({','.join(str(int(rag_col.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.15); color:{rag_col}; border:1px solid {rag_col}40;">
                    ● {rag_label} &nbsp; {rag_desc}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# --- HERO METRICS ---
k1, k2, k3, k4 = st.columns(4)

def score_color(val, out_of=10):
    pct = val / out_of
    if pct >= 0.8: return C["success"]
    if pct >= 0.5: return C["warning"]
    return C["danger"]

with k1:
    col = rag_col
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{C['card']},rgba(26,34,53,0.7));padding:20px;border-radius:16px;border:1px solid {C['border']};box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.05);">
        <div class="metric-label">Brand Pulse Score</div>
        <div style="font-size:2.4rem;font-weight:800;color:{col};line-height:1.1;">{total_score:.1f}<span style="font-size:1rem;color:{C['text_muted']};font-weight:400;">/30</span></div>
        <div style="margin-top:10px;height:4px;background:{C['border']};border-radius:2px;"><div style="height:4px;background:linear-gradient(90deg,{col},{col}80);border-radius:2px;width:{(total_score/30)*100:.0f}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)

for label, val, dim in [("Clarity Index", score_clarity, "clarity"), ("Consistency", score_consistency, "consistency"), ("Visibility", score_visibility, "visibility")]:
    col_obj = k2 if dim == "clarity" else (k3 if dim == "consistency" else k4)
    dim_c = DIM_COLORS[dim]
    icon = DIM_ICONS[dim]
    with col_obj:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{C['card']},rgba(26,34,53,0.7));padding:20px;border-radius:16px;border:1px solid {C['border']};box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.05);">
            <div class="metric-label">{icon} {label}</div>
            <div style="font-size:2.4rem;font-weight:800;color:{dim_c};line-height:1.1;">{val:.1f}<span style="font-size:1rem;color:{C['text_muted']};font-weight:400;">/10</span></div>
            <div style="margin-top:10px;height:4px;background:{C['border']};border-radius:2px;"><div style="height:4px;background:linear-gradient(90deg,{dim_c},{dim_c}60);border-radius:2px;width:{(val/10)*100:.0f}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["⚡  Strategic Pulse", "📊  Sector Intelligence", "📥  Deliverables"])

# ── TAB 1 ──────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.1, 1])

    with c1:
        # Circular Pulse Ring
        fig = go.Figure()
        dim_colors_list = [C["coral"], C["sage"], C["amber"]]
        dims  = ["Clarity", "Consistency", "Visibility"]
        vals  = [score_clarity, score_consistency, score_visibility]

        for i, (dim, val) in enumerate(zip(dims, vals)):
            fig.add_trace(go.Pie(
                values=[val, 10 - val],
                labels=[dim, ""],
                hole=0.85 - (i * 0.14),
                marker=dict(
                    colors=[dim_colors_list[i], "rgba(255,255,255,0.03)"],
                    line=dict(width=0)
                ),
                textinfo='none',
                hovertemplate=f"<b>{dim}</b><br>Score: {val:.1f}/10<extra></extra>",
                sort=False
            ))

        fig.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            height=380,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(
                text=f"<b>{total_score:.1f}</b>",
                x=0.5, y=0.52,
                font=dict(size=52, color="white", family="Inter"),
                showarrow=False
            ), dict(
                text="/ 30",
                x=0.5, y=0.38,
                font=dict(size=16, color=C["text_muted"], family="Inter"),
                showarrow=False
            )]
        )

        # Legend below ring
        legend_html = "<div style='display:flex;justify-content:center;gap:20px;margin-top:-8px;margin-bottom:16px;'>"
        for dim, val, col_v in zip(dims, vals, dim_colors_list):
            legend_html += f"""
            <div style="text-align:center;">
                <div style="width:28px;height:4px;background:{col_v};border-radius:2px;margin:0 auto 4px;"></div>
                <div style="font-size:0.7rem;color:{C['text_muted']};text-transform:uppercase;letter-spacing:0.06em;">{dim}</div>
                <div style="font-size:1rem;font-weight:700;color:{col_v};">{val:.1f}</div>
            </div>"""
        legend_html += "</div>"

        st.plotly_chart(fig, use_container_width=True)
        st.markdown(legend_html, unsafe_allow_html=True)

        # Radar
        st.markdown(f"<p class='section-header' style='margin-top:8px;'>Dimension Balance</p>", unsafe_allow_html=True)
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[score_clarity, score_consistency, score_visibility, score_clarity],
            theta=["Clarity", "Consistency", "Visibility", "Clarity"],
            fill='toself',
            fillcolor=f"rgba(99,102,241,0.15)",
            line=dict(color=C["primary"], width=2.5),
            marker=dict(color=C["primary"], size=8)
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color=C["text_muted"], size=10), tickvals=[2,4,6,8,10]),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color=C["text"], size=12, family="Inter")),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(t=20, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c2:
        if 'last_audit' in st.session_state:
            st.markdown(f"<p class='section-header'>Strategic Diagnoses</p>", unsafe_allow_html=True)
            for dim in ["clarity", "consistency", "visibility"]:
                diag  = st.session_state['last_audit']['diagnoses'][dim]
                dim_c = DIM_COLORS[dim]
                icon  = DIM_ICONS[dim]
                score_val = st.session_state['last_audit']['scores'][dim]
                st.markdown(f"""
                <div class="diag-card" style="border-left:4px solid {dim_c}; margin-bottom:14px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:1.1rem;">{icon}</span>
                            <span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{dim_c};">{dim}</span>
                        </div>
                        <div style="background:rgba({','.join(str(int(dim_c.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.15);color:{dim_c};padding:3px 10px;border-radius:100px;font-size:0.75rem;font-weight:700;">
                            {score_val}/10
                        </div>
                    </div>
                    <p style="font-size:0.875rem;line-height:1.6;color:{C['text']};margin:0;">{diag}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='section-header'>Top Brand Attributes</p>", unsafe_allow_html=True)
            attr_df = pd.DataFrame({
                "Attribute": ["Positioning", "Problem Statement", "Customer Fit", "Visual Identity", "Brand Voice", "Google Presence", "AI Discoverability"],
                "Score": [score_clarity*0.8, score_clarity*0.9, score_clarity*0.7, score_consistency*0.85, score_consistency*0.75, score_visibility*0.9, score_visibility*0.6],
                "Dimension": ["Clarity","Clarity","Clarity","Consistency","Consistency","Visibility","Visibility"]
            }).sort_values("Score")
            color_map = {"Clarity": C["coral"], "Consistency": C["sage"], "Visibility": C["amber"]}
            fig_attr = go.Figure()
            for dim_name, grp in attr_df.groupby("Dimension"):
                fig_attr.add_trace(go.Bar(
                    y=grp["Attribute"], x=grp["Score"],
                    orientation='h',
                    name=dim_name,
                    marker=dict(color=color_map[dim_name], line=dict(width=0)),
                    hovertemplate="%{y}: %{x:.2f}<extra></extra>"
                ))
            fig_attr.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(t=10,b=10,l=10,r=10),
                legend=dict(font=dict(color=C["text_muted"], size=11), bgcolor='rgba(0,0,0,0)'),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color=C["text_muted"])),
                yaxis=dict(tickfont=dict(color=C["text"], size=12))
            )
            st.plotly_chart(fig_attr, use_container_width=True)

            st.markdown(f"<p class='section-header' style='margin-top:8px;'>Avg. Score Breakdown</p>", unsafe_allow_html=True)
            breakdown_html = ""
            for dim, val in [("Clarity", score_clarity), ("Consistency", score_consistency), ("Visibility", score_visibility)]:
                dim_c = DIM_COLORS[dim.lower()]
                pct = (val / 10) * 100
                breakdown_html += f"""
                <div style="margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                        <span style="font-size:0.8rem;color:{C['text']};font-weight:500;">{DIM_ICONS[dim.lower()]} {dim}</span>
                        <span style="font-size:0.8rem;color:{dim_c};font-weight:700;">{val:.1f}/10</span>
                    </div>
                    <div style="height:6px;background:{C['border']};border-radius:3px;">
                        <div style="height:6px;background:linear-gradient(90deg,{dim_c},{dim_c}80);border-radius:3px;width:{pct:.0f}%;transition:width 0.5s;"></div>
                    </div>
                </div>"""
            st.markdown(breakdown_html, unsafe_allow_html=True)

# ── TAB 2 ──────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if hist_df.empty:
        st.info("No historical data available.")
    else:
        l, r = st.columns(2)
        with l:
            st.markdown(f"<p class='section-header'>Score Distribution by Sector</p>", unsafe_allow_html=True)
            fig_box = px.box(
                hist_df, x="market", y="score", color="market",
                template="plotly_dark",
                color_discrete_sequence=[C["coral"], C["sage"], C["amber"], C["primary"], "#C084FC", "#34D399"]
            )
            fig_box.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["text_muted"])),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["text_muted"])),
                margin=dict(t=10,b=10,l=10,r=10)
            )
            st.plotly_chart(fig_box, use_container_width=True)

        with r:
            st.markdown(f"<p class='section-header'>Clarity vs Visibility (Bubble = Score)</p>", unsafe_allow_html=True)
            fig_scat = px.scatter(
                hist_df, x="clarity", y="visibility",
                size="score", color="consistency",
                template="plotly_dark",
                color_continuous_scale=[[0, C["danger"]], [0.5, C["warning"]], [1, C["success"]]],
                hover_data={"score": True, "market": True},
                labels={"clarity": "Clarity", "visibility": "Visibility", "consistency": "Consistency"}
            )
            fig_scat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["text_muted"])),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["text_muted"])),
                coloraxis_colorbar=dict(tickfont=dict(color=C["text_muted"]), title=dict(font=dict(color=C["text_muted"]))),
                margin=dict(t=10,b=10,l=10,r=10)
            )
            st.plotly_chart(fig_scat, use_container_width=True)

        st.markdown(f"<p class='section-header' style='margin-top:8px;'>Sector Averages</p>", unsafe_allow_html=True)
        sector_avg = hist_df.groupby("market")[["clarity","consistency","visibility","score"]].mean().round(1).reset_index()
        sector_avg.columns = ["Sector","Clarity","Consistency","Visibility","Avg Score"]
        fig_heat = go.Figure(data=go.Heatmap(
            z=sector_avg[["Clarity","Consistency","Visibility"]].values.T,
            x=sector_avg["Sector"],
            y=["Clarity","Consistency","Visibility"],
            colorscale=[[0,"#EF4444"],[0.5,"#F59E0B"],[1,"#22C55E"]],
            text=sector_avg[["Clarity","Consistency","Visibility"]].values.T,
            texttemplate="%{text}",
            textfont=dict(color="white", size=12, family="Inter"),
            hoverongaps=False,
            zmin=0, zmax=10
        ))
        fig_heat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=220,
            margin=dict(t=10,b=10,l=10,r=10),
            xaxis=dict(tickfont=dict(color=C["text"], size=11)),
            yaxis=dict(tickfont=dict(color=C["text"], size=11))
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ── TAB 3 ──────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if 'last_audit' in st.session_state:
        audit = st.session_state['last_audit']
        rec_colors = [C["coral"], C["sage"], C["amber"]]

        d1, d2 = st.columns([1, 1.4])
        with d1:
            st.markdown(f"<p class='section-header'>PDF Scorecard</p>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{C['card']},{C['card_hover']});border-radius:16px;border:1px solid {C['border']};padding:28px;text-align:center;margin-bottom:16px;">
                <div style="font-size:3rem;margin-bottom:12px;">📄</div>
                <div style="font-size:1.1rem;font-weight:700;color:{C['text']};margin-bottom:4px;">{audit['business_name']}</div>
                <div style="font-size:0.8rem;color:{C['text_muted']};margin-bottom:16px;">Brand Pulse Scorecard · {audit.get('audit_date','')}</div>
                <div style="display:flex;justify-content:center;gap:16px;margin-bottom:20px;">
                    <div style="text-align:center;"><div style="font-size:1.4rem;font-weight:800;color:{C['coral']};">{audit['scores']['clarity']}</div><div style="font-size:0.65rem;text-transform:uppercase;color:{C['text_muted']};">Clarity</div></div>
                    <div style="text-align:center;"><div style="font-size:1.4rem;font-weight:800;color:{C['sage']};">{audit['scores']['consistency']}</div><div style="font-size:0.65rem;text-transform:uppercase;color:{C['text_muted']};">Consistency</div></div>
                    <div style="text-align:center;"><div style="font-size:1.4rem;font-weight:800;color:{C['amber']};">{audit['scores']['visibility']}</div><div style="font-size:0.65rem;text-transform:uppercase;color:{C['text_muted']};">Visibility</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            with open(st.session_state['last_pdf'], "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Branded PDF Scorecard",
                data=pdf_bytes,
                file_name=f"BrandPulse_{audit['business_name'].replace(' ','_')}.pdf",
                mime="application/pdf"
            )

        with d2:
            st.markdown(f"<p class='section-header'>Priority Recommendations</p>", unsafe_allow_html=True)
            for i, rec in enumerate(audit['recommendations']):
                rc = rec_colors[i % len(rec_colors)]
                st.markdown(f"""
                <div class="rec-card" style="border-top:3px solid {rc};">
                    <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:12px;">
                        <span class="rec-number" style="background:rgba({','.join(str(int(rc.lstrip('#')[j:j+2],16)) for j in (0,2,4))},0.2);color:{rc};flex-shrink:0;">#{i+1}</span>
                        <div style="font-size:0.95rem;font-weight:700;color:{C['text']};line-height:1.3;">{rec['title']}</div>
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;">
                        <span class="stat-pill">⏱ {rec['timeframe']}</span>
                        <span class="stat-pill">💷 {rec['effort']}</span>
                    </div>
                    <p style="font-size:0.85rem;line-height:1.6;color:{C['text_muted']};margin:0;">{rec['detail']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center;padding:60px 20px;background:{C['card']};border-radius:16px;border:1px dashed rgba(99,102,241,0.3);">
            <div style="font-size:3rem;margin-bottom:16px;">⚡</div>
            <div style="font-size:1.1rem;font-weight:600;color:{C['text']};margin-bottom:8px;">No audit yet</div>
            <div style="font-size:0.875rem;color:{C['text_muted']};">Upload a Typeform CSV brief in the sidebar to generate a scorecard and download the PDF.</div>
        </div>
        """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown(f"""
<div style="margin-top:40px;padding:20px 0;border-top:1px solid {C['border']};display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:0.75rem;color:{C['text_dim']};">⚡ The Brand Pulse &nbsp;·&nbsp; Strategic Intelligence for SMEs</span>
    <span style="font-size:0.75rem;color:{C['text_dim']};">v2.0 &nbsp;·&nbsp; © 2026</span>
</div>
""", unsafe_allow_html=True)
