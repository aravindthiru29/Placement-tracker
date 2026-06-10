from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from models import db, User, LeetCodeProgress, AptitudeProgress, GitHubProgress, MonthlyProject, Notification
from forms import LeetCodeForm, AptitudeForm, GitHubForm, ProjectForm, ProjectFeedbackForm
from services.scoring import calculate_readiness_score, calculate_leaderboard, get_latest_leetcode, get_latest_aptitude, get_latest_github, get_current_project
from services.alerts import check_and_generate_alerts, create_notification_if_not_exists
from services.reports import compile_report_data, export_report_to_excel, export_report_to_pdf

main_bp = Blueprint('main', __name__)

def get_admin_stats():
    members = User.query.filter_by(role='member').all()
    if not members:
        return {}
        
    leaderboard = calculate_leaderboard()
    top_performer = leaderboard[0]['name'] if leaderboard else 'N/A'
    
    # Most consistent: highest current streak in leetcode
    most_consistent = 'N/A'
    max_streak = -1
    for m in members:
        latest_lc = LeetCodeProgress.query.filter_by(user_id=m.id).order_by(LeetCodeProgress.date.desc()).first()
        if latest_lc and latest_lc.streak > max_streak:
            max_streak = latest_lc.streak
            most_consistent = m.name
            
    # Most improved: difference in leetcode solved in last 14 days
    most_improved = 'N/A'
    max_improvement = -1
    today = date.today()
    two_weeks_ago = today - timedelta(days=14)
    for m in members:
        latest = LeetCodeProgress.query.filter_by(user_id=m.id).order_by(LeetCodeProgress.date.desc()).first()
        old = LeetCodeProgress.query.filter_by(user_id=m.id).filter(LeetCodeProgress.date <= two_weeks_ago).order_by(LeetCodeProgress.date.desc()).first()
        if latest:
            old_solved = old.total_solved if old else 0
            diff = latest.total_solved - old_solved
            if diff > max_improvement:
                max_improvement = diff
                most_improved = m.name
                
    # Lowest activity: member at the bottom of the leaderboard
    lowest_activity = leaderboard[-1]['name'] if leaderboard else 'N/A'
    
    # Active/Inactive members
    active_count = 0
    inactive_count = 0
    seven_days_ago = today - timedelta(days=7)
    for m in members:
        lc = LeetCodeProgress.query.filter_by(user_id=m.id).filter(LeetCodeProgress.date >= seven_days_ago).first()
        apt = AptitudeProgress.query.filter_by(user_id=m.id).filter(AptitudeProgress.date >= seven_days_ago).first()
        gh = GitHubProgress.query.filter_by(user_id=m.id).filter(GitHubProgress.date >= seven_days_ago).first()
        if lc or apt or gh:
            active_count += 1
        else:
            inactive_count += 1
            
    return {
        'total_members': len(members),
        'active_members': active_count,
        'inactive_members': inactive_count,
        'top_performer': top_performer,
        'most_consistent': most_consistent,
        'most_improved': most_improved if max_improvement > 0 else (members[0].name if members else 'N/A'),
        'lowest_activity': lowest_activity
    }

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    
    if current_user.role == 'admin':
        # Admin View
        stats = get_admin_stats()
        pending_projects = MonthlyProject.query.filter_by(status='Review Pending').order_by(MonthlyProject.deadline.asc()).all()
        members = User.query.filter_by(role='member').all()
        
        # Search members
        search_query = request.args.get('search', '')
        if search_query:
            members = User.query.filter(
                (User.role == 'member') & 
                ((User.name.like(f"%{search_query}%")) | (User.email.like(f"%{search_query}%")))
            ).all()
            
        # Compile readiness scores for all filtered members
        member_scores = []
        for m in members:
            member_scores.append({
                'user': m,
                'scores': calculate_readiness_score(m.id)
            })
            
        # Group performance stats for graphs
        # LeetCode average, Aptitude average, GitHub average
        group_lc = 0
        group_apt = 0
        group_gh = 0
        active_projects_count = 0
        completed_projects_count = 0
        
        for m in User.query.filter_by(role='member').all():
            scores = calculate_readiness_score(m.id)
            group_lc += scores['leetcode_total']
            group_apt += scores['aptitude_total']
            group_gh += scores['github_points']
            proj = get_current_project(m.id)
            if proj:
                active_projects_count += 1
                if proj.status == 'Completed':
                    completed_projects_count += 1
                    
        total_members = len(User.query.filter_by(role='member').all()) or 1
        analytics = {
            'avg_leetcode': round(group_lc / total_members, 1),
            'avg_aptitude': round(group_apt / total_members, 1),
            'avg_github': round(group_gh / total_members, 1),
            'project_completion_rate': round((completed_projects_count / active_projects_count) * 100, 1) if active_projects_count else 0.0,
            'active_projects': active_projects_count,
            'completed_projects': completed_projects_count
        }
        feedback_form = ProjectFeedbackForm()
        
        return render_template('dashboard/admin.html', title='Admin Dashboard', stats=stats, pending_projects=pending_projects, member_scores=member_scores, analytics=analytics, search_query=search_query, unread_notifs=unread_notifs, feedback_form=feedback_form)
    
    else:
        # Member View
        # Generate alert notifications automatically on dashboard load
        check_and_generate_alerts(current_user.id)
        # Refresh notifications list
        unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
        
        scores = calculate_readiness_score(current_user.id)
        
        latest_lc = get_latest_leetcode(current_user.id)
        latest_apt = get_latest_aptitude(current_user.id)
        latest_gh = get_latest_github(current_user.id)
        current_proj = get_current_project(current_user.id)
        
        # Rankings details
        leaderboard = calculate_leaderboard()
        user_rank = next((x for x in leaderboard if x['user_id'] == current_user.id), None)
        
        return render_template('dashboard/member.html', title='Dashboard', scores=scores, latest_lc=latest_lc, latest_apt=latest_apt, latest_gh=latest_gh, current_proj=current_proj, user_rank=user_rank, unread_notifs=unread_notifs)

