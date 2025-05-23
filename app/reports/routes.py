"""Routes for generating reports"""
from flask import render_template
from app.reports import bp
from app.models import ATV, Part, Expense
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

@bp.route('/reports')
def index():
    """Reports dashboard"""
    return render_template('reports/index.html')

@bp.route('/reports/financial')
def financial():
    """Financial reports"""
    # Overall summary
    total_revenue = db.session.query(func.sum(Part.sold_price)).filter(Part.status == 'sold').scalar() or 0
    total_parts_cost = db.session.query(func.sum(Part.source_price)).filter(Part.status == 'sold').scalar() or 0
    total_shipping = db.session.query(func.sum(Part.shipping_cost)).filter(Part.status == 'sold').scalar() or 0
    total_fees = db.session.query(func.sum(Part.platform_fees)).filter(Part.status == 'sold').scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    
    # Calculate total costs including general expenses
    total_costs = total_parts_cost + total_shipping + total_fees + total_expenses
    total_profit = total_revenue - total_costs

    # Monthly breakdown - more accurate calculation using calendar months
    now = datetime.utcnow()
    months = []
    current_month_data = None  # Store current month data separately
    
    for i in range(6):  # Last 6 months
        # Get first day of the month
        start_date = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get last day of the month more accurately
        if start_date.month == 12:
            end_date = datetime(start_date.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(start_date.year, start_date.month + 1, 1) - timedelta(seconds=1)
        
        # Monthly revenue
        month_revenue = db.session.query(func.sum(Part.sold_price))\
            .filter(Part.status == 'sold')\
            .filter(Part.sold_date.between(start_date, end_date))\
            .scalar() or 0
        
        # Monthly part-specific costs
        month_parts_cost = db.session.query(
            func.sum(Part.source_price + Part.shipping_cost + Part.platform_fees)
        ).filter(Part.status == 'sold')\
         .filter(Part.sold_date.between(start_date, end_date))\
         .scalar() or 0
         
        # Monthly general expenses
        month_expenses = db.session.query(func.sum(Expense.amount))\
            .filter(Expense.date.between(start_date, end_date))\
            .scalar() or 0
            
        # Calculate monthly profit
        month_total_costs = month_parts_cost + month_expenses
        month_profit = month_revenue - month_total_costs
        
        month_data = {
            'month': start_date.strftime('%B %Y'),
            'month_obj': start_date,
            'revenue': month_revenue,
            'parts_cost': month_parts_cost,
            'expenses': month_expenses,
            'total_costs': month_total_costs,
            'profit': month_profit
        }
        
        # Store current month separately for highlighting in the UI
        if i == 0:
            current_month_data = month_data
        
        months.append(month_data)

    # Get expense categories breakdown
    expense_categories = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).group_by(Expense.category).all()

    # Get current month's expense categories breakdown for more detailed view
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_month_start.month == 12:
        current_month_end = datetime(current_month_start.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        current_month_end = datetime(current_month_start.year, current_month_start.month + 1, 1) - timedelta(seconds=1)
        
    current_month_expenses = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(Expense.date.between(current_month_start, current_month_end))\
     .group_by(Expense.category).all()
    
    return render_template('reports/financial.html',
                         total_revenue=total_revenue,
                         total_parts_cost=total_parts_cost,
                         total_shipping=total_shipping,
                         total_fees=total_fees,
                         total_expenses=total_expenses,
                         total_costs=total_costs,
                         total_profit=total_profit,
                         months=months,
                         current_month=current_month_data,
                         today=datetime.utcnow(),
                         current_month_name=datetime.utcnow().strftime('%B %Y'),
                         expense_categories=expense_categories,
                         current_month_expenses=current_month_expenses)

@bp.route('/reports/inventory')
def inventory():
    """Inventory reports"""
    # Overall inventory stats
    total_parts = Part.query.count()
    parts_in_stock = Part.query.filter_by(status='in_stock').count()
    parts_listed = Part.query.filter_by(status='listed').count()
    parts_sold = Part.query.filter_by(status='sold').count()
    
    # Value of current inventory
    inventory_value = db.session.query(func.sum(Part.list_price))\
        .filter(Part.status.in_(['in_stock', 'listed']))\
        .scalar() or 0
    
    # Parts by ATV
    atvs = ATV.query.filter(ATV.status != 'deleted').all()
    atv_stats = []
    for atv in atvs:
        total = atv.parts.count()
        sold = atv.parts.filter_by(status='sold').count()
        if total > 0:
            completion = (sold / total) * 100
        else:
            completion = 0
            
        atv_stats.append({
            'name': f'{atv.year} {atv.make} {atv.model}',
            'total_parts': total,
            'parts_sold': sold,
            'completion': completion,
            'id': atv.id,
            'total_earnings': atv.total_earnings or 0
        })

    return render_template('reports/inventory.html',
                         total_parts=total_parts,
                         parts_in_stock=parts_in_stock,
                         parts_listed=parts_listed,
                         parts_sold=parts_sold,
                         inventory_value=inventory_value,
                         atv_stats=atv_stats)
