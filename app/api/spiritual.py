from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/spiritual", response_class=HTMLResponse)
async def spiritual(request: Request):
    return templates.TemplateResponse("spiritual.html", {"request": request})
