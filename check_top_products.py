from dotenv import load_dotenv
import os, pymongo
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

ps = db.products_sold
print("products_sold count:", ps.count_documents({}))
for s in ps.find({}, {"product_name":1,"total":1,"quantity":1}).limit(5):
    print(" ", s.get("product_name"), "|", s.get("quantity"), "|", s.get("total"))

udb = db.user_data_bought
print("\nuser_data_bought count:", udb.count_documents({}))
for s in udb.find({}, {"product_name":1,"total":1,"quantity":1}).limit(5):
    print(" ", s.get("product_name"), "|", s.get("quantity"), "|", s.get("total"))

# what are ALL distinct product_names in products_sold?
print("\nDistinct product names in products_sold (first 20):")
names = ps.distinct("product_name")
for n in names[:20]:
    print(" -", n)

print("\nDistinct product names in user_data_bought (first 20):")
names2 = udb.distinct("product_name")
for n in names2[:20]:
    print(" -", n)
