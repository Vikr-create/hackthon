from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    reports = db.relationship('Report', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Basic Info
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    
    # Education
    college = db.Column(db.String(150), nullable=True)
    university = db.Column(db.String(150), nullable=True)
    degree = db.Column(db.String(80), nullable=True)     # B.Tech, B.E., B.Sc, M.Tech, BCA, MCA
    branch = db.Column(db.String(80), nullable=True)     # Computer Science, Information Technology, AI/ML, ECE, Mechanical
    year = db.Column(db.String(20), nullable=True)       # 1st Year, 2nd Year, 3rd Year, 4th Year, Graduate
    semester = db.Column(db.Integer, nullable=True)      # 1 to 8
    cgpa = db.Column(db.Float, nullable=True)            # 0.00 - 10.00
    graduation_year = db.Column(db.Integer, nullable=True)

    # Preferences & Location
    location = db.Column(db.String(100), nullable=True)
    work_preference = db.Column(db.String(50), default='Any') # Remote, On-site, Hybrid, Any
    preferred_categories = db.Column(db.String(255), nullable=True) # Comma-separated categories
    preferred_locations = db.Column(db.String(255), nullable=True)  # Comma-separated locations
    
    # Professional & Links
    experience = db.Column(db.Text, nullable=True)
    resume_link = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    github = db.Column(db.String(255), nullable=True)
    portfolio = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = db.relationship('Skill', secondary='student_skills', backref=db.backref('students', lazy='dynamic'))
    interests = db.relationship('Interest', secondary='student_interests', backref=db.backref('students', lazy='dynamic'))

    def calculate_completion_percentage(self):
        """Calculates profile completion percentage based on key fields."""
        fields_to_check = [
            bool(self.full_name),
            bool(self.phone),
            bool(self.college),
            bool(self.degree),
            bool(self.branch),
            bool(self.year),
            bool(self.cgpa),
            bool(self.graduation_year),
            bool(self.location),
            bool(self.bio),
            bool(self.skills and len(self.skills) > 0),
            bool(self.interests and len(self.interests) > 0),
            bool(self.preferred_categories),
            bool(self.work_preference),
            bool(self.resume_link or self.github or self.linkedin or self.portfolio)
        ]
        completed = sum(1 for item in fields_to_check if item)
        return int((completed / len(fields_to_check)) * 100)

    def get_preferred_categories_list(self):
        if not self.preferred_categories:
            return []
        return [c.strip() for c in self.preferred_categories.split(',') if c.strip()]

    def get_skills_names(self):
        return [s.name for s in self.skills]

    def get_interests_names(self):
        return [i.name for i in self.interests]

    def __repr__(self):
        return f'<StudentProfile {self.full_name or "Anonymous"}>'
