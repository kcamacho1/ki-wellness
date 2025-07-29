# Page Rendering
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.api.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Basic Routes
@router.get("/", name="homepage", response_class=HTMLResponse)
async def read_root(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "profile": user})

@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})

@router.get("/resources", response_class=HTMLResponse)
async def resources(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("resources.html", {"request": request, "user": user})

@router.get("/human-coach", response_class=HTMLResponse)
async def human_coach(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("human-coach.html", {"request": request, "user": user})

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request):
    return templates.TemplateResponse("reset-password.html", {"request": request})

@router.get("/privacy-policy", name="pravcy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("privacy-policy.html", {"request": request, "user": user})

@router.get("/tos", name="tos", response_class=HTMLResponse)
async def tos(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("tos.html", {"request": request, "user": user})

@router.get("/disclaimer", name="disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("disclaimer.html", {"request": request, "user": user})


# AI Coaching Dashboard PROTECTED Routes
@router.get("/meals", response_class=HTMLResponse)
async def meals(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("meals.html", {"request": request, "user": user})

@router.get("/exercise", response_class=HTMLResponse)
async def exercise(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("exercise.html", {"request": request, "user": user})

@router.get("/spiritual", response_class=HTMLResponse)
async def spiritual(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("spiritual.html", {"request": request, "user": user})

@router.get("/ai-coach", response_class=HTMLResponse)
async def ai_coach(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("ai-coach.html", {"request": request, "user": user, "summary": user})