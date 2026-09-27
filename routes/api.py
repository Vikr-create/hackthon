from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date
from models import db, Opportunity, Bookmark, Application, Notification

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/bookmark/toggle', methods=['POST'])
@login_required
def toggle_bookmark():
    data = request.get_json() or {}
    opp_id = data.get('opportunity_id') or request.form.get('opportunity_id', type=int)

    if not opp_id:
        return jsonify({'success': False, 'message': 'Missing opportunity_id'}), 400

    opp = Opportunity.query.get(opp_id)
    if not opp:
        return jsonify({'success': False, 'message': 'Opportunity not found'}), 404

    existing = Bookmark.query.filter_by(user_id=current_user.id, opportunity_id=opp_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        bookmarked = False
        message = "Removed from bookmarks"
    else:
        new_bm = Bookmark(user_id=current_user.id, opportunity_id=opp_id)
        db.session.add(new_bm)
        db.session.commit()
        bookmarked = True
        message = "Added to bookmarks"

    total_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).count()

    return jsonify({
        'success': True,
        'bookmarked': bookmarked,
        'message': message,
        'total_user_bookmarks': total_bookmarks,
        'opp_bookmark_count': opp.bookmark_count()
    })


@api_bp.route('/application/status', methods=['POST'])
@login_required
def update_application_status():
    data = request.get_json() or {}
    opp_id = data.get('opportunity_id')
    new_status = data.get('status')
    notes = data.get('notes', '')

    if not opp_id or not new_status:
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400

    if new_status not in Application.STATUS_CHOICES:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    app = Application.query.filter_by(user_id=current_user.id, opportunity_id=opp_id).first()
    if not app:
        app = Application(
            user_id=current_user.id,
            opportunity_id=opp_id,
            status=new_status,
            notes=notes,
            applied_date=date.today()
        )
        db.session.add(app)
    else:
        app.status = new_status
        if notes:
            app.notes = notes

    db.session.commit()
    return jsonify({
        'success': True,
        'status': app.status,
        'badge_class': app.status_badge_class(),
        'message': f"Application updated to {app.status}"
    })


@api_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    opps = Opportunity.query.filter(
        Opportunity.status == 'Active',
        (Opportunity.title.ilike(f'%{q}%') | Opportunity.organization.ilike(f'%{q}%'))
    ).limit(6).all()

    results = []
    for opp in opps:
        results.append({
            'id': opp.id,
            'title': opp.title,
            'organization': opp.organization,
            'category': opp.category,
            'mode': opp.mode
        })

    return jsonify(results)
