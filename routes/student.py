from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, asc
from models import (
    db, User, StudentProfile, Opportunity, Category, Skill, Interest,
    Bookmark, Application, Notification, Report
)
from utils.recommendation import calculate_match_score, get_recommended_opportunities, get_similar_opportunities
from utils.helpers import send_notification

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    profile = current_user.profile
    completion_percentage = profile.calculate_completion_percentage() if profile else 0

    # Top recommendations
    recommendations = get_recommended_opportunities(profile, limit=4)

    # Saved bookmarks preview
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).limit(4).all()
    bookmarked_opps = [b.opportunity for b in bookmarks if b.opportunity]

    # Upcoming deadlines
    today = date.today()
    upcoming_deadlines = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline >= today
    ).order_by(Opportunity.deadline.asc()).limit(4).all()

    # Application status stats
    user_apps = Application.query.filter_by(user_id=current_user.id).all()
    app_stats = {
        'total': len(user_apps),
        'Interested': sum(1 for a in user_apps if a.status == 'Interested'),
        'Applied': sum(1 for a in user_apps if a.status == 'Applied'),
        'Shortlisted': sum(1 for a in user_apps if a.status == 'Shortlisted'),
        'Selected': sum(1 for a in user_apps if a.status == 'Selected'),
        'Rejected': sum(1 for a in user_apps if a.status == 'Rejected'),
        'Completed': sum(1 for a in user_apps if a.status == 'Completed'),
    }

    # Trending & New opportunities
    trending = Opportunity.query.filter_by(status='Active').order_by(Opportunity.views_count.desc()).limit(4).all()
    new_opps = Opportunity.query.filter_by(status='Active').order_by(Opportunity.created_at.desc()).limit(4).all()

    return render_template(
        'student/dashboard.html',
        profile=profile,
        completion_percentage=completion_percentage,
        recommendations=recommendations,
        bookmarked_opps=bookmarked_opps,
        upcoming_deadlines=upcoming_deadlines,
        app_stats=app_stats,
        trending=trending,
        new_opps=new_opps
    )


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile = current_user.profile
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    all_categories = Category.query.all()
    all_skills = Skill.query.order_by(Skill.name).all()
    all_interests = Interest.query.order_by(Interest.name).all()

    if request.method == 'POST':
        profile.full_name = request.form.get('full_name', '').strip()
        profile.phone = request.form.get('phone', '').strip()
        profile.college = request.form.get('college', '').strip()
        profile.university = request.form.get('university', '').strip()
        profile.degree = request.form.get('degree', '').strip()
        profile.branch = request.form.get('branch', '').strip()
        profile.year = request.form.get('year', '').strip()
        
        sem = request.form.get('semester', '').strip()
        profile.semester = int(sem) if sem.isdigit() else None

        cgpa_val = request.form.get('cgpa', '').strip()
        try:
            profile.cgpa = float(cgpa_val) if cgpa_val else None
        except ValueError:
            profile.cgpa = None

        grad_yr = request.form.get('graduation_year', '').strip()
        profile.graduation_year = int(grad_yr) if grad_yr.isdigit() else None

        profile.location = request.form.get('location', '').strip()
        profile.work_preference = request.form.get('work_preference', 'Any')
        
        # Preferred categories list
        selected_categories = request.form.getlist('preferred_categories')
        profile.preferred_categories = ','.join(selected_categories)

        # Experience & links
        profile.experience = request.form.get('experience', '').strip()
        profile.resume_link = request.form.get('resume_link', '').strip()
        profile.linkedin = request.form.get('linkedin', '').strip()
        profile.github = request.form.get('github', '').strip()
        profile.portfolio = request.form.get('portfolio', '').strip()
        profile.bio = request.form.get('bio', '').strip()

        # Handle Skills
        raw_skills = request.form.get('skills_input', '').strip()
        if raw_skills:
            skill_names = [s.strip().title() for s in raw_skills.split(',') if s.strip()]
            new_skills_list = []
            for s_name in skill_names:
                existing_skill = Skill.query.filter_by(name=s_name).first()
                if not existing_skill:
                    existing_skill = Skill(name=s_name, category='General')
                    db.session.add(existing_skill)
                    db.session.flush()
                new_skills_list.append(existing_skill)
            profile.skills = new_skills_list
        else:
            profile.skills = []

        # Handle Interests
        raw_interests = request.form.get('interests_input', '').strip()
        if raw_interests:
            interest_names = [i.strip().title() for i in raw_interests.split(',') if i.strip()]
            new_interests_list = []
            for i_name in interest_names:
                existing_interest = Interest.query.filter_by(name=i_name).first()
                if not existing_interest:
                    existing_interest = Interest(name=i_name)
                    db.session.add(existing_interest)
                    db.session.flush()
                new_interests_list.append(existing_interest)
            profile.interests = new_interests_list
        else:
            profile.interests = []

        profile.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('student.profile'))

    completion_percentage = profile.calculate_completion_percentage()
    student_skills_str = ', '.join([s.name for s in profile.skills])
    student_interests_str = ', '.join([i.name for i in profile.interests])
    user_preferred_cats = profile.get_preferred_categories_list()

    return render_template(
        'student/profile.html',
        profile=profile,
        completion_percentage=completion_percentage,
        all_categories=all_categories,
        all_skills=all_skills,
        all_interests=all_interests,
        student_skills_str=student_skills_str,
        student_interests_str=student_interests_str,
        user_preferred_cats=user_preferred_cats
    )


