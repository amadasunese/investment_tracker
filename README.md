# Investment Monitor

A Flask-based web application for monitoring investments in **FGN Bonds**, **Nigerian Stocks**, **Treasury Bills**, **Mutual Funds**, **Fixed Deposits**, **Real Estate**, and other investment assets.

The application helps users track investment value, income, maturity dates, dividends, coupon payments, price history, portfolio performance, and downloadable reports.

---

## Features

### User and Role Management

- User registration and login
- Password hashing
- Role-based access control
- Supported roles:
  - `user`
  - `admin`
  - `superadmin`
- Users can only view and manage their own investments
- Admins and superadmins can manage wider system records

---

### Investment Tracking

Users can record and monitor different investment types, including:

- FGN Bonds
- Nigerian Stocks
- Treasury Bills
- Mutual Funds
- Fixed Deposits
- Real Estate
- Other Investments

Each investment can include:

- Investment name
- Investment type
- Sector
- Symbol or bond code
- Institution or broker
- Purchase date
- Maturity date
- Units or shares
- Purchase price
- Current price
- Principal amount invested
- Current value
- Interest/coupon rate
- Coupon frequency
- Notes

---

### Auto Calculation

The system automatically calculates:

```text
Principal / Amount Invested = Units × Purchase Price
Current Value = Units × Current Price
Profit / Loss = Current Value + Income - Principal Amount
ROI (%) = Profit or Loss / Principal Amount × 100