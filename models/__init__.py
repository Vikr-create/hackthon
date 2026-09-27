from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, StudentProfile
from .opportunity import Category, Organization, Skill, Interest, Opportunity, student_skills, student_interests
from .interaction import Bookmark, Application, Notification, Report

__all__ = [
    'db',
    'User',
    'StudentProfile',
    'Category',
    'Organization',
    'Skill',
    'Interest',
    'Opportunity',
    'student_skills',
    'student_interests',
    'Bookmark',
    'Application',
    'Notification',
    'Report'
]
