# Seed Realistic Data - Usage Guide

This script (`seed_realistic_data.py`) populates your MongoDB database with realistic sample data including:

- **50 Users** - With varying registration dates and locations across Indian cities
- **15 Workers** - With realistic sales data and activity
- **30+ Products** - Tamil-named products across multiple categories (Food, Vegetables, Spices, Dairy, Dry Fruits, Snacks)
- **600+ Sales Records** - 30 days of sales data (15-35 sales per day) showing high activity
- **Custom Festivals** - Active festival discounts (Holi, Spring Sale, Mega Discount Week)
- **Shopping Carts** - Sample abandoned/active carts
- **Email Logs** - 50 email send records
- **Admin Account** - Default admin for testing

## Quick Start

### 1. Run the Seed Script

```bash
python seed_realistic_data.py
```

### 2. Expected Output

```
🚀 Starting realistic data seed...
============================================================
🗑️  Clearing existing collections...
  ✓ Cleared products_update
  ✓ Cleared users
  [... more collections ...]

📦 Seeding products...
  ✓ Created 30 products

👥 Seeding users...
  ✓ Created 50 users

👷 Seeding workers...
  ✓ Created 15 workers

🔐 Seeding admin...
  ✓ Created admin user

🎉 Seeding custom festivals...
  ✓ Created 3 custom festivals

💰 Seeding sales data with high activity...
  ✓ Created 600 sales records
  💵 Total Revenue Simulated: ₹500,000+

🛒 Seeding cart data...
  ✓ Created sample carts

📧 Seeding email logs...
  ✓ Created 50 email logs

============================================================
📊 SAMPLE DATA SUMMARY
============================================================
  • Products: 30
  • Users: 50
  • Workers: 15
  • Sales Records: 600+
  • Custom Festivals: 3
  • Shopping Carts: 10
  • Email Logs: 50
  • Admin Accounts: 1

  💰 Total Sales Revenue: ₹500,000+

✅ Seeding completed successfully!
============================================================
```

## What Gets Populated

### Collections Created/Updated:

1. **products_update** - All products with variants (1kg, 500g)
2. **users** - Customer accounts with purchase history
3. **workers_update** - Worker/staff accounts
4. **user_data_bought** - Main sales transaction records
5. **products_sold** - Backup sales collection (for compatibility)
6. **custom_festivals** - Active promotional campaigns
7. **carts** - Sample shopping carts
8. **email_logs** - Email delivery history
9. **admins** - Admin accounts

### Default Credentials:

**Admin Panel:**
- Email: `admin`
- Password: `admin123`

**Worker Portal:**
- Email: `worker1@example.com` to `worker15@example.com`
- Password: `worker123`

**Users:**
- Emails: `user1@example.com` to `user50@example.com`

## Features in Sample Data

✅ **High Sales Activity** - 600+ transactions over 30 days  
✅ **Revenue Tracking** - ₹500,000+ in simulated sales  
✅ **Geographic Diversity** - Users from 8 Indian cities  
✅ **Product Categories** - Food, Vegetables, Spices, Dairy, Dry Fruits, Snacks  
✅ **Tamil Language** - All products with Tamil names  
✅ **Worker Performance** - Sales assigned to different workers  
✅ **Festival Discounts** - Active promotional campaigns  
✅ **Realistic Dates** - Sales distributed across 30 days  
✅ **Cart Data** - Abandoned/active carts for testing  
✅ **Email History** - Email logs for notification tracking  

## Home Page Will Show:

- 📊 **Total Users**: 50
- 💰 **Total Sales Revenue**: ₹500,000+
- 📦 **Total Products**: 30
- 👷 **Total Workers**: 15
- 📈 **30-Day Sales Trends** - With daily breakdown
- 🏆 **Top Performing Products** - By revenue and customer engagement
- 🛍️ **Category-wise Breakdown** - Pie chart visualization
- 📝 **Recent Transactions** - Latest 20 purchases
- 👥 **Recent Users** - Newest registrations
- 🎉 **Active Festival Promotions** - Current discounts

## Notes

- The script **clears all existing data** before seeding (use with caution on production!)
- Sales data is generated for the **last 30 days**
- All timestamps are realistic (past dates for historical data)
- Product variants have different sizes and prices
- Payment methods are randomized (Cash, Card, UPI, Online)
- All cities are real Indian locations

## Integrating with Your App

After running the seed script, restart your Flask app:

```bash
python app.py
```

Then visit:
- **Home Page**: `http://localhost:5000/`
- **Admin Dashboard**: `http://localhost:5000/admin/dashboard` (login: admin/admin123)
- **Analytics**: `http://localhost:5000/analytics`

All charts, statistics, and analytics will display realistic data! 📊
