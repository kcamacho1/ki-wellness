# KI Wellness - Food Journal & Profile Management System

A comprehensive wellness application built with Python Flask, featuring a user profile management system and an advanced food journal with nutritional tracking capabilities.

## 🌟 Features

### Profile Management
- **User Profile**: Complete profile with personal details, health metrics, and wellness goals
- **Avatar Selection**: Choose from multiple avatar options with a modal interface
- **Age Calculation**: Automatic age calculation based on date of birth
- **Weight Units**: Support for both kg and lbs with unit conversion
- **Auto-save**: Real-time form saving with user-friendly feedback

### Food Journal System
- **Nutritional Search**: Search for foods using Open Food Facts and USDA APIs
- **Food Cache**: Intelligent caching system to avoid repeated API calls
- **Serving Size Conversion**: Automatic nutritional data conversion based on user's serving size and units
- **Mood Tracking**: Track emotional state with each food entry
- **Notes System**: Add personal observations and notes to entries
- **7-Day View**: Display only the last 7 days of entries for focused tracking
- **Bulk Operations**: Select and delete multiple entries at once
- **CSV Import/Export**: Full data portability with CSV file support

## 🏗️ Architecture

### Backend Stack
- **Python 3.11.8**: Core application language
- **Flask 3.1.1**: Web framework
- **SQLAlchemy 2.0.41**: ORM for database operations
- **PostgreSQL**: Primary database
- **psycopg2-binary**: PostgreSQL adapter
- **requests**: HTTP client for API integrations

### Frontend Stack
- **TailwindCSS**: Utility-first CSS framework
- **JavaScript (ES6+)**: Frontend interactivity
- **HTML5**: Semantic markup
- **Jinja2**: Template engine

### External APIs
- **Open Food Facts**: Global food database
- **USDA FoodData Central**: Comprehensive nutritional database

## 📊 Database Schema

### User Profiles (`user_profiles`)
```sql
- id (Primary Key)
- name, date_of_birth, age
- weight, height, weight_unit
- goals, ailments, daily_activities, day_notes
- sleep_schedule, night_notes, dietary_preferences
- avatar, created_at, updated_at
```

### Food Cache (`food_cache`)
```sql
- id (Primary Key)
- food_name, brand
- serving_size, serving_unit
- calories, protein, carbs, fat, fiber, sugar, sodium
- source (openfoodfacts/usda/manual)
- created_at
```

### Food Journal (`food_journal`)
```sql
- id (Primary Key)
- user_id (Foreign Key to user_profiles)
- food_name, brand, serving_size, serving_unit
- calories, protein, carbs, fat, fiber, sugar, sodium
- mood, notes
- consumed_at, created_at
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11.8+
- PostgreSQL 12+
- pip (Python package manager)

### 1. Clone Repository
```bash
git clone <repository-url>
cd ki_wellness
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the project root:
```env
SECRET_KEY=[YOUR_SECRET_KEY]
DATABASE_URL=postgresql://postgres:[PASSWORD]@localhost/ki_wellness
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[YOUR_PASSWORD]
POSTGRES_DB=ki_wellness
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 5. Set Up Database
```bash
# Initialize database and tables
python init_db.py

# Run migrations for new features
python migrate_food_cache.py
python migrate_food_journal.py
```

### 6. Start Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 📡 API Endpoints

### Profile Management
- `GET /profile` - Profile page
- `POST /profile/save` - Save profile data
- `GET /profile/data` - Get profile data

### Food Journal
- `GET /food-journal` - Food journal page
- `POST /food-journal/search` - Search for nutritional information
- `POST /food-journal/add` - Add food entry
- `GET /food-journal/entries` - Get last 7 days of entries
- `POST /food-journal/delete` - Delete selected entries
- `GET /food-journal/export` - Export to CSV
- `POST /food-journal/import` - Import from CSV

### Static Files
- `GET /favicon.ico` - Application favicon
- `GET /avatars/<filename>` - Avatar images

## 🍎 Food Journal Features

### Nutritional Search
1. **Enter Food Name**: Type the name of the food item
2. **Set Serving Size**: Specify amount and unit (g, oz, cup, tbsp, tsp, piece, slice, ml)
3. **Search APIs**: System searches Open Food Facts first, then USDA
4. **Cache Results**: Found nutritional data is cached for future use
5. **Convert Data**: Nutritional values are automatically converted to user's serving size

### Supported Units
- **Weight**: grams (g), ounces (oz), pounds (lb), kilograms (kg)
- **Volume**: cups, tablespoons (tbsp), teaspoons (tsp), milliliters (ml), liters (l)
- **Count**: piece, slice

### Mood Tracking
Track your emotional state with each food entry:
- 😊 Happy
- 😌 Calm
- 😴 Tired
- 😤 Stressed
- 😋 Satisfied
- 😐 Neutral
- 😔 Sad
- 🤢 Sick

### Data Management
- **7-Day View**: Only shows entries from the last 7 days
- **Bulk Delete**: Select multiple entries and delete them at once
- **CSV Export**: Download your food journal as a CSV file
- **CSV Import**: Import food entries from a CSV file

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_food_journal.py
```

This will test:
- ✅ Food search functionality
- ✅ Adding food entries
- ✅ Retrieving entries
- ✅ CSV export
- ✅ Bulk deletion

## 🔧 Development

### Project Structure
```
ki_wellness/
├── app/
│   ├── main.py              # Flask application
│   ├── templates/
│   │   ├── profile.html     # Profile page
│   │   └── food_journal.html # Food journal page
│   └── static/              # Static assets
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── run.py                  # Application runner
├── init_db.py              # Database initialization
├── migrate_*.py            # Database migrations
└── test_*.py               # Test scripts
```

### Adding New Features
1. **Database Changes**: Create migration scripts
2. **Backend Logic**: Add routes in `app/main.py`
3. **Frontend**: Update templates and JavaScript
4. **Testing**: Add comprehensive tests

### API Integration
The system integrates with external APIs for nutritional data:
- **Open Food Facts**: Free, open database of food products
- **USDA FoodData Central**: Comprehensive nutritional database

## 🚀 Deployment

### Production Setup
1. **Environment Variables**: Set production environment variables
2. **Database**: Use production PostgreSQL instance
3. **Web Server**: Deploy with Gunicorn or similar
4. **Static Files**: Serve with Nginx or CDN

### Docker Support
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please open an issue on the repository.

---

**Built with ❤️ using Flask, PostgreSQL, and TailwindCSS**