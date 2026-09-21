# UFC Ticket Tracker

Tracks live UFC event resale pricing from SeatGeek's public API over time,
so you can see the actual trend (rising/falling/flat) instead of guessing.

## Setup (one time)

1. Get a free `client_id` at https://seatgeek.com/account/develop
2. Either:
   - `export SEATGEEK_CLIENT_ID=your_id_here` (add to your ~/.zshrc to persist it), or
   - open `config.py` and paste it directly in place of `PASTE_YOUR_CLIENT_ID_HERE`

## Run it manually

```bash
python3 fetch_events.py   # pulls current UFC events + pricing, logs a snapshot
python3 export_json.py    # writes dashboard_data.json for the dashboard to read
python3 analyze.py        # prints a terminal report of trends
```

Or just run both fetch+export in one go:
```bash
./poll.sh
```

## View the dashboard

```bash
python3 -m http.server 8800
```
Then open http://localhost:8800/dashboard.html

(Must be served over http://, not opened as a file:// -- browsers block
local JSON fetches from file:// for security.)

## Automate it (recommended)

The more snapshots logged, the better the trend/timing signal gets. Set up
a cron job to run `poll.sh` every few hours:

```bash
crontab -e
```
Add this line (runs every 4 hours):
```
0 */4 * * * /Users/babyjupiter/ufc-ticket-tracker/poll.sh
```

## What you get right away vs. what takes time

- **Immediately**: current lowest/average/highest price + listing count for
  every upcoming UFC event, refreshed every time you poll.
- **After a few days of polling**: per-event trend lines (is this specific
  event's resale price climbing or dropping right now).
- **After 3+ events have actually passed**: the cross-event curve in
  `analyze.py` -- the real answer to "how many days before an event does
  resale value typically peak." This is the part that makes the model
  actually predictive instead of just descriptive. It only gets better the
  longer the poller runs.

## Known limitation

SeatGeek's public API only exposes whole-event pricing stats, not individual
section/row listings. This tells you *when* to sell, not *which exact seat*.
Getting section-level data would require scraping listing pages directly,
which is against SeatGeek/StubHub/Vivid Seats' terms of service -- a
separate conversation if you want to go there later.
