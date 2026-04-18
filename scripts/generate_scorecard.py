"""
Brand Pulse Scorecard - PDF Generator

Takes a scoring dict and produces a branded PDF scorecard with:
  1. RAG traffic-light summary dial
  2. Three dimension bar charts
  3. Radar chart across the 3 dimensions
  4. Benchmark comparison vs industry average
  5. Priority roadmap visual for the 3 recommendations

Usage:
    python generate_scorecard.py <input.json> <output.pdf>

Input JSON schema:
{
  "business_name": str,
  "industry": str,
  "audit_date": str (YYYY-MM-DD),
  "scores": {
    "clarity": int (0-10),
    "consistency": int (0-10),
    "visibility": int (0-10)
  },
  "industry_benchmarks": {
    "clarity": float,
    "consistency": float,
    "visibility": float
  },
  "diagnoses": {
    "clarity": str,
    "consistency": str,
    "visibility": str
  },
  "recommendations": [
    {"title": str, "detail": str, "timeframe": str, "effort": str}
  ],
  "industry_context": str
}
"""
import os
import sys
import json
import math
from datetime import datetime

import warnings
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Wedge, Circle
import matplotlib.patheffects as pe
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------- BRAND TOKENS ----------
INK = "#1A1A1A"
PAPER = "#FAF7F2"
CORAL = "#FF6B5B"
AMBER = "#F5B73C"
SAGE = "#7FB685"
MIST = "#E8E4DC"
INK_SOFT = "#4A4A4A"

# Font registration - tries DM Sans + Figtree first, falls back to Poppins,
# then to Helvetica. The skill instructions include where to place these fonts.
FONT_CANDIDATES = {
    "heading": [
        ("Figtree", "/home/claude/fonts/Figtree-Bold.ttf"),
        ("Figtree", "/usr/share/fonts/truetype/google-fonts/Figtree-Bold.ttf"),
        ("Poppins-Bold", "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"),
    ],
    "heading_regular": [
        ("Figtree-Regular", "/home/claude/fonts/Figtree-Regular.ttf"),
        ("Figtree-Regular", "/usr/share/fonts/truetype/google-fonts/Figtree-Regular.ttf"),
        ("Poppins-Medium", "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"),
    ],
    "body": [
        ("DMSans", "/home/claude/fonts/DMSans-Regular.ttf"),
        ("DMSans", "/usr/share/fonts/truetype/google-fonts/DMSans-Regular.ttf"),
        ("Poppins", "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"),
    ],
    "body_light": [
        ("DMSans-Light", "/home/claude/fonts/DMSans-Light.ttf"),
        ("Poppins-Light", "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf"),
    ],
}

FONTS = {}
def register_fonts():
    for role, candidates in FONT_CANDIDATES.items():
        for name, path in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    FONTS[role] = name
                    break
                except Exception:
                    continue
        if role not in FONTS:
            FONTS[role] = "Helvetica-Bold" if "heading" in role else "Helvetica"
    return FONTS

# ---------- RAG CLASSIFICATION ----------
def rag_status(total):
    if total >= 24: return "GREEN", SAGE, "Strong foundations"
    if total >= 15: return "AMBER", AMBER, "Gaps identified"
    return "RED", CORAL, "Urgent action needed"

def dimension_rag(score):
    if score >= 8: return SAGE
    if score >= 5: return AMBER
    return CORAL

# ---------- CHART GENERATORS ----------
def _setup_mpl():
    # Try to make matplotlib use a similar font to the PDF body.
    for candidate in ["DM Sans", "Figtree", "Poppins", "DejaVu Sans"]:
        try:
            plt.rcParams["font.family"] = candidate
            break
        except Exception:
            continue
    plt.rcParams["axes.edgecolor"] = INK
    plt.rcParams["axes.labelcolor"] = INK
    plt.rcParams["xtick.color"] = INK_SOFT
    plt.rcParams["ytick.color"] = INK_SOFT

