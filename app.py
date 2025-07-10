import streamlit as st
import pandas as pd
import pickle
import os
import time
from datetime import datetime, timedelta
import pytz
from fyers_apiv3 import fyersModel
from typing import Dict, List, Optional, Tuple
import requests

# ================================
# CONFIGURATION
# ================================

st.set_page_config(
    page_title="Fyers Stock Scanner Pro",
    page_icon="📈",
    layout="wide"
)

FYERS_CONFIG = {
    "client_id": "F5ZQTMKTTH-100",
    "secret_key": st.secrets.get("FYERS_SECRET_KEY", "KDHZZYT6FW"),
    "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/index.html"
}

TIMEZONE = pytz.timezone('Asia/Kolkata')
CACHE_FILE = "stock_data_cache.pkl"

# Market holidays for 2025
HOLIDAYS_2025 = [
    "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
    "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
    "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
    "2025-11-05", "2025-12-25"
]

# Nifty SmallCap 250 symbols (exactly 250 from your CSV)
NIFTY_SMALLCAP_250 = [
    "360ONE", "AADHARHFC", "AARTIIND", "AAVAS", "ACE", "ABREL", "ABSLAMC", "AEGISLOG", "AFFLE", "AKUMS",
    "APLLTD", "ALKYLAMINE", "ALOKINDS", "ARE&M", "AMBER", "ANANDRATHI", "ANANTRAJ", "ANGELONE", "APARINDS", "APTUS",
    "ACI", "ASAHIINDIA", "ASTERDM", "ASTRAZEN", "ATUL", "AVANTIFEED", "BASF", "BEML", "BLS", "BALAMINES",
    "BALRAMCHIN", "BATAINDIA", "BIKAJI", "BIRLACORPN", "BSOFT", "BLUEDART", "BLUESTARCO", "BBTC", "BRIGADE", "MAPMYINDIA",
    "CCL", "CESC", "CIEINDIA", "CAMPUS", "CANFINHOME", "CAPLIPOINT", "CGCL", "CASTROLIND", "CEATLTD", "CELLO",
    "CENTRALBK", "CDSL", "CENTURYPLY", "CERA", "CHALET", "CHAMBLFERT", "CHEMPLASTS", "CHENNPETRO", "CHOLAHLDNG", "CUB",
    "CLEAN", "CAMS", "CONCORDBIO", "CRAFTSMAN", "CREDITACC", "CROMPTON", "CYIENT", "DOMS", "DATAPATTNS", "DEEPAKFERT",
    "DEVYANI", "LALPATHLAB", "EIDPARRY", "EIHOTEL", "EASEMYTRIP", "ELECON", "ELGIEQUIP", "EMCURE", "ENGINERSIN", "EQUITASBNK",
    "ERIS", "FINEORG", "FINCABLES", "FINPIPE", "FSL", "FIVESTAR", "GRINFRA", "GVT&D", "GRSE", "GILLETTE",
    "GLENMARK", "GODIGIT", "GPIL", "GODFRYPHLP", "GODREJAGRO", "GRANULES", "GRAPHITE", "GESHIP", "GAEL", "GMDCLTD",
    "GNFC", "GPPL", "GSFC", "GSPL", "HEG", "HBLENGINE", "HFCL", "HAPPSTMNDS", "HSCL", "HINDCOPPER",
    "HOMEFIRST", "HONASA", "ISEC", "IFCI", "IIFL", "INOXINDIA", "IRCON", "ITI", "INDGN", "INDIACEM",
    "INDIAMART", "IEX", "INOXWIND", "INTELLECT", "JBCHEPHARM", "JBMA", "JKLAKSHMI", "JKTYRE", "JMFINANCIL", "JPPOWER",
    "J&KBANK", "JINDALSAW", "JUBLINGREA", "JUBLPHARMA", "JWL", "JUSTDIAL", "JYOTHYLAB", "JYOTICNC", "KNRCON", "KSB",
    "KAJARIACER", "KPIL", "KANSAINER", "KARURVYSYA", "KAYNES", "KEC", "KFINTECH", "KIRLOSBROS", "KIRLOSENG", "KIMS",
    "LATENTVIEW", "LAURUSLABS", "LEMONTREE", "MMTC", "MGL", "MAHSEAMLES", "MAHLIFE", "MANAPPURAM", "MASTEK", "METROPOLIS",
    "MINDACORP", "MOTILALOFS", "MCX", "NATCOPHARM", "NBCC", "NCC", "NSLNISP", "NH", "NATIONALUM", "NAVINFLUOR",
    "NETWEB", "NETWORK18", "NEWGEN", "NUVAMA", "NUVOCO", "OLECTRA", "PCBL", "PNBHOUSING", "PNCINFRA", "PTCIL",
    "PVRINOX", "PFIZER", "PEL", "PPLPHARMA", "POLYMED", "PRAJIND", "QUESS", "RRKABEL", "RBLBANK", "RHIM",
    "RITES", "RADICO", "RAILTEL", "RAINBOW", "RAJESHEXPO", "RKFORGE", "RCF", "RATNAMANI", "RTNINDIA", "RAYMOND",
    "REDINGTON", "ROUTE", "SBFC", "SAMMAANCAP", "SANOFI", "SAPPHIRE", "SAREGAMA", "SCHNEIDER", "SCI", "RENUKA",
    "SHYAMMETL", "SIGNATURE", "SOBHA", "SONATSOFTW", "SWSOLAR", "SUMICHEM", "SPARC", "SUVENPHAR", "SWANENERGY", "SYRMA",
    "TBOTEK", "TVSSCS", "TANLA", "TTML", "TECHNOE", "TEJASNET", "RAMCOCEM", "TITAGARH", "TRIDENT", "TRIVENI",
    "TRITURBINE", "UCOBANK", "UTIAMC", "UJJIVANSFB", "USHAMART", "VGUARD", "VIPIND", "DBREALTY", "VTL", "VARROC",
    "MANYAVAR", "VIJAYA", "VINATIORGA", "WELCORP", "WELSPUNLIV", "WESTLIFE", "WHIRLPOOL", "ZEEL", "ZENSARTECH", "ECLERX"
]

