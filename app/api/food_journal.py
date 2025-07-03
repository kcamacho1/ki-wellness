from fastapi import APIRouter, Request, Form, HTTPException, Path, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase, get_user_supabase
from app.api.auth import get_current_user
from openai import OpenAI
import os

import httpx
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



@router.get("/food-journal", response_class=HTMLResponse)
async def food_journal_page(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")

    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/food_journal",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
            params={
                "select": "*",
                "order": "date_logged.desc"  # ✅ no parentheses
            }
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    entries = resp.json()

    return templates.TemplateResponse(
        "food-journal.html",
        {"request": request, "entries": entries, "user": user}
    )


@router.post("/food-journal")
async def add_entry(
    request: Request,
    date_logged: str = Form(...),
    meal_type: str = Form(...),
    food_name: str = Form(...),
    servings: int = Form(...),
    serving_unit: str = Form(...),
    calories: int = Form(...),
    protein: float = Form(...),
    carbs: float = Form(...),
    fat: float = Form(...),
    mood: str = Form(None),
    notes: str = Form(None),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")

    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")

    user_id = user.get("id") or user.get("sub")

    # Prepare data
    data = {
        "user_id": user_id,
        "date_logged": date_logged,
        "meal_type": meal_type,
        "food_name": food_name,
        "servings": servings,
        "serving_unit": serving_unit,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "mood": mood,
        "notes": notes,
    }

    # Use httpx to POST
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/food_journal",
            json=data,
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Supabase insert failed: {resp.text}"
        )

    return RedirectResponse("/food-journal", status_code=302)

@router.delete("/api/food_journal/{entry_id}")
async def delete_entry(request: Request, entry_id: str = Path(...)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{SUPABASE_URL}/rest/v1/food_journal",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
            params={
                "id": f"eq.{entry_id}"
            }
        )
    if resp.status_code != 204:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": "Entry deleted."}


""" Endpoint to generate a summary of the food journal """
@router.post("/api/food_journal/summary")
async def generate_summary(data: dict = Body(...)):
    entries = data.get("entries", [])

    # Convert entries to a readable string
    entry_text = "\n".join([
        f"- {e.get('date_logged')}: {e.get('food_name')} ({e.get('calories')} kcal, {e.get('protein')}g protein, {e.get('carbs')}g carbs, {e.get('fat')}g fat)"
        for e in entries
    ])

    prompt = (
        "You are a friendly, motivational nutrition assistant. "
        "Analyze this food journal for the past 4 weeks. Return the response in three clearly separated sections titled "
        "'Summary', 'Nutritional Gaps', and 'Suggestions'. Each section should be concise, motivational and educational.\n\n"
        "Food Journal Entries:\n"
        f"{entry_text}\n\n"
        "Format:\n"
        "Summary:\n<summary text>\n\n"
        "Nutritional Gaps:\n<nutritional gaps text>\n\n"
        "Suggestions:\n<suggestions text>"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful nutrition coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        summary = completion.choices[0].message.content.strip()
        parts = summary.split("\n\n")
        sections = {}
        for part in parts:
            if part.startswith("Summary:"):
                sections["summary"] = part.replace("Summary:", "").strip()
            elif part.startswith("Nutritional Gaps:"):
                sections["gaps"] = part.replace("Nutritional Gaps:", "").strip()
            elif part.startswith("Suggestions:"):
                sections["suggestions"] = part.replace("Suggestions:", "").strip()

        return sections
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
