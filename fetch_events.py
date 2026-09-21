"""
Pulls current UFC events + live pricing stats from the SeatGeek API
and logs a timestamped snapshot to tickets.db.

Run this on a schedule (cron, launchd, or Claude's own scheduler) --
every snapshot makes the price-trend model better. Event-level only
(SeatGeek doesn't expose section/row data via the public API).
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from config import SEATGEEK_CLIENT_ID
from db import get_conn, init_db

API_BASE = "https://api.seatgeek.com/2/events"


def fetch_ufc_events():
    """Fetch all upcoming UFC events, paginating through results."""
    events = []
    page = 1
    per_page = 50
    while True:
        params = {
            "client_id": SEATGEEK_CLIENT_ID,
            "q": "UFC",
            "per_page": per_page,
            "page": page,
            "sort": "datetime_local.asc",
            "datetime_local.gte": datetime.now().strftime("%Y-%m-%d"),
        }
        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())

        batch = data.get("events", [])
        events.extend(batch)

        total = data.get("meta", {}).get("total", 0)
        if page * per_page >= total or not batch:
            break
        page += 1

    # Keep only events that are actually UFC (query is fuzzy and can
    # pull in unrelated stuff that happens to mention "UFC").
    ufc_events = [
        e for e in events
        if "ufc" in e.get("title", "").lower()
        or any("ufc" in p.get("slug", "") for p in e.get("performers", []))
    ]
    return ufc_events


def upsert_event(conn, event):
    venue = event.get("venue", {}) or {}
    conn.execute(
        """INSERT INTO events (id, title, event_datetime, venue_name, venue_city, venue_state, seatgeek_url)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             title=excluded.title,
             event_datetime=excluded.event_datetime,
             venue_name=excluded.venue_name,
             venue_city=excluded.venue_city,
             venue_state=excluded.venue_state,
             seatgeek_url=excluded.seatgeek_url""",
        (
            event["id"],
            event.get("title"),
            event.get("datetime_local"),
            venue.get("name"),
            venue.get("city"),
            venue.get("state"),
            event.get("url"),
        ),
    )


def insert_snapshot(conn, event):
    stats = event.get("stats", {}) or {}
    event_dt = event.get("datetime_local")
    days_to_event = None
    if event_dt:
        try:
            dt = datetime.fromisoformat(event_dt)
            days_to_event = (dt - datetime.now()).total_seconds() / 86400
        except ValueError:
            pass

    conn.execute(
        """INSERT INTO price_snapshots
           (event_id, days_to_event, lowest_price, average_price, highest_price,
            median_price, listing_count, visible_listing_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event["id"],
            days_to_event,
            stats.get("lowest_price"),
            stats.get("average_price"),
            stats.get("highest_price"),
            stats.get("median_price"),
            stats.get("listing_count"),
            stats.get("visible_listing_count"),
        ),
    )


def run():
    if SEATGEEK_CLIENT_ID == "PASTE_YOUR_CLIENT_ID_HERE":
        raise SystemExit(
            "Set your SeatGeek client_id first -- either export SEATGEEK_CLIENT_ID "
            "or edit config.py directly. Get one free at https://seatgeek.com/account/develop"
        )

    init_db()
    events = fetch_ufc_events()
    conn = get_conn()

    for event in events:
        upsert_event(conn, event)
        insert_snapshot(conn, event)

    conn.commit()
    conn.close()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{ts}] Logged {len(events)} UFC events.")
    for e in events[:10]:
        stats = e.get("stats", {})
        print(f"  - {e['title']} ({e.get('datetime_local', '?')[:10]}): "
              f"low ${stats.get('lowest_price')}, avg ${stats.get('average_price')}, "
              f"{stats.get('listing_count')} listings")


if __name__ == "__main__":
    run()
