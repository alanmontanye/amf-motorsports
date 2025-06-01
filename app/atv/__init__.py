from flask import Blueprint

bp = Blueprint('atv', __name__, url_prefix='/atv')

# Import all route modules
from . import routes
from .parts import parts_bp
from .parting import parting_bp
from .parts_bulk import parts_bulk_bp
from .quick_edit import quick_edit_bp
from app.atv import storage, ebay, ebay_settings, ebay_analytics, ebay_api, ebay_routes, ebay_dashboard, ai_description

# Register blueprints
bp.register_blueprint(parts_bp)
bp.register_blueprint(parting_bp)
bp.register_blueprint(parts_bulk_bp)
bp.register_blueprint(quick_edit_bp)
