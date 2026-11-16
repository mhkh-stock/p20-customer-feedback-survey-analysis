# P20 — Customer Feedback Survey Analysis

**Client (SAMPLE):** CityMart — fictional Pakistani retail buyer,
6 months (Thu 2026-01-01 → Tue 2026-06-30, 181 days) ·
**Status: SAMPLE delivery on DEMO data**
**Repo:** https://github.com/mhkh-stock/p20-customer-feedback-survey-analysis
**Tools:** Python · Excel (live formulas) · reportlab
**Deliverable:** `outputs/feedback_report.pdf` (2 pages) +
`outputs/customer_feedback_report_SAMPLE.xlsx`

> ⚠️ **What this is and is not.** The survey file is a fictional
> buyer's demo data, generated to show the method. No real buyer,
> branch or customer is involved. What is real is the analysis: the
> same NPS, driver and theme cross-tabs and workbook run on a real
> client's survey export the same way, and every number in the
> report is recomputed from the data, never typed.

## Business question it answers

> "Would our customers recommend us — and what should we fix first?"

A store that only watches its average satisfaction cannot tell
whether its customers would actually recommend it, or which of the
five things it does — quality, price, delivery, staff, cleanliness
— is holding that recommendation back. This delivery answers it
from the survey: the NPS overall, by branch and by channel, which
driver matters most to satisfaction, what the detractors actually
complain about, and the month-by-month trend — with the fix-first
driver named, not guessed.

## The method (plainly stated)

Every respondent answers "How likely are you to recommend us?" on
a 0–10 scale:

| Segment | Recommend score | What it means |
|---|---|---|
| Promoter | 9–10 | Would recommend the store |
| Passive | 7–8 | Satisfied but not enthusiastic |
| Detractor | 0–6 | Would not recommend the store |

**NPS = 100 × (promoters − detractors) / responses**, so it runs
from −100 to +100. NPS is a recommendation score, not a
satisfaction score — a customer can be fairly satisfied (3/5) and
still be a detractor, because 0–6 all count as "would not
recommend".

**Drivers:** overall satisfaction and five drivers (product
quality, price, delivery speed, staff service, store cleanliness)
are each rated 1–5. Each driver's Pearson correlation with overall
satisfaction is computed with numpy (and with CORREL in the
workbook — the two must agree).

**Fix-first score = (5 − average driver rating) × correlation with
overall satisfaction.** A driver ranks high only if it is BOTH
low-rated (room to improve) AND strongly tied to satisfaction
(improving it matters). Fixing the top driver first is a judgement
about where effort pays most — not a promise the score will rise
by that amount.

**Comments:** each response carries one open-text comment drawn
from a fixed phrase bank (6 promoter phrases, 5 passive, 6
detractor), chosen by the respondent's NPS segment. Themes are
counted from the phrase tags (delivery, price, staff, stock,
cleanliness, quality, overall) — no free text is invented beyond
the bank.

**Limits, stated upfront:** NPS from 350 responses is a survey
estimate, not a census — a branch with 74 responses has a wider
margin of error than one with 146, and the workbook shows the
response count next to every share. Ratings are self-reported — a
4/5 from one customer is not the same experience as a 4/5 from
another. Correlations show which drivers move with satisfaction in
this survey, not which ones cause it. The fix-first ranking assumes
drivers can be improved independently; in practice fixing delivery
may also lift staff scores, or neither.

## What is inside

