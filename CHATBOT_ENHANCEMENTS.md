# AI Chatbot Enhancements - Complete Documentation

## Overview

The SalesSense AI Assistant has been significantly enhanced with comprehensive data retrieval and analysis capabilities. Users can now ask natural language questions about festival offers, specific users, worker dashboards, product recommendations, and revenue analytics.

---

## Fixed Issues

### 🔧 Mother's Day Festival Bug

**Problem:** Customer portal showed "upcoming festival mother's day" but offers listed "Labour Day"

**Root Cause:** Mother's Day was missing from the festival calendar in `festival_notifications.py`

**Solution:** Added Mother's Day entry with:
- Date: May 11, 2026
- Products: Flowers, Chocolates, Sarees, Perfume, Jewelry, Gifts, Personal Care Items
- Categories: Gifts & Occasions, Personal Care, Food & Beverages, Fashion
- Discount: 15-40%
- Emoji: 👩‍❤️‍👨

---

## New Chatbot Features

### 1. 🎉 Festival Offers

**What it does:** Returns all active and upcoming festival offers with discount details

**Example Queries:**
- "Show all festival offers"
- "Tell me about upcoming festivals"
- "List all festival offers"
- "What festivals do we have?"

**Response includes:**
- Festival name with emoji
- Discount percentage
- Product categories
- Days until the festival
- Status (Active/Upcoming)

**Example Output:**
```
🎉 ALL FESTIVAL OFFERS:

1. 👩‍❤️‍👨 Mother's Day (15-40%)
   Celebrating the special mothers in our lives
   📅 In 11 days
   Products: Flowers, Chocolates, Sarees

2. 👷 Labour Day (10-25%)
   Honoring workers and their contributions
   ✅ ACTIVE
   Products: Groceries, Daily Essentials, Personal Care
```

---

### 2. 👤 User Data Lookup

**What it does:** Retrieves detailed information about specific users or lists all users

**Example Queries:**
- "Find user Rajesh"
- "Show user data for Priya"
- "Get user information about Amit"
- "List all users"

**Response includes (for specific user):**
- Name, Email, Phone
- Total Orders
- Total Amount Spent
- Recent Purchase History (last 5 purchases)
- Product names and purchase amounts

**Response includes (all users):**
- List of all users with names and emails
- Total user count

**Example Output:**
```
👤 USER DATA:

Name: Kandan Chinnadurai
Email: kandan@example.com
Phone: +91-9876543210
Total Orders: 45
Total Spent: ₹12,500.00

Recent Purchases:
  • Rice - ₹500.00
  • Oil - ₹800.00
  • Milk - ₹300.00
  • Spices - ₹250.00
  • Sugar - ₹150.00
```

---

### 3. 👷 Worker Dashboard

**What it does:** Shows top users, products, and categories for worker/staff view

**Example Queries:**
- "Show worker dashboard"
- "What are the top users?"
- "Top selling products"
- "Worker data"

**Response includes:**
- **Top Users:** Name, Amount Spent, Order Count, Average Order Value
- **Top Products:** Product Name, Revenue, Units Sold, Order Count
- **Top Categories:** Category Name, Revenue, Units Sold

**Example Output:**
```
👷 WORKER DASHBOARD DATA:

🏆 TOP USERS:
1. Anitha Selvam - ₹36,541.00 (82 orders)
2. Govindaraj S - ₹32,496.00 (56 orders)
3. Senthil Kumar - ₹32,460.00 (61 orders)

📦 TOP PRODUCTS:
1. சந்தனம் (Sandalwood) - ₹58,237.64 (156 units)
2. சஃபோலா கோல்ட் எண்ணெய் (Oil) - ₹56,145.00 (234 units)
3. சர்ஃப் எக்செல் சலவை பொடி (Detergent) - ₹51,995.00 (189 units)

📊 TOP CATEGORIES:
1. மளிகை (Groceries) - ₹251,758.74
2. தனிப்பட்ட பராமரிப்பு (Personal Care) - ₹153,293.35
3. தின்பண்டங்கள் (Snacks) - ₹104,542.46
```

---

### 4. 📦 Product Recommendations

**What it does:** Analyzes sales history to recommend which products to buy more of and which to stop ordering

**Example Queries:**
- "Product recommendations"
- "Should I buy more products?"
- "Which products should we stop buying?"
- "Buy now suggestions"
- "Inventory recommendations"

**Response includes:**

**BUY NOW (High Demand):**
- High demand + low stock
- Weekly sales and current stock levels
- Priority action: Reorder immediately

