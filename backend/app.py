# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ki Wellness FastAPI backend is running 🌿"}

@app.get("/api/food_journal")
def get_entries():
    response = supabase.table("food_journal").select("*").order("date", desc=True).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"entries": response.data}

@app.post("/api/food_journal")
def add_entry(entry: dict):
    response = supabase.table("food_journal").insert(entry).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"success": True}
