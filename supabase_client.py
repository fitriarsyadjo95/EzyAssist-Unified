from supabase import create_client, Client
import os
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    else:
        print("Supabase URL or KEY missing")
        supabase = None
except Exception as e:
    print(f"Supabase initialization error: {e}")
    print("Continuing without Supabase - bot will still work for basic functions")
    supabase = None

class SupabaseClient:
    def __init__(self):
        self.client = supabase

    async def upsert_user(self, telegram_id: str):
        """Insert or update user in the users table"""
        if not self.client:
            print("Supabase client not initialized")
            return None

        try:
            data = {
                "telegram_id": telegram_id,
                "last_seen_at": datetime.utcnow().isoformat(),
                "engagement": 0
            }

            result = self.client.table("users").upsert(data, on_conflict="telegram_id").execute()
            return result
        except Exception as e:
            print(f"Error upserting user: {e}")
            return None

    async def update_user_last_seen(self, telegram_id: str):
        """Update user's last seen timestamp"""
        if not self.client:
            print("Supabase client not initialized")
            return None

        try:
            data = {
                "last_seen_at": datetime.utcnow().isoformat()
            }

            result = self.client.table("users").update(data).eq("telegram_id", telegram_id).execute()
            return result
        except Exception as e:
            print(f"Error updating user last seen: {e}")
            return None

def upload_image_and_get_url(base64_string, filename):
    if not supabase:
        print("Supabase client not available for upload")
        return ""

    try:
        file_data = base64.b64decode(base64_string.split(",")[1])
        supabase.storage.from_("proofs").upload(filename, file_data)
        return supabase.storage.from_("proofs").get_public_url(filename)
    except Exception as e:
        print(f"Error uploading image: {e}")
        return ""