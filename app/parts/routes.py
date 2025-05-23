from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from app import db
from app.parts import bp
from app.models import Part, ATV

@bp.route('/parts')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    parts = Part.query.order_by(Part.date_added.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('parts/index.html', title='Parts Inventory', parts=parts)

@bp.route('/parts/add', methods=['GET', 'POST'])
@login_required
def add_part():
    # This will be implemented in the next phase
    flash('Parts management will be implemented in Phase 2', 'info')
    return redirect(url_for('parts.index'))
