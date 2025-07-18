# /app/api/csv_upload.py
from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
TEMP_CSV_PATH = "temp_upload.csv"

@router.post("/upload-csv-preview", response_class=HTMLResponse)
async def upload_csv_preview(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    with open(TEMP_CSV_PATH, "wb") as f:
        f.write(contents)
    df = pd.read_csv(TEMP_CSV_PATH)
    csv_columns = list(df.columns)
    required_fields = ["date", "meal_type", "food_name", "quantity", "unit", "calories", "protein", "carbs", "fat", "notes"]
    return templates.TemplateResponse("partials/csv_field_mapper.html", {
        "request": request,
        "csv_columns": csv_columns,
        "required_fields": required_fields
    })

@router.post("/map-fields")
async def map_fields(request: Request, mapping: dict = Form(...)):
    df = pd.read_csv(TEMP_CSV_PATH)
    # Flatten mapping: {'mapping[date]': 'Date'} => {'date': 'Date'}
    cleaned_mapping = {k.split("[")[1][:-1]: v for k, v in mapping.items()}
    df = df.rename(columns=cleaned_mapping)

    # Basic cleaning example
    def clean_numeric(val):
        try:
            return float(str(val).strip().replace("g", "").replace("cup", "").split()[0])
        except:
            return None

    df["quantity"] = df["quantity"].apply(clean_numeric)
    df["protein"] = df["protein"].apply(clean_numeric)
    df["carbs"] = df["carbs"].apply(clean_numeric)
    df["fat"] = df["fat"].apply(clean_numeric)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["user_id"] = "test-user-id-001"  # Replace with actual session user_id

    # Upload to Supabase or DB here
    # supabase.table("food_journal").insert(df.to_dict(orient="records"))

    os.remove(TEMP_CSV_PATH)
    return RedirectResponse("/food-journal", status_code=303)