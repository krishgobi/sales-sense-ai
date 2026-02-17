"""
MongoDB Connection Test Script
This script tests your MongoDB connection independently of the main application.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test MongoDB connection with detailed error reporting"""
    
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Get credentials
    mongodb_url = os.getenv('MONGODB_URL')
    database_name = os.getenv('MONGODB_DATABASE')
    
    print(f"\n1. Environment Variables Check:")
    print(f"   - MONGODB_URL exists: {'Yes' if mongodb_url else 'No'}")
    print(f"   - MONGODB_DATABASE: {database_name if database_name else 'Not set'}")
    
    if not mongodb_url:
        print("\n❌ ERROR: MONGODB_URL not found in .env file")
        return False
    
    if not database_name:
        print("\n❌ ERROR: MONGODB_DATABASE not found in .env file")
        return False
    
    # Hide password in URL for display
    display_url = mongodb_url
    if '@' in mongodb_url:
        parts = mongodb_url.split('@')
        user_pass = parts[0].split('://')[-1]
        if ':' in user_pass:
            username = user_pass.split(':')[0]
            display_url = mongodb_url.replace(user_pass, f"{username}:****")
    
    print(f"   - Connection URL: {display_url}")
    
    print(f"\n2. Attempting to connect...")
    
    try:
        # Create client
        client = MongoClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            connectTimeoutMS=10000
        )
        
        # Test connection
        print("   - Testing connection with ping...")
        client.admin.command('ping')
        print("   ✅ Ping successful!")
        
        # Get database
        db = client[database_name]
        
        # List collections
        print(f"\n3. Database: {database_name}")
        collections = db.list_collection_names()
        print(f"   - Collections found: {len(collections)}")
        if collections:
            for col in collections:
                count = db[col].count_documents({})
                print(f"     • {col}: {count} documents")
        else:
            print("     (No collections yet)")
        
        print(f"\n✅ SUCCESS! MongoDB connection is working properly.")
        print("=" * 60)
        
        client.close()
        return True
        
    except OperationFailure as e:
        print(f"\n❌ AUTHENTICATION ERROR:")
        print(f"   Error: {e}")
        print(f"\n   Possible causes:")
        print(f"   1. Username or password is incorrect")
        print(f"   2. Database user doesn't exist")
        print(f"   3. User doesn't have proper permissions")
        print(f"\n   Solutions:")
        print(f"   1. Go to MongoDB Atlas → Database Access")
        print(f"   2. Verify or recreate the database user")
        print(f"   3. Update .env file with correct credentials")
        print("=" * 60)
        return False
        
    except ConnectionFailure as e:
        print(f"\n❌ CONNECTION ERROR:")
        print(f"   Error: {e}")
        print(f"\n   Possible causes:")
        print(f"   1. IP address not whitelisted")
        print(f"   2. Network/firewall blocking connection")
        print(f"   3. MongoDB cluster is paused or deleted")
        print(f"\n   Solutions:")
        print(f"   1. Go to MongoDB Atlas → Network Access")
        print(f"   2. Add your current IP address")
        print(f"   3. Or add 0.0.0.0/0 for testing (not for production)")
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error: {e}")
        print(f"\n   Please check:")
        print(f"   1. Connection string format in .env file")
        print(f"   2. Special characters in password are URL-encoded")
        print(f"   3. MongoDB Atlas cluster is active")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_connection()
    input("\nPress Enter to exit...")
