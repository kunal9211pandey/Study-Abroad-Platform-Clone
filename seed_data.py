#!/usr/bin/env python3
"""
Script to populate the database with sample data
Run this after setting up the database
"""

from app import app, db
from models import User, Institution, Program, UserRole, PaymentStatus
from werkzeug.security import generate_password_hash
import json

def create_sample_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            email='admin@applyboard.com',
            first_name='Admin',
            last_name='User',
            country='CA',
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample student
        student = User(
            email='student@example.com',
            first_name='John',
            last_name='Doe',
            phone='+1-555-0123',
            country='IN',
            role=UserRole.STUDENT,
            education_level='bachelor',
            field_of_interest='Computer Science',
            preferred_destinations='["CA", "US", "GB"]',
            is_active=True,
            is_verified=True
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Create sample institutions
        institutions_data = [
            {
                'name': 'University of Toronto',
                'short_name': 'UofT',
                'country': 'Canada',
                'country_code': 'CA',
                'city': 'Toronto',
                'state_province': 'Ontario',
                'type': 'university',
                'founded_year': 1827,
                'student_population': 97000,
                'international_students': 24000,
                'website': 'https://www.utoronto.ca',
                'world_ranking': 18,
                'application_fee': 150.00,
                'description': 'The University of Toronto is a public research university in Toronto, Ontario, Canada, located on the grounds that surround Queen\'s Park.',
                'logo_url': 'https://via.placeholder.com/100x100/0066CC/FFFFFF?text=UofT'
            },
            {
                'name': 'University of British Columbia',
                'short_name': 'UBC',
                'country': 'Canada',
                'country_code': 'CA',
                'city': 'Vancouver',
                'state_province': 'British Columbia',
                'type': 'university',
                'founded_year': 1908,
                'student_population': 68000,
                'international_students': 18000,
                'website': 'https://www.ubc.ca',
                'world_ranking': 34,
                'application_fee': 118.00,
                'description': 'The University of British Columbia is a public research university with campuses in Vancouver and Kelowna, British Columbia.',
                'logo_url': 'https://via.placeholder.com/100x100/002145/FFFFFF?text=UBC'
            },
            {
                'name': 'Harvard University',
                'short_name': 'Harvard',
                'country': 'United States',
                'country_code': 'US',
                'city': 'Cambridge',
                'state_province': 'Massachusetts',
                'type': 'university',
                'founded_year': 1636,
                'student_population': 31000,
                'international_students': 5800,
                'website': 'https://www.harvard.edu',
                'world_ranking': 1,
                'application_fee': 85.00,
                'description': 'Harvard University is a private Ivy League research university in Cambridge, Massachusetts.',
                'logo_url': 'https://via.placeholder.com/100x100/A51C30/FFFFFF?text=Harvard'
            },
            {
                'name': 'University of Oxford',
                'short_name': 'Oxford',
                'country': 'United Kingdom',
                'country_code': 'GB',
                'city': 'Oxford',
                'state_province': 'England',
                'type': 'university',
                'founded_year': 1096,
                'student_population': 26000,
                'international_students': 12000,
                'website': 'https://www.ox.ac.uk',
                'world_ranking': 4,
                'application_fee': 75.00,
                'description': 'The University of Oxford is a collegiate research university in Oxford, England.',
                'logo_url': 'https://via.placeholder.com/100x100/002147/FFFFFF?text=Oxford'
            },
            {
                'name': 'University of Melbourne',
                'short_name': 'Melbourne',
                'country': 'Australia',
                'country_code': 'AU',
                'city': 'Melbourne',
                'state_province': 'Victoria',
                'type': 'university',
                'founded_year': 1853,
                'student_population': 52000,
                'international_students': 19000,
                'website': 'https://www.unimelb.edu.au',
                'world_ranking': 33,
                'application_fee': 100.00,
                'description': 'The University of Melbourne is a public research university located in Melbourne, Australia.',
                'logo_url': 'https://via.placeholder.com/100x100/003768/FFFFFF?text=Melbourne'
            }
        ]
        
        institutions = []
        for inst_data in institutions_data:
            institution = Institution(**inst_data)
            db.session.add(institution)
            institutions.append(institution)
        
        # Commit to get IDs
        db.session.commit()
        
        # Create sample programs
        programs_data = [
            # University of Toronto programs
            {
                'institution_id': institutions[0].id,
                'name': 'Bachelor of Science in Computer Science',
                'code': 'BSC-CS',
                'degree_type': 'Bachelor',
                'field_of_study': 'Computer Science',
                'duration_months': 48,
                'tuition_fee': 58160.00,
                'currency': 'CAD',
                'description': 'A comprehensive program covering algorithms, software engineering, and computer systems.',
                'min_gpa': 3.7,
                'scholarships_available': True,
                'work_permit_eligible': True
            },
            {
                'institution_id': institutions[0].id,
                'name': 'Master of Business Administration',
                'code': 'MBA',
                'degree_type': 'Master',
                'field_of_study': 'Business Administration',
                'duration_months': 20,
                'tuition_fee': 124080.00,
                'currency': 'CAD',
                'description': 'A world-class MBA program preparing leaders for global business.',
                'min_gpa': 3.5,
                'scholarships_available': True,
                'work_permit_eligible': True
            },
            # UBC programs
            {
                'institution_id': institutions[1].id,
                'name': 'Bachelor of Engineering',
                'code': 'BENG',
                'degree_type': 'Bachelor',
                'field_of_study': 'Engineering',
                'duration_months': 48,
                'tuition_fee': 55000.00,
                'currency': 'CAD',
                'description': 'Comprehensive engineering program with multiple specializations.',
                'min_gpa': 3.5,
                'scholarships_available': True,
                'work_permit_eligible': True
            },
            # Harvard programs
            {
                'institution_id': institutions[2].id,
                'name': 'Bachelor of Arts in Economics',
                'code': 'BA-ECON',
                'degree_type': 'Bachelor',
                'field_of_study': 'Economics',
                'duration_months': 48,
                'tuition_fee': 54880.00,
                'currency': 'USD',
                'description': 'Rigorous economics program at one of the world\'s top universities.',
                'min_gpa': 3.9,
                'scholarships_available': True,
                'work_permit_eligible': False
            },
            # Oxford programs
            {
                'institution_id': institutions[3].id,
                'name': 'Bachelor of Arts in Philosophy, Politics and Economics',
                'code': 'BA-PPE',
                'degree_type': 'Bachelor',
                'field_of_study': 'Liberal Arts',
                'duration_months': 36,
                'tuition_fee': 39000.00,
                'currency': 'GBP',
                'description': 'Oxford\'s famous PPE degree combining three disciplines.',
                'min_gpa': 3.8,
                'scholarships_available': True,
                'work_permit_eligible': False
            },
            # Melbourne programs
            {
                'institution_id': institutions[4].id,
                'name': 'Bachelor of Science in Data Science',
                'code': 'BSC-DS',
                'degree_type': 'Bachelor',
                'field_of_study': 'Data Science',
                'duration_months': 36,
                'tuition_fee': 45000.00,
                'currency': 'AUD',
                'description': 'Cutting-edge data science program with industry partnerships.',
                'min_gpa': 3.6,
                'scholarships_available': True,
                'work_permit_eligible': True
            }
        ]
        
        for prog_data in programs_data:
            program = Program(**prog_data)
            db.session.add(program)
        
        db.session.commit()
        
        print("Sample data created successfully!")
        print("Admin login: admin@applyboard.com / admin123")
        print("Student login: student@example.com / student123")

if __name__ == '__main__':
    create_sample_data()