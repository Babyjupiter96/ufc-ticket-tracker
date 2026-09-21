import os

_HERE = os.path.dirname(__file__)


def _load_client_id():
    # 1) environment variable, 2) git-ignored local file, 3) placeholder
    env = os.environ.get("SEATGEEK_CLIENT_ID")
    if env:
        return env.strip()
    path = os.path.join(_HERE, ".seatgeek_client_id")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return "PASTE_YOUR_CLIENT_ID_HERE"


# Get your free client_id at https://seatgeek.com/account/develop
SEATGEEK_CLIENT_ID = _load_client_id()

DB_PATH = os.path.join(_HERE, "tickets.db")
