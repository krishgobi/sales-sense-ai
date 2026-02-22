from dotenv import load_dotenv
import os, pymongo
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

print("=== ADMIN ACCOUNTS ===")
for u in db.users.find({"is_admin": True}, {"email":1, "password":1, "name":1}).limit(3):
    print(f"  email={u.get('email')} | pass={u.get('password')} | name={u.get('name')}")

print("\n=== WORKERS ===")
for col_name in ["workers", "workers_update"]:
    col = db[col_name]
    c = col.count_documents({})
    print(f"{col_name}: {c} docs")
    for w in col.find({}, {"username":1,"email":1,"password":1,"name":1,"role":1}).limit(3):
        print(f"  id={w['_id']} | user={w.get('username')} | email={w.get('email')} | pass={w.get('password')} | name={w.get('name')}")

print("\n=== ADMIN COLLECTION ===")
for col_name in ["admin", "admins"]:
    col = db[col_name]
    c = col.count_documents({})
    print(f"{col_name}: {c} docs")
    for a in col.find({}, {"email":1, "password":1, "username":1}).limit(3):
        print(f"  {a}")
