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