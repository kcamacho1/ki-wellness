# 🌱 Ki Wellness

**Ki Wellness** is a holistic, AI-powered health and wellness platform that combines nutrition tracking, fitness planning, spiritual growth, and AI coaching — all in one user-friendly dashboard.

The platform uses modern **React (Next.js)** frontend with a **FastAPI** backend and integrates AI-driven analysis to provide personalized recommendations for meals, workouts, and mindfulness.

---

## 🚀 Features

- **AI Health Coach** – Personalized guidance on nutrition, fitness, and spiritual wellness.
- **Food Journal** – Track daily intake with AI-powered nutrient analysis.
- **Meal Planner** – Plan and organize weekly healthy recipes.
- **Exercise Playlist** – Save and schedule fitness routines.
- **Spiritual Wellness** – Manage and explore guided meditations, affirmations, and mindfulness content.
- **Analytics Dashboard** – View progress trends with visual charts and insights.

---

## 🛠 Tech Stack

### **Frontend**
- [Next.js](https://nextjs.org/) – React framework
- [Tailwind CSS](https://tailwindcss.com/) – Styling
- [Supabase JS](https://supabase.com/docs/reference/javascript) – Auth & data fetching

### **Backend**
- [FastAPI](https://fastapi.tiangolo.com/) – Python web framework
- [Supabase](https://supabase.com/) – Database & authentication
- [OpenAI API](https://platform.openai.com/) – AI content generation
- [Nutritionix API](https://www.nutritionix.com/) – Food/nutrition data

### **Tools**
- [Vercel](https://vercel.com/) – Frontend hosting
- [Railway](https://railway.app/) – Backend hosting
- [Stripe](https://stripe.com/) – Payment processing
- [Zoom API](https://marketplace.zoom.us/docs/api-reference/introduction/) – Virtual appointments

---

## 📸 Screenshots

| AI Health Coach | Food Journal | Analytics |
|----------------|--------------|-----------|
| ![AI Health Coach](docs/screenshots/ai-coach.png) | ![Food Journal](docs/screenshots/food-journal.png) | ![Analytics Dashboard](docs/screenshots/analytics.png) |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/kcamacho1/ki-wellness.git
cd ki-wellness
```
###  2️⃣ Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
## 🔑 Environment Variables
Create a .env file in both backend and frontend with the following variables:

Backend .env
```ini
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_key
NUTRITIONIX_APP_ID=your_app_id
NUTRITIONIX_APP_KEY=your_app_key
STRIPE_SECRET_KEY=your_stripe_secret
```
Frontend .env.local
```ini
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 📌 Roadmap
 [x] Mobile-first responsive design improvements
 [x] AI-driven meal and exercise suggestions
 [ ] Food scanning with image recognition
 [ ] Social wellness challenges
 [ ] Integrations with Fitbit, Apple Health, Google Fit

## 🤝 Contributing
- We welcome contributions!
- Fork the repository
- Create a new branch: git checkout -b feature-name
- Commit your changes: git commit -m 'Add feature name'
- Push to the branch: git push origin feature-name
- Create a Pull Request

## 📄 License
This project is licensed under the MIT License – see the LICENSE file for details.

## 📬 Contact
Kristina Camacho
💼 [Portfolio](https://kcamacho1.github.io)
💌 [Email](kristina@kiwellness.org)
🐙 [GitHub](https://github.com/kcamacho1)
🔗 [LinkedIn](https://www.linkedin.com/in/kristinacassiecamacho/)