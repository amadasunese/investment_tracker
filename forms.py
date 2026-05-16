from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    FloatField,
    DateField,
    TextAreaField,
    SubmitField
)
from wtforms.validators import DataRequired, Optional, Email, Length, EqualTo, NumberRange


from flask_wtf.file import FileField, FileAllowed, FileRequired





class PriceUploadForm(FlaskForm):
    price_file = FileField(
        "Upload Price File",
        validators=[
            FileRequired(),
            FileAllowed(["csv", "xlsx", "xls"], "Only CSV and Excel files are allowed.")
        ]
    )

    submit = SubmitField("Upload and Update Prices")
    

class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class InvestmentForm(FlaskForm):
    investment_name = StringField("Investment Name", validators=[DataRequired()])

    investment_type = SelectField(
        "Investment Type",
        choices=[
            ("FGN Bond", "FGN Bond"),
            ("Nigerian Stock", "Nigerian Stock"),
            ("Treasury Bill", "Treasury Bill"),
            ("Mutual Fund", "Mutual Fund"),
            ("Fixed Deposit", "Fixed Deposit"),
            ("Real Estate", "Real Estate"),
            ("Other", "Other")
        ],
        validators=[DataRequired()]
    )

    sector = StringField("Sector", validators=[Optional()])
    symbol = StringField("Stock Symbol / Bond Code", validators=[Optional()])
    institution = StringField("Institution / Broker / Issuer", validators=[Optional()])

    purchase_date = DateField("Purchase Date", validators=[DataRequired()])
    maturity_date = DateField("Maturity Date", validators=[Optional()])

    units = FloatField("Units / Shares", validators=[Optional(), NumberRange(min=0)])
    purchase_price = FloatField("Purchase Price per Unit", validators=[Optional(), NumberRange(min=0)])
    current_price = FloatField("Current Price per Unit", validators=[Optional(), NumberRange(min=0)])

    principal_amount = FloatField("Principal / Amount Invested", validators=[Optional(), NumberRange(min=0)])
    current_value = FloatField("Current Value", validators=[Optional(), NumberRange(min=0)])

    interest_rate = FloatField("Interest / Coupon Rate (%)", validators=[Optional(), NumberRange(min=0)])

    coupon_frequency = SelectField(
        "Coupon / Interest Frequency",
        choices=[
            ("", "Not Applicable"),
            ("Monthly", "Monthly"),
            ("Quarterly", "Quarterly"),
            ("Semi-Annual", "Semi-Annual"),
            ("Annual", "Annual"),
            ("At Maturity", "At Maturity")
        ],
        validators=[Optional()]
    )
    
    dividends_received = FloatField("Dividends Received", validators=[Optional(), NumberRange(min=0)])

    interest_received = FloatField("Other Interest Received", validators=[Optional(), NumberRange(min=0)])

    notes = TextAreaField("Notes", validators=[Optional()])

    submit = SubmitField("Save Investment")


class DividendForm(FlaskForm):
    payment_date = DateField("Payment Date", validators=[DataRequired()])
    amount_per_share = FloatField("Dividend Per Share", validators=[DataRequired(), NumberRange(min=0)])
    units = FloatField("Units", validators=[DataRequired(), NumberRange(min=0)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Dividend")


class CouponForm(FlaskForm):
    due_date = DateField("Due Date", validators=[DataRequired()])
    amount = FloatField("Coupon Amount", validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField(
        "Status",
        choices=[
            ("Pending", "Pending"),
            ("Paid", "Paid"),
            ("Missed", "Missed")
        ],
        validators=[DataRequired()]
    )
    paid_date = DateField("Paid Date", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Coupon")


class BondYieldForm(FlaskForm):
    recorded_date = DateField("Recorded Date", validators=[DataRequired()])
    yield_rate = FloatField("Yield Rate (%)", validators=[DataRequired(), NumberRange(min=0)])
    market_price = FloatField("Market Price", validators=[Optional(), NumberRange(min=0)])
    source = StringField("Source", validators=[Optional()])
    submit = SubmitField("Save Yield")