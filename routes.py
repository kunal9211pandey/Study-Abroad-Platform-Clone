import json
import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import app
from models import User, Institution, Program, Application, Payment, db, ApplicationStatus

def load_json_data(filename):
    """Helper function to load JSON data from the data directory"""
    file_path = os.path.join('data', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

@app.route('/')
def index():
    """Homepage with hero section and featured universities"""
    # Get featured institutions from database
    institutions = Institution.query.filter_by(is_active=True).all()
    
    # Group universities by country for display
    featured_universities = {}
    countries = ['ca', 'us', 'gb', 'au', 'ie', 'de']
    
    for country in countries:
        country_unis = [uni for uni in institutions if uni.country_code.lower() == country]
        if country_unis:
            featured_universities[country] = country_unis[:3]  # Get top 3 per country
    
    # Load testimonials from JSON for now
    testimonials = load_json_data('testimonials.json')
    featured_testimonials = testimonials[:6] if testimonials else []
    
    return render_template('index.html', 
                         featured_universities=featured_universities,
                         testimonials=featured_testimonials)

@app.route('/search')
def search():
    """University and program search page"""
    # Get search parameters
    country = request.args.get('country', '')
    field = request.args.get('field', '')
    search_query = request.args.get('q', '')
    
    # Build query for institutions
    query = Institution.query.filter_by(is_active=True)
    
    if country:
        query = query.filter_by(country_code=country)
    
    if search_query:
        query = query.filter(
            db.or_(
                Institution.name.contains(search_query),
                Institution.city.contains(search_query),
                Institution.description.contains(search_query)
            )
        )
    
    institutions = query.all()
    
    # Get programs if field is specified
    programs = []
    if field:
        programs = Program.query.filter(
            Program.field_of_study.contains(field),
            Program.is_active == True
        ).all()
    
    # Get unique countries for filter dropdown
    countries = db.session.query(
        Institution.country_code, 
        Institution.country
    ).filter_by(is_active=True).distinct().all()
    
    # Get unique fields for filter dropdown
    fields = db.session.query(Program.field_of_study).filter_by(is_active=True).distinct().all()
    
    return render_template('search.html',
                         universities=institutions,
                         programs=programs,
                         countries=countries,
                         fields=[f[0] for f in fields],
                         selected_country=country,
                         selected_field=field,
                         search_query=search_query)

@app.route('/institution/<int:institution_id>')
def institution_detail(institution_id):
    """Institution detail page"""
    institution = Institution.query.get_or_404(institution_id)
    programs = Program.query.filter_by(
        institution_id=institution_id, 
        is_active=True
    ).all()
    
    return render_template('institution_detail.html', 
                         institution=institution, 
                         programs=programs)

@app.route('/program/<int:program_id>')
def program_detail(program_id):
    """Program detail page"""
    program = Program.query.get_or_404(program_id)
    return render_template('program_detail.html', program=program)

@app.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard"""
    applications = Application.query.filter_by(user_id=current_user.id).all()
    payments = Payment.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                         applications=applications,
                         payments=payments)

@app.route('/apply/<int:program_id>', methods=['GET', 'POST'])
@login_required
def apply_to_program(program_id):
    """Apply to a program"""
    program = Program.query.get_or_404(program_id)
    
    # Check if user already has an application for this program
    existing_app = Application.query.filter_by(
        user_id=current_user.id,
        program_id=program_id
    ).first()
    
    if existing_app:
        flash('You have already applied to this program.', 'info')
        return redirect(url_for('view_application', application_id=existing_app.id))
    
    if request.method == 'POST':
        # Create new application
        application = Application(
            user_id=current_user.id,
            institution_id=program.institution_id,
            program_id=program_id,
            status=ApplicationStatus.DRAFT,
            personal_statement=request.form.get('personal_statement', ''),
            statement_of_purpose=request.form.get('statement_of_purpose', '')
        )
        
        # Generate reference number
        application.reference_number = application.generate_reference_number()
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application created successfully!', 'success')
        return redirect(url_for('view_application', application_id=application.id))
    
    return render_template('application_form.html', program=program)

@app.route('/application/<int:application_id>')
@login_required
def view_application(application_id):
    """View application details"""
    application = Application.query.get_or_404(application_id)
    
    # Verify user owns this application
    if application.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('application_detail.html', application=application)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            flash('Please fill in all fields.', 'error')
            return render_template('contact.html')
        
        # For now, just show success message
        # In production, send email or save to database
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# API endpoints for dynamic content
@app.route('/api/universities')
def api_universities():
    """API endpoint to get universities data"""
    country = request.args.get('country', '')
    search = request.args.get('search', '')
    
    query = Institution.query.filter_by(is_active=True)
    
    if country:
        query = query.filter_by(country_code=country)
    
    if search:
        query = query.filter(Institution.name.contains(search))
    
    institutions = query.all()
    
    return jsonify([{
        'id': inst.id,
        'name': inst.name,
        'country': inst.country,
        'city': inst.city,
        'logo_url': inst.logo_url
    } for inst in institutions])

@app.route('/api/programs')
def api_programs():
    """API endpoint to get programs data"""
    university_id = request.args.get('university_id', type=int)
    field = request.args.get('field', '')
    
    query = Program.query.filter_by(is_active=True)
    
    if university_id:
        query = query.filter_by(institution_id=university_id)
    
    if field:
        query = query.filter(Program.field_of_study.contains(field))
    
    programs = query.all()
    
    return jsonify([{
        'id': prog.id,
        'name': prog.name,
        'degree_type': prog.degree_type,
        'field_of_study': prog.field_of_study,
        'tuition_fee': float(prog.tuition_fee),
        'currency': prog.currency
    } for prog in programs])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500