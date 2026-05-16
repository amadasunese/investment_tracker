from datetime import datetime, date
from extensions import db
# from models import Investment, PriceUpdateLog
from models import Investment, PriceUpdateLog, PriceHistory


# from datetime import datetime
import pandas as pd

# from extensions import db
# from models import Investment, PriceUpdateLog




ALLOWED_COLUMNS = ["symbol", "current_price", "date"]


def read_price_file(file_storage):
    """
    Reads uploaded CSV or Excel file and returns a pandas DataFrame.
    """

    filename = file_storage.filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(file_storage)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(file_storage)
    else:
        raise ValueError("Unsupported file type. Please upload CSV or Excel file.")

    # Normalize column names
    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    if "symbol" not in df.columns:
        raise ValueError("The uploaded file must contain a 'symbol' column.")

    if "current_price" not in df.columns:
        raise ValueError("The uploaded file must contain a 'current_price' column.")

    return df


def clean_symbol(symbol):
    if symbol is None:
        return ""

    return str(symbol).strip().upper()


def update_prices_from_file(file_storage, uploaded_by=None):
    """
    Updates investment prices from uploaded CSV/Excel file.

    Expected columns:
    - symbol
    - current_price
    - date optional
    """

    df = read_price_file(file_storage)

    updated_count = 0
    failed_count = 0
    skipped_count = 0

    results = []

    for index, row in df.iterrows():
        symbol = clean_symbol(row.get("symbol"))
        raw_price = row.get("current_price")

        if not symbol:
            failed_count += 1
            results.append({
                "symbol": "-",
                "status": "Failed",
                "message": "Missing symbol"
            })
            continue

        try:
            new_price = float(raw_price)
        except (TypeError, ValueError):
            failed_count += 1

            log = PriceUpdateLog(
                symbol=symbol,
                old_price=0,
                new_price=0,
                old_value=0,
                new_value=0,
                status="Failed",
                message="Invalid current_price value",
                uploaded_by=uploaded_by
            )

            db.session.add(log)

            results.append({
                "symbol": symbol,
                "status": "Failed",
                "message": "Invalid current_price value"
            })

            continue

        if new_price < 0:
            failed_count += 1

            log = PriceUpdateLog(
                symbol=symbol,
                old_price=0,
                new_price=new_price,
                old_value=0,
                new_value=0,
                status="Failed",
                message="Price cannot be negative",
                uploaded_by=uploaded_by
            )

            db.session.add(log)

            results.append({
                "symbol": symbol,
                "status": "Failed",
                "message": "Price cannot be negative"
            })

            continue

        investments = Investment.query.filter(
            Investment.symbol == symbol
        ).all()

        if not investments:
            skipped_count += 1

            log = PriceUpdateLog(
                symbol=symbol,
                old_price=0,
                new_price=new_price,
                old_value=0,
                new_value=0,
                status="Skipped",
                message="No investment found with this symbol",
                uploaded_by=uploaded_by
            )

            db.session.add(log)

            results.append({
                "symbol": symbol,
                "status": "Skipped",
                "message": "No investment found with this symbol"
            })

            continue

        # for investment in investments:
        #     old_price = investment.current_price or 0
        #     old_value = investment.calculate_current_value()

        #     investment.current_price = new_price

        #     if investment.units and investment.units > 0:
        #         investment.current_value = investment.units * new_price
        #     else:
        #         investment.current_value = new_price

        #     investment.last_price_update = datetime.utcnow()

        #     new_value = investment.calculate_current_value()
            
        #     recorded_date = date.today()

        #     if "date" in df.columns and row.get("date") is not None:
        #         try:
        #             recorded_date = pd.to_datetime(row.get("date")).date()
        #         except Exception:
        #             recorded_date = date.today()

        #     price_history = PriceHistory(
        #         investment_id=investment.id,
        #         symbol=symbol,
        #         price=new_price,
        #         value=new_value,
        #         recorded_date=recorded_date,
        #         source="Upload"
        #     )

        #     db.session.add(price_history)


        #     log = PriceUpdateLog(
        #         investment_id=investment.id,
        #         symbol=symbol,
        #         investment_name=investment.investment_name,
        #         old_price=old_price,
        #         new_price=new_price,
        #         old_value=old_value,
        #         new_value=new_value,
        #         status="Success",
        #         message="Price updated successfully",
        #         uploaded_by=uploaded_by
        #     )

        #     db.session.add(log)

        #     updated_count += 1

        #     results.append({
        #         "symbol": symbol,
        #         "investment": investment.investment_name,
        #         "status": "Success",
        #         "old_price": old_price,
        #         "new_price": new_price,
        #         "old_value": old_value,
        #         "new_value": new_value,
        #         "message": "Price updated successfully"
        #     })
        
        for investment in investments:
            old_price = investment.current_price or 0
            old_value = investment.calculate_current_value()

            investment.current_price = new_price

            if investment.units and investment.units > 0:
                investment.current_value = investment.units * new_price
            else:
                investment.current_value = new_price

            investment.last_price_update = datetime.utcnow()

            new_value = investment.calculate_current_value()

            recorded_date = date.today()

            if "date" in df.columns and row.get("date") is not None:
                try:
                    recorded_date = pd.to_datetime(row.get("date")).date()
                except Exception:
                    recorded_date = date.today()

            # price_history = PriceHistory(
            #     investment_id=investment.id,
            #     symbol=symbol,
            #     price=new_price,
            #     value=new_value,
            #     recorded_date=recorded_date,
            #     source="Upload"
            # )
            
            existing_history = PriceHistory.query.filter_by(
                investment_id=investment.id,
                recorded_date=recorded_date,
                source="Upload"
            ).first()

            if existing_history:
                existing_history.price = new_price
                existing_history.value = new_value
                existing_history.symbol = symbol
            else:
                price_history = PriceHistory(
                    investment_id=investment.id,
                    symbol=symbol,
                    price=new_price,
                    value=new_value,
                    recorded_date=recorded_date,
                    source="Upload"
                )

                db.session.add(price_history)

            # db.session.add(price_history)

            log = PriceUpdateLog(
                investment_id=investment.id,
                symbol=symbol,
                investment_name=investment.investment_name,
                old_price=old_price,
                new_price=new_price,
                old_value=old_value,
                new_value=new_value,
                status="Success",
                message="Price updated successfully",
                uploaded_by=uploaded_by
            )

            db.session.add(log)

            updated_count += 1

            results.append({
                "symbol": symbol,
                "investment": investment.investment_name,
                "status": "Success",
                "old_price": old_price,
                "new_price": new_price,
                "old_value": old_value,
                "new_value": new_value,
                "message": "Price updated successfully"
            })

    db.session.commit()

    return {
        "updated": updated_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results
    }
    
    
