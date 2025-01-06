from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Import routes after app is created to avoid circular imports
    with app.app_context():
        from app import routes
        db.create_all()
    
    return app