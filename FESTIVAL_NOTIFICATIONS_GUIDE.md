# Festival Notification System - Implementation Guide

## Overview
The Sales Sense AI now includes an automated festival-based email marketing system that sends promotional emails to users 7 days before major Indian festivals.

## ✅ Completed Tasks

### 1. User Generation (50+ Users)
- **File:** `generate_indian_users.py`
- **Users Added:** 50+ Indian users with realistic data
- **Total Users in DB:** 1,750 users
- **Features:**
  - Realistic Indian names (first and last names)
  - Indian phone numbers (+91-XXXXXXXXXX)
  - Indian email addresses (.co.in domains)
  - Indian cities, states, and 6-digit pincodes
  - Email notifications enabled by default
  - Preferred language support

### 2. Festival Calendar System
- **File:** `festival_notifications.py`
- **Festivals Configured for 2026:**
  1. **Pongal** (Jan 14) - Tamil harvest festival
  2. **Republic Day** (Jan 26) - National pride
  3. **Holi** (Mar 14) - Festival of colors
  4. **Ramadan** (Mar 23) - Holy month
  5. **Eid-ul-Fitr** (Apr 22) - Breaking the fast
  6. **Labour Day** (May 1) - Workers' day
  7. **Independence Day** (Aug 15) - Freedom celebration
  8. **Ganesh Chaturthi** (Sep 2) - Lord Ganesha
  9. **Dussehra** (Oct 13) - Victory of good over evil
  10. **Diwali** (Nov 1) - Festival of lights
  11. **Christmas** (Dec 25) - Joy and togetherness
  12. **New Year** (Jan 1, 2027) - New beginnings

### 3. Automated Email System
- **Trigger:** 7 days before each festival
- **Frequency:** Daily checks at midnight
- **Recipients:** All active users with email_notifications=True
- **Email Features:**
  - Beautiful HTML design with festival emojis
  - Personalized greetings
  - Festival-specific product recommendations
  - Discount information (10-40% based on festival)
  - Product listings with prices in ₹ (Indian Rupees)
  - Call-to-action button to shop
  - Professional branding

### 4. Product-Festival Matching
Each festival is tagged with:
- **Products:** Specific items relevant to the festival
- **Categories:** Product categories to search
- **Discounts:** Festival-specific discount ranges
- **Smart Matching:** Automatically finds products by name or category

## 🚀 How to Use

### Running the User Generator
```bash
cd sales-sense-ai
venv\Scripts\python.exe generate_indian_users.py
```

### Testing Festival Notifications
```bash
venv\Scripts\python.exe festival_notifications.py
```

### Accessing Admin Panel
1. Login as admin at: http://localhost:5000/admin/login
2. Navigate to "Festival Notifications" in the sidebar
3. View upcoming festivals and calendar
4. Click "Send Test Notifications Now" to manually trigger

### Automatic Operation
The system runs automatically when you start the app:
```bash
python app.py
```
- Festival checker runs in background
- Checks daily for upcoming festivals
- Sends emails automatically 7 days before

## 📧 Email Configuration

To enable actual email sending, configure these in your `.env` file:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Note:** For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an "App Password"
3. Use the app password in SMTP_PASSWORD

## 🎨 Email Preview

Each email includes:
- Festival-specific greeting with emoji
- Days until festival countdown
- Discount percentage highlight
- Top 10 relevant products with prices
- Stock availability indicators
- Professional footer with unsubscribe info

## 📊 Admin Dashboard Features

### Festival Notifications Page
- **System Status:** Shows active/inactive state
- **Upcoming Festivals:** Festivals in next 30 days with countdown
- **Complete Calendar:** All festivals for 2026
- **Manual Trigger:** Test button to send notifications immediately
- **Product Lists:** Shows which products match each festival
- **How It Works:** Documentation for admins

### Dashboard Stats
- Total users: 1,750
- Active users: ~1,500
- Users with email enabled: All new users
- Festivals configured: 12

## 💰 Currency Update

All prices throughout the application now display in **₹ (Indian Rupees)** instead of $.

### Updated Templates:
- `products.html` - Product catalog with variants
- `admin_dashboard.html` - Revenue and sales stats
- `cart.html` - Shopping cart prices
- `user_products.html` - User product view
- `user_detail.html` - Order history
- `worker_dashboard.html` - Worker stats

### Features:
- Proper INR symbol (₹)
- Two decimal places formatting
- Variant prices displayed correctly
- Stock indicators with color coding

## 🔧 Technical Implementation

### Background Thread
- Runs in daemon mode (doesn't block app shutdown)
- Checks every 24 hours
- Automatically restarts if app restarts
- Thread-safe database operations

### Smart Product Matching
```python
query = {
    '$or': [
        {'category': {'$in': festival_categories}},
        {'name': {'$regex': 'product_names', '$options': 'i'}}
    ],
    'is_active': True
}
```

### Email HTML Template
- Responsive design
- Works on mobile and desktop
- Gradient headers
- Product tables
- Professional styling

## 📝 Future Enhancements

1. **A/B Testing:** Test different email designs
2. **Click Tracking:** Track which products users click
3. **Purchase Attribution:** Link sales to festival emails
4. **Personalization:** Send based on user purchase history
5. **SMS Notifications:** Add SMS alongside email
6. **Regional Festivals:** Add state-specific festivals
7. **Language Support:** Send in user's preferred language

## 🐛 Troubleshooting

### Emails Not Sending
- Check SMTP credentials in `.env`
- Verify Gmail app password is correct
- Check if port 587 is not blocked
- Look for error messages in console

### No Festivals Found
- System looks 7 days ahead
- Adjust `days_ahead` parameter if needed
- Check festival dates are correct for current year

### Products Not Matching
- Verify product categories match festival config
- Check product names contain festival keywords
- Ensure products have `is_active: True`

## 📞 Support

For issues or questions:
- Check console logs for errors
- Verify MongoDB connection
- Ensure all dependencies installed
- Test email configuration separately

---

## Summary

✅ **50+ Indian users** with realistic data generated
✅ **12 festivals** configured with dates and products
✅ **Automated email system** running in background
✅ **Admin interface** for monitoring and manual triggering
✅ **INR currency** displayed throughout application
✅ **Products page** fixed to show prices and stock
✅ **Smart product matching** based on categories and names
✅ **Beautiful HTML emails** with festival themes

The system is now fully operational and will automatically send promotional emails to all active users 7 days before each Indian festival!
