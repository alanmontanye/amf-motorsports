from flask import Blueprint

bp = Blueprint('parts', __name__)

from app.parts import routes