**STOP BUYING (Low Demand, Overstocked):**
- Low demand + high inventory
- Total sales and current stock levels
- Priority action: Reduce orders, plan promotions

**Analysis Criteria:**
- **Buy Now:** Weekly sales > 10 units AND stock < 20 units
- **Stop Buying:** Total sales < 5 units AND stock > 50 units

**Example Output:**
```
📦 Product Recommendations Based on Sales History:

🛒 BUY NOW: 3 products need restocking
  • வெண்ணெய் (Butter) - High demand (12 units/week), Low stock (8 left)
  • தொட்டி (Curd) - High demand (15 units/week), Low stock (5 left)

🚫 STOP BUYING: 2 products are overstocked
  • சிறிய சோயா சாஸ் (Soy Sauce) - Low demand (2 units sold), Overstocked (75 units)
  • குளிர்பான (Soft Drink) - Low demand (3 units sold), Overstocked (100 units)
```

---

### 5. 💰 Revenue Queries

**What it does:** Retrieves revenue data for specific dates or date ranges

**Example Queries:**
- "What's today's revenue?"
- "Yesterday's sales"
- "Revenue for last 7 days"
- "Monthly revenue (last 30 days)"
- "Revenue for 2025-04-28"
- "Sales between 2025-04-20 and 2025-04-28"

**Response includes:**
- Total Revenue
- Number of Orders
- Average Order Value
- Time Period (date or range)

**Date Parsing Support:**
- "today" → Current date
- "yesterday" → Previous day
- "last 7 days" → Past 7 days
- "last 30 days" / "month" → Past 30 days
- "2025-04-28" or "28-04-2025" → Specific date
- Date ranges with start and end dates

**Example Output:**
```
💰 REVENUE FOR 2025-04-28:

Total Revenue: ₹5,391.92
Total Orders: 50
Avg Order Value: ₹107.84

💰 REVENUE (2025-04-21 to 2025-04-28):

Total Revenue: ₹21,293.01
Total Orders: 215
Avg Order Value: ₹98.98
```

---

## New API Endpoints

### 1. `/api/festival-offers` (GET)

**Authentication:** Required (Admin)

**Response:**
```json
{
  "success": true,
  "count": 14,
  "offers": [
    {
      "name": "Mother's Day",
      "emoji": "👩‍❤️‍👨",
      "discount": "15-40%",
      "products": ["Flowers", "Chocolates", "Sarees", "Perfume"],
      "description": "Celebrating the special mothers in our lives",
      "days_until": 11,
      "active": false,
      "type": "predefined"
    }
  ]
}
```

---

### 2. `/api/user-data` (GET)

**Authentication:** Required (Admin)

**Query Parameters:**
- `name` (optional): Specific user name to search

**Response (specific user):**
```json
{
  "success": true,
  "user": {
    "name": "Kandan Chinnadurai",
    "email": "kandan@example.com",
    "phone": "+91-9876543210",
    "total_spent": 12500.00,
    "total_orders": 45,
    "purchase_history": [
      {
        "product_name": "Rice",
        "quantity": 5,
        "total": 500.00,
        "category": "Groceries",
        "purchase_date": "2025-04-28"
      }
    ]
  }
}
```

**Response (all users):**
```json
{
  "success": true,
  "count": 2317,
  "users": [
    {
      "name": "Kandan Chinnadurai",
      "email": "kandan@example.com"
    }
  ]
}
```

---

### 3. `/api/worker-dashboard` (GET)

**Authentication:** Required (Admin)

**Response:**
```json
{
  "success": true,
  "data": {
    "top_users": [
      {
        "name": "Anitha Selvam",
        "spent": 36541.00,
        "orders": 82,
        "avg_order_value": 445.88
      }
    ],
    "top_products": [
      {
        "name": "Sandalwood",
        "revenue": 58237.64,
        "units_sold": 156,
        "orders": 32
      }
    ],
    "top_categories": [
      {
        "name": "Groceries",
        "revenue": 251758.74,
        "units_sold": 4532
      }
    ]
  }
}
```

---

### 4. `/api/product-recommendations` (GET)

**Authentication:** Required (Admin)