# ================================
# UTILITY FUNCTIONS
# ================================

def get_holidays() -> set:
    """Get market holidays as date objects"""
    return set(pd.to_datetime(HOLIDAYS_2025).date)

def is_trading_day(date: datetime) -> bool:
    """Check if a given date is a trading day"""
    holidays = get_holidays()
    return date.weekday() < 5 and date.date() not in holidays

def get_previous_trading_day(date: datetime) -> datetime:
    """Get the previous trading day"""
    prev_day = date - timedelta(days=1)
    while not is_trading_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day

def get_rebalance_dates(num_dates: int = 6) -> List[Dict]:
    """Get upcoming rebalance dates"""
    rebalance_dates = []
    current_date = datetime.now(TIMEZONE).replace(day=1)
    
    for _ in range(num_dates):
        # First trading day of month
        first_day = current_date.replace(day=1)
        while not is_trading_day(first_day):
            first_day += timedelta(days=1)
        
        data_cutoff = get_previous_trading_day(first_day)
        rebalance_dates.append({
            "rebalance_date": first_day,
            "data_cutoff_date": data_cutoff,
            "type": "Month Start"
        })
        
        # 15th of month (or next trading day)
        mid_month = current_date.replace(day=15)
        while not is_trading_day(mid_month):
            mid_month += timedelta(days=1)
        
        data_cutoff = get_previous_trading_day(mid_month)
        rebalance_dates.append({
            "rebalance_date": mid_month,
            "data_cutoff_date": data_cutoff,
            "type": "Mid Month"
        })
        
        # Next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return sorted(rebalance_dates, key=lambda x: x['rebalance_date'])

# ================================
# STOCK SCANNER CLASS
# ================================

