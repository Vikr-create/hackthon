from datetime import datetime, date
from models import db, Notification

def send_notification(user_id, title, message, link=None, notif_type='general'):
    """Helper to dispatch in-app notifications to a user."""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            type=notif_type
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        return None


def get_category_icon(category_name):
    """Maps opportunity category names to FontAwesome icons."""
    icons = {
        'Internship': 'fas fa-briefcase',
        'Hackathon': 'fas fa-laptop-code',
        'Scholarship': 'fas fa-graduation-cap',
        'Course': 'fas fa-book-open',
        'Certification': 'fas fa-certificate',
        'Competition': 'fas fa-trophy',
        'Workshop': 'fas fa-chalkboard-teacher',
        'Job': 'fas fa-user-tie',
        'Fellowship': 'fas fa-award',
        'Webinar': 'fas fa-video',
        'Conference': 'fas fa-users',
        'Bootcamp': 'fas fa-fire',
        'Research': 'fas fa-microscope',
        'Volunteering': 'fas fa-hands-helping',
        'Apprenticeship': 'fas fa-tools'
    }
    return icons.get(category_name, 'fas fa-star')


def get_category_color(category_name):
    """Maps opportunity category names to CSS badge color classes."""
    colors = {
        'Internship': 'primary',
        'Hackathon': 'warning',
        'Scholarship': 'success',
        'Course': 'info',
        'Certification': 'secondary',
        'Competition': 'danger',
        'Workshop': 'dark',
        'Fellowship': 'purple',
        'Job': 'primary',
        'Webinar': 'info',
        'Conference': 'dark',
        'Bootcamp': 'danger',
        'Research': 'info',
        'Volunteering': 'success',
        'Apprenticeship': 'warning'
    }
    return colors.get(category_name, 'primary')
