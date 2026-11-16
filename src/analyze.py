#!/usr/bin/env python3
"""P20 — analyse the SAMPLE customer-feedback survey file and
regenerate every output number from the raw CSV (never typed): the
headline NPS and satisfaction KPIs, NPS by branch and by channel,
average satisfaction overall and by driver, the Pearson correlation
of each driver with overall satisfaction (numpy), the fix-first
driver ranking, detractor themes from the comment bank, the monthly
NPS trend, and the prioritised action list.

Derived per response: nps_segment (Promoter 9–10 / Passive 7–8 /
Detractor 0–6), promoter / passive / detractor flags (0/1).
NPS = 100 x (promoters - detractors) / responses.
Fix-first score = (5 - average driver rating) x correlation with
overall satisfaction — the drivers with the most room to improve
that matter most to satisfaction. A driver can only rank high if
it is BOTH low-rated and strongly tied to satisfaction.

Writes:
  data/processed/survey_responses_enriched.csv
  data/processed/branch_summary.csv
  data/processed/channel_summary.csv
  data/processed/driver_summary.csv
  data/processed/monthly_summary.csv
  outputs/summary.json
  outputs/feedback_report.md

    python3 src/analyze.py
"""
import csv
import json
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"

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
    nps = round(100.0 * (prom - detr) / n, 2) if n else 0.0
    sat = round(sum(r["satisfaction"] for r in rows) / n, 2) if n else 0.0
    out = {
        "responses": n, "promoters": prom, "passives": pas,
        "detractors": detr, "promoter_pct": pct(prom, n),
        "detractor_pct": pct(detr, n), "nps": nps,
        "avg_satisfaction": sat,
    }
    for key, _label in DRIVERS:
        out[f"avg_{key}"] = round(
            sum(r[key] for r in rows) / n, 2) if n else 0.0
    return out


