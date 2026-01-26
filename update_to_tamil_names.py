"""
Script to update all user names to Tamil names
Replaces foreign names with authentic Tamil names
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random

load_dotenv()

# Tamil names database
TAMIL_MALE_NAMES = [
    "Aadhi", "Aakash", "Aarav", "Abishek", "Adithya", "Ajay", "Akash", "Anand", "Anil", "Anirudh",
    "Arjun", "Arun", "Arvind", "Ashok", "Ashwin", "Babu", "Balaji", "Bala", "Bharath", "Chandran",
    "Darshan", "Deepak", "Deva", "Dinesh", "Ganesh", "Gopal", "Hari", "Harish", "Ilango", "Ilaya",
    "Jagadeesh", "Jagan", "Jeeva", "Kailash", "Kalaiarasan", "Kalyan", "Kamal", "Kandan", "Karthik", "Kathir",
    "Kishore", "Krishna", "Kumar", "Kumaran", "Madhavan", "Mahesh", "Manikandan", "Manoj", "Mohan", "Mukesh",
    "Murugan", "Muthu", "Nagaraj", "Naresh", "Naveen", "Nehru", "Nithin", "Parthiban", "Prakash", "Prasanth",
    "Praveen", "Pugazh", "Rajan", "Rajesh", "Rajkumar", "Rakesh", "Ram", "Ramesh", "Ravi", "Sakthi",
    "Saravanan", "Selvan", "Senthil", "Shiva", "Siva", "Sivakumar", "Sridhar", "Srikanth", "Srinivasan", "Subash",
    "Sudarshan", "Sudhakar", "Suresh", "Surya", "Tamizh", "Thamarai", "Thiru", "Udhay", "Varun", "Velu",
    "Venkat", "Vignesh", "Vijay", "Vikram", "Vinay", "Vishnu", "Vishwa", "Yogesh"
]

TAMIL_FEMALE_NAMES = [
    "Aarthi", "Abinaya", "Ananya", "Anjali", "Anitha", "Anusha", "Archana", "Arundhati", "Bhavani", "Chithra",
    "Deepa", "Devika", "Dhanya", "Divya", "Gayathri", "Geetha", "Gomathi", "Hema", "Indira", "Ishwarya",
    "Janaki", "Jaya", "Jayalakshmi", "Jyothi", "Kala", "Kamala", "Kalpana", "Kanimozhi", "Karthika", "Kavitha",
    "Keerthi", "Kumari", "Lakshmi", "Lalitha", "Lavanya", "Latha", "Madhumitha", "Mahalakshmi", "Malini", "Meena",
    "Meenakshi", "Mohana", "Mythili", "Nandini", "Narmada", "Nila", "Padma", "Parvathi", "Pavithra", "Pooja",
    "Poorani", "Prabha", "Preethi", "Priya", "Pushpa", "Radha", "Rajalakshmi", "Raji", "Ramya", "Rashmi",
    "Revathi", "Rohini", "Rukmini", "Sangeetha", "Saranya", "Saraswathi", "Savithri", "Selvi", "Shakthi", "Shanthi",
    "Sharmila", "Shobana", "Shruti", "Sindhu", "Sivagami", "Sneha", "Sowmya", "Sri", "Sridevi", "Sujatha",
    "Sukanya", "Sumathi", "Sundari", "Swathi", "Tamilarasi", "Thamarai", "Thulasi", "Uma", "Usha", "Valli",
    "Vanitha", "Vasanthi", "Vasuki", "Vennila", "Vijaya", "Vijayalakshmi", "Vimala", "Yamuna"
]

TAMIL_SURNAMES = [
    "Kumar", "Raj", "Pandian", "Selvam", "Moorthy", "Rajan", "Nathan", "Balan", "Kannan", "Mohan",
    "Krishnan", "Murugan", "Subramanian", "Ramachandran", "Venkatesh", "Nagarajan", "Sundaram", "Karthikeyan",
    "Balakrishnan", "Ramalingam", "Annamalai", "Govindan", "Shanmugam", "Thangavel", "Perumal", "Velu",
    "Ramasamy", "Gopal", "Senthilkumar", "Manickam", "Arumugam", "Palani", "Velmurugan", "Sakthivel",
    "Ganesan", "Muthukumar", "Palanisamy", "Dhandapani", "Chinnadurai", "Muthuvel"
]

def generate_tamil_name():
    """Generate a random Tamil name with surname"""
    first_name = random.choice(TAMIL_MALE_NAMES + TAMIL_FEMALE_NAMES)
    surname = random.choice(TAMIL_SURNAMES)
    return f"{first_name} {surname}"

def generate_tamil_email(name, index):
    """Generate unique email from Tamil name with index"""
    # Remove spaces and convert to lowercase
    name_parts = name.lower().split()
    
    # Create email variations with index to ensure uniqueness
    email_formats = [
        f"{name_parts[0]}.{name_parts[1]}{index}@gmail.com",
        f"{name_parts[0]}{name_parts[1]}{index}@gmail.com",
        f"{name_parts[0]}.{name_parts[1]}{index}@yahoo.co.in",
        f"{name_parts[0]}_{name_parts[1]}{index}@outlook.com",
        f"{name_parts[0]}{index}{random.randint(10, 99)}@gmail.com",
    ]
    
    return random.choice(email_formats)

def main():
    print("="*70)
    print("UPDATING USERS TO TAMIL NAMES")
    print("="*70)
    
    # Connect to MongoDB
    MONGODB_URL = os.getenv('MONGODB_URL')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')
    
    print(f"Connecting to MongoDB...")
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    users_collection = db['users']
    
    # Get all users
    users = list(users_collection.find())
    total_users = len(users)
    
    print(f"\n✅ Found {total_users} users to update")
    print(f"📝 Updating names to Tamil names...\n")
    
    # Track used names to avoid duplicates
    used_names = set()
    used_emails = set()
    updated_count = 0
    
    for i, user in enumerate(users, 1):
        # Generate unique Tamil name
        while True:
            tamil_name = generate_tamil_name()
            if tamil_name not in used_names:
                used_names.add(tamil_name)
                break
        
        # Generate unique Tamil email
        while True:
            tamil_email = generate_tamil_email(tamil_name, i)
            if tamil_email not in used_emails:
                used_emails.add(tamil_email)
                break
        
        # Update user in database
        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'name': tamil_name,
                    'email': tamil_email
                }
            }
        )
        
        updated_count += 1
        
        # Show progress
        if i % 100 == 0 or i == total_users:
            print(f"Progress: {i}/{total_users} users updated ({(i/total_users)*100:.1f}%)")
    
    print(f"\n✅ Successfully updated {updated_count} users to Tamil names!")
    print("\n📋 Sample updated users:")
    
    # Show 10 sample users
    sample_users = list(users_collection.find().limit(10))
    for idx, user in enumerate(sample_users, 1):
        print(f"{idx}. {user.get('name')} - {user.get('email')}")
    
    print("\n" + "="*70)
    print("✅ ALL USERS NOW HAVE TAMIL NAMES!")
    print("="*70)

if __name__ == '__main__':
    main()
