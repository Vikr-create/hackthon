from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, current_app
from flask_login import current_user
from models import db, Category, Opportunity, User, Application

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch categories
    categories = Category.query.all()
    
    # Platform stats
    total_opportunities = Opportunity.query.filter_by(status='Active').count()
    total_students = User.query.filter_by(role='student').count()
    total_applications = Application.query.count()
    
    # Featured opportunities
    featured_opps = Opportunity.query.filter_by(status='Active', featured=True).limit(6).all()
    if not featured_opps:
        featured_opps = Opportunity.query.filter_by(status='Active').limit(6).all()
        
    # Upcoming urgent deadlines (within 14 days)
    today = date.today()
    two_weeks = today + timedelta(days=14)
    upcoming_deadlines = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline >= today,
        Opportunity.deadline <= two_weeks
    ).order_by(Opportunity.deadline.asc()).limit(4).all()

    return render_template(
        'index.html',
        categories=categories,
        total_opportunities=total_opportunities,
        total_students=total_students,
        total_applications=total_applications,
        featured_opportunities=featured_opps,
        upcoming_deadlines=upcoming_deadlines
    )


@main_bp.app_context_processor
def inject_global_vars():
    """Inject variables accessible in all templates."""
    all_categories = Category.query.all() if Category.query else []
    unread_notifs = 0
    if current_user.is_authenticated:
        unread_notifs = current_user.unread_notifications_count()
        
    return {
        'BRAND_NAME': 'OpportunityHub',
        'APP_NAME': 'Student Opportunity Discovery Platform',
        'nav_categories': all_categories,
        'unread_notifications_count': unread_notifs,
        'current_year': datetime.utcnow().year
    }


@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500
