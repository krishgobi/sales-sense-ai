"""
update_to_tamil_products.py
────────────────────────────
• Renames all English products in `products` collection to Tamil
• Adds `emoji` and `image_color` fields to EVERY product in both collections
  so the products page can display a colourful product image card.
"""

from dotenv import load_dotenv
import os, pymongo
load_dotenv()

client = pymongo.MongoClient(os.getenv("MONGODB_URL"), serverSelectionTimeoutMS=10000)
db     = client[os.getenv("MONGODB_DATABASE", "saless")]

# ──────────────────────────────────────────────────────────────────
# Helper — pick emoji + bg-color from product name keywords
# MUST be defined before it is called below
# ──────────────────────────────────────────────────────────────────
KEYWORD_EMOJI = [
    (["அரிசி","rice"],                       ("🍚","#fef9c3")),
    (["இட்லி","idli"],                       ("🥞","#fef9c3")),
    (["மாவு","flour","atta"],                ("🌾","#fde68a")),
    (["பால்","milk"],                        ("🥛","#eff6ff")),
    (["பட்டர்மில்","buttermilk"],            ("🥛","#f0fdf4")),
    (["தயிர்","curd","yogurt"],              ("🥛","#f0fdf4")),
    (["வெண்ணெய்","butter"],                  ("🧈","#fef9c3")),
    (["எண்ணெய்","oil","cooking oil"],        ("🫙","#fefce8")),
    (["சர்க்கரை","sugar"],                   ("🍬","#fdf2f8")),
    (["உப்பு","salt"],                      ("🧂","#f0f9ff")),
    (["மிளகாய்","chilli"],                   ("🌶️","#fef2f2")),
    (["மஞ்சள்","turmeric"],                  ("🟡","#fef9c3")),
    (["கொத்தமல்லி","coriander"],              ("🌿","#f0fdf4")),
    (["சீரகம்","cumin"],                     ("🌿","#fefce8")),
    (["மிளகு","pepper"],                    ("\u26ab","#f8fafc")),
    (["ஏலக்காய்","cardamom"],               ("🌿","#f0fdf4")),
    (["புளி","tamarind"],                   ("\U0001f7e4","#fef3c7")),
    (["வெல்லம்","jaggery"],                  ("\U0001f7eb","#fef3c7")),
    (["சாம்பார்","sambar"],                  ("🍲","#fff7ed")),
    (["ரசம்","rasam"],                      ("🍲","#fef2f2")),
    (["முறுக்கு","murukku"],                  ("🌀","#fef9c3")),
    (["மிக்சர்","mixture"],                  ("🥗","#fef9c3")),
    (["வடாம்","papad","appalam"],            ("\u2b55","#fef9c3")),
    (["தட்டை","thattai"],                   ("🥮","#fef9c3")),
    (["கடலை","peanut","nuts"],              ("🥜","#fef3c7")),
    (["லட்டு","laddu"],                     ("\U0001f7e0","#fff7ed")),
    (["ஜாங்கிரி","jangri"],                  ("\U0001f7e1","#fef9c3")),
    (["அதிரசம","adhirasam"],                ("\U0001f7e4","#fef3c7")),
    (["சீடை","seedai"],                     ("\u26aa","#f9fafb")),
    (["உருளை","potato"],                   ("🥔","#fef9c3")),
    (["தக்காளி","tomato"],                   ("🍅","#fef2f2")),
    (["வாழை","banana"],                    ("🍌","#fefce8")),
    (["தேங்காய்","coconut"],                 ("🥥","#f0fdf4")),
    (["நெல்லி","amla"],                     ("\U0001f7e2","#f0fdf4")),
    (["வேப்பிலை","neem"],                   ("🌿","#f0fdf4")),
    (["சோப்பு","soap","dove"],              ("🧼","#eff6ff")),
    (["தேநீர்","tea","red label","lipton"], ("🍵","#fef3c7")),
    (["காபி","coffee","bru"],               ("\u2615","#fef3c7")),
    (["juice","ஜூஸ்","orange"],             ("🍊","#fff7ed")),
    (["water","வாட்டர்","mineral"],          ("\U0001f4a7","#eff6ff")),
    (["cola","கோலா","pepsi","coke"],        ("🥤","#fce7f3")),
    (["chocolate","சாக்லேட்","munch"],       ("🍫","#fdf2f8")),
    (["biscuit","பிஸ்கட்","cookies","parle","britannia","good day"],("🍪","#fef9c3")),
    (["chips","சிப்ஸ்","lay"],              ("🥔","#fef9c3")),
    (["popcorn","பாப்கார்ன்"],               ("🍿","#fff7ed")),
    (["pretzel"],                           ("🥨","#fef3c7")),
    (["pasta","பாஸ்தா","maggi","noodle"],   ("🍝","#fef9c3")),
    (["lentil","பருப்பு"],                   ("\U0001fad8","#fdf4ff")),
    (["beans","பீன்ஸ்"],                    ("\U0001fad3","#f0fdf4")),
    (["chickpea","channa","கொண்டை"],        ("\U0001fad8","#fef3c7")),
    (["sauce","சாஸ்"],                      ("🍅","#fef2f2")),
    (["detergent","surf","washing","henko"],("🧴","#eff6ff")),
    (["harpic","toilet","कझिवறை"],         ("\U0001f6bf","#f0f9ff")),
    (["vim"],                               ("\U0001f9fd","#f0fdf4")),
    (["shampoo","clinic plus"],             ("🧴","#fdf4ff")),
    (["toothpaste","colgate","dental"],     ("\U0001f9b7","#eff6ff")),
    (["face wash","facial","himalaya"],     ("🧴","#fdf4ff")),
    (["glucose","glucose d"],               ("\U0001f3c3","#fef9c3")),
    (["saffola","sunflower"],               ("\U0001f33b","#fefce8")),
    (["dettol"],                            ("🧼","#eff6ff")),
    (["amul"],                              ("🥛","#fef9c3")),
    (["haldiram","bhujia"],                 ("🥗","#fef9c3")),
]

