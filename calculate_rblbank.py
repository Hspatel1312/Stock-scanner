import pandas as pd
import pickle
from datetime import datetime, timedelta
import pytz
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load the cached data
CACHE_FILE = "stock_data_cache.pkl"
TIMEZONE = pytz.timezone('Asia/Kolkata')

print("=" * 80)
print("RBLBANK Momentum Calculation for December 15, 2025 Rebalance")
print("=" * 80)

# Check if cache exists
try:
    with open(CACHE_FILE, "rb") as f:
        cached_data = pickle.load(f)
        stock_data = cached_data.get("data", {})

    if "RBLBANK" in stock_data:
        df = stock_data["RBLBANK"]
        print(f"\n✓ Found RBLBANK data in cache")
        print(f"  Data points: {len(df)}")
        print(f"  Date range: {df.index.min()} to {df.index.max()}")

        # Rebalance date logic
        print("\n" + "=" * 80)
        print("STEP 1: REBALANCE DATE CALCULATION")
        print("=" * 80)

        rebalance_date_input = datetime(2025, 12, 15)
        print(f"Input rebalance date: December 15, 2025")

        # In real code, this would check if it's a trading day
        # For now, assume Dec 15, 2025 is Monday (trading day)
        rebalance_date = rebalance_date_input
        print(f"✓ Rebalance Date: {rebalance_date.strftime('%B %d, %Y (%A)')}")

        # Data cutoff date (previous trading day)
        print("\n" + "=" * 80)
        print("STEP 2: DATA CUTOFF DATE")
        print("=" * 80)

        # Dec 15 is Monday, so previous trading day is Friday Dec 12
        data_cutoff_date = datetime(2025, 12, 12)
        print(f"Data Cutoff Date: {data_cutoff_date.strftime('%B %d, %Y (%A)')}")
        print(f"(Previous trading day before rebalance)")

        # Momentum calculation parameters
        print("\n" + "=" * 80)
        print("STEP 3: LOOKBACK PERIOD CALCULATION")
        print("=" * 80)

        lookback_period = 12  # months
        last_month_exclusion = 0

        print(f"Lookback period: {lookback_period} months")
        print(f"Last month exclusion: {last_month_exclusion} months")

        # Convert to pandas timestamp for calculation (with timezone)
        cutoff_ts = pd.Timestamp(data_cutoff_date, tz=TIMEZONE)

        # Calculate end date (FIXED: use DateOffset instead of MonthBegin)
        if last_month_exclusion == 0:
            end_date = cutoff_ts
        else:
            end_date = cutoff_ts - pd.DateOffset(months=last_month_exclusion)

        print(f"\nEnd Date Calculation:")
        if last_month_exclusion == 0:
            print(f"  No exclusion, end_date = cutoff_date")
        else:
            print(f"  {cutoff_ts.strftime('%B %d, %Y')} - {last_month_exclusion} months")
        print(f"  = {end_date.strftime('%B %d, %Y')}")

        # Find closest available end date in data
        all_dates = df.index
        if end_date not in all_dates:
            previous_dates = all_dates[all_dates <= end_date]
            if len(previous_dates) > 0:
                end_date_actual = previous_dates[-1]
                print(f"  Closest available date: {end_date_actual.strftime('%B %d, %Y')}")
            else:
                print("  ERROR: No data available before end date")
                end_date_actual = None
        else:
            end_date_actual = end_date
            print(f"  Exact date available: {end_date_actual.strftime('%B %d, %Y')}")

        if end_date_actual is not None:
            # Calculate start date (FIXED: go to month start, then find first trading day)
            target_month = end_date_actual - pd.DateOffset(months=lookback_period)
            month_start = target_month.replace(day=1)

            print(f"\nStart Date Calculation:")
            print(f"  {end_date_actual.strftime('%B %d, %Y')} - {lookback_period} months = {target_month.strftime('%B %d, %Y')}")
            print(f"  Month start: {month_start.strftime('%B %d, %Y')}")

            # Find first trading day on or after that month start
            if month_start not in all_dates:
                next_dates = all_dates[all_dates >= month_start]
                if len(next_dates) > 0:
                    start_date_actual = next_dates[0]
                    print(f"  First trading day on/after {month_start.strftime('%B %d')}: {start_date_actual.strftime('%B %d, %Y')}")
                else:
                    print("  ERROR: No data available after month start")
                    start_date_actual = None
            else:
                start_date_actual = month_start
                print(f"  Exact date available: {start_date_actual.strftime('%B %d, %Y')}")

            if start_date_actual is not None:
                # Get prices
                print("\n" + "=" * 80)
                print("STEP 4: PRICE DATA")
                print("=" * 80)

                start_price = df['close'].loc[start_date_actual]
                end_price = df['close'].loc[end_date_actual]

                print(f"\nStart Date: {start_date_actual.strftime('%B %d, %Y')}")
                print(f"Start Price: ₹{start_price:.2f}")
                print(f"\nEnd Date: {end_date_actual.strftime('%B %d, %Y')}")
                print(f"End Price: ₹{end_price:.2f}")

                # Calculate momentum
                print("\n" + "=" * 80)
                print("STEP 5: MOMENTUM CALCULATION")
                print("=" * 80)

                momentum = (end_price - start_price) / start_price
                print(f"\nMomentum = (End Price - Start Price) / Start Price")
                print(f"Momentum = ({end_price:.2f} - {start_price:.2f}) / {start_price:.2f}")
                print(f"Momentum = {momentum:.6f}")
                print(f"Momentum % = {momentum * 100:.2f}%")

                # Calculate volatility
                print("\n" + "=" * 80)
                print("STEP 6: VOLATILITY CALCULATION")
                print("=" * 80)

                subset = df.loc[start_date_actual:end_date_actual]
                print(f"Data points in lookback period: {len(subset)}")

                daily_returns = subset['close'].pct_change().dropna()
                volatility = daily_returns.std()

                print(f"\nDaily Returns calculated: {len(daily_returns)} values")
                print(f"Volatility (Std Dev of Daily Returns): {volatility:.6f}")

                # Calculate FITP
                print("\n" + "=" * 80)
                print("STEP 7: FITP CALCULATION")
                print("=" * 80)

                if momentum > 0:
                    fitp = (daily_returns > 0).mean()
                    print(f"Momentum is POSITIVE")
                    print(f"FITP = Fraction of days with positive returns")
                elif momentum < 0:
                    fitp = (daily_returns < 0).mean()
                    print(f"Momentum is NEGATIVE")
                    print(f"FITP = Fraction of days with negative returns")
                else:
                    fitp = 0.5
                    print(f"Momentum is ZERO")
                    print(f"FITP = 0.5 (neutral)")

                print(f"FITP = {fitp:.6f}")

                # Calculate score (volatility strategy)
                print("\n" + "=" * 80)
                print("STEP 8: SCORE CALCULATION (VOLATILITY STRATEGY)")
                print("=" * 80)

                if volatility > 0:
                    score = momentum / volatility
                    print(f"Score = Momentum / Volatility")
                    print(f"Score = {momentum:.6f} / {volatility:.6f}")
                    print(f"Score = {score:.6f}")
                else:
                    print(f"Volatility is zero, cannot calculate score")
                    score = None

                # Summary
                print("\n" + "=" * 80)
                print("FINAL SUMMARY - RBLBANK")
                print("=" * 80)
                score_str = f"{score:.6f}" if score else "N/A"
                print(f"""
Rebalance Date:       {rebalance_date.strftime('%B %d, %Y (%A)')}
Data Cutoff Date:     {data_cutoff_date.strftime('%B %d, %Y (%A)')}

Lookback Period:      {lookback_period} months
Start Date:           {start_date_actual.strftime('%B %d, %Y')}
End Date:             {end_date_actual.strftime('%B %d, %Y')}
Trading Days:         {len(subset)} days

Start Price:          ₹{start_price:.2f}
End Price:            ₹{end_price:.2f}
Price Change:         ₹{end_price - start_price:.2f}

Momentum:             {momentum:.6f} ({momentum * 100:.2f}%)
Volatility:           {volatility:.6f}
FITP:                 {fitp:.6f}
Score (Vol Strategy): {score_str}
""")

    else:
        print(f"\n✗ RBLBANK not found in cache")
        print(f"Available symbols: {list(stock_data.keys())[:10]}...")

except FileNotFoundError:
    print(f"\n✗ Cache file not found: {CACHE_FILE}")
    print("Please run the stock scanner first to generate cached data")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
