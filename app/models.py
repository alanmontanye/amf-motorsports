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
    
    def __repr__(self):
        return f"<Storage {self.name}>"

class ATV(db.Model):
    __tablename__ = 'atv'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float, default=0)
    purchase_location = db.Column(db.String(100))
    description = db.Column(db.Text)
    total_earnings = db.Column(db.Float, default=0)
    
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
    location = db.Column(db.String(64))
    status = db.Column(db.String(20), default='in_stock')  # in_stock, listed, sold
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'))
    atv_id = db.Column(db.Integer, db.ForeignKey('atv.id'), nullable=False)
    source_price = db.Column(db.Float, default=0)
    list_price = db.Column(db.Float)
    sold_price = db.Column(db.Float)
    sold_date = db.Column(db.Date)
    shipping_cost = db.Column(db.Float)
    platform_fees = db.Column(db.Float)
    platform = db.Column(db.String(20))
    listing_url = db.Column(db.String(256))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    storage = db.relationship('Storage', backref=db.backref('parts', lazy='dynamic'))
    images = db.relationship('Image', backref='part', lazy='dynamic', cascade="all, delete-orphan")
    ebay_listings = db.relationship('EbayListing', backref='part', lazy='dynamic', cascade="all, delete-orphan")
    
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

class EbayListing(db.Model):
    """Model for tracking eBay listings"""
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ebay_item_id = db.Column(db.String(128))  # eBay's item ID (for API integration)
    status = db.Column(db.String(20), default='pending')  # pending, active, ended, sold
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON field to store additional listing data
    listing_data = db.Column(db.Text)  # Will store JSON
    
    def __repr__(self):
        return f'<EbayListing {self.title}>'

class EbayCredentials(db.Model):
    """Model for storing eBay API credentials and tokens"""
    id = db.Column(db.Integer, primary_key=True)
    
    # OAuth tokens
    access_token = db.Column(db.String(2000))
    refresh_token = db.Column(db.String(2000))
    token_expiry = db.Column(db.DateTime)
    
    # Environment settings
    environment = db.Column(db.String(20), default='sandbox')  # 'sandbox' or 'production'
    
    # Developer credentials (encrypted in production)
    client_id = db.Column(db.String(256))
    client_secret = db.Column(db.String(256))
    
    # User preferences
    default_return_policy = db.Column(db.String(20), default='30_days')
    default_shipping_policy = db.Column(db.String(20), default='calculated')
    default_payment_policy = db.Column(db.String(20), default='immediate')
    
    # Integration status
    is_active = db.Column(db.Boolean, default=False)
    last_sync = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_token_valid(self):
        """Check if the access token is still valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.utcnow() < self.token_expiry
    
    def __repr__(self):
        return f'<EbayCredentials {self.environment}>'

class EbayCategory(db.Model):
    """Model for storing eBay category information"""
    id = db.Column(db.Integer, primary_key=True)
    ebay_category_id = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    level = db.Column(db.Integer)
    parent_id = db.Column(db.String(20))
    
    # Store the full category path for easier display
    category_path = db.Column(db.String(512))
    
    # Is this a common category for ATV parts?
    is_favorite = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EbayCategory {self.name}>'

class EbayTemplate(db.Model):
    """Model for storing reusable eBay listing templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    # HTML template with placeholders
    html_content = db.Column(db.Text)
    
    # Default values and settings
    default_category_id = db.Column(db.String(20))
    default_shipping_options = db.Column(db.Text)  # JSON string
    default_return_policy = db.Column(db.Text)  # JSON string
    default_payment_policy = db.Column(db.Text)  # JSON string
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_shipping_options(self):
        """Convert shipping options JSON to dict"""
        if not self.default_shipping_options:
            return {}
        try:
            return json.loads(self.default_shipping_options)
        except json.JSONDecodeError:
            return {}
    
    def set_shipping_options(self, options_dict):
        """Convert dict to JSON and store"""
        self.default_shipping_options = json.dumps(options_dict)
    
    def __repr__(self):
        return f'<EbayTemplate {self.name}>'

class EbayOrderSync(db.Model):
    """Model for tracking eBay order synchronization"""
    id = db.Column(db.Integer, primary_key=True)
    ebay_order_id = db.Column(db.String(128), nullable=False, unique=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('ebay_listing.id'))
    
    # Order details from eBay
    buyer_username = db.Column(db.String(128))
    order_total = db.Column(db.Float)
    order_status = db.Column(db.String(20))
    payment_status = db.Column(db.String(20))
    shipping_status = db.Column(db.String(20))
    
    # Address details
    shipping_address = db.Column(db.Text)  # JSON string
    
    # Tracking information
    tracking_number = db.Column(db.String(64))
    carrier = db.Column(db.String(64))
    
    # Full order details
    order_data = db.Column(db.Text)  # JSON string of complete order
    
    # Local processing status
    is_processed = db.Column(db.Boolean, default=False)
    processing_notes = db.Column(db.Text)
    
    order_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    listing = db.relationship('EbayListing', backref='orders', lazy=True)
    
    def get_order_data(self):
        """Convert order data JSON to dict"""
        if not self.order_data:
            return {}
        try:
            return json.loads(self.order_data)
        except json.JSONDecodeError:
            return {}
    
    def __repr__(self):
        return f'<EbayOrderSync {self.ebay_order_id}>'

class EbayHistoricalPrice(db.Model):
    """Model for storing historical price data from eBay"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Search criteria used
    keywords = db.Column(db.String(256))
    category_id = db.Column(db.String(20))
    condition = db.Column(db.String(20))
    
    # Item details
    ebay_item_id = db.Column(db.String(128))
    title = db.Column(db.String(256))
    sold_price = db.Column(db.Float)
    shipping_cost = db.Column(db.Float)
    total_price = db.Column(db.Float)
    
    # Dates
    sold_date = db.Column(db.DateTime)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    
    def __repr__(self):
        return f'<EbayHistoricalPrice {self.title}>'