@main_bp.route('/leetcode', methods=['GET', 'POST'])
@login_required
def leetcode():
    if current_user.role == 'admin':
        flash('Admins do not log personal activity.', 'info')
        return redirect(url_for('main.dashboard'))
        
    form = LeetCodeForm()
    today = date.today()
    
    # Find or create today's record
    record = LeetCodeProgress.query.filter_by(user_id=current_user.id, date=today).first()
    
    if form.validate_on_submit():
        if not record:
            record = LeetCodeProgress(user_id=current_user.id, date=today)
            db.session.add(record)
            
        record.easy_solved = form.easy_solved.data
        record.medium_solved = form.medium_solved.data
        record.hard_solved = form.hard_solved.data
        record.total_solved = record.easy_solved + record.medium_solved + record.hard_solved
        record.streak = form.streak.data
        
        db.session.commit()
        flash('LeetCode progress updated successfully!', 'success')
        return redirect(url_for('main.leetcode'))
        
    elif request.method == 'GET' and record:
        form.easy_solved.data = record.easy_solved
        form.medium_solved.data = record.medium_solved
        form.hard_solved.data = record.hard_solved
        form.streak.data = record.streak
        
    # Get user's history (limit to last 30 logs for charts)
    history = LeetCodeProgress.query.filter_by(user_id=current_user.id).order_by(LeetCodeProgress.date.asc()).all()
    
    # Targets (Hardcoded defaults for tracking)
    weekly_target = 10
    monthly_target = 40
    
    latest_lc = get_latest_leetcode(current_user.id)
    best_streak = db.session.query(db.func.max(LeetCodeProgress.streak)).filter_by(user_id=current_user.id).scalar() or 0
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('modules/leetcode.html', title='LeetCode Progress', form=form, history=history, latest=latest_lc, best_streak=best_streak, weekly_target=weekly_target, monthly_target=monthly_target, unread_notifs=unread_notifs)

@main_bp.route('/aptitude', methods=['GET', 'POST'])
@login_required
def aptitude():
    if current_user.role == 'admin':
        flash('Admins do not log personal activity.', 'info')
        return redirect(url_for('main.dashboard'))
        
    form = AptitudeForm()
    today = date.today()
    record = AptitudeProgress.query.filter_by(user_id=current_user.id, date=today).first()
    
    if form.validate_on_submit():
        if not record:
            record = AptitudeProgress(user_id=current_user.id, date=today)
            db.session.add(record)
            
        record.quant_questions = form.quant_questions.data
        record.logical_questions = form.logical_questions.data
        record.verbal_questions = form.verbal_questions.data
        record.total_questions = record.quant_questions + record.logical_questions + record.verbal_questions
        record.accuracy_percentage = form.accuracy_percentage.data
        record.mock_test_score = form.mock_test_score.data
        
        db.session.commit()
        flash('Aptitude progress updated successfully!', 'success')
        return redirect(url_for('main.aptitude'))
        
    elif request.method == 'GET' and record:
        form.quant_questions.data = record.quant_questions
        form.logical_questions.data = record.logical_questions
        form.verbal_questions.data = record.verbal_questions
        form.accuracy_percentage.data = record.accuracy_percentage
        form.mock_test_score.data = record.mock_test_score
        
    history = AptitudeProgress.query.filter_by(user_id=current_user.id).order_by(AptitudeProgress.date.asc()).all()
    latest = get_latest_aptitude(current_user.id)
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('modules/aptitude.html', title='Aptitude Preparation', form=form, history=history, latest=latest, unread_notifs=unread_notifs)

