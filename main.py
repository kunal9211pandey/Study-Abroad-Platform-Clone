from app import app, db, login_manager
from models import *
from auth import auth as auth_blueprint, init_auth
from admin import admin as admin_blueprint
from api import api as api_blueprint  
from payments import payments as payments_blueprint
import routes

# Initialize authentication
init_auth(login_manager, User, db)

# Register blueprints
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(api_blueprint, url_prefix='/api')
app.register_blueprint(payments_blueprint, url_prefix='/payments')

# Create tables
with app.app_context():
    db.create_all()
    print("Database tables created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
