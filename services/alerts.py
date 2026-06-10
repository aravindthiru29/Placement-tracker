from datetime import date, datetime, timedelta
from models import db, Notification, LeetCodeProgress, AptitudeProgress, GitHubProgress, MonthlyProject

def create_notification_if_not_exists(user_id, message):
    """
    Avoids notification spam by checking if an identical unread notification
    or a notification with the same text created in the last 24 hours exists.
    """
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    existing = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.message == message,
        (Notification.is_read == False) | (Notification.created_at >= one_day_ago)
    ).first()
    
    if not existing:
        notif = Notification(user_id=user_id, message=message, created_at=datetime.utcnow(), is_read=False)
        db.session.add(notif)
        db.session.commit()
        return True
    return False

def check_and_generate_alerts(user_id):
    """
    Scans a user's recent logs and project states to automatically generate alert notifications:
    - No LeetCode activity for 7 days
    - No Aptitude activity for 7 days
    - No GitHub contribution for 10 days
    - Project not started
    - Project deadline approaching (within 3 days)
    - Project overdue
    """
    today = date.today()
    
    # 1. LeetCode inactivity (7 days)
    latest_lc = LeetCodeProgress.query.filter_by(user_id=user_id).order_by(LeetCodeProgress.date.desc()).first()
    if latest_lc:
        diff_days = (today - latest_lc.date).days
        if diff_days >= 7:
            create_notification_if_not_exists(
                user_id,
                f"Alert: No LeetCode progress has been logged for {diff_days} days. Keep coding!"
            )
    else:
        create_notification_if_not_exists(
            user_id,
            "Notice: You haven't logged any LeetCode progress. Log your first problems solved!"
        )
        
    # 2. Aptitude inactivity (7 days)
    latest_apt = AptitudeProgress.query.filter_by(user_id=user_id).order_by(AptitudeProgress.date.desc()).first()
    if latest_apt:
        diff_days = (today - latest_apt.date).days
        if diff_days >= 7:
            create_notification_if_not_exists(
                user_id,
                f"Alert: No Aptitude preparation has been logged for {diff_days} days. Don't let your quant skills slide!"
            )
    else:
        create_notification_if_not_exists(
            user_id,
            "Notice: You haven't logged any Aptitude preparation. Start loggin' questions solved!"
        )

    # 3. GitHub inactivity (10 days)
    latest_gh = GitHubProgress.query.filter_by(user_id=user_id).order_by(GitHubProgress.date.desc()).first()
    if latest_gh:
        diff_days = (today - latest_gh.date).days
        if diff_days >= 10:
            create_notification_if_not_exists(
                user_id,
                f"Alert: No GitHub contributions logged for {diff_days} days. Push some commits to GitHub!"
            )
    else:
        create_notification_if_not_exists(
            user_id,
            "Notice: You haven't tracked your GitHub progress yet. Log commits and features completed!"
        )

    # 4. Project alerts
    # Get user's active/latest project
    active_project = MonthlyProject.query.filter_by(user_id=user_id).order_by(MonthlyProject.deadline.desc()).first()
    if active_project:
        if active_project.status == 'Not Started':
            create_notification_if_not_exists(
                user_id,
                f"Alert: Your monthly project '{active_project.project_name}' has not been started yet."
            )
        elif active_project.status != 'Completed':
            days_to_deadline = (active_project.deadline - today).days
            if days_to_deadline < 0:
                create_notification_if_not_exists(
                    user_id,
                    f"Warning: Your project '{active_project.project_name}' is OVERDUE by {abs(days_to_deadline)} days!"
                )
            elif days_to_deadline <= 3:
                create_notification_if_not_exists(
                    user_id,
                    f"Alert: Deadline for project '{active_project.project_name}' is approaching in {days_to_deadline} days."
                )
    else:
        create_notification_if_not_exists(
            user_id,
            "Notice: You do not have a monthly project active. Create one to stay on track!"
        )
