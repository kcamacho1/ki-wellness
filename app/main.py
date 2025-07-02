from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import auth, frontend, food_journal
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth.router)
app.include_router(frontend.router)
app.include_router(food_journal.router)