def chart_rag_dial(total, out_path):
    _setup_mpl()
    fig, ax = plt.subplots(figsize=(4.6, 2.8), dpi=200)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_aspect("equal")
    # Half-donut: Red 0-14, Amber 15-23, Green 24-30
    # Angles: 180° at left, 0° at right. 30 units maps to 180°.
    def val_to_angle(v):
        return 180 - (v / 30) * 180
    # Draw arcs
    for start_v, end_v, color in [(0, 14, CORAL), (14, 23, AMBER), (23, 30, SAGE)]:
        theta2 = val_to_angle(start_v)
        theta1 = val_to_angle(end_v)
        wedge = Wedge((0, 0), 1.0, theta1, theta2, width=0.28,
                      facecolor=color, edgecolor=PAPER, linewidth=2)
        ax.add_patch(wedge)
    # Needle
    needle_angle_deg = val_to_angle(total)
    needle_angle_rad = math.radians(needle_angle_deg)
    nx = 0.78 * math.cos(needle_angle_rad)
    ny = 0.78 * math.sin(needle_angle_rad)
    ax.plot([0, nx], [0, ny], color=INK, linewidth=3, solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 0.06, facecolor=INK, zorder=5))
    # Total number
    ax.text(0, -0.28, f"{total}", ha="center", va="center",
            fontsize=38, fontweight="bold", color=INK)
    ax.text(0, -0.48, "out of 30", ha="center", va="center",
            fontsize=10, color=INK_SOFT)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.15)
    ax.axis("off")
    plt.tight_layout(pad=0.1)
    plt.savefig(out_path, facecolor=PAPER, bbox_inches="tight", dpi=200)
    plt.close()

def chart_dimension_bars(scores, out_path):
    _setup_mpl()
    fig, ax = plt.subplots(figsize=(6.5, 2.6), dpi=200)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    labels = ["Clarity", "Consistency", "Visibility"]
    values = [scores["clarity"], scores["consistency"], scores["visibility"]]
    colors = [dimension_rag(v) for v in values]
    y_pos = np.arange(len(labels))
    # Background track
    ax.barh(y_pos, [10]*3, color=MIST, height=0.55, zorder=1)
    bars = ax.barh(y_pos, values, color=colors, height=0.55, zorder=2)
    for i, (v, bar) in enumerate(zip(values, bars)):
        # Value label inside or right of bar
        if v >= 1.5:
            ax.text(v - 0.3, i, f"{v}/10", va="center", ha="right",
                    color=PAPER, fontsize=11, fontweight="bold")
        else:
            ax.text(v + 0.3, i, f"{v}/10", va="center", ha="left",
                    color=INK, fontsize=11, fontweight="bold")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=12, color=INK)
    ax.set_xlim(0, 10)
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.tick_params(axis="x", labelsize=9)
    ax.invert_yaxis()
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", color=MIST, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout(pad=0.2)
    plt.savefig(out_path, facecolor=PAPER, bbox_inches="tight", dpi=200)
    plt.close()

def chart_radar(scores, benchmarks, out_path):
    _setup_mpl()
    categories = ["Clarity", "Consistency", "Visibility"]
    client_vals = [scores["clarity"], scores["consistency"], scores["visibility"]]
    bench_vals = [benchmarks["clarity"], benchmarks["consistency"], benchmarks["visibility"]]
    angles = [n / 3 * 2 * math.pi for n in range(3)]
    angles += angles[:1]
    client_vals_c = client_vals + client_vals[:1]
    bench_vals_c = bench_vals + bench_vals[:1]

    fig, ax = plt.subplots(figsize=(4.8, 4.8), dpi=200,
                            subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(0)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], color=INK_SOFT, fontsize=8)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11, color=INK)
    ax.grid(color=MIST, linewidth=0.8)
    ax.spines['polar'].set_color(MIST)
    # Industry benchmark (dashed)
    ax.plot(angles, bench_vals_c, color=INK_SOFT, linewidth=1.4,
            linestyle="--", label="Industry average")
    ax.fill(angles, bench_vals_c, color=INK_SOFT, alpha=0.08)
    # Client (solid)
    ax.plot(angles, client_vals_c, color=CORAL, linewidth=2.2,
            label="Your business")
    ax.fill(angles, client_vals_c, color=CORAL, alpha=0.22)
    # Legend
    legend = ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.12),
                        frameon=False, fontsize=9, ncol=2)
    for text in legend.get_texts():
        text.set_color(INK)
    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, facecolor=PAPER, bbox_inches="tight", dpi=200)
    plt.close()

