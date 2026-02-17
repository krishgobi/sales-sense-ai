"""
Password URL Encoder for MongoDB Connection Strings
Use this to properly encode passwords with special characters.
"""

from urllib.parse import quote_plus

def encode_password():
    """Encode a password for use in MongoDB connection strings"""
    
    print("=" * 60)
    print("MongoDB Password URL Encoder")
    print("=" * 60)
    print("\nSpecial characters in passwords need to be URL-encoded")
    print("for MongoDB connection strings.")
    print("\nExamples of special characters: @ : / ? # [ ] % $ & + , ; = ")
    print("=" * 60)
    
    password = input("\nEnter your MongoDB password: ")
    
    if not password:
        print("❌ No password entered!")
        return
    
    # Encode the password
    encoded = quote_plus(password)
    
    print(f"\n📋 Results:")
    print(f"   Original password: {password}")
    print(f"   Encoded password:  {encoded}")
    
    if password == encoded:
        print("\n✅ Your password doesn't need encoding (no special characters)")
    else:
        print("\n⚠️  Your password contains special characters and has been encoded")
        print("   Use the ENCODED password in your MongoDB connection string")
    
    print("\n" + "=" * 60)
    print("Example connection string:")
    print("=" * 60)
    username = input("\nEnter your MongoDB username: ") or "your_username"
    
    example_url = f"mongodb+srv://{username}:{encoded}@cluster0.rigkacg.mongodb.net/?retryWrites=true&w=majority"
    
    print(f"\nMONGODB_URL={example_url}")
    print("\n📝 Copy this line to your .env file")
    print("=" * 60)

if __name__ == "__main__":
    try:
        encode_password()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    
    input("\nPress Enter to exit...")
