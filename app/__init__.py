from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Determine configuration to use
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.atv import bp as atv_bp
    app.register_blueprint(atv_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    # Register the initialization blueprint
    from app.admin.init_routes import init_bp
    app.register_blueprint(init_bp, url_prefix='/admin')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp)

    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Create specific folders for uploads
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'atv'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'part'), exist_ok=True)

    # Set up error logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AMF Motorsports startup')
    else:
        # Also log in debug mode, but to console
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.debug('Debug mode enabled')

    # Import models before creating tables
    from app import models

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add a global template context processor for date/time
        @app.context_processor
        def inject_now():
            from datetime import datetime
            return {'now': datetime.utcnow()}

    return app
