from dotenv import load_dotenv
import os, pymongo
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

udb = db.user_data_bought
# See actual doc structure
doc = udb.find_one({"product_name": {"$ne": None}})
if doc:
    print("Fields:", list(doc.keys()))
    print("Sample:", {k: doc[k] for k in list(doc.keys())[:10]})
else:
    doc = udb.find_one({})
    print("Any doc fields:", list(doc.keys()) if doc else "empty")
    print("Sample:", doc)

# Check top by revenue
print("\nTop 10 by revenue in user_data_bought:")
pipeline = [
    {"$group": {"_id": "$product_name", "revenue": {"$sum": "$total"}, "units": {"$sum": "$quantity"}}},
    {"$sort": {"revenue": -1}},
    {"$limit": 10}
]
for r in udb.aggregate(pipeline):
    print(f"  {r['_id']}: ₹{r['revenue']:.0f} ({r['units']} units)")
