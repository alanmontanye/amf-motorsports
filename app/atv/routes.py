from flask import render_template, redirect, url_for, request, send_file, current_app, flash
from app.atv import bp
from app.models import ATV, Part, Expense, Sale, Image
from app import db
from app.atv.forms import ATVForm, PartForm, ExpenseForm, SaleForm, ImageUploadForm
from datetime import datetime, timedelta, date, time
import os
from werkzeug.utils import secure_filename
import csv
from io import StringIO, BytesIO
from sqlalchemy import func
import uuid

@bp.route('/')
def index():
    atvs = ATV.query.filter(ATV.status != 'deleted').order_by(ATV.created_at.desc()).all()
    return render_template('atv/index.html', title='ATVs', atvs=atvs)

@bp.route('/add', methods=['GET', 'POST'])
def add_atv():
    form = ATVForm()
    if form.validate_on_submit():
        atv = ATV(
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            vin=form.vin.data,
            status=form.status.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            purchase_location=form.purchase_location.data,
            description=form.description.data,
            acquisition_hours=form.acquisition_hours.data or 0,
            repair_hours=form.repair_hours.data or 0,
            selling_hours=form.selling_hours.data or 0
        )
        
        # Calculate total hours
        atv.update_total_hours()
            
        db.session.add(atv)
        db.session.commit()
        flash(f'ATV added successfully!', 'success')
        return redirect(url_for('atv.view_atv', id=atv.id))
    return render_template('atv/edit.html', title='Add ATV', form=form)

@bp.route('/<int:id>')
def view_atv(id):
    atv = ATV.query.get_or_404(id)
    return render_template('atv/view.html', title=f'{atv.year} {atv.make} {atv.model}', atv=atv)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_atv(id):
    atv = ATV.query.get_or_404(id)
    form = ATVForm(obj=atv)
    
    if form.validate_on_submit():
        atv.make = form.make.data
        atv.model = form.model.data
        atv.year = form.year.data
        atv.vin = form.vin.data
        atv.status = form.status.data
        atv.purchase_date = form.purchase_date.data
        atv.purchase_price = form.purchase_price.data
        atv.purchase_location = form.purchase_location.data
        atv.description = form.description.data
        atv.acquisition_hours = form.acquisition_hours.data or 0
        atv.repair_hours = form.repair_hours.data or 0
        atv.selling_hours = form.selling_hours.data or 0
        
        # Calculate total hours
        atv.update_total_hours()
        
        db.session.commit()
        flash('ATV updated successfully!', 'success')
        return redirect(url_for('atv.view_atv', id=atv.id))
        
    return render_template('atv/edit.html', title='Edit ATV', form=form, atv=atv)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete_atv(id):
    atv = ATV.query.get_or_404(id)
    db.session.delete(atv)
    db.session.commit()
    return redirect(url_for('atv.index'))

# Expense routes
@bp.route('/<int:atv_id>/add-expense', methods=['GET', 'POST'])
def add_expense(atv_id):
    from app.atv.forms import ExpenseForm
    atv = ATV.query.get_or_404(atv_id)
    form = ExpenseForm()
    
    if form.validate_on_submit():
        from app.models import Expense
        expense = Expense(
            date=form.date.data,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data,
            atv=atv
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('atv.view_atv', id=atv_id))
    
    return render_template('atv/expense_form.html', title='Add Expense', form=form, atv=atv)

@bp.route('/expense/<int:id>/edit', methods=['GET', 'POST'])
def edit_expense(id):
    from app.atv.forms import ExpenseForm
    from app.models import Expense
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)
    
    if form.validate_on_submit():
        expense.date = form.date.data
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.description = form.description.data
        db.session.commit()
        return redirect(url_for('atv.view_atv', id=expense.atv_id))
    
    return render_template('atv/expense_form.html', title='Edit Expense', form=form, expense=expense)

@bp.route('/expense/<int:id>/delete', methods=['POST'])
def delete_expense(id):
    from app.models import Expense
    expense = Expense.query.get_or_404(id)
    atv_id = expense.atv_id
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('atv.view_atv', id=atv_id))