def chart_benchmark_comparison(scores, benchmarks, out_path):
    _setup_mpl()
    fig, ax = plt.subplots(figsize=(6.5, 2.6), dpi=200)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    labels = ["Clarity", "Consistency", "Visibility"]
    client = [scores["clarity"], scores["consistency"], scores["visibility"]]
    bench = [benchmarks["clarity"], benchmarks["consistency"], benchmarks["visibility"]]
    x = np.arange(len(labels))
    w = 0.36
    b1 = ax.bar(x - w/2, client, w, color=CORAL, label="Your score", zorder=2)
    b2 = ax.bar(x + w/2, bench, w, color=INK_SOFT, alpha=0.55,
                label="Industry average", zorder=2)
    for rect in list(b1) + list(b2):
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2, h + 0.18, f"{h:.1f}",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11, color=INK)
    ax.set_ylim(0, 10.8)
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.tick_params(axis="y", labelsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(MIST)
    ax.spines["bottom"].set_color(MIST)
    ax.grid(axis="y", color=MIST, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, fontsize=9, loc="upper right")
    for text in legend.get_texts():
        text.set_color(INK)
    plt.tight_layout(pad=0.2)
    plt.savefig(out_path, facecolor=PAPER, bbox_inches="tight", dpi=200)
    plt.close()

def chart_roadmap(recommendations, out_path):
    """Horizontal roadmap with three numbered priorities."""
    _setup_mpl()
    fig, ax = plt.subplots(figsize=(6.8, 2.4), dpi=200)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    # Draw baseline
    ax.plot([0.6, 9.4], [2, 2], color=MIST, linewidth=3, zorder=1)
    # Three nodes
    positions = [1.5, 5.0, 8.5]
    colors = [CORAL, AMBER, SAGE]

    def wrap_by_chars(text, max_chars=22):
        """Word-aware wrap so labels don't overrun."""
        words = text.split()
        lines, line = [], ""
        for w in words:
            trial = (line + " " + w).strip()
            if len(trial) <= max_chars:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        # Cap at 2 lines; ellipsis if more
        if len(lines) > 2:
            lines = lines[:2]
            if len(lines[1]) > max_chars - 1:
                lines[1] = lines[1][:max_chars-1]
            lines[1] = lines[1] + "…"
        return "\n".join(lines)

    for i, (x, color, rec) in enumerate(zip(positions, colors, recommendations)):
        ax.add_patch(Circle((x, 2), 0.42, facecolor=color,
                             edgecolor=PAPER, linewidth=3, zorder=3))
        ax.text(x, 2, str(i+1), ha="center", va="center",
                fontsize=18, fontweight="bold", color=PAPER, zorder=4)
        # Label above (wrapped + centred, positioned further from node)
        label = wrap_by_chars(rec["title"], max_chars=22)
        ax.text(x, 3.3, label, ha="center", va="center",
                fontsize=9, color=INK, fontweight="bold",
                linespacing=1.25)
        # Timeframe below
        ax.text(x, 1.2, rec.get("timeframe", ""), ha="center", va="top",
                fontsize=8.5, color=INK_SOFT, style="italic")
    ax.axis("off")
    plt.tight_layout(pad=0.1)
    plt.savefig(out_path, facecolor=PAPER, bbox_inches="tight", dpi=200)
    plt.close()

# ---------- PDF LAYOUT ----------
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

def draw_text(c, text, x, y, font, size, color=INK, align="left"):
    c.setFont(font, size)
    c.setFillColor(HexColor(color))
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)

def draw_wrapped(c, text, x, y, width, font, size, color=INK, leading=None):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    if leading is None:
        leading = size * 1.35
    c.setFont(font, size)
    c.setFillColor(HexColor(color))
    words = text.split()
    line = ""
    cursor_y = y
    for word in words:
        trial = (line + " " + word).strip()
        if stringWidth(trial, font, size) <= width:
            line = trial
        else:
            c.drawString(x, cursor_y, line)
            cursor_y -= leading
            line = word
    if line:
        c.drawString(x, cursor_y, line)
        cursor_y -= leading
    return cursor_y  # y after last baseline

def measure_wrapped(text, width, font, size, leading=None):
    """Return (num_lines, total_height) for text wrapped at `width`."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    if leading is None:
        leading = size * 1.35
    words = text.split()
    if not words:
        return 0, 0
    line = ""
    lines = 0
    for word in words:
        trial = (line + " " + word).strip()
        if stringWidth(trial, font, size) <= width:
            line = trial
        else:
            lines += 1
            line = word
    if line:
        lines += 1
    return lines, lines * leading

def truncate_to_width(text, width, font, size, ellipsis="…"):
    """Hard-truncate a single line to fit in width, adding ellipsis if cut."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    if stringWidth(text, font, size) <= width:
        return text
    # Binary-search the longest prefix that fits with ellipsis
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if stringWidth(text[:mid] + ellipsis, font, size) <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis

