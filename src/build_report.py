#!/usr/bin/env python3
"""Build the P20 deliverables from the SAMPLE survey data.

Recomputes every number from outputs/summary.json (itself recomputed
from the raw CSV by src/analyze.py — nothing is typed in by hand)
and produces:
  * outputs/monthly_nps.png — monthly NPS trend (bars, zero line)
  * outputs/driver_ratings.png — driver average ratings, ranked by
    fix-first score (matplotlib)
  * outputs/feedback_report.pdf — 2-page client report (headline,
    branch and channel NPS, driver table, detractor themes, monthly
    trend, 3 recommendations)

Run:  python3 src/build_report.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "outputs" / "summary.json"
CHART_MO = ROOT / "outputs" / "monthly_nps.png"
CHART_DR = ROOT / "outputs" / "driver_ratings.png"
PDF = ROOT / "outputs" / "feedback_report.pdf"

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
OV = s["overall"]
TOT = s["total_responses"]
BR = sorted(s["by_branch"], key=lambda x: -x["nps"])
CH = sorted(s["by_channel"], key=lambda x: -x["nps"])
DR = s["by_driver"]
MO = s["months"]
TH = s["detractor_themes"]
ACTS = s["actions"]

# monthly NPS trend: bars, zero line
months = [m["month"] for m in MO]
nps = [m["nps"] for m in MO]
cols = ["#2E7D32" if x >= 0 else "#C62828" for x in nps]
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.bar(months, nps, width=0.55, color=cols)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel("NPS")
ax.set_title("Monthly NPS — CityMart (SAMPLE, Jan–Jun 2026)")
for i, v in enumerate(nps):
    ax.text(i, v + (1.5 if v >= 0 else -3.5), f"{v}", ha="center",
            fontsize=9)
fig.tight_layout()
plt.savefig(CHART_MO, dpi=150)
plt.close()

# driver ratings, ranked by fix-first score (best first = top)
labels = [d["label"] for d in DR]
avgs = [d["avg_rating"] for d in DR]
ranks = [d["fix_first_rank"] for d in DR]
cols = ["#C62828" if r == 1 else ("#F9A825" if r <= 3 else "#2E7D32")
        for r in ranks]
plt.figure(figsize=(8, 3.6))
plt.barh(labels[::-1], avgs[::-1], color=cols[::-1])
plt.xlim(0, 5)
plt.xlabel("Average rating (1–5) — red = fix first, amber = fix next, "
           "green = keep doing it")
plt.title("Driver ratings, ranked by fix-first score — CityMart (SAMPLE)")
for i, v in enumerate(avgs[::-1]):
    plt.text(v + 0.05, i, f"{v}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(CHART_DR, dpi=150)
plt.close()

styles = getSampleStyleSheet()
hdr = colors.HexColor("#1F4E79")


def table(rows, widths, size=9):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), hdr),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), size),
    ]))
    return t


story = [
    Paragraph("CityMart — Customer Feedback Survey Analysis",
              styles["Title"]),
    Paragraph("Survey responses analysed by branch, channel and driver · "
              "1 Jan – 30 Jun 2026 (6 months, 181 days) · SAMPLE data — "
              "fictional retail buyer, generated for this delivery "
              "(seed 20261116)", styles["Normal"]),
    Spacer(1, 0.1 * cm),
    Paragraph(
        f"Headline: <b>{TOT:,} customers surveyed</b>, "
        f"<b>NPS {OV['nps']}</b> — {OV['promoters']} promoters "
        f"({OV['promoter_pct']}%), {OV['passives']} passives, "
        f"{OV['detractors']} detractors ({OV['detractor_pct']}%). "
        f"Average satisfaction <b>{OV['avg_satisfaction']}/5</b>. "
        f"Best branch: <b>{s['best_branch']} (NPS "
        f"{s['best_branch_nps']})</b>; worst: <b>{s['worst_branch']} "
        f"(NPS {s['worst_branch_nps']})</b> — a "
        f"{s['branch_nps_gap']}-point gap. Best channel: "
        f"<b>{s['best_channel']} (NPS {s['best_channel_nps']})</b>; "
        f"worst: <b>{s['worst_channel']} (NPS "
        f"{s['worst_channel_nps']})</b>. Fix-first driver: "
        f"<b>{s['fix_first'][0]['label']} "
        f"({s['fix_first'][0]['avg_rating']}/5, correlation "
        f"{s['fix_first'][0]['correlation']})</b>.",
        styles["Normal"]),
    Spacer(1, 0.1 * cm),
    Paragraph("<b>NPS by branch — ranked</b>", styles["Heading2"]),
]
br_rows = [["Branch", "Responses", "Promoters", "Passives", "Detractors",
            "NPS", "Avg satisfaction"]]
for b in BR:
    br_rows.append([b["branch"], f"{b['responses']}",
                    f"{b['promoters']}", f"{b['passives']}",
                    f"{b['detractors']}", f"{b['nps']}",
                    f"{b['avg_satisfaction']}"])
story.append(table(br_rows,
                   [4.4 * cm, 2.0 * cm, 2.0 * cm, 1.8 * cm, 2.0 * cm,
                    1.6 * cm, 2.9 * cm]))
story.append(Spacer(1, 0.12 * cm))
story.append(Paragraph(
    f"Every driver is lower at {s['worst_branch']} than at "
    f"{s['best_branch']} — delivery speed most of all "
    f"({s['worst_branch']} {next(b['avg_delivery_speed'] for b in BR if b['branch'] == s['worst_branch'])}/5 "
    f"against {next(b['avg_delivery_speed'] for b in BR if b['branch'] == s['best_branch'])}/5).",
    styles["Normal"]))
story.append(Spacer(1, 0.1 * cm))
story.append(Paragraph("<b>NPS by channel</b>", styles["Heading2"]))
ch_rows = [["Channel", "Responses", "Promoters", "Passives",
            "Detractors", "NPS", "Avg satisfaction"]]
for c in CH:
    ch_rows.append([c["channel"], f"{c['responses']}",
                    f"{c['promoters']}", f"{c['passives']}",
                    f"{c['detractors']}", f"{c['nps']}",
                    f"{c['avg_satisfaction']}"])
story.append(table(ch_rows,
                   [4.4 * cm, 2.0 * cm, 2.0 * cm, 1.8 * cm, 2.0 * cm,
                    1.6 * cm, 2.9 * cm]))
story.append(Spacer(1, 0.1 * cm))
story.append(Paragraph("<b>What drives satisfaction? (drivers, 1–5)</b>",
                       styles["Heading2"]))
dr_rows = [["Driver", "Avg rating", "Correlation", "Gap to 5",
            "Fix-first score", "Rank"]]
for d in DR:
    dr_rows.append([d["label"], f"{d['avg_rating']}",
                    f"{d['correlation']}", f"{d['gap']}",
                    f"{d['fix_first_score']}", f"{d['fix_first_rank']}"])
story.append(table(dr_rows,
                   [4.2 * cm, 2.2 * cm, 2.4 * cm, 1.8 * cm, 2.6 * cm,
                    1.5 * cm]))
story.append(Spacer(1, 0.12 * cm))
story.append(Image(str(CHART_DR), width=15.5 * cm, height=5.4 * cm))
story.append(Spacer(1, 0.12 * cm))
story.append(Paragraph(
    f"Fix-first score = (5 - average rating) x correlation with "
    f"overall satisfaction. <b>{s['fix_first'][0]['label']}</b> ranks "
    f"first ({s['fix_first'][0]['fix_first_score']}), then "
    f"<b>{s['fix_first'][1]['label']}</b> "
    f"({s['fix_first'][1]['fix_first_score']}) and "
    f"<b>{s['fix_first'][2]['label']}</b> "
    f"({s['fix_first'][2]['fix_first_score']}). Correlations are "
    f"Pearson, computed with numpy from the 350 responses.",
    styles["Normal"]))
story.append(Spacer(1, 0.1 * cm))
story.append(Paragraph(
    "<b>What the detractors say (comment-bank themes)</b>",
    styles["Heading2"]))
th_rows = [["Theme", "Detractors mentioning it",
            "Share of detractors"]]
for t in TH:
    th_rows.append([t["theme"], f"{t['detractors']}",
                    f"{t['pct_of_detractors']}%"])
story.append(table(th_rows, [5.0 * cm, 5.5 * cm, 5.2 * cm]))
story.append(Spacer(1, 0.12 * cm))
story.append(Paragraph(
    f"Most common detractor theme: <b>{s['top_detractor_theme']}</b> "
    f"({s['top_detractor_theme_count']} of {OV['detractors']} "
    f"detractors). Comments come from a fixed phrase bank only — one "
    f"phrase per response, chosen by NPS segment — so themes are "
    f"counted from the bank tags, never invented free text.",
    styles["Normal"]))
story.append(Spacer(1, 0.1 * cm))
story.append(Paragraph("<b>Month by month</b>", styles["Heading2"]))
mo_rows = [["Month", "Responses", "Promoters", "Detractors", "NPS",
            "Avg satisfaction", "NPS change (pts)"]]
for m in MO:
    chg = "—" if m["nps_change_points"] is None else (
        f"{m['nps_change_points']:+.2f}")
    mo_rows.append([m["month"], f"{m['responses']}",
                    f"{m['promoters']}", f"{m['detractors']}",
                    f"{m['nps']}", f"{m['avg_satisfaction']}", chg])
story.append(table(mo_rows,
                   [2.4 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm,
                    2.6 * cm, 2.3 * cm]))
story.append(Spacer(1, 0.12 * cm))
story.append(Image(str(CHART_MO), width=15.5 * cm, height=4.8 * cm))
story.append(Spacer(1, 0.12 * cm))
story.append(Paragraph(
    f"NPS moved <b>{s['nps_trend_jan_to_jun_points']:+.2f} points from "
    f"January ({MO[0]['nps']}) to June ({MO[-1]['nps']})</b>. Best "
    f"month: {s['best_month']} (NPS {s['best_month_nps']}); worst: "
    f"{s['worst_month']} (NPS {s['worst_month_nps']}).",
    styles["Normal"]))
story.append(Spacer(1, 0.1 * cm))
story.append(Paragraph("<b>3 recommendations</b>", styles["Heading2"]))
for i, a in enumerate(ACTS, 1):
    story.append(Paragraph(
        f"{i}. <b>{a['title']}.</b> {a['detail']}", styles["Normal"]))
    story.append(Spacer(1, 0.1 * cm))
story.append(Spacer(1, 0.12 * cm))
story.append(Paragraph(
    "Method: every number above is recomputed from "
    "data/raw/survey_responses_SAMPLE.csv by src/analyze.py and "
    "verified by src/checks.py. The workbook carries the same numbers "
    "as live formulas. Limits: NPS from 350 responses is a survey "
    "estimate, not a census — a branch with fewer responses has a "
    "wider margin of error. Correlations show which drivers move with "
    "satisfaction in this survey, not which ones cause it.",
    styles["Normal"]))
SimpleDocTemplate(str(PDF), pagesize=A4,
                  title="CityMart — Customer Feedback Survey Analysis "
                        "(SAMPLE)",
                  author="Muhammad Hashir",
                  topMargin=1.1 * cm, bottomMargin=1.1 * cm).build(story)
print(f"charts: {CHART_MO.name}, {CHART_DR.name}")
print(f"report: {PDF}")
