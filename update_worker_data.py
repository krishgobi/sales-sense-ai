"""
Backfill dashboard data gaps.

Updates:
- Adds missing/invalid user and worker phone numbers (Indian format)
- Adds missing user join dates / created_at dates
- Recalculates worker products_added and total_products_added
- Ensures today's fake sales exist in the same database used by app.py
"""

import os
import random
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import re
from seed_daily_sales import ensure_today_sales

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE") or "saless"

if not MONGODB_URL:
	raise SystemExit("MONGODB_URL is not set in .env")

client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]

workers_update = db["workers_update"]
products_by_user = db["products_by_user"]
users = db["users"]
users_update = db["users_update"]

PHONE_REGEX = re.compile(r"^(\+?91[-\s]?)?[6-9]\d{9}$")
KNOWN_USER_PHONES = {
	"dharsh@gmail.com": "9876543210",
	"kowshi@gmail.com": "9876543211",
	"jaan@gmail.com": "9876543212",
	"subhashreenatraj@gmail.com": "9876543213",
}


def generate_indian_phone() -> str:
	return f"+91-{random.choice([6, 7, 8, 9])}{random.randint(100000000, 999999999)}"


def is_valid_phone(phone: str) -> bool:
	if not phone:
		return False
	normalized = phone.replace(" ", "").replace("-", "")
	return bool(PHONE_REGEX.match(normalized))


def backfill_users() -> int:
	updated = 0
	now = datetime.datetime.utcnow()
	for collection in [users, users_update]:
		for user in collection.find({}):
			updates = {}
			email = (user.get("email") or "").strip().lower()
			phone = user.get("phone") or user.get("mobile") or ""
			if not is_valid_phone(phone):
				phone = KNOWN_USER_PHONES.get(email, generate_indian_phone())
				updates["phone"] = phone
				updates["mobile"] = phone
			else:
				updates["phone"] = phone
				updates["mobile"] = user.get("mobile") or phone

			created_at = user.get("created_at") or user.get("join_date")
			if not created_at:
				created_at = now
			updates["created_at"] = created_at
			updates["join_date"] = user.get("join_date") or created_at

			collection.update_one({"_id": user["_id"]}, {"$set": updates})
			updated += 1
	return updated


def backfill_workers() -> int:
	workers = list(workers_update.find({}))
	print(f"Found {len(workers)} workers.")

	updated = 0
	now = datetime.datetime.utcnow()
	for worker in workers:
		worker_id = worker.get("_id")
		if not worker_id:
			continue

		# Count products added by this worker (supports worker_id or added_by)
		count = products_by_user.count_documents({
			"$or": [
				{"worker_id": worker_id},
				{"added_by": worker_id},
				{"worker_id": str(worker_id)},
				{"added_by": str(worker_id)}
			]
		})

		updates = {
			"products_added": count,
			"total_products_added": count
		}

		phone = worker.get("phone", "")
		if not is_valid_phone(phone):
			updates["phone"] = generate_indian_phone()
		if not worker.get("date_of_joining"):
			updates["date_of_joining"] = worker.get("created_at") or now
		if not worker.get("created_at"):
			updates["created_at"] = updates.get("date_of_joining", now)
		if not worker.get("status"):
			updates["status"] = "Active"

		workers_update.update_one({"_id": worker_id}, {"$set": updates})
		updated += 1

	return updated


def main() -> None:
	user_count = backfill_users()
	worker_count = backfill_workers()
	inserted_sales = ensure_today_sales(50)
	print(f"Updated {user_count} user records.")
	print(f"Updated {worker_count} worker records.")
	print(f"Inserted {inserted_sales} sales records for today.")


if __name__ == "__main__":
	main()
