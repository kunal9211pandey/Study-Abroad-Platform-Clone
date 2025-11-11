from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json

auth = Blueprint('auth', __name__)

def init_auth(login_manager, User, db):
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Store references for use in routes
    auth.User = User
    auth.db = db

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')
        
        user = auth.User.query.filter_by(email=email.lower()).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            auth.db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user role
            if user.role.name == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        country = request.form.get('country', '')
        education_level = request.form.get('education_level', '')
        field_of_interest = request.form.get('field_of_interest', '')
        
        # Get selected destinations
        destinations = request.form.getlist('destinations')
        
        # Validation
        if not all([first_name, last_name, email, password, country]):
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if auth.User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = auth.User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                country=country,
                education_level=education_level,
                field_of_interest=field_of_interest,
                preferred_destinations=json.dumps(destinations) if destinations else None
            )
            user.set_password(password)
            
            auth.db.session.add(user)
            auth.db.session.commit()
            
            # Auto-login after registration
            login_user(user)
            
            flash('Registration successful! Welcome to ApplyBoard.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            auth.db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update profile information
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.country = request.form.get('country', '')
        current_user.education_level = request.form.get('education_level', '')
        current_user.field_of_interest = request.form.get('field_of_interest', '')
        
        # Update destinations
        destinations = request.form.getlist('destinations')
        current_user.preferred_destinations = json.dumps(destinations) if destinations else None
        
        try:
            auth.db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            auth.db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            print(f"Profile update error: {e}")
    
    # Parse preferred destinations for form
    preferred_destinations = []
    if current_user.preferred_destinations:
        try:
            preferred_destinations = json.loads(current_user.preferred_destinations)
        except:
            preferred_destinations = []
    
    return render_template('auth/edit_profile.html', 
                         user=current_user, 
                         preferred_destinations=preferred_destinations)