class StockScanner:
    def __init__(self):
        self.fyers = None
        self.cached_data = None
    
    def authenticate_fyers(self, auth_code: str) -> bool:
        """Authenticate with Fyers"""
        try:
            session = fyersModel.SessionModel(
                client_id=FYERS_CONFIG["client_id"],
                secret_key=FYERS_CONFIG["secret_key"],
                redirect_uri=FYERS_CONFIG["redirect_uri"],
                response_type="code",
                grant_type="authorization_code"
            )
            session.set_token(auth_code)
            token_response = session.generate_token()
            token = token_response.get("access_token")
            
            if token:
                self.fyers = fyersModel.FyersModel(
                    client_id=FYERS_CONFIG["client_id"],
                    token=token,
                    is_async=False
                )
                
                profile = self.fyers.get_profile()
                return profile.get("s") == "ok"
            return False
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def fetch_historical_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch historical data for a symbol"""
        try:
            all_data = []
            start_date = pd.Timestamp(start)
            end_date = pd.Timestamp(end)
            
            current = end_date
            while current >= start_date:
                chunk_start = max(start_date, current - pd.Timedelta(days=365))
                
                response = self.fyers.history({
                    "symbol": f"NSE:{symbol}-EQ",
                    "resolution": "D",
                    "date_format": 1,
                    "range_from": chunk_start.strftime("%Y-%m-%d"),
                    "range_to": current.strftime("%Y-%m-%d"),
                    "cont_flag": "1"
                })
                
                if response["s"] == "ok":
                    all_data.extend(response.get("candles", []))
                
                current = chunk_start - pd.Timedelta(days=1)
                time.sleep(0.5)
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
            df = df.set_index("timestamp").sort_index()
            df.index = df.index.normalize()
            return df
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_metrics(self, df: pd.DataFrame, cutoff_date: datetime, lookback_months: int = 12) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate momentum, volatility, and FITP"""
        try:
            all_dates = df.index
            
            # End date
            end_date = cutoff_date
            if end_date not in all_dates:
                previous_dates = all_dates[all_dates <= end_date]
                if len(previous_dates) == 0:
                    return None, None, None
                end_date = previous_dates[-1]
            
            # Start date
            start_date = end_date - pd.offsets.MonthBegin(lookback_months)
            if start_date not in all_dates:
                previous_dates = all_dates[all_dates <= start_date]
                if len(previous_dates) == 0:
                    return None, None, None
                start_date = previous_dates[-1]
            
            if start_date >= end_date:
                return None, None, None
            
            # Calculate metrics
            start_price = df['close'].loc[start_date]
            end_price = df['close'].loc[end_date]
            momentum = (end_price - start_price) / start_price
            
            subset = df.loc[start_date:end_date]
            daily_returns = subset['close'].pct_change().dropna()
            
            if len(daily_returns) < 1:
                return momentum, None, None
            
            volatility = daily_returns.std()
            
            if momentum > 0:
                fitp = (daily_returns > 0).mean()
            elif momentum < 0:
                fitp = (daily_returns < 0).mean()
            else:
                fitp = 0.5
            
            return momentum, volatility, fitp
            
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
            return None, None, None
    
    def scan_stocks(self, symbols: List[str], cutoff_date: datetime, strategy: str = "volatility", 
                   num_stocks: int = 20, lookback_months: int = 12) -> List[Tuple[str, float, float, float, float]]:
        """Scan and rank stocks"""
        if not self.fyers:
            st.error("Please authenticate with Fyers first!")
            return []
        
        # Check cache
        cache_key = f"{cutoff_date.strftime('%Y-%m-%d')}_{strategy}_{lookback_months}"
        cache_valid = False
        
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached_data = pickle.load(f)
                    if cached_data.get("cache_key") == cache_key:
                        self.cached_data = cached_data["data"]
                        cache_valid = True
                        st.success("✅ Using cached data")
            except:
                pass
        
        # Fetch data if not cached
        if not cache_valid:
            st.info("📊 Fetching fresh data...")
            hist_data = {}
            progress_bar = st.progress(0)
            
            for i, symbol in enumerate(symbols):
                st.text(f"Fetching {symbol} ({i+1}/{len(symbols)})")
                start_date = (cutoff_date - pd.Timedelta(days=730)).strftime("%Y-%m-%d")
                end_date = cutoff_date.strftime("%Y-%m-%d")
                hist_data[symbol] = self.fetch_historical_data(symbol, start_date, end_date)
                progress_bar.progress((i + 1) / len(symbols))
            
            self.cached_data = hist_data
            
            # Save cache
            try:
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump({"cache_key": cache_key, "data": hist_data}, f)
            except Exception as e:
                st.warning(f"Could not save cache: {str(e)}")
        
        # Calculate scores
        st.info("🧮 Calculating momentum scores...")
        scores = []
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(symbols):
            df = self.cached_data.get(symbol, pd.DataFrame())
            if df.empty:
                continue
            
            momentum, volatility, fitp = self.calculate_metrics(df, cutoff_date, lookback_months)
            
            if momentum is not None:
                if strategy == 'volatility' and volatility is not None and volatility > 0:
                    score = momentum / volatility
                elif strategy == 'fitp' and fitp is not None:
                    score = momentum * fitp
                else:
                    score = momentum
                
                scores.append((symbol, momentum, volatility, fitp, score))
            
            progress_bar.progress((i + 1) / len(symbols))
        
        # Return top stocks
        return sorted(scores, key=lambda x: x[4], reverse=True)[:num_stocks]

