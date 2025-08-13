#!/usr/bin/env python3
"""
Database migration script to add registration flow tracking fields
"""

import os
import sys
from sqlalchemy import create_engine, text
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Add the new registration tracking columns to existing database"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable not found")
        return False
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔄 Starting migration to add registration tracking fields...")
            
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if columns already exist
                check_columns = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'vip_registrations' 
                    AND column_name IN ('account_setup_action', 'account_setup_completed_at', 'step_completed')
                """)
                
                existing_columns = [row[0] for row in conn.execute(check_columns)]
                print(f"📊 Existing tracking columns: {existing_columns}")
                
                # Add account_setup_action column if it doesn't exist
                if 'account_setup_action' not in existing_columns:
                    print("➕ Adding account_setup_action column...")
                    conn.execute(text("""
                        ALTER TABLE vip_registrations 
                        ADD COLUMN account_setup_action VARCHAR(20)
                    """))
                    print("✅ account_setup_action column added")
                else:
                    print("⏭️  account_setup_action column already exists")
                
                # Add account_setup_completed_at column if it doesn't exist
                if 'account_setup_completed_at' not in existing_columns:
                    print("➕ Adding account_setup_completed_at column...")
                    conn.execute(text("""
                        ALTER TABLE vip_registrations 
                        ADD COLUMN account_setup_completed_at TIMESTAMP
                    """))
                    print("✅ account_setup_completed_at column added")
                else:
                    print("⏭️  account_setup_completed_at column already exists")
                
                # Add step_completed column if it doesn't exist
                if 'step_completed' not in existing_columns:
                    print("➕ Adding step_completed column...")
                    conn.execute(text("""
                        ALTER TABLE vip_registrations 
                        ADD COLUMN step_completed INTEGER DEFAULT 0
                    """))
                    print("✅ step_completed column added")
                else:
                    print("⏭️  step_completed column already exists")
                
                # Update existing records to have step_completed = 2 (both steps completed)
                # since they were created before the two-step flow
                print("🔄 Updating existing records to mark as completed...")
                result = conn.execute(text("""
                    UPDATE vip_registrations 
                    SET step_completed = 2 
                    WHERE step_completed IS NULL OR step_completed = 0
                """))
                
                updated_count = result.rowcount
                print(f"✅ Updated {updated_count} existing records to step_completed = 2")
                
                # Commit the transaction
                trans.commit()
                print("🎉 Migration completed successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)