from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/meals", response_class=HTMLResponse)
async def meals(request: Request):
    return templates.TemplateResponse("meals.html", {"request": request})