def draw_divider(c, y, x1=MARGIN, x2=PAGE_W-MARGIN, color=MIST):
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(0.6)
    c.line(x1, y, x2, y)

def draw_rounded_box(c, x, y, w, h, fill=None, stroke=None, radius=4*mm):
    if fill:
        c.setFillColor(HexColor(fill))
    if stroke:
        c.setStrokeColor(HexColor(stroke))
    c.roundRect(x, y, w, h, radius, stroke=1 if stroke else 0,
                fill=1 if fill else 0)

def draw_pill(c, text, x, y, color, font, size=8):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    pad_x = 3 * mm
    pad_y = 1.5 * mm
    text_w = stringWidth(text, font, size)
    w = text_w + 2 * pad_x
    h = size + 2 * pad_y
    c.setFillColor(HexColor(color))
    c.roundRect(x, y, w, h, h/2, stroke=0, fill=1)
    c.setFillColor(HexColor(PAPER))
    c.setFont(font, size)
    c.drawString(x + pad_x, y + pad_y + 1, text)
    return w

# ---------- MAIN PDF BUILD ----------
def build_pdf(data, out_path, chart_dir):
    register_fonts()
    H = FONTS["heading"]
    HR = FONTS["heading_regular"]
    B = FONTS["body"]

    # Generate charts
    os.makedirs(chart_dir, exist_ok=True)
    scores = data["scores"]
    total = scores["clarity"] + scores["consistency"] + scores["visibility"]
    status_name, status_color, status_label = rag_status(total)
    benchmarks = data["industry_benchmarks"]

    dial_path = os.path.join(chart_dir, "dial.png")
    bars_path = os.path.join(chart_dir, "bars.png")
    radar_path = os.path.join(chart_dir, "radar.png")
    bench_path = os.path.join(chart_dir, "bench.png")
    roadmap_path = os.path.join(chart_dir, "roadmap.png")
    chart_rag_dial(total, dial_path)
    chart_dimension_bars(scores, bars_path)
    chart_radar(scores, benchmarks, radar_path)
    chart_benchmark_comparison(scores, benchmarks, bench_path)
    chart_roadmap(data["recommendations"], roadmap_path)

    c = canvas.Canvas(out_path, pagesize=A4)
    # --- Background ---
    def page_bg():
        c.setFillColor(HexColor(PAPER))
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    def page_footer(page_num):
        c.setStrokeColor(HexColor(MIST))
        c.setLineWidth(0.5)
        c.line(MARGIN, 15*mm, PAGE_W-MARGIN, 15*mm)
        draw_text(c, "The Brand Pulse", MARGIN, 10*mm, H, 8, INK)
        draw_text(c, f"Scorecard for {data['business_name']}",
                  PAGE_W/2, 10*mm, B, 8, INK_SOFT, align="center")
        draw_text(c, f"Page {page_num}", PAGE_W-MARGIN, 10*mm,
                  B, 8, INK_SOFT, align="right")

    # ========== PAGE 1: COVER + HEADLINE ==========
    page_bg()
    # Top bar
    c.setFillColor(HexColor(INK))
    c.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, stroke=0, fill=1)
    c.setFillColor(HexColor(CORAL))
    c.rect(0, PAGE_H - 8*mm, 40*mm, 8*mm, stroke=0, fill=1)

    # Wordmark
    y = PAGE_H - 30*mm
    draw_text(c, "THE BRAND PULSE", MARGIN, y, H, 11, INK_SOFT)

    y -= 18*mm
    draw_text(c, "Brand & AI Readiness", MARGIN, y, H, 28, INK)
    y -= 10*mm
    draw_text(c, "Scorecard", MARGIN, y, H, 28, CORAL)

    # Business meta card — 2-col layout to give business name full width
    y -= 22*mm
    meta_h = 24*mm
    draw_rounded_box(c, MARGIN, y - meta_h, PAGE_W - 2*MARGIN, meta_h,
                      fill=None, stroke=MIST)
    # Row 1: Business name (full width)
    draw_text(c, "BUSINESS", MARGIN + 5*mm, y - 6*mm, H, 7.5, INK_SOFT)
    biz_name = truncate_to_width(data["business_name"],
                                  PAGE_W - 2*MARGIN - 10*mm, H, 13)
    draw_text(c, biz_name, MARGIN + 5*mm, y - 11*mm, H, 13, INK)
    # Row 2: Industry + Audited (split 65/35)
    row2_y = y - 17*mm
    ind_w = (PAGE_W - 2*MARGIN) * 0.65
    draw_text(c, "INDUSTRY", MARGIN + 5*mm, row2_y, H, 7.5, INK_SOFT)
    industry = truncate_to_width(data["industry"],
                                  ind_w - 5*mm, B, 10)
    draw_text(c, industry, MARGIN + 5*mm, row2_y - 4.5*mm, B, 10, INK)
    aud_x = MARGIN + ind_w + 5*mm
    draw_text(c, "AUDITED", aud_x, row2_y, H, 7.5, INK_SOFT)
    draw_text(c, data["audit_date"], aud_x, row2_y - 4.5*mm, B, 10, INK)

    # RAG Dial + headline
    y -= (meta_h + 10*mm)
    dial_w = 85*mm
    dial_h = 52*mm
    c.drawImage(dial_path, MARGIN, y - dial_h, width=dial_w, height=dial_h,
                preserveAspectRatio=True, mask="auto")

    # Headline on right
    right_x = MARGIN + dial_w + 8*mm
    right_w = PAGE_W - right_x - MARGIN
    draw_text(c, "OVERALL STATUS", right_x, y - 5*mm, H, 8, INK_SOFT)
    # Big pill
    pill_y = y - 16*mm
    c.setFillColor(HexColor(status_color))
    c.roundRect(right_x, pill_y, 38*mm, 9*mm, 4.5*mm, stroke=0, fill=1)
    draw_text(c, status_name, right_x + 19*mm, pill_y + 2.5*mm,
              H, 12, PAPER, align="center")
    # Status description
    desc = {
        "GREEN": "Your brand has strong foundations. Sharpening a few edges will turn good into great.",
        "AMBER": "Your brand has real strengths but also real gaps. The priorities in this report will close them.",
        "RED": "Right now your brand is working against you. The good news: the fixes are clear and achievable.",
    }[status_name]
    draw_wrapped(c, desc, right_x, pill_y - 5*mm, right_w, B, 11, INK, leading=15)

    # Dimension bars section
    y -= (dial_h + 8*mm)
    draw_text(c, "Your scores at a glance", MARGIN, y, H, 14, INK)
    y -= 3*mm
    bars_h = 45*mm
    c.drawImage(bars_path, MARGIN, y - bars_h, width=PAGE_W - 2*MARGIN,
                height=bars_h, preserveAspectRatio=True, mask="auto")
    y -= (bars_h + 6*mm)

    # What's inside card (fills bottom space meaningfully)
    inside_h = 38*mm
    draw_rounded_box(c, MARGIN, y - inside_h, PAGE_W - 2*MARGIN, inside_h,
                      fill=INK, stroke=None, radius=4*mm)
    inner_x = MARGIN + 8*mm
    draw_text(c, "WHAT'S INSIDE", inner_x, y - 8*mm, H, 8, CORAL)
    # 3 bullets in a row
    bullet_items = [
        ("01", "What the scores mean",
         "A plain-English read of each of the three dimensions."),
        ("02", "How you compare",
         "Where you sit against the typical business in your sector."),
        ("03", "Your top 3 priorities",
         "Ordered by impact and calibrated for a business your size."),
    ]
    col_w = (PAGE_W - 2*MARGIN - 16*mm) / 3
    for i, (num, title, body) in enumerate(bullet_items):
        cx = inner_x + i * col_w
        draw_text(c, num, cx, y - 16*mm, H, 11, CORAL)
        draw_text(c, title, cx, y - 21*mm, H, 10, PAPER)
        draw_wrapped(c, body, cx, y - 25.5*mm, col_w - 4*mm,
                     B, 8.5, "#C9C4BC", leading=11)

    page_footer(1)
    c.showPage()

    # ========== PAGE 2: DIMENSION DIAGNOSES ==========
    page_bg()
    y = PAGE_H - 25*mm
    draw_text(c, "What the scores mean", MARGIN, y, H, 20, INK)
    y -= 7*mm
    draw_text(c, "A plain-English read of where you stand across the three dimensions.",
              MARGIN, y, B, 10, INK_SOFT)
    y -= 10*mm

    from reportlab.pdfbase.pdfmetrics import stringWidth

    for dim_key, dim_label in [
        ("clarity", "Brand Clarity"),
        ("consistency", "Brand Consistency"),
        ("visibility", "Brand Visibility"),
    ]:
        score = scores[dim_key]
        color = dimension_rag(score)
        diagnosis = data["diagnoses"][dim_key]

        # Dynamic card height based on diagnosis length
        score_box_w = 28*mm
        cx = MARGIN + score_box_w + 6*mm
        cw = PAGE_W - MARGIN - cx - 5*mm
        _, diag_h = measure_wrapped(diagnosis, cw, B, 10, leading=14)
        # title area (14mm) + diag + bottom padding
        box_h = max(38*mm, 14*mm + diag_h + 6*mm)

        # Card
        draw_rounded_box(c, MARGIN, y - box_h, PAGE_W - 2*MARGIN, box_h,
                          fill=None, stroke=MIST)
        # Left score block
        c.setFillColor(HexColor(color))
        c.roundRect(MARGIN, y - box_h, score_box_w, box_h, 4*mm,
                     stroke=0, fill=1)
        # Mask right side to make it a flat "left tab"
        c.setFillColor(HexColor(color))
        c.rect(MARGIN + score_box_w - 4*mm, y - box_h + 0.5*mm,
                4*mm, box_h - 1*mm, stroke=0, fill=1)
        # Score number vertically centred on card
        num_y = y - box_h/2 + 3*mm
        draw_text(c, str(score), MARGIN + score_box_w/2, num_y,
                   H, 30, PAPER, align="center")
        draw_text(c, "out of 10", MARGIN + score_box_w/2, num_y - 6*mm,
                   B, 8, PAPER, align="center")
        # Right content — pill placed AFTER title based on actual width
        title_y = y - 9*mm
        draw_text(c, dim_label, cx, title_y, H, 13, INK)
        title_w = stringWidth(dim_label, H, 13)
        rag_text = {SAGE: "GREEN", AMBER: "AMBER", CORAL: "RED"}[color]
        draw_pill(c, rag_text, cx + title_w + 4*mm, title_y - 1.5*mm,
                   color, H, size=7)
        # Diagnosis text
        draw_wrapped(c, diagnosis, cx, y - 16*mm, cw,
                     B, 10, INK_SOFT, leading=14)
        y -= (box_h + 6*mm)

    page_footer(2)
    c.showPage()

    # ========== PAGE 3: HOW YOU COMPARE ==========
    page_bg()
    y = PAGE_H - 25*mm
    draw_text(c, "How you compare", MARGIN, y, H, 20, INK)
    y -= 7*mm
    draw_text(c,
              "Two views of the same data. The shape on the left shows your brand's",
              MARGIN, y, B, 10, INK_SOFT)
    y -= 4.5*mm
    draw_text(c,
              "balance; the bars on the right show you against the typical business in your sector.",
              MARGIN, y, B, 10, INK_SOFT)
    y -= 12*mm

    # Radar left, benchmark bars right — roomier now with a whole page
    chart_h = 85*mm
    half_w = (PAGE_W - 2*MARGIN - 6*mm) / 2
    c.drawImage(radar_path, MARGIN, y - chart_h,
                 width=half_w, height=chart_h,
                 preserveAspectRatio=True, mask="auto")
    c.drawImage(bench_path, MARGIN + half_w + 6*mm, y - chart_h,
                 width=half_w, height=chart_h,
                 preserveAspectRatio=True, mask="auto")
    y -= (chart_h + 12*mm)

    # How to read this box
    hint_h = 42*mm
    draw_rounded_box(c, MARGIN, y - hint_h, PAGE_W - 2*MARGIN, hint_h,
                      fill=None, stroke=MIST)
    draw_text(c, "HOW TO READ THIS", MARGIN + 6*mm, y - 7*mm, H, 8, CORAL)
    hint_text = (
        "The radar chart shows the shape of your brand. A balanced triangle means "
        "you're developing all three dimensions evenly; a lopsided one means you've "
        "invested heavily in some areas and let others slide. The bars on the right "
        "tell you whether you're keeping pace with the rest of your sector — any "
        "coral bar shorter than its grey counterpart is a gap worth closing."
    )
    draw_wrapped(c, hint_text, MARGIN + 6*mm, y - 13*mm,
                 PAGE_W - 2*MARGIN - 12*mm, B, 9.5, INK, leading=13)

    page_footer(3)
    c.showPage()

    # ========== PAGE 4: RECOMMENDATIONS + ROADMAP ==========
    page_bg()
    y = PAGE_H - 25*mm
    draw_text(c, "Your top 3 priorities", MARGIN, y, H, 20, INK)
    y -= 7*mm
    draw_text(c,
              "Ordered by impact, calibrated for a business your size. Start with #1.",
              MARGIN, y, B, 10, INK_SOFT)

    # Roadmap visual
    y -= 8*mm
    roadmap_h = 38*mm
    c.drawImage(roadmap_path, MARGIN, y - roadmap_h,
                 width=PAGE_W - 2*MARGIN, height=roadmap_h,
                 preserveAspectRatio=True, mask="auto")
    y -= (roadmap_h + 6*mm)

    # Detail cards for each rec — dynamic heights
    priority_colors = [CORAL, AMBER, SAGE]
    # Reserve space for footer
    FOOTER_RESERVE = 22*mm

    for i, rec in enumerate(data["recommendations"]):
        # Measure detail text
        content_x = MARGIN + 20*mm
        content_w = PAGE_W - MARGIN - content_x - 5*mm
        _, detail_h = measure_wrapped(rec["detail"], content_w, B, 9.5, leading=13)
        # title(8mm) + meta(5mm) + gap(3mm) + detail + bottom pad(5mm)
        box_h = max(30*mm, 8*mm + 5*mm + 3*mm + detail_h + 5*mm)

        # If this card would run into the footer area, break to new page
        if y - box_h < FOOTER_RESERVE:
            page_footer(4)
            c.showPage()
            page_bg()
            y = PAGE_H - 25*mm

        # Card
        draw_rounded_box(c, MARGIN, y - box_h, PAGE_W - 2*MARGIN, box_h,
                          fill=None, stroke=MIST)
        # Number circle
        num_x = MARGIN + 9*mm
        num_y = y - 11*mm
        c.setFillColor(HexColor(priority_colors[i]))
        c.circle(num_x, num_y, 6*mm, stroke=0, fill=1)
        draw_text(c, str(i+1), num_x, num_y - 2.5*mm, H, 16, PAPER, align="center")
        # Title (truncate hard if absurdly long)
        title = truncate_to_width(rec["title"], content_w, H, 12)
        draw_text(c, title, content_x, y - 9*mm, H, 12, INK)
        # Meta row
        meta_y = y - 14*mm
        draw_text(c, f"TIMEFRAME   {rec.get('timeframe', '—')}",
                  content_x, meta_y, H, 7.5, INK_SOFT)
        draw_text(c, f"EFFORT   {rec.get('effort', '—')}",
                  MARGIN + 80*mm, meta_y, H, 7.5, INK_SOFT)
        # Detail
        draw_wrapped(c, rec["detail"],
                     content_x, y - 20*mm, content_w,
                     B, 9.5, INK, leading=13)
        y -= (box_h + 4*mm)

    # Industry context box — measure and paginate if needed
    ctx_inner_w = PAGE_W - 2*MARGIN - 12*mm
    _, ctx_text_h = measure_wrapped(data["industry_context"],
                                     ctx_inner_w, B, 10, leading=14)
    ctx_h = ctx_text_h + 16*mm  # label area + padding

    if y - ctx_h - 2*mm < FOOTER_RESERVE:
        page_footer(4)
        c.showPage()
        page_bg()
        y = PAGE_H - 25*mm

    y -= 2*mm
    draw_rounded_box(c, MARGIN, y - ctx_h, PAGE_W - 2*MARGIN, ctx_h,
                      fill=INK, stroke=None)
    draw_text(c, "INDUSTRY CONTEXT", MARGIN + 6*mm, y - 7*mm, H, 8, CORAL)
    draw_wrapped(c, data["industry_context"],
                 MARGIN + 6*mm, y - 13*mm, ctx_inner_w,
                 B, 10, PAPER, leading=14)

    page_footer(4)
    c.showPage()
    c.save()
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_scorecard.py <input.json> <output.pdf>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    build_pdf(data, sys.argv[2], "/tmp/bp_charts")
    print(f"Wrote {sys.argv[2]}")
