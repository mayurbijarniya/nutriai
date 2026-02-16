#!/usr/bin/env python3
"""Create MongoDB indexes once, outside request startup path."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import get_db


def main():
    db = get_db()
    if not db.client:
        print("Database not connected. Check MONGODB_URI.")
        raise SystemExit(1)

    ok = db.ensure_indexes()
    if not ok:
        print("Index creation failed.")
        raise SystemExit(1)

    print("Index creation completed.")


if __name__ == "__main__":
    main()
