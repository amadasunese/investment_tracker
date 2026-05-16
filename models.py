from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(30), default="user")  
    # roles: user, admin, superadmin

    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    investments = db.relationship("Investment", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role in ["admin", "superadmin"]

    def is_superadmin(self):
        return self.role == "superadmin"


class Investment(db.Model):
    __tablename__ = "investments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    investment_name = db.Column(db.String(150), nullable=False)
    investment_type = db.Column(db.String(50), nullable=False)
    sector = db.Column(db.String(100), nullable=True)

    symbol = db.Column(db.String(30), nullable=True)
    institution = db.Column(db.String(150), nullable=True)

    purchase_date = db.Column(db.Date, nullable=False)
    maturity_date = db.Column(db.Date, nullable=True)

    units = db.Column(db.Float, default=0)
    purchase_price = db.Column(db.Float, default=0)
    current_price = db.Column(db.Float, default=0)

    principal_amount = db.Column(db.Float, nullable=False, default=0)
    current_value = db.Column(db.Float, nullable=False, default=0)

    interest_rate = db.Column(db.Float, default=0)
    coupon_frequency = db.Column(db.String(50), nullable=True)

    dividends_received = db.Column(db.Float, default=0)
    interest_received = db.Column(db.Float, default=0)

    last_price_update = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dividends = db.relationship(
        "DividendHistory",
        backref="investment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    coupons = db.relationship(
        "CouponSchedule",
        backref="investment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    bond_yields = db.relationship(
        "BondYieldHistory",
        backref="investment",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    price_history = db.relationship(
        "PriceHistory",
        backref="investment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def calculate_current_value(self):
        if self.investment_type == "Nigerian Stock" and self.units and self.current_price:
            return self.units * self.current_price

        if self.investment_type == "Mutual Fund" and self.units and self.current_price:
            return self.units * self.current_price

        if self.current_value:
            return self.current_value

        return self.principal_amount

    def total_dividends(self):
        return sum(d.amount or 0 for d in self.dividends)

    def total_coupon_income(self):
        return sum(c.amount or 0 for c in self.coupons if c.status == "Paid")

    def total_income(self):
        return self.total_dividends() + self.total_coupon_income() + (self.interest_received or 0)

    def profit_or_loss(self):
        return self.calculate_current_value() + self.total_income() - self.principal_amount

    def roi_percentage(self):
        if not self.principal_amount:
            return 0
        return (self.profit_or_loss() / self.principal_amount) * 100

    def days_to_maturity(self):
        if not self.maturity_date:
            return None
        return (self.maturity_date - date.today()).days

    def maturity_status(self):
        days = self.days_to_maturity()

        if days is None:
            return "No maturity date"

        if days < 0:
            return "Matured"

        if days <= 30:
            return "Maturing soon"

        return "Active"


class DividendHistory(db.Model):
    __tablename__ = "dividend_history"

    id = db.Column(db.Integer, primary_key=True)

    investment_id = db.Column(db.Integer, db.ForeignKey("investments.id"), nullable=False)

    payment_date = db.Column(db.Date, nullable=False)
    amount_per_share = db.Column(db.Float, default=0)
    units = db.Column(db.Float, default=0)
    amount = db.Column(db.Float, default=0)

    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CouponSchedule(db.Model):
    __tablename__ = "coupon_schedule"

    id = db.Column(db.Integer, primary_key=True)

    investment_id = db.Column(db.Integer, db.ForeignKey("investments.id"), nullable=False)

    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default="Pending")
    # Pending, Paid, Missed

    paid_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BondYieldHistory(db.Model):
    __tablename__ = "bond_yield_history"

    id = db.Column(db.Integer, primary_key=True)

    investment_id = db.Column(db.Integer, db.ForeignKey("investments.id"), nullable=False)

    recorded_date = db.Column(db.Date, nullable=False)
    yield_rate = db.Column(db.Float, nullable=False)
    market_price = db.Column(db.Float, default=0)

    source = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PriceUpdateLog(db.Model):
    __tablename__ = "price_update_logs"

    id = db.Column(db.Integer, primary_key=True)
    
    investment_id = db.Column(db.Integer, db.ForeignKey("investments.id"), nullable=True)
    
    investment_name = db.Column(db.String(150), nullable=True)


    symbol = db.Column(db.String(30), nullable=False)
    old_price = db.Column(db.Float, default=0)
    new_price = db.Column(db.Float, default=0)
    
    old_value = db.Column(db.Float, default=0)
    new_value = db.Column(db.Float, default=0)

    status = db.Column(db.String(30), default="Success")
    message = db.Column(db.Text, nullable=True)
    
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)

    investment_id = db.Column(
        db.Integer,
        db.ForeignKey("investments.id"),
        nullable=False
    )

    symbol = db.Column(db.String(30), nullable=False)

    price = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)

    recorded_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(100), default="Upload")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)