"""
Turns logged snapshots into signal:
  - per-event trend (is this event's resale price rising or falling right now)
  - cross-event curve (once multiple events have completed, what does the
    typical price-vs-days-to-event curve look like, i.e. when does resale
    value historically peak)

Run any time -- read-only, safe to run as often as you want.
"""
from datetime import datetime
from db import get_conn


def per_event_trends(conn):
    """For each tracked event, show the last few snapshots and the trend."""
    events = conn.execute(
        "SELECT id, title, event_datetime FROM events ORDER BY event_datetime ASC"
    ).fetchall()

    results = []
    for event_id, title, event_dt in events:
        rows = conn.execute(
            """SELECT polled_at, days_to_event, lowest_price, average_price, listing_count
               FROM price_snapshots WHERE event_id=? ORDER BY polled_at ASC""",
            (event_id,),
        ).fetchall()

        if not rows:
            continue

        first, last = rows[0], rows[-1]
        trend = None
        pct_change = None
        if len(rows) >= 2 and first[2] and last[2]:
            pct_change = (last[2] - first[2]) / first[2] * 100
            trend = "rising" if pct_change > 2 else "falling" if pct_change < -2 else "flat"

        results.append({
            "event_id": event_id,
            "title": title,
            "event_datetime": event_dt,
            "snapshots": len(rows),
            "days_to_event": last[1],
            "current_lowest": last[2],
            "current_avg": last[3],
            "current_listings": last[4],
            "pct_change_since_tracked": round(pct_change, 1) if pct_change is not None else None,
            "trend": trend,
        })
    return results


def cross_event_curve(conn, bucket_size_days=5):
    """
    Bucket every snapshot from every COMPLETED event by days-to-event,
    normalize each event's price to a % of its own final/last-seen lowest
    price, and average within each bucket. This is the 'when does resale
    value peak' curve. Needs multiple completed events with good snapshot
    coverage to mean anything -- returns None until there's enough data.
    """
    now_iso = datetime.now().isoformat()
    completed_events = conn.execute(
        "SELECT id FROM events WHERE event_datetime < ?", (now_iso,)
    ).fetchall()

    if len(completed_events) < 3:
        return None  # not enough finished events to trust a curve yet

    buckets = {}
    for (event_id,) in completed_events:
        rows = conn.execute(
            """SELECT days_to_event, lowest_price FROM price_snapshots
               WHERE event_id=? AND lowest_price IS NOT NULL
               ORDER BY days_to_event DESC""",
            (event_id,),
        ).fetchall()
        if len(rows) < 3:
            continue

        baseline = rows[0][1]  # earliest-seen price for this event
        if not baseline:
            continue

        for days_to_event, price in rows:
            bucket = int(days_to_event // bucket_size_days) * bucket_size_days
            pct_of_baseline = price / baseline * 100
            buckets.setdefault(bucket, []).append(pct_of_baseline)

    if not buckets:
        return None

    curve = sorted(
        [(days, round(sum(vals) / len(vals), 1), len(vals)) for days, vals in buckets.items()],
        key=lambda r: -r[0],
    )
    return curve  # list of (days_to_event_bucket, avg_pct_of_baseline, sample_count)


def report():
    conn = get_conn()

    print("=" * 60)
    print("PER-EVENT STATUS")
    print("=" * 60)
    trends = per_event_trends(conn)
    if not trends:
        print("No data yet -- run fetch_events.py first.")
    for t in trends:
        dte = f"{t['days_to_event']:.0f}d out" if t["days_to_event"] is not None else "?"
        print(f"\n{t['title']} ({dte})")
        print(f"  snapshots: {t['snapshots']}  |  current low: ${t['current_lowest']}  "
              f"avg: ${t['current_avg']}  listings: {t['current_listings']}")
        if t["trend"]:
            print(f"  trend since we started tracking: {t['trend']} "
                  f"({t['pct_change_since_tracked']:+.1f}%)")
        else:
            print("  trend: need more snapshots to tell")

    print("\n" + "=" * 60)
    print("CROSS-EVENT PRICE CURVE (when resale value historically peaks)")
    print("=" * 60)
    curve = cross_event_curve(conn)
    if curve is None:
        completed = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_datetime < datetime('now')"
        ).fetchone()[0]
        print(f"Not enough completed events yet ({completed}/3 minimum). "
              f"This fills in automatically as events pass -- keep the poller running.")
    else:
        for days, pct, n in curve:
            bar = "#" * int(pct / 5)
            print(f"  {days:>4}d out: {pct:>6.1f}% of baseline price  {bar}  (n={n})")

    conn.close()


if __name__ == "__main__":
    report()
