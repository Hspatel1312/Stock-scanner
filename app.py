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
GITHUB_CSV_FILENAME = "momentum_scan_results.csv"
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

# Nifty SmallCap 250 Stock List (Exact 250 symbols from CSV)
NIFTY_SMALLCAP_250_SYMBOLS = [
    "360ONE", "AADHARHFC", "AARTIIND", "AAVAS", "ACE", "ABREL", "ABSLAMC", "AEGISLOG", 
    "AFFLE", "AKUMS", "APLLTD", "ALKYLAMINE", "ALOKINDS", "ARE&M", "AMBER", "ANANDRATHI", 
    "ANANTRAJ", "ANGELONE", "APARINDS", "APTUS", "ACI", "ASAHIINDIA", "ASTERDM", "ASTRAZEN", 
    "ATUL", "AVANTIFEED", "BASF", "BEML", "BLS", "BALAMINES", "BALRAMCHIN", "BATAINDIA", 
    "BIKAJI", "BIRLACORPN", "BSOFT", "BLUEDART", "BLUESTARCO", "BBTC", "BRIGADE", "MAPMYINDIA", 
    "CCL", "CESC", "CIEINDIA", "CAMPUS", "CANFINHOME", "CAPLIPOINT", "CGCL", "CASTROLIND", 
    "CEATLTD", "CELLO", "CENTRALBK", "CDSL", "CENTURYPLY", "CERA", "CHALET", "CHAMBLFERT", 
    "CHEMPLASTS", "CHENNPETRO", "CHOLAHLDNG", "CUB", "CLEAN", "CAMS", "CONCORDBIO", "CRAFTSMAN", 
    "CREDITACC", "CROMPTON", "CYIENT", "DOMS", "DATAPATTNS", "DEEPAKFERT", "DEVYANI", "LALPATHLAB", 
    "EIDPARRY", "EIHOTEL", "EASEMYTRIP", "ELECON", "ELGIEQUIP", "EMCURE", "ENGINERSIN", "EQUITASBNK", 
    "ERIS", "FINEORG", "FINCABLES", "FINPIPE", "FSL", "FIVESTAR", "GRINFRA", "GVT&D", 
    "GRSE", "GILLETTE", "GLENMARK", "GODIGIT", "GPIL", "GODFRYPHLP", "GODREJAGRO", "GRANULES", 
    "GRAPHITE", "GESHIP", "GAEL", "GMDCLTD", "GNFC", "GPPL", "GSFC", "GSPL", 
    "HEG", "HBLENGINE", "HFCL", "HAPPSTMNDS", "HSCL", "HINDCOPPER", "HOMEFIRST", "HONASA", 
    "ISEC", "IFCI", "IIFL", "INOXINDIA", "IRCON", "ITI", "INDGN", "INDIACEM", 
    "INDIAMART", "IEX", "INOXWIND", "INTELLECT", "JBCHEPHARM", "JBMA", "JKLAKSHMI", "JKTYRE", 
    "JMFINANCIL", "JPPOWER", "J&KBANK", "JINDALSAW", "JUBLINGREA", "JUBLPHARMA", "JWL", "JUSTDIAL", 
    "JYOTHYLAB", "JYOTICNC", "KNRCON", "KSB", "KAJARIACER", "KPIL", "KANSAINER", "KARURVYSYA", 
    "KAYNES", "KEC", "KFINTECH", "KIRLOSBROS", "KIRLOSENG", "KIMS", "LATENTVIEW", "LAURUSLABS", 
    "LEMONTREE", "MMTC", "MGL", "MAHSEAMLES", "MAHLIFE", "MANAPPURAM", "MASTEK", "METROPOLIS", 
    "MINDACORP", "MOTILALOFS", "MCX", "NATCOPHARM", "NBCC", "NCC", "NSLNISP", "NH", 
    "NATIONALUM", "NAVINFLUOR", "NETWEB", "NETWORK18", "NEWGEN", "NUVAMA", "NUVOCO", "OLECTRA", 
    "PCBL", "PNBHOUSING", "PNCINFRA", "PTCIL", "PVRINOX", "PFIZER", "PEL", "PPLPHARMA", 
    "POLYMED", "PRAJIND", "QUESS", "RRKABEL", "RBLBANK", "RHIM", "RITES", "RADICO", 
    "RAILTEL", "RAINBOW", "RAJESHEXPO", "RKFORGE", "RCF", "RATNAMANI", "RTNINDIA", "RAYMOND", 
    "REDINGTON", "ROUTE", "SBFC", "SAMMAANCAP", "SANOFI", "SAPPHIRE", "SAREGAMA", "SCHNEIDER", 
    "SCI", "RENUKA", "SHYAMMETL", "SIGNATURE", "SOBHA", "SONATSOFTW", "SWSOLAR", "SUMICHEM", 
    "SPARC", "SUVENPHAR", "SWANENERGY", "SYRMA", "TBOTEK", "TVSSCS", "TANLA", "TTML", 
    "TECHNOE", "TEJASNET", "RAMCOCEM", "TITAGARH", "TRIDENT", "TRIVENI", "TRITURBINE", "UCOBANK", 
    "UTIAMC", "UJJIVANSFB", "USHAMART", "VGUARD", "VIPIND", "DBREALTY", "VTL", "VARROC", 
    "MANYAVAR", "VIJAYA", "VINATIORGA", "WELCORP", "WELSPUNLIV", "WESTLIFE", "WHIRLPOOL", "ZEEL", 
    "ZENSARTECH", "ECLERX"
]

