from flask import Blueprint, jsonify, request
from models import Institution, Program, db
import requests
import json

api = Blueprint('api', __name__)

# Mock external university API integration
# In production, you would integrate with real APIs like:
# - Universities API
# - Government education databases
# - Institution ranking services

@api.route('/universities/search')
def search_universities():
    """Search universities with external API integration"""
    country = request.args.get('country', '')
    field = request.args.get('field', '')
    search_term = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Institution.query.filter_by(is_active=True)
    
    if country:
        query = query.filter_by(country_code=country)
    
    if search_term:
        query = query.filter(
            db.or_(
                Institution.name.contains(search_term),
                Institution.city.contains(search_term),
                Institution.description.contains(search_term)
            )
        )
    
    universities = query.offset((page - 1) * 20).limit(20).all()
    total = query.count()
    
    # Format response
    result = {
        'universities': [{
            'id': uni.id,
            'name': uni.name,
            'location': f"{uni.city}, {uni.country}",
            'country_code': uni.country_code,
            'description': uni.description,
            'logo_url': uni.logo_url,
            'website': uni.website,
            'type': uni.type,
            'world_ranking': uni.world_ranking,
            'application_fee': float(uni.application_fee) if uni.application_fee else 0,
            'program_count': uni.programs.filter_by(is_active=True).count()
        } for uni in universities],
        'total': total,
        'page': page,
        'has_next': total > page * 20
    }
    
    return jsonify(result)

@api.route('/programs/search')
def search_programs():
    """Search programs with filtering"""
    university_id = request.args.get('university_id', type=int)
    field = request.args.get('field', '')
    degree_type = request.args.get('degree_type', '')
    min_fee = request.args.get('min_fee', type=float)
    max_fee = request.args.get('max_fee', type=float)
    page = request.args.get('page', 1, type=int)
    
    query = Program.query.filter_by(is_active=True).join(Institution)
    
    if university_id:
        query = query.filter_by(institution_id=university_id)
    
    if field:
        query = query.filter(Program.field_of_study.contains(field))
    
    if degree_type:
        query = query.filter_by(degree_type=degree_type)
    
    if min_fee is not None:
        query = query.filter(Program.tuition_fee >= min_fee)
    
    if max_fee is not None:
        query = query.filter(Program.tuition_fee <= max_fee)
    
    programs = query.offset((page - 1) * 20).limit(20).all()
    total = query.count()
    
    result = {
        'programs': [{
            'id': prog.id,
            'name': prog.name,
            'institution': prog.institution.name,
            'degree_type': prog.degree_type,
            'field_of_study': prog.field_of_study,
            'duration_months': prog.duration_months,
            'tuition_fee': float(prog.tuition_fee),
            'currency': prog.currency,
            'language': prog.language_of_instruction,
            'scholarships_available': prog.scholarships_available,
            'work_permit_eligible': prog.work_permit_eligible,
            'online_available': prog.online_available
        } for prog in programs],
        'total': total,
        'page': page,
        'has_next': total > page * 20
    }
    
    return jsonify(result)

@api.route('/universities/<int:uni_id>/programs')
def university_programs(uni_id):
    """Get programs for a specific university"""
    university = Institution.query.get_or_404(uni_id)
    programs = Program.query.filter_by(institution_id=uni_id, is_active=True).all()
    
    result = {
        'university': {
            'id': university.id,
            'name': university.name,
            'country': university.country,
            'website': university.website
        },
        'programs': [{
            'id': prog.id,
            'name': prog.name,
            'degree_type': prog.degree_type,
            'field_of_study': prog.field_of_study,
            'tuition_fee': float(prog.tuition_fee),
            'currency': prog.currency,
            'duration_months': prog.duration_months
        } for prog in programs]
    }
    
    return jsonify(result)

# External API integration functions
def fetch_university_rankings():
    """
    Integrate with external ranking APIs
    Example: QS World University Rankings, Times Higher Education
    """
    # This would be a real API call in production
    # response = requests.get('https://api.universityrankings.com/rankings')
    # return response.json()
    
    # Mock data for demonstration
    return {
        'rankings': [
            {'university_name': 'Harvard University', 'world_rank': 1},
            {'university_name': 'MIT', 'world_rank': 2},
            {'university_name': 'Stanford University', 'world_rank': 3}
        ]
    }

def fetch_government_accreditation(country_code):
    """
    Integrate with government education databases
    Example: US Department of Education, UK HESA
    """
    # Mock implementation
    accredited_institutions = {
        'us': ['Harvard University', 'MIT', 'Stanford University'],
        'gb': ['Oxford University', 'Cambridge University', 'Imperial College'],
        'ca': ['University of Toronto', 'McGill University', 'UBC']
    }
    
    return accredited_institutions.get(country_code, [])

@api.route('/external/update-rankings')
def update_rankings():
    """Update university rankings from external sources"""
    try:
        rankings_data = fetch_university_rankings()
        
        for ranking in rankings_data.get('rankings', []):
            university = Institution.query.filter_by(
                name=ranking['university_name']
            ).first()
            
            if university:
                university.world_ranking = ranking['world_rank']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Rankings updated successfully',
            'updated_count': len(rankings_data.get('rankings', []))
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api.route('/external/verify-accreditation/<country_code>')
def verify_accreditation(country_code):
    """Verify institutional accreditation from government sources"""
    try:
        accredited_names = fetch_government_accreditation(country_code)
        
        # Update institutions in database
        institutions = Institution.query.filter_by(country_code=country_code).all()
        verified_count = 0
        
        for institution in institutions:
            if institution.name in accredited_names:
                institution.is_verified = True
                verified_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Accreditation verified for {country_code}',
            'verified_count': verified_count,
            'total_institutions': len(institutions)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Real-time application status updates
@api.route('/applications/<int:app_id>/status')
def get_application_status(app_id):
    """Get real-time application status"""
    from models import Application
    
    application = Application.query.get_or_404(app_id)
    
    return jsonify({
        'id': application.id,
        'reference_number': application.reference_number,
        'status': application.status.value,
        'submitted_at': application.submitted_at.isoformat() if application.submitted_at else None,
        'decision_date': application.decision_date.isoformat() if application.decision_date else None,
        'institution': application.institution.name,
        'program': application.program.name
    })

# Notification system
@api.route('/notifications/send', methods=['POST'])
def send_notification():
    """Send notifications to users (email, SMS, push)"""
    data = request.get_json()
    
    # In production, integrate with:
    # - SendGrid/Mailgun for emails
    # - Twilio for SMS
    # - Firebase for push notifications
    
    notification_type = data.get('type')  # email, sms, push
    recipient = data.get('recipient')
    message = data.get('message')
    
    # Mock implementation
    return jsonify({
        'status': 'success',
        'message': f'{notification_type} notification sent to {recipient}',
        'notification_id': 'mock_notification_123'
    })