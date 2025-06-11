from flask import Blueprint

bp = Blueprint('atv', __name__, url_prefix='/atv')

# Import core route modules only
from . import routes
from . import parts
from .parting import parting_bp
from .parts_bulk import parts_bulk_bp
from .quick_edit import quick_edit_bp
from . import storage

# eBay-related modules have been removed to simplify the application

# Register blueprints
bp.register_blueprint(parting_bp)
bp.register_blueprint(parts_bulk_bp)
bp.register_blueprint(quick_edit_bp)
