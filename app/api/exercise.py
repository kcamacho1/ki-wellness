from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/exercise", response_class=HTMLResponse)
async def exercise(request: Request):
    return templates.TemplateResponse("exercise.html", {"request": request})
