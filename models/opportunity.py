from datetime import datetime, date
from . import db

# Many-to-Many association tables
student_skills = db.Table(
    'student_skills',
    db.Column('student_profile_id', db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
)

student_interests = db.Table(
    'student_interests',
    db.Column('student_profile_id', db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('interest_id', db.Integer, db.ForeignKey('interests.id', ondelete='CASCADE'), primary_key=True)
)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default='fas fa-briefcase')
    badge_color = db.Column(db.String(30), default='primary')  # primary, success, info, warning, danger, purple

    def __repr__(self):
        return f'<Category {self.name}>'


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Organization {self.name}>'


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)  # Programming, Web, AI/Data, Cloud, Soft Skills

    def __repr__(self):
        return f'<Skill {self.name}>'


class Interest(db.Model):
    __tablename__ = 'interests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f'<Interest {self.name}>'


class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    organization = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # Internship, Hackathon, Scholarship, etc.
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.String(255), nullable=True)  # Comma-separated required skills
    eligibility = db.Column(db.Text, nullable=True)    # Eligibility criteria (e.g., "Open to all 2nd-4th year CS/IT students")
    
    # Location & Mode
    location = db.Column(db.String(100), default='Remote', index=True)
    mode = db.Column(db.String(20), default='Online', index=True)  # Online, Offline, Hybrid
    
    # Timeline
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True, index=True)
    
    # Financials
    stipend = db.Column(db.String(80), nullable=True)  # "₹30,000 / month", "Unpaid", etc.
    prize = db.Column(db.String(80), nullable=True)    # "₹10,00,000 Total Prize Pool"
    is_paid = db.Column(db.Boolean, default=False)
    beginner_friendly = db.Column(db.Boolean, default=False)
    
    # Links & Contact
    registration_link = db.Column(db.String(500), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    
    # Metadata & Status
    featured = db.Column(db.Boolean, default=False, index=True)
    verified = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='Active', index=True)  # Active, Pending, Closed, Rejected
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookmarks = db.relationship('Bookmark', backref='opportunity', lazy='dynamic', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='opportunity', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='opportunity', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def days_remaining(self):
        """Returns days remaining until deadline. Negative if expired."""
        if not self.deadline:
            return None
        today = date.today()
        delta = (self.deadline - today).days
        return delta

    def deadline_status(self):
        """Returns urgency level: 'expired', 'urgent', 'upcoming', 'none'."""
        days = self.days_remaining()
        if days is None:
            return 'none'
        if days < 0:
            return 'expired'
        elif days <= 3:
            return 'urgent'
        elif days <= 14:
            return 'soon'
        return 'upcoming'

    def deadline_badge_text(self):
        days = self.days_remaining()
        if days is None:
            return "No Deadline"
        if days < 0:
            return "Expired"
        if days == 0:
            return "Deadline Today!"
        if days == 1:
            return "Deadline Tomorrow!"
        return f"{days} days left"

    def bookmark_count(self):
        return self.bookmarks.count()

    def application_count(self):
        return self.applications.count()

    def __repr__(self):
        return f'<Opportunity {self.id}: {self.title}>'