@main_bp.route('/github', methods=['GET', 'POST'])
@login_required
def github():
    if current_user.role == 'admin':
        flash('Admins do not log personal activity.', 'info')
        return redirect(url_for('main.dashboard'))
        
    form = GitHubForm()
    today = date.today()
    record = GitHubProgress.query.filter_by(user_id=current_user.id, date=today).first()
    
    if form.validate_on_submit():
        if not record:
            record = GitHubProgress(user_id=current_user.id, date=today)
            db.session.add(record)
            
        record.commits = form.commits.data
        record.repositories_created = form.repositories_created.data
        record.features_completed = form.features_completed.data
        record.pull_requests = form.pull_requests.data
        
        db.session.commit()
        flash('GitHub contributions updated successfully!', 'success')
        return redirect(url_for('main.github'))
        
    elif request.method == 'GET' and record:
        form.commits.data = record.commits
        form.repositories_created.data = record.repositories_created
        form.features_completed.data = record.features_completed
        form.pull_requests.data = record.pull_requests
        
    history = GitHubProgress.query.filter_by(user_id=current_user.id).order_by(GitHubProgress.date.asc()).all()
    latest = get_latest_github(current_user.id)
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('modules/github.html', title='GitHub Progress', form=form, history=history, latest=latest, unread_notifs=unread_notifs)

@main_bp.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    if current_user.role == 'admin':
        # Admin: view all members' projects
        status_filter = request.args.get('status', 'All')
        query = MonthlyProject.query
        if status_filter != 'All':
            query = query.filter_by(status=status_filter)
        projects_list = query.order_by(MonthlyProject.deadline.asc()).all()
        
        # Project feedback form
        feedback_form = ProjectFeedbackForm()
        return render_template('modules/admin_projects.html', title='Manage Group Projects', projects=projects_list, feedback_form=feedback_form, status_filter=status_filter, unread_notifs=unread_notifs)
    
    else:
        # Member: view their own projects
        my_projects = MonthlyProject.query.filter_by(user_id=current_user.id).order_by(MonthlyProject.deadline.desc()).all()
        
        # Log a new project or edit active one
        active_proj = get_current_project(current_user.id)
        
        form = ProjectForm()
        
        # If user edits the current project
        action = request.args.get('action', 'new')
        proj_id = request.args.get('proj_id')
        
        editing_proj = None
        if action == 'edit' and proj_id:
            editing_proj = MonthlyProject.query.filter_by(id=proj_id, user_id=current_user.id).first_or_404()
            
        if form.validate_on_submit():
            if action == 'edit' and editing_proj:
                editing_proj.project_name = form.project_name.data
                editing_proj.description = form.description.data
                editing_proj.github_link = form.github_link.data
                editing_proj.live_demo_link = form.live_demo_link.data
                editing_proj.deadline = form.deadline.data
                editing_proj.completion_percentage = form.completion_percentage.data
                editing_proj.status = form.status.data
                
                # If they set status to completed, set it to review pending first so admin approves!
                if editing_proj.status == 'Completed':
                    editing_proj.status = 'Review Pending'
                    flash('Project submitted for Review. Admin approval pending!', 'info')
                else:
                    flash('Project updated successfully!', 'success')
            else:
                # Create new project
                new_status = form.status.data
                if new_status == 'Completed':
                    new_status = 'Review Pending'
                    
                proj = MonthlyProject(
                    user_id=current_user.id,
                    project_name=form.project_name.data,
                    description=form.description.data,
                    github_link=form.github_link.data,
                    live_demo_link=form.live_demo_link.data,
                    start_date=date.today(),
                    deadline=form.deadline.data,
                    completion_percentage=form.completion_percentage.data,
                    status=new_status
                )
                db.session.add(proj)
                if new_status == 'Review Pending':
                    flash('Project created and submitted for review!', 'info')
                else:
                    flash('New project added successfully!', 'success')
                    
            db.session.commit()
            return redirect(url_for('main.projects'))
            
        elif request.method == 'GET':
            if action == 'edit' and editing_proj:
                form.project_name.data = editing_proj.project_name
                form.description.data = editing_proj.description
                form.github_link.data = editing_proj.github_link
                form.live_demo_link.data = editing_proj.live_demo_link
                form.deadline.data = editing_proj.deadline
                form.completion_percentage.data = editing_proj.completion_percentage
                form.status.data = editing_proj.status
            else:
                form.deadline.data = date.today() + timedelta(days=30)
                
        return render_template('modules/member_projects.html', title='My Monthly Projects', form=form, projects=my_projects, active_proj=active_proj, action=action, editing_proj=editing_proj, unread_notifs=unread_notifs)

