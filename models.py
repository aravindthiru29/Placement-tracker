from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member') # 'admin' or 'member'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leetcode_records = db.relationship('LeetCodeProgress', backref='user', lazy=True, cascade="all, delete-orphan")
    aptitude_records = db.relationship('AptitudeProgress', backref='user', lazy=True, cascade="all, delete-orphan")
    github_records = db.relationship('GitHubProgress', backref='user', lazy=True, cascade="all, delete-orphan")
    monthly_projects = db.relationship('MonthlyProject', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class LeetCodeProgress(db.Model):
    __tablename__ = 'leetcode_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    easy_solved = db.Column(db.Integer, nullable=False, default=0)
    medium_solved = db.Column(db.Integer, nullable=False, default=0)
    hard_solved = db.Column(db.Integer, nullable=False, default=0)
    total_solved = db.Column(db.Integer, nullable=False, default=0)
    streak = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f'<LeetCodeProgress User:{self.user_id} Date:{self.date} Total:{self.total_solved}>'


class AptitudeProgress(db.Model):
    __tablename__ = 'aptitude_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    quant_questions = db.Column(db.Integer, nullable=False, default=0)
    logical_questions = db.Column(db.Integer, nullable=False, default=0)
    verbal_questions = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    accuracy_percentage = db.Column(db.Float, nullable=False, default=0.0)
    mock_test_score = db.Column(db.Float, nullable=False, default=0.0)
    
    def __repr__(self):
        return f'<AptitudeProgress User:{self.user_id} Date:{self.date} Total:{self.total_questions}>'


class GitHubProgress(db.Model):
    __tablename__ = 'github_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    commits = db.Column(db.Integer, nullable=False, default=0)
    repositories_created = db.Column(db.Integer, nullable=False, default=0)
    features_completed = db.Column(db.Integer, nullable=False, default=0)
    pull_requests = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f'<GitHubProgress User:{self.user_id} Date:{self.date} Commits:{self.commits}>'


class MonthlyProject(db.Model):
    __tablename__ = 'monthly_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    live_demo_link = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    deadline = db.Column(db.Date, nullable=False)
    completion_percentage = db.Column(db.Integer, nullable=False, default=0) # 0 to 100
    status = db.Column(db.String(30), nullable=False, default='Not Started') # 'Not Started', 'In Progress', 'Review Pending', 'Completed'
    admin_feedback = db.Column(db.Text, nullable=True) # Feedback or reasons for reject/change request
    
    def __repr__(self):
        return f'<MonthlyProject User:{self.user_id} Name:{self.project_name} Status:{self.status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<Notification User:{self.user_id} Msg:{self.message[:20]} Read:{self.is_read}>'
