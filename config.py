import os

class Config:
    # Secret key for session security and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-placement-tracker-18475'
    
    # Database configuration - defaults to local SQLite file
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    if os.environ.get('VERCEL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            "sqlite:////tmp/placement_tracker.db"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            f"sqlite:///{os.path.join(BASE_DIR, 'database', 'placement_tracker.db')}"
        
    # Silence SQLAlchemy event tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enable automatic template reloading for UI development
    TEMPLATES_AUTO_RELOAD = True
