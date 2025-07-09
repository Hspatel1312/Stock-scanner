import streamlit as st
import pandas as pd
import pickle
import os
import time
from datetime import datetime
import pytz
from fyers_apiv3 import fyersModel
from typing import Dict, List, Optional, Tuple
import requests

# Configure the page
st.set_page_config(
    page_title="Fyers Stock Scanner",
    page_icon="📈",
    layout="wide"
)

# Configuration
FYERS_CONFIG = {
    "client_id": "F5ZQTMKTTH-100",
    "secret_key": "KDHZZYT6FW",
    "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/index.html"
}

# Default file paths (you can modify these)
STOCK_LIST_FILE = "ind_niftysmallcap250list.csv"
CACHE_FILE = "stock_data_cache.pkl"

# Timezone
tz = pytz.timezone('Asia/Kolkata')

class StockScanner:
    def __init__(self):
        self.fyers = None
        self.cached_data = None
        
    def authenticate_fyers(self, auth_code: str) -> bool:
        """Authenticate with Fyers using auth code"""
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
                
                # Test the token
                profile = self.fyers.get_profile()
                if profile.get("s") == "ok":
                    return True
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
            chunk_days = 365
            
            current = end_date
            while current >= start_date:
                chunk_start = max(start_date, current - pd.Timedelta(days=chunk_days - 1))
                
                response = self.fyers.history({
                    "symbol": f"NSE:{symbol}-EQ",
                    "resolution": "D",
                    "date_format": 1,
                    "range_from": chunk_start.strftime("%Y-%m-%d"),
                    "range_to": current.strftime("%Y-%m-%d"),
                    "cont_flag": "1"
                })
                
                if response["s"] == "ok":
                    candles = response.get("candles", [])
                    all_data.extend(candles)
                    
                current = chunk_start - pd.Timedelta(days=1)
                time.sleep(0.5)  # Rate limiting
            
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
    
    def calculate_momentum_volatility_fitp(self, df: pd.DataFrame, date: pd.Timestamp, 
                                          lookback_period: int = 12, last_month_exclusion: int = 0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate momentum, volatility, and FITP"""
        try:
            all_dates = df.index
            end_date = date - pd.offsets.MonthBegin(last_month_exclusion)
            if end_date not in all_dates:
                previous_dates = all_dates[all_dates <= end_date]
                if len(previous_dates) == 0:
                    return None, None, None
                end_date = previous_dates[-1]
            end_price = df['close'].loc[end_date]
        
            start_date = end_date - pd.offsets.MonthBegin(lookback_period)
            if start_date not in all_dates:
                previous_dates = all_dates[all_dates <= start_date]
                if len(previous_dates) == 0:
                    return None, None, None
                start_date = previous_dates[-1]
        
            if start_date >= end_date:
                return None, None, None
        
            subset = df.loc[start_date:end_date]
            if len(subset) < 2:
                return None, None, None
        
            start_price = df['close'].loc[start_date]
            momentum = (end_price - start_price) / start_price
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
    
    def scan_stocks(self, symbols: List[str], strategy: str = "volatility", num_stocks: int = 20, 
                   lookback_period: int = 12, last_month_exclusion: int = 0) -> List[Tuple[str, float, float, float, float]]:
        """Scan and rank stocks based on momentum strategy"""
        if not self.fyers:
            st.error("Fyers not authenticated!")
            return []
        
        scores = []
        date = pd.Timestamp.now(tz).normalize()
        
        # Check cache first
        cache_valid = False
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached_data = pickle.load(f)
                    cache_date = pd.Timestamp(cached_data["timestamp"], tz="Asia/Kolkata").normalize()
                    if cache_date == date:
                        self.cached_data = cached_data["data"]
                        cache_valid = True
                        st.success("Using cached data from today")
            except:
                pass
        
        if not cache_valid:
            st.info("Fetching fresh data... This may take a few minutes.")
            # Fetch historical data
            end = date
            start = end - pd.Timedelta(days=730)
            hist_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, symbol in enumerate(symbols):
                status_text.text(f"Fetching data for {symbol} ({i+1}/{len(symbols)})")
                df = self.fetch_historical_data(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                hist_data[symbol] = df
                progress_bar.progress((i + 1) / len(symbols))
            
            self.cached_data = hist_data
            
            # Save cache
            try:
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump({"data": hist_data, "timestamp": date.strftime("%Y-%m-%d")}, f)
                st.success("Data cached successfully")
            except Exception as e:
                st.warning(f"Could not save cache: {str(e)}")
        
        # Calculate scores
        st.info("Calculating momentum scores...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(symbols):
            status_text.text(f"Analyzing {symbol} ({i+1}/{len(symbols)})")
            df = self.cached_data.get(symbol, pd.DataFrame())
            
            if df.empty:
                continue
            
            momentum, volatility, fitp = self.calculate_momentum_volatility_fitp(
                df, date, lookback_period, last_month_exclusion
            )
            
            if momentum is not None:
                if strategy == 'volatility' and volatility is not None and volatility > 0:
                    score = momentum / volatility
                elif strategy == 'fitp' and fitp is not None:
                    score = momentum * fitp
                else:
                    score = momentum
                scores.append((symbol, momentum, volatility, fitp, score))
            
            progress_bar.progress((i + 1) / len(symbols))
        
        # Sort and return top stocks
        sorted_scores = sorted(scores, key=lambda x: x[4], reverse=True)[:num_stocks]
        return sorted_scores

def main():
    st.title("📈 Fyers Stock Scanner")
    st.write("Authenticate with Fyers and scan stocks using momentum strategies")
    
    # Initialize scanner
    if 'scanner' not in st.session_state:
        st.session_state.scanner = StockScanner()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Authentication section
        st.subheader("🔐 Fyers Authentication")
        
        # Show authentication link
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={FYERS_CONFIG['client_id']}&redirect_uri={FYERS_CONFIG['redirect_uri']}&response_type=code&state=None"
        st.markdown(f"**Step 1:** [Get Authorization Code]({auth_url})")
        
        # Auth code input
        auth_code = st.text_input(
            "**Step 2:** Enter Authorization Code:",
            type="password",
            help="Paste the authorization code from the Fyers authentication page"
        )
        
        if st.button("🔑 Authenticate"):
            if auth_code:
                with st.spinner("Authenticating..."):
                    if st.session_state.scanner.authenticate_fyers(auth_code):
                        st.success("✅ Authentication successful!")
                        st.session_state.authenticated = True
                    else:
                        st.error("❌ Authentication failed!")
                        st.session_state.authenticated = False
            else:
                st.warning("Please enter authorization code")
        
        # Scanner parameters
        st.subheader("📊 Scanner Parameters")
        strategy = st.selectbox("Strategy:", ["volatility", "fitp", "momentum"])
        num_stocks = st.slider("Number of stocks:", 5, 50, 20)
        lookback_period = st.slider("Lookback period (months):", 3, 24, 12)
        last_month_exclusion = st.slider("Last month exclusion:", 0, 3, 0)
    
    # Main content
    if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
        st.info("👆 Please authenticate with Fyers using the sidebar first")
        
        # Show sample stock list format
        st.subheader("📋 Stock List Format")
        st.write("Your stock list CSV should have a 'Symbol' column with stock symbols:")
        sample_df = pd.DataFrame({
            "Symbol": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
            "Company Name": ["Reliance Industries", "Tata Consultancy Services", "Infosys", "HDFC Bank", "ICICI Bank"]
        })
        st.dataframe(sample_df)
        
    else:
        # File upload
        st.subheader("📁 Upload Stock List")
        uploaded_file = st.file_uploader(
            "Choose CSV file with stock symbols",
            type="csv",
            help="Upload a CSV file with a 'Symbol' column containing stock symbols"
        )
        
        # Use sample stocks if no file uploaded
        if uploaded_file is None:
            st.info("No file uploaded. Using sample stock list.")
            symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", 
                      "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "ASIANPAINT",
                      "MARUTI", "BAJFINANCE", "HCLTECH", "KOTAKBANK", "LT",
                      "WIPRO", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID"]
        else:
            try:
                df = pd.read_csv(uploaded_file)
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                    st.success(f"✅ Loaded {len(symbols)} symbols from file")
                else:
                    st.error("❌ CSV file must have a 'Symbol' column")
                    symbols = []
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                symbols = []
        
        # Scan button
        if symbols and st.button("🔍 Scan Stocks", type="primary"):
            try:
                results = st.session_state.scanner.scan_stocks(
                    symbols=symbols,
                    strategy=strategy,
                    num_stocks=num_stocks,
                    lookback_period=lookback_period,
                    last_month_exclusion=last_month_exclusion
                )
                
                if results:
                    st.success(f"✅ Scan completed! Found {len(results)} stocks")
                    
                    # Display results
                    st.subheader("📊 Top Stocks")
                    
                    # Create DataFrame for display
                    results_df = pd.DataFrame(results, columns=[
                        "Symbol", "Momentum", "Volatility", "FITP", "Score"
                    ])
                    
                    # Format numbers
                    results_df["Momentum"] = results_df["Momentum"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                    results_df["Volatility"] = results_df["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                    results_df["FITP"] = results_df["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                    results_df["Score"] = results_df["Score"].apply(lambda x: f"{x:.4f}")
                    
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download button
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results",
                        data=csv,
                        file_name=f"stock_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Save to pickle
                    pickle_data = {
                        "results": results,
                        "timestamp": datetime.now().isoformat(),
                        "parameters": {
                            "strategy": strategy,
                            "num_stocks": num_stocks,
                            "lookback_period": lookback_period,
                            "last_month_exclusion": last_month_exclusion
                        }
                    }
                    
                    pickle_filename = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                    with open(pickle_filename, 'wb') as f:
                        pickle.dump(pickle_data, f)
                    
                    with open(pickle_filename, 'rb') as f:
                        st.download_button(
                            label="📥 Download Pickle File",
                            data=f.read(),
                            file_name=pickle_filename,
                            mime="application/octet-stream"
                        )
                    
                    # Clean up pickle file
                    try:
                        os.remove(pickle_filename)
                    except:
                        pass
                        
                else:
                    st.warning("⚠️ No stocks found matching the criteria")
                    
            except Exception as e:
                st.error(f"❌ Error during scan: {str(e)}")
        
        # Show current parameters
        if symbols:
            st.subheader("📋 Current Configuration")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Symbols:** {len(symbols)}")
                st.write(f"**Strategy:** {strategy}")
            with col2:
                st.write(f"**Top stocks:** {num_stocks}")
                st.write(f"**Lookback:** {lookback_period} months")

if __name__ == "__main__":
    main()