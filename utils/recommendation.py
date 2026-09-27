from datetime import date
from models import Opportunity

def calculate_match_score(student_profile, opportunity):
    """
    Rule-based recommendation engine.
    Calculates match percentage (0-100%) between student profile and opportunity.
    Returns a dictionary with score, percentage string, matched items, and reasons.
    """
    if not student_profile:
        # Default fallback score for unauthenticated/unfilled profiles
        base_score = 65 if opportunity.featured else 50
        return {
            'score': base_score,
            'percentage': f"{base_score}%",
            'matched_skills': [],
            'matched_interests': [],
            'category_match': False,
            'reasons': ['Popular opportunity', 'Featured discovery'] if opportunity.featured else ['General recommendation']
        }

    total_score = 0
    reasons = []
    matched_skills = []
    matched_interests = []

    # 1. Skill Matching (Weight: 40 points)
    opp_skills = [s.strip().lower() for s in (opportunity.skills or '').split(',') if s.strip()]
    student_skills = [s.name.lower() for s in student_profile.skills]
    
    if opp_skills and student_skills:
        for sk in student_skills:
            for req in opp_skills:
                if req in sk or sk in req:
                    matched_skills.append(req.title())
                    break
        matched_skills = list(set(matched_skills))
        if len(opp_skills) > 0:
            match_ratio = min(1.0, len(matched_skills) / len(opp_skills))
            skill_points = int(match_ratio * 40)
            total_score += skill_points
            if matched_skills:
                reasons.append(f"Matches your skills: {', '.join(matched_skills[:3])}")
    elif not opp_skills:
        # Opportunity requires no specific skills -> beginner-friendly
        total_score += 25
        reasons.append("No prerequisite skills required")

    # 2. Interest Matching (Weight: 20 points)
    student_interests = [i.name.lower() for i in student_profile.interests]
    opp_text = f"{opportunity.title} {opportunity.description} {opportunity.category}".lower()
    
    for interest in student_interests:
        if interest in opp_text:
            matched_interests.append(interest.title())
    
    matched_interests = list(set(matched_interests))
    if matched_interests:
        interest_points = min(20, len(matched_interests) * 10)
        total_score += interest_points
        reasons.append(f"Aligns with your interests: {', '.join(matched_interests[:2])}")
    elif len(student_interests) == 0:
        total_score += 10

    # 3. Category Match (Weight: 20 points)
    pref_categories = [c.lower() for c in student_profile.get_preferred_categories_list()]
    if pref_categories:
        if opportunity.category.lower() in pref_categories:
            total_score += 20
            reasons.append(f"In your preferred category: {opportunity.category}")
        else:
            total_score += 5
    else:
        # No category preference set
        total_score += 12

    # 4. Education & Branch Eligibility (Weight: 10 points)
    eligibility_text = (opportunity.eligibility or '').lower()
    student_branch = (student_profile.branch or '').lower()
    student_degree = (student_profile.degree or '').lower()
    
    is_eligible = False
    if not eligibility_text or "all" in eligibility_text or "open to all" in eligibility_text:
        is_eligible = True
        total_score += 10
        reasons.append("Open to all academic backgrounds")
    else:
        if student_branch and (student_branch in eligibility_text or "engineering" in student_branch and "engineering" in eligibility_text):
            is_eligible = True
            total_score += 10
            reasons.append(f"Matches your branch: {student_profile.branch}")
        elif student_degree and student_degree in eligibility_text:
            is_eligible = True
            total_score += 8
            reasons.append(f"Matches your degree: {student_profile.degree}")
        else:
            total_score += 4

    # 5. Work Mode & Location (Weight: 5 points)
    student_pref_mode = (student_profile.work_preference or 'Any').lower()
    opp_mode = (opportunity.mode or '').lower()
    if student_pref_mode == 'any' or student_pref_mode == opp_mode:
        total_score += 5
        reasons.append(f"Preferred work mode: {opportunity.mode}")
    elif 'remote' in student_pref_mode and opp_mode == 'online':
        total_score += 5
        reasons.append("Online / Remote friendly")

    # 6. Deadline Active & Urgency (Weight: 5 points)
    days_left = opportunity.days_remaining()
    if days_left is not None:
        if days_left >= 0:
            total_score += 5
        else:
            total_score = max(10, total_score - 20)  # Penalize expired opportunities
            reasons.append("Deadline has passed")
    else:
        total_score += 5

    # Scale between 40% and 98% for realistic UX
    final_score = max(35, min(99, total_score))

    return {
        'score': final_score,
        'percentage': f"{final_score}%",
        'matched_skills': matched_skills,
        'matched_interests': matched_interests,
        'category_match': opportunity.category.lower() in pref_categories if pref_categories else False,
        'reasons': reasons if reasons else ['Based on trending student activity']
    }


def get_recommended_opportunities(student_profile, limit=10, min_score=40):
    """
    Fetches active opportunities and sorts them by match score for the student.
    """
    opportunities = Opportunity.query.filter_by(status='Active').all()
    
    scored_opps = []
    for opp in opportunities:
        match_info = calculate_match_score(student_profile, opp)
        if match_info['score'] >= min_score:
            scored_opps.append({
                'opportunity': opp,
                'match': match_info
            })
            
    scored_opps.sort(key=lambda x: (x['match']['score'], x['opportunity'].featured), reverse=True)
    return scored_opps[:limit]


def get_similar_opportunities(opportunity, limit=4):
    """
    Finds opportunities in the same category or sharing required skills.
    """
    query = Opportunity.query.filter(
        Opportunity.id != opportunity.id,
        Opportunity.status == 'Active'
    )
    
    # Prioritize same category
    same_cat = query.filter_by(category=opportunity.category).limit(limit).all()
    if len(same_cat) >= limit:
        return same_cat
        
    # Fallback to general active opportunities
    additional = query.filter(Opportunity.id.notin_([o.id for o in same_cat])).limit(limit - len(same_cat)).all()
    return same_cat + additional
