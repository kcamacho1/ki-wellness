from datetime import datetime
from fastapi import APIRouter, Request, Form, HTTPException, Path, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase, get_user_supabase
from app.core.supabase_client import SUPABASE_URL, SUPABASE_ANON_KEY, get_user_id_from_token
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY
from app.api.auth import get_current_user
from app.utils.gpt_client import basic_nutrition_prompt


from pydantic import BaseModel
import httpx
import os


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class DeleteRequest(BaseModel):
    ids: list[str]

class CsvUploadRequest(BaseModel):
    entries: list[dict]

@router.post("/add-food-entry")
async def add_food_entry(request: Request, payload: dict = Body(...)):
    token = request.cookies.get("access_token")
    user_id = await get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    food_name = payload["food_name"]
    servings = float(payload["servings"])
    serving_unit = payload["serving_unit"]

    # Step 1: check food_cache
    cache_resp = supabase.table("food_cache").select("*").eq("food_name", food_name).single().execute()
    nutrients = cache_resp.data if cache_resp.data else None

    # Step 2: try OpenFoodFacts
    if not nutrients:
        nutrients = await query_openfood(food_name)

    # Step 3: fallback to GPT
    if not nutrients:
        nutrients = await query_gpt_estimate(food_name)

    if not nutrients:
        raise HTTPException(status_code=404, detail="Nutrient data not found.")

    # Optionally store in food_cache
    if not cache_resp.data:
        supabase.table("food_cache").insert({**{"food_name": food_name}, **nutrients}).execute()

    # Save to food_journal
    entry = {
        "user_id": user_id,
        "date_logged": datetime.utcnow().date().isoformat(),
        "food_name": food_name,
        "meal_type": "unspecified",
        "servings": servings,
        "serving_unit": serving_unit,
        "calories": round(servings * nutrients.get("calories", 0)),
        "protein": round(servings * nutrients.get("protein", 0), 2),
        "carbs": round(servings * nutrients.get("carbs", 0), 2),
        "fat": round(servings * nutrients.get("fat", 0), 2),
        **{k: round(servings * nutrients.get(k, 0), 2)
           for k in nutrients if k.startswith("vitamin_") or k in ["iron", "zinc", "magnesium", "potassium"]}
    }

    supabase.table("food_journal").insert(entry).execute()
    return {"message": "Food entry added."}

# GPT fallback
async def query_gpt_estimate(food_name: str):
    try:
        prompt = f"Estimate basic nutrition (calories, protein, carbs, fat) for 100g of {food_name} in JSON with those 4 keys only."
        return await basic_nutrition_prompt(prompt)
    except Exception as e:
        print(f"[GPT] fallback error: {e}")
        return None

# OpenFoodFacts
async def query_openfood(food_name):
    url = "https://world.openfoodfacts.org/cgi/search.pl"
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
            # Add more micros if needed
        }


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

@router.post("/delete-food-entries")
async def delete_food_entries(request: Request, req: DeleteRequest):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        async with httpx.AsyncClient() as client:
            for entry_id in req.ids:
                await client.delete(
                    f"{SUPABASE_URL}/rest/v1/food_journal",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {token}",
                    },
                    params={"id": f"eq.{entry_id}"}
                )
        return {"message": "Entries deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/upload-csv-entries")
async def upload_csv_entries(request: Request, req: CsvUploadRequest):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Fetch user_id from Supabase auth
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            }
        )

        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Unable to verify user.")

        user_data = user_resp.json()
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user ID")

        # Insert entries with user_id
        for entry in req.entries:
            entry["user_id"] = user_id
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/food_journal",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                    "Prefer": "return=representation"
                },
                json=entry
            )
            print("Upload response:", response.status_code, response.text)

    return {"message": "CSV entries uploaded"}

async def query_gpt_estimate(food_name: str) -> dict:
    try:
        prompt = f"Estimate basic nutrition (calories, protein, carbs, fat) for 100g of {food_name} in JSON format with keys: calories, protein, carbs, fat."
        result = await basic_nutrition_prompt(prompt)
        return result if result else {}
    except Exception as e:
        print(f"[GPT] Fallback failed: {e}")
        return {}