@main_bp.route('/project/review/<int:project_id>', methods=['POST'])
@login_required
def review_project(project_id):
    if current_user.role != 'admin':
        abort(403)
        
    project = MonthlyProject.query.get_or_404(project_id)
    form = ProjectFeedbackForm()
    
    if form.validate_on_submit():
        old_status = project.status
        project.status = form.status.data
        project.admin_feedback = form.feedback.data
        
        # Trigger appropriate notifications based on approval
        status_text = ""
        if project.status == 'Completed':
            project.completion_percentage = 100
            status_text = "APPROVED & COMPLETED"
            flash(f"Project '{project.project_name}' has been approved and marked Completed!", "success")
        elif project.status == 'In Progress':
            status_text = "REJECTED (Changes Requested)"
            project.completion_percentage = 80
            flash(f"Project '{project.project_name}' feedback sent. Status set to In Progress.", "warning")
        else:
            status_text = "KEPT IN REVIEW"
            flash(f"Project review updated.", "info")
            
        # Create a notification for the user
        msg = f"Admin feedback on project '{project.project_name}': {status_text}. Reason: {project.admin_feedback}"
        notif = Notification(user_id=project.user_id, message=msg)
        db.session.add(notif)
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Review validation error in '{field}': {error}", "danger")
        
    next_page = request.referrer or url_for('main.dashboard')
    return redirect(next_page)

@main_bp.route('/leaderboard')
@login_required
def leaderboard():
    leaderboard_data = calculate_leaderboard()
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    return render_template('leaderboard/view.html', title='Leaderboard', leaderboard=leaderboard_data, unread_notifs=unread_notifs)

@main_bp.route('/reports')
@login_required
def reports():
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    report_type = request.args.get('type', 'group' if current_user.role == 'admin' else 'member')
    days = int(request.args.get('days', '7'))
    
    # For filters
    members = User.query.filter_by(role='member').all()
    selected_member_id = request.args.get('member_id', current_user.id if current_user.role == 'member' else '')
    
    if current_user.role == 'member':
        selected_member_id = current_user.id
        if report_type == 'group':
            report_type = 'member'
            
    # Compile the preview data
    target_user_id = int(selected_member_id) if selected_member_id else None
    report_data = compile_report_data(report_type, user_id=target_user_id, days=days)
    
    return render_template('reports/view.html', title='Performance Reports', report_data=report_data, report_type=report_type, days=days, members=members, selected_member_id=selected_member_id, unread_notifs=unread_notifs)

@main_bp.route('/reports/export/<string:file_format>')
@login_required
def export_report(file_format):
    report_type = request.args.get('type', 'group' if current_user.role == 'admin' else 'member')
    days = int(request.args.get('days', '7'))
    selected_member_id = request.args.get('member_id', current_user.id if current_user.role == 'member' else '')
    
    if current_user.role == 'member':
        selected_member_id = current_user.id
        if report_type == 'group':
            report_type = 'member'
            
    target_user_id = int(selected_member_id) if selected_member_id else None
    report_data = compile_report_data(report_type, user_id=target_user_id, days=days)
    
    if not report_data:
        flash('Could not generate report data.', 'danger')
        return redirect(url_for('main.reports'))
        
    filename = f"placement_report_{report_type}_{date.today().strftime('%Y%m%d')}"
    
    if file_format == 'excel':
        buffer = export_report_to_excel(report_data)
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename}.xlsx"
        )
    elif file_format == 'pdf':
        buffer = export_report_to_pdf(report_data)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{filename}.pdf"
        )
    else:
        abort(400)

@main_bp.route('/notifications')
@login_required
def notifications():
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    all_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications/view.html', title='Notifications Center', all_notifications=all_notifs, unread_notifs=unread_notifs)

@main_bp.route('/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('main.notifications'))

@main_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('main.notifications'))

@main_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    flash('Notification deleted.', 'success')
    return redirect(url_for('main.notifications'))

@main_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
        
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("You cannot delete your own administrator account.", "danger")
        return redirect(url_for('main.dashboard'))
        
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User '{user.name}' has been successfully deleted from the system.", "success")
    return redirect(url_for('main.dashboard'))
