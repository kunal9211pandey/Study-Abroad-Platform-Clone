# ApplyBoard Clone - Study Abroad Platform

## Overview
This is a Flask-based web application replicating ApplyBoard's core functionality. The platform helps international students discover, apply to, and manage applications for universities and programs worldwide. It includes user authentication, payment processing, admin management, and real university data integration.

## Features
- User authentication with role-based access
- Student and admin dashboards
- Payment processing with Stripe
- Real university API integration
- University/program search with filters
- Sample data with universities and programs
- Logging and session management

## Technologies
- **Backend:** Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend:** Jinja2 templates, Bootstrap 5.3.0, Font Awesome 6.4.0
- **Database:** JSON files initially; PostgreSQL support possible via `psycopg2`
- **Payment:** Stripe API
- **Environment Management:** python-dotenv

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd ApplyClone