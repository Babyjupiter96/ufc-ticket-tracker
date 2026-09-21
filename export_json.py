"""Exports current DB state to dashboard_data.json for dashboard.html to read."""
import json
import os
from db import get_conn

OUT_PATH = os.path.join(os.path.dirname(__file__), "dashboard_data.json")


def export():
    conn = get_conn()
    events = conn.execute(
        "SELECT id, title, event_datetime, venue_name, venue_city, venue_state, seatgeek_url FROM events ORDER BY event_datetime ASC"
    ).fetchall()

    data = []
    for eid, title, edt, vname, vcity, vstate, url in events:
        snaps = conn.execute(
            """SELECT polled_at, days_to_event, lowest_price, average_price,
                      highest_price, median_price, listing_count, visible_listing_count
               FROM price_snapshots WHERE event_id=? ORDER BY polled_at ASC""",
            (eid,),
        ).fetchall()
        data.append({
            "id": eid,
            "title": title,
            "event_datetime": edt,
            "venue": f"{vname}, {vcity} {vstate}".strip(", "),
            "url": url,
            "snapshots": [
                {
                    "polled_at": s[0], "days_to_event": s[1], "lowest_price": s[2],
                    "average_price": s[3], "highest_price": s[4], "median_price": s[5],
                    "listing_count": s[6], "visible_listing_count": s[7],
                }
                for s in snaps
            ],
        })

    conn.close()
    with open(OUT_PATH, "w") as f:
        json.dump({"generated_at": __import__("datetime").datetime.now().isoformat(), "events": data}, f, indent=2)
    print(f"Wrote {len(data)} events to {OUT_PATH}")


if __name__ == "__main__":
    export()
