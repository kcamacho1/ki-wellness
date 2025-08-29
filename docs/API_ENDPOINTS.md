# Ki Wellness - API Endpoints & Database Models

## API Endpoints

### Authentication & User Management
- `GET /dashboard` - Main dashboard page (requires login)
- `GET /api/test-auth` - Test authentication status

### Dashboard Data
- `GET /api/dashboard-data?date=YYYY-MM-DD` - Get complete dashboard data for a specific date
  - Returns: food_logs, water_logs, mood_logs, notes, totals (calories, protein, carbs, fat, water)
  - Auth: Required (@login_required)

### Food Logging
- `POST /api/food-log` - Add new food entry
- `PUT /api/food-log/<int:food_id>/edit` - Edit existing food entry
  - Updates: quantity, calories, protein, carbs, fat, serving_size, date, time_of_day
  - Auth: Required (@login_required)

### Notes
- `POST /api/notes` - Save daily notes
  - Body: `{"content": "note text", "date": "YYYY-MM-DD"}`
  - Auth: Required (@login_required)
- `GET /api/mood-notes-history?date=YYYY-MM-DD` - Get mood and notes history for a date
  - Returns: mood_logs, notes arrays
  - Auth: Required (@login_required)

### Analytics & AI
- `GET /api/get-stored-analysis` - Get AI analysis of user data
  - Returns: patterns and health suggestions based on recent activity
  - Auth: Required (@login_required)

## Database Models

### User Data
```python
class User(db.Model):
    # Standard user authentication fields
    # Linked to all other models via user_id foreign key
```

### Food Tracking
```python
class FoodLog(db.Model):
    __tablename__ = 'food_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # Food name
    brand = db.Column(db.String(200))  # Food brand
    quantity = db.Column(db.Float, nullable=False)  # Serving quantity
    serving_size = db.Column(db.Float)  # Serving size in grams
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    time_of_day = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

### Water Tracking
```python
class WaterLog(db.Model):
    __tablename__ = 'water_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount in oz
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

### Mood Tracking
```python
class MoodLog(db.Model):
    __tablename__ = 'mood_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.Integer, nullable=False)  # 1-5 scale
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

### Notes
```python
class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

### Recipes
```python
class Recipe(db.Model):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    servings = db.Column(db.Integer, default=1)
    prep_time = db.Column(db.Integer)  # in minutes
    cook_time = db.Column(db.Integer)  # in minutes
    # Additional recipe fields...
```

## Frontend JavaScript Modules

### Dashboard Components
- `DashboardCore` - Main dashboard manager, data loading
- `DashboardUI` - UI updates, macros, charts
- `DashboardFood` - Food log display, editing, nutrition calculations
- `DashboardMood` - Mood display and history
- `DashboardWater` - Water tracking display
- `APIClient` - Centralized API request handling
- `FoodJournal` - Food search, selection, and logging

### Key Functions
- `loadDashboardDataOptimized()` - Efficient dashboard data loading
- `saveNotes()` - Save daily notes to database
- `saveEditedFood()` - Update existing food entries
- `updateCalculatedNutrition()` - Real-time nutrition calculation
- `refreshFoodLog()` - Refresh dashboard after food changes

## Security Middleware
- Rate limiting (60 requests/minute, whitelisted for localhost in dev)
- Bot detection and IP blocking (disabled for development IPs)
- Input validation
- CSP headers for XSS protection

## Notes for Development
- All API endpoints use `@login_required` decorator
- Frontend uses `credentials: 'same-origin'` for authenticated requests
- Real-time nutrition calculation: `newQuantityGrams / originalServingSizeGrams`
- Dashboard auto-refreshes after data changes
- Toast notifications for user feedback
- Modular architecture with separate JS files for each component

## Recent Implementation Status
✅ **Dashboard Data Loading** - Complete with authentication
✅ **Food Log Editing** - Full CRUD with real-time nutrition calculation
✅ **Notes Saving** - Connected to existing API and database
✅ **Security Middleware** - Development IP whitelisting
✅ **Real-time Updates** - Dashboard refreshes after changes
✅ **Error Handling** - Toast notifications and graceful failures

Last Updated: January 2025
