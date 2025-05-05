from flask import render_template
from app.main import bp
from app.models import ATV, Part
from datetime import datetime, timedelta
from sqlalchemy import func

@bp.route('/')
@bp.route('/index')
def index():
    """Home page with quick stats"""
    # Calculate quick stats
    stats = {
        'active_atvs': ATV.query.filter_by(status='active').count(),
        'parts_in_stock': Part.query.filter_by(status='in_stock').count(),
        'listed_parts': Part.query.filter_by(status='listed').count(),
        'monthly_profit': calculate_monthly_profit()
    }
    return render_template('main/index.html', title='Dashboard', stats=stats)

def calculate_monthly_profit():
    """Calculate total profit for the current month"""
    # Get the first day of the current month
    today = datetime.utcnow()
    first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate profit from ATVs sold this month
    atv_profit = 0
    atvs_sold = ATV.query.filter(
        ATV.status == 'sold',
        ATV.updated_at >= first_day
    ).all()
    for atv in atvs_sold:
        atv_profit += atv.profit_loss()

    # Calculate profit from parts sold this month
    parts_profit = 0
    parts_sold = Part.query.filter(
        Part.status == 'sold',
        Part.sold_date >= first_day
    ).all()
    for part in parts_sold:
        parts_profit += part.net_profit()

    return atv_profit + parts_profit
