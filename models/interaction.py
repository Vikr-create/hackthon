from datetime import datetime, date
from . import db

class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'opportunity_id', name='uq_user_opportunity_bookmark'),
    )

    def __repr__(self):
        return f'<Bookmark user_id={self.user_id} opp_id={self.opportunity_id}>'


class Application(db.Model):
    __tablename__ = 'applications'

    # Status choices: Interested, Saved, Applied, Shortlisted, Selected, Rejected, Completed
    STATUS_CHOICES = ['Interested', 'Saved', 'Applied', 'Shortlisted', 'Selected', 'Rejected', 'Completed']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(30), default='Interested', nullable=False)
    notes = db.Column(db.Text, nullable=True)
    applied_date = db.Column(db.Date, default=date.today)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'opportunity_id', name='uq_user_opportunity_application'),
    )

    def status_badge_class(self):
        status_map = {
            'Interested': 'bg-secondary',
            'Saved': 'bg-info text-dark',
            'Applied': 'bg-primary',
            'Shortlisted': 'bg-warning text-dark',
            'Selected': 'bg-success',
            'Rejected': 'bg-danger',
            'Completed': 'bg-dark'
        }
        return status_map.get(self.status, 'bg-secondary')

    def __repr__(self):
        return f'<Application user_id={self.user_id} opp_id={self.opportunity_id} status={self.status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(40), default='general')  # match, deadline, status, profile, announcement
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def type_icon(self):
        icon_map = {
            'match': 'fas fa-bullseye text-primary',
            'deadline': 'fas fa-hourglass-half text-danger',
            'status': 'fas fa-clipboard-check text-success',
            'profile': 'fas fa-user-edit text-warning',
            'announcement': 'fas fa-bell text-info'
        }
        return icon_map.get(self.type, 'fas fa-bell text-primary')

    def __repr__(self):
        return f'<Notification user_id={self.user_id} title={self.title}>'


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, Resolved, Dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Report id={self.id} opp_id={self.opportunity_id}>'
