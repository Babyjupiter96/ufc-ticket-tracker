# UFC Ticket Tracker

Logs resale pricing for upcoming UFC events from SeatGeek's public API over time, so you can see whether an event's tickets are actually rising, falling, or flat, instead of guessing.

It stores a timestamped price snapshot for every event on each run, then turns those snapshots into per-event trends and, once enough events have finished, a "when does resale value peak" curve.

## How it works

```
SeatGeek API ──▶ fetch_events.py ──▶ SQLite (events, price_snapshots)
                                          │
                       ┌──────────────────┴──────────────────┐
                       ▼                                     ▼
                 analyze.py                            export_json.py
          (terminal trend report)                   dashboard_data.json
                                                             │
                                                             ▼
                                                     dashboard.html
```

- **`fetch_events.py`** pages through SeatGeek's events endpoint, keeps only real UFC events (the search is fuzzy), upserts each event, and inserts a snapshot: lowest, average, median, and highest price, listing counts, and days until the event.
- **`db.py`** holds the SQLite schema and connection helper (Python standard library only, no dependencies).
- **`analyze.py`** prints a read-only report:
  - *Per-event trend:* compares an event's first and latest snapshot and labels it rising, falling, or flat (a change within ±2% counts as flat).
  - *Cross-event curve:* buckets every snapshot from completed events by days-to-event, normalizes each event's price to its own earliest-seen price, and averages within each bucket. This is meant to answer "how many days before an event does resale peak." It returns nothing until at least 3 events have finished, each with at least 3 snapshots, so it doesn't draw conclusions from too little data.
- **`export_json.py`** dumps the database to `dashboard_data.json`.
- **`dashboard.html`** is a static page that reads that JSON (it must be served over `http://`, not opened as a file).
- **`poll.sh`** runs one fetch-and-export cycle, suitable for cron.

## Setup

Requires Python 3 (no third-party packages).

1. Get a free `client_id` at https://seatgeek.com/account/develop
2. Provide it in either of these ways (neither is committed to the repo):
   - `export SEATGEEK_CLIENT_ID=your_id`, or
   - put the ID in a file named `.seatgeek_client_id` next to `config.py` (it is git-ignored)

## Run it

```bash
python3 fetch_events.py    # log a snapshot of current prices
python3 export_json.py     # refresh the dashboard data
python3 analyze.py         # print trends in the terminal
# or both fetch + export at once:
./poll.sh
```

View the dashboard:

```bash
python3 -m http.server 8800
# open http://localhost:8800/dashboard.html
```

To collect data continuously, run `poll.sh` on a schedule, for example every 4 hours with cron:

```
0 */4 * * * /path/to/ufc-ticket-tracker/poll.sh
```

## What you get, and when

- **Immediately:** current lowest, average, and highest price plus listing count for each upcoming event.
- **After a few days of polling:** per-event trend lines.
- **After 3+ events have finished:** the cross-event peak-timing curve. This is the predictive part, and it only improves the longer the poller runs.

## Known limitations

- **Early data.** The tracker has only logged a handful of events so far, so the cross-event curve isn't populated yet. The design is what's finished; the insight depends on collecting more history.
- **Event-level pricing only.** SeatGeek's public API doesn't expose section or row data.
- **Not scheduled by default.** Trends only improve if you set up the cron job.
- **No automated tests.**

## Tech

Python 3 (standard library only) · SQLite · SeatGeek Platform API · vanilla HTML/JS dashboard
