from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.supabase_client import supabase, get_user_id_from_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile")
async def view_or_create_profile(request: Request):
    token = request.cookies.get("access_token")
    user_id = await get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401)

    try:
        resp = supabase.table("profiles").select("*").eq("user_id", user_id).single().execute()
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

    update_data = {
        "name": name,
        "dob": dob,
        "weight": weight,
        "height": height,
        "goals": goals,
        "ailments": ailments,
        "notes": notes
    }

    # Ensure the record exists, else insert first
    existing = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
    if existing.data:
        supabase.table("profiles").update(update_data).eq("user_id", user_id).execute()
    else:
        update_data["user_id"] = user_id
        supabase.table("profiles").insert(update_data).execute()

    return RedirectResponse("/profile", status_code=302)
