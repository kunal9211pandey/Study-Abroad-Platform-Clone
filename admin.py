from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import User, Institution, Program, Application, Payment, AdminLog, db, UserRole, ApplicationStatus, PaymentStatus
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_
import json

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action, target_type=None, target_id=None, details=None):
    """Log admin actions for audit trail"""
    try:
        log = AdminLog(
            admin_id=current_user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=json.dumps(details) if details else None,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")

@admin.route('/dashboard')
@admin_required
def dashboard():
    # Get dashboard statistics
    stats = {
        'total_users': User.query.filter_by(role=UserRole.STUDENT).count(),
        'total_institutions': Institution.query.filter_by(is_active=True).count(),
        'total_programs': Program.query.filter_by(is_active=True).count(),
        'total_applications': Application.query.count(),
        'pending_applications': Application.query.filter_by(status=ApplicationStatus.SUBMITTED).count(),
        'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(status=PaymentStatus.COMPLETED).scalar() or 0
    }
    
    # Recent activity
    recent_applications = Application.query.order_by(desc(Application.created_at)).limit(10).all()
    recent_users = User.query.filter_by(role=UserRole.STUDENT).order_by(desc(User.created_at)).limit(10).all()
    recent_payments = Payment.query.order_by(desc(Payment.created_at)).limit(10).all()
    
    # Monthly application trends (last 12 months)
    monthly_stats = []
    for i in range(12):
        start_date = datetime.now().replace(day=1) - timedelta(days=30*i)
        end_date = start_date.replace(day=28) + timedelta(days=4)  # end of month
        count = Application.query.filter(
            Application.created_at >= start_date,
            Application.created_at < end_date
        ).count()
        monthly_stats.append({
            'month': start_date.strftime('%b %Y'),
            'applications': count
        })
    
    monthly_stats.reverse()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_applications=recent_applications,
                         recent_users=recent_users,
                         recent_payments=recent_payments,
                         monthly_stats=monthly_stats)

# User Management
@admin.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(or_(
            User.email.contains(search),
            User.first_name.contains(search),
            User.last_name.contains(search)
        ))
    
    if role_filter:
        query = query.filter_by(role=UserRole(role_filter))
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, role_filter=role_filter)

@admin.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    applications = Application.query.filter_by(user_id=user_id).order_by(desc(Application.created_at)).all()
    payments = Payment.query.filter_by(user_id=user_id).order_by(desc(Payment.created_at)).all()
    
    return render_template('admin/user_detail.html', user=user, applications=applications, payments=payments)

@admin.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activated" if user.is_active else "deactivated"
    log_admin_action(f'user_{status}', 'user', user_id, {'email': user.email})
    
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))

