from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes
from app.admin import init_routes

# Register the initialization blueprint
from app.admin.init_routes import init_bp