CATEGORY_FALLBACK = {
    "மளிகை":         ("\U0001f6d2","#fef9ec"),
    "groceries":     ("\U0001f6d2","#fef9ec"),
    "பானங்கள்":      ("🥤","#eff6ff"),
    "beverages":     ("🥤","#eff6ff"),
    "தின்பண்டங்கள்": ("🍿","#fff7ed"),
    "snacks":        ("🍿","#fff7ed"),
    "காய்கறி":       ("\U0001f966","#f0fdf4"),
    "vegetable":     ("\U0001f966","#f0fdf4"),
    "தனிப்பட்ட":     ("🧴","#fdf4ff"),
    "personal":      ("🧴","#fdf4ff"),
    "இல்லம்":       ("\U0001f3e0","#f8fafc"),
    "household":     ("\U0001f3e0","#f8fafc"),
    "instant":       ("🍜","#fef9c3"),
    "dairy":         ("🥛","#f0f9ff"),
}

def get_emoji(name: str, category: str = ""):
    """Return (emoji, bg_color) for a product based on name/category keywords."""
    n = (name or "").lower()
    c = (category or "").lower()
    for keywords, result in KEYWORD_EMOJI:
        for kw in keywords:
            if kw in n or kw in c:
                return result
    for key, val in CATEGORY_FALLBACK.items():
        if key in c:
            return val
    return ("\U0001f4e6","#f9fafb")   # 📦

# ──────────────────────────────────────────────────────────────────
# English → Tamil product name + category map
# ──────────────────────────────────────────────────────────────────
RENAME_MAP = {
    "Rice - Premium Quality":  ("அரிசி - சிறப்பு தரம் (Rice)",            "மளிகை (Groceries)"),
    "Wheat Flour":             ("கோதுமை மாவு (Wheat Flour)",               "மளிகை (Groceries)"),
    "Sugar":                   ("சர்க்கரை (Sugar)",                         "மளிகை (Groceries)"),
    "Salt":                    ("உப்பு (Salt)",                             "மளிகை (Groceries)"),
    "Cola - 2L":               ("கோலா பானம் 2L (Cola)",                    "பானங்கள் (Beverages)"),
    "Orange Juice - 1L":       ("ஆரஞ்சு ஜூஸ் 1L (Orange Juice)",          "பானங்கள் (Beverages)"),
    "Mineral Water - 1L":      ("மினரல் வாட்டர் 1L (Water)",               "பானங்கள் (Beverages)"),
    "Pasta":                   ("பாஸ்தா (Pasta)",                           "மளிகை (Groceries)"),
    "Cooking Oil":             ("சமையல் எண்ணெய் (Cooking Oil)",             "மளிகை (Groceries)"),
    "Lentils":                 ("பருப்பு (Lentils/Dal)",                    "மளிகை (Groceries)"),
    "Beans":                   ("பீன்ஸ் (Beans)",                           "காய்கறிகள் & பழங்கள் (Vegetables)"),
    "Chickpeas":               ("கொண்டைக்கடலை (Chickpeas)",                "மளிகை (Groceries)"),
    "Tomato Sauce":            ("தக்காளி சாஸ் (Tomato Sauce)",              "மளிகை (Groceries)"),
    "Potato Chips":            ("உருளைக்கிழங்கு சிப்ஸ் (Potato Chips)",    "தின்பண்டங்கள் (Snacks)"),
    "Popcorn":                 ("பாப்கார்ன் (Popcorn)",                     "தின்பண்டங்கள் (Snacks)"),
    "Pretzels":                ("பிரெட்ஸல் (Pretzels)",                     "தின்பண்டங்கள் (Snacks)"),
    "Chocolate Bar":           ("சாக்லேட் (Chocolate)",                     "தின்பண்டங்கள் (Snacks)"),
    "Cookies":                 ("குக்கீஸ் (Cookies)",                       "தின்பண்டங்கள் (Snacks)"),
    "Nuts Mix":                ("நட்ஸ் மிக்ஸ் (Nuts Mix)",                  "தின்பண்டங்கள் (Snacks)"),
}

# ── 1. Rename English → Tamil in `products` collection ────────────
print("\n[1/2] Renaming English products to Tamil in `products` collection…")
renamed = 0
for eng, (tamil_name, tamil_cat) in RENAME_MAP.items():
    em, col = get_emoji(tamil_name, tamil_cat)
    res = db.products.update_many(
        {"name": eng},
        {"$set": {"name": tamil_name, "category": tamil_cat, "emoji": em, "image_color": col}}
    )
    if res.modified_count:
        print(f"  ✓ {eng}  →  {tamil_name}")
        renamed += res.modified_count

print(f"  → {renamed} product(s) renamed")

# ── 2. Add emoji/image_color to all products in every collection ───
print("\n[2/2] Patching emoji + image_color on ALL products…")
patched = 0
for col_name in ["products", "products_update", "products_by_user"]:
    coll = db[col_name]
    count = coll.count_documents({})
    if count == 0:
        continue
    updated = 0
    for prod in coll.find({}):
        em, bg = get_emoji(prod.get("name",""), prod.get("category",""))
        coll.update_one(
            {"_id": prod["_id"]},
            {"$set": {"emoji": em, "image_color": bg}}
        )
        updated += 1
    print(f"  {col_name}: {updated} products patched")
    patched += updated

print(f"\n[DONE] ✅  {patched} products patched in total.")
print("Restart Flask server and refresh /products to see the changes.")
