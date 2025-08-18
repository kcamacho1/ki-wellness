# Ki Wellness - Self Health Simplified

A comprehensive self-health application that helps users track nutrition, water intake, and mood with an intuitive and interactive dashboard.

## Features

### 🍎 Nutrition Tracking
- **Food Search**: Search for foods using Open Food Facts and USDA APIs
- **Barcode Scanner**: Scan product barcodes to get nutritional information
- **Manual Entry**: Add custom foods with nutritional data
- **Serving Size Conversion**: Automatically convert nutrition data based on your serving size
- **Food Journal**: View and manage your daily food intake

### 💧 Water Intake Monitoring
- **Daily Goal Tracking**: Monitor progress toward 64 oz daily water goal
- **Quick Add Buttons**: Easily log water intake with one-click buttons
- **Visual Progress Bar**: See your progress at a glance

### 😊 Mood & Wellness Tracking
- **Mood Logging**: Track your daily mood on a 1-5 scale
- **Daily Notes**: Record personal observations and health notes
- **Visual Feedback**: See your current mood with emojis and descriptions

### 👤 User Management
- **User Registration**: Create accounts with username, email, and name
- **Profile Management**: Update personal information, health goals, and measurements
- **Admin Accounts**: Special admin user with enhanced privileges
- **Secure Authentication**: Password-protected accounts with session management

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Quicksand Font**: Clean, modern typography
- **Interactive Dashboard**: Three vertical cards for quick overview
- **Real-time Updates**: Instant feedback and data synchronization
- **Toast Notifications**: User-friendly success and error messages

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User authentication
- **PostgreSQL/SQLite**: Database (PostgreSQL for production, SQLite for development)

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **JavaScript (ES6+)**: Modern JavaScript with async/await
- **Quicksand Font**: Google Fonts integration
- **SVG Icons**: Custom and Heroicons

### APIs
- **Open Food Facts**: Food database and barcode lookup
- **USDA FoodData Central**: Nutritional information for basic foods
- **reCAPTCHA v2**: Conditional spam protection (kiwellness.org only)

## Installation

### Prerequisites
- Python 3.8+
- pip
- PostgreSQL (for production)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ki_wellness
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   USDA_API_KEY=your-usda-api-key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin-password
   ADMIN_EMAIL=admin@kiwellness.org
   DATABASE_URL=postgresql://user:password@localhost/ki_wellness  # For production
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```
   This will create the database tables and the admin user automatically.

6. **Run the application**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard page
- `GET /profile` - User profile page
- `GET /api/dashboard-data` - Get dashboard data for a specific date

### Food Management
- `POST /api/search-food` - Search for food items
- `GET /api/product/<barcode>` - Get product by barcode
- `POST /api/food-log` - Add food to daily log
- `DELETE /api/food-log/<id>` - Remove food from log

### Health Tracking
- `POST /api/water-log` - Log water intake
- `POST /api/mood-log` - Log mood
- `POST /api/notes` - Save daily notes

### User Profile
- `GET /api/profile` - Get user profile data
- `POST /api/profile` - Update user profile

### Legal Pages
- `GET /privacy` - Privacy policy
- `GET /terms` - Terms of service
- `GET /disclaimer` - Medical disclaimer

## Database Schema

### Users
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `name`
- `age`
- `weight` (kg)
- `height` (cm)
- `health_goals`
- `is_admin`
- `created_at`

### Food Logs
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `name`
- `brand`
- `calories`, `protein`, `carbs`, `fat`, `fiber`, `sugar`, `sodium`
- `serving_size` (grams)
- `original_amount`, `original_unit`
- `quantity`
- `date`
- `timestamp`

### Water Logs
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `amount` (cups)
- `date`
- `timestamp`

### Mood Logs
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `mood` (1-5 scale)
- `date`
- `timestamp`

### Notes
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `content`
- `date`
- `timestamp`

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for sessions
- `USDA_API_KEY`: USDA FoodData Central API key
- `ADMIN_USERNAME`: Admin account username
- `ADMIN_PASSWORD`: Admin account password
- `ADMIN_EMAIL`: Admin account email
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)

### reCAPTCHA Configuration
reCAPTCHA v2 is automatically enabled when the domain is `kiwellness.org`. For other domains, it's bypassed for development purposes.

## Development

### Project Structure
```
ki_wellness/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (not in repo)
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── landing.html      # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Main dashboard
│   ├── profile.html      # User profile
│   ├── privacy.html      # Privacy policy
│   ├── terms.html        # Terms of service
│   ├── disclaimer.html   # Medical disclaimer
│   └── components/       # Modular components
│       ├── navigation.html
│       └── footer.html
└── static/               # Static assets
    ├── css/
    │   └── main.css      # Custom styles
    ├── js/
    │   └── dashboard.js  # Dashboard functionality
    └── assets/           # Images and icons
        ├── leaf.png      # Logo
        └── favicon.ico   # Favicon
```

### Adding New Features
1. Create database models in `app.py`
2. Add API endpoints for new functionality
3. Update frontend JavaScript in `static/js/dashboard.js`
4. Modify templates as needed
5. Update CSS styles in `static/css/main.css`

## Deployment

### Production Setup
1. Set up PostgreSQL database
2. Configure environment variables
3. Set up reverse proxy (nginx)
4. Use WSGI server (gunicorn)
5. Enable HTTPS
6. Configure domain for reCAPTCHA

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@kiwellness.org
- Issues: GitHub Issues page

## Acknowledgments

- Open Food Facts for food database
- USDA FoodData Central for nutritional data
- Tailwind CSS for styling framework
- Flask community for the web framework
