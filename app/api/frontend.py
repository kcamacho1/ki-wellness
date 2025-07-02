from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.api.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user = await get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


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
