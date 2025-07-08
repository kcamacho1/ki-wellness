from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ai-coach", response_class=HTMLResponse)
async def ai_coach(request: Request):
    return templates.TemplateResponse("ai_coach.html", {"request": request})
