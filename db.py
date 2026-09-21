import sqlite3
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    event_datetime TEXT,
    venue_name TEXT,
    venue_city TEXT,
    venue_state TEXT,
    seatgeek_url TEXT,
    first_seen TEXT DEFAULT (datetime('now')),
    UNIQUE(id)
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    polled_at TEXT DEFAULT (datetime('now')),
    days_to_event REAL,
    lowest_price REAL,
    average_price REAL,
    highest_price REAL,
    median_price REAL,
    listing_count INTEGER,
    visible_listing_count INTEGER,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_event ON price_snapshots(event_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_polled ON price_snapshots(polled_at);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
