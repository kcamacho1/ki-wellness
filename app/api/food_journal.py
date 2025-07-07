from fastapi import APIRouter, Request, Form, HTTPException, Path, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase, get_user_supabase
from app.api.auth import get_current_user
import httpx
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

""" Free OpenFood API """
async def query_openfood(food_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "fields": "product_name,nutriments"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data["count"] == 0:
            return None
        nutriments = data["products"][0].get("nutriments", {})
        return {
            "calories": nutriments.get("energy-kcal_100g", 0),
            "protein": nutriments.get("proteins_100g", 0),
            "carbs": nutriments.get("carbohydrates_100g", 0),
            "fat": nutriments.get("fat_100g", 0),
            "vitamin_a": nutriments.get("vitamin-a_100g", 0),
            "vitamin_c": nutriments.get("vitamin-c_100g", 0),
            "vitamin_d": nutriments.get("vitamin-d_100g", 0),
            "vitamin_e": nutriments.get("vitamin-e_100g", 0),
            "vitamin_k": nutriments.get("vitamin-k_100g", 0),
            "vitamin_b1": nutriments.get("vitamin-b1_100g", 0),
            "vitamin_b2": nutriments.get("vitamin-b2_100g", 0),
            "vitamin_b3": nutriments.get("vitamin-pp_100g", 0),
            "vitamin_b6": nutriments.get("vitamin-b6_100g", 0),
            "vitamin_b12": nutriments.get("vitamin-b12_100g", 0),
            "folate": nutriments.get("folate_100g", 0),
            "calcium": nutriments.get("calcium_100g", 0),
            "iron": nutriments.get("iron_100g", 0),
            "magnesium": nutriments.get("magnesium_100g", 0),
            "potassium": nutriments.get("potassium_100g", 0),
            "zinc": nutriments.get("zinc_100g", 0),
            "sodium": nutriments.get("sodium_100g", 0),
            "copper": nutriments.get("copper_100g", 0),
            "selenium": nutriments.get("selenium_100g", 0),
            "manganese": nutriments.get("manganese_100g", 0),
        }

"""Nutritionix API is more reliable for US foods, so we use it as a fallback"""
async def query_nutritionix(food_name):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": os.getenv("NUTRITIONIX_APP_ID"),
        "x-app-key": os.getenv("NUTRITIONIX_APP_KEY"),
        "Content-Type": "application/json"
    }
    body = {"query": food_name}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get("foods"):
            return None
        f = data["foods"][0]
        return {
            "calories": f["nf_calories"],
            "protein": f["nf_protein"],
            "carbs": f["nf_total_carbohydrate"],
            "fat": f["nf_total_fat"],
            # Micronutrients may be sparse here
            "vitamin_a": f.get("full_nutrients", [{}])[0].get("value", 0),
            "vitamin_c": f.get("full_nutrients", [{}])[0].get("value", 0),
            # Add other micros as needed
        }


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
                "order": "date_logged.desc"
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
