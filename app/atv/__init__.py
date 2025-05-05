from flask import Blueprint

bp = Blueprint('atv', __name__, url_prefix='/atv')

from app.atv import routes, parts, storage, ebay, ebay_settings, ebay_analytics, ebay_api