# Sale routes
@bp.route('/<int:atv_id>/add-sale', methods=['GET', 'POST'])
def add_sale(atv_id):
    from app.atv.forms import SaleForm
    atv = ATV.query.get_or_404(atv_id)
    form = SaleForm()
    
    if form.validate_on_submit():
        from app.models import Sale
        sale = Sale(
            date=form.date.data,
            amount=form.amount.data,
            platform=form.platform.data,
            fees=form.fees.data,
            shipping_cost=form.shipping_cost.data,
            type=form.type.data,
            description=form.description.data,
            atv=atv
        )
        sale.calculate_net()
        db.session.add(sale)
        db.session.commit()
        return redirect(url_for('atv.view_atv', id=atv_id))
    
    return render_template('atv/sale_form.html', title='Add Sale', form=form, atv=atv)

@bp.route('/sale/<int:id>/edit', methods=['GET', 'POST'])
def edit_sale(id):
    from app.atv.forms import SaleForm
    from app.models import Sale
    sale = Sale.query.get_or_404(id)
    form = SaleForm(obj=sale)
    
    if form.validate_on_submit():
        sale.date = form.date.data
        sale.amount = form.amount.data
        sale.platform = form.platform.data
        sale.fees = form.fees.data
        sale.shipping_cost = form.shipping_cost.data
        sale.type = form.type.data
        sale.description = form.description.data
        sale.calculate_net()
        db.session.commit()
        return redirect(url_for('atv.view_atv', id=sale.atv_id))
    
    return render_template('atv/sale_form.html', title='Edit Sale', form=form, sale=sale)

@bp.route('/sale/<int:id>/delete', methods=['POST'])
def delete_sale(id):
    from app.models import Sale
    sale = Sale.query.get_or_404(id)
    atv_id = sale.atv_id
    db.session.delete(sale)
    db.session.commit()
    return redirect(url_for('atv.view_atv', id=atv_id))

