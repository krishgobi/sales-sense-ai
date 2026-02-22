from dotenv import load_dotenv
import os, pymongo, datetime
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Check today's records have total fields
docs = list(db.user_data_bought.find({"purchase_date": {"$gte": today}}).limit(5))
print("Today's sample records:")
for d in docs:
    print(f"  total={d.get('total')} | product={d.get('product_name','?')[:30]} | date={d.get('purchase_date')}")

# Check worker login form field issue 
print("\nTesting worker login via HTTP:")
import urllib.request, urllib.parse
data = urllib.parse.urlencode({"email": "gobi@gmail.com", "password": "gobi@123"}).encode()
try:
    req = urllib.request.Request("http://127.0.0.1:5000/worker/login", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(req, timeout=5)
    print(f"  Status: {resp.status}, URL: {resp.url}")
except Exception as e:
    print(f"  Error/Redirect: {type(e).__name__}: {e}")

print("\nChecking add-worker form post:")
data2 = urllib.parse.urlencode({
    "name": "TestWorker", "email": "test@test.com", "password": "test123"
}).encode()
req2 = urllib.request.Request("http://127.0.0.1:5000/admin/add-worker", data=data2, method="POST")
req2.add_header("Content-Type", "application/x-www-form-urlencoded")
try:
    resp2 = urllib.request.urlopen(req2, timeout=5)
    print(f"  Status: {resp2.status}")
except Exception as e:
    print(f"  Error/Redirect: {type(e).__name__}: {e}")

# Check email config
print("\nEmail config:")
print(f"  MAIL_SERVER={os.getenv('MAIL_SERVER','NOT SET')}")
print(f"  MAIL_PORT={os.getenv('MAIL_PORT','NOT SET')}")
print(f"  MAIL_USERNAME={os.getenv('MAIL_USERNAME','NOT SET')}")
print(f"  MAIL_PASSWORD={'SET' if os.getenv('MAIL_PASSWORD') else 'NOT SET'}")
print(f"  SENDER_EMAIL={os.getenv('SENDER_EMAIL','NOT SET')}")

# Check .env file
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if any(k in line.upper() for k in ["MAIL","EMAIL","SMTP","SEND"]):
                key = line.split("=")[0].strip()
                val = line.split("=",1)[1].strip() if "=" in line else ""
                # mask passwords
                if "PASS" in key.upper() or "SECRET" in key.upper():
                    print(f"  {key}=***")
                else:
                    print(f"  {key}={val}")
