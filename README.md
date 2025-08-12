# Ki Wellness - Your Personal AI Health Coach

A simple, safe, and affordable wellness application built by someone who understands your journey. Get personalized guidance from AI and human coaches to track your health, nutrition, and wellness goals.

## 🌟 What Makes Ki Wellness Different

### 🤖 **AI Health Coach**
- **Personalized AI Guidance**: Get intelligent insights and recommendations from your AI Health Coach
- **Pay Only for What You Use**: Buy AI sessions as you need them, no subscriptions required
- **Evidence-Based Data**: All recommendations based on reputable sources (ISSA, NIH, PubMed, PhD research)

### 👩‍💼 **Built by Someone Who Understands**
- **Founder's Story**: Created by Kristina, who needed simple wellness tracking herself
- **Expert Background**: Software development, project management, nutrition, and personal training
- **Mission-Driven**: Your donations fund health awareness, keep the app affordable, and support education

### 🛡️ **Safe & Affordable**
- **Free to Try**: Start your wellness journey completely free
- **No Hidden Fees**: Transparent pricing, no pressure
- **Human Coach Available**: Get personalized guidance from a real coach (donation-based)

## 🚀 Key Features

### AI Health Coach
- **Personalized Insights**: Get AI-powered analysis of your nutrition and mood patterns
- **Smart Recommendations**: Receive customized guidance based on your unique data
- **Session-Based Pricing**: Buy AI coaching sessions as you need them

### Human Coach Support
- **Real Coach Guidance**: Connect with a certified human coach
- **Donation-Based Pricing**: Accessible to everyone regardless of budget
- **Personalized Support**: Get one-on-one guidance for your specific needs

### Simple Wellness Tracking
- **Food Journal**: Easy meal tracking with nutritional information
- **Mood Tracking**: Monitor your emotional state and wellness patterns
- **Dashboard Insights**: Clear overview of your wellness journey
- **Mobile Friendly**: Access your data anywhere, anytime

### Evidence-Based Approach
- **Reputable Sources**: Data from ISSA, NIH, PubMed, and peer-reviewed research
- **Scientific Backing**: All recommendations based on credible health research
- **Transparent Methods**: Clear explanation of data sources and methodologies

## 🏗️ Technical Architecture

### Backend Stack
- **Python 3.11+**: Core application language
- **Flask 3.1.1**: Lightweight web framework
- **SQLAlchemy 2.0.41**: Database ORM
- **PostgreSQL**: Primary database
- **Stripe**: Payment processing for AI sessions
- **OpenAI API**: AI coaching capabilities

### Frontend Stack
- **TailwindCSS**: Modern, utility-first styling
- **JavaScript (ES6+)**: Interactive features
- **HTML5**: Semantic markup
- **Jinja2**: Template engine

### Security & Privacy
- **Enterprise-Grade Security**: Your data is protected
- **Privacy First**: Your wellness journey stays private
- **Secure Payments**: Stripe-powered payment processing
- **Data Encryption**: All sensitive data is encrypted

## 📊 Database Schema

### Core Tables
- **Users**: User accounts and authentication
- **User Profiles**: Personal details, health metrics, goals
- **Food Journal**: Meal tracking and nutritional data
- **Mood Entries**: Emotional state tracking
- **AI Usage Sessions**: AI coaching session tracking
- **Session Credits**: AI session credit management
- **User Subscriptions**: Subscription management
- **System Settings**: Application configuration

### Payment & Billing
- **Stripe Integration**: Secure payment processing
- **Session Credits**: Pay-per-use AI coaching
- **Donation System**: Human coach accessibility
- **Subscription Management**: Flexible billing options

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Stripe account (for payments)
- OpenAI API key (for AI features)

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
# Application
SECRET_KEY=[YOUR_SECRET_KEY]
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@localhost/ki_wellness
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[YOUR_PASSWORD]
POSTGRES_DB=ki_wellness
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Stripe (Live)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe (Sandbox)
STRIPE_SANDBOX_PUBLISHABLE_KEY=pk_test_...
STRIPE_SANDBOX_SECRET_KEY=sk_test_...
STRIPE_SANDBOX_WEBHOOK_SECRET=whsec_...

# OpenAI
OPENAI_API_KEY=sk-...