@student_bp.route('/opportunities')
def opportunities():
    profile = current_user.profile if current_user.is_authenticated else None
    
    # Query parameters
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    mode = request.args.get('mode', '').strip()
    is_paid = request.args.get('is_paid', '').strip()
    stipend = request.args.get('stipend', '').strip()
    location = request.args.get('location', '').strip()
    beginner = request.args.get('beginner_friendly', '').strip()
    featured = request.args.get('featured', '').strip()
    verified = request.args.get('verified', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()
    page = request.args.get('page', 1, type=int)

    query = Opportunity.query.filter_by(status='Active')

    # Keyword Search (title, organization, description, skills, category, location)
    if q:
        search_filter = or_(
            Opportunity.title.ilike(f'%{q}%'),
            Opportunity.organization.ilike(f'%{q}%'),
            Opportunity.description.ilike(f'%{q}%'),
            Opportunity.skills.ilike(f'%{q}%'),
            Opportunity.category.ilike(f'%{q}%'),
            Opportunity.location.ilike(f'%{q}%')
        )
        query = query.filter(search_filter)

    # Category Filter
    if category and category != 'All':
        query = query.filter_by(category=category)

    # Mode Filter
    if mode and mode != 'All':
        query = query.filter_by(mode=mode)

    # Paid / Free Filter
    if is_paid == '1':
        query = query.filter_by(is_paid=True)
    elif is_paid == '0':
        query = query.filter_by(is_paid=False)

    # Location Filter
    if location:
        query = query.filter(Opportunity.location.ilike(f'%{location}%'))

    # Beginner Friendly
    if beginner == '1':
        query = query.filter_by(beginner_friendly=True)

    # Featured
    if featured == '1':
        query = query.filter_by(featured=True)

    # Verified
    if verified == '1':
        query = query.filter_by(verified=True)

    # Sorting
    if sort_by == 'deadline':
        query = query.order_by(Opportunity.deadline.asc().nullslast())
    elif sort_by == 'popular':
        query = query.order_by(Opportunity.views_count.desc())
    elif sort_by == 'title_asc':
        query = query.order_by(Opportunity.title.asc())
    elif sort_by == 'stipend_high':
        query = query.order_by(Opportunity.is_paid.desc(), Opportunity.stipend.desc().nullslast())
    else:  # newest default
        query = query.order_by(Opportunity.created_at.desc())

    # Pagination
    per_page = 9
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    opportunities_list = pagination.items

    # Match percentage computation & bookmark mapping
    opp_cards = []
    bookmarked_ids = set()
    if current_user.is_authenticated:
        user_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
        bookmarked_ids = {b.opportunity_id for b in user_bookmarks}

    for opp in opportunities_list:
        match_info = calculate_match_score(profile, opp)
        opp_cards.append({
            'opp': opp,
            'match': match_info,
            'is_bookmarked': opp.id in bookmarked_ids
        })

    categories = Category.query.all()

    return render_template(
        'student/opportunities.html',
        opp_cards=opp_cards,
        pagination=pagination,
        categories=categories,
        selected_category=category,
        selected_mode=mode,
        selected_sort=sort_by,
        search_query=q,
        is_paid=is_paid,
        location_filter=location,
        beginner=beginner,
        featured=featured,
        verified=verified,
        total_count=pagination.total
    )


@student_bp.route('/opportunity/<int:id>')
def opportunity_detail(id):
    opp = Opportunity.query.get_or_404(id)
    
    # Increment views
    opp.views_count = (opp.views_count or 0) + 1
    db.session.commit()

    profile = current_user.profile if current_user.is_authenticated else None
    match_info = calculate_match_score(profile, opp)
    
    # Bookmark status
    is_bookmarked = False
    application = None
    if current_user.is_authenticated:
        is_bookmarked = Bookmark.query.filter_by(user_id=current_user.id, opportunity_id=opp.id).first() is not None
        application = Application.query.filter_by(user_id=current_user.id, opportunity_id=opp.id).first()

    similar_opps = get_similar_opportunities(opp, limit=3)

    return render_template(
        'student/opportunity_detail.html',
        opp=opp,
        match=match_info,
        is_bookmarked=is_bookmarked,
        application=application,
        similar_opps=similar_opps
    )


@student_bp.route('/bookmarks')
@login_required
def bookmarks():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Bookmark.query.filter_by(user_id=current_user.id).join(Opportunity)

    if q:
        query = query.filter(
            or_(
                Opportunity.title.ilike(f'%{q}%'),
                Opportunity.organization.ilike(f'%{q}%'),
                Opportunity.category.ilike(f'%{q}%')
            )
        )
    if category and category != 'All':
        query = query.filter(Opportunity.category == category)

    saved_bookmarks = query.order_by(Bookmark.created_at.desc()).all()
    categories = Category.query.all()

    return render_template(
        'student/bookmarks.html',
        saved_bookmarks=saved_bookmarks,
        categories=categories,
        selected_category=category,
        search_query=q
    )


@student_bp.route('/applications', methods=['GET', 'POST'])
@login_required
def applications():
    if request.method == 'POST':
        opp_id = request.form.get('opportunity_id', type=int)
        status = request.form.get('status', 'Interested')
        notes = request.form.get('notes', '').strip()

        if not opp_id:
            flash("Invalid opportunity selection.", "danger")
            return redirect(url_for('student.applications'))

        app_record = Application.query.filter_by(user_id=current_user.id, opportunity_id=opp_id).first()
        if not app_record:
            app_record = Application(
                user_id=current_user.id,
                opportunity_id=opp_id,
                status=status,
                notes=notes,
                applied_date=date.today()
            )
            db.session.add(app_record)
            flash("Opportunity added to your Application Tracker!", "success")
        else:
            app_record.status = status
            app_record.notes = notes
            flash("Application tracker updated!", "info")

        db.session.commit()
        return redirect(url_for('student.applications'))

    status_filter = request.args.get('status', 'All')
    query = Application.query.filter_by(user_id=current_user.id).join(Opportunity)

    if status_filter != 'All':
        query = query.filter(Application.status == status_filter)

    user_applications = query.order_by(Application.updated_at.desc()).all()
    
    # Counts
    all_apps = Application.query.filter_by(user_id=current_user.id).all()
    status_counts = {status: 0 for status in Application.STATUS_CHOICES}
    for a in all_apps:
        if a.status in status_counts:
            status_counts[a.status] += 1

    return render_template(
        'student/applications.html',
        applications=user_applications,
        selected_status=status_filter,
        status_choices=Application.STATUS_CHOICES,
        status_counts=status_counts,
        total_tracked=len(all_apps)
    )


@student_bp.route('/recommendations')
@login_required
def recommendations():
    profile = current_user.profile
    if not profile or profile.calculate_completion_percentage() < 20:
        flash("Complete your profile (Skills, Branch, Interests) to unlock higher accuracy recommendations!", "warning")

    recommended_list = get_recommended_opportunities(profile, limit=20, min_score=35)

    bookmarked_ids = {b.opportunity_id for b in Bookmark.query.filter_by(user_id=current_user.id).all()}

    return render_template(
        'student/recommendations.html',
        recommended_list=recommended_list,
        bookmarked_ids=bookmarked_ids,
        profile=profile
    )


@student_bp.route('/deadlines')
def deadlines():
    today = date.today()
    urgent_date = today + timedelta(days=3)
    soon_date = today + timedelta(days=14)

    urgent = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline >= today,
        Opportunity.deadline <= urgent_date
    ).order_by(Opportunity.deadline.asc()).all()

    soon = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline > urgent_date,
        Opportunity.deadline <= soon_date
    ).order_by(Opportunity.deadline.asc()).all()

    later = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline > soon_date
    ).order_by(Opportunity.deadline.asc()).all()

    expired = Opportunity.query.filter(
        Opportunity.status == 'Active',
        Opportunity.deadline < today
    ).order_by(Opportunity.deadline.desc()).limit(10).all()

    return render_template(
        'student/deadlines.html',
        urgent=urgent,
        soon=soon,
        later=later,
        expired=expired
    )


