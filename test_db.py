# test_db.py
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("Testing environment variables...")
print(f"GEMINI_API_KEY: {'✅ Found' if os.getenv('GEMINI_API_KEY') else '❌ Not found'}")
print(f"MONGODB_URI: {'✅ Found' if os.getenv('MONGODB_URI') else '❌ Not found'}")

if os.getenv('MONGODB_URI'):
    print(f"MongoDB URI starts with: {os.getenv('MONGODB_URI')[:30]}...")
    
    # Test database connection
    from database import get_db
    db = get_db()
    
    if db.client:
        print("🎉 Database connection successful!")
        stats = db.get_stats()
        print(f"Database stats: {stats}")
    else:
        print("❌ Database connection failed")
else:
    print("❌ Cannot test database - MONGODB_URI not found")