# Institution Management
@admin.route('/institutions')
@admin_required
def institutions():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    country_filter = request.args.get('country', '')
    
    query = Institution.query
    
    if search:
        query = query.filter(or_(
            Institution.name.contains(search),
            Institution.city.contains(search),
            Institution.country.contains(search)
        ))
    
    if country_filter:
        query = query.filter_by(country_code=country_filter)
    
    institutions = query.order_by(Institution.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique countries for filter
    countries = db.session.query(Institution.country_code, Institution.country).distinct().all()
    
    return render_template('admin/institutions.html', 
                         institutions=institutions, 
                         search=search, 
                         country_filter=country_filter,
                         countries=countries)

@admin.route('/institutions/add', methods=['GET', 'POST'])
@admin_required
def add_institution():
    if request.method == 'POST':
        try:
            institution = Institution(
                name=request.form.get('name'),
                short_name=request.form.get('short_name'),
                description=request.form.get('description'),
                country=request.form.get('country'),
                country_code=request.form.get('country_code'),
                state_province=request.form.get('state_province'),
                city=request.form.get('city'),
                address=request.form.get('address'),
                postal_code=request.form.get('postal_code'),
                website=request.form.get('website'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                type=request.form.get('type'),
                founded_year=int(request.form.get('founded_year')) if request.form.get('founded_year') else None,
                student_population=int(request.form.get('student_population')) if request.form.get('student_population') else None,
                logo_url=request.form.get('logo_url'),
                application_fee=float(request.form.get('application_fee', 0)),
                accepts_international=bool(request.form.get('accepts_international'))
            )
            
            db.session.add(institution)
            db.session.commit()
            
            log_admin_action('institution_created', 'institution', institution.id, {'name': institution.name})
            
            flash('Institution added successfully!', 'success')
            return redirect(url_for('admin.institutions'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding institution. Please try again.', 'error')
            print(f"Error adding institution: {e}")
    
    return render_template('admin/add_institution.html')

@admin.route('/institutions/<int:institution_id>')
@admin_required
def institution_detail(institution_id):
    institution = Institution.query.get_or_404(institution_id)
    programs = Program.query.filter_by(institution_id=institution_id).all()
    applications = Application.query.filter_by(institution_id=institution_id).count()
    
    return render_template('admin/institution_detail.html', 
                         institution=institution, 
                         programs=programs, 
                         applications=applications)

@admin.route('/institutions/<int:institution_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_institution(institution_id):
    institution = Institution.query.get_or_404(institution_id)
    
    if request.method == 'POST':
        try:
            institution.name = request.form.get('name')
            institution.short_name = request.form.get('short_name')
            institution.description = request.form.get('description')
            institution.country = request.form.get('country')
            institution.country_code = request.form.get('country_code')
            institution.state_province = request.form.get('state_province')
            institution.city = request.form.get('city')
            institution.address = request.form.get('address')
            institution.postal_code = request.form.get('postal_code')
            institution.website = request.form.get('website')
            institution.email = request.form.get('email')
            institution.phone = request.form.get('phone')
            institution.type = request.form.get('type')
            institution.founded_year = int(request.form.get('founded_year')) if request.form.get('founded_year') else None
            institution.student_population = int(request.form.get('student_population')) if request.form.get('student_population') else None
            institution.logo_url = request.form.get('logo_url')
            institution.application_fee = float(request.form.get('application_fee', 0))
            institution.accepts_international = bool(request.form.get('accepts_international'))
            
            db.session.commit()
            
            log_admin_action('institution_updated', 'institution', institution_id, {'name': institution.name})
            
            flash('Institution updated successfully!', 'success')
            return redirect(url_for('admin.institution_detail', institution_id=institution_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating institution. Please try again.', 'error')
            print(f"Error updating institution: {e}")
    
    return render_template('admin/edit_institution.html', institution=institution)

# Program Management
@admin.route('/programs')
@admin_required
def programs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    institution_filter = request.args.get('institution', '', type=int)
    field_filter = request.args.get('field', '')
    
    query = Program.query.join(Institution)
    
    if search:
        query = query.filter(or_(
            Program.name.contains(search),
            Institution.name.contains(search)
        ))
    
    if institution_filter:
        query = query.filter_by(institution_id=institution_filter)
    
    if field_filter:
        query = query.filter(Program.field_of_study.contains(field_filter))
    
    programs = query.order_by(Institution.name, Program.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get institutions for filter
    institutions = Institution.query.filter_by(is_active=True).order_by(Institution.name).all()
    
    return render_template('admin/programs.html', 
                         programs=programs, 
                         search=search,
                         institution_filter=institution_filter,
                         field_filter=field_filter,
                         institutions=institutions)

# Application Management
@admin.route('/applications')
@admin_required
def applications():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Application.query.join(User).join(Institution).join(Program)
    
    if status_filter:
        query = query.filter(Application.status == ApplicationStatus(status_filter))
    
    if search:
        query = query.filter(or_(
            User.email.contains(search),
            User.first_name.contains(search),
            User.last_name.contains(search),
            Application.reference_number.contains(search)
        ))
    
    applications = query.order_by(desc(Application.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/applications.html', 
                         applications=applications,
                         status_filter=status_filter,
                         search=search)

@admin.route('/applications/<int:application_id>')
@admin_required
def application_detail(application_id):
    application = Application.query.get_or_404(application_id)
    return render_template('admin/application_detail.html', application=application)

@admin.route('/applications/<int:application_id>/update-status', methods=['POST'])
@admin_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    new_status = request.form.get('status')
    decision_notes = request.form.get('decision_notes')
    
    try:
        old_status = application.status.value
        application.status = ApplicationStatus(new_status)
        application.decision_notes = decision_notes
        
        if new_status in ['accepted', 'rejected']:
            application.decision_date = datetime.utcnow()
        
        db.session.commit()
        
        log_admin_action('application_status_updated', 'application', application_id, {
            'old_status': old_status,
            'new_status': new_status,
            'reference_number': application.reference_number
        })
        
        flash(f'Application status updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating application status.', 'error')
        print(f"Error updating application: {e}")
    
    return redirect(url_for('admin.application_detail', application_id=application_id))

# Payment Management
@admin.route('/payments')
@admin_required
def payments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query.join(User)
    
    if status_filter:
        query = query.filter(Payment.status == PaymentStatus(status_filter))
    
    payments = query.order_by(desc(Payment.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/payments.html', payments=payments, status_filter=status_filter)

# Analytics and Reports
@admin.route('/analytics')
@admin_required
def analytics():
    # Application statistics by status
    app_stats = db.session.query(
        Application.status, 
        func.count(Application.id).label('count')
    ).group_by(Application.status).all()
    
    # Revenue statistics by month
    revenue_stats = db.session.query(
        func.extract('month', Payment.completed_at).label('month'),
        func.sum(Payment.amount).label('revenue')
    ).filter_by(status=PaymentStatus.COMPLETED).group_by('month').all()
    
    # Top institutions by application count
    top_institutions = db.session.query(
        Institution.name,
        func.count(Application.id).label('count')
    ).join(Application).group_by(Institution.name).order_by(desc('count')).limit(10).all()
    
    return render_template('admin/analytics.html',
                         app_stats=app_stats,
                         revenue_stats=revenue_stats,
                         top_institutions=top_institutions)

# Settings
@admin.route('/settings')
@admin_required
def settings():
    return render_template('admin/settings.html')

# Admin logs
@admin.route('/logs')
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs = AdminLog.query.join(User).order_by(desc(AdminLog.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('admin/logs.html', logs=logs)