# Reports route
@bp.route('/reports')
def reports():
    """Show financial reports and logs"""
    # Get date range from request args or default to current month
    today = datetime.utcnow()
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    if not start_date:
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

    if not end_date:
        end_date = today
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)

    # Calculate summary statistics
    atv_sales = db.session.query(
        func.count(Sale.id).label('count'),
        func.sum(Sale.amount).label('revenue'),
        func.sum(Sale.net_amount).label('profit')
    ).join(ATV).filter(
        Sale.type == 'full_atv',
        Sale.date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).first()

    part_sales = db.session.query(
        func.count(Part.id).label('count'),
        func.sum(Part.sold_price).label('revenue'),
        func.sum(Part.sold_price - Part.source_price - Part.shipping_cost - Part.platform_fees).label('profit')
    ).join(ATV).filter(
        Part.status == 'sold',
        Part.sold_date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).first()

    # Get ATV purchase costs within the date range
    atv_purchases = db.session.query(
        func.count(ATV.id).label('count'),
        func.sum(ATV.purchase_price).label('total')
    ).filter(
        ATV.purchase_date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).first()

    # Get regular expenses
    expenses = db.session.query(
        Expense.category,
        func.count(Expense.id).label('count'),
        func.sum(Expense.amount).label('total')
    ).join(ATV).filter(
        Expense.date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).group_by(Expense.category).all()

    # Add ATV purchases as a special expense category
    expenses_by_category = [
        {'name': e.category, 'count': e.count, 'total': e.total}
        for e in expenses
    ]
    expenses_by_category.append({
        'name': 'ATV Purchases',
        'count': atv_purchases.count or 0,
        'total': atv_purchases.total or 0
    })

    # Calculate totals
    total_revenue = (atv_sales.revenue or 0) + (part_sales.revenue or 0)
    total_profit = (atv_sales.profit or 0) + (part_sales.profit or 0)
    regular_expenses = sum(e.total or 0 for e in expenses)
    
    # For financial summary, we shouldn't count ATV purchases as direct expenses 
    # against revenue when we're already counting the part profits
    # since the ATV cost is reflected in the part costs
    total_expenses = regular_expenses
    
    # Net profit is the profit from sales minus only the non-purchase expenses
    net_profit = total_profit - regular_expenses
    
    try:
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    except (TypeError, ZeroDivisionError):
        profit_margin = 0

    summary = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'atv_sales': {
            'count': atv_sales.count or 0,
            'revenue': atv_sales.revenue or 0,
            'profit': atv_sales.profit or 0
        },
        'part_sales': {
            'count': part_sales.count or 0,
            'revenue': part_sales.revenue or 0,
            'profit': part_sales.profit or 0
        },
        'expenses_by_category': expenses_by_category
    }

    # Get recent transactions
    transactions = []
    
    # Add sales
    sales = Sale.query.join(ATV).filter(
        Sale.date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).all()
    for sale in sales:
        transactions.append({
            'date': sale.date,
            'type': 'Sale',
            'description': f"{'ATV' if sale.type == 'full_atv' else 'Part'} Sale - {sale.description or ''}",
            'amount': sale.amount,
            'net': sale.net_amount
        })
    
    # Add regular expenses
    expenses = Expense.query.join(ATV).filter(
        Expense.date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).all()
    for expense in expenses:
        transactions.append({
            'date': expense.date,
            'type': 'Expense',
            'description': f"{expense.category.title()} - {expense.description or ''}",
            'amount': expense.amount,
            'net': -expense.amount
        })

    # Add ATV purchases as transactions
    atv_purchases = ATV.query.filter(
        ATV.purchase_date.between(start_date, end_date),
        ATV.status != 'deleted'
    ).all()
    for atv in atv_purchases:
        transactions.append({
            'date': atv.purchase_date,
            'type': 'Expense',
            'description': f"ATV Purchase - {atv.year} {atv.make} {atv.model}",
            'amount': atv.purchase_price,
            'net': -atv.purchase_price
        })

    # Sort transactions by date - convert all dates to datetime objects for consistent comparison
    def get_sort_date(transaction):
        date_val = transaction['date']
        # If it's a date (not datetime), convert to datetime for consistent comparison
        if isinstance(date_val, date) and not isinstance(date_val, datetime):
            return datetime.combine(date_val, time.min)
        return date_val
        
    transactions.sort(key=get_sort_date, reverse=True)

    return render_template('atv/reports.html', 
                         title='Reports & Logs',
                         summary=summary,
                         transactions=transactions)

@bp.route('/export/<data_type>')
def export_data(data_type):
    """Export data as CSV"""
    if data_type not in ['atvs', 'parts', 'expenses', 'sales']:
        return redirect(url_for('atv.reports'))

    # Create a string buffer for the CSV data
    output = StringIO()
    writer = csv.writer(output)

    if data_type == 'atvs':
        # Write ATV data
        writer.writerow(['ID', 'Make', 'Model', 'Year', 'VIN', 'Status', 'Purchase Date',
                        'Purchase Price', 'Purchase Location', 'Description', 'Total Earnings'])
        atvs = ATV.query.filter(ATV.status != 'deleted').all()
        for atv in atvs:
            writer.writerow([
                atv.id, atv.make, atv.model, atv.year, atv.vin, atv.status,
                atv.purchase_date.strftime('%Y-%m-%d') if atv.purchase_date else '',
                atv.purchase_price, atv.purchase_location, atv.description, atv.total_earnings
            ])
    elif data_type == 'parts':
        # Write Parts data
        writer.writerow(['ID', 'ATV', 'Name', 'Part Number', 'Condition', 'Location',
                        'Status', 'Source Price', 'List Price', 'Sold Price',
                        'Sold Date', 'Platform', 'Listing URL', 'Description'])
        parts = Part.query.join(ATV).filter(ATV.status != 'deleted').all()
        for part in parts:
            writer.writerow([
                part.id, f"{part.atv.year} {part.atv.make} {part.atv.model}",
                part.name, part.part_number, part.condition, part.location,
                part.status, part.source_price, part.list_price, part.sold_price,
                part.sold_date.strftime('%Y-%m-%d') if part.sold_date else '',
                part.platform, part.listing_url, part.description
            ])
    elif data_type == 'expenses':
        # Write Expenses data
        writer.writerow(['ID', 'ATV', 'Date', 'Category', 'Amount', 'Description'])
        expenses = Expense.query.join(ATV).filter(ATV.status != 'deleted').all()
        for expense in expenses:
            writer.writerow([
                expense.id, f"{expense.atv.year} {expense.atv.make} {expense.atv.model}",
                expense.date.strftime('%Y-%m-%d'), expense.category,
                expense.amount, expense.description
            ])
    elif data_type == 'sales':
        # Write Sales data
        writer.writerow(['ID', 'ATV', 'Date', 'Type', 'Platform', 'Amount',
                        'Fees', 'Shipping', 'Net Amount', 'Description'])
        sales = Sale.query.join(ATV).filter(ATV.status != 'deleted').all()
        for sale in sales:
            writer.writerow([
                sale.id, f"{sale.atv.year} {sale.atv.make} {sale.atv.model}",
                sale.date.strftime('%Y-%m-%d'), sale.type, sale.platform,
                sale.amount, sale.fees, sale.shipping_cost, sale.net_amount,
                sale.description
            ])

    # Create the response
    output.seek(0)
    output_str = output.getvalue()
    
    # Convert to BytesIO for send_file
    bytes_output = BytesIO(output_str.encode('utf-8'))
    
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{data_type}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

