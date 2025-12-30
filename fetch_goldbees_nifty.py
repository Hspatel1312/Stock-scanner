import pickle
import pandas as pd
import pytz
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

TIMEZONE = pytz.timezone('Asia/Kolkata')
CACHE_FILE = "stock_data_cache.pkl"

print("=" * 80)
print("GOLDBEES vs NIFTY50 - Real Data Analysis")
print("Rebalance Date: December 15, 2025")
print("=" * 80)
print()

# Load cache
try:
    with open(CACHE_FILE, "rb") as f:
        cached = pickle.load(f)
        data = cached.get('data', {})

    print(f"✓ Cache loaded: {len(data)} symbols available")
    print()

    # Check for GOLDBEES and NIFTY50
    has_goldbees = "GOLDBEES" in data
    has_nifty = "NIFTY50" in data

    print("=== Symbol Availability ===")
    print(f"GOLDBEES: {'✓ Available' if has_goldbees else '✗ NOT FOUND'}")
    print(f"NIFTY50: {'✓ Available' if has_nifty else '✗ NOT FOUND'}")
    print()

    if not has_goldbees and not has_nifty:
        print("Available symbols in cache:")
        print(f"  {list(data.keys())[:30]}")
        print()
        print("⚠️ Neither GOLDBEES nor NIFTY50 found in cache")
        print("These need to be fetched using Fyers API first")
        print()
        print("To add them:")
        print("1. Include 'GOLDBEES' and 'NIFTY50' in the stock universe")
        print("2. Run the scanner to fetch data")
        print("3. The data will be cached for future use")

    else:
        # Calculate 3-month returns
        cutoff_date = pd.Timestamp('2025-12-12', tz=TIMEZONE)
        lookback_period = 3

        print("=== 3-Month Calculation Parameters ===")
        print(f"Cutoff Date: {cutoff_date.strftime('%B %d, %Y')}")
        print(f"Lookback Period: {lookback_period} months")
        print()

        def calculate_3m_return(symbol, df, cutoff_date):
            """Calculate 3-month return using the same logic as app.py"""
            # End date = cutoff date
            end_date = cutoff_date

            # Find actual end date
            if end_date not in df.index:
                prev_dates = df.index[df.index <= end_date]
                if len(prev_dates) == 0:
                    return None, None, None, None
                end_date_actual = prev_dates[-1]
            else:
                end_date_actual = end_date

            # Start date: go back 3 months to month start
            target_month = end_date_actual - pd.DateOffset(months=3)
            month_start = target_month.replace(day=1)

            # Find first trading day on/after month start
            if month_start not in df.index:
                next_dates = df.index[df.index >= month_start]
                if len(next_dates) == 0:
                    return None, None, None, None
                start_date_actual = next_dates[0]
            else:
                start_date_actual = month_start

            # Get prices
            start_price = df['close'].loc[start_date_actual]
            end_price = df['close'].loc[end_date_actual]

            # Calculate return
            return_3m = (end_price - start_price) / start_price

            return start_date_actual, end_date_actual, start_price, end_price, return_3m

        results = {}

        if has_goldbees:
            print("=== GOLDBEES Analysis ===")
            gb_df = data["GOLDBEES"]
            print(f"Data points: {len(gb_df)}")
            print(f"Date range: {gb_df.index.min().strftime('%Y-%m-%d')} to {gb_df.index.max().strftime('%Y-%m-%d')}")

            start_date, end_date, start_price, end_price, return_3m = calculate_3m_return(
                "GOLDBEES", gb_df, cutoff_date
            )

            if return_3m is not None:
                results["GOLDBEES"] = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "start_price": start_price,
                    "end_price": end_price,
                    "return": return_3m
                }

                print(f"\nStart Date: {start_date.strftime('%B %d, %Y (%A)')}")
                print(f"Start Price: Rs.{start_price:.2f}")
                print(f"\nEnd Date: {end_date.strftime('%B %d, %Y (%A)')}")
                print(f"End Price: Rs.{end_price:.2f}")
                print(f"\n3-Month Return: {return_3m:.6f} ({return_3m*100:.2f}%)")
            else:
                print("✗ Could not calculate 3-month return")
            print()

        if has_nifty:
            print("=== NIFTY50 Analysis ===")
            nifty_df = data["NIFTY50"]
            print(f"Data points: {len(nifty_df)}")
            print(f"Date range: {nifty_df.index.min().strftime('%Y-%m-%d')} to {nifty_df.index.max().strftime('%Y-%m-%d')}")

            start_date, end_date, start_price, end_price, return_3m = calculate_3m_return(
                "NIFTY50", nifty_df, cutoff_date
            )

            if return_3m is not None:
                results["NIFTY50"] = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "start_price": start_price,
                    "end_price": end_price,
                    "return": return_3m
                }

                print(f"\nStart Date: {start_date.strftime('%B %d, %Y (%A)')}")
                print(f"Start Price: {start_price:.2f}")
                print(f"\nEnd Date: {end_date.strftime('%B %d, %Y (%A)')}")
                print(f"End Price: {end_price:.2f}")
                print(f"\n3-Month Return: {return_3m:.6f} ({return_3m*100:.2f}%)")
            else:
                print("✗ Could not calculate 3-month return")
            print()

        # Comparison
        if "GOLDBEES" in results and "NIFTY50" in results:
            print("=" * 80)
            print("ALLOCATION DECISION")
            print("=" * 80)
            print()

            gb_return = results["GOLDBEES"]["return"]
            nifty_return = results["NIFTY50"]["return"]

            print(f"GOLDBEES 3-Month Return: {gb_return*100:.2f}%")
            print(f"NIFTY50 3-Month Return:  {nifty_return*100:.2f}%")
            print()

            if gb_return > nifty_return:
                diff = gb_return - nifty_return
                print(f"✓ GOLDBEES OUTPERFORMED by {diff*100:.2f}%")
                print()
                print("DECISION: ADD GOLDBEES to stock selection")
                print("ALLOCATION: 50% Gold / 50% Equity")
            else:
                diff = nifty_return - gb_return
                print(f"✓ NIFTY50 OUTPERFORMED by {diff*100:.2f}%")
                print()
                print("DECISION: Do NOT add GOLDBEES")
                print("ALLOCATION: 100% Equity")

            print()
            print("=" * 80)

except FileNotFoundError:
    print(f"✗ Cache file not found: {CACHE_FILE}")
    print()
    print("Please run the stock scanner first to generate cached data")
    print("The scanner needs to fetch GOLDBEES and NIFTY50 data via Fyers API")

except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
