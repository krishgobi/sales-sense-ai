from dotenv import load_dotenv
import os, pymongo
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

names = db.user_data_bought.distinct("product_name")
english = [n for n in names if n and all(ord(c) < 128 for c in n)]
print("English names count:", len(english))
for n in sorted(english):
    print(" -", n)