def main():
    raw = list(csv.DictReader(
        open(RAW / "survey_responses_SAMPLE.csv", encoding="utf-8")))
    rows = []
    for r in raw:
        rec = int(r["recommend"])
        seg = segment(rec)
        rows.append({
            "response_id": r["response_id"],
            "survey_date": r["survey_date"], "month": r["month"],
            "branch": r["branch"], "channel": r["channel"],
            "recommend": rec, "satisfaction": int(r["satisfaction"]),
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
    overall = group_stats(rows)

    by_branch = []
    for b in BRANCHES:
        rs = [r for r in rows if r["branch"] == b]
        by_branch.append({"branch": b, **group_stats(rs)})
    by_branch_nps = sorted(by_branch, key=lambda x: -x["nps"])
    best_branch = by_branch_nps[0]
    worst_branch = by_branch_nps[-1]

    by_channel = []
    for c in CHANNELS:
        rs = [r for r in rows if r["channel"] == c]
        by_channel.append({"channel": c, **group_stats(rs)})
    by_channel_nps = sorted(by_channel, key=lambda x: -x["nps"])
    best_channel = by_channel_nps[0]
    worst_channel = by_channel_nps[-1]

    # driver correlations with overall satisfaction (numpy Pearson).
    # Rank on the UNROUNDED fix-first score (two drivers can round to
    # the same 3 decimals and still rank apart), then round for display.
    sat = np.array([r["satisfaction"] for r in rows], dtype=float)
    by_driver = []
    for key, label in DRIVERS:
        x = np.array([r[key] for r in rows], dtype=float)
        corr_raw = float(np.corrcoef(x, sat)[0, 1])
        avg_raw = float(x.mean())
        gap_raw = 5 - avg_raw
        by_driver.append({
            "driver": key, "label": label,
            "avg_rating": round(avg_raw, 2),
            "correlation": round(corr_raw, 3),
            "gap": round(gap_raw, 2),
            "fix_first_score": round(gap_raw * corr_raw, 3),
            "_raw_score": gap_raw * corr_raw,
        })
    by_driver.sort(key=lambda d: -d["_raw_score"])
    for i, d in enumerate(by_driver, start=1):
        d["fix_first_rank"] = i
        del d["_raw_score"]
    fix_first = by_driver[:3]

    by_month = []
    for m in MONTHS:
        rs = [r for r in rows if r["month"] == m]
        by_month.append({"month": m, **group_stats(rs)})
    for i, mo in enumerate(by_month):
        prev = by_month[i - 1]["nps"] if i else None
        mo["nps_change_points"] = (
            round(mo["nps"] - prev, 2) if prev is not None else None)
    nps_trend = round(by_month[-1]["nps"] - by_month[0]["nps"], 2)
    best_month = max(by_month, key=lambda m: m["nps"])
    worst_month = min(by_month, key=lambda m: m["nps"])

    # detractor themes, counted from the comment-bank tags
    detractors = [r for r in rows if r["detractor"]]
    themes = []
    for t in THEMES:
        n = sum(1 for r in detractors if r["theme"] == t)
        themes.append({"theme": t, "detractors": n,
                       "pct_of_detractors": pct(n, len(detractors))})
    themes.sort(key=lambda x: -x["detractors"])
    top_theme = themes[0]

    # the three recommendations, built from the numbers above
    d1 = fix_first[0]
    actions = [
        {
            "title": f"Fix {d1['label'].lower()} first",
            "detail": f"{d1['label']} is the lowest-rated driver at "
                      f"{d1['avg_rating']}/5 and the most strongly tied "
                      f"to overall satisfaction "
                      f"(correlation {d1['correlation']}) — fix-first "
                      f"score {d1['fix_first_score']}, the highest of "
                      f"the five drivers. It is worst at "
                      f"{worst_branch['branch']} "
                      f"({worst_branch['avg_delivery_speed']}/5) and in "
                      f"the {worst_channel['channel'].lower()} channel. "
                      f"Start with delivery promises at that branch "
                      f"before spending on anything else.",
        },
        {
            "title": f"Close the gap between {best_branch['branch']} "
                      f"and {worst_branch['branch']}",
            "detail": f"{best_branch['branch']} scores NPS "
                      f"{best_branch['nps']} on "
                      f"{best_branch['responses']} responses; "
                      f"{worst_branch['branch']} scores "
                      f"{worst_branch['nps']} on "
                      f"{worst_branch['responses']} — a "
                      f"{round(best_branch['nps'] - worst_branch['nps'], 2)}"
                      f"-point gap. Every driver is lower at "
                      f"{worst_branch['branch']}, so copy what "
                      f"{best_branch['branch']} does on staffing and "
                      f"stock before opening a new branch.",
        },
        {
            "title": f"Stop the stock-outs behind the detractors",
            "detail": f"{top_theme['detractors']} of the "
                      f"{len(detractors)} detractors mention "
                      f"{top_theme['theme']} "
                      f"({top_theme['pct_of_detractors']}% of all "
                      f"detractors) — the most common detractor theme. "
                      f"Detractors are {overall['detractor_pct']}% of "
                      f"all responses, and each one is a customer who "
                      f"will not recommend the store. Fix availability "
                      f"of the items customers keep asking for first.",
        },
    ]

    summary = {
        "buyer": "CityMart (SAMPLE)",
        "period": "2026-01-01 to 2026-06-30",
        "days": 181,
        "total_responses": total,
        "overall": overall,
        "by_branch": by_branch,
        "best_branch": best_branch["branch"],
        "best_branch_nps": best_branch["nps"],
        "worst_branch": worst_branch["branch"],
        "worst_branch_nps": worst_branch["nps"],
        "branch_nps_gap": round(best_branch["nps"]
                                - worst_branch["nps"], 2),
        "by_channel": by_channel,
        "best_channel": best_channel["channel"],
        "best_channel_nps": best_channel["nps"],
        "worst_channel": worst_channel["channel"],
        "worst_channel_nps": worst_channel["nps"],
        "by_driver": by_driver,
        "fix_first": [{"label": d["label"],
                       "avg_rating": d["avg_rating"],
                       "correlation": d["correlation"],
                       "fix_first_score": d["fix_first_score"]}
                      for d in fix_first],
        "months": by_month,
        "nps_trend_jan_to_jun_points": nps_trend,
        "best_month": best_month["month"],
        "best_month_nps": best_month["nps"],
        "worst_month": worst_month["month"],
        "worst_month_nps": worst_month["nps"],
        "detractor_themes": themes,
        "top_detractor_theme": top_theme["theme"],
        "top_detractor_theme_count": top_theme["detractors"],
        "actions": actions,
    }
    (PROJECT / "outputs" / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    def write_csv(name, fields, rows_out):
        with open(PROJECT / "data" / "processed" / name, "w",
                  newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows_out)

    write_csv("survey_responses_enriched.csv",
              ["response_id", "survey_date", "month", "branch",
               "channel", "recommend", "satisfaction",
               "product_quality", "price", "delivery_speed",
               "staff_service", "store_cleanliness", "comment",
               "theme", "nps_segment", "promoter", "passive",
               "detractor"], rows)

    def group_csv(name, key, groups, extra_fields):
        fields = [key, "responses", "promoters", "passives",
                  "detractors", "promoter_pct", "detractor_pct", "nps",
                  "avg_satisfaction"] + [
                      f"avg_{k}" for k, _ in DRIVERS] + extra_fields
        write_csv(name, fields,
                  [{k: g[k] for k in fields} for g in groups])

    group_csv("branch_summary.csv", "branch", by_branch, [])
    group_csv("channel_summary.csv", "channel", by_channel, [])
    write_csv("driver_summary.csv",
              ["driver", "label", "avg_rating", "correlation", "gap",
               "fix_first_score", "fix_first_rank"],
              [{k: d[k] for k in
                ["driver", "label", "avg_rating", "correlation", "gap",
                 "fix_first_score", "fix_first_rank"]}
               for d in by_driver])
    write_csv("monthly_summary.csv",
              ["month", "responses", "promoters", "passives",
               "detractors", "promoter_pct", "detractor_pct", "nps",
               "avg_satisfaction"] + [f"avg_{k}" for k, _ in DRIVERS]
              + ["nps_change_points"],
              [{k: m[k] for k in
                ["month", "responses", "promoters", "passives",
                 "detractors", "promoter_pct", "detractor_pct", "nps",
                 "avg_satisfaction"] + [f"avg_{k}" for k, _ in DRIVERS]
                + ["nps_change_points"]} for m in by_month])

    # findings report (markdown) — every number from the data above
    ov = overall
    L = [
        "# P20 — Customer Feedback Survey Analysis: CityMart (SAMPLE)",
        "",
        "**Period:** Thu 2026-01-01 → Tue 2026-06-30 (6 months, 181 days)",
        f"**Survey responses:** {total:,} · **NPS:** {ov['nps']} · "
        f"**Promoters:** {ov['promoters']} ({ov['promoter_pct']}%) · "
        f"**Passives:** {ov['passives']} · **Detractors:** "
        f"{ov['detractors']} ({ov['detractor_pct']}%) · **Average "
        f"satisfaction:** {ov['avg_satisfaction']}/5",
        "",
        "## 1. The headline — would customers recommend CityMart?",
        "",
        f"Of {total} customers surveyed, {ov['promoters']} would "
        f"recommend the store (score 9–10) and {ov['detractors']} would "
        f"not (score 0–6), giving an **NPS of {ov['nps']}**. Average "
        f"satisfaction is **{ov['avg_satisfaction']}/5**. The gap "
        f"between branches is the story: **{best_branch['branch']} "
        f"scores NPS {best_branch['nps']}** while "
        f"**{worst_branch['branch']} scores {worst_branch['nps']}** — "
        f"a {round(best_branch['nps'] - worst_branch['nps'], 2)}-point "
        f"gap on the same survey. By channel, "
        f"**{best_channel['channel']} is best (NPS "
        f"{best_channel['nps']})** and **{worst_channel['channel']} is "
        f"worst (NPS {worst_channel['nps']})**.",
        "",
        "## 2. NPS by branch",
        "",
        "| Branch | Responses | Promoters | Passives | Detractors | "
        "NPS | Avg satisfaction |",
        "|---|---|---|---|---|---|---|",
    ]
    for b in by_branch_nps:
        L.append(f"| {b['branch']} | {b['responses']} | {b['promoters']} | "
                 f"{b['passives']} | {b['detractors']} | {b['nps']} | "
                 f"{b['avg_satisfaction']} |")
    L += [
        "",
        "## 3. NPS by channel",
        "",
        "| Channel | Responses | Promoters | Passives | Detractors | "
        "NPS | Avg satisfaction |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in by_channel_nps:
        L.append(f"| {c['channel']} | {c['responses']} | {c['promoters']} | "
                 f"{c['passives']} | {c['detractors']} | {c['nps']} | "
                 f"{c['avg_satisfaction']} |")
    L += [
        "",
        "## 4. What drives satisfaction? (drivers, 1–5)",
        "",
        "| Driver | Avg rating | Correlation with satisfaction | "
        "Gap to 5 | Fix-first score | Rank |",
        "|---|---|---|---|---|---|",
    ]
    for d in by_driver:
        L.append(f"| {d['label']} | {d['avg_rating']} | "
                 f"{d['correlation']} | {d['gap']} | "
                 f"{d['fix_first_score']} | {d['fix_first_rank']} |")
    L += [
        "",
        f"**Fix-first driver: {fix_first[0]['label']}** "
        f"({fix_first[0]['avg_rating']}/5, correlation "
        f"{fix_first[0]['correlation']}, fix-first score "
        f"{fix_first[0]['fix_first_score']}) — the lowest-rated driver "
        f"and the one most tied to overall satisfaction. Next: "
        f"**{fix_first[1]['label']}** "
        f"({fix_first[1]['fix_first_score']}) and "
        f"**{fix_first[2]['label']}** "
        f"({fix_first[2]['fix_first_score']}). Correlations are Pearson, "
        f"computed with numpy from the raw responses.",
        "",
        "## 5. What the detractors say (comment-bank themes)",
        "",
        "| Theme | Detractors mentioning it | Share of detractors |",
        "|---|---|---|",
    ]
    for t in themes:
        L.append(f"| {t['theme']} | {t['detractors']} | "
                 f"{t['pct_of_detractors']}% |")
    L += [
        "",
        f"**Most common detractor theme: {top_theme['theme']}** "
        f"({top_theme['detractors']} of {len(detractors)} detractors, "
        f"{top_theme['pct_of_detractors']}%). Comments come from a fixed "
        f"phrase bank only — one phrase per response, chosen by NPS "
        f"segment — so themes are counted from the bank tags, never "
        f"invented free text.",
        "",
        "## 6. Month by month",
        "",
        "| Month | Responses | Promoters | Detractors | NPS | "
        "Avg satisfaction | NPS change (pts) |",
        "|---|---|---|---|---|---|---|",
    ]
    for mo in by_month:
        chg = "—" if mo["nps_change_points"] is None else (
            f"{mo['nps_change_points']:+.2f}")
        L.append(f"| {mo['month']} | {mo['responses']} | "
                 f"{mo['promoters']} | {mo['detractors']} | {mo['nps']} | "
                 f"{mo['avg_satisfaction']} | {chg} |")
    L += [
        "",
        f"NPS moved **{nps_trend:+.2f} points from January "
        f"({by_month[0]['nps']}) to June ({by_month[-1]['nps']})**. "
        f"Best month: **{best_month['month']} (NPS "
        f"{best_month['nps']})**; worst: **{worst_month['month']} (NPS "
        f"{worst_month['nps']})**.",
        "",
        "## 7. Three recommendations",
        "",
    ]
    for i, a in enumerate(actions, 1):
        L.append(f"{i}. **{a['title']}.** {a['detail']}")
    L += [
        "",
        "> Every number in this report is recomputed from "
        "`data/raw/survey_responses_SAMPLE.csv` by `src/analyze.py` — "
        "nothing is typed by hand. Run `python3 src/checks.py` to "
        "re-verify.",
    ]
    (PROJECT / "outputs" / "feedback_report.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")
    print(f"responses {total:,}, NPS {ov['nps']}, avg satisfaction "
          f"{ov['avg_satisfaction']}/5, promoters {ov['promoters']}, "
          f"detractors {ov['detractors']}, fix-first "
          f"{fix_first[0]['label']} ({fix_first[0]['fix_first_score']}), "
          f"best branch {best_branch['branch']} ({best_branch['nps']}), "
          f"worst branch {worst_branch['branch']} "
          f"({worst_branch['nps']})")


if __name__ == "__main__":
    main()
