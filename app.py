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
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import subprocess
import json
from pathlib import Path

# Configure the page
st.set_page_config(
    page_title="🚀 Fyers Stock Scanner Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-container { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.9);
        margin-bottom: 0;
    }
    
    .status-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .status-success { border-left: 4px solid #10B981; background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%); }
    .status-warning { border-left: 4px solid #F59E0B; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); }
    .status-error { border-left: 4px solid #EF4444; background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%); }
    .status-info { border-left: 4px solid #3B82F6; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    .metric-value { font-size: 1.8rem; font-weight: 700; margin: 0.5rem 0; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .github-section {
        background: linear-gradient(135deg, #24292e 0%, #586069 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
FYERS_CONFIG = {
    "client_id": "F5ZQTMKTTH-100",
    "secret_key": "KDHZZYT6FW",
    "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/index.html"
}

CACHE_FILE = "stock_data_cache.pkl"
GITHUB_CSV_FILENAME = "nifty_smallcap_momentum_scan.csv"
TIMEZONE = pytz.timezone('Asia/Kolkata')

def get_repo_path():
    current = Path.cwd()
    if "/workspaces/" in str(current):
        codespaces_path = Path("/workspaces/Stock-scanner")
        if codespaces_path.exists() and (codespaces_path / ".git").exists():
            return str(codespaces_path)
    if (current / ".git").exists():
        return str(current)
    return str(current)

GITHUB_CONFIG = {
    "username": "Hspatel1312",
    "repo_name": "Stock-scanner",
    "data_repo_path": get_repo_path(),
    "data_folder": "data"
}

# Valid symbols based on your working code
VALID_NIFTY_SMALLCAP_SYMBOLS = [
    "AFFLE", "ASTERDM", "DEEPAKFERT", "ERIS", "FSL", "GLENMARK", "GOLDBEES", 
    "JMFINANCIL", "JUBLPHARMA", "KFINTECH", "KIMS", "LAURUSLABS", "NH", 
    "PCBL", "RADICO", "WELCORP", "REDINGTON", "SONATSOFTW", "TRIVENI", 
    "TRIDENT", "CYIENT", "CAMS", "METROPOLIS", "LEMONTREE", "MASTEK",
    "TANLA", "KAYNES", "RAINBOW", "CROMPTON", "VGUARD", "SOBHA",
    "MINDACORP", "NEWGEN", "ECLERX", "SYRMA", "AMBER", "APLLTD", 
    "CRAFTSMAN", "FINPIPE", "JYOTHYLAB", "MAPMYINDIA", "RATNAMANI",
    "AARTIIND", "AAVAS", "ALKYLAMINE", "ALOKINDS", "ANANDRATHI",
    "ANANTRAJ", "ANGELONE", "APARINDS", "APTUS", "ASAHIINDIA",
    "ATUL", "AVANTIFEED", "BASF", "BEML", "BLS", "BALAMINES",
    "BALRAMCHIN", "BATAINDIA", "BIKAJI", "BIRLACORPN", "BSOFT",
    "BLUEDART", "BLUESTARCO", "BBTC", "BRIGADE", "CCL", "CESC",
    "CIEINDIA", "CAMPUS", "CANFINHOME", "CAPLIPOINT", "CGCL",
    "CASTROLIND", "CEATLTD", "CELLO", "CENTRALBK", "CDSL",
    "CENTURYPLY", "CERA", "CHALET", "CHAMBLFERT", "CHEMPLASTS",
    "CHENNPETRO", "CHOLAHLDNG", "CUB", "CLEAN", "CONCORDBIO",
    "CREDITACC", "DOMS", "DATAPATTNS", "DEVYANI", "LALPATHLAB",
    "EIDPARRY", "EIHOTEL", "EASEMYTRIP", "ELECON", "ELGIEQUIP",
    "EMCURE", "ENGINERSIN", "EQUITASBNK", "FINEORG", "FINCABLES",
    "FIVESTAR", "GRINFRA", "GRSE", "GILLETTE", "GODIGIT", "GPIL",
    "GODFRYPHLP", "GODREJAGRO", "GRANULES", "GRAPHITE", "GSHIP",
    "GAEL", "GMDCLTD", "GNFC", "GPPL", "GSFC", "GSPL", "HEG",
    "HBLENGINE", "HFCL", "HAPPSTMNDS", "HSCL", "HINDCOPPER",
    "HOMEFIRST", "HONASA", "ISEC", "IFCI", "IIFL", "INOXINDIA",
    "IRCON", "ITI", "INDGN", "INDIACEM", "INDIAMART", "IEX",
    "INOXWIND", "INTELLECT", "JBCHEPHARM", "JBMA", "JKLAKSHMI",
    "JKTYRE", "JPPOWER", "JINDALSAW", "JUBLINGREA", "JWL",
    "JUSTDIAL", "JYOTICNC", "KNRCON", "KSB", "KAJARIACER",
    "KPIL", "KANSAINER", "KARURVYSYA", "KEC", "KIRLOSBROS",
    "KIRLOSENG", "LATENTVIEW", "MMTC", "MGL", "MAHSEAMLES",
    "MAHLIFE", "MANAPPURAM", "MOTILALOFS", "MCX", "NATCOPHARM",
    "NBCC", "NCC", "NSLNISP", "NATIONALUM", "NAVISFLUOR",
    "NETWEB", "NETWORK18", "NUVAMA", "NUVOCO", "OLECTRA",
    "PNBHOUSING", "PNCINFRA", "PTCIL", "PVRINOX", "PFIZER",
    "PEL", "PPLPHARMA", "POLYMED", "PRAJIND", "QUESS", "RRKABEL",
    "RBLBANK", "RHIM", "RITES", "RAILTEL", "RAJESHEXPO",
    "RKFORGE", "RCF", "RTNINDIA", "RAYMOND", "ROUTE", "SBFC",
    "SAMMAANCAP", "SANOFI", "SAPPHIRE", "SAREGAMA", "SCHNEIDER",
    "SCI", "RENUKA", "SHYAMMETL", "SIGNATURE", "SWSOLAR",
    "SUMICHEM", "SPARC", "SUVENPHAR", "SWANENERGY", "TBOTEK",
    "TVSSCS", "TTML", "TECHNOE", "TEJASNET", "RAMCOCEM",
    "TITAGARH", "TRITURBINE", "UCOBANK", "UTIAMC", "UJJIVANSFB",
    "USHAMART", "VIPIND", "DBREALTY", "VTL", "VARROC",
    "MANYAVAR", "VIJAYA", "VINATIORGA", "WELSPUNLIV", "WESTLIFE",
    "WHIRLPOOL", "ZEEL", "ZENSARTECH"
]

class GitHubIntegration:
    def __init__(self, repo_path=None, github_token=None):
        self.repo_path = Path(repo_path or GITHUB_CONFIG["data_repo_path"])
        self.data_folder = Path(self.repo_path) / GITHUB_CONFIG["data_folder"]
        self.username = GITHUB_CONFIG["username"]
        self.repo_name = GITHUB_CONFIG["repo_name"]
        self.github_token = github_token or os.getenv("GITHUB_TOKEN") or st.secrets.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token not provided or found in environment variable GITHUB_TOKEN or Streamlit secrets")
        self.ensure_repo_exists()

    def ensure_repo_exists(self):
        if not self.repo_path.exists():
            return False
        self.data_folder.mkdir(exist_ok=True)
        return True

    def push_csv_to_github(self, df, commit_message=None):
        try:
            if not self.ensure_repo_exists():
                return False, "Repository not found"

            csv_path = self.data_folder / GITHUB_CSV_FILENAME
            df.to_csv(csv_path, index=False)

            if commit_message is None:
                commit_message = f"Update momentum scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            original_cwd = Path.cwd()

            try:
                os.chdir(self.repo_path)

                # Configure Git user
                subprocess.run(["git", "config", "user.email", "app@example.com"], check=True, capture_output=True, timeout=10)
                subprocess.run(["git", "config", "user.name", "Scanner App"], check=True, capture_output=True, timeout=10)

                # Set up remote with authentication
                remote_url = f"https://{self.username}:{self.github_token}@github.com/{self.username}/{self.repo_name}.git"
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True, capture_output=True, timeout=10)

                # Stage the file
                subprocess.run(["git", "add", f"data/{GITHUB_CSV_FILENAME}"], check=True, capture_output=True, timeout=30)

                # Check if there are changes to commit
                diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True, timeout=30)
                if diff_result.returncode == 0:
                    return True, f"File {GITHUB_CSV_FILENAME} already up to date"

                # Commit and push
                subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, timeout=30)
                push_result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=60)

                if push_result.returncode == 0:
                    return True, f"Successfully updated {GITHUB_CSV_FILENAME}"
                else:
                    return False, f"Git push failed: {push_result.stderr}"

            except subprocess.CalledProcessError as e:
                return False, f"Git error: {e.stderr}"
            except Exception as e:
                return False, f"Error: {str(e)}"
            finally:
                os.chdir(original_cwd)

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_csv_url(self, raw=True):
        if raw:
            return f"https://raw.githubusercontent.com/{self.username}/{self.repo_name}/main/data/{GITHUB_CSV_FILENAME}"
        else:
            return f"https://github.com/{self.username}/{self.repo_name}/blob/main/data/{GITHUB_CSV_FILENAME}"

class EnhancedStockScanner:
    def __init__(self):
        self.fyers = None
        self.cached_data = None
        self.holidays = self.load_holidays()

    def load_holidays(self) -> set:
        default_holidays = [
            "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
            "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
            "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
            "2025-11-05", "2025-12-25"
        ]
        return set(pd.to_datetime(default_holidays).date)

    def is_cache_valid(self, cache_key: str, cache_timestamp: str) -> bool:
        """Check if cache is valid based on Indian timezone and date"""
        try:
            # Get current date in Indian timezone
            current_ist = datetime.now(TIMEZONE).date()
            
            # Parse cache timestamp
            cache_time = datetime.fromisoformat(cache_timestamp)
            cache_date = cache_time.date()
            
            # Cache is invalid if it's from a different date
            if cache_date != current_ist:
                return False
                
            return True
        except Exception:
            return False

    def get_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        trading_days = []
        current_date = start_date

        while current_date <= end_date:
            if (current_date.weekday() < 5) and (current_date.date() not in self.holidays):
                trading_days.append(current_date)
            current_date += timedelta(days=1)

        return trading_days

    def get_next_rebalance_dates(self, num_dates: int = 6) -> List[Dict]:
        rebalance_dates = []
        current_date = datetime.now(TIMEZONE).replace(day=1)

        for _ in range(num_dates):
            first_day = current_date.replace(day=1)
            trading_days = self.get_trading_days(first_day, first_day + timedelta(days=10))
            if trading_days:
                first_trading_day = trading_days[0]
                data_cutoff = self.get_previous_trading_day(first_trading_day)

                rebalance_dates.append({
                    "rebalance_date": first_trading_day,
                    "data_cutoff_date": data_cutoff,
                    "type": "Month Start"
                })

            mid_month = current_date.replace(day=15)
            trading_days = self.get_trading_days(mid_month, mid_month + timedelta(days=10))
            if trading_days:
                mid_trading_day = trading_days[0]
                data_cutoff = self.get_previous_trading_day(mid_trading_day)

                rebalance_dates.append({
                    "rebalance_date": mid_trading_day,
                    "data_cutoff_date": data_cutoff,
                    "type": "Mid Month"
                })

            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return sorted(rebalance_dates, key=lambda x: x['rebalance_date'])

    def get_previous_trading_day(self, date: datetime) -> datetime:
        prev_day = date - timedelta(days=1)
        while prev_day.weekday() >= 5 or prev_day.date() in self.holidays:
            prev_day -= timedelta(days=1)
        return prev_day

    def authenticate_fyers(self, auth_code: str) -> bool:
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
                if profile.get("s") == "ok":
                    return True
            return False
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False

    def fetch_historical_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch historical data with chunked approach exactly like working code"""
        all_data = []
        start_date = pd.Timestamp(start)
        end_date = pd.Timestamp(end)
        chunk_days = 365

        # Determine symbol format based on type
        # ETFs and Indices need different suffix than regular equity stocks
        # Common Fyers symbol formats:
        # - Equities: NSE:SYMBOL-EQ
        # - ETFs: NSE:SYMBOL-EQ or NSE:SYMBOL (varies by ETF)
        # - Indices: NSE:SYMBOL-INDEX

        if symbol == "GOLDBEES":
            # GOLDBEES ETF - verified from Fyers
            fyers_symbol = "NSE:GOLDBEES-EQ"
        elif symbol == "NIFTY50":
            # NIFTY50 Index - verified from Fyers (no space in name)
            fyers_symbol = "NSE:NIFTY50-INDEX"
        elif symbol in ["NIFTYBEES", "LIQUIDBEES"]:
            # Other ETFs - try -EQ format
            fyers_symbol = f"NSE:{symbol}-EQ"
        elif symbol in ["NIFTYBANK", "BANKNIFTY"]:
            # Bank NIFTY indices
            fyers_symbol = f"NSE:NIFTYBANK-INDEX"
        else:
            # Regular equity stocks
            fyers_symbol = f"NSE:{symbol}-EQ"

        current = end_date
        while current >= start_date:
            chunk_start = max(start_date, current - pd.Timedelta(days=chunk_days - 1))

            try:
                response = self.fyers.history({
                    "symbol": fyers_symbol,
                    "resolution": "D",
                    "date_format": 1,
                    "range_from": chunk_start.strftime("%Y-%m-%d"),
                    "range_to": current.strftime("%Y-%m-%d"),
                    "cont_flag": "1"
                })
                
                if response["s"] == "ok":
                    candles = response.get("candles", [])
                    all_data.extend(candles)
                else:
                    error_msg = response.get('message', 'Unknown error')
                    print(f"Data fetch error for {symbol} (Fyers: {fyers_symbol})")
                    print(f"  Period: {chunk_start.strftime('%Y-%m-%d')} to {current.strftime('%Y-%m-%d')}")
                    print(f"  Error: {error_msg}")
                    
            except Exception as e:
                print(f"Exception fetching {symbol} chunk {chunk_start.strftime('%Y-%m-%d')} to {current.strftime('%Y-%m-%d')}: {str(e)}")
                
            current = chunk_start - pd.Timedelta(days=1)
            time.sleep(0.5)

        if not all_data:
            print(f"No data fetched for {symbol} across all chunks.")
            return pd.DataFrame()

        # Process the data exactly like your working code
        df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
        df = df.set_index("timestamp").sort_index()
        df.index = df.index.normalize()  # Normalize to date-only
        return df

    def calculate_momentum_volatility_fitp(self, df: pd.DataFrame, date: pd.Timestamp,
                                          lookback_period: int = 12, last_month_exclusion: int = 0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            if df.empty or len(df) < 2:
                return None, None, None

            all_dates = df.index

            # Calculate end_date: if last_month_exclusion=0, use the cutoff date as-is
            # If last_month_exclusion>0, go back that many months
            if last_month_exclusion == 0:
                end_date = date
            else:
                end_date = date - pd.DateOffset(months=last_month_exclusion)

            # Find the closest available date
            if end_date not in all_dates:
                previous_dates = all_dates[all_dates <= end_date]
                if len(previous_dates) == 0:
                    return None, None, None
                end_date = previous_dates[-1]

            end_price = df['close'].loc[end_date]

            # Calculate start_date: go back lookback_period months to month start, then find first trading day
            # Go back to the 1st of the month that is lookback_period months ago
            target_month = end_date - pd.DateOffset(months=lookback_period)
            month_start = target_month.replace(day=1)

            # Find first trading day on or after that month start
            if month_start not in all_dates:
                next_dates = all_dates[all_dates >= month_start]
                if len(next_dates) == 0:
                    return None, None, None
                start_date = next_dates[0]
            else:
                start_date = month_start

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
            return None, None, None

    def scan_stocks(self, symbols: List[str], cutoff_date: datetime, strategy: str = "volatility", 
                   num_stocks: int = 20, lookback_period: int = 12, last_month_exclusion: int = 0) -> List[Tuple[str, float, float, float, float]]:
        if not self.fyers:
            st.error("❌ Fyers not authenticated!")
            return []

        scores = []
        cache_key = f"{cutoff_date.strftime('%Y-%m-%d')}_{strategy}_{lookback_period}"

        # Check for valid cache
        cache_valid = False
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached_data = pickle.load(f)
                    if (cached_data.get("cache_key") == cache_key and 
                        self.is_cache_valid(cache_key, cached_data.get("timestamp", ""))):
                        self.cached_data = cached_data["data"]
                        cache_valid = True
                        st.success("✅ Using cached data")
            except Exception as e:
                st.warning(f"⚠️ Cache error: {str(e)}")

        # Fetch new data if cache is invalid
        if not cache_valid:
            st.info("📊 Fetching fresh data...")
            end = cutoff_date
            start = end - pd.Timedelta(days=730)
            hist_data = {}

            progress_bar = st.progress(0)
            status_text = st.empty()
            failed_symbols = []
            successful_count = 0

            # Collect all fetch errors to show at the end
            fetch_errors = []

            for i, symbol in enumerate(symbols):
                status_text.text(f"📈 Fetching {symbol} ({i+1}/{len(symbols)}) - Success: {successful_count}")
                
                df = self.fetch_historical_data(
                    symbol, 
                    start.strftime("%Y-%m-%d"), 
                    end.strftime("%Y-%m-%d")
                )
                
                if not df.empty:
                    hist_data[symbol] = df
                    successful_count += 1
                else:
                    failed_symbols.append(symbol)
                    fetch_errors.append(f"No data for {symbol}")
                
                progress_bar.progress((i + 1) / len(symbols))

            # Show combined error message like your working code
            if fetch_errors:
                combined_message = "⚠️ Data Fetch Errors:\n" + "\n".join(fetch_errors[:10])  # Show first 10 errors
                if len(fetch_errors) > 10:
                    combined_message += f"\n... and {len(fetch_errors) - 10} more errors"
                st.warning(combined_message)

            self.cached_data = hist_data
            
            st.info(f"📊 Successfully fetched data for {successful_count}/{len(symbols)} symbols")

            # Save cache with timestamp
            try:
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump({
                        "cache_key": cache_key,
                        "data": hist_data,
                        "timestamp": datetime.now(TIMEZONE).isoformat()
                    }, f)
            except Exception as e:
                st.warning(f"⚠️ Cache save error: {str(e)}")

        # Calculate scores - only for symbols with data
        valid_symbols = [s for s in symbols if s in self.cached_data and not self.cached_data[s].empty]
        
        if not valid_symbols:
            st.error("❌ No valid symbols with data found")
            return []
        
        st.info(f"🧮 Calculating momentum scores for {len(valid_symbols)} valid symbols...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        processed_count = 0

        for i, symbol in enumerate(valid_symbols):
            status_text.text(f"🔍 Analyzing {symbol} ({i+1}/{len(valid_symbols)})")
            df = self.cached_data[symbol]

            momentum, volatility, fitp = self.calculate_momentum_volatility_fitp(
                df, cutoff_date, lookback_period, last_month_exclusion
            )

            if momentum is not None:
                if strategy == 'volatility' and volatility is not None and volatility > 0:
                    score = momentum / volatility
                elif strategy == 'fitp' and fitp is not None:
                    score = momentum * fitp
                else:
                    score = momentum
                scores.append((symbol, momentum, volatility, fitp, score))
            
            processed_count += 1
            progress_bar.progress(processed_count / len(valid_symbols))

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        if not scores:
            st.error("❌ No valid scores calculated. Check data availability.")
            return []

        # Dynamic Asset Allocation: GOLDBEES vs NIFTY 3-month comparison
        # If GOLDBEES 3-month return > NIFTY 3-month return, add GOLDBEES to final selection
        goldbees_symbol = "GOLDBEES"
        nifty_symbol = "NIFTY50"  # NIFTY 50 Index

        if goldbees_symbol in self.cached_data and nifty_symbol in self.cached_data:
            goldbees_df = self.cached_data[goldbees_symbol]
            nifty_df = self.cached_data[nifty_symbol]

            # Calculate 3-month returns for both (fixed 3-month lookback)
            goldbees_3m_return, _, _ = self.calculate_momentum_volatility_fitp(
                goldbees_df, cutoff_date, lookback_period=3, last_month_exclusion=0
            )

            nifty_3m_return, _, _ = self.calculate_momentum_volatility_fitp(
                nifty_df, cutoff_date, lookback_period=3, last_month_exclusion=0
            )

            if goldbees_3m_return is not None and nifty_3m_return is not None:
                st.info(f"📊 3-Month Allocation Comparison: GOLDBEES ({goldbees_3m_return*100:.2f}%) vs NIFTY50 ({nifty_3m_return*100:.2f}%)")

                if goldbees_3m_return > nifty_3m_return:
                    # GOLDBEES outperformed - add to selection (50% Gold allocation)
                    st.success(f"✅ GOLDBEES outperformed NIFTY - Adding GOLDBEES (50% Gold / 50% Equity allocation)")

                    # Calculate full period metrics for GOLDBEES using main lookback period
                    gb_momentum, gb_volatility, gb_fitp = self.calculate_momentum_volatility_fitp(
                        goldbees_df, cutoff_date, lookback_period, last_month_exclusion
                    )

                    if gb_momentum is not None:
                        if strategy == 'volatility' and gb_volatility is not None and gb_volatility > 0:
                            gb_score = gb_momentum / gb_volatility
                        elif strategy == 'fitp' and gb_fitp is not None:
                            gb_score = gb_momentum * gb_fitp
                        else:
                            gb_score = gb_momentum

                        # Add GOLDBEES to scores if not already present
                        if not any(s[0] == goldbees_symbol for s in scores):
                            scores.append((goldbees_symbol, gb_momentum, gb_volatility, gb_fitp, gb_score))
                else:
                    # NIFTY outperformed - 100% Equity allocation (don't add GOLDBEES)
                    st.info(f"ℹ️ NIFTY outperformed GOLDBEES - 100% Equity allocation (GOLDBEES not added)")
            else:
                # Could not calculate returns - default to 100% equity
                st.warning(f"⚠️ Could not calculate 3-month returns - Defaulting to 100% Equity (GOLDBEES not added)")
        else:
            # GOLDBEES or NIFTY data not available - default to 100% equity
            missing = []
            if goldbees_symbol not in self.cached_data:
                missing.append(goldbees_symbol)
            if nifty_symbol not in self.cached_data:
                missing.append(nifty_symbol)
            st.warning(f"⚠️ Missing data for {', '.join(missing)} - Defaulting to 100% Equity allocation")

        sorted_scores = sorted(scores, key=lambda x: x[4], reverse=True)[:num_stocks]
        st.success(f"✅ Successfully analyzed {len(scores)} stocks, returning top {len(sorted_scores)}")
        return sorted_scores

def display_status_card(status_type, title, message, icon=""):
    card_class = f"status-card status-{status_type}"
    st.markdown(f"""
    <div class="{card_class}">
        <h4>{icon} {title}</h4>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">🚀 Fyers Stock Scanner Pro</h1>
        <p class="hero-subtitle">Advanced momentum-based stock screening</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize
    if 'scanner' not in st.session_state:
        st.session_state.scanner = EnhancedStockScanner()
    if 'github_integration' not in st.session_state:
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                try:
                    github_token = st.secrets.get("GITHUB_TOKEN")
                except:
                    github_token = None
            if github_token:
                st.session_state.github_integration = GitHubIntegration(github_token=github_token)
            else:
                st.session_state.github_integration = None
        except Exception as e:
            st.session_state.github_integration = None

    # Sidebar
    with st.sidebar:
        st.header("🔧 Control Panel")

        # Authentication
        st.subheader("🔐 Fyers Authentication")
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={FYERS_CONFIG['client_id']}&redirect_uri={FYERS_CONFIG['redirect_uri']}&response_type=code&state=None"

        st.markdown(f"[🔗 Get Auth Code]({auth_url})")

        auth_code = st.text_input("Authorization Code:", type="password", placeholder="Enter auth code...")

        if st.button("🔑 Authenticate", type="primary", use_container_width=True):
            if auth_code:
                with st.spinner("Authenticating..."):
                    if st.session_state.scanner.authenticate_fyers(auth_code):
                        st.success("✅ Authenticated!")
                        st.session_state.authenticated = True
                    else:
                        st.error("❌ Failed!")
                        st.session_state.authenticated = False
            else:
                st.warning("Enter auth code")

        # Parameters
        st.subheader("📊 Parameters")
        strategy = st.selectbox("Strategy:", ["volatility", "fitp", "momentum"])
        num_stocks = st.slider("Number of stocks:", 5, 50, 20)
        lookback_period = st.slider("Lookback (months):", 3, 24, 12)
        last_month_exclusion = st.slider("Last month exclusion:", 0, 3, 0)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Scanner", "📅 Calendar", "📊 Analytics"])

    with tab1:
        if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
            display_status_card("info", "Getting Started", "Please authenticate with Fyers first", "👈")
        else:
            # Rebalance date selection
            st.subheader("📅 Select Rebalance Date")
            rebalance_dates = st.session_state.scanner.get_next_rebalance_dates(6)

            col1, col2 = st.columns([2, 1])

            with col1:
                selected_rebalance = st.selectbox(
                    "Choose rebalance date:",
                    options=range(len(rebalance_dates)),
                    format_func=lambda x: f"{rebalance_dates[x]['rebalance_date'].strftime('%Y-%m-%d')} ({rebalance_dates[x]['type']})"
                )

            with col2:
                if selected_rebalance is not None:
                    cutoff_date = rebalance_dates[selected_rebalance]['data_cutoff_date']
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📊 Data Cutoff</div>
                        <div class="metric-value">{cutoff_date.strftime('%Y-%m-%d')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Stock universe selection
            st.subheader("📁 Stock Universe")
            stock_source = st.radio(
                "Choose stock universe:",
                ["📈 Validated SmallCap Stocks", "📁 Upload CSV", "✏️ Manual Entry"],
                horizontal=True
            )

            if stock_source == "📈 Validated SmallCap Stocks":
                # Use a subset of validated symbols for testing
                symbols = VALID_NIFTY_SMALLCAP_SYMBOLS[:20]  # Start with first 20 symbols
                st.success(f"✅ Using {len(symbols)} validated stocks")

                with st.expander(f"📋 View validated stock list ({len(symbols)} symbols)"):
                    cols = st.columns(5)
                    for i, symbol in enumerate(symbols):
                        with cols[i % 5]:
                            st.code(symbol)

            elif stock_source == "📁 Upload CSV":
                uploaded_file = st.file_uploader("Upload CSV with 'Symbol' column", type="csv")

                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        if 'Symbol' in df.columns:
                            symbols = df['Symbol'].tolist()
                            st.success(f"✅ Loaded {len(symbols)} symbols")
                            st.dataframe(df.head(), use_container_width=True)
                        else:
                            st.error("❌ CSV must have 'Symbol' column")
                            symbols = VALID_NIFTY_SMALLCAP_SYMBOLS[:10]
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        symbols = VALID_NIFTY_SMALLCAP_SYMBOLS[:10]
                else:
                    st.info("📤 Upload CSV file")
                    symbols = VALID_NIFTY_SMALLCAP_SYMBOLS[:10]

            else:  # Manual Entry
                manual_symbols = st.text_area(
                    "Enter symbols (comma-separated):",
                    value="KFINTECH, LAURUSLABS, DEEPAKFERT, ERIS, AFFLE",
                    help="Enter stock symbols separated by commas"
                )

                if manual_symbols:
                    symbols = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()]
                    st.success(f"✅ {len(symbols)} symbols ready")
                else:
                    symbols = VALID_NIFTY_SMALLCAP_SYMBOLS[:10]

            # Always add GOLDBEES and NIFTY50 for dynamic asset allocation
            # These are required for the 3-month comparison logic
            required_symbols = ["GOLDBEES", "NIFTY50"]
            for req_symbol in required_symbols:
                if req_symbol not in symbols:
                    symbols.append(req_symbol)

            st.info(f"📊 Total symbols (including GOLDBEES & NIFTY50 for allocation): {len(symbols)}")

            # Clear cache button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Clear Cache", help="Clear cached data to force fresh fetch"):
                    if os.path.exists(CACHE_FILE):
                        os.remove(CACHE_FILE)
                        st.session_state.scanner.cached_data = None
                        st.success("✅ Cache cleared")

            # Scan button
            with col1:
                if symbols and st.button("🔍 Start Scan", type="primary", use_container_width=True):
                    if selected_rebalance is not None:
                        selected_date_info = rebalance_dates[selected_rebalance]
                        cutoff_date = selected_date_info['data_cutoff_date']

                        try:
                            with st.spinner("🔄 Scanning stocks..."):
                                results = st.session_state.scanner.scan_stocks(
                                    symbols=symbols,
                                    cutoff_date=cutoff_date,
                                    strategy=strategy,
                                    num_stocks=num_stocks,
                                    lookback_period=lookback_period,
                                    last_month_exclusion=last_month_exclusion
                                )

                            if results:
                                results_df = pd.DataFrame(results, columns=[
                                    "Symbol", "Momentum", "Volatility", "FITP", "Score"
                                ])

                                st.session_state.results_df = results_df
                                st.session_state.scan_info = {
                                    "cutoff_date": cutoff_date,
                                    "rebalance_date": selected_date_info['rebalance_date'],
                                    "strategy": strategy,
                                    "completed": True
                                }

                                display_status_card("success", "Scan Complete", f"Found {len(results)} stocks", "🎉")

                                # Results display
                                st.subheader("🏆 Top Momentum Stocks")

                                display_df = results_df.copy()
                                display_df["Momentum"] = display_df["Momentum"].apply(lambda x: f"{x:.4f}")
                                display_df["Volatility"] = display_df["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                                display_df["FITP"] = display_df["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                                display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.4f}")
                                display_df.index = range(1, len(display_df) + 1)

                                st.dataframe(display_df, use_container_width=True, height=400)

                            else:
                                display_status_card("warning", "No Results", "No stocks found matching criteria", "⚠️")

                        except Exception as e:
                            display_status_card("error", "Scan Error", f"Error: {str(e)}", "❌")
                            st.exception(e)  # Show full error for debugging

            # GitHub Integration
            if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty and st.session_state.github_integration:
                st.divider()

                st.markdown("""
                <div class="github-section">
                    <h3>🔗 Push to GitHub</h3>
                    <p>Save results to GitHub for access from other applications</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **📁 File:** `{GITHUB_CSV_FILENAME}`  
                    **📊 Rows:** {len(st.session_state.results_df)}  
                    **🔄 Action:** Replace existing file  
                    """)

                with col2:
                    if st.button("📤 Push to GitHub", type="primary", use_container_width=True):
                        with st.spinner("Uploading..."):
                            try:
                                success, message = st.session_state.github_integration.push_csv_to_github(
                                    st.session_state.results_df,
                                    f"Momentum scan - {strategy} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                )

                                if success:
                                    display_status_card("success", "Upload Success", message, "✅")

                                    csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                                    st.markdown(f"""
                                    **🌐 Direct CSV URL:**
                                    ```
                                    {csv_url}
                                    ```
                                    """)

                                    if st.button("🧪 Test URL"):
                                        try:
                                            response = requests.get(csv_url, timeout=10)
                                            if response.status_code == 200:
                                                display_status_card("success", "URL Test", "CSV accessible", "✅")
                                                lines = response.text.split('\n')[:3]
                                                for line in lines:
                                                    st.code(line)
                                            else:
                                                display_status_card("error", "URL Test", f"Status: {response.status_code}", "❌")
                                        except Exception as e:
                                            display_status_card("error", "URL Test", f"Error: {str(e)}", "❌")

                                    st.balloons()
                                else:
                                    display_status_card("error", "Upload Failed", message, "❌")

                            except Exception as e:
                                display_status_card("error", "Upload Error", f"Error: {str(e)}", "❌")

                # Usage examples
                with st.expander("💡 Usage in other applications"):
                    csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                    st.markdown(f"""
                    **Python:**
                    ```python
                    import pandas as pd
                    df = pd.read_csv('{csv_url}')
                    ```

                    **JavaScript:**
                    ```javascript
                    fetch('{csv_url}').then(r => r.text()).then(data => console.log(data));
                    ```

                    **Excel/Sheets:** Data > From Web > Enter URL
                    """)

    with tab2:
        st.subheader("📅 Rebalance Calendar")

        rebalance_dates = st.session_state.scanner.get_next_rebalance_dates(8)
        schedule_df = pd.DataFrame(rebalance_dates)
        schedule_df['Rebalance Date'] = schedule_df['rebalance_date'].dt.strftime('%Y-%m-%d (%A)')
        schedule_df['Data Cutoff'] = schedule_df['data_cutoff_date'].dt.strftime('%Y-%m-%d (%A)')
        schedule_df['Days Until'] = (schedule_df['rebalance_date'] - datetime.now(TIMEZONE)).dt.days

        display_schedule = schedule_df[['type', 'Rebalance Date', 'Data Cutoff', 'Days Until']].copy()
        display_schedule.columns = ['Type', 'Rebalance Date', 'Data Cutoff Date', 'Days Until']
        display_schedule.index = range(1, len(display_schedule) + 1)

        st.dataframe(display_schedule, use_container_width=True)

        # Market holidays
        st.subheader("🎭 Market Holidays 2025")
        if st.session_state.scanner.holidays:
            holidays_list = sorted(list(st.session_state.scanner.holidays))
            holidays_df = pd.DataFrame({
                'Date': [h.strftime('%Y-%m-%d (%A)') for h in holidays_list],
                'Days from Today': [(h - datetime.now().date()).days for h in holidays_list]
            })
            holidays_df = holidays_df[holidays_df['Days from Today'] >= 0]
            holidays_df.index = range(1, len(holidays_df) + 1)
            st.dataframe(holidays_df, use_container_width=True)

    with tab3:
        st.subheader("📊 Analytics Dashboard")

        if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_momentum = st.session_state.results_df['Momentum'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📈 Avg Momentum</div>
                    <div class="metric-value">{avg_momentum:.4f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                avg_volatility = st.session_state.results_df['Volatility'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📊 Avg Volatility</div>
                    <div class="metric-value">{avg_volatility:.4f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                top_score = st.session_state.results_df['Score'].max()
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🏆 Top Score</div>
                    <div class="metric-value">{top_score:.4f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                positive_momentum = (st.session_state.results_df['Momentum'] > 0).sum()
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📈 Positive Count</div>
                    <div class="metric-value">{positive_momentum}/{len(st.session_state.results_df)}</div>
                </div>
                """, unsafe_allow_html=True)

            # Charts
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Momentum Distribution', 'Score vs Volatility', 'FITP Distribution', 'Top 10 Stocks'),
                specs=[[{"type": "histogram"}, {"type": "scatter"}],
                       [{"type": "histogram"}, {"type": "bar"}]]
            )

            fig.add_trace(go.Histogram(x=st.session_state.results_df['Momentum'], nbinsx=20), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=st.session_state.results_df['Volatility'], 
                y=st.session_state.results_df['Score'],
                mode='markers',
                text=st.session_state.results_df['Symbol']
            ), row=1, col=2)
            fig.add_trace(go.Histogram(x=st.session_state.results_df['FITP'], nbinsx=20), row=2, col=1)

            top_10 = st.session_state.results_df.head(10)
            fig.add_trace(go.Bar(x=top_10['Symbol'], y=top_10['Score']), row=2, col=2)

            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Top performers
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Top 5 by Momentum**")
                top_momentum = st.session_state.results_df.nlargest(5, 'Momentum')[['Symbol', 'Momentum']]
                for idx, row in top_momentum.iterrows():
                    st.markdown(f"• **{row['Symbol']}**: {row['Momentum']:.4f}")

            with col2:
                st.markdown("**📊 Top 5 by Score**")
                top_score = st.session_state.results_df.nlargest(5, 'Score')[['Symbol', 'Score']]
                for idx, row in top_score.iterrows():
                    st.markdown(f"• **{row['Symbol']}**: {row['Score']:.4f}")

        else:
            display_status_card("info", "No Data", "Run a scan first to see analytics", "📊")

if __name__ == "__main__":
    main()