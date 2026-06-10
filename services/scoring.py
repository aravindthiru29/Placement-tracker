from datetime import date, datetime
from models import db, User, LeetCodeProgress, AptitudeProgress, GitHubProgress, MonthlyProject

def get_latest_leetcode(user_id):
    return LeetCodeProgress.query.filter_by(user_id=user_id).order_by(LeetCodeProgress.date.desc()).first()

def get_latest_aptitude(user_id):
    return AptitudeProgress.query.filter_by(user_id=user_id).order_by(AptitudeProgress.date.desc()).first()

def get_latest_github(user_id):
    return GitHubProgress.query.filter_by(user_id=user_id).order_by(GitHubProgress.date.desc()).first()

def get_current_project(user_id):
    # Returns the project that has a deadline in the current month/year or is active
    today = date.today()
    # Find projects where deadline is this month or later, or not completed yet
    project = MonthlyProject.query.filter_by(user_id=user_id)\
        .order_by(MonthlyProject.deadline.desc()).first()
    return project

def calculate_readiness_score(user_id):
    """
    Calculates readiness score out of 100:
    1. LeetCode (35%): target 200 total solved problems
    2. Aptitude (25%): target 300 questions (12.5 pts) and 80%+ accuracy (12.5 pts)
    3. GitHub (20%): target score (commits + PR*5 + features*10) of 150 points
    4. Monthly Project (20%): current project progress (completion_percentage * 0.20)
    """
    # 1. LeetCode Score (Max 35)
    lc = get_latest_leetcode(user_id)
    lc_score = 0.0
    lc_total = 0
    if lc:
        lc_total = lc.total_solved or (lc.easy_solved + lc.medium_solved + lc.hard_solved)
        # Target of 200 total solved
        lc_score = min(35.0, (lc_total / 200.0) * 35.0)
    
    # 2. Aptitude Score (Max 25)
    apt = get_latest_aptitude(user_id)
    apt_score = 0.0
    apt_total = 0
    apt_accuracy = 0.0
    if apt:
        apt_total = apt.total_questions or (apt.quant_questions + apt.logical_questions + apt.verbal_questions)
        apt_accuracy = apt.accuracy_percentage or 0.0
        
        # 12.5 pts for volume (target 300 questions)
        vol_score = min(12.5, (apt_total / 300.0) * 12.5)
        # 12.5 pts for accuracy (target 80% accuracy)
        acc_score = min(12.5, (apt_accuracy / 80.0) * 12.5)
        apt_score = vol_score + acc_score

    # 3. GitHub Score (Max 20)
    gh = get_latest_github(user_id)
    gh_score = 0.0
    gh_points = 0
    if gh:
        # Calculate a weighted contribution score: commits + PR*5 + features*10
        gh_points = (gh.commits or 0) + ((gh.pull_requests or 0) * 5) + ((gh.features_completed or 0) * 10)
        # Target of 150 contribution points
        gh_score = min(20.0, (gh_points / 150.0) * 20.0)

    # 4. Monthly Project Score (Max 20)
    proj = get_current_project(user_id)
    proj_score = 0.0
    proj_percentage = 0
    if proj:
        proj_percentage = proj.completion_percentage
        if proj.status == 'Completed':
            proj_score = 20.0
        else:
            # Cap at 15.0 (75% of project points) until officially approved by Admin
            proj_score = min(15.0, (proj_percentage / 100.0) * 20.0)
            
    overall_score = round(lc_score + apt_score + gh_score + proj_score, 1)
    
    return {
        'overall': overall_score,
        'leetcode': round(lc_score, 1),
        'leetcode_total': lc_total,
        'aptitude': round(apt_score, 1),
        'aptitude_total': apt_total,
        'aptitude_accuracy': apt_accuracy,
        'github': round(gh_score, 1),
        'github_points': gh_points,
        'project': round(proj_score, 1),
        'project_percentage': proj_percentage,
        'project_name': proj.project_name if proj else 'No Active Project'
    }

def calculate_leaderboard():
    """
    Leaderboard scoring rules:
    - Easy Problem = 2 points
    - Medium Problem = 5 points
    - Hard Problem = 10 points
    - 10 Aptitude Questions = 3 points (0.3 points per question)
    - GitHub Feature Completed = 10 points
    - Monthly Project Completed = 100 points
    """
    users = User.query.filter_by(role='member').all()
    leaderboard = []
    
    for user in users:
        # LeetCode points
        lc = get_latest_leetcode(user.id)
        lc_pts = 0
        if lc:
            lc_pts = (lc.easy_solved * 2) + (lc.medium_solved * 5) + (lc.hard_solved * 10)
            
        # Aptitude points
        apt = get_latest_aptitude(user.id)
        apt_pts = 0
        if apt:
            total_q = apt.total_questions or (apt.quant_questions + apt.logical_questions + apt.verbal_questions)
            apt_pts = total_q * 0.3
            
        # GitHub points (Features Completed)
        gh = get_latest_github(user.id)
        gh_pts = 0
        if gh:
            gh_pts = (gh.features_completed or 0) * 10
            
        # Projects points (completed projects)
        proj_count = MonthlyProject.query.filter_by(user_id=user.id, status='Completed').count()
        proj_pts = proj_count * 100
        
        total_score = round(lc_pts + apt_pts + gh_pts + proj_pts, 1)
        
        # Calculate trend (for demonstration, compare this month's score with overall history,
        # or mock a trend indicator based on recent updates)
        # We can look at how many updates they made in the last 7 days.
        recent_updates = LeetCodeProgress.query.filter_by(user_id=user.id).filter(LeetCodeProgress.date >= date.today()).count() + \
                         AptitudeProgress.query.filter_by(user_id=user.id).filter(AptitudeProgress.date >= date.today()).count()
        trend = 'up' if recent_updates > 0 else 'flat'
        
        leaderboard.append({
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'score': total_score,
            'trend': trend,
            'lc_pts': lc_pts,
            'apt_pts': round(apt_pts, 1),
            'gh_pts': gh_pts,
            'proj_pts': proj_pts
        })
        
    # Sort leaderboard by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Assign ranks
    for rank, entry in enumerate(leaderboard, 1):
        entry['rank'] = rank
        
    return leaderboard
