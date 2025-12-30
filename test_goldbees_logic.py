import pandas as pd
import pytz
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

TIMEZONE = pytz.timezone('Asia/Kolkata')

print("=" * 80)
print("GOLDBEES vs NIFTY50 3-Month Allocation Logic Test")
print("=" * 80)
print()

# Test the 3-month calculation logic
cutoff_date = pd.Timestamp('2025-12-12', tz=TIMEZONE)

print(f"Cutoff Date: {cutoff_date.strftime('%B %d, %Y')}")
print()

# Calculate 3-month lookback dates
lookback_period = 3
last_month_exclusion = 0

print("=== 3-Month Lookback Calculation ===")
print(f"Lookback period: {lookback_period} months")
print(f"Last month exclusion: {last_month_exclusion}")
print()

# End date calculation
if last_month_exclusion == 0:
    end_date = cutoff_date
else:
    end_date = cutoff_date - pd.DateOffset(months=last_month_exclusion)

print(f"End Date: {end_date.strftime('%B %d, %Y')}")
print()

# Start date calculation (go back 3 months to month start)
target_month = end_date - pd.DateOffset(months=lookback_period)
month_start = target_month.replace(day=1)

print(f"Target Month (3 months back): {target_month.strftime('%B %d, %Y')}")
print(f"Month Start: {month_start.strftime('%B %d, %Y')}")
print()

print("Expected for Dec 12, 2025:")
print("  End Date: December 12, 2025")
print("  Start Date: September 1, 2025 (or first trading day after)")
print()

print("=== Logic Summary ===")
print("1. Calculate GOLDBEES 3-month return (Sep 1 to Dec 12)")
print("2. Calculate NIFTY50 3-month return (Sep 1 to Dec 12)")
print("3. If GOLDBEES > NIFTY50:")
print("   - Add GOLDBEES to final stock selection")
print("   - Allocation: 50% Gold / 50% Equity")
print("4. If NIFTY50 > GOLDBEES:")
print("   - Don't add GOLDBEES")
print("   - Allocation: 100% Equity")
print()

# Example calculation
print("=== Example ===")
print("Suppose:")
print("  GOLDBEES 3-month return: 14.96%")
print("  NIFTY50 3-month return: 4.52%")
print()
print("Decision: 14.96% > 4.52%")
print("Result: ADD GOLDBEES to selection (50% Gold / 50% Equity)")
print()

print("=" * 80)
print("The logic has been added to app.py at lines 598-656")
print("=" * 80)
