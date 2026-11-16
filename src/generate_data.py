#!/usr/bin/env python3
"""P20 — generate the SAMPLE customer-feedback survey file for
CityMart (SAMPLE).

Fictional Pakistani retail buyer, 6 months of survey responses:
Thu 2026-01-01 -> Tue 2026-06-30 (181 days). Seeded, so the file is
reproducible. One file, one row per survey response:

  data/raw/survey_responses_SAMPLE.csv — grain: one survey response
      (response_id, survey_date, month, branch, channel, recommend,
       satisfaction, product_quality, price, delivery_speed,
       staff_service, store_cleanliness, comment, theme)

How the demo data is built (and why the report can still find real
things in it): each branch has a fixed behaviour profile — driver
offsets that make one branch the strong one (Lahore — Gulberg) and
one the weak one (Rawalpindi — Saddar, slow delivery and weaker
staff service) — and each channel has its own small effect (online
orders feel the delivery problem most). Every response starts from
one latent "how good was this visit" draw, so the five drivers move
together and the correlations with overall satisfaction are real,
not asserted. The recommend score (0–10) is driven by overall
satisfaction, so the NPS segments are measured from the file. The
open-text comment comes from a fixed phrase bank only — one phrase
per response, chosen by NPS segment — so detractor themes are
counted from the bank tags, never invented free text.

    python3 src/generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"

SEED = 20261116
START = date(2026, 1, 1)
END = date(2026, 6, 30)
N_RESPONSES = 350

# branch: (driver offsets in order product_quality, price,
#          delivery_speed, staff_service, store_cleanliness,
#          volume weight)
BRANCHES = {
    "Lahore — Gulberg": ((0.3, 0.2, 0.3, 0.3, 0.3), 0.40),
    "Karachi — Clifton": ((0.0, 0.0, 0.0, 0.0, 0.0), 0.35),
    "Rawalpindi — Saddar": ((-0.1, -0.2, -0.7, -0.4, -0.3), 0.25),
}
# channel: (driver offsets, volume weight) — online orders feel the
# delivery problem most; phone orders get a little extra staff care
CHANNELS = {
    "In-store": ((0.0, 0.0, 0.1, 0.1, 0.0), 0.55),
    "Online": ((0.0, 0.0, -0.4, -0.1, 0.0), 0.30),
    "Phone": ((0.0, 0.0, 0.1, 0.2, 0.0), 0.15),
}
# month: small seasonal effect on the latent visit quality, so the
# monthly NPS trend has a real shape (rises into April, dips in May)
MONTH_EFFECT = {"2026-01": -0.20, "2026-02": -0.10, "2026-03": 0.00,
                "2026-04": 0.15, "2026-05": -0.25, "2026-06": 0.05}
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
MONTH_WEIGHTS = [0.15, 0.15, 0.17, 0.17, 0.18, 0.18]
DRIVERS = ["product_quality", "price", "delivery_speed",
           "staff_service", "store_cleanliness"]

# fixed comment bank: (phrase, theme). One phrase per response,
# chosen by NPS segment — no free text is invented beyond this bank.
PROMOTER_COMMENTS = [
    ("Staff were friendly and helpful.", "staff"),
    ("Good quality products, fresh stock.", "quality"),
    ("Delivery arrived before time.", "delivery"),
    ("Fair prices for the quality.", "price"),
    ("Clean store, easy to shop.", "cleanliness"),
    ("Best branch in the area, I will come again.", "overall"),
]
PASSIVE_COMMENTS = [
    ("Good overall, delivery could be faster.", "delivery"),
    ("Prices are a little high but quality is fine.", "price"),
    ("Staff are okay, nothing special.", "staff"),
    ("Store is fine, parking is difficult.", "overall"),
    ("Products are good, some items were out of stock.", "stock"),
]
DETRACTOR_COMMENTS = [
    ("Delivery was very late, no one called.", "delivery"),
    ("Prices are too high compared to other stores.", "price"),
    ("Staff were rude and did not help.", "staff"),
    ("The item I wanted was out of stock again.", "stock"),
    ("Store was dirty and shelves were messy.", "cleanliness"),
    ("Product quality was poor, had to return it.", "quality"),
]


def clamp_int(x, lo, hi):
    return max(lo, min(hi, int(round(x))))


def main():
    rng = random.Random(SEED)
    month_days = {}
    for m in range(1, 7):
        first = date(2026, m, 1)
        nxt = date(2026, m + 1, 1) if m < 6 else date(2026, 7, 1)
        month_days[f"2026-{m:02d}"] = (first, (nxt - first).days)

    branch_names = list(BRANCHES)
    branch_weights = [BRANCHES[b][1] for b in branch_names]
    channel_names = list(CHANNELS)
    channel_weights = [CHANNELS[c][1] for c in channel_names]

    rows = []
    for i in range(N_RESPONSES):
        mi = rng.choices(range(6), weights=MONTH_WEIGHTS)[0]
        mkey = MONTHS[mi]
        first, ndays = month_days[mkey]
        day = first + timedelta(days=rng.randrange(ndays))
        branch = rng.choices(branch_names, weights=branch_weights)[0]
        channel = rng.choices(channel_names,
                              weights=channel_weights)[0]
        b_off = BRANCHES[branch][0]
        c_off = CHANNELS[channel][0]
        # one latent visit quality; drivers move together with it
        latent = rng.gauss(4.0, 0.75) + MONTH_EFFECT[mkey]
        drivers = {}
        for j, name in enumerate(DRIVERS):
            drivers[name] = clamp_int(
                latent + b_off[j] + c_off[j] + rng.gauss(0, 0.5), 1, 5)
        satisfaction = clamp_int(
            sum(drivers.values()) / len(DRIVERS) + rng.gauss(0, 0.4),
            1, 5)
        recommend = clamp_int(
            satisfaction * 2 + rng.gauss(0, 1.2), 0, 10)
        if recommend >= 9:
            comment, theme = rng.choice(PROMOTER_COMMENTS)
        elif recommend >= 7:
            comment, theme = rng.choice(PASSIVE_COMMENTS)
        else:
            comment, theme = rng.choice(DETRACTOR_COMMENTS)
        rows.append({
            "response_id": f"R-{i + 1:04d}",
            "survey_date": day.isoformat(), "month": mkey,
            "branch": branch, "channel": channel,
            "recommend": recommend, "satisfaction": satisfaction,
            **drivers, "comment": comment, "theme": theme,
        })

    rows.sort(key=lambda r: (r["survey_date"], r["response_id"]))
    for i, r in enumerate(rows):
        r["response_id"] = f"R-{i + 1:04d}"
    with open(RAW / "survey_responses_SAMPLE.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "response_id", "survey_date", "month", "branch", "channel",
            "recommend", "satisfaction", "product_quality", "price",
            "delivery_speed", "staff_service", "store_cleanliness",
            "comment", "theme"])
        w.writeheader()
        w.writerows(rows)

    n_prom = sum(1 for r in rows if r["recommend"] >= 9)
    n_det = sum(1 for r in rows if r["recommend"] <= 6)
    nps = round(100.0 * (n_prom - n_det) / len(rows), 2)
    avg_sat = round(sum(r["satisfaction"] for r in rows) / len(rows), 2)
    print(f"wrote {len(rows)} survey responses "
          f"({rows[0]['survey_date']}..{rows[-1]['survey_date']}), "
          f"promoters {n_prom}, detractors {n_det}, NPS {nps}, "
          f"avg satisfaction {avg_sat}/5")


if __name__ == "__main__":
    main()
