from datetime import datetime
from app import db

class Storage(db.Model):
    __tablename__ = 'storage'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ATV(db.Model):
    __tablename__ = 'atv'
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64), index=True)
    model = db.Column(db.String(64), index=True)
    year = db.Column(db.Integer)
    status = db.Column(db.String(64), default='active')  # active, parting_out, sold
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_price = db.Column(db.Float)
    purchase_location = db.Column(db.String(128))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships
    expenses = db.relationship('Expense', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    parts = db.relationship('Part', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='atv', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('Image', backref='atv', lazy='dynamic', cascade='all, delete-orphan')

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

class Part(db.Model):
    __tablename__ = 'part'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    part_number = db.Column(db.String(64), index=True)
    condition = db.Column(db.String(64))  # new, used_good, used_fair, used_poor
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'))
    status = db.Column(db.String(64), default='in_stock')  # in_stock, listed, sold
    source_price = db.Column(db.Float)    # Value when removed from ATV
    list_price = db.Column(db.Float)      # Listed price
    sold_price = db.Column(db.Float)      # Actual sold price
    sold_date = db.Column(db.DateTime)    # Date when sold
    shipping_cost = db.Column(db.Float)   # Shipping cost if sold
    platform_fees = db.Column(db.Float)   # Platform fees if sold
    platform = db.Column(db.String(64))   # ebay, facebook, local, etc.
    listing_url = db.Column(db.String(256))  # URL to the listing if active
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships
    images = db.relationship('Image', backref='part', lazy='dynamic', cascade='all, delete-orphan')
    storage = db.relationship('Storage', backref='stored_parts', lazy='dynamic')
    ebay_listings = db.relationship('EbayListing', backref='part', lazy='dynamic', cascade='all, delete-orphan')

    def net_profit(self):
        """Calculate net profit for the part if sold"""
        if self.status != 'sold' or not self.sold_price:
            return 0
        
        total_cost = self.source_price or 0
        total_cost += self.shipping_cost or 0
        total_cost += self.platform_fees or 0
        
        return self.sold_price - total_cost

class Expense(db.Model):
    __tablename__ = 'expense'
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
    __tablename__ = 'sale'
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
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)  # For future AI-generated descriptions

class EbayListing(db.Model):
    __tablename__ = 'ebay_listing'
    id = db.Column(db.Integer, primary_key=True)
    ebay_id = db.Column(db.String(64), unique=True)
    title = db.Column(db.String(256))
    price = db.Column(db.Float)
    status = db.Column(db.String(64))  # active, sold, ended
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
