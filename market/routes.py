from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required

from utils import admin_required
from market.services import update_stock_prices

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from forms import PriceUploadForm

from market.services import update_stock_prices, update_prices_from_file
# from models import PriceUpdateLog

from models import Investment, PriceUpdateLog, PriceHistory

from flask import Response

from datetime import datetime, date


market_bp = Blueprint("market", __name__, url_prefix="/market")


# @market_bp.route("/update-stock-prices", methods=["POST"])
# @login_required
# @admin_required
# def update_prices():
#     result = update_stock_prices()

#     flash(
#         f"Stock price update completed. Updated: {result['updated']}, Failed: {result['failed']}",
#         "success"
#     )

#     return redirect(url_for("dashboard"))









@market_bp.route("/update-stock-prices", methods=["POST"])
@login_required
# @admin_required
def update_prices():
    result = update_stock_prices()

    flash(
        f"Stock price update completed. Updated: {result['updated']}, Failed: {result['failed']}",
        "success"
    )

    return redirect(url_for("dashboard"))


@market_bp.route("/upload-prices", methods=["GET", "POST"])
@login_required
# @admin_required
def upload_prices():
    form = PriceUploadForm()
    result = None

    if form.validate_on_submit():
        file = form.price_file.data

        try:
            result = update_prices_from_file(
                file_storage=file,
                uploaded_by=current_user.id
            )

            flash(
                f"Price upload completed. Updated: {result['updated']}, "
                f"Skipped: {result['skipped']}, Failed: {result['failed']}.",
                "success"
            )

        except Exception as e:
            flash(str(e), "danger")

    logs = PriceUpdateLog.query.order_by(
        PriceUpdateLog.created_at.desc()
    ).limit(50).all()

    return render_template(
        "market/upload_prices.html",
        form=form,
        result=result,
        logs=logs
    )






@market_bp.route("/sample-price-template")
@login_required
# @admin_required
def sample_price_template():
    csv_content = """symbol,current_price,date
GTCO,45.20,2026-05-14
ZENITHBANK,42.75,2026-05-14
MTNN,240.00,2026-05-14
FGN2031,1020.00,2026-05-14
"""

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=price_update_template.csv"
        }
    )