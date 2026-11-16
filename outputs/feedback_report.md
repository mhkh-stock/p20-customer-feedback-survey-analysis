# P20 — Customer Feedback Survey Analysis: CityMart (SAMPLE)

**Period:** Thu 2026-01-01 → Tue 2026-06-30 (6 months, 181 days)
**Survey responses:** 350 · **NPS:** 16.29 · **Promoters:** 138 (39.43%) · **Passives:** 131 · **Detractors:** 81 (23.14%) · **Average satisfaction:** 4.03/5

## 1. The headline — would customers recommend CityMart?

Of 350 customers surveyed, 138 would recommend the store (score 9–10) and 81 would not (score 0–6), giving an **NPS of 16.29**. Average satisfaction is **4.03/5**. The gap between branches is the story: **Lahore — Gulberg scores NPS 34.62** while **Rawalpindi — Saddar scores 4.05** — a 30.57-point gap on the same survey. By channel, **In-store is best (NPS 23.26)** and **Online is worst (NPS 8.18)**.

## 2. NPS by branch

| Branch | Responses | Promoters | Passives | Detractors | NPS | Avg satisfaction |
|---|---|---|---|---|---|---|
| Lahore — Gulberg | 130 | 66 | 43 | 21 | 34.62 | 4.25 |
| Karachi — Clifton | 146 | 49 | 57 | 40 | 6.16 | 3.99 |
| Rawalpindi — Saddar | 74 | 23 | 31 | 20 | 4.05 | 3.73 |

## 3. NPS by channel

| Channel | Responses | Promoters | Passives | Detractors | NPS | Avg satisfaction |
|---|---|---|---|---|---|---|
| In-store | 172 | 73 | 66 | 33 | 23.26 | 4.12 |
| Phone | 68 | 24 | 28 | 16 | 11.76 | 4.0 |
| Online | 110 | 41 | 37 | 32 | 8.18 | 3.9 |

## 4. What drives satisfaction? (drivers, 1–5)

| Driver | Avg rating | Correlation with satisfaction | Gap to 5 | Fix-first score | Rank |
|---|---|---|---|---|---|
| Delivery speed | 3.84 | 0.725 | 1.16 | 0.843 | 1 |
| Product quality | 4.02 | 0.677 | 0.98 | 0.662 | 2 |
| Price | 3.99 | 0.652 | 1.01 | 0.661 | 3 |
| Store cleanliness | 3.99 | 0.641 | 1.01 | 0.646 | 4 |
| Staff service | 4.06 | 0.688 | 0.94 | 0.644 | 5 |

**Fix-first driver: Delivery speed** (3.84/5, correlation 0.725, fix-first score 0.843) — the lowest-rated driver and the one most tied to overall satisfaction. Next: **Product quality** (0.662) and **Price** (0.661). Correlations are Pearson, computed with numpy from the raw responses.

## 5. What the detractors say (comment-bank themes)

| Theme | Detractors mentioning it | Share of detractors |
|---|---|---|
| stock | 18 | 22.22% |
| price | 16 | 19.75% |
| staff | 16 | 19.75% |
| quality | 15 | 18.52% |
| delivery | 9 | 11.11% |
| cleanliness | 7 | 8.64% |
| overall | 0 | 0.0% |

**Most common detractor theme: stock** (18 of 81 detractors, 22.22%). Comments come from a fixed phrase bank only — one phrase per response, chosen by NPS segment — so themes are counted from the bank tags, never invented free text.

## 6. Month by month

| Month | Responses | Promoters | Detractors | NPS | Avg satisfaction | NPS change (pts) |
|---|---|---|---|---|---|---|
| 2026-01 | 49 | 11 | 13 | -4.08 | 3.86 | — |
| 2026-02 | 47 | 24 | 8 | 34.04 | 4.04 | +38.12 |
| 2026-03 | 65 | 30 | 14 | 24.62 | 4.14 | -9.42 |
| 2026-04 | 54 | 24 | 11 | 24.07 | 4.07 | -0.55 |
| 2026-05 | 74 | 22 | 23 | -1.35 | 3.92 | -25.42 |
| 2026-06 | 61 | 27 | 12 | 24.59 | 4.13 | +25.94 |

NPS moved **+28.67 points from January (-4.08) to June (24.59)**. Best month: **2026-02 (NPS 34.04)**; worst: **2026-01 (NPS -4.08)**.

## 7. Three recommendations

1. **Fix delivery speed first.** Delivery speed is the lowest-rated driver at 3.84/5 and the most strongly tied to overall satisfaction (correlation 0.725) — fix-first score 0.843, the highest of the five drivers. It is worst at Rawalpindi — Saddar (3.3/5) and in the online channel. Start with delivery promises at that branch before spending on anything else.
2. **Close the gap between Lahore — Gulberg and Rawalpindi — Saddar.** Lahore — Gulberg scores NPS 34.62 on 130 responses; Rawalpindi — Saddar scores 4.05 on 74 — a 30.57-point gap. Every driver is lower at Rawalpindi — Saddar, so copy what Lahore — Gulberg does on staffing and stock before opening a new branch.
3. **Stop the stock-outs behind the detractors.** 18 of the 81 detractors mention stock (22.22% of all detractors) — the most common detractor theme. Detractors are 23.14% of all responses, and each one is a customer who will not recommend the store. Fix availability of the items customers keep asking for first.

> Every number in this report is recomputed from `data/raw/survey_responses_SAMPLE.csv` by `src/analyze.py` — nothing is typed by hand. Run `python3 src/checks.py` to re-verify.
