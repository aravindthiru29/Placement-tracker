import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User, LeetCodeProgress, AptitudeProgress, GitHubProgress, MonthlyProject, Notification
from datetime import date, datetime, timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Database
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    
    # Context Processor to expose datetime/date in templates
    @app.context_processor
    def inject_datetime():
        return {'datetime': datetime, 'date': date}
        
    # Global Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
        
    # Database initialization and seeding
    with app.app_context():
        # Ensure database directory exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI']
        if db_path.startswith('sqlite:///'):
            dir_path = os.path.dirname(db_path.split('sqlite:///')[1])
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                
        db.create_all()
        seed_database()
        
    return app

def seed_database():
    """
    Seeds a default administrator, two members, and historical progress logs.
    """
    # Check if database is already seeded
    if User.query.first():
        return
        
    print("Seeding database with demo records...")
    
    # 1. Create Users
    admin = User(name="Alex Admin", email="admin@tracker.com", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    
    m1 = User(name="Sam Coder", email="member@tracker.com", role="member")
    m1.set_password("member123")
    db.session.add(m1)
    
    m2 = User(name="Jordan Dev", email="jordan@tracker.com", role="member")
    m2.set_password("member123")
    db.session.add(m2)
    
    db.session.commit() # Commit users first so we have IDs
    
    # 2. Seed Progress Logs for Sam Coder (m1)
    today = date.today()
    for i in range(15, -1, -1):
        log_date = today - timedelta(days=i)
        
        # LeetCode Log
        lc = LeetCodeProgress(
            user_id=m1.id,
            date=log_date,
            easy_solved=15 + (15-i)*2,
            medium_solved=8 + (15-i),
            hard_solved=2 + (15-i)//3,
            streak=15-i if (15-i) > 0 else 1
        )
        lc.total_solved = lc.easy_solved + lc.medium_solved + lc.hard_solved
        db.session.add(lc)
        
        # Aptitude Log
        apt = AptitudeProgress(
            user_id=m1.id,
            date=log_date,
            quant_questions=20 + (15-i)*4,
            logical_questions=15 + (15-i)*3,
            verbal_questions=10 + (15-i)*2,
            accuracy_percentage=72.0 + (15-i)*0.8,
            mock_test_score=68.0 + (15-i)*1.2
        )
        apt.total_questions = apt.quant_questions + apt.logical_questions + apt.verbal_questions
        db.session.add(apt)
        
        # GitHub Log
        gh = GitHubProgress(
            user_id=m1.id,
            date=log_date,
            commits=25 + (15-i)*3,
            repositories_created=1 + (15-i)//7,
            features_completed=1 + (15-i)//4,
            pull_requests=2 + (15-i)//5
        )
        db.session.add(gh)

    # 3. Seed Progress Logs for Jordan Dev (m2) - slightly lower stats
    for i in range(15, -1, -1):
        log_date = today - timedelta(days=i)
        
        # LeetCode Log
        lc = LeetCodeProgress(
            user_id=m2.id,
            date=log_date,
            easy_solved=10 + (15-i),
            medium_solved=4 + (15-i)//2,
            hard_solved=1 + (15-i)//5,
            streak=min(12, 15-i) if (15-i) > 0 else 1 # Jordan broke their streak 3 days ago
        )
        lc.total_solved = lc.easy_solved + lc.medium_solved + lc.hard_solved
        db.session.add(lc)
        
        # Aptitude Log
        apt = AptitudeProgress(
            user_id=m2.id,
            date=log_date,
            quant_questions=12 + (15-i)*3,
            logical_questions=10 + (15-i)*2,
            verbal_questions=8 + (15-i),
            accuracy_percentage=65.0 + (15-i)*0.5,
            mock_test_score=60.0 + (15-i)*1.0
        )
        apt.total_questions = apt.quant_questions + apt.logical_questions + apt.verbal_questions
        db.session.add(apt)
        
        # GitHub Log
        gh = GitHubProgress(
            user_id=m2.id,
            date=log_date,
            commits=15 + (15-i)*2,
            repositories_created=1,
            features_completed=(15-i)//5,
            pull_requests=(15-i)//6
        )
        db.session.add(gh)

    # 4. Seed Monthly Projects
    p1 = MonthlyProject(
        user_id=m1.id,
        project_name="Placement Progress Tracker",
        description="A comprehensive SaaS application with Bootstrap 5 design and Chart.js dashboards for tracking member milestones.",
        github_link="https://github.com/samcoder/placement-tracker",
        live_demo_link="https://placement-tracker-demo.herokuapp.com",
        start_date=today - timedelta(days=20),
        deadline=today + timedelta(days=10),
        completion_percentage=75,
        status="In Progress"
    )
    db.session.add(p1)
    
    p2 = MonthlyProject(
        user_id=m2.id,
        project_name="Fake Project Detector",
        description="An AI-driven repository audit tool to evaluate code complexity and flag structural red flags.",
        github_link="https://github.com/jordandev/repo-auditor",
        live_demo_link="https://repo-auditor-demo.herokuapp.com",
        start_date=today - timedelta(days=25),
        deadline=today + timedelta(days=5),
        completion_percentage=90,
        status="Review Pending"
    )
    db.session.add(p2)
    
    # 5. Seed initial notifications
    n1 = Notification(
        user_id=m1.id,
        message="Notice: Your monthly project 'Placement Progress Tracker' is due in 10 days. Keep building!"
    )
    db.session.add(n1)
    
    n2 = Notification(
        user_id=m2.id,
        message="Notice: Your monthly project 'Fake Project Detector' is due in 5 days. Submit for review when done."
    )
    db.session.add(n2)
    
    db.session.commit()
    print("Database seeding completed.")

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
