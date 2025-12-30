# Fyers API Symbol Formats

## Common Symbol Formats

Based on Fyers API documentation, different instrument types use different symbol formats:

### 1. **Equity Stocks**
Format: `NSE:SYMBOL-EQ`

Examples:
- RELIANCE: `NSE:RELIANCE-EQ`
- INFY: `NSE:INFY-EQ`
- TCS: `NSE:TCS-EQ`

### 2. **ETFs (Exchange Traded Funds)**
Format: Usually `NSE:SYMBOL-EQ` (treated like equities)

Common ETFs:
- GOLDBEES: `NSE:GOLDBEES-EQ` ✅ **Current format**
- NIFTYBEES: `NSE:NIFTYBEES-EQ`
- LIQUIDBEES: `NSE:LIQUIDBEES-EQ`

Alternative formats to try if above doesn't work:
- `NSE:GOLDBEES` (without -EQ)
- Check if symbol name is different in Fyers (e.g., `GOLDIETF`)

### 3. **Indices**
Format: `NSE:INDEX NAME-INDEX`

Examples:
- NIFTY 50: `NSE:NIFTY 50-INDEX` ✅ **Current format**
- NIFTY BANK: `NSE:NIFTYBANK-INDEX`
- SENSEX: `BSE:SENSEX-INDEX`

**Important:** Index names may have spaces (e.g., "NIFTY 50" not "NIFTY50")

### 4. **Futures**
Format: `NSE:SYMBOL-FUTIDX` or `NSE:SYMBOL-FUTSTK`

### 5. **Options**
Format: `NSE:SYMBOL-OPTIDX` or `NSE:SYMBOL-OPTSTK`

## Troubleshooting

If a symbol is not fetching data:

1. **Check the exact symbol name in Fyers**
   - Login to Fyers web/app
   - Search for the symbol
   - Note the exact format shown

2. **Common issues:**
   - Extra spaces in index names
   - Wrong exchange (NSE vs BSE)
   - Symbol renamed or delisted
   - Wrong suffix (-EQ vs -INDEX)

3. **For GOLDBEES specifically:**
   - Try: `NSE:GOLDBEES-EQ` (most likely)
   - Try: `NSE:GOLDBEES`
   - Try: `BSE:GOLDBEES-EQ`
   - Verify it exists in Fyers symbol master

4. **For NIFTY50:**
   - Try: `NSE:NIFTY 50-INDEX` (with space)
   - Try: `NSE:NIFTY50-INDEX` (without space)
   - Try: `NSE:Nifty 50-INDEX` (capital N)

## How to Find Correct Symbol

Use Fyers Symbol Master API or web interface:
1. Login to Fyers
2. Go to Market Watch
3. Search for the symbol
4. Right-click → Copy Symbol
5. Use that exact format in the code

## Current Implementation

See `app.py` line 386-401 for symbol format logic.

The code currently uses:
- GOLDBEES → `NSE:GOLDBEES-EQ`
- NIFTY50 → `NSE:NIFTY 50-INDEX`

If these don't work, you need to verify the correct format from Fyers interface.
