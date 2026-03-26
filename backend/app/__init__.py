"""Flask application factory for VoiceNote."""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from config import config_by_name

db = SQLAlchemy()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    logger = logging.getLogger('voicenote')
    logger.info(f"VoiceNote app created with '{config_name}' config")

    # Register blueprints
    from app.routes.notes import notes_bp
    from app.routes.reminders import reminders_bp
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(reminders_bp, url_prefix='/reminders')

    # Create database tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    # Initialize scheduler (after tables exist)
    from app.services.scheduler import init_scheduler
    if not app.config.get('TESTING'):
        init_scheduler(app)

    return app
