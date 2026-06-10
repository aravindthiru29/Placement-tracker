from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, FloatField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, URL
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValueError('That email is already registered. Please use a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')


class LeetCodeForm(FlaskForm):
    easy_solved = IntegerField('Easy Problems Solved', validators=[NumberRange(min=0)], default=0)
    medium_solved = IntegerField('Medium Problems Solved', validators=[NumberRange(min=0)], default=0)
    hard_solved = IntegerField('Hard Problems Solved', validators=[NumberRange(min=0)], default=0)
    streak = IntegerField('Current Streak (Days)', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Log LeetCode Progress')


class AptitudeForm(FlaskForm):
    quant_questions = IntegerField('Quantitative Questions Solved', validators=[NumberRange(min=0)], default=0)
    logical_questions = IntegerField('Logical Reasoning Questions Solved', validators=[NumberRange(min=0)], default=0)
    verbal_questions = IntegerField('Verbal Ability Questions Solved', validators=[NumberRange(min=0)], default=0)
    accuracy_percentage = FloatField('Average Accuracy (%)', validators=[NumberRange(min=0, max=100)], default=0.0)
    mock_test_score = FloatField('Latest Mock Test Score (%)', validators=[NumberRange(min=0, max=100)], default=0.0)
    submit = SubmitField('Log Aptitude Progress')


class GitHubForm(FlaskForm):
    commits = IntegerField('Commits Logged', validators=[NumberRange(min=0)], default=0)
    repositories_created = IntegerField('Repositories Created', validators=[NumberRange(min=0)], default=0)
    features_completed = IntegerField('Features/Milestones Completed', validators=[NumberRange(min=0)], default=0)
    pull_requests = IntegerField('Pull Requests Raised', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Log GitHub Progress')


class ProjectForm(FlaskForm):
    project_name = StringField('Project Name', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    github_link = StringField('GitHub Repository Link', validators=[Optional(), URL(message='Please enter a valid URL (starting with http/https)')])
    live_demo_link = StringField('Live Demo Link', validators=[Optional(), URL(message='Please enter a valid URL (starting with http/https)')])
    deadline = DateField('Deadline', validators=[DataRequired()], format='%Y-%m-%d')
    completion_percentage = IntegerField('Completion Percentage (%)', validators=[NumberRange(min=0, max=100)], default=0)
    status = SelectField('Status', choices=[
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Review Pending', 'Review Pending'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Project Details')


class ProjectFeedbackForm(FlaskForm):
    status = SelectField('Review Status', choices=[
        ('Completed', 'Approve & Mark Completed'),
        ('In Progress', 'Request Changes / Reject (Back to In Progress)'),
        ('Review Pending', 'Keep in Pending Review')
    ], validators=[DataRequired()])
    feedback = TextAreaField('Admin Feedback / Comments', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Submit Review')
