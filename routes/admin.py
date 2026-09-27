from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import func, desc
from models import (
    db, User, StudentProfile, Opportunity, Category, Skill,
    Bookmark, Application, Report
)
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    today = date.today()
    total_students = User.query.filter_by(role='student').count()
    total_opportunities = Opportunity.query.count()
    active_opportunities = Opportunity.query.filter_by(status='Active').count()
    expired_opportunities = Opportunity.query.filter(
        Opportunity.deadline < today,
        Opportunity.status == 'Active'
    ).count()
    total_bookmarks = Bookmark.query.count()
    total_applications = Application.query.count()
    pending_reports = Report.query.filter_by(status='Pending').count()

    # Category distribution
    cat_counts = db.session.query(
        Opportunity.category, func.count(Opportunity.id)
    ).group_by(Opportunity.category).all()
    categories_chart = {
        'labels': [c[0] for c in cat_counts],
        'data': [c[1] for c in cat_counts]
    }

    # Students by branch
    branch_counts = db.session.query(
        StudentProfile.branch, func.count(StudentProfile.id)
    ).filter(StudentProfile.branch.isnot(None)).group_by(StudentProfile.branch).limit(8).all()
    branches_chart = {
        'labels': [b[0] for b in branch_counts if b[0]],
        'data': [b[1] for b in branch_counts if b[0]]
    }

    # Applications by status
    app_counts = db.session.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    apps_chart = {
        'labels': [a[0] for a in app_counts],
        'data': [a[1] for a in app_counts]
    }

    # Recent opportunities
    recent_opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_opportunities=total_opportunities,
        active_opportunities=active_opportunities,
        expired_opportunities=expired_opportunities,
        total_bookmarks=total_bookmarks,
        total_applications=total_applications,
        pending_reports=pending_reports,
        categories_chart=categories_chart,
        branches_chart=branches_chart,
        apps_chart=apps_chart,
        recent_opportunities=recent_opportunities
    )


