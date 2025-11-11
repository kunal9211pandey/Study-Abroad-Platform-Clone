from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import enum

class UserRole(enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"
    INSTITUTION = "institution"

class ApplicationStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(2))  # ISO country code
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    # Student-specific fields
    education_level = db.Column(db.String(50))
    field_of_interest = db.Column(db.String(100))
    preferred_destinations = db.Column(db.Text)  # JSON string of country codes
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    applications = db.relationship('Application', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

class Institution(db.Model):
    __tablename__ = 'institutions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    # Location
    country = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(2), nullable=False, index=True)
    state_province = db.Column(db.String(100))
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    postal_code = db.Column(db.String(20))
    
    # Contact
    website = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Institution details
    type = db.Column(db.String(50))  # university, college, institute
    founded_year = db.Column(db.Integer)
    student_population = db.Column(db.Integer)
    international_students = db.Column(db.Integer)
    
    # Media
    logo_url = db.Column(db.String(500))
    banner_url = db.Column(db.String(500))
    images = db.Column(db.Text)  # JSON string of image URLs
    
    # Rankings and accreditation
    world_ranking = db.Column(db.Integer)
    national_ranking = db.Column(db.Integer)
    accreditations = db.Column(db.Text)  # JSON string
    
    # Application settings
    application_fee = db.Column(db.Numeric(10, 2), default=0.00)
    application_deadline = db.Column(db.Date)
    accepts_international = db.Column(db.Boolean, default=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    programs = db.relationship('Program', backref='institution', lazy='dynamic', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='institution', lazy='dynamic')
    
    def __repr__(self):
        return f'<Institution {self.name}>'

class Program(db.Model):
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20))
    description = db.Column(db.Text)
    
    # Program details
    degree_type = db.Column(db.String(50), nullable=False)  # Bachelor, Master, PhD, etc.
    field_of_study = db.Column(db.String(100), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    language_of_instruction = db.Column(db.String(50), default='English')
    
    # Costs
    tuition_fee = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    additional_fees = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Requirements
    min_gpa = db.Column(db.Numeric(3, 2))
    english_requirements = db.Column(db.Text)  # JSON string
    other_requirements = db.Column(db.Text)
    
    # Intake
    intake_months = db.Column(db.String(50))  # e.g., "1,5,9" for Jan, May, Sep
    application_deadline = db.Column(db.Date)
    
    # Program features
    scholarships_available = db.Column(db.Boolean, default=False)
    work_permit_eligible = db.Column(db.Boolean, default=False)
    online_available = db.Column(db.Boolean, default=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    seats_available = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='program', lazy='dynamic')
    
    @property
    def formatted_tuition(self):
        return f"{self.currency} {self.tuition_fee:,.2f}"
    
    def __repr__(self):
        return f'<Program {self.name} at {self.institution.name}>'

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    
    # Application details
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.DRAFT, nullable=False)
    reference_number = db.Column(db.String(20), unique=True)
    
    # Personal information
    personal_info = db.Column(db.Text)  # JSON string
    academic_history = db.Column(db.Text)  # JSON string
    documents = db.Column(db.Text)  # JSON string of document URLs
    
    # Application essays/statements
    personal_statement = db.Column(db.Text)
    statement_of_purpose = db.Column(db.Text)
    
    # Application dates
    submitted_at = db.Column(db.DateTime)
    decision_date = db.Column(db.DateTime)
    response_deadline = db.Column(db.DateTime)
    
    # Decision
    decision_notes = db.Column(db.Text)
    offer_conditions = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='application', lazy='dynamic')
    
    def generate_reference_number(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    def __repr__(self):
        return f'<Application {self.reference_number}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    
    # Payment details
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Stripe metadata
    stripe_metadata = db.Column(db.Text)  # JSON string
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} {self.currency}>'

# Admin activity logging
class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))  # user, institution, program, etc.
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('User', backref='admin_logs')
    
    def __repr__(self):
        return f'<AdminLog {self.action} by {self.admin_id}>'