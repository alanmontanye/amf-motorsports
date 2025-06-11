from app import db
from datetime import datetime
import json

class Storage(db.Model):
    """Model for tracking storage locations of parts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add stored_parts property
    @property
    def stored_parts(self):
        return self.parts
    
    def parts_count(self):
        """Get the number of parts in this storage location"""
        return self.parts.count()
    
    def get_parts_info(self):
        """Get summary information about parts in this storage"""
        total_parts = self.parts_count()
        value = sum(part.list_price or 0 for part in self.parts)
        return {
            'count': total_parts,
            'value': value
        }
    
    def __repr__(self):
        return f"<Storage {self.name}>"

class ATV(db.Model):
    __tablename__ = 'atv'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')  # General status: active, sold, scrapped, etc.
    parting_status = db.Column(db.String(20), default='whole')  # Parting status: whole, parting_out, parted_out
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float, default=0)
    purchase_location = db.Column(db.String(100))
    description = db.Column(db.Text)
    total_earnings = db.Column(db.Float, default=0)
    machine_id = db.Column(db.String(64))  # Slug-style or UUID for machine identification
    
    # Hours tracking fields as database columns
    acquisition_hours = db.Column(db.Float, default=0)
    repair_hours = db.Column(db.Float, default=0)
    selling_hours = db.Column(db.Float, default=0)
    total_hours = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    parts = db.relationship('Part', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('Image', backref='atv', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(ATV, self).__init__(**kwargs)
        # Ensure hours fields have default values to avoid None errors
        if self.acquisition_hours is None:
            self.acquisition_hours = 0
        if self.repair_hours is None:
            self.repair_hours = 0
        if self.selling_hours is None:
            self.selling_hours = 0
        if self.total_hours is None:
            self.total_hours = 0
        # Set default parting status if not provided
        if self.parting_status is None:
            self.parting_status = 'whole'
        # Generate a machine_id if not provided
        if self.machine_id is None:
            import uuid
            self.machine_id = str(uuid.uuid4())
        # Update total hours when initializing
        self.update_total_hours()
    
    def update_total_hours(self):
        """Update total hours based on component hours"""
        self.acquisition_hours = self.acquisition_hours or 0
        self.repair_hours = self.repair_hours or 0
        self.selling_hours = self.selling_hours or 0
        self.total_hours = self.acquisition_hours + self.repair_hours + self.selling_hours
        return self.total_hours
    
    def total_expenses(self):
        """Calculate total expenses including handling None values"""
        return sum(expense.amount or 0 for expense in self.expenses)

    def total_sales(self):
        """Calculate total sales including handling None values"""
        return sum(sale.amount or 0 for sale in self.sales)

    def total_parts_value(self):
        """Calculate total value of parts based on their status"""
        total = 0
        for part in self.parts:
            if part.status == 'sold':
                total += part.sold_price or 0
            else:
                total += part.list_price or 0
        return total

    def parts_profit(self):
        """Calculate total profit from parts"""
        return sum((part.net_profit() for part in self.parts if part.status == 'sold'), 0)

    def profit_loss(self):
        """Calculate total profit/loss including parts"""
        parts_profit = self.parts_profit()
        direct_profit = self.total_sales() - self.total_expenses() - (self.purchase_price or 0)
        return direct_profit + parts_profit

    def total_profit(self):
        """Calculate total profit"""
        return self.total_earnings - self.purchase_price - self.total_expenses()

    def hourly_profit_rate(self):
        """Calculate profit per hour invested"""
        if self.total_hours is None or self.total_hours == 0:
            return 0
        return self.profit_loss() / self.total_hours

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    part_number = db.Column(db.String(64))
    condition = db.Column(db.String(20))
    location = db.Column(db.String(64))  # Traditional location reference
    tote = db.Column(db.String(20))      # Tote identifier (e.g., TOTE_A2)
    description = db.Column(db.Text)
    source_price = db.Column(db.Float)
    list_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='in_stock')  # in_stock, sold, reserved, listed
    platform = db.Column(db.String(32))  # platform where sold/listed
    
    # Sales data
    sold_price = db.Column(db.Float)
    sold_date = db.Column(db.DateTime)
    shipping_cost = db.Column(db.Float)
    platform_fees = db.Column(db.Float)
    estimated_value = db.Column(db.Float)  # For ROI calculations/auto-generated values
    
    # Listing info
    listing_id = db.Column(db.String(128))  # External listing ID 
    listing_url = db.Column(db.String(256))  # URL to the listing
    listing_date = db.Column(db.DateTime)    # When the item was listed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Added missing created_at field
    
    # Foreign keys
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'))
    
    # Relationships
    images = db.relationship('Image', backref='part', lazy='dynamic', cascade='all, delete-orphan')
    storage = db.relationship('Storage', backref='parts', lazy=True)
    
    def net_profit(self):
        """Calculate the net profit for this part"""
        if self.status != 'sold' or not self.sold_price:
            return 0
        
        # If source_price is None or 0, use 0 as the cost basis
        cost_basis = self.source_price or 0
        shipping = self.shipping_cost or 0
        fees = self.platform_fees or 0
        
        return self.sold_price - cost_basis - shipping - fees

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)
    category = db.Column(db.String(64))  # gas, repairs, tools, shipping, etc.
    description = db.Column(db.Text)
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def monthly_by_category(year, month):
        """Get total expenses by category for a specific month"""
        expenses = Expense.query.filter(
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).all()
        totals = {}
        for expense in expenses:
            totals[expense.category] = totals.get(expense.category, 0) + expense.amount
        return totals

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)
    platform = db.Column(db.String(64))  # ebay, facebook, local, etc.
    fees = db.Column(db.Float, default=0.0)  # Platform fees
    shipping_cost = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float)  # amount - fees - shipping
    type = db.Column(db.String(64))  # full_atv, part
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_net(self):
        self.net_amount = self.amount - (self.fees or 0) - (self.shipping_cost or 0)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    image_type = db.Column(db.String(64))  # 'general', 'vin', 'damage', etc.
    
    def __repr__(self):
        return f"<Image {self.filename}>"

# eBay related models removed to simplify the application

# EbayCredentials model removed

# EbayCategory model removed

# EbayTemplate model removed

# All eBay-related models removed to simplify the application
