#!/usr/bin/env python3
"""Checks as code for P20. Recomputes every headline number from the
raw CSV and verifies the JSON, the processed CSVs, the workbook
formulas and the LibreOffice recalc against it — three independent
paths that must agree. Correlations are recomputed with numpy here
and with CORREL in the workbook; the fix-first ranking is checked
against the unrounded score, so two drivers that round to the same
3 decimals can still rank apart.

    python3 src/checks.py        (after the full pipeline + recalc:
    soffice --headless --calc --convert-to xlsx --outdir outputs/.recalc
    outputs/customer_feedback_report_SAMPLE.xlsx)

Exit code 0 when every check passes, 1 otherwise.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SUMMARY = PROJECT / "outputs" / "summary.json"
WORKBOOK = PROJECT / "outputs" / "customer_feedback_report_SAMPLE.xlsx"
RECALC = PROJECT / "outputs" / ".recalc" / "customer_feedback_report_SAMPLE.xlsx"
PDF = PROJECT / "outputs" / "feedback_report.pdf"
MD = PROJECT / "outputs" / "feedback_report.md"

BRANCHES = ["Lahore — Gulberg", "Karachi — Clifton",
            "Rawalpindi — Saddar"]
CHANNELS = ["In-store", "Online", "Phone"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
DRIVERS = [
    ("product_quality", "Product quality"),
    ("price", "Price"),
    ("delivery_speed", "Delivery speed"),
    ("staff_service", "Staff service"),
    ("store_cleanliness", "Store cleanliness"),
]
THEMES = ["delivery", "price", "staff", "stock", "cleanliness",
          "quality", "overall"]
fails = []
ran = []


def check(name, cond, detail=""):
    ran.append(name)
    print(("PASS " if cond else "FAIL ") + name +
          (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def segment(recommend):
    if recommend >= 9:
        return "Promoter"
    if recommend >= 7:
        return "Passive"
    return "Detractor"


def group_stats(rows):
    n = len(rows)
    prom = sum(r["promoter"] for r in rows)
    detr = sum(r["detractor"] for r in rows)
    pas = n - prom - detr
    out = {
        "responses": n, "promoters": prom, "passives": pas,
        "detractors": detr, "promoter_pct": pct(prom, n),
        "detractor_pct": pct(detr, n),
        "nps": round(100.0 * (prom - detr) / n, 2) if n else 0.0,
        "avg_satisfaction": round(
            sum(r["satisfaction"] for r in rows) / n, 2) if n else 0.0,
    }
    for key, _label in DRIVERS:
        out[f"avg_{key}"] = round(
            sum(r[key] for r in rows) / n, 2) if n else 0.0
    return out


raw = list(csv.DictReader(open(RAW / "survey_responses_SAMPLE.csv",
                               encoding="utf-8")))
rows = []
for r in raw:
    rec = int(r["recommend"])
    seg = segment(rec)
    rows.append({
        "response_id": r["response_id"], "survey_date": r["survey_date"],
        "month": r["month"], "branch": r["branch"],
        "channel": r["channel"], "recommend": rec,
        "satisfaction": int(r["satisfaction"]),
        "product_quality": int(r["product_quality"]),
        "price": int(r["price"]),
        "delivery_speed": int(r["delivery_speed"]),
        "staff_service": int(r["staff_service"]),
        "store_cleanliness": int(r["store_cleanliness"]),
        "comment": r["comment"], "theme": r["theme"],
        "nps_segment": seg,
        "promoter": 1 if seg == "Promoter" else 0,
        "passive": 1 if seg == "Passive" else 0,
        "detractor": 1 if seg == "Detractor" else 0,
    })
total = len(rows)
ov = group_stats(rows)
by_branch = {b: group_stats([r for r in rows if r["branch"] == b])
             for b in BRANCHES}
by_channel = {c: group_stats([r for r in rows if r["channel"] == c])
              for c in CHANNELS}
by_month = {m: group_stats([r for r in rows if r["month"] == m])
            for m in MONTHS}
best_branch = max(BRANCHES, key=lambda b: by_branch[b]["nps"])
worst_branch = min(BRANCHES, key=lambda b: by_branch[b]["nps"])
best_channel = max(CHANNELS, key=lambda c: by_channel[c]["nps"])
worst_channel = min(CHANNELS, key=lambda c: by_channel[c]["nps"])
best_month = max(MONTHS, key=lambda m: by_month[m]["nps"])
worst_month = min(MONTHS, key=lambda m: by_month[m]["nps"])

sat = np.array([r["satisfaction"] for r in rows], dtype=float)
drivers = {}
for key, label in DRIVERS:
    x = np.array([r[key] for r in rows], dtype=float)
    corr_raw = float(np.corrcoef(x, sat)[0, 1])
    avg_raw = float(x.mean())
    drivers[key] = {
        "label": label, "avg_rating": round(avg_raw, 2),
        "correlation": round(corr_raw, 3),
        "gap": round(5 - avg_raw, 2),
        "fix_first_score": round((5 - avg_raw) * corr_raw, 3),
        "raw_score": (5 - avg_raw) * corr_raw,
    }
ranked = sorted(drivers, key=lambda k: -drivers[k]["raw_score"])
for i, k in enumerate(ranked, start=1):
    drivers[k]["fix_first_rank"] = i

detractors = [r for r in rows if r["detractor"]]
themes = {}
for t in THEMES:
    n = sum(1 for r in detractors if r["theme"] == t)
    themes[t] = {"detractors": n, "pct_of_detractors": pct(n, len(detractors))}
top_theme = max(THEMES, key=lambda t: themes[t]["detractors"])

# ── raw file ───────────────────────────────────────────────────────────
check("responses = 350", total == 350, str(total))
check("dates span 2026-01-01..2026-06-30",
      min(r["survey_date"] for r in rows) == "2026-01-01" and
      max(r["survey_date"] for r in rows) == "2026-06-30")
check("6 distinct months",
      sorted({r["month"] for r in rows}) == MONTHS)
check("3 branches only",
      {r["branch"] for r in rows} == set(BRANCHES))
check("3 channels only",
      {r["channel"] for r in rows} == set(CHANNELS))
check("response_ids unique",
      len({r["response_id"] for r in rows}) == total)
check("response_ids are R-####",
      all(re.fullmatch(r"R-\d{4}", r["response_id"]) for r in rows))
check("month matches the survey-date prefix",
      all(r["month"] == r["survey_date"][:7] for r in rows))
check("recommend is 0..10 throughout",
      all(0 <= r["recommend"] <= 10 for r in rows))
check("satisfaction is 1..5 throughout",
      all(1 <= r["satisfaction"] <= 5 for r in rows))
for key, _label in DRIVERS:
    check(f"driver {key} is 1..5 throughout",
          all(1 <= r[key] <= 5 for r in rows))
check("every branch has >= 50 responses",
      min(v["responses"] for v in by_branch.values()) >= 50,
      str(min(v["responses"] for v in by_branch.values())))
check("every channel has >= 50 responses",
      min(v["responses"] for v in by_channel.values()) >= 50,
      str(min(v["responses"] for v in by_channel.values())))
check("every month has >= 40 responses",
      min(v["responses"] for v in by_month.values()) >= 40,
      str(min(v["responses"] for v in by_month.values())))
check("comments come from the fixed phrase bank only",
      all(r["comment"] in {
          "Staff were friendly and helpful.",
          "Good quality products, fresh stock.",
          "Delivery arrived before time.",
          "Fair prices for the quality.",
          "Clean store, easy to shop.",
          "Best branch in the area, I will come again.",
          "Good overall, delivery could be faster.",
          "Prices are a little high but quality is fine.",
          "Staff are okay, nothing special.",
          "Store is fine, parking is difficult.",
          "Products are good, some items were out of stock.",
          "Delivery was very late, no one called.",
          "Prices are too high compared to other stores.",
          "Staff were rude and did not help.",
          "The item I wanted was out of stock again.",
          "Store was dirty and shelves were messy.",
          "Product quality was poor, had to return it."}
          for r in rows))
check("promoter comments are only promoter phrases",
      all(r["comment"] in {
          "Staff were friendly and helpful.",
          "Good quality products, fresh stock.",
          "Delivery arrived before time.",
          "Fair prices for the quality.",
          "Clean store, easy to shop.",
          "Best branch in the area, I will come again."}
          for r in rows if r["promoter"]))
check("detractor comments are only detractor phrases",
      all(r["comment"] in {
          "Delivery was very late, no one called.",
          "Prices are too high compared to other stores.",
          "Staff were rude and did not help.",
          "The item I wanted was out of stock again.",
          "Store was dirty and shelves were messy.",
          "Product quality was poor, had to return it."}
          for r in rows if r["detractor"]))
check("theme is one of the 7 bank themes",
      {r["theme"] for r in rows} <= set(THEMES))

# ── recompute: headline NPS ────────────────────────────────────────────
check("promoters + passives + detractors = total",
      ov["promoters"] + ov["passives"] + ov["detractors"] == total)
check("NPS recomputes from segments",
      ov["nps"] == round(100.0 * (ov["promoters"] - ov["detractors"])
                         / total, 2), str(ov["nps"]))
check("NPS is 16.29", ov["nps"] == 16.29, str(ov["nps"]))
check("promoters = 138", ov["promoters"] == 138, str(ov["promoters"]))
check("passives = 131", ov["passives"] == 131, str(ov["passives"]))
check("detractors = 81", ov["detractors"] == 81, str(ov["detractors"]))
check("avg satisfaction = 4.03", ov["avg_satisfaction"] == 4.03,
      str(ov["avg_satisfaction"]))
check("best branch = Lahore — Gulberg",
      best_branch == "Lahore — Gulberg", best_branch)
check("best branch NPS = 34.62",
      by_branch[best_branch]["nps"] == 34.62,
      str(by_branch[best_branch]["nps"]))
check("worst branch = Rawalpindi — Saddar",
      worst_branch == "Rawalpindi — Saddar", worst_branch)
check("worst branch NPS = 4.05",
      by_branch[worst_branch]["nps"] == 4.05,
      str(by_branch[worst_branch]["nps"]))
check("branch NPS gap = 30.57",
      round(by_branch[best_branch]["nps"]
            - by_branch[worst_branch]["nps"], 2) == 30.57)
check("best channel = In-store", best_channel == "In-store",
      best_channel)
check("worst channel = Online", worst_channel == "Online",
      worst_channel)
check("branch responses sum to 350",
      sum(v["responses"] for v in by_branch.values()) == total)
check("channel responses sum to 350",
      sum(v["responses"] for v in by_channel.values()) == total)
check("monthly responses sum to 350",
      sum(v["responses"] for v in by_month.values()) == total)
check("branch promoters sum to 138",
      sum(v["promoters"] for v in by_branch.values()) == 138)
check("branch detractors sum to 81",
      sum(v["detractors"] for v in by_branch.values()) == 81)
check("January is the worst month for NPS",
      worst_month == "2026-01", worst_month)
check("February is the best month for NPS",
      best_month == "2026-02", best_month)
check("NPS trend Jan->Jun = +28.67",
      round(by_month["2026-06"]["nps"] - by_month["2026-01"]["nps"], 2)
      == 28.67)
check("May dips below April (NPS falls)",
      by_month["2026-05"]["nps"] < by_month["2026-04"]["nps"],
      f"{by_month['2026-05']['nps']} vs {by_month['2026-04']['nps']}")
for b in BRANCHES:
    check(f"branch {b}: NPS recomputes from its segments",
          by_branch[b]["nps"] == round(
              100.0 * (by_branch[b]["promoters"]
                       - by_branch[b]["detractors"])
              / by_branch[b]["responses"], 2),
          str(by_branch[b]["nps"]))
for c in CHANNELS:
    check(f"channel {c}: NPS recomputes from its segments",
          by_channel[c]["nps"] == round(
              100.0 * (by_channel[c]["promoters"]
                       - by_channel[c]["detractors"])
              / by_channel[c]["responses"], 2),
          str(by_channel[c]["nps"]))

# ── drivers ────────────────────────────────────────────────────────────
check("delivery speed is the lowest-rated driver",
      min(drivers, key=lambda k: drivers[k]["avg_rating"])
      == "delivery_speed")
check("delivery speed avg = 3.84",
      drivers["delivery_speed"]["avg_rating"] == 3.84)
check("delivery speed has the highest correlation",
      max(drivers, key=lambda k: drivers[k]["correlation"])
      == "delivery_speed")
check("delivery speed correlation = 0.725",
      drivers["delivery_speed"]["correlation"] == 0.725)
check("fix-first #1 = delivery speed", ranked[0] == "delivery_speed")
check("fix-first #2 = product quality",
      ranked[1] == "product_quality")
check("fix-first #3 = price", ranked[2] == "price")
check("fix-first delivery score = 0.843",
      drivers["delivery_speed"]["fix_first_score"] == 0.843)
check("all correlations are between 0.5 and 0.9",
      all(0.5 < drivers[k]["correlation"] < 0.9 for k in drivers))
check("Rawalpindi delivery (3.30) is far below Lahore (4.18)",
      by_branch["Rawalpindi — Saddar"]["avg_delivery_speed"] == 3.3
      and by_branch["Lahore — Gulberg"]["avg_delivery_speed"] == 4.18)
check("top detractor theme = stock", top_theme == "stock", top_theme)
check("stock detractors = 18", themes["stock"]["detractors"] == 18)
check("detractor themes sum to 81",
      sum(t["detractors"] for t in themes.values()) == 81)

# ── summary JSON ───────────────────────────────────────────────────────
s = json.loads(SUMMARY.read_text(encoding="utf-8"))
check("JSON total responses = 350", s["total_responses"] == total)
check("JSON overall NPS matches recompute",
      s["overall"]["nps"] == ov["nps"])
check("JSON overall promoters matches recompute",
      s["overall"]["promoters"] == ov["promoters"])
check("JSON overall detractors matches recompute",
      s["overall"]["detractors"] == ov["detractors"])
check("JSON avg satisfaction matches recompute",
      s["overall"]["avg_satisfaction"] == ov["avg_satisfaction"])
check("JSON best branch matches recompute",
      s["best_branch"] == best_branch)
check("JSON worst branch matches recompute",
      s["worst_branch"] == worst_branch)
check("JSON best channel matches recompute",
      s["best_channel"] == best_channel)
check("JSON worst channel matches recompute",
      s["worst_channel"] == worst_channel)
check("JSON branches match recompute",
      all(x["nps"] == by_branch[x["branch"]]["nps"]
          and x["responses"] == by_branch[x["branch"]]["responses"]
          for x in s["by_branch"]))
check("JSON channels match recompute",
      all(x["nps"] == by_channel[x["channel"]]["nps"]
          and x["responses"] == by_channel[x["channel"]]["responses"]
          for x in s["by_channel"]))
check("JSON drivers match recompute",
      all(d["avg_rating"] == drivers[d["driver"]]["avg_rating"]
          and d["correlation"] == drivers[d["driver"]]["correlation"]
          and d["fix_first_score"]
          == drivers[d["driver"]]["fix_first_score"]
          and d["fix_first_rank"]
          == drivers[d["driver"]]["fix_first_rank"]
          for d in s["by_driver"]))
check("JSON months match recompute",
      all(m["nps"] == by_month[m["month"]]["nps"]
          and m["responses"] == by_month[m["month"]]["responses"]
          for m in s["months"]))
check("JSON NPS trend Jan->Jun matches recompute",
      s["nps_trend_jan_to_jun_points"]
      == round(by_month["2026-06"]["nps"]
               - by_month["2026-01"]["nps"], 2))
check("JSON top detractor theme matches recompute",
      s["top_detractor_theme"] == top_theme)
check("JSON detractor themes match recompute",
      all(t["detractors"] == themes[t["theme"]]["detractors"]
          for t in s["detractor_themes"]))
check("JSON has 3 actions", len(s["actions"]) == 3)
check("JSON action 1 names the fix-first driver",
      "delivery speed" in s["actions"][0]["title"].lower())
check("JSON action 2 names the best and worst branches",
      best_branch in s["actions"][1]["title"]
      and worst_branch in s["actions"][1]["title"])
check("JSON fix-first list is delivery, product, price",
      [f["label"] for f in s["fix_first"]]
      == ["Delivery speed", "Product quality", "Price"])


def read_csv(name):
    return list(csv.DictReader(open(
        PROJECT / "data" / "processed" / name, encoding="utf-8")))


enr = read_csv("survey_responses_enriched.csv")
check("enriched CSV has 350 rows", len(enr) == 350)
check("enriched segment flags match recommend throughout",
      all((r["nps_segment"] == "Promoter") == (int(r["recommend"]) >= 9)
          and (r["nps_segment"] == "Passive")
          == (7 <= int(r["recommend"]) <= 8)
          and (r["nps_segment"] == "Detractor")
          == (int(r["recommend"]) <= 6) for r in enr))
check("enriched promoter flags match segments throughout",
      all(int(r["promoter"]) == (1 if r["nps_segment"] == "Promoter"
                                 else 0) for r in enr))
check("enriched detractor flags match segments throughout",
      all(int(r["detractor"]) == (1 if r["nps_segment"] == "Detractor"
                                  else 0) for r in enr))
check("enriched first row is R-0001", enr[0]["response_id"] == "R-0001")
bcsv = read_csv("branch_summary.csv")
check("branch CSV has 3 rows", len(bcsv) == 3)
check("branch CSV NPS matches recompute",
      all(float(r["nps"]) == by_branch[r["branch"]]["nps"]
          for r in bcsv))
ccsv = read_csv("channel_summary.csv")
check("channel CSV has 3 rows", len(ccsv) == 3)
check("channel CSV NPS matches recompute",
      all(float(r["nps"]) == by_channel[r["channel"]]["nps"]
          for r in ccsv))
dcsv = read_csv("driver_summary.csv")
check("driver CSV has 5 rows", len(dcsv) == 5)
check("driver CSV fix-first ranks match recompute",
      all(int(r["fix_first_rank"])
          == drivers[r["driver"]]["fix_first_rank"] for r in dcsv))
check("driver CSV first row is the fix-first driver",
      dcsv[0]["driver"] == "delivery_speed")
mcsv = read_csv("monthly_summary.csv")
check("monthly CSV has 6 rows", len(mcsv) == 6)
check("monthly CSV NPS matches recompute",
      all(float(r["nps"]) == by_month[r["month"]]["nps"] for r in mcsv))
check("monthly CSV January NPS change is blank",
      mcsv[0]["nps_change_points"] in ("", None))
check("monthly CSV June NPS change = +25.94 (June minus May)",
      float(mcsv[5]["nps_change_points"]) == 25.94)

# ── workbook (formulas) ────────────────────────────────────────────────
wb = load_workbook(WORKBOOK)
check("sheets = Dashboard, Responses, By Branch, By Channel, "
      "By Driver, Monthly Trend, Method",
      wb.sheetnames == ["Dashboard", "Responses", "By Branch",
                        "By Channel", "By Driver", "Monthly Trend",
                        "Method"], str(wb.sheetnames))
rsw = wb["Responses"]
check("Responses rows = 351 incl header", rsw.max_row == 351,
      str(rsw.max_row))
check("Responses header has 18 columns", rsw.max_column == 18,
      str(rsw.max_column))
check("Responses A2 = R-0001", rsw["A2"].value == "R-0001",
      str(rsw["A2"].value))
check("Responses O2 is the NPS-segment IF formula",
      rsw["O2"].value == '=IF(F2>=9,"Promoter",IF(F2>=7,"Passive",'
                          '"Detractor"))', str(rsw["O2"].value))
check("Responses P2 is the promoter flag formula",
      rsw["P2"].value == '=IF(O2="Promoter",1,0)', str(rsw["P2"].value))
check("Responses Q2 is the passive flag formula",
      rsw["Q2"].value == '=IF(O2="Passive",1,0)', str(rsw["Q2"].value))
check("Responses R2 is the detractor flag formula",
      rsw["R2"].value == '=IF(O2="Detractor",1,0)', str(rsw["R2"].value))
dash = wb["Dashboard"]
check("Dashboard B5 is a COUNTA formula over Responses",
      dash["B5"].value == f"=COUNTA(Responses!A2:A{total + 1})",
      str(dash["B5"].value))
check("Dashboard B6 is the NPS formula",
      dash["B6"].value == "=IF(B5=0,0,100*(B7-B9)/B5)",
      str(dash["B6"].value))
check("Dashboard B7 sums promoter flags",
      dash["B7"].value == f"=SUM(Responses!P2:P{total + 1})",
      str(dash["B7"].value))
check("Dashboard B9 sums detractor flags",
      dash["B9"].value == f"=SUM(Responses!R2:R{total + 1})",
      str(dash["B9"].value))
check("Dashboard B12 averages satisfaction",
      dash["B12"].value == f"=AVERAGE(Responses!G2:G{total + 1})",
      str(dash["B12"].value))
check("Dashboard B15 averages delivery speed",
      dash["B15"].value == f"=AVERAGE(Responses!J2:J{total + 1})",
      str(dash["B15"].value))
check("Dashboard B18 is the best-branch INDEX/MATCH",
      isinstance(dash["B18"].value, str) and
      dash["B18"].value.startswith(
          "=INDEX('By Branch'!A4:A6,MATCH(MAX("),
      str(dash["B18"].value))
check("Dashboard B19 is the worst-branch INDEX/MATCH",
      isinstance(dash["B19"].value, str) and
      dash["B19"].value.startswith(
          "=INDEX('By Branch'!A4:A6,MATCH(MIN("),
      str(dash["B19"].value))
check("Dashboard B20 is the best-channel INDEX/MATCH",
      isinstance(dash["B20"].value, str) and
      dash["B20"].value.startswith(
          "=INDEX('By Channel'!A4:A6,MATCH(MAX("),
      str(dash["B20"].value))
check("Dashboard B22 is the top fix-first driver INDEX/MATCH",
      isinstance(dash["B22"].value, str) and
      dash["B22"].value.startswith(
          "=INDEX('By Driver'!A4:A8,MATCH(MAX("),
      str(dash["B22"].value))
check("Dashboard B24 uses _xlfn.MAXIFS for best branch NPS (50+)",
      isinstance(dash["B24"].value, str) and
      dash["B24"].value.startswith("=_xlfn.MAXIFS("),
      str(dash["B24"].value))
check("Dashboard B25 uses _xlfn.MINIFS for worst branch NPS (50+)",
      isinstance(dash["B25"].value, str) and
      dash["B25"].value.startswith("=_xlfn.MINIFS("),
      str(dash["B25"].value))
check("Dashboard monthly B29 is a COUNTIFS over Responses month",
      isinstance(dash["B29"].value, str) and
      dash["B29"].value.startswith("=COUNTIFS(Responses!$C$"),
      str(dash["B29"].value))
check("Dashboard monthly C29 is the NPS formula",
      isinstance(dash["C29"].value, str) and
      "SUMIFS(Responses!$P$" in dash["C29"].value
      and "SUMIFS(Responses!$R$" in dash["C29"].value,
      str(dash["C29"].value))
check("Dashboard monthly total row uses SUM",
      dash["B35"].value == "=SUM(B29:B34)", str(dash["B35"].value))
check("Dashboard has a chart", len(dash._charts) >= 1)
brw = wb["By Branch"]
check("By Branch rows = 7 incl header + total", brw.max_row == 7,
      str(brw.max_row))
check("By Branch B4 is a COUNTIFS over Responses branch",
      isinstance(brw["B4"].value, str) and
      brw["B4"].value.startswith("=COUNTIFS(Responses!$D$"),
      str(brw["B4"].value))
check("By Branch F4 is the NPS formula",
      brw["F4"].value == "=IF(B4=0,0,100*(C4-E4)/B4)",
      str(brw["F4"].value))
check("By Branch G4 is an AVERAGEIFS satisfaction formula",
      isinstance(brw["G4"].value, str) and
      brw["G4"].value.startswith("=AVERAGEIFS(Responses!$G$"),
      str(brw["G4"].value))
check("By Branch total row B7 sums responses",
      brw["B7"].value == "=SUM(B4:B6)", str(brw["B7"].value))
chw = wb["By Channel"]
check("By Channel B4 is a COUNTIFS over Responses channel",
      isinstance(chw["B4"].value, str) and
      chw["B4"].value.startswith("=COUNTIFS(Responses!$E$"),
      str(chw["B4"].value))
check("By Channel total row B7 sums responses",
      chw["B7"].value == "=SUM(B4:B6)", str(chw["B7"].value))
drw = wb["By Driver"]
check("By Driver rows = 8 incl header", drw.max_row == 8,
      str(drw.max_row))
check("By Driver B4 averages a driver column",
      drw["B4"].value == f"=AVERAGE(Responses!H2:H{total + 1})",
      str(drw["B4"].value))
check("By Driver C4 is a CORREL formula",
      isinstance(drw["C4"].value, str) and
      drw["C4"].value.startswith("=CORREL(Responses!H2:H"),
      str(drw["C4"].value))
check("By Driver D4 is the gap-to-5 formula",
      drw["D4"].value == "=5-B4", str(drw["D4"].value))
check("By Driver E4 is the fix-first formula",
      drw["E4"].value == "=D4*C4", str(drw["E4"].value))
check("By Driver F4 is the RANK formula",
      drw["F4"].value == "=RANK(E4,$E$4:$E$8,0)", str(drw["F4"].value))
mow = wb["Monthly Trend"]
check("Monthly B4 is a COUNTIFS over Responses month",
      isinstance(mow["B4"].value, str) and
      mow["B4"].value.startswith("=COUNTIFS(Responses!$C$"),
      str(mow["B4"].value))
check("Monthly M4 is the em-dash for January",
      mow["M4"].value == "—", str(mow["M4"].value))
check("Monthly M5 is the NPS-change formula",
      mow["M5"].value == "=F5-F4", str(mow["M5"].value))
check("Monthly total row B10 sums responses",
      mow["B10"].value == "=SUM(B4:B9)", str(mow["B10"].value))
check("Method sheet mentions _xlfn.",
      any("_xlfn." in (wb["Method"].cell(row=r, column=2).value or "")
          for r in range(3, 15)))
check("Method sheet states the NPS 9–10 / 7–8 / 0–6 bands",
      any("Promoter = 9" in (wb["Method"].cell(row=r, column=2).value
                             or "")
          for r in range(3, 15)))
check("Method sheet states the fix-first formula",
      any("Fix-first score" in (wb["Method"].cell(row=r, column=2).value
                                or "")
          for r in range(3, 15)))
# no literal {last} / unexpanded placeholder in any formula
bad = []
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("=") \
                    and "{" in cell.value:
                bad.append(f"{ws.title}!{cell.coordinate}={cell.value}")
check("no formula contains an unexpanded {placeholder}",
      not bad, "; ".join(bad[:3]))

# ── LibreOffice recalculated values ────────────────────────────────────
if RECALC.exists():
    wb2 = load_workbook(RECALC, data_only=True)
    d2 = wb2["Dashboard"]
    check("recalc Dashboard total responses = 350",
          d2["B5"].value == 350, str(d2["B5"].value))
    check("recalc Dashboard NPS matches recompute",
          abs(d2["B6"].value - ov["nps"]) < 0.01, str(d2["B6"].value))
    check("recalc Dashboard promoters = 138",
          d2["B7"].value == 138, str(d2["B7"].value))
    check("recalc Dashboard passives = 131",
          d2["B8"].value == 131, str(d2["B8"].value))
    check("recalc Dashboard detractors = 81",
          d2["B9"].value == 81, str(d2["B9"].value))
    check("recalc Dashboard promoter % matches recompute",
          abs(d2["B10"].value - ov["promoter_pct"] / 100) < 0.0005,
          str(d2["B10"].value))
    check("recalc Dashboard detractor % matches recompute",
          abs(d2["B11"].value - ov["detractor_pct"] / 100) < 0.0005,
          str(d2["B11"].value))
    check("recalc Dashboard avg satisfaction matches recompute",
          abs(d2["B12"].value - ov["avg_satisfaction"]) < 0.01,
          str(d2["B12"].value))
    check("recalc Dashboard avg delivery speed matches recompute",
          abs(d2["B15"].value - ov["avg_delivery_speed"]) < 0.01,
          str(d2["B15"].value))
    check("recalc Dashboard best branch = Lahore — Gulberg",
          d2["B18"].value == "Lahore — Gulberg", str(d2["B18"].value))
    check("recalc Dashboard best branch NPS matches recompute",
          abs(d2["C18"].value - by_branch[best_branch]["nps"]) < 0.01,
          str(d2["C18"].value))
    check("recalc Dashboard worst branch = Rawalpindi — Saddar",
          d2["B19"].value == "Rawalpindi — Saddar",
          str(d2["B19"].value))
    check("recalc Dashboard worst branch NPS matches recompute",
          abs(d2["C19"].value - by_branch[worst_branch]["nps"]) < 0.01,
          str(d2["C19"].value))
    check("recalc Dashboard best channel = In-store",
          d2["B20"].value == "In-store", str(d2["B20"].value))
    check("recalc Dashboard worst channel = Online",
          d2["B21"].value == "Online", str(d2["B21"].value))
    check("recalc Dashboard top fix-first driver = Delivery speed",
          d2["B22"].value == "Delivery speed", str(d2["B22"].value))
    check("recalc Dashboard top fix-first score matches recompute",
          abs(d2["C22"].value
              - drivers["delivery_speed"]["fix_first_score"]) < 0.01,
          str(d2["C22"].value))
    check("recalc best branch NPS (50+) = 34.62",
          abs(d2["B24"].value - 34.62) < 0.01, str(d2["B24"].value))
    check("recalc best branch NPS (50+) name = Lahore — Gulberg",
          d2["C24"].value == "Lahore — Gulberg", str(d2["C24"].value))
    check("recalc worst branch NPS (50+) = 4.05",
          abs(d2["B25"].value - 4.05) < 0.01, str(d2["B25"].value))
    check("recalc worst branch NPS (50+) name = Rawalpindi — Saddar",
          d2["C25"].value == "Rawalpindi — Saddar",
          str(d2["C25"].value))
    check("recalc monthly Jan NPS matches recompute",
          abs(d2["C29"].value - by_month["2026-01"]["nps"]) < 0.01,
          str(d2["C29"].value))
    check("recalc monthly Jun NPS matches recompute",
          abs(d2["C34"].value - by_month["2026-06"]["nps"]) < 0.01,
          str(d2["C34"].value))
    check("recalc monthly TOTAL responses = 350",
          d2["B35"].value == 350, str(d2["B35"].value))
    check("recalc monthly TOTAL NPS matches recompute",
          abs(d2["C35"].value - ov["nps"]) < 0.01, str(d2["C35"].value))
    b2 = wb2["By Branch"]
    for name in BRANCHES:
        row = next(r for r in range(4, 7)
                   if b2.cell(row=r, column=1).value == name)
        v = by_branch[name]
        check(f"recalc By Branch {name}: NPS matches",
              abs(b2.cell(row=row, column=6).value - v["nps"]) < 0.01,
              str(b2.cell(row=row, column=6).value))
        check(f"recalc By Branch {name}: avg satisfaction matches",
              abs(b2.cell(row=row, column=7).value
                  - v["avg_satisfaction"]) < 0.01,
              str(b2.cell(row=row, column=7).value))
    check("recalc By Branch TOTAL responses = 350",
          b2["B7"].value == 350, str(b2["B7"].value))
    c2 = wb2["By Channel"]
    for name in CHANNELS:
        row = next(r for r in range(4, 7)
                   if c2.cell(row=r, column=1).value == name)
        check(f"recalc By Channel {name}: NPS matches",
              abs(c2.cell(row=row, column=6).value
                  - by_channel[name]["nps"]) < 0.01,
              str(c2.cell(row=row, column=6).value))
    check("recalc By Channel TOTAL responses = 350",
          c2["B7"].value == 350, str(c2["B7"].value))
    dr2 = wb2["By Driver"]
    for key, label in DRIVERS:
        row = next(r for r in range(4, 9)
                   if dr2.cell(row=r, column=1).value == label)
        v = drivers[key]
        check(f"recalc By Driver {label}: avg rating matches",
              abs(dr2.cell(row=row, column=2).value
                  - v["avg_rating"]) < 0.01,
              str(dr2.cell(row=row, column=2).value))
        check(f"recalc By Driver {label}: correlation matches numpy",
              abs(dr2.cell(row=row, column=3).value
                  - v["correlation"]) < 0.002,
              str(dr2.cell(row=row, column=3).value))
        check(f"recalc By Driver {label}: fix-first score matches",
              abs(dr2.cell(row=row, column=5).value
                  - v["fix_first_score"]) < 0.01,
              str(dr2.cell(row=row, column=5).value))
        check(f"recalc By Driver {label}: rank matches",
              dr2.cell(row=row, column=6).value == v["fix_first_rank"],
              str(dr2.cell(row=row, column=6).value))
    m2 = wb2["Monthly Trend"]
    check("recalc Monthly TOTAL responses = 350",
          m2["B10"].value == 350, str(m2["B10"].value))
    check("recalc Monthly Jun NPS change = +25.94 (June minus May)",
          abs(m2["M9"].value - 25.94) < 0.01, str(m2["M9"].value))
    o2 = wb2["Responses"]
    check("recalc Responses promoter flags sum to 138",
          sum(o2.cell(row=r, column=16).value or 0 for r in range(2, 352))
          == 138)
    check("recalc Responses detractor flags sum to 81",
          sum(o2.cell(row=r, column=18).value or 0 for r in range(2, 352))
          == 81)
    errors = []
    for ws in wb2.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("#"):
                    errors.append(f"{ws.title}!{cell.coordinate}={cell.value}")
    check("recalc workbook has no error values (#NAME?, #VALUE!, ...)",
          not errors, "; ".join(errors[:5]))
else:
    print(f"  NOTE: no LibreOffice recalc copy found at {RECALC} — "
          "recalc checks skipped")

# ── PDF + markdown ─────────────────────────────────────────────────────
check("feedback_report.pdf exists", PDF.exists())
if PDF.exists():
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True,
                          text=True)
    pages = re.search(r"Pages:\s+(\d+)", info.stdout)
    check("PDF has exactly 2 pages",
          pages is not None and int(pages.group(1)) == 2,
          info.stdout.splitlines()[0] if info.stdout else "pdfinfo failed")
    text = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True,
                          text=True).stdout
    check("PDF text contains total responses", "350" in text)
    check("PDF text contains NPS 16.29", "16.29" in text)
    check("PDF text contains Lahore", "Lahore" in text)
    check("PDF text contains Rawalpindi", "Rawalpindi" in text)
    check("PDF text contains Delivery speed", "Delivery speed" in text)
    check("PDF text contains stock theme", "stock" in text)
check("feedback_report.md exists", MD.exists())
if MD.exists():
    md = MD.read_text(encoding="utf-8")
    check("MD contains NPS 16.29", "16.29" in md)
    check("MD contains fix-first driver", "Delivery speed" in md)
    check("MD contains 3 recommendations",
          md.count("**Fix ") + md.count("**Close the gap")
          + md.count("**Stop the stock-outs") == 3)

print(f"\n{len(ran) - len(fails)}/{len(ran)} checks passed")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
