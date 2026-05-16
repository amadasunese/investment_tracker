from flask import Flask, render_template
from flask_login import login_required, current_user

from config import Config
from extensions import db, migrate, login_manager
from models import Investment, CouponSchedule

from auth.routes import auth_bp
from investments.routes import investment_bp
from reports.routes import reports_bp
from market.routes import market_bp

from datetime import date, timedelta


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(investment_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(market_bp)

    @app.route("/")
    @login_required
    def dashboard():
        query = Investment.query

        if current_user.role not in ["admin", "superadmin"]:
            query = query.filter_by(user_id=current_user.id)

        investments = query.order_by(Investment.created_at.desc()).all()

        total_invested = sum(i.principal_amount or 0 for i in investments)
        total_current_value = sum(i.calculate_current_value() for i in investments)
        total_income = sum(i.total_income() for i in investments)
        total_profit_loss = sum(i.profit_or_loss() for i in investments)

        roi = 0
        if total_invested > 0:
            roi = (total_profit_loss / total_invested) * 100

        by_type = {}
        by_sector = {}
        by_maturity_year = {}

        for inv in investments:
            value = inv.calculate_current_value()

            by_type[inv.investment_type] = by_type.get(inv.investment_type, 0) + value

            sector = inv.sector or "Unclassified"
            by_sector[sector] = by_sector.get(sector, 0) + value

            if inv.maturity_date:
                year = str(inv.maturity_date.year)
                by_maturity_year[year] = by_maturity_year.get(year, 0) + value

        today = date.today()
        maturity_limit = today + timedelta(days=30)

        maturity_alerts = [
            inv for inv in investments
            if inv.maturity_date and today <= inv.maturity_date <= maturity_limit
        ]

        coupon_alerts = CouponSchedule.query.join(Investment)

        if current_user.role not in ["admin", "superadmin"]:
            coupon_alerts = coupon_alerts.filter(Investment.user_id == current_user.id)

        coupon_alerts = coupon_alerts.filter(
            CouponSchedule.status == "Pending",
            CouponSchedule.due_date >= today,
            CouponSchedule.due_date <= maturity_limit
        ).order_by(CouponSchedule.due_date.asc()).all()

        return render_template(
            "dashboard.html",
            investments=investments,
            total_invested=total_invested,
            total_current_value=total_current_value,
            total_income=total_income,
            total_profit_loss=total_profit_loss,
            roi=roi,
            by_type=by_type,
            by_sector=by_sector,
            by_maturity_year=by_maturity_year,
            maturity_alerts=maturity_alerts,
            coupon_alerts=coupon_alerts
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)