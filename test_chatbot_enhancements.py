#!/usr/bin/env python3
"""
Test script for AI Chatbot Enhancements
Tests all new functions and chatbot query types
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Test imports
try:
    from app import (
        app, db, users, products_update, user_data_bought, workers_update,
        get_all_festival_offers, get_user_data, get_top_users_and_products,
        get_product_recommendations, get_revenue_by_date_range, process_admin_query
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_festival_offers():
    """Test festival offers retrieval"""
    print("\n🎉 Testing Festival Offers...")
    try:
        offers = get_all_festival_offers()
        print(f"  ✅ Retrieved {len(offers)} festival offers")
        
        # Check for Mother's Day
        mothers_day = [o for o in offers if 'mother' in o['name'].lower()]
        if mothers_day:
            print(f"  ✅ Found Mother's Day: {mothers_day[0]['name']} on {mothers_day[0]['days_until']} days")
        else:
            print(f"  ⚠️  Mother's Day not found in offers")
        
        # Check for Labour Day
        labour_day = [o for o in offers if 'labour' in o['name'].lower()]
        if labour_day:
            print(f"  ✅ Found Labour Day: {labour_day[0]['name']}")
        else:
            print(f"  ⚠️  Labour Day not found in offers")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_user_data():
    """Test user data retrieval"""
    print("\n👤 Testing User Data...")
    try:
        # Get all users
        all_users = get_user_data()
        print(f"  ✅ Retrieved {len(all_users)} users")
        
        # Try to get specific user if any exist
        if all_users:
            user_name = all_users[0].get('name', '')
            if user_name:
                user_data = get_user_data(user_name)
                if user_data:
                    print(f"  ✅ Retrieved user data for: {user_data.get('name', 'Unknown')}")
                    print(f"     - Total Spent: ₹{user_data.get('total_spent', 0):.2f}")
                    print(f"     - Total Orders: {user_data.get('total_orders', 0)}")
                else:
                    print(f"  ⚠️  User '{user_name}' not found")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_dashboard():
    """Test worker dashboard data"""
    print("\n👷 Testing Worker Dashboard...")
    try:
        dashboard = get_top_users_and_products()
        
        print(f"  ✅ Top Users: {len(dashboard['top_users'])} users")
        for i, user in enumerate(dashboard['top_users'][:3], 1):
            print(f"     {i}. {user['name']} - ₹{user['spent']:.2f} ({user['orders']} orders)")
        
        print(f"  ✅ Top Products: {len(dashboard['top_products'])} products")
        for i, product in enumerate(dashboard['top_products'][:3], 1):
            print(f"     {i}. {product['name']} - ₹{product['revenue']:.2f}")
        
        print(f"  ✅ Top Categories: {len(dashboard['top_categories'])} categories")
        for i, cat in enumerate(dashboard['top_categories'][:3], 1):
            print(f"     {i}. {cat['name']} - ₹{cat['revenue']:.2f}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_recommendations():
    """Test product recommendations"""
    print("\n📦 Testing Product Recommendations...")
    try:
        recommendations = get_product_recommendations()
        
        print(f"  ✅ Products to Buy Now: {len(recommendations['buy_now'])}")
        for i, p in enumerate(recommendations['buy_now'][:3], 1):
            print(f"     {i}. {p['name']} - {p['reason']}")
        
        print(f"  ✅ Products to Stop Buying: {len(recommendations['stop_buying'])}")
        for i, p in enumerate(recommendations['stop_buying'][:3], 1):
            print(f"     {i}. {p['name']} - {p['reason']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_revenue_by_date():
    """Test revenue by date queries"""
    print("\n💰 Testing Revenue by Date...")
    try:
        # Today's revenue
        today_revenue = get_revenue_by_date_range(specific_date=datetime.now().strftime('%Y-%m-%d'))
        print(f"  ✅ Today's Revenue: ₹{today_revenue['revenue']:.2f} ({today_revenue['orders']} orders)")
        
        # Last 7 days
        start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        weekly_revenue = get_revenue_by_date_range(start_date=start, end_date=end)
        print(f"  ✅ Last 7 Days Revenue: ₹{weekly_revenue['revenue']:.2f}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chatbot_queries():
    """Test enhanced process_admin_query"""
    print("\n💬 Testing Chatbot Queries...")
    
    test_queries = [
        ("hi", "Greeting"),
        ("show all festival offers", "Festival Offers"),
        ("find user", "User Data Lookup"),
        ("worker dashboard", "Worker Dashboard"),
        ("product recommendations", "Product Recommendations"),
        ("revenue today", "Revenue Query"),
        ("what's my revenue last 7 days", "Revenue 7 Days"),
    ]
    
    all_passed = True
    for query, query_type in test_queries:
        try:
            response = process_admin_query(query)
            if response:
                print(f"  ✅ {query_type}: Got response ({len(response)} chars)")
            else:
                print(f"  ⚠️  {query_type}: Empty response")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {query_type}: Error - {e}")
            all_passed = False
    
    return all_passed

def main():
    print("=" * 60)
    print("AI CHATBOT ENHANCEMENTS - TEST SUITE")
    print("=" * 60)
    
    # Check database connection
    try:
        if db is None:
            print("⚠️  WARNING: Database connection is None - some tests may fail")
            print("   Make sure MongoDB is running and connected\n")
    except Exception as e:
        print(f"⚠️  Database check failed: {e}\n")
    
    results = {}
    
    # Run all tests
    results['Festival Offers'] = test_festival_offers()
    results['User Data'] = test_user_data()
    results['Worker Dashboard'] = test_worker_dashboard()
    results['Product Recommendations'] = test_product_recommendations()
    results['Revenue by Date'] = test_revenue_by_date()
    results['Chatbot Queries'] = test_chatbot_queries()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhancements are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
