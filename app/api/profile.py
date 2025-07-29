from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase, get_user_id_from_token
from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile")
async def view_or_create_profile(request: Request):
    token = request.cookies.get("access_token")
    user_id = await get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401)

    try:
        resp = supabase.table("profile").select("*").eq("user_id", user_id).single().execute()
        profile = resp.data or {}
    except Exception as e:
        print(f"[Profile] Error fetching profile: {e}")
        profile = {}

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": profile
    })


@router.post("/profile")
async def update_profile(
    request: Request,
    name: str = Form(...),
    dob: str = Form(...),
    weight: str = Form(...),
    height: str = Form(...),
    goals: str = Form(...),
    ailments: str = Form(""),
    notes: str = Form(""),
):
    token = request.cookies.get("access_token")
    user_id = await get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401)

    try:
        dob_date = date.fromisoformat(dob.strip()) if dob else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    update_data = {
        "user_id": user_id,
        "name": name,
        "dob": dob_date.isoformat() if dob_date else None,
        "weight": weight,
        "height": height,
        "goals": goals,
        "ailments": ailments,
        "notes": notes
    }

    try:
        supabase.table("profile").upsert(update_data, on_conflict="user_id").execute()
    except Exception as e:
        print(f"[Profile] Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Could not update profile")

    return RedirectResponse("/profile", status_code=302)
