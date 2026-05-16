from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from extensions import db
# from models import Investment, DividendHistory, CouponSchedule, BondYieldHistory
from models import Investment, DividendHistory, CouponSchedule, BondYieldHistory, PriceHistory
from forms import InvestmentForm, DividendForm, CouponForm, BondYieldForm
from utils import user_can_access_investment


investment_bp = Blueprint("investments", __name__, url_prefix="/investments")


@investment_bp.route("/")
@login_required
def list_investments():
    investment_type = request.args.get("type")
    search = request.args.get("q")

    query = Investment.query

    if current_user.role not in ["admin", "superadmin"]:
        query = query.filter_by(user_id=current_user.id)

    if investment_type:
        query = query.filter(Investment.investment_type == investment_type)

    if search:
        query = query.filter(Investment.investment_name.ilike(f"%{search}%"))

    investments = query.order_by(Investment.created_at.desc()).all()

    return render_template(
        "investments/list.html",
        investments=investments,
        investment_type=investment_type,
        search=search
    )


@investment_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_investment():
    form = InvestmentForm()

    if form.validate_on_submit():
        units = form.units.data or 0
        purchase_price = form.purchase_price.data or 0
        current_price = form.current_price.data or 0

        principal_amount = units * purchase_price
        current_value = units * current_price

        investment = Investment(
            user_id=current_user.id,
            investment_name=form.investment_name.data,
            investment_type=form.investment_type.data,
            sector=form.sector.data,
            symbol=form.symbol.data.upper() if form.symbol.data else None,
            institution=form.institution.data,
            purchase_date=form.purchase_date.data,
            maturity_date=form.maturity_date.data,
            units=units,
            purchase_price=purchase_price,
            current_price=current_price,
            principal_amount=principal_amount,
            current_value=current_value,
            interest_rate=form.interest_rate.data or 0,
            coupon_frequency=form.coupon_frequency.data,
            interest_received=form.interest_received.data or 0,
            notes=form.notes.data
        )

        db.session.add(investment)
        db.session.commit()

        flash("Investment added successfully.", "success")
        return redirect(url_for("investments.list_investments"))

    return render_template("investments/add.html", form=form)


@investment_bp.route("/<int:id>")
@login_required
def detail(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    return render_template("investments/detail.html", investment=investment)


@investment_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    form = InvestmentForm(obj=investment)

    if form.validate_on_submit():
        investment.investment_name = form.investment_name.data
        investment.investment_type = form.investment_type.data
        investment.sector = form.sector.data
        investment.symbol = form.symbol.data.upper() if form.symbol.data else None
        investment.institution = form.institution.data
        investment.purchase_date = form.purchase_date.data
        investment.maturity_date = form.maturity_date.data
        units = form.units.data or 0
        purchase_price = form.purchase_price.data or 0
        current_price = form.current_price.data or 0

        investment.units = units
        investment.purchase_price = purchase_price
        investment.current_price = current_price
        investment.principal_amount = units * purchase_price
        investment.current_value = units * current_price
        investment.interest_rate = form.interest_rate.data or 0
        investment.coupon_frequency = form.coupon_frequency.data
        investment.interest_received = form.interest_received.data or 0
        investment.notes = form.notes.data

        db.session.commit()

        flash("Investment updated successfully.", "success")
        return redirect(url_for("investments.detail", id=investment.id))

    return render_template("investments/edit.html", form=form, investment=investment)


@investment_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    db.session.delete(investment)
    db.session.commit()

    flash("Investment deleted successfully.", "success")
    return redirect(url_for("investments.list_investments"))


@investment_bp.route("/<int:id>/dividends", methods=["GET", "POST"])
@login_required
def dividends(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    form = DividendForm()

    if form.validate_on_submit():
        amount = (form.amount_per_share.data or 0) * (form.units.data or 0)

        dividend = DividendHistory(
            investment_id=investment.id,
            payment_date=form.payment_date.data,
            amount_per_share=form.amount_per_share.data,
            units=form.units.data,
            amount=amount,
            notes=form.notes.data
        )

        db.session.add(dividend)
        db.session.commit()

        flash("Dividend recorded successfully.", "success")
        return redirect(url_for("investments.dividends", id=investment.id))

    dividends = DividendHistory.query.filter_by(
        investment_id=investment.id
    ).order_by(DividendHistory.payment_date.desc()).all()

    return render_template(
        "investments/dividends.html",
        investment=investment,
        form=form,
        dividends=dividends
    )


@investment_bp.route("/<int:id>/coupons", methods=["GET", "POST"])
@login_required
def coupons(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    form = CouponForm()

    if form.validate_on_submit():
        coupon = CouponSchedule(
            investment_id=investment.id,
            due_date=form.due_date.data,
            amount=form.amount.data,
            status=form.status.data,
            paid_date=form.paid_date.data,
            notes=form.notes.data
        )

        db.session.add(coupon)
        db.session.commit()

        flash("Coupon schedule saved successfully.", "success")
        return redirect(url_for("investments.coupons", id=investment.id))

    coupons = CouponSchedule.query.filter_by(
        investment_id=investment.id
    ).order_by(CouponSchedule.due_date.asc()).all()

    return render_template(
        "investments/coupons.html",
        investment=investment,
        form=form,
        coupons=coupons
    )


@investment_bp.route("/<int:id>/bond-yields", methods=["GET", "POST"])
@login_required
def bond_yields(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    form = BondYieldForm()

    if form.validate_on_submit():
        bond_yield = BondYieldHistory(
            investment_id=investment.id,
            recorded_date=form.recorded_date.data,
            yield_rate=form.yield_rate.data,
            market_price=form.market_price.data or 0,
            source=form.source.data
        )

        investment.current_price = form.market_price.data or investment.current_price
        investment.current_value = form.market_price.data or investment.current_value

        db.session.add(bond_yield)
        db.session.commit()

        flash("Bond yield recorded successfully.", "success")
        return redirect(url_for("investments.bond_yields", id=investment.id))

    yields = BondYieldHistory.query.filter_by(
        investment_id=investment.id
    ).order_by(BondYieldHistory.recorded_date.desc()).all()

    return render_template(
        "investments/bond_yields.html",
        investment=investment,
        form=form,
        yields=yields
    )
    
    
@investment_bp.route("/<int:id>/price-history")
@login_required
def price_history(id):
    investment = Investment.query.get_or_404(id)

    if not user_can_access_investment(current_user, investment):
        abort(403)

    history = PriceHistory.query.filter_by(
        investment_id=investment.id
    ).order_by(PriceHistory.recorded_date.asc()).all()

    labels = [h.recorded_date.strftime("%Y-%m-%d") for h in history]
    prices = [h.price for h in history]
    values = [h.value for h in history]

    return render_template(
        "investments/price_history.html",
        investment=investment,
        history=history,
        labels=labels,
        prices=prices,
        values=values
    )