| File | What it does |
|---|---|
| `outputs/feedback_report.pdf` | The deliverable: 2-page client report — headline, branch and channel NPS, driver table, detractor themes, monthly trend, 3 recommendations |
| `outputs/customer_feedback_report_SAMPLE.xlsx` | The working report: Dashboard (KPIs + monthly NPS trend, live formulas) + Responses + By Branch + By Channel + By Driver + Monthly Trend + Method sheets |
| `outputs/feedback_report.md` | Findings report: headline numbers, all tables, the reasoning |
| `outputs/summary.json` | Machine-readable summary (overall KPIs + branches + channels + drivers + months + themes + actions) |
| `outputs/monthly_nps.png` | Monthly NPS trend chart (render of the same data) |
| `outputs/driver_ratings.png` | Driver average ratings, ranked by fix-first score (render of the same data) |
| `data/raw/survey_responses_SAMPLE.csv` | The survey file: 350 responses, branch + channel + recommend + satisfaction + 5 drivers + comment + theme |
| `data/processed/survey_responses_enriched.csv` | All 350 responses with the derived columns attached (NPS segment, promoter/passive/detractor flags) |
| `data/processed/branch_summary.csv` | 3-row branch summary produced by `src/analyze.py` |
| `data/processed/channel_summary.csv` | 3-row channel summary produced by `src/analyze.py` |
| `data/processed/driver_summary.csv` | 5-row driver summary (average, correlation, gap, fix-first score, rank) produced by `src/analyze.py` |
| `data/processed/monthly_summary.csv` | 6-month summary produced by `src/analyze.py` |
| `data/README.md` | Data dictionary + known quirks |
| `src/generate_data.py` | Makes the demo file (seeded; NOT run on a real client file) |
| `src/analyze.py` | Recomputes every headline number from the raw CSV |
| `src/build_workbook.py` | Builds the workbook: 7 sheets, live formulas |
| `src/build_report.py` | Builds the 2-page PDF + charts from `outputs/summary.json` |
| `src/checks.py` | Data-quality + reconciliation checks as code — 218 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2`, `reportlab==5.0.1`, `matplotlib==3.6.3` (Python 3.12) |

## How it fits together

```
Client survey export (same columns) ──▶ src/analyze.py ──▶ summary.json
        (350 rows in the demo)                + feedback_report.md
                                                 ▼
                                       src/build_workbook.py ──▶ customer_feedback_report_SAMPLE.xlsx
                                                 │              (7 sheets, live formulas)
                                                 ▼
                                       src/build_report.py ──▶ feedback_report.pdf (2 pages)
                                                 ▲ src/checks.py verifies all of it (218 checks)
