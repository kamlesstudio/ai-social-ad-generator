"""
Initialize PostgreSQL Database for AI Ad Generator
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import init_db, engine, Base
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 Initializing PostgreSQL Database")
    print("=" * 50)
    
    # Show database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:studio45@127.0.0.1:5433/ai_ad_generator")
    print(f"📊 Database: {db_url}")
    
    # Check connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="ai_ad_generator",
            user="postgres",
            password="studio45",
            host="127.0.0.1",
            port="5433"
        )
        conn.close()
        print("✅ PostgreSQL connection successful!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Please check:")
        print("   - PostgreSQL is running")
        print("   - Port: 5433")
        print("   - Credentials: postgres/studio45")
        print("   - Database: ai_ad_generator")
        return
    
    # Create tables
    try:
        init_db()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return
    
    print("\n🎉 Database ready for AI Ad Generator!")
    print("\n📊 Tables created:")
    print("   - users")
    print("   - videos")
    print("   - purchases")

if __name__ == "__main__":
    main()