@admin_bp.route('/opportunities')
@admin_required
def opportunities():
    status = request.args.get('status', 'All')
    category = request.args.get('category', 'All')
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Opportunity.query

    if status != 'All':
        query = query.filter_by(status=status)
    if category != 'All':
        query = query.filter_by(category=category)
    if q:
        query = query.filter(
            Opportunity.title.ilike(f'%{q}%') |
            Opportunity.organization.ilike(f'%{q}%')
        )

    pagination = query.order_by(Opportunity.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    categories = Category.query.all()

    return render_template(
        'admin/opportunities.html',
        opportunities=pagination.items,
        pagination=pagination,
        categories=categories,
        selected_status=status,
        selected_category=category,
        search_query=q
    )


@admin_bp.route('/opportunities/new', methods=['GET', 'POST'])
@admin_required
def create_opportunity():
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        org = request.form.get('organization', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        location = request.form.get('location', 'Remote').strip()
        mode = request.form.get('mode', 'Online').strip()
        
        deadline_str = request.form.get('deadline', '').strip()
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                deadline = None

        stipend = request.form.get('stipend', '').strip()
        prize = request.form.get('prize', '').strip()
        is_paid = bool(request.form.get('is_paid'))
        beginner_friendly = bool(request.form.get('beginner_friendly'))
        reg_link = request.form.get('registration_link', '').strip()
        website = request.form.get('website', '').strip()
        contact = request.form.get('contact_email', '').strip()
        featured = bool(request.form.get('featured'))
        verified = bool(request.form.get('verified', True))
        status = request.form.get('status', 'Active')

        if not title or not org or not category or not description or not reg_link:
            flash("Please fill in all required fields marked with *.", "danger")
            return render_template('admin/opportunity_form.html', categories=categories, opportunity=None)

        opp = Opportunity(
            title=title,
            organization=org,
            category=category,
            description=description,
            skills=skills,
            eligibility=eligibility,
            location=location,
            mode=mode,
            deadline=deadline,
            stipend=stipend if stipend else None,
            prize=prize if prize else None,
            is_paid=is_paid,
            beginner_friendly=beginner_friendly,
            registration_link=reg_link,
            website=website,
            contact_email=contact,
            featured=featured,
            verified=verified,
            status=status
        )
        db.session.add(opp)
        db.session.commit()

        flash("Opportunity created successfully!", "success")
        return redirect(url_for('admin.opportunities'))

    return render_template('admin/opportunity_form.html', categories=categories, opportunity=None)


@admin_bp.route('/opportunities/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_opportunity(id):
    opp = Opportunity.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == 'POST':
        opp.title = request.form.get('title', '').strip()
        opp.organization = request.form.get('organization', '').strip()
        opp.category = request.form.get('category', '').strip()
        opp.description = request.form.get('description', '').strip()
        opp.skills = request.form.get('skills', '').strip()
        opp.eligibility = request.form.get('eligibility', '').strip()
        opp.location = request.form.get('location', 'Remote').strip()
        opp.mode = request.form.get('mode', 'Online').strip()

        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                opp.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            opp.deadline = None

        opp.stipend = request.form.get('stipend', '').strip() or None
        opp.prize = request.form.get('prize', '').strip() or None
        opp.is_paid = bool(request.form.get('is_paid'))
        opp.beginner_friendly = bool(request.form.get('beginner_friendly'))
        opp.registration_link = request.form.get('registration_link', '').strip()
        opp.website = request.form.get('website', '').strip()
        opp.contact_email = request.form.get('contact_email', '').strip()
        opp.featured = bool(request.form.get('featured'))
        opp.verified = bool(request.form.get('verified'))
        opp.status = request.form.get('status', 'Active')
        opp.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Opportunity updated successfully!", "success")
        return redirect(url_for('admin.opportunities'))

    return render_template('admin/opportunity_form.html', categories=categories, opportunity=opp)


@admin_bp.route('/opportunities/<int:id>/delete', methods=['POST'])
@admin_required
def delete_opportunity(id):
    opp = Opportunity.query.get_or_404(id)
    db.session.delete(opp)
    db.session.commit()
    flash(f"Opportunity '{opp.title}' has been deleted.", "info")
    return redirect(url_for('admin.opportunities'))


@admin_bp.route('/opportunities/<int:id>/status/<new_status>', methods=['POST'])
@admin_required
def change_opportunity_status(id, new_status):
    opp = Opportunity.query.get_or_404(id)
    if new_status in ['Active', 'Pending', 'Closed', 'Rejected']:
        opp.status = new_status
        db.session.commit()
        flash(f"Status for '{opp.title}' changed to {new_status}.", "success")
    return redirect(request.referrer or url_for('admin.opportunities'))


@admin_bp.route('/opportunities/<int:id>/toggle-feature', methods=['POST'])
@admin_required
def toggle_feature(id):
    opp = Opportunity.query.get_or_404(id)
    opp.featured = not opp.featured
    db.session.commit()
    flash(f"Opportunity {'marked as featured' if opp.featured else 'unfeatured'}.", "info")
    return redirect(request.referrer or url_for('admin.opportunities'))


@admin_bp.route('/opportunities/<int:id>/toggle-verify', methods=['POST'])
@admin_required
def toggle_verify(id):
    opp = Opportunity.query.get_or_404(id)
    opp.verified = not opp.verified
    db.session.commit()
    flash(f"Opportunity verification status updated.", "info")
    return redirect(request.referrer or url_for('admin.opportunities'))


@admin_bp.route('/students')
@admin_required
def students():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = User.query.filter_by(role='student')
    if q:
        query = query.join(StudentProfile).filter(
            User.email.ilike(f'%{q}%') |
            StudentProfile.full_name.ilike(f'%{q}%') |
            StudentProfile.college.ilike(f'%{q}%') |
            StudentProfile.branch.ilike(f'%{q}%')
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'admin/students.html',
        students=pagination.items,
        pagination=pagination,
        search_query=q
    )


@admin_bp.route('/students/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_student_status(id):
    student = User.query.get_or_404(id)
    if student.is_admin():
        flash("Cannot deactivate an administrator account.", "danger")
        return redirect(url_for('admin.students'))

    student.is_active = not student.is_active
    db.session.commit()
    status_str = "activated" if student.is_active else "deactivated"
    flash(f"Account for {student.email} has been {status_str}.", "info")
    return redirect(url_for('admin.students'))


@admin_bp.route('/analytics')
@admin_required
def analytics():
    # 1. Opportunities by category
    cat_data = db.session.query(
        Opportunity.category, func.count(Opportunity.id)
    ).group_by(Opportunity.category).all()

    # 2. Opportunities by mode
    mode_data = db.session.query(
        Opportunity.mode, func.count(Opportunity.id)
    ).group_by(Opportunity.mode).all()

    # 3. Applications status breakdown
    app_data = db.session.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()

    # 4. Top skills in opportunities
    opps = Opportunity.query.filter(Opportunity.skills.isnot(None)).all()
    skill_frequency = {}
    for o in opps:
        for sk in o.skills_list:
            sk_clean = sk.strip().title()
            skill_frequency[sk_clean] = skill_frequency.get(sk_clean, 0) + 1
    top_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

    # 5. Top universities / colleges
    college_data = db.session.query(
        StudentProfile.college, func.count(StudentProfile.id)
    ).filter(StudentProfile.college.isnot(None)).group_by(StudentProfile.college).limit(6).all()

    return render_template(
        'admin/analytics.html',
        cat_data=cat_data,
        mode_data=mode_data,
        app_data=app_data,
        top_skills=top_skills,
        college_data=college_data
    )


@admin_bp.route('/reports')
@admin_required
def reports():
    reports_list = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin/reports.html', reports=reports_list)


@admin_bp.route('/reports/<int:id>/status/<new_status>', methods=['POST'])
@admin_required
def update_report_status(id, new_status):
    report = Report.query.get_or_404(id)
    if new_status in ['Resolved', 'Dismissed', 'Pending']:
        report.status = new_status
        db.session.commit()
        flash(f"Report marked as {new_status}.", "info")
    return redirect(url_for('admin.reports'))