```

## Headline numbers (SAMPLE — CityMart, 6 months)

- **350 survey responses** · **NPS 16.29** · **138 promoters
  (39.43%), 131 passives, 81 detractors (23.14%)** · **average
  satisfaction 4.03/5**
- **Best branch: Lahore — Gulberg (NPS 34.62, 130 responses)**;
  worst: **Rawalpindi — Saddar (NPS 4.05, 74 responses)** — a
  30.57-point gap
- **Best channel: In-store (NPS 23.26)**; worst: **Online (NPS
  8.18)**
- **Fix-first driver: Delivery speed (3.84/5, correlation 0.725,
  fix-first score 0.843)** — the lowest-rated driver and the one
  most tied to overall satisfaction
- **Most common detractor theme: stock (18 of 81 detractors,
  22.22%)**
- **NPS rose +28.67 points from January (−4.08) to June (24.59)**
  — but May dipped to −1.35, breaking the climb

## NPS by branch

| Branch | Responses | Promoters | Passives | Detractors | NPS | Avg satisfaction |
|---|---|---|---|---|---|---|
| Lahore — Gulberg | 130 | 66 | 43 | 21 | 34.62 | 4.25 |
| Karachi — Clifton | 146 | 49 | 57 | 40 | 6.16 | 3.99 |
| Rawalpindi — Saddar | 74 | 23 | 31 | 20 | 4.05 | 3.73 |

The gap is the story: Lahore would be recommended by half its
customers (66 promoters against 21 detractors), while Rawalpindi
barely breaks even (23 against 20). Every driver is lower at
Rawalpindi — delivery speed most of all (3.30/5 against 4.18/5).

## NPS by channel

| Channel | Responses | Promoters | Passives | Detractors | NPS | Avg satisfaction |
|---|---|---|---|---|---|---|
| In-store | 172 | 73 | 66 | 33 | 23.26 | 4.12 |
| Phone | 68 | 24 | 28 | 16 | 11.76 | 4.00 |
| Online | 110 | 41 | 37 | 32 | 8.18 | 3.90 |

Online is the weakest channel — the same delivery problem, felt
most by customers who never set foot in the store.

## What drives satisfaction? (drivers, 1–5)

| Driver | Avg rating | Correlation with satisfaction | Gap to 5 | Fix-first score | Rank |
|---|---|---|---|---|---|
| Delivery speed | 3.84 | 0.725 | 1.16 | 0.843 | 1 |
| Product quality | 4.02 | 0.677 | 0.98 | 0.662 | 2 |
| Price | 3.99 | 0.652 | 1.01 | 0.661 | 3 |
| Store cleanliness | 3.99 | 0.641 | 1.01 | 0.646 | 4 |
| Staff service | 4.06 | 0.688 | 0.94 | 0.644 | 5 |

Delivery speed wins the fix-first ranking on both halves of the
formula: it is the lowest-rated driver (3.84/5) and the most
strongly correlated with overall satisfaction (0.725). Staff
service is the highest-rated driver (4.06/5), so even though it
correlates well (0.688), there is little room left to gain there —
it ranks last on fix-first, not because staff do not matter, but
because they are already doing well.

## What the detractors say (comment-bank themes)

| Theme | Detractors mentioning it | Share of detractors |
|---|---|---|
| stock | 18 | 22.22% |
| price | 16 | 19.75% |
| staff | 16 | 19.75% |
| quality | 15 | 18.52% |
| delivery | 9 | 11.11% |
| cleanliness | 7 | 8.64% |
| overall | 0 | 0.0% |

Stock-outs are the single most common detractor complaint — nearly
one detractor in four says the item they wanted was not there. Note
the split with the driver table: delivery is the fix-first driver
by the ratings, but stock is the top complaint in the words. Both
are true — the ratings say what moves satisfaction, the comments
say what detractors remember. Fix delivery first, then availability.

## Month by month

| Month | Responses | Promoters | Detractors | NPS | Avg satisfaction | NPS change (pts) |
|---|---|---|---|---|---|---|
| 2026-01 | 49 | 11 | 13 | -4.08 | 3.86 | — |
| 2026-02 | 47 | 24 | 8 | 34.04 | 4.04 | +38.12 |
| 2026-03 | 65 | 30 | 14 | 24.62 | 4.14 | -9.42 |
| 2026-04 | 54 | 24 | 11 | 24.07 | 4.07 | -0.55 |
| 2026-05 | 74 | 22 | 23 | -1.35 | 3.92 | -25.42 |
| 2026-06 | 61 | 27 | 12 | 24.59 | 4.13 | +25.94 |

NPS moved **+28.67 points from January (−4.08) to June (24.59)**.
February is the best month (34.04); January the worst (−4.08).
May breaks the climb — NPS falls 25.42 points in one month, on the
largest response count of the half year (74), so it is not a small
sample wobbling. The report shows the measured months, never a
smoothed trend line.

## The three recommendations (from the data, not from a template)

1. **Fix delivery speed first.** Delivery speed is the
   lowest-rated driver at 3.84/5 and the most strongly tied to
   overall satisfaction (correlation 0.725) — fix-first score
   0.843, the highest of the five drivers. It is worst at
   Rawalpindi — Saddar (3.3/5) and in the online channel. Start
   with delivery promises at that branch before spending on
   anything else.
2. **Close the gap between Lahore — Gulberg and Rawalpindi —
   Saddar.** Lahore — Gulberg scores NPS 34.62 on 130 responses;
   Rawalpindi — Saddar scores 4.05 on 74 — a 30.57-point gap.
   Every driver is lower at Rawalpindi — Saddar, so copy what
   Lahore — Gulberg does on staffing and stock before opening a
   new branch.
3. **Stop the stock-outs behind the detractors.** 18 of the 81
   detractors mention stock (22.22% of all detractors) — the most
   common detractor theme. Detractors are 23.14% of all responses,
   and each one is a customer who will not recommend the store.
   Fix availability of the items customers keep asking for first.

## Same logic, two ways — and they must agree

The headline KPIs, the branch, channel, driver and monthly totals
exist in two forms: the Python in `src/analyze.py` and this
workbook's formulas. `src/checks.py` runs both against the raw
file and compares them — a mistake in either one shows up as a
failure. The workbook's formulas were also recalculated in
LibreOffice (including the `_xlfn.MAXIFS` / `_xlfn.MINIFS` best /
worst branch NPS cells and the CORREL driver correlations): every
total matches the recompute exactly, with zero error values.

## Reproduce it (2 minutes)

```bash
python3 src/generate_data.py   # rebuild the SAMPLE file (seed 20261116)
python3 src/analyze.py         # summary.json + feedback_report.md
python3 src/build_workbook.py  # outputs/customer_feedback_report_SAMPLE.xlsx
python3 src/build_report.py    # outputs/feedback_report.pdf (2 pages)
python3 src/checks.py          # 218 checks — expect all passing
```

On a real client file, replace `data/raw/survey_responses_SAMPLE.csv`
with the survey export (same columns) and skip
`generate_data.py` — everything downstream runs unchanged.
