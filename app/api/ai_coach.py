# app/api/coach.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase_client import get_user_profile
from app.utils.ai import generate_ai_coach_tips
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ai-coach", response_class=HTMLResponse)
async def ai_coach_dashboard(request: Request):
    try:
        user_id = request.session.get("user_id") or "dev-id"  # fallback for dev
        print("Using user_id:", user_id)

        user_data = get_user_profile(user_id)
        print("Fetched user_data:", user_data)

        tips = await generate_ai_coach_tips(user_data)
        print("Generated tips:", tips)

        return templates.TemplateResponse("ai-coach.html", {
            "request": request,
            "summary": user_data,
            "tips": tips
        })

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