class GitHubIntegration:
    def __init__(self, repo_path=None):
        self.repo_path = Path(repo_path or GITHUB_CONFIG["data_repo_path"])
        self.data_folder = Path(self.repo_path) / GITHUB_CONFIG["data_folder"]
        self.username = GITHUB_CONFIG["username"]
        self.repo_name = GITHUB_CONFIG["repo_name"]
        # Use timestamp-based filename for unique files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"stock_scan_{timestamp}.csv"
        self.csv_file_path = self.data_folder / self.csv_filename
        self._setup_repo()
    
    def _setup_repo(self):
        """Setup repository and data folder"""
        if not self.repo_path.exists():
            st.error(f"Repository path not found: {self.repo_path}")
            return False
        self.data_folder.mkdir(exist_ok=True)
        
        # Create README if it doesn't exist
        readme_path = self.data_folder / "README.md"
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write("# Data Folder\nThis folder contains CSV outputs from stock scans.\n")
        
        return True
    
    def _run_git_command(self, command, timeout=30):
        """Run git command with proper error handling"""
        try:
            result = subprocess.run(
                command, 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)
    
    def _check_git_status(self):
        """Check if we're in a git repository and get status"""
        success, stdout, stderr = self._run_git_command(["git", "status", "--porcelain"])
        return success, stdout
    
    def _setup_git_credentials(self):
        """Setup git credentials for GitHub"""
        try:
            # Check if we're in a Codespace or have GitHub token
            github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
            
            if github_token:
                # Configure git to use token authentication
                git_url = f"https://{github_token}@github.com/{self.username}/{self.repo_name}.git"
                success, _, _ = self._run_git_command(["git", "remote", "set-url", "origin", git_url])
                return success, "Token authentication configured"
            else:
                # Try to use existing credentials
                success, _, _ = self._run_git_command(["git", "config", "--get", "user.name"])
                if success:
                    return True, "Using existing git configuration"
                else:
                    return False, "No GitHub token found and no git credentials configured"
                    
        except Exception as e:
            return False, f"Error setting up credentials: {str(e)}"
    
    def save_csv_locally(self, df, scan_date, strategy, commit_message=None):
        """Save CSV file locally in the data folder"""
        try:
            if not self._setup_repo():
                return False, "Repository setup failed"
            
            # Generate filename with scan details
            date_str = scan_date.strftime("%Y%m%d")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_filename = f"stock_scan_{date_str}_{strategy}_{timestamp}.csv"
            self.csv_file_path = self.data_folder / self.csv_filename
            
            # Save CSV file
            df.to_csv(self.csv_file_path, index=False)
            
            # Create metadata file
            metadata = {
                "filename": self.csv_filename,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "scan_date": scan_date.strftime('%Y-%m-%d'),
                "strategy": strategy,
                "generated_by": "Fyers Stock Scanner Pro",
                "file_size_kb": round(self.csv_file_path.stat().st_size / 1024, 2),
                "scan_parameters": {
                    "strategy": strategy,
                    "scan_date": scan_date.isoformat()
                }
            }
            
            metadata_path = self.data_folder / f"{self.csv_filename.replace('.csv', '_metadata.json')}"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, f"CSV saved successfully to {self.csv_file_path}"
            
        except Exception as e:
            return False, f"Error saving CSV: {str(e)}"
    
    def push_to_github(self, df, scan_date, strategy, commit_message=None):
        """Save CSV locally and attempt to push to GitHub"""
        # First save locally
        success, message = self.save_csv_locally(df, scan_date, strategy, commit_message)
        if not success:
            return False, message
        
        # Check git status
        git_ok, git_status = self._check_git_status()
        if not git_ok:
            return True, f"✅ CSV saved locally. Git repository not available."
        
        # Setup credentials
        cred_ok, cred_message = self._setup_git_credentials()
        if not cred_ok:
            return True, f"✅ CSV saved locally. {cred_message}"
        
        # Attempt git operations
        try:
            if commit_message is None:
                commit_message = f"Add {strategy} scan results - {scan_date.strftime('%Y-%m-%d')} - {datetime.now().strftime('%H:%M:%S')}"
            
            original_cwd = Path.cwd()
            os.chdir(self.repo_path)
            
            try:
                # Configure git user
                self._run_git_command(["git", "config", "user.email", "scanner@fyersapp.com"], timeout=10)
                self._run_git_command(["git", "config", "user.name", "Fyers Stock Scanner"], timeout=10)
                
                # Add files
                add_success1, _, add_error1 = self._run_git_command(["git", "add", f"data/{self.csv_filename}"])
                add_success2, _, add_error2 = self._run_git_command(["git", "add", f"data/{self.csv_filename.replace('.csv', '_metadata.json')}"])
                
                if not add_success1:
                    return True, f"✅ CSV saved locally. Git add failed: {add_error1}"
                
                # Check if there are changes to commit
                diff_success, _, _ = self._run_git_command(["git", "diff", "--cached", "--quiet"])
                if diff_success:
                    return True, f"✅ CSV saved locally. No changes to commit."
                
                # Commit changes
                commit_success, commit_out, commit_error = self._run_git_command(["git", "commit", "-m", commit_message])
                
                if not commit_success:
                    return True, f"✅ CSV saved locally. Commit failed: {commit_error}"
                
                # Try to push (this might fail due to authentication)
                push_success, push_out, push_error = self._run_git_command(["git", "push"], timeout=60)
                
                if push_success:
                    return True, f"🎉 Successfully pushed {self.csv_filename} to GitHub!"
                else:
                    # Clean up the error message
                    clean_error = push_error.replace("fatal: ", "").replace("error: ", "")
                    return True, f"✅ CSV saved and committed locally. GitHub push failed: {clean_error}"
                    
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            return True, "✅ CSV saved locally. Git operation timed out"
        except subprocess.CalledProcessError as e:
            return True, f"✅ CSV saved locally. Git error: {str(e)}"
        except Exception as e:
            return True, f"✅ CSV saved locally. Unexpected error: {str(e)}"
    
    def get_csv_url(self, raw=True):
        """Get the GitHub URL for the CSV file"""
        if raw:
            return f"https://raw.githubusercontent.com/{self.username}/{self.repo_name}/main/data/{self.csv_filename}"
        else:
            return f"https://github.com/{self.username}/{self.repo_name}/blob/main/data/{self.csv_filename}"
    
    def get_local_csv_path(self):
        """Get the local path of the CSV file"""
        return str(self.csv_file_path)
    
    def test_github_url(self):
        """Test if the GitHub URL is accessible"""
        try:
            csv_url = self.get_csv_url(raw=True)
            response = requests.get(csv_url, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.split('\n')[:3]
                return True, "✅ CSV accessible from GitHub", lines
            else:
                return False, f"⚠️ GitHub URL not accessible (Status: {response.status_code})", []
                
        except requests.exceptions.RequestException as e:
            return False, f"⚠️ GitHub URL not accessible: {str(e)}", []
        except Exception as e:
            return False, f"⚠️ Error testing URL: {str(e)}", []

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
    
    def calculate_momentum_volatility_fitp(self, df: pd.DataFrame, date: pd.Timestamp, 
                                          lookback_period: int = 12, last_month_exclusion: int = 0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
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
            return None, None, None
    
    def scan_stocks(self, symbols: List[str], cutoff_date: datetime, strategy: str = "volatility", 
                   num_stocks: int = 20, lookback_period: int = 12, last_month_exclusion: int = 0) -> List[Tuple[str, float, float, float, float]]:
        if not self.fyers:
            st.error("Fyers not authenticated!")
            return []
        
        scores = []
        cache_key = f"{cutoff_date.strftime('%Y-%m-%d')}_{strategy}_{lookback_period}"
        
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached_data = pickle.load(f)
                    if cached_data.get("cache_key") == cache_key:
                        self.cached_data = cached_data["data"]
                        st.success("✅ Using cached data")
            except:
                pass
        
        if not self.cached_data:
            st.info("📊 Fetching data...")
            end = cutoff_date
            start = end - pd.Timedelta(days=730)
            hist_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, symbol in enumerate(symbols):
                status_text.text(f"📈 Fetching {symbol} ({i+1}/{len(symbols)})")
                df = self.fetch_historical_data(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                hist_data[symbol] = df
                progress_bar.progress((i + 1) / len(symbols))
            
            self.cached_data = hist_data
            
            try:
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump({
                        "cache_key": cache_key,
                        "data": hist_data,
                        "timestamp": datetime.now().isoformat()
                    }, f)
            except:
                pass
        
        st.info("🧮 Calculating scores...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(symbols):
            status_text.text(f"🔍 Analyzing {symbol} ({i+1}/{len(symbols)})")
            df = self.cached_data.get(symbol, pd.DataFrame())
            
            if df.empty:
                continue
            
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
            
            progress_bar.progress((i + 1) / len(symbols))
        
        sorted_scores = sorted(scores, key=lambda x: x[4], reverse=True)[:num_stocks]
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
        st.session_state.github_integration = GitHubIntegration()
    
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
                ["📈 Nifty SmallCap 250 (Default)", "📁 Upload CSV", "✏️ Manual Entry"],
                horizontal=True
            )
            
            if stock_source == "📈 Nifty SmallCap 250 (Default)":
                symbols = NIFTY_SMALLCAP_250_SYMBOLS
                st.success(f"✅ Using {len(symbols)} stocks from Nifty SmallCap 250")
                
                with st.expander(f"📋 View stock list ({len(symbols)} symbols)"):
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
                            symbols = NIFTY_SMALLCAP_250_SYMBOLS[:20]
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        symbols = NIFTY_SMALLCAP_250_SYMBOLS[:20]
                else:
                    st.info("📤 Upload CSV file")
                    symbols = NIFTY_SMALLCAP_250_SYMBOLS[:20]
                    
            else:  # Manual Entry
                manual_symbols = st.text_area(
                    "Enter symbols (comma-separated):",
                    value="RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK",
                    help="Enter stock symbols separated by commas"
                )
                
                if manual_symbols:
                    symbols = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()]
                    st.success(f"✅ {len(symbols)} symbols ready")
                else:
                    symbols = NIFTY_SMALLCAP_250_SYMBOLS[:20]
            
            # Scan button
            if symbols and st.button("🔍 Start Scan", type="primary", use_container_width=True):
                if selected_rebalance is not None:
                    selected_date_info = rebalance_dates[selected_rebalance]
                    cutoff_date = selected_date_info['data_cutoff_date']
                    
                    try:
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
                            display_status_card("warning", "No Results", "No stocks found", "⚠️")
                            
                    except Exception as e:
                        display_status_card("error", "Scan Error", f"Error: {str(e)}", "❌")
            
            # GitHub Integration
            if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty:
                st.divider()
                
                st.markdown("""
                <div class="github-section">
                    <h3>💾 Save Results to GitHub</h3>
                    <p>Save scan results locally and push to GitHub repository</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show current scan info
                if hasattr(st.session_state, 'scan_info'):
                    scan_info = st.session_state.scan_info
                    st.markdown(f"""
                    **📊 Scan Details:**
                    - **Strategy:** {scan_info['strategy'].title()}
                    - **Cutoff Date:** {scan_info['cutoff_date'].strftime('%Y-%m-%d')}
                    - **Rebalance Date:** {scan_info['rebalance_date'].strftime('%Y-%m-%d')}
                    - **Stocks Found:** {len(st.session_state.results_df)}
                    """)
                
                col1, col2 = st.columns([3, 1])
                
                with col2:
                    if st.button("💾 Save & Push to GitHub", type="primary", use_container_width=True):
                        with st.spinner("Uploading..."):
                            try:
                                # Create new GitHub integration instance for this scan
                                github_integration = GitHubIntegration()
                                
                                scan_info = st.session_state.scan_info
                                success, message = st.session_state.github_integration.push_to_github(
                                    st.session_state.results_df,
                                    scan_info['cutoff_date'],
                                    scan_info['strategy'],
                                    f"{scan_info['strategy'].title()} scan - {scan_info['cutoff_date'].strftime('%Y-%m-%d')}"
                                )
                                
                                if "Successfully pushed" in message:
                                    display_status_card("success", "GitHub Success", message, "🎉")
                                    st.balloons()
                                else:
                                    display_status_card("info", "Local Save Success", message, "✅")
                                
                                # Store the integration instance for URL testing
                                st.session_state.current_github_integration = st.session_state.github_integration
                                
                            except Exception as e:
                                display_status_card("error", "Save Error", f"Error: {str(e)}", "❌")
                
                # Show file information after save
                if hasattr(st.session_state, 'current_github_integration'):
                    github_int = st.session_state.current_github_integration
                    
                    with col1:
                        # Show local file path
                        local_path = github_int.get_local_csv_path()
                        st.markdown(f"""
                        **📁 Local File:**
                        ```
                        {local_path}
                        ```
                        """)
                        
                        # Show GitHub URL
                        csv_url = github_int.get_csv_url(raw=True)
                        st.markdown(f"""
                        **🌐 GitHub URL:**
                        ```
                        {csv_url}
                        ```
                        """)
                    
                    # Test GitHub URL button
                    col_test1, col_test2 = st.columns([1, 1])
                    
                    with col_test1:
                        if st.button("🧪 Test GitHub URL", key="test_github_url"):
                            with st.spinner("Testing GitHub URL..."):
                                url_success, url_message, preview_lines = github_int.test_github_url()
                                    
                                if url_success:
                                    st.success(url_message)
                                    if preview_lines:
                                        st.markdown("**📄 Preview:**")
                                        for line in preview_lines:
                                            if line.strip():
                                                st.code(line)
                                else:
                                    st.warning(url_message)
                    
                    with col_test2:
                        if st.button("📋 Copy Local Path", key="copy_local_path"):
                            st.code(local_path)
                            st.success("Path displayed above - copy manually")
                
                # GitHub Setup Instructions
                with st.expander("🔧 GitHub Setup Instructions"):
                    st.markdown("""
                    ### For GitHub Codespaces:
                    The app should automatically use your GitHub token. If push fails:
                                    
                    1. Check if you have write access to the repository
                    2. Ensure the repository exists and is accessible
                    
                    ### For Local Development:
                    Set up GitHub authentication:
                    ```bash
                    # Set up GitHub token
                    export GITHUB_TOKEN=your_github_token_here
                    
                    # Or configure git credentials
                    git config --global user.name "Your Name"
                    git config --global user.email "your.email@example.com"
                    ```
                                    
                    ### Alternative:
                    Files are always saved locally in the `data/` folder. You can manually commit and push:
                    ```bash
                    git add data/
                    git commit -m "Add scan results"
                    git push
                    ```
                    """)
                
                # Usage examples
                with st.expander("💡 Usage Examples"):
                    if hasattr(st.session_state, 'current_github_integration'):
                        csv_url = st.session_state.current_github_integration.get_csv_url(raw=True)
                        local_path = st.session_state.current_github_integration.get_local_csv_path()
                        
                        st.markdown(f"""
                        **Python (from GitHub):**
                        ```python
                        import pandas as pd
                        df = pd.read_csv('{csv_url}')
                        print(df.head())
                        ```
                        
                        **Python (from Local File):**
                        ```python
                        import pandas as pd
                        df = pd.read_csv(r'{local_path}')
                        print(df.head())
                        ```
                        
                        **JavaScript/Fetch:**
                        ```javascript
                        fetch('{csv_url}')
                            .then(response => response.text())
                            .then(data => console.log(data));
                        ```
                        
                        **Excel/Google Sheets:**
                        - **From Web:** Data → From Web → Enter GitHub URL
                        - **From File:** File → Open → Browse to local file
                        
                        **curl Command:**
                        ```bash
                        curl -o scan_results.csv '{csv_url}'
                        ```
                        """)
                    else:
                        st.info("Save a scan first to see usage examples")
        
        # Clear any previous GitHub integration when starting new scan
        if 'current_github_integration' in st.session_state and st.button("🔍 Start Scan", type="primary", use_container_width=True):
            if 'current_github_integration' in st.session_state:
                del st.session_state.current_github_integration
                                    
                            except Exception as e:
                                display_status_card("error", "Save Error", f"Error: {str(e)}", "❌")
                
                # Usage examples
                with st.expander("💡 Usage in other applications"):
                    csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                    local_path = st.session_state.github_integration.get_local_csv_path()
                    st.markdown(f"""
                    **From GitHub (if accessible):**
                    ```python
                    import pandas as pd
                    df = pd.read_csv('{csv_url}')
                    ```
                    
                    **From Local File:**
                    ```python
                    import pandas as pd
                    df = pd.read_csv('{local_path}')
                    ```
                    
                    **JavaScript:**
                    ```javascript
                    fetch('{csv_url}').then(r => r.text()).then(data => console.log(data));
                    ```
                    
                    **Excel/Sheets:** 
                    - From Web: Data > From Web > Enter GitHub URL
                    - From File: Open > Browse to local file path
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