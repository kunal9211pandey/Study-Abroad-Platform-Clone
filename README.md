# Apply Board Clone - Study Abroad Platform

## Overview
This is a comprehensive Flask-based web application that replicates ApplyBoard's core functionality. The platform helps international students discover, apply to, and manage applications for universities and programs worldwide. It features complete user authentication, payment processing, admin management, and real university data integration.

## Features
- Complete user authentication with role-based access
- Student and admin dashboards
- Payment processing integration using Stripe
- Real university API integration framework
- University and program search with filters
- Sample data with universities and programs
- Logging and session management for development and debugging

## Technologies
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend**: Jinja2 templates, Bootstrap 5.3.0, Font Awesome 6.4.0
- **Database**: Initially JSON files; PostgreSQL support possible via `psycopg2`
- **Payment**: Stripe API
- **Environment Management**: `python-dotenv` for environment variables

## Installation

1. Clone the repository:

bash
git clone <your-repo-url>
cd ApplyClone 

2. (Optional) Create and activate a virtual environment:

python -m venv venv
### Windows
.\venv\Scripts\activate
### macOS/Linux
source venv/bin/activate

3. Install dependencies:

pip install -r requirements.txt

4. Set environment variables (optional):

# Windows PowerShell
$env:DATABASE_URL="sqlite:///mydatabase.db"

$env:SESSION_SECRET="your-secret-key"

5. Running the App
python main.py

6. The app will run on:
http://0.0.0.0:5000

## Notes

Use a valid DATABASE_URL for database integration (default: SQLite).

Stripe API keys must be configured for payment functionality.


## Known Issues

Some routes in routes.py may be incomplete

Currently uses JSON files for storage; database integration may be needed

Authentication/login routes may require full implementation

Limited error handling for missing/malformed files




## Recommended Enhancements

Complete search and form routes

Add full authentication system

Integrate a proper database (e.g., PostgreSQL or Drizzle ORM)

Add CSRF protection and input validation

Implement error pages and logging improvements
