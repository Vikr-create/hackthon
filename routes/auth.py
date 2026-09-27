from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, StudentProfile
from utils.helpers import send_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact support.", "danger")
                return render_template('auth/login.html')

            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)

            flash(f"Welcome back, {user.profile.full_name if user.profile and user.profile.full_name else user.email}!", "success")
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        college = request.form.get('college', '').strip()
        branch = request.form.get('branch', '').strip()

        # Validations
        if not full_name or not email or not password:
            flash("All mandatory fields are required.", "danger")
            return render_template('auth/register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('auth/register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email address already exists. Please login.", "warning")
            return redirect(url_for('auth.login'))

        # Create new student user
        user = User(email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id,
            full_name=full_name,
            college=college if college else None,
            branch=branch if branch else None
        )
        db.session.add(profile)
        db.session.commit()

        # Create welcome notification
        send_notification(
            user_id=user.id,
            title="Welcome to OpportunityHub!",
            message="Your account has been created. Complete your skills & education profile to unlock personalized recommendations.",
            link=url_for('student.profile'),
            notif_type='profile'
        )

        login_user(user)
        flash("Registration successful! Welcome to Student Opportunity Discovery Platform.", "success")
        return redirect(url_for('student.profile'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.index'))