def fetch_nigerian_stock_price(symbol):
    """
    Replace this placeholder with a real NGX/broker/API price feed.

    Example expected return:
    {
        "symbol": "GTCO",
        "price": 45.20
    }
    """

    demo_prices = {
        "GTCO": 45.20,
        "ZENITHBANK": 42.75,
        "UBA": 34.10,
        "ACCESSCORP": 23.55,
        "MTNN": 240.00,
        "DANGCEM": 420.00,
        "SEPLAT": 3200.00
    }

    price = demo_prices.get(symbol.upper())

    if price is None:
        return None

    return {
        "symbol": symbol.upper(),
        "price": price
    }


def update_stock_prices():
    stocks = Investment.query.filter(
        Investment.investment_type == "Nigerian Stock",
        Investment.symbol.isnot(None)
    ).all()

    updated = 0
    failed = 0

    for stock in stocks:
        old_price = stock.current_price or 0
        result = fetch_nigerian_stock_price(stock.symbol)

        # if result:
        #     new_price = result["price"]

        #     stock.current_price = new_price
        #     stock.current_value = (stock.units or 0) * new_price
        #     stock.last_price_update = datetime.utcnow()

        #     log = PriceUpdateLog(
        #         symbol=stock.symbol,
        #         old_price=old_price,
        #         new_price=new_price,
        #         status="Success",
        #         message="Price updated successfully"
        #     )

        #     updated += 1
        if result:
            new_price = result["price"]

            stock.current_price = new_price
            stock.current_value = (stock.units or 0) * new_price
            stock.last_price_update = datetime.utcnow()

            price_history = PriceHistory(
                investment_id=stock.id,
                symbol=stock.symbol,
                price=new_price,
                value=stock.current_value,
                recorded_date=date.today(),
                source="Auto Update"
            )

            db.session.add(price_history)

            log = PriceUpdateLog(
                symbol=stock.symbol,
                old_price=old_price,
                new_price=new_price,
                status="Success",
                message="Price updated successfully"
            )

            updated += 1
    
        else:
            log = PriceUpdateLog(
                symbol=stock.symbol,
                old_price=old_price,
                new_price=old_price,
                status="Failed",
                message="Price not found"
            )

            failed += 1

        db.session.add(log)

    db.session.commit()

    return {
        "updated": updated,
        "failed": failed
    }



