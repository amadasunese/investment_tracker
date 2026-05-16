from flask import Blueprint, render_template, send_file, abort, request
from flask_login import login_required, current_user

from extensions import db
from models import Investment, CouponSchedule, DividendHistory, PriceHistory

from io import BytesIO
from datetime import date
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas



reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def get_user_investments():
    query = Investment.query

    if current_user.role not in ["admin", "superadmin"]:
        query = query.filter_by(user_id=current_user.id)

    return query.order_by(Investment.created_at.desc()).all()


@reports_bp.route("/export/excel")
@login_required
def export_excel():
    investments = get_user_investments()

    rows = []

    for inv in investments:
        rows.append({
            "Investment Name": inv.investment_name,
            "Type": inv.investment_type,
            "Sector": inv.sector,
            "Symbol": inv.symbol,
            "Institution": inv.institution,
            "Purchase Date": inv.purchase_date,
            "Maturity Date": inv.maturity_date,
            "Units": inv.units,
            "Purchase Price": inv.purchase_price,
            "Current Price": inv.current_price,
            "Principal Amount": inv.principal_amount,
            "Current Value": inv.calculate_current_value(),
            "Total Income": inv.total_income(),
            "Profit/Loss": inv.profit_or_loss(),
            "ROI (%)": inv.roi_percentage(),
            "Maturity Status": inv.maturity_status()
        })

    df = pd.DataFrame(rows)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Portfolio")

        workbook = writer.book
        worksheet = writer.sheets["Portfolio"]

        for column_cells in worksheet.columns:
            length = max(len(str(cell.value or "")) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 3

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="investment_portfolio.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@reports_bp.route("/monthly")
@login_required
def monthly_report():
    month = request.args.get("month", type=int) or date.today().month
    year = request.args.get("year", type=int) or date.today().year

    investments = get_user_investments()

    monthly_dividends = DividendHistory.query.join(Investment)

    if current_user.role not in ["admin", "superadmin"]:
        monthly_dividends = monthly_dividends.filter(Investment.user_id == current_user.id)

    monthly_dividends = monthly_dividends.filter(
        db.extract("month", DividendHistory.payment_date) == month,
        db.extract("year", DividendHistory.payment_date) == year
    ).all()

    monthly_coupons = CouponSchedule.query.join(Investment)

    if current_user.role not in ["admin", "superadmin"]:
        monthly_coupons = monthly_coupons.filter(Investment.user_id == current_user.id)

    monthly_coupons = monthly_coupons.filter(
        db.extract("month", CouponSchedule.due_date) == month,
        db.extract("year", CouponSchedule.due_date) == year
    ).all()

    total_invested = sum(i.principal_amount or 0 for i in investments)
    total_current_value = sum(i.calculate_current_value() for i in investments)
    total_profit_loss = sum(i.profit_or_loss() for i in investments)

    total_dividends = sum(d.amount or 0 for d in monthly_dividends)
    total_coupon_due = sum(c.amount or 0 for c in monthly_coupons)
    total_coupon_paid = sum(c.amount or 0 for c in monthly_coupons if c.status == "Paid")

    return render_template(
        "reports/monthly.html",
        investments=investments,
        monthly_dividends=monthly_dividends,
        monthly_coupons=monthly_coupons,
        total_invested=total_invested,
        total_current_value=total_current_value,
        total_profit_loss=total_profit_loss,
        total_dividends=total_dividends,
        total_coupon_due=total_coupon_due,
        total_coupon_paid=total_coupon_paid,
        month=month,
        year=year
    )


@reports_bp.route("/statement/pdf")
@login_required
def pdf_statement():
    investments = get_user_investments()

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Investment Portfolio Statement")

    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Generated for: {current_user.full_name}")
    y -= 15
    pdf.drawString(50, y, f"Date: {date.today().strftime('%d %B %Y')}")

    y -= 35

    total_invested = sum(i.principal_amount or 0 for i in investments)
    total_current_value = sum(i.calculate_current_value() for i in investments)
    total_income = sum(i.total_income() for i in investments)
    total_profit_loss = sum(i.profit_or_loss() for i in investments)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, f"Total Invested: N{total_invested:,.2f}")
    y -= 18
    pdf.drawString(50, y, f"Current Value: N{total_current_value:,.2f}")
    y -= 18
    pdf.drawString(50, y, f"Total Income: N{total_income:,.2f}")
    y -= 18
    pdf.drawString(50, y, f"Profit/Loss: N{total_profit_loss:,.2f}")

    y -= 35

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(50, y, "Investment")
    pdf.drawString(180, y, "Type")
    pdf.drawString(280, y, "Invested")
    pdf.drawString(370, y, "Current")
    pdf.drawString(460, y, "P/L")

    y -= 12
    pdf.line(50, y, 550, y)
    y -= 15

    pdf.setFont("Helvetica", 8)

    for inv in investments:
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 8)

        pdf.drawString(50, y, str(inv.investment_name)[:22])
        pdf.drawString(180, y, str(inv.investment_type)[:18])
        pdf.drawString(280, y, f"N{inv.principal_amount:,.2f}")
        pdf.drawString(370, y, f"N{inv.calculate_current_value():,.2f}")
        pdf.drawString(460, y, f"N{inv.profit_or_loss():,.2f}")

        y -= 15

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="investment_statement.pdf",
        mimetype="application/pdf"
    )
    
    
    
@reports_bp.route("/portfolio-history")
@login_required
def portfolio_history():
    query = PriceHistory.query.join(Investment)

    if current_user.role not in ["admin", "superadmin"]:
        query = query.filter(Investment.user_id == current_user.id)

    histories = query.order_by(PriceHistory.recorded_date.asc()).all()

    portfolio_by_date = {}

    for item in histories:
        date_key = item.recorded_date.strftime("%Y-%m-%d")
        portfolio_by_date[date_key] = portfolio_by_date.get(date_key, 0) + (item.value or 0)

    labels = list(portfolio_by_date.keys())
    values = list(portfolio_by_date.values())

    return render_template(
        "reports/portfolio_history.html",
        histories=histories,
        labels=labels,
        values=values
    )