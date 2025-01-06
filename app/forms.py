from flask_wtf import FlaskForm
from wtforms import (
    SelectField, FloatField, IntegerField, StringField, 
    SelectMultipleField, SubmitField
)
from wtforms.validators import DataRequired, NumberRange

class InvestmentForm(FlaskForm):
    risk_level = SelectField(
        'Risk Level',
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk')
        ],
        validators=[DataRequired()]
    )
    
    desired_return = FloatField(
        'Desired Annual Return (%)',
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100)
        ]
    )
    
    duration = IntegerField(
        'Investment Duration (Years)',
        validators=[
            DataRequired(),
            NumberRange(min=1, max=30)
        ]
    )
    
    sectors = SelectMultipleField(
        'Preferred Sectors',
        choices=[
            ('tech', 'Technology'),
            ('healthcare', 'Healthcare'),
            ('finance', 'Financial'),
            ('energy', 'Energy'),
            ('consumer', 'Consumer Goods'),
            ('real_estate', 'Real Estate'),
            ('utilities', 'Utilities')
        ]
    )
    
    budget = FloatField(
        'Investment Budget ($)',
        validators=[
            DataRequired(),
            NumberRange(min=1000)
        ]
    )
    
    dividend_priority = SelectField(
        'Dividend Priority',
        choices=[
            ('0', 'Not Important'),
            ('1', 'Somewhat Important'),
            ('2', 'Very Important')
        ]
    )
    
    ethical_considerations = SelectMultipleField(
        'Ethical Considerations',
        choices=[
            ('esg', 'ESG Focused'),
            ('green', 'Green Energy'),
            ('social', 'Social Impact'),
            ('governance', 'Good Governance')
        ]
    )
    
    investment_types = SelectMultipleField(
        'Investment Types',
        choices=[
            ('stocks', 'Individual Stocks'),
            ('etf', 'ETFs'),
            ('mutual_funds', 'Mutual Funds'),
            ('bonds', 'Bonds')
        ]
    )
    
    submit = SubmitField('Get Recommendations')