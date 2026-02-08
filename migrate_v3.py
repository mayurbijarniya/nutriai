#!/usr/bin/env python3
"""Migrate legacy analysis_history data into v3 meal_logs.

Run with:
    source venv/bin/activate
    python migrate_v3.py

Optional:
    python migrate_v3.py --email user@example.com
    python migrate_v3.py --user-id 64f...
"""

import argparse
from bson import ObjectId

from database import get_db
from v3_features import migrate_user_history_to_meal_logs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", help="Migrate only this user email")
    parser.add_argument("--user-id", help="Migrate only this user ObjectId")
    args = parser.parse_args()

    db = get_db()
    if not db.client:
        print("Database connection unavailable.")
        return

    users = []
    if args.user_id:
        try:
            users = [db.users.find_one({"_id": ObjectId(args.user_id)})]
        except Exception:
            print("Invalid --user-id")
            return
    elif args.email:
        users = [db.users.find_one({"email": args.email})]
    else:
        users = list(db.users.find({}, {"_id": 1, "email": 1, "name": 1}))

    users = [u for u in users if u]
    if not users:
        print("No users found for migration.")
        return

    total_migrated = 0
    total_skipped = 0
    for user in users:
        stats = migrate_user_history_to_meal_logs(user["_id"])
        total_migrated += stats.get("migrated", 0)
        total_skipped += stats.get("skipped", 0)
        print(
            f"[{user.get('email', user.get('_id'))}] migrated={stats.get('migrated', 0)} "
            f"skipped={stats.get('skipped', 0)} already_completed={stats.get('already_completed', False)}"
        )

    print(f"Done. total_migrated={total_migrated} total_skipped={total_skipped}")


if __name__ == "__main__":
    main()
