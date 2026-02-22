from dotenv import load_dotenv
import os, pymongo, datetime
load_dotenv()
client = pymongo.MongoClient(os.getenv('MONGODB_URL'), serverSelectionTimeoutMS=10000)
db = client[os.getenv('MONGODB_DATABASE', 'saless')]
udb = db['user_data_bought']
ps  = db['products_sold']
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
ft = list(udb.aggregate([{'$group': {'_id': None, 't': {'$sum': '$total'}}}]))
fd = list(udb.aggregate([{'$match': {'purchase_date': {'$gte': today}}}, {'$group': {'_id': None, 't': {'$sum': '$total'}}}]))
thirty = today - datetime.timedelta(days=30)
f30 = list(udb.aggregate([{'$match': {'purchase_date': {'$gte': thirty}}}, {'$group': {'_id': None, 't': {'$sum': '$total'}}}]))
print("="*45)
print(f"  Total revenue (all time): Rs.{ft[0]['t']:,.2f}" if ft else "  No data")
print(f"  Today revenue           : Rs.{fd[0]['t']:,.2f}" if fd else "  Today: Rs.0")
print(f"  Last 30 days revenue    : Rs.{f30[0]['t']:,.2f}" if f30 else "  30d: Rs.0")
print(f"  Total orders (sold)     : {ps.count_documents({})}")
print(f"  Total line-items        : {udb.count_documents({})}")
print("="*45)