**Response:**
```json
{
  "success": true,
  "recommendations": {
    "recommendations": "Product Recommendations Based on Sales History:\n\n🛒 BUY NOW: 3 products need restocking\n  - High demand with low stock\n\n🚫 STOP BUYING: 2 products are overstocked\n  - Low demand but high inventory",
    "buy_now": [
      {
        "name": "Butter",
        "category": "Dairy",
        "stock": 8,
        "weekly_sales": 12,
        "reason": "High demand (12 units/week), Low stock (8 left)",
        "priority": "HIGH"
      }
    ],
    "stop_buying": [
      {
        "name": "Soy Sauce",
        "category": "Condiments",
        "stock": 75,
        "total_sales": 2,
        "reason": "Low demand (only 2 units sold), Overstocked (75 units)",
        "priority": "MEDIUM"
      }
    ]
  }
}
```

---

### 5. `/api/revenue-by-date` (GET)

**Authentication:** Required (Admin)

**Query Parameters:**
- `date`: Specific date (YYYY-MM-DD)
- OR `start_date` and `end_date`: Date range (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "revenue_data": {
    "date": "2025-04-28",
    "revenue": 5391.92,
    "orders": 50,
    "avg_order_value": 107.84,
    "type": "daily"
  }
}
```

---

## Implementation Details

### New Functions in `app.py`

#### `get_all_festival_offers()`
- Retrieves all active and upcoming festivals
- Merges custom festivals from database with predefined Indian festivals
- Returns sorted list with activation status and days until occurrence

#### `get_user_data(user_identifier=None)`
- Searches users by ID, name, or email
- Returns complete user profile with purchase history
- Supports searching in both `users` and `users_update` collections

#### `get_top_users_and_products()`
- Aggregates data from `user_data_bought` collection
- Calculates top users by spending, top products by revenue, top categories
- Returns 10 results per category with detailed metrics

#### `get_product_recommendations()`
- Analyzes product demand using 7-day sales window
- Evaluates stock levels and purchase frequency
- Returns categorized recommendations with priority levels

#### `get_revenue_by_date_range(start_date=None, end_date=None, specific_date=None)`
- Aggregates revenue data for specified date range
- Calculates orders and average order value
- Supports single date or date range queries

### Enhanced Function: `process_admin_query(query)`
- Pattern matching for natural language queries
- Automatically parses date formats (today, yesterday, last 7 days, specific dates)
- Returns formatted responses with emojis and clear sections
- Caches responses for 90 seconds for performance

---

## Database Collections Used

| Collection | Usage |
|-----------|-------|
| `custom_festivals` | Custom festival offers |
| `users` / `users_update` | User profile data |
| `user_data_bought` | Purchase history and revenue data |
| `products_update` | Product inventory and stock levels |
| `workers_update` | Worker information |

---

## Query Examples

### By Feature Type

**Festival Queries:**
```
- "show all festival offers"
- "What festivals do we have?"
- "List upcoming festivals"
- "Tell me about festival offers"
```

**User Queries:**
```
- "Find user Rajesh"
- "Show data for Priya Kumar"
- "Get user info on Amit"
- "List all users"
```

**Worker Queries:**
```
- "Worker dashboard"
- "Show top users and products"
- "Who are our top customers?"
- "Top selling products"
```

**Product Queries:**
```
- "Product recommendations"
- "What should we buy now?"
- "Which products are overstocked?"
- "Buy or stop buying suggestions"
```

**Revenue Queries:**
```
- "Today's revenue"
- "Yesterday's sales"
- "Last 7 days revenue"
- "Revenue for April 28, 2025"
- "Sales between April 20 and April 28"
```

---

## Testing

Run the included test suite to verify all enhancements:

```bash
python test_chatbot_enhancements.py
```

**Tests Included:**
1. Festival Offers Retrieval (includes Mother's Day verification)
2. User Data Lookup
3. Worker Dashboard Data
4. Product Recommendations
5. Revenue by Date Queries
6. Chatbot Query Processing

---

## Notes

- All functions are protected by appropriate authentication (where applicable)
- Database queries are optimized using MongoDB aggregation pipelines
- Responses are cached for 90 seconds for performance
- Date parsing supports multiple formats (today, yesterday, YYYY-MM-DD, DD-MM-YYYY)
- Product recommendations use configurable thresholds (can be adjusted in code)
- All monetary values displayed in Indian Rupees (₹)

---

## Future Enhancements

Potential improvements for future versions:
1. Advanced filtering options for user queries
2. Custom date range selections for revenue analytics
3. Predictive recommendations using machine learning
4. Export reports to PDF/Excel
5. Real-time notifications for stock alerts
6. Seasonal trend analysis
7. Customer segmentation and targeting
8. Inventory forecasting
