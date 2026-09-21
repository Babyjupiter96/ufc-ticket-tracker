import os

# Get your free client_id at https://seatgeek.com/account/develop
# Then either set the env var SEATGEEK_CLIENT_ID, or paste it directly below.
SEATGEEK_CLIENT_ID = os.environ.get("SEATGEEK_CLIENT_ID", "NjAzNDg2Nzd8MTc4NjY1MjE5OS42NjYwOTg0")

DB_PATH = os.path.join(os.path.dirname(__file__), "tickets.db")
