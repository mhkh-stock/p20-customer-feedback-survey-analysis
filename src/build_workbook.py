#!/usr/bin/env python3
"""P20 — build the deliverable workbook for CityMart (SAMPLE):

  Dashboard              — KPIs (NPS, promoters/passives/detractors,
                           average satisfaction, driver averages),
                           best/worst branch and channel, top
                           fix-first driver, best/worst branch NPS via
                           MAXIFS/MINIFS (written with the _xlfn.
                           prefix so LibreOffice and Excel calculate
                           them), monthly NPS trend + chart — all live
                           formulas over Responses
  Responses              — all 350 survey responses (values for the
                           source columns, live formulas for NPS
                           segment and promoter/passive/detractor
                           flags)
  By Branch              — 3 branches: responses, NPS segments, NPS,
                           average satisfaction + driver averages,
                           all live COUNTIFS / SUMIFS / AVERAGEIFS
                           over Responses
  By Channel             — same, 3 channels
  By Driver              — 5 drivers: average rating, Pearson
                           correlation with overall satisfaction
                           (CORREL), gap to 5, fix-first score and
                           rank, all live formulas over Responses
  Monthly Trend          — 6 months: responses, NPS segments, NPS,
                           average satisfaction, month-on-month NPS
                           change, all live formulas over Responses
  Method                 — how to read it, the NPS rules, the
                           fix-first score and their limits, how to
                           re-verify

    python3 src/build_workbook.py
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
OUT = PROJECT / "outputs" / "customer_feedback_report_SAMPLE.xlsx"

BRANCHES = ["Lahore — Gulberg", "Karachi — Clifton",
            "Rawalpindi — Saddar"]
CHANNELS = ["In-store", "Online", "Phone"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
DRIVERS = [
    ("product_quality", "Product quality", "H"),
    ("price", "Price", "I"),
    ("delivery_speed", "Delivery speed", "J"),
    ("staff_service", "Staff service", "K"),
    ("store_cleanliness", "Store cleanliness", "L"),
]
HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
COUNT_FMT = "#,##0"
PCT_FMT = "0.00%"
AVG_FMT = "0.00"
NPS_FMT = "0.00"


def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT


def main():
    raw = list(csv.DictReader(
        open(RAW / "survey_responses_SAMPLE.csv", encoding="utf-8")))
    n = len(raw)
    last = n + 1  # last data row on Responses (row 1 = header)

    wb = Workbook()

    # ── Responses (values for source columns, formulas for derived) ──
    rs = wb.active
    rs.title = "Responses"
    rs.append(["response_id", "survey_date", "month", "branch",
               "channel", "recommend", "satisfaction",
               "product_quality", "price", "delivery_speed",
               "staff_service", "store_cleanliness", "comment",
               "theme", "nps_segment", "promoter", "passive",
               "detractor"])
    for r in raw:
        rs.append([r["response_id"], r["survey_date"], r["month"],
                   r["branch"], r["channel"], int(r["recommend"]),
                   int(r["satisfaction"]), int(r["product_quality"]),
                   int(r["price"]), int(r["delivery_speed"]),
                   int(r["staff_service"]),
                   int(r["store_cleanliness"]), r["comment"],
                   r["theme"]])
    for i in range(2, last + 1):
        rs.cell(row=i, column=15).value = (
            f'=IF(F{i}>=9,"Promoter",IF(F{i}>=7,"Passive","Detractor"))')
        rs.cell(row=i, column=16).value = f'=IF(O{i}="Promoter",1,0)'
        rs.cell(row=i, column=17).value = f'=IF(O{i}="Passive",1,0)'
        rs.cell(row=i, column=18).value = f'=IF(O{i}="Detractor",1,0)'
    style_header(rs, 18)
    rs.freeze_panes = "A2"
    widths = {"A": 12, "B": 12, "C": 9, "D": 20, "E": 10, "F": 10,
              "G": 12, "H": 15, "I": 8, "J": 14, "K": 13, "L": 17,
              "M": 48, "N": 12, "O": 11, "P": 9, "Q": 9, "R": 10}
    for col, w in widths.items():
        rs.column_dimensions[col].width = w
    for r in range(2, last + 1):
        for col in (6, 7, 8, 9, 10, 11, 12):
            rs.cell(row=r, column=col).number_format = COUNT_FMT

    # ── shared group sheet (branch / channel / month) ────────────────
    def group_sheet(name, title, labels, key_letter, nrows, total=True):
        ws = wb.create_sheet(name)
        ws["A1"] = title
        ws["A1"].font = TITLE_FONT
        headers = ["Label", "Responses", "Promoters", "Passives",
                   "Detractors", "NPS", "Avg satisfaction",
                   "Avg product quality", "Avg price",
                   "Avg delivery speed", "Avg staff service",
                   "Avg store cleanliness"]
        for c, h in enumerate(headers, start=1):
            ws.cell(row=3, column=c, value=h)
        style_header(ws, 12, row=3)
        ws.freeze_panes = "A4"
        for i, label in enumerate(labels):
            r = 4 + i
            ws.cell(row=r, column=1, value=label)
            ws.cell(row=r, column=2).value = (
                f"=COUNTIFS(Responses!${key_letter}$2:${key_letter}"
                f"${last},$A{r})")
            ws.cell(row=r, column=3).value = (
                f"=SUMIFS(Responses!$P$2:$P${last},"
                f"Responses!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=4).value = (
                f"=SUMIFS(Responses!$Q$2:$Q${last},"
                f"Responses!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=5).value = (
                f"=SUMIFS(Responses!$R$2:$R${last},"
                f"Responses!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=6).value = (
                f"=IF(B{r}=0,0,100*(C{r}-E{r})/B{r})")
            ws.cell(row=r, column=6).number_format = NPS_FMT
            ws.cell(row=r, column=7).value = (
                f"=AVERAGEIFS(Responses!$G$2:$G${last},"
                f"Responses!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=7).number_format = AVG_FMT
            for j, (_key, _label, col) in enumerate(DRIVERS):
                ws.cell(row=r, column=8 + j).value = (
                    f"=AVERAGEIFS(Responses!${col}$2:${col}${last},"
                    f"Responses!${key_letter}$2:${key_letter}${last},"
                    f"$A{r})")
                ws.cell(row=r, column=8 + j).number_format = AVG_FMT
        t = 4 + nrows  # total row
        if total:
            ws.cell(row=t, column=1, value="TOTAL").font = Font(bold=True)
            ws.cell(row=t, column=2).value = f"=SUM(B4:B{t-1})"
            for col in (3, 4, 5):
                letter = "CDE"[col - 3]
                ws.cell(row=t, column=col).value = (
                    f"=SUM({letter}4:{letter}{t-1})")
            ws.cell(row=t, column=6).value = (
                f"=IF(B{t}=0,0,100*(C{t}-E{t})/B{t})")
            ws.cell(row=t, column=6).number_format = NPS_FMT
            ws.cell(row=t, column=7).value = (
                f"=AVERAGE(Responses!G2:G{last})")
            ws.cell(row=t, column=7).number_format = AVG_FMT
            for j, (_key, _label, col) in enumerate(DRIVERS):
                ws.cell(row=t, column=8 + j).value = (
                    f"=AVERAGE(Responses!{col}2:{col}{last})")
                ws.cell(row=t, column=8 + j).number_format = AVG_FMT
        for col, w in zip("ABCDEFGHIJKL",
                          [22, 10, 10, 9, 10, 9, 14, 16, 10, 15, 14, 18]):
            ws.column_dimensions[col].width = w
        return ws

    group_sheet("By Branch",
                "NPS by branch — live formulas over Responses",
                BRANCHES, "D", len(BRANCHES))
    group_sheet("By Channel",
                "NPS by channel — live formulas over Responses",
                CHANNELS, "E", len(CHANNELS))
    mo = group_sheet("Monthly Trend",
                     "Monthly NPS trend — live formulas over Responses",
                     MONTHS, "C", len(MONTHS))
    # month-on-month NPS change on the Monthly Trend sheet (col M)
    mo.cell(row=3, column=13, value="NPS change (pts)")
    style_header(mo, 13, row=3)
    mo.cell(row=4, column=13, value="—")
    for r in range(5, 10):
        mo.cell(row=r, column=13).value = f"=F{r}-F{r-1}"
        mo.cell(row=r, column=13).number_format = NPS_FMT
    mo.column_dimensions["M"].width = 15

    # ── By Driver ────────────────────────────────────────────────────
    dr = wb.create_sheet("By Driver")
    dr["A1"] = ("What drives satisfaction? — live formulas over "
                "Responses; fix-first score = (5 - average rating) x "
                "correlation with overall satisfaction")
    dr["A1"].font = TITLE_FONT
    for c, h in enumerate(["Driver", "Avg rating (1–5)",
                           "Correlation with satisfaction",
                           "Gap to 5", "Fix-first score",
                           "Fix-first rank"], start=1):
        dr.cell(row=3, column=c, value=h)
    style_header(dr, 6, row=3)
    dr.freeze_panes = "A4"
    for i, (_key, label, col) in enumerate(DRIVERS):
        r = 4 + i
        dr.cell(row=r, column=1, value=label)
        dr.cell(row=r, column=2).value = (
            f"=AVERAGE(Responses!{col}2:{col}{last})")
        dr.cell(row=r, column=2).number_format = AVG_FMT
        dr.cell(row=r, column=3).value = (
            f"=CORREL(Responses!{col}2:{col}{last},"
            f"Responses!$G$2:$G${last})")
        dr.cell(row=r, column=3).number_format = AVG_FMT
        dr.cell(row=r, column=4).value = f"=5-B{r}"
        dr.cell(row=r, column=4).number_format = AVG_FMT
        dr.cell(row=r, column=5).value = f"=D{r}*C{r}"
        dr.cell(row=r, column=5).number_format = "0.000"
        dr.cell(row=r, column=6).value = (
            f"=RANK(E{r},$E$4:$E$8,0)")
    for col, w in zip("ABCDEF", [20, 15, 28, 10, 15, 14]):
        dr.column_dimensions[col].width = w

    # ── Dashboard ────────────────────────────────────────────────────
    dash = wb.create_sheet("Dashboard", 0)
    dash["A1"] = "Customer Feedback Survey Analysis — CityMart (SAMPLE)"
    dash["A1"].font = TITLE_FONT
    dash["A2"] = ("6 months, 2026-01-01 → 2026-06-30 · every number below "
                  "is a live formula over the Responses sheet — change "
                  "the data and the report rebuilds itself. NPS = "
                  "100 x (promoters - detractors) / responses; "
                  "Promoter = recommend 9–10, Passive = 7–8, "
                  "Detractor = 0–6; see the Method sheet.")
    dash["A2"].font = Font(italic=True, size=10, color="595959")
    dash["A4"] = "Key metrics"
    dash["A4"].font = Font(bold=True, size=12, color="1F4E79")
    kpis = [
        ("Total survey responses", f"=COUNTA(Responses!A2:A{last})",
         COUNT_FMT),
        ("NPS score", f"=IF(B5=0,0,100*(B7-B9)/B5)", NPS_FMT),
        ("Promoters (recommend 9–10)",
         f"=SUM(Responses!P2:P{last})", COUNT_FMT),
        ("Passives (recommend 7–8)",
         f"=SUM(Responses!Q2:Q{last})", COUNT_FMT),
        ("Detractors (recommend 0–6)",
         f"=SUM(Responses!R2:R{last})", COUNT_FMT),
        ("Promoter %", "=IF(B5=0,0,B7/B5)", PCT_FMT),
        ("Detractor %", "=IF(B5=0,0,B9/B5)", PCT_FMT),
        ("Average satisfaction (1–5)",
         f"=AVERAGE(Responses!G2:G{last})", AVG_FMT),
        ("Avg product quality (1–5)",
         f"=AVERAGE(Responses!H2:H{last})", AVG_FMT),
        ("Avg price (1–5)", f"=AVERAGE(Responses!I2:I{last})", AVG_FMT),
        ("Avg delivery speed (1–5)",
         f"=AVERAGE(Responses!J2:J{last})", AVG_FMT),
        ("Avg staff service (1–5)",
         f"=AVERAGE(Responses!K2:K{last})", AVG_FMT),
        ("Avg store cleanliness (1–5)",
         f"=AVERAGE(Responses!L2:L{last})", AVG_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(kpis):
        r = 5 + i
        dash.cell(row=r, column=1, value=label)
        c = dash.cell(row=r, column=2, value=formula)
        if fmt:
            c.number_format = fmt
        c.font = Font(bold=True)
    # KPI rows: 5 total, 6 NPS, 7 promoters, 8 passives, 9 detractors,
    # 10 promoter %, 11 detractor %, 12 avg sat, 13-17 driver avgs
    dash.cell(row=6, column=3).value = (
        "NPS = 100 x (promoters - detractors) / responses.")
    dash.cell(row=12, column=3).value = "Overall satisfaction, 1–5."
    dash.cell(row=15, column=3).value = (
        "Lowest-rated driver — and the one most tied to satisfaction.")
    # best / worst branch and channel by NPS
    dash.cell(row=18, column=1, value="Best branch (NPS)").font = Font(
        bold=True)
    dash.cell(row=18, column=2).value = (
        "=INDEX('By Branch'!A4:A6,MATCH(MAX('By Branch'!F4:F6),"
        "'By Branch'!F4:F6,0))")
    dash.cell(row=18, column=2).font = Font(bold=True)
    dash.cell(row=18, column=3).value = "=MAX('By Branch'!F4:F6)"
    dash.cell(row=18, column=3).number_format = NPS_FMT
    dash.cell(row=19, column=1, value="Worst branch (NPS)").font = Font(
        bold=True)
    dash.cell(row=19, column=2).value = (
        "=INDEX('By Branch'!A4:A6,MATCH(MIN('By Branch'!F4:F6),"
        "'By Branch'!F4:F6,0))")
    dash.cell(row=19, column=2).font = Font(bold=True)
    dash.cell(row=19, column=3).value = "=MIN('By Branch'!F4:F6)"
    dash.cell(row=19, column=3).number_format = NPS_FMT
    dash.cell(row=20, column=1, value="Best channel (NPS)").font = Font(
        bold=True)
    dash.cell(row=20, column=2).value = (
        "=INDEX('By Channel'!A4:A6,MATCH(MAX('By Channel'!F4:F6),"
        "'By Channel'!F4:F6,0))")
    dash.cell(row=20, column=2).font = Font(bold=True)
    dash.cell(row=20, column=3).value = "=MAX('By Channel'!F4:F6)"
    dash.cell(row=20, column=3).number_format = NPS_FMT
    dash.cell(row=21, column=1, value="Worst channel (NPS)").font = Font(
        bold=True)
    dash.cell(row=21, column=2).value = (
        "=INDEX('By Channel'!A4:A6,MATCH(MIN('By Channel'!F4:F6),"
        "'By Channel'!F4:F6,0))")
    dash.cell(row=21, column=2).font = Font(bold=True)
    dash.cell(row=21, column=3).value = "=MIN('By Channel'!F4:F6)"
    dash.cell(row=21, column=3).number_format = NPS_FMT
    dash.cell(row=22, column=1, value="Top fix-first driver").font = Font(
        bold=True)
    dash.cell(row=22, column=2).value = (
        "=INDEX('By Driver'!A4:A8,MATCH(MAX('By Driver'!E4:E8),"
        "'By Driver'!E4:E8,0))")
    dash.cell(row=22, column=2).font = Font(bold=True)
    dash.cell(row=22, column=3).value = "=MAX('By Driver'!E4:E8)"
    dash.cell(row=22, column=3).number_format = "0.000"

    # best / worst branch NPS among branches with 50+ responses
    # (MAXIFS/MINIFS written with the _xlfn. prefix)
    dash.cell(row=24, column=1,
             value="Best branch NPS (50+ responses)").font = Font(bold=True)
    dash.cell(row=24, column=2).value = (
        '=_xlfn.MAXIFS(\'By Branch\'!$F$4:$F$6,'
        '\'By Branch\'!$B$4:$B$6,">=50")')
    dash.cell(row=24, column=2).number_format = NPS_FMT
    dash.cell(row=24, column=3).value = (
        "=INDEX('By Branch'!$A$4:$A$6,MATCH(B24,'By Branch'!$F$4:$F$6,0))")
    dash.cell(row=25, column=1,
             value="Worst branch NPS (50+ responses)").font = Font(
                 bold=True)
    dash.cell(row=25, column=2).value = (
        '=_xlfn.MINIFS(\'By Branch\'!$F$4:$F$6,'
        '\'By Branch\'!$B$4:$B$6,">=50")')
    dash.cell(row=25, column=2).number_format = NPS_FMT
    dash.cell(row=25, column=3).value = (
        "=INDEX('By Branch'!$A$4:$A$6,MATCH(B25,'By Branch'!$F$4:$F$6,0))")
    dash.column_dimensions["A"].width = 32
    dash.column_dimensions["B"].width = 26
    dash.column_dimensions["C"].width = 14

    tr = 27  # monthly trend title row
    dash.cell(row=tr, column=1, value="Monthly NPS trend").font = Font(
        bold=True, size=12, color="1F4E79")
    headers = ["Month", "Responses", "NPS", "Avg satisfaction"]
    for c, h in enumerate(headers, start=1):
        dash.cell(row=tr + 1, column=c, value=h)
    style_header(dash, 4, row=tr + 1)
    for i, m in enumerate(MONTHS):
        r = tr + 2 + i  # rows 29..34
        dash.cell(row=r, column=1, value=m)
        dash.cell(row=r, column=2).value = (
            f"=COUNTIFS(Responses!$C$2:$C${last},$A{r})")
        dash.cell(row=r, column=3).value = (
            f"=IF(B{r}=0,0,100*(SUMIFS(Responses!$P$2:$P${last},"
            f"Responses!$C$2:$C${last},$A{r})-SUMIFS(Responses!$R$2:"
            f"$R${last},Responses!$C$2:$C${last},$A{r}))/B{r})")
        dash.cell(row=r, column=3).number_format = NPS_FMT
        dash.cell(row=r, column=4).value = (
            f"=AVERAGEIFS(Responses!$G$2:$G${last},"
            f"Responses!$C$2:$C${last},$A{r})")
        dash.cell(row=r, column=4).number_format = AVG_FMT
    t = tr + 2 + len(MONTHS)  # total row = 35
    dash.cell(row=t, column=1, value="TOTAL (6 months)").font = Font(
        bold=True)
    dash.cell(row=t, column=2).value = f"=SUM(B{tr+2}:B{t-1})"
    dash.cell(row=t, column=3).value = (
        f"=IF(B{t}=0,0,100*(SUM(Responses!P2:P{last})"
        f"-SUM(Responses!R2:R{last}))/B{t})")
    dash.cell(row=t, column=3).number_format = NPS_FMT
    dash.cell(row=t, column=4).value = f"=AVERAGE(Responses!G2:G{last})"
    dash.cell(row=t, column=4).number_format = AVG_FMT
    for col, w in zip("ABCD", [12, 10, 12, 15]):
        dash.column_dimensions[col].width = w

    chart = BarChart()
    chart.type = "col"
    chart.title = "NPS by month"
    chart.y_axis.title = "NPS"
    chart.x_axis.title = "Month"
    chart.data = Reference(dash, min_col=3, min_row=tr + 1, max_row=t - 1)
    chart.categories = Reference(dash, min_col=1, min_row=tr + 2,
                                 max_row=t - 1)
    chart.height, chart.width = 7.5, 15
    dash.add_chart(chart, f"A{t + 2}")

    # ── Method ─────────────────────────────────────────────────────────
    m = wb.create_sheet("Method")
    m["A1"] = "How this report is built"
    m["A1"].font = TITLE_FONT
    lines = [
        ("What this is", "A customer feedback survey analysis for "
         "CityMart, a fictional Pakistani retail buyer. 6 months, "
         "2026-01-01 → 2026-06-30, 181 days, 350 survey responses, "
         "3 branches, 3 channels, 5 satisfaction drivers."),
        ("Data", f"SAMPLE: {n:,} survey responses. Generated by "
         "src/generate_data.py (seed 20261116). Demo data, never "
         "claimed as real client work. Each branch was given a fixed "
         "behaviour profile (Lahore — Gulberg the strong branch, "
         "Rawalpindi — Saddar the weak one on delivery and staff "
         "service) and each channel its own small effect, so the "
         "report has a real branch story and a real channel story to "
         "find."),
        ("NPS", "Every respondent answers 'How likely are you to "
         "recommend us?' on a 0–10 scale. Promoter = 9–10, Passive = "
         "7–8, Detractor = 0–6. NPS = 100 x (promoters - detractors) "
         "/ responses, so it runs from -100 to +100. NPS is a "
         "recommendation score, not a satisfaction score — a customer "
         "can be fairly satisfied (3/5) and still be a detractor, "
         "because 0–6 all count as 'would not recommend'."),
        ("Satisfaction", "Overall satisfaction and the five drivers "
         "(product quality, price, delivery speed, staff service, "
         "store cleanliness) are each rated 1–5. Averages are plain "
         "means over the responses in the group shown."),
        ("Driver correlation", "The Pearson correlation between each "
         "driver's 1–5 rating and overall satisfaction, computed "
         "with numpy in src/analyze.py and with the CORREL function "
         "in this workbook — the two must agree. Correlation is "
         "measured on the same 350 responses, so it shows which "
         "drivers move with satisfaction in this survey, not which "
         "ones cause it."),
        ("Fix-first score", "Fix-first score = (5 - average driver "
         "rating) x correlation with overall satisfaction. A driver "
         "ranks high only if it is BOTH low-rated (room to improve) "
         "AND strongly tied to satisfaction (improving it matters). "
         "Fixing the top driver first is a judgement about where "
         "effort pays most — it is not a promise that the score "
         "will rise by that amount."),
        ("Comments", "Each response carries one open-text comment "
         "drawn from a fixed phrase bank (6 promoter phrases, 5 "
         "passive, 6 detractor), chosen by the respondent's NPS "
         "segment. Themes are counted from the phrase tags "
         "(delivery, price, staff, stock, cleanliness, quality, "
         "overall) — no free text is invented beyond the bank."),
        ("Limits", "NPS from 350 responses is a survey estimate, "
         "not a census: a branch with 74 responses has a wider "
         "margin of error than one with 146, and the workbook shows "
         "the response count next to every share. Ratings are "
         "self-reported — a 4/5 from one customer is not the same "
         "experience as a 4/5 from another. The fix-first ranking "
         "assumes drivers can be improved independently; in practice "
         "fixing delivery may also lift staff scores, or neither."),
        ("Live formulas", "Every KPI, branch, channel, driver and "
         "month number is a live COUNTIFS / SUMIFS / AVERAGEIFS / "
         "CORREL / RANK formula over the Responses sheet — paste a "
         "real survey export in the same columns and the report "
         "rebuilds itself. The Responses sheet's derived columns "
         "(NPS segment, promoter/passive/detractor flags) are "
         "formulas too."),
        ("MAXIFS / MINIFS", "Best and worst branch NPS among branches "
         "with 50+ responses on the Dashboard use MAXIFS and MINIFS, "
         "written with the _xlfn. prefix (=_xlfn.MAXIFS(...)) so "
         "LibreOffice and Excel calculate them — the plain form "
         "shows #NAME? in LibreOffice."),
        ("Check it", "Every number here is recomputed from the raw "
         "CSV by src/analyze.py and verified by src/checks.py — run "
         "it: python3 src/checks.py"),
        ("Same logic, two ways", "The headline KPIs, the branch, "
         "channel, driver and monthly totals exist in two forms that "
         "must agree: the Python in src/analyze.py and this "
         "workbook's formulas. src/checks.py verifies both against "
         "the raw file, including a LibreOffice recalc."),
    ]
    r = 3
    for title, text in lines:
        m.cell(row=r, column=1, value=title).font = Font(bold=True)
        m.cell(row=r, column=2, value=text)
        m.cell(row=r, column=2).alignment = Alignment(wrap_text=True,
                                                      vertical="top")
        r += 1
    m.column_dimensions["A"].width = 22
    m.column_dimensions["B"].width = 110

    wb._sheets = [wb[n] for n in
                  ["Dashboard", "Responses", "By Branch", "By Channel",
                   "By Driver", "Monthly Trend", "Method"]]
    wb.save(OUT)
    print(f"wrote {OUT.name}: sheets {wb.sheetnames}")


if __name__ == "__main__":
    main()