# Google reCAPTCHA
RECAPTCHA_SITE_KEY=...
RECAPTCHA_SECRET_KEY=...
```

### 5. Initialize Database
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 🎯 Core Features

### AI Health Coach
- **Chat Interface**: Direct conversation with your AI coach
- **Nutritional Analysis**: AI-powered food recommendations
- **Mood Insights**: Pattern recognition and emotional wellness guidance
- **Goal Setting**: Personalized goal creation and tracking
- **Progress Monitoring**: AI-driven progress analysis

### Human Coach Integration
- **Coach Matching**: Connect with certified wellness coaches
- **Donation System**: Flexible pricing based on your budget
- **Scheduling**: Easy appointment booking
- **Follow-up Support**: Ongoing guidance and accountability

### Wellness Tracking
- **Food Journal**: Simple meal logging with nutritional data
- **Mood Tracking**: Daily emotional state monitoring
- **Sleep Tracking**: Sleep quality and patterns
- **Activity Logging**: Exercise and movement tracking
- **Goal Progress**: Visual progress tracking

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Test admin dashboard functionality
python tests/test_admin_tabs.py

# Test username validation
python tests/test_username_validation.py

# Test other features
python tests/test_*.py
```

## 🔧 Development

### Project Structure
```
ki_wellness/
├── app/
│   ├── main.py              # Flask application & routes
│   ├── templates/           # HTML templates
│   │   ├── landing.html     # Homepage
│   │   ├── dashboard.html   # User dashboard
│   │   ├── ai_self_health.html # AI coaching interface
│   │   ├── coaching.html    # Human coaching
│   │   ├── food_journal.html # Food tracking
│   │   ├── profile.html     # User profile
│   │   ├── settings.html    # User settings
│   │   └── admin_dashboard.html # Admin panel
│   └── static/              # Static assets
├── tests/                   # Test suite
├── docs/                    # Documentation
│   ├── setup/              # Setup guides
│   ├── development/        # Development docs
│   └── private/           # Private documentation
├── cleanup_backup/         # Migration scripts
├── config.py              # Configuration
├── requirements.txt       # Dependencies
└── run.py                # Application runner
```

### Key Components
- **AI Coaching Engine**: OpenAI-powered health guidance
- **Payment System**: Stripe integration for session credits
- **Admin Dashboard**: Business management and monitoring
- **User Management**: Authentication and profile system
- **Data Analytics**: Wellness pattern analysis

## 🚀 Deployment

### Render Deployment
The application is configured for deployment on Render:

1. **Connect Repository**: Link your GitHub repository
2. **Environment Variables**: Set all required environment variables
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python run.py`

### Environment Configuration
- **Production Database**: PostgreSQL on Render
- **Payment Processing**: Stripe live keys
- **AI Services**: OpenAI API
- **Security**: reCAPTCHA protection

## 💰 Pricing Model

### AI Health Coach
- **Free Trial**: Start with free features
- **Session Credits**: $1 per AI coaching session
- **Custom Quantities**: Buy as many sessions as you need
- **No Subscriptions**: Pay only for what you use

### Human Coach
- **Donation-Based**: Pay what you can afford
- **Flexible Pricing**: No set rates
- **Accessible**: Available to everyone
- **Certified Coaches**: Qualified wellness professionals

## 📈 Business Dashboard

### Admin Features
- **Financial Tracking**: Revenue, costs, and profit monitoring
- **User Analytics**: User growth and engagement metrics
- **AI Cost Management**: Token usage and cost optimization
- **System Settings**: Application configuration
- **Emergency Controls**: Quick system management

### Key Metrics
- **Monthly Revenue**: Track income from AI sessions
- **Monthly Costs**: Monitor AI API costs and expenses
- **Customer Growth**: User acquisition and retention
- **Profitability**: Real-time profit/loss analysis

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Email**: Contact through the application
- **Documentation**: Check `/docs` for detailed guides
- **Issues**: Report bugs on GitHub

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **ISSA**: International Sports Sciences Association
- **NIH**: National Institutes of Health
- **PubMed**: Medical research database
- **OpenAI**: AI coaching capabilities
- **Stripe**: Payment processing
- **Our Community**: Users who share their wellness journeys

---

**Built with ❤️ by Kristina - A developer who understands your wellness journey**

*"Wellness doesn't have to be complicated or expensive. It should be simple, safe, and accessible to everyone."*