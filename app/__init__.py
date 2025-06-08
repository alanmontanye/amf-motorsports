from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()
migrate = Migrate()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema(app):
    """Add missing columns to database tables if they don't exist"""
    logger.info("Checking database schema for missing columns...")
    try:
        with app.app_context():
            # Get database inspector
            inspector = inspect(db.engine)
            
            # Check if atv table exists
            if 'atv' not in inspector.get_table_names():
                logger.warning("'atv' table not found! Creating all tables...")
                db.create_all()
                logger.info("Tables created successfully")
                return
            
            # Each operation in a separate transaction for better reliability
            # 1. Add missing columns to ATV table
            with db.engine.begin() as connection:
                # Check atv table columns
                columns = [column['name'] for column in inspector.get_columns('atv')]
                logger.info(f"Found columns in atv table: {', '.join(columns)}")
                
                # Define required columns and their SQL definitions
                required_columns = {
                    'status': "VARCHAR(20) DEFAULT 'active'",
                    'parting_status': "VARCHAR(20) DEFAULT 'whole'",
                    'machine_id': "VARCHAR(64)"
                }
                
                # Add any missing columns
                for column, definition in required_columns.items():
                    if column not in columns:
                        try:
                            logger.info(f"Adding missing column '{column}' to atv table")
                            connection.execute(text(f"ALTER TABLE atv ADD COLUMN IF NOT EXISTS {column} {definition}"))
                            logger.info(f"Added '{column}' successfully")
                        except Exception as e:
                            logger.error(f"Error adding column '{column}': {str(e)}")
            
            # 2. Update NULL statuses in a separate transaction
            with db.engine.begin() as connection:
                try:
                    result = connection.execute(text("UPDATE atv SET status = 'active' WHERE status IS NULL"))
                    logger.info(f"Updated {result.rowcount} ATVs with NULL status to 'active'")
                except Exception as e:
                    logger.error(f"Error updating NULL statuses: {str(e)}")
                    
            # 3. Check part table in a separate transaction
            if 'part' in inspector.get_table_names():
                with db.engine.begin() as connection:
                    part_columns = [column['name'] for column in inspector.get_columns('part')]
                    if 'condition' not in part_columns:
                        logger.info("Adding 'condition' column to part table")
                        try:
                            connection.execute(text("ALTER TABLE part ADD COLUMN IF NOT EXISTS condition VARCHAR(20)"))
                            logger.info("Added 'condition' column to part table successfully")
                        except Exception as e:
                            logger.error(f"Error adding 'condition' to part table: {str(e)}")
            
            logger.info("Database schema check and fix completed successfully")
    except Exception as e:
        logger.error(f"Unexpected error during schema fix: {str(e)}")

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
        logger.info("Initializing database schema...")
        db.create_all()
        fix_database_schema(app)
        logger.info("Database initialization complete")
    
    # Add a global template context processor for date/time
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    return app
