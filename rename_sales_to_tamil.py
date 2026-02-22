"""
rename_sales_to_tamil.py
─────────────────────────
Renames all English product names in `user_data_bought` (the sales history)
to Tamil names so Top Selling Products shows Tamil names everywhere.
"""
from dotenv import load_dotenv
import os, pymongo
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless
col = db.user_data_bought

# English → (Tamil name, Tamil category)
RENAME = {
    "Aashirvaad Atta 5kg":       ("ஆஷிர்வாத் கோதுமை மாவு 5kg (Atta)",       "மளிகை (Groceries)"),
    "Amul Butter 500g":          ("அமுல் வெண்ணெய் 500g (Butter)",             "பால் பொருட்கள் (Dairy)"),
    "Amul Full Cream Milk":      ("அமுல் முழு கொழுப்பு பால் (Full Cream Milk)","பால் பொருட்கள் (Dairy)"),
    "Britannia Good Day":        ("பிரிட்டானியா குட் டே பிஸ்கட் (Biscuit)",   "தின்பண்டங்கள் (Snacks)"),
    "Bru Instant Coffee":        ("பிரூ இன்ஸ்டன்ட் காபி (Coffee)",             "பானங்கள் (Beverages)"),
    "Clinic Plus Shampoo":       ("கிளினிக் பிளஸ் ஷாம்பு (Shampoo)",          "தனிப்பட்ட பராமரிப்பு (Personal Care)"),
    "Colgate MaxFresh":          ("கோல்கேட் மேக்ஸ்ஃப்ரெஷ் பேஸ்ட் (Toothpaste)","தனிப்பட்ட பராமரிப்பு (Personal Care)"),
    "Dettol Soap":               ("டெட்டால் சோப்பு (Dettol Soap)",             "தனிப்பட்ட பராமரிப்பு (Personal Care)"),
    "Dove Soap":                 ("டவ் சோப்பு (Dove Soap)",                    "தனிப்பட்ட பராமரிப்பு (Personal Care)"),
    "Fortune Sunflower Oil":     ("ஃபார்ச்சூன் சூரியகாந்தி எண்ணெய் (Sunflower Oil)", "மளிகை (Groceries)"),
    "Glucose D Powder":          ("க்ளூக்கோஸ் டி பவுடர் (Glucose Powder)",    "தின்பண்டங்கள் (Snacks)"),
    "Haldiram Bhujia 400g":      ("ஹல்திராம் பூஜியா 400g (Bhujia)",           "தின்பண்டங்கள் (Snacks)"),
    "Harpic Power Plus":         ("ஹார்பிக் பவர் பிளஸ் (Toilet Cleaner)",     "இல்லப் பொருட்கள் (Household)"),
    "Himalaya Face Wash":        ("ஹிமாலயா ஃபேஸ் வாஷ் (Face Wash)",           "தனிப்பட்ட பராமரிப்பு (Personal Care)"),
    "Lay's Classic Salted":      ("லேஸ் க்ளாசிக் சால்டட் சிப்ஸ் (Chips)",     "தின்பண்டங்கள் (Snacks)"),
    "Lipton Green Tea":          ("லிப்டன் க்ரீன் டீ (Green Tea)",             "பானங்கள் (Beverages)"),
    "Maggi Noodles":             ("மாகி நூடுல்ஸ் (Noodles)",                   "உணவு (Instant Food)"),
    "Munch Chocolate":           ("மஞ்ச் சாக்லேட் (Chocolate)",                "தின்பண்டங்கள் (Snacks)"),
    "Parle-G Biscuits":          ("பார்லே-ஜி பிஸ்கட் (Parle-G)",              "தின்பண்டங்கள் (Snacks)"),
    "Pepsi 2L":                  ("பெப்சி 2L (Pepsi)",                         "பானங்கள் (Beverages)"),
    "Red Label Tea 500g":        ("ரெட் லேபிள் தேனீர் 500g (Red Label Tea)",   "பானங்கள் (Beverages)"),
    "Saffola Gold Oil":          ("சஃபோலா கோல்ட் எண்ணெய் (Saffola Gold Oil)", "மளிகை (Groceries)"),
    "Surf Excel Detergent":      ("சர்ஃப் எக்செல் சலவை பொடி (Detergent)",     "இல்லப் பொருட்கள் (Household)"),
    "Tata Salt 1kg":             ("டாட்டா உப்பு 1kg (Tata Salt)",              "மளிகை (Groceries)"),
    "Vim Bar":                   ("வீம் பாத்திரம் கழுவும் சோப்பு (Vim Bar)",   "இல்லப் பொருட்கள் (Household)"),
}

print("Renaming English product names → Tamil in `user_data_bought`…\n")
total = 0
for eng, (tamil, cat) in RENAME.items():
    res = col.update_many(
        {"product_name": eng},
        {"$set": {"product_name": tamil, "category": cat}}
    )
    if res.modified_count:
        print(f"  ✓ {eng}")
        print(f"    → {tamil} ({res.modified_count} docs)")
        total += res.modified_count

print(f"\n✅ Done — {total} sales records updated to Tamil product names.")
