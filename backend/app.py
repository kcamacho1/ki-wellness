from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Enable CORS for frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://www.kiwellness.org", "https://kiwellness.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class EntryRequest(BaseModel):
    entries: List[Dict]

@app.post("/api/ai-nutrition-analysis")
async def analyze_nutrition(data: EntryRequest):
    # TODO: Replace with your GPT/OpenRouter logic
    return {
        "summary": "Analysis complete",
        "received_entries": data.entries
    }
