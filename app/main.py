from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Mount static files (Tailwind, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Simple in-memory storage (replace with DB later)
food_entries = []

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    # Here you'd validate against Supabase if desired
    response = RedirectResponse("/", status_code=302)
    return response

@app.get("/food-journal", response_class=HTMLResponse)
def food_journal(request: Request):
    return templates.TemplateResponse(
        "food_journal.html", 
        {"request": request, "entries": food_entries}
    )

@app.post("/food-journal")
def add_entry(
    date_logged: str = Form(...),
    meal: str = Form(...),
    calories: int = Form(...),
    protein: int = Form(...),
    carbs: int = Form(...),
    fat: int = Form(...),
    notes: str = Form(None),
):
    food_entries.append({
        "date_logged": date_logged,
        "meal": meal,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "notes": notes
    })
    return RedirectResponse("/food-journal", status_code=302)
