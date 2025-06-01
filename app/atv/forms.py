from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, IntegerField, SelectField, TextAreaField, FloatField, DateField, URLField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL
from datetime import datetime
from app.models import Storage

def storage_query():
    return Storage.query

class ATVForm(FlaskForm):
    make = StringField('Make', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900, max=datetime.now().year)])
    vin = StringField('VIN')
    status = SelectField('Status', choices=[
        ('active', 'Active'), 
        ('sold', 'Sold'),
        ('scrapped', 'Scrapped')
    ], validators=[DataRequired()])
    parting_status = SelectField('Parting Status', choices=[
        ('whole', 'Whole Machine'),
        ('parting_out', 'Currently Parting Out'),
        ('parted_out', 'Completely Parted Out')
    ], validators=[DataRequired()])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()])
    purchase_price = FloatField('Purchase Price', validators=[DataRequired(), NumberRange(min=0)])
    purchase_location = StringField('Purchase Location')
    description = TextAreaField('Description')
    
    # Add hours tracking fields
    acquisition_hours = FloatField('Acquisition Hours', default=0, validators=[NumberRange(min=0)])
    repair_hours = FloatField('Repair Hours', default=0, validators=[NumberRange(min=0)])
    selling_hours = FloatField('Selling Hours', default=0, validators=[NumberRange(min=0)])
    
    submit = SubmitField('Save')

class ExpenseForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('gas', 'Gas/Fuel'),
        ('repairs', 'Repairs'),
        ('tools', 'Tools'),
        ('shipping', 'Shipping'),
        ('storage', 'Storage'),
        ('other', 'Other')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])

class SaleForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    amount = FloatField('Sale Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    platform = SelectField('Platform', choices=[
        ('ebay', 'eBay'),
        ('facebook', 'Facebook'),
        ('local', 'Local/In-Person'),
        ('other', 'Other')
    ])
    fees = FloatField('Platform Fees ($)', validators=[Optional(), NumberRange(min=0)])
    shipping_cost = FloatField('Shipping Cost ($)', validators=[Optional(), NumberRange(min=0)])
    type = SelectField('Sale Type', choices=[
        ('full_atv', 'Full ATV'),
        ('part', 'Part')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])

class PartForm(FlaskForm):
    name = StringField('Part Name', validators=[DataRequired(), Length(max=128)])
    part_number = StringField('Part Number', validators=[Optional(), Length(max=64)])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('used_poor', 'Used - Poor')
    ])
    storage_id = SelectField('Storage Location', coerce=int, validators=[Optional()])
    location = StringField('Legacy Storage Location', validators=[Optional(), Length(max=64)])
    tote = StringField('Tote ID', validators=[Optional(), Length(max=20)], 
                     description='Tote identifier (e.g., TOTE_A2)')
    status = SelectField('Status', choices=[
        ('in_stock', 'In Stock'),
        ('listed', 'Listed'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold')
    ])
    source_price = FloatField('Individual Purchase Cost ($)', validators=[Optional(), NumberRange(min=0)],
                            description='Only for individually purchased parts. Leave at $0 for parts from complete ATVs.')
    estimated_value = FloatField('Estimated Value ($)', validators=[Optional(), NumberRange(min=0)],
                               description='Value estimated from market research or ROI script')
    list_price = FloatField('List Price ($)', validators=[Optional(), NumberRange(min=0)])
    sold_price = FloatField('Sold Price ($)', validators=[Optional(), NumberRange(min=0)])
    sold_date = DateField('Sold Date', validators=[Optional()])
    shipping_cost = FloatField('Shipping Cost ($)', validators=[Optional(), NumberRange(min=0)])
    platform_fees = FloatField('Platform Fees ($)', validators=[Optional(), NumberRange(min=0)])
    platform = SelectField('Platform', choices=[
        ('', 'Not Listed'),
        ('ebay', 'eBay'),
        ('facebook', 'Facebook'),
        ('local', 'Local/In-Person'),
        ('other', 'Other')
    ])
    listing_id = StringField('Listing ID', validators=[Optional(), Length(max=128)],
                           description='External listing ID (e.g., eBay item number)')
    listing_url = URLField('Listing URL', validators=[Optional(), URL()])
    listing_date = DateField('Listing Date', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])

class ImageUploadForm(FlaskForm):
    image = FileField('Image File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    description = TextAreaField('Image Description', validators=[Optional(), Length(max=200)])
    image_type = SelectField('Image Type', choices=[
        ('general', 'General Image'),
        ('vin', 'VIN Photo'),
        ('damage', 'Damage Photo'),
        ('front', 'Front View'),
        ('rear', 'Rear View'),
        ('side', 'Side View'),
        ('engine', 'Engine'),
        ('parts', 'Parts Photo'),
        ('part_detail', 'Part Detail'),
        ('other', 'Other')
    ])


class BulkPartForm(FlaskForm):
    """Form for adding multiple parts at once"""
    storage_id = SelectField('Storage Location', coerce=int, validators=[DataRequired()])
    tote = StringField('Tote (shared for all parts)')
    
    # Part 1
    part1_name = StringField('Part 1 Name')
    part1_description = TextAreaField('Part 1 Description')
    part1_condition = SelectField('Part 1 Condition', choices=[
        ('', '-- Select Condition --'),
        ('new', 'New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('used_poor', 'Used - Poor')
    ])
    
    # Part 2
    part2_name = StringField('Part 2 Name')
    part2_description = TextAreaField('Part 2 Description')
    part2_condition = SelectField('Part 2 Condition', choices=[
        ('', '-- Select Condition --'),
        ('new', 'New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('used_poor', 'Used - Poor')
    ])
    
    # Part 3
    part3_name = StringField('Part 3 Name')
    part3_description = TextAreaField('Part 3 Description')
    part3_condition = SelectField('Part 3 Condition', choices=[
        ('', '-- Select Condition --'),
        ('new', 'New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('used_poor', 'Used - Poor')
    ])
    
    submit = SubmitField('Add Parts')


class QuickEditPartForm(FlaskForm):
    """Simplified form for quick inline editing"""
    name = StringField('Name', validators=[DataRequired(), Length(max=128)])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('used_poor', 'Used - Poor')
    ])
    status = SelectField('Status', choices=[
        ('in_stock', 'In Stock'),
        ('listed', 'Listed'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold')
    ])
    tote = StringField('Tote')
    list_price = FloatField('Price', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Update')
