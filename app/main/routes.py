from flask import render_template
from app.main import bp
from app.models import ATV, Part
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from app import db

def safe_count(sql_query):
    """Safely execute a simple COUNT query with error handling"""
    try:
        # Use text() for raw SQL queries
        result = db.session.execute(text(sql_query)).scalar()
        return result or 0
    except Exception as e:
        print(f"Database query error: {str(e)}")
        return 0

@bp.route('/')
@bp.route('/index')
def index():
    """Home page with basic stats - SIMPLIFIED VERSION"""
    try:
        # Ultra simplified stats - just basic counts with error protection
        stats = {
            'active_atvs': safe_count("SELECT COUNT(*) FROM atv WHERE status = 'active'"),
            'parts_in_stock': safe_count("SELECT COUNT(*) FROM part WHERE status = 'in_stock'"),
            'listed_parts': safe_count("SELECT COUNT(*) FROM part WHERE status = 'listed'"),
            'monthly_profit': 0  # Skip profit calculation for now
        }
    except Exception as e:
        # If anything goes wrong, return empty stats
        print(f"Error generating stats: {str(e)}")
        stats = {
            'active_atvs': 0,
            'parts_in_stock': 0,
            'listed_parts': 0,
            'monthly_profit': 0
        }
    return render_template('main/index.html', title='Dashboard - Simplified', stats=stats)

def get_active_atv_count():
    """Get active ATV count safely"""
    try:
        # Try the model-based approach first (preferred)
        return ATV.query.filter_by(status='active').count()
    except SQLAlchemyError:
        try:
            # Fallback to direct SQL which only uses the columns we know exist
            return db.session.execute(text(
                "SELECT COUNT(*) FROM atv WHERE status = 'active'"
            )).scalar() or 0
        except SQLAlchemyError as e:
            print(f"Error counting active ATVs: {str(e)}")
            return 0

def get_parts_count(status_value):
    """Get parts count safely by status"""
    try:
        # Try the model-based approach first (preferred)
        return Part.query.filter_by(status=status_value).count()
    except SQLAlchemyError:
        try:
            # Fallback to direct SQL
            return db.session.execute(text(
                "SELECT COUNT(*) FROM part WHERE status = :status"
            ), {"status": status_value}).scalar() or 0
        except SQLAlchemyError as e:
            print(f"Error counting parts with status '{status_value}': {str(e)}")
            return 0

def calculate_monthly_profit():
    """Calculate total profit for the current month"""
    try:
        # Get the first day of the current month
        today = datetime.utcnow()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate profit from ATVs sold this month
        atv_profit = 0
        try:
            atvs_sold = ATV.query.filter(
                ATV.status == 'sold',
                ATV.updated_at >= first_day
            ).all()
            for atv in atvs_sold:
                try:
                    atv_profit += atv.profit_loss()
                except (AttributeError, SQLAlchemyError) as e:
                    print(f"Error calculating profit for ATV {atv.id}: {str(e)}")
        except SQLAlchemyError as e:
            print(f"Error querying sold ATVs: {str(e)}")

        # Calculate profit from parts sold this month
        parts_profit = 0
        try:
            parts_sold = Part.query.filter(
                Part.status == 'sold',
                Part.sold_date >= first_day
            ).all()
            for part in parts_sold:
                try:
                    parts_profit += part.net_profit()
                except (AttributeError, SQLAlchemyError) as e:
                    print(f"Error calculating profit for part {part.id}: {str(e)}")
        except SQLAlchemyError as e:
            print(f"Error querying sold parts: {str(e)}")

        return atv_profit + parts_profit
    except Exception as e:
        print(f"Error in calculate_monthly_profit: {str(e)}")
        return 0