@student_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('student/notifications.html', notifications=notifs)


@student_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "info")
    return redirect(url_for('student.notifications'))


@student_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_password':
            old_pass = request.form.get('old_password')
            new_pass = request.form.get('new_password')
            confirm_pass = request.form.get('confirm_password')

            if not current_user.check_password(old_pass):
                flash("Current password is incorrect.", "danger")
            elif len(new_pass) < 6:
                flash("New password must be at least 6 characters.", "warning")
            elif new_pass != confirm_pass:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_pass)
                db.session.commit()
                flash("Password updated successfully!", "success")
        elif action == 'save_preferences':
            flash("Notification preferences saved.", "success")
        return redirect(url_for('student.settings'))

    return render_template('student/settings.html')


@student_bp.route('/report/<int:id>', methods=['POST'])
@login_required
def report_opportunity(id):
    opp = Opportunity.query.get_or_404(id)
    reason = request.form.get('reason', '').strip()
    details = request.form.get('details', '').strip()

    if not reason:
        flash("Please provide a reason for the report.", "warning")
        return redirect(url_for('student.opportunity_detail', id=opp.id))

    report = Report(
        user_id=current_user.id,
        opportunity_id=opp.id,
        reason=reason,
        details=details
    )
    db.session.add(report)
    db.session.commit()

    flash("Thank you for your report. The administrative team will inspect this opportunity.", "info")
    return redirect(url_for('student.opportunity_detail', id=opp.id))
