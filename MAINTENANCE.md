
# 📘 Ki Wellness App – Maintenance & Troubleshooting Guide

---

## 🔧 SYSTEM OVERVIEW

| Component     | Stack                          | Host/Service        |
|---------------|--------------------------------|----------------------|
| **Frontend**  | Next.js (React)                | Vercel               |
| **Backend**   | FastAPI (Python)               | Render               |
| **Database**  | Supabase (PostgreSQL, Auth)    | Supabase             |
| **APIs Used** | GPT (via OpenRouter), Nutritionix/OpenFoodFacts | Various |

---

## 🧩 DIRECTORY STRUCTURE

```
ki_wellness/
├── frontend/       # React app (Vercel)
├── backend/        # FastAPI app (Render)
│   ├── app.py
│   └── requirements.txt
├── .env.local      # Frontend environment variables
├── .env (backend)  # Backend environment variables
```

---

## 🚦 HEALTH CHECK & MONITORING

| Component  | Check Method                                         |
|------------|------------------------------------------------------|
| Backend    | Open `/api/health` or home route in browser or curl |
| Frontend   | Visit Vercel URL directly                           |
| Supabase   | Log in to dashboard and check API logs              |

---

## 🧪 MANUAL TESTING

1. Use [https://reqbin.com](https://reqbin.com) to test:
   - `POST /api/ai-nutrition-analysis`
   - `POST /api/food-lookup`

2. Or use `curl`:
```bash
curl -X POST https://your-backend.onrender.com/api/ai-nutrition-analysis \
-H "Content-Type: application/json" \
-d '{"entries":[{"food":"apple"}]}'
```

---

## ❌ COMMON ISSUES & FIXES

| Issue                                  | Cause                                | Fix                                                       |
|----------------------------------------|--------------------------------------|------------------------------------------------------------|
| CORS error                             | Frontend URL not whitelisted         | Add frontend URL in `CORSMiddleware` config in FastAPI     |
| 404 Not Found                          | Wrong route or method                | Double-check fetch URL and request type (`POST` vs `GET`)  |
| Fetch fails silently                   | Missing `await` or `.json()` call    | Check frontend fetch code logic                            |
| No data saving in Supabase             | Supabase keys misconfigured          | Check `.env` values and Supabase logs                      |

---

## 🔐 ENVIRONMENT VARIABLES

### `.env.local` (Frontend)
```
NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
```

### `.env` (Backend)
```
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

---

## 🧼 MAINTENANCE TASKS

| Frequency | Task                            |
|-----------|----------------------------------|
| Weekly    | Test all API routes              |
| Weekly    | Monitor Supabase usage & errors  |
| Monthly   | Review backend logs on Render    |
| Monthly   | Update dependencies via pip/npm  |

---

## 🔄 DEPLOYMENT NOTES

**Backend (Render):**
- Root Directory: `backend`
- Start Command: `uvicorn app:app --host 0.0.0.0 --port 10000`

**Frontend (Vercel):**
- Set `NEXT_PUBLIC_BACKEND_URL` in dashboard
