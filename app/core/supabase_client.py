from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env regardless of import order
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase credentials are missing. Check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_user_supabase(token: str):
    """
    Returns a Supabase client using the user's access token for RLS.
    """
    from app.core.config import SUPABASE_URL
    return create_client(SUPABASE_URL, token)

def get_user_profile(user_id: str) -> dict:
    try:
        response = supabase.table("Users").select("*").eq("id", user_id).single().execute()
        return response.data if response.data else {}
    except Exception as e:
        print(f"[Supabase] Failed to fetch user: {e}")
        # fallback mock data for local dev
        return {
            "id": user_id,
            "name": "Demo User",
            "calories_today": 1550,
            "sleep_hours": 7.5,
            "mood": "Neutral",
            "goals": "energy and tone"
        }