def save_image(file, parent_type="atv", parent_id=None, image_type="general", description=""):
    """Save an uploaded image file and create database record"""
    # Generate a unique filename
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Create upload directory if it doesn't exist
    uploads_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], parent_type, str(parent_id))
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(uploads_dir, unique_filename)
    file.save(file_path)
    
    # Create database record
    image = Image(
        filename=unique_filename,
        description=description,
        image_type=image_type
    )
    
    # Associate with either ATV or Part
    if parent_type == 'atv':
        image.atv_id = parent_id
    elif parent_type == 'part':
        image.part_id = parent_id
        
    db.session.add(image)
    db.session.commit()
    
    return image

@bp.route('/<int:id>/images', methods=['GET', 'POST'])
def atv_images(id):
    """View and manage images for an ATV"""
    atv = ATV.query.get_or_404(id)
    form = ImageUploadForm()
    
    if form.validate_on_submit():
        # Handle image upload
        save_image(
            file=form.image.data,
            parent_type="atv",
            parent_id=id,
            image_type=form.image_type.data,
            description=form.description.data
        )
        flash('Image uploaded successfully.', 'success')
        return redirect(url_for('atv.atv_images', id=id))
    
    # Group images by type
    image_groups = {}
    all_images = atv.images.all()
    for image in all_images:
        if image.image_type not in image_groups:
            image_groups[image.image_type] = []
        image_groups[image.image_type].append(image)
    
    return render_template(
        'atv/images.html', 
        title=f'Images for {atv.year} {atv.make} {atv.model}', 
        atv=atv, 
        form=form,
        image_groups=image_groups
    )

@bp.route('/image/<int:id>')
def view_image(id):
    """View a single image"""
    image = Image.query.get_or_404(id)
    
    # Determine the parent object
    parent = None
    if image.atv_id:
        parent = ATV.query.get(image.atv_id)
        parent_type = 'atv'
    elif image.part_id:
        parent = Part.query.get(image.part_id)
        parent_type = 'part'
    
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], parent_type, str(parent.id), image.filename)
    
    return send_file(image_path)

@bp.route('/image/<int:id>/delete', methods=['POST'])
def delete_image(id):
    """Delete an image"""
    image = Image.query.get_or_404(id)
    
    # Determine the parent
    if image.atv_id:
        parent_id = image.atv_id
        parent_type = 'atv'
        redirect_url = url_for('atv.atv_images', id=parent_id)
    elif image.part_id:
        parent_id = image.part_id
        parent_type = 'part'
        redirect_url = url_for('atv.part_detail', id=parent_id)
    else:
        flash('Image not associated with any object.', 'error')
        return redirect(url_for('atv.index'))
    
    # Delete the file from filesystem
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], parent_type, str(parent_id), image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)
    
    # Delete from database
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully.', 'success')
    return redirect(redirect_url)

# Import all the parts routes
from app.atv.parts import *
