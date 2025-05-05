from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, URL
from wtforms import BooleanField

class EbayListingForm(FlaskForm):
    title = StringField('Listing Title', validators=[DataRequired(), Length(max=80)], 
                       description='Ebay title - max 80 characters')
    
    condition = SelectField('Item Condition', choices=[
        ('New', 'New'),
        ('Like New', 'Like New'),
        ('Open box', 'Open Box'),
        ('Used', 'Used'),
        ('For parts or not working', 'For Parts/Not Working')
    ])
    
    condition_description = TextAreaField('Condition Description', 
                                         validators=[Optional(), Length(max=1000)],
                                         description='Describe any wear, damage, or flaws')
    
    format = SelectField('Listing Format', choices=[
        ('fixed_price', 'Buy It Now'),
        ('auction', 'Auction')
    ])
    
    price = FloatField('Price ($)', validators=[DataRequired(), NumberRange(min=0.01)],
                      description='For Buy It Now, this is the price. For auctions, this is the starting bid.')
    
    reserve_price = FloatField('Reserve Price ($)', validators=[Optional(), NumberRange(min=0.01)],
                              description='Minimum price you\'ll accept (for auctions)')
    
    duration = SelectField('Listing Duration', choices=[
        ('1', '1 Day'),
        ('3', '3 Days'),
        ('5', '5 Days'),
        ('7', '7 Days'),
        ('10', '10 Days'),
        ('30', '30 Days (Buy It Now only)')
    ])
    
    category = StringField('eBay Category', validators=[Optional(), Length(max=100)],
                          description='e.g. ATV Parts, Powersports Parts')
    
    description = TextAreaField('Item Description', validators=[DataRequired(), Length(max=5000)])
    
    shipping_cost = FloatField('Shipping Cost ($)', validators=[Optional(), NumberRange(min=0)],
                              description='Leave blank for calculated shipping or free shipping')
    
    handling_time = SelectField('Handling Time', choices=[
        ('1', '1 Business Day'),
        ('2', '2 Business Days'),
        ('3', '3 Business Days'),
        ('4', '4 Business Days'),
        ('5', '5 Business Days')
    ])
    
    return_policy = SelectField('Return Policy', choices=[
        ('no_returns', 'No Returns'),
        ('30_days', '30 Day Returns'),
        ('60_days', '60 Day Returns')
    ])
    
    free_shipping = BooleanField('Offer Free Shipping')
    
    calculated_shipping = BooleanField('Use Calculated Shipping')
    
    package_weight = FloatField('Package Weight (lbs)', validators=[Optional(), NumberRange(min=0.01)],
                               description='For calculated shipping')
    
    package_dimensions = StringField('Package Dimensions (LxWxH in inches)', 
                                   validators=[Optional(), Length(max=50)],
                                   description='For calculated shipping, e.g. 12x8x4')