# ================================
# USER INTERFACE
# ================================

def main():
    st.title("🚀 Fyers Stock Scanner Pro")
    st.markdown("### Advanced momentum-based stock screening")
    
    # Initialize scanner
    if 'scanner' not in st.session_state:
        st.session_state.scanner = StockScanner()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Settings")
        
        # Authentication
        st.subheader("🔐 Authentication")
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={FYERS_CONFIG['client_id']}&redirect_uri={FYERS_CONFIG['redirect_uri']}&response_type=code&state=None"
        st.markdown(f"[Get Auth Code]({auth_url})")
        
        auth_code = st.text_input("Authorization Code:", type="password")
        
        if st.button("🔑 Authenticate"):
            if auth_code:
                if st.session_state.scanner.authenticate_fyers(auth_code):
                    st.success("✅ Authenticated!")
                    st.session_state.authenticated = True
                else:
                    st.error("❌ Authentication failed!")
            else:
                st.warning("Please enter auth code")
        
        # Parameters
        st.subheader("📊 Parameters")
        strategy = st.selectbox("Strategy:", ["volatility", "fitp", "momentum"])
        num_stocks = st.slider("Top stocks:", 5, 50, 20)
        lookback_months = st.slider("Lookback (months):", 3, 24, 12)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📈 Scanner", "📅 Calendar", "ℹ️ About"])
    
    with tab1:
        if not hasattr(st.session_state, 'authenticated'):
            st.info("👈 Please authenticate with Fyers first")
            return
        
        # Rebalance date selection
        st.subheader("📅 Select Rebalance Date")
        rebalance_dates = get_rebalance_dates(6)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_idx = st.selectbox(
                "Rebalance Date:",
                range(len(rebalance_dates)),
                format_func=lambda x: f"{rebalance_dates[x]['rebalance_date'].strftime('%Y-%m-%d')} ({rebalance_dates[x]['type']})"
            )
        
        with col2:
            if selected_idx is not None:
                selected_date = rebalance_dates[selected_idx]
                cutoff_date = selected_date['data_cutoff_date']
                lookback_start = cutoff_date - pd.DateOffset(months=lookback_months)
                
                st.info(f"""
                **Data Cutoff:** {cutoff_date.strftime('%Y-%m-%d')}  
                **Lookback:** {lookback_start.strftime('%Y-%m-%d')} to {cutoff_date.strftime('%Y-%m-%d')}  
                **Period:** {lookback_months} months
                """)
        
        # Stock selection
        st.subheader("📁 Stock Universe")
        stock_option = st.radio(
            "Choose stocks:",
            ["📈 Nifty SmallCap 250", "📁 Upload CSV", "✏️ Manual Entry"]
        )
        
        if stock_option == "📈 Nifty SmallCap 250":
            symbols = NIFTY_SMALLCAP_250
            st.success(f"✅ Using {len(symbols)} stocks from Nifty SmallCap 250")
            
        elif stock_option == "📁 Upload CSV":
            uploaded_file = st.file_uploader("Upload CSV with 'Symbol' column", type="csv")
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                    st.success(f"✅ Loaded {len(symbols)} symbols")
                else:
                    st.error("CSV must have 'Symbol' column")
                    symbols = NIFTY_SMALLCAP_250[:20]
            else:
                symbols = NIFTY_SMALLCAP_250[:20]
                
        else:  # Manual entry
            manual_input = st.text_area("Enter symbols (comma-separated):", "RELIANCE,TCS,INFY")
            symbols = [s.strip().upper() for s in manual_input.split(",") if s.strip()]
            st.info(f"Ready to scan {len(symbols)} symbols")
        
        # Scan button
        if st.button("🔍 Start Scan", type="primary"):
            if selected_idx is not None:
                selected_date = rebalance_dates[selected_idx]
                cutoff_date = selected_date['data_cutoff_date']
                
                st.warning("⚠️ Do not refresh during scanning!")
                
                results = st.session_state.scanner.scan_stocks(
                    symbols=symbols,
                    cutoff_date=cutoff_date,
                    strategy=strategy,
                    num_stocks=num_stocks,
                    lookback_months=lookback_months
                )
                
                if results:
                    st.success("✅ Scan completed!")
                    
                    # Display results
                    st.subheader("🏆 Top Momentum Stocks")
                    
                    df_results = pd.DataFrame(results, columns=["Symbol", "Momentum", "Volatility", "FITP", "Score"])
                    df_display = df_results.copy()
                    df_display["Momentum"] = df_display["Momentum"].apply(lambda x: f"{x:.4f}")
                    df_display["Volatility"] = df_display["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                    df_display["FITP"] = df_display["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                    df_display["Score"] = df_display["Score"].apply(lambda x: f"{x:.4f}")
                    df_display.index = range(1, len(df_display) + 1)
                    
                    st.dataframe(df_display, use_container_width=True)
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv_data = df_results.to_csv(index=False)
                        st.download_button("📥 Download CSV", csv_data, f"scan_{cutoff_date.strftime('%Y%m%d')}.csv")
                    
                    with col2:
                        df_results.to_csv("latest_results.csv", index=False)
                        with open("latest_results.csv", "rb") as f:
                            st.download_button("📤 GitHub Upload", f.read(), "latest_results.csv")
                    
                    with col3:
                        pickle_data = {"results": results, "timestamp": datetime.now().isoformat()}
                        pickle_file = f"results_{cutoff_date.strftime('%Y%m%d')}.pkl"
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(pickle_data, f)
                        with open(pickle_file, 'rb') as f:
                            st.download_button("📥 Pickle File", f.read(), pickle_file)
                        try:
                            os.remove(pickle_file)
                        except:
                            pass
                else:
                    st.warning("No stocks found matching criteria")
    
    with tab2:
        st.subheader("📅 Rebalance Calendar")
        
        rebalance_dates = get_rebalance_dates(12)
        df_calendar = pd.DataFrame(rebalance_dates)
        df_calendar['Rebalance Date'] = df_calendar['rebalance_date'].dt.strftime('%Y-%m-%d (%A)')
        df_calendar['Data Cutoff'] = df_calendar['data_cutoff_date'].dt.strftime('%Y-%m-%d (%A)')
        df_calendar['Days Until'] = (df_calendar['rebalance_date'] - datetime.now(TIMEZONE)).dt.days
        
        display_df = df_calendar[['type', 'Rebalance Date', 'Data Cutoff', 'Days Until']].copy()
        display_df.columns = ['Type', 'Rebalance Date', 'Data Cutoff', 'Days Until']
        display_df.index = range(1, len(display_df) + 1)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Holidays
        st.subheader("🎭 Market Holidays 2025")
        holidays = get_holidays()
        holidays_df = pd.DataFrame({
            'Date': [h.strftime('%Y-%m-%d (%A)') for h in sorted(holidays)],
            'Days from Today': [(h - datetime.now().date()).days for h in sorted(holidays)]
        })
        holidays_df.index = range(1, len(holidays_df) + 1)
        st.dataframe(holidays_df, use_container_width=True)
    
    with tab3:
        st.subheader("ℹ️ About")
        
        st.markdown("""
        ### 🎯 Purpose
        Advanced momentum-based stock screening with intelligent rebalance timing.
        
        ### 🔬 Methodology
        - **Momentum:** Price change over lookback period
        - **Volatility-Adjusted:** Momentum ÷ Volatility  
        - **FITP:** Fraction in Trend Period (consistency measure)
        
        ### 📊 Features
        - **250 Stock Universe:** Nifty SmallCap 250 index
        - **Smart Caching:** Avoids re-downloading data
        - **Holiday Awareness:** Proper trading day calculations
        - **Multiple Export Formats:** CSV, Pickle files
        
        ### 🚀 Usage
        1. Authenticate with Fyers
        2. Select rebalance date  
        3. Choose stock universe
        4. Configure parameters
        5. Run scan and download results
        
        ### 📈 Best Practices
        - Run 1-2 days before rebalance
        - Compare multiple strategies
        - Consider market conditions
        """)

if __name__ == "__main__":
    main()