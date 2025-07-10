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

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .github-box {
        background: linear-gradient(135deg, #24292e 0%, #586069 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Configuration
FYERS_CONFIG = {
    "client_id": "F5ZQTMKTTH-100",
    "secret_key": "KDHZZYT6FW",
    "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/index.html"
}

# Default file paths
CACHE_FILE = "stock_data_cache.pkl"
TIMEZONE = pytz.timezone('Asia/Kolkata')

# GitHub Configuration - SMART PATH DETECTION
def get_repo_path():
    """Dynamically detect the repository path"""
    current = Path.cwd()
    
    # Check if we're in a Codespaces environment
    if "/workspaces/" in str(current):
        # Codespaces - use the specific path
        codespaces_path = Path("/workspaces/Stock-scanner")
        if codespaces_path.exists() and (codespaces_path / ".git").exists():
            return str(codespaces_path)
    
    # Check if current directory is the repo
    if (current / ".git").exists():
        return str(current)
    
    # Fallback to current directory
    return str(current)

GITHUB_CONFIG = {
    "username": "Hspatel1312",
    "repo_name": "Stock-scanner",
    "data_repo_path": get_repo_path(),  # Dynamic path detection
    "data_folder": "data"
}

class GitHubIntegration:
    def __init__(self, repo_path=None):
        self.repo_path = Path(repo_path or GITHUB_CONFIG["data_repo_path"])
        self.data_folder = Path(self.repo_path) / GITHUB_CONFIG["data_folder"]
        self.username = GITHUB_CONFIG["username"]
        self.repo_name = GITHUB_CONFIG["repo_name"]
        self.ensure_repo_exists()
    
    def ensure_repo_exists(self):
        """Check if the repository and data folder exist"""
        if not self.repo_path.exists():
            st.warning(f"⚠️ Repository not found at {self.repo_path}")
            return False
        
        # Create data folder if it doesn't exist
        self.data_folder.mkdir(exist_ok=True)
        
        # Create .gitignore for data folder if needed
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_content = """
# Data files (uncomment if you want to ignore large data files)
# data/*.csv
# data/*.pkl

# Cache files
*.pkl
__pycache__/
.streamlit/
"""
        
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
        
        return True
    
    def push_csv_to_github(self, df, filename, commit_message=None):
        """Push CSV file to the same repository in data folder with better error handling"""
        try:
            if not self.ensure_repo_exists():
                return False, "Repository not found or data folder creation failed."
            
            # Save CSV to the data folder (this will overwrite existing files)
            csv_path = self.data_folder / filename
            df.to_csv(csv_path, index=False)
            
            # Create metadata file
            metadata = {
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "scan_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_by": "Fyers Stock Scanner Pro",
                "file_size_kb": round(csv_path.stat().st_size / 1024, 2),
                "replaced_existing": csv_path.exists()
            }
            
            metadata_path = self.data_folder / f"{filename.replace('.csv', '_metadata.json')}"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Git operations with better error handling
            if commit_message is None:
                action = "Replace" if csv_path.exists() else "Add"
                commit_message = f"{action} {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Change to repo directory and commit
            original_cwd = Path.cwd()
            
            try:
                os.chdir(self.repo_path)
                
                # Check if git repo is initialized
                result = subprocess.run(["git", "status"], capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    return False, f"Not a git repository: {result.stderr}"
                
                # Configure git user if not set (for Streamlit Cloud)
                subprocess.run(["git", "config", "user.email", "streamlit-app@example.com"], 
                             capture_output=True, timeout=10)
                subprocess.run(["git", "config", "user.name", "Streamlit App"], 
                             capture_output=True, timeout=10)
                
                # Git operations - add files from data folder
                add_result = subprocess.run(["git", "add", f"data/{filename}"], 
                                          check=True, capture_output=True, timeout=30)
                subprocess.run(["git", "add", f"data/{filename.replace('.csv', '_metadata.json')}"], 
                             check=True, capture_output=True, timeout=30)
                
                # Check if there are changes to commit
                diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"], 
                                           capture_output=True, timeout=30)
                if diff_result.returncode == 0:
                    return True, f"File {filename} already up to date (no changes to commit)"
                
                # Commit changes
                commit_result = subprocess.run(["git", "commit", "-m", commit_message], 
                                             check=True, capture_output=True, timeout=30)
                
                # Push changes
                push_result = subprocess.run(["git", "push"], 
                                           check=True, capture_output=True, timeout=60)
                
                return True, f"Successfully {'replaced' if metadata.get('replaced_existing') else 'added'} {filename} on GitHub"
            
            except subprocess.TimeoutExpired:
                return False, "Git operation timed out. Please try again."
            
            except subprocess.CalledProcessError as e:
                error_msg = f"Git operation failed: {e}"
                if e.stderr:
                    stderr_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                    error_msg += f" - {stderr_msg}"
                
                # Check for common issues
                if "permission denied" in error_msg.lower():
                    return False, "Permission denied. GitHub authentication may be required."
                elif "not found" in error_msg.lower():
                    return False, "Repository or file not found. Check your GitHub setup."
                else:
                    return False, error_msg
            
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_csv_url(self, filename, raw=True):
        """Get direct URL to CSV file in data folder"""
        if raw:
            return f"https://raw.githubusercontent.com/{self.username}/{self.repo_name}/main/data/{filename}"
        else:
            return f"https://github.com/{self.username}/{self.repo_name}/blob/main/data/{filename}"
    
    def get_repo_status(self):
        """Get repository status information"""
        try:
            if not self.ensure_repo_exists():
                return {"status": "not_found", "message": "Repository not found"}
            
            original_cwd = Path.cwd()
            os.chdir(self.repo_path)
            
            try:
                # Check git status
                result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
                has_changes = len(result.stdout.strip()) > 0
                
                # Get last commit info
                result = subprocess.run(["git", "log", "-1", "--format=%H|%s|%cd"], capture_output=True, text=True, check=True)
                if result.stdout:
                    commit_hash, commit_msg, commit_date = result.stdout.strip().split("|", 2)
                    last_commit = {
                        "hash": commit_hash[:8],
                        "message": commit_msg,
                        "date": commit_date
                    }
                else:
                    last_commit = None
                
                # Count data files
                data_files = list(self.data_folder.glob("*.csv"))
                
                return {
                    "status": "ok",
                    "has_changes": has_changes,
                    "last_commit": last_commit,
                    "repo_url": f"https://github.com/{self.username}/{self.repo_name}",
                    "data_files_count": len(data_files),
                    "data_folder": str(self.data_folder)
                }
            
            except subprocess.CalledProcessError as e:
                return {"status": "error", "message": f"Git error: {str(e)}"}
            
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return {"status": "error", "message": f"Error checking repository: {str(e)}"}

class EnhancedStockScanner:
    def __init__(self):
        self.fyers = None
        self.cached_data = None
        self.holidays = self.load_holidays()
        
    def load_holidays(self) -> set:
        """Load holidays from embedded data or uploaded file"""
        try:
            # Default holidays for 2025 (embedded in code)
            default_holidays = [
                "2025-02-26",  # Mahashivratri
                "2025-03-14",  # Holi
                "2025-03-31",  # Id-Ul-Fitr (Ramadan Eid)
                "2025-04-10",  # Shri Mahavir Jayanti
                "2025-04-14",  # Dr. Baba Saheb Ambedkar Jayanti
                "2025-04-18",  # Good Friday
                "2025-05-01",  # Maharashtra Day
                "2025-08-15",  # Independence Day / Parsi New Year
                "2025-08-27",  # Shri Ganesh Chaturthi
                "2025-10-02",  # Mahatma Gandhi Jayanti/Dussehra
                "2025-10-21",  # Diwali Laxmi Pujan
                "2025-10-22",  # Balipratipada
                "2025-11-05",  # Prakash Gurpurb Sri Guru Nanak Dev
                "2025-12-25"   # Christmas
            ]
            
            # Try to read uploaded holidays file first
            if os.path.exists('holidays_2025.csv'):
                holidays_df = pd.read_csv('holidays_2025.csv')
                holidays = set(pd.to_datetime(holidays_df['Date'], format='%d-%b-%Y').dt.date)
                return holidays
            else:
                # Use embedded default holidays
                return set(pd.to_datetime(default_holidays).date)
        except Exception as e:
            st.warning(f"Using default holidays due to error: {str(e)}")
            # Fallback to embedded holidays
            default_holidays = [
                "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
                "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
                "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
                "2025-11-05", "2025-12-25"
            ]
            return set(pd.to_datetime(default_holidays).date)
    
    def get_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate trading days between start and end date"""
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            # Check if it's a weekday and not a holiday
            if (current_date.weekday() < 5) and (current_date.date() not in self.holidays):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def get_next_rebalance_dates(self, num_dates: int = 6) -> List[Dict]:
        """Get next few rebalance dates with proper trading day calculation"""
        rebalance_dates = []
        current_date = datetime.now(TIMEZONE).replace(day=1)
        
        for _ in range(num_dates):
            # First trading day of the month
            first_day = current_date.replace(day=1)
            trading_days = self.get_trading_days(first_day, first_day + timedelta(days=10))
            if trading_days:
                first_trading_day = trading_days[0]
                # Data cutoff is previous trading day
                data_cutoff = self.get_previous_trading_day(first_trading_day)
                
                rebalance_dates.append({
                    "rebalance_date": first_trading_day,
                    "data_cutoff_date": data_cutoff,
                    "type": "Month Start"
                })
            
            # 15th trading day of the month
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
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return sorted(rebalance_dates, key=lambda x: x['rebalance_date'])
    
    def get_previous_trading_day(self, date: datetime) -> datetime:
        """Get the previous trading day"""
        prev_day = date - timedelta(days=1)
        while prev_day.weekday() >= 5 or prev_day.date() in self.holidays:
            prev_day -= timedelta(days=1)
        return prev_day
    
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
    
    def scan_stocks(self, symbols: List[str], cutoff_date: datetime, strategy: str = "volatility", 
                   num_stocks: int = 20, lookback_period: int = 12, last_month_exclusion: int = 0) -> List[Tuple[str, float, float, float, float]]:
        """Scan and rank stocks based on momentum strategy with proper cutoff date"""
        if not self.fyers:
            st.error("Fyers not authenticated!")
            return []
        
        scores = []
        
        # Check cache first
        cache_valid = False
        cache_key = f"{cutoff_date.strftime('%Y-%m-%d')}_{strategy}_{lookback_period}"
        
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached_data = pickle.load(f)
                    if cached_data.get("cache_key") == cache_key:
                        self.cached_data = cached_data["data"]
                        cache_valid = True
                        st.success("✅ Using cached data for this configuration")
            except:
                pass
        
        if not cache_valid:
            st.info(f"📊 Fetching data until {cutoff_date.strftime('%Y-%m-%d')}... This may take a few minutes.")
            # Fetch historical data up to cutoff date
            end = cutoff_date
            start = end - pd.Timedelta(days=730)  # 2 years of data
            hist_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, symbol in enumerate(symbols):
                status_text.text(f"📈 Fetching data for {symbol} ({i+1}/{len(symbols)})")
                df = self.fetch_historical_data(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                hist_data[symbol] = df
                progress_bar.progress((i + 1) / len(symbols))
            
            self.cached_data = hist_data
            
            # Save cache
            try:
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump({
                        "cache_key": cache_key,
                        "data": hist_data,
                        "timestamp": datetime.now().isoformat()
                    }, f)
                st.success("💾 Data cached successfully")
            except Exception as e:
                st.warning(f"Could not save cache: {str(e)}")
        
        # Calculate scores
        st.info("🧮 Calculating momentum scores...")
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
        
        # Sort and return top stocks
        sorted_scores = sorted(scores, key=lambda x: x[4], reverse=True)[:num_stocks]
        return sorted_scores

def create_rebalance_calendar():
    """Create a visual rebalance calendar"""
    scanner = EnhancedStockScanner()
    rebalance_dates = scanner.get_next_rebalance_dates(12)
    
    # Create calendar visualization
    df_calendar = pd.DataFrame(rebalance_dates)
    df_calendar['rebalance_date_str'] = df_calendar['rebalance_date'].dt.strftime('%Y-%m-%d')
    df_calendar['data_cutoff_str'] = df_calendar['data_cutoff_date'].dt.strftime('%Y-%m-%d')
    
    fig = px.timeline(
        df_calendar,
        x_start="data_cutoff_date",
        x_end="rebalance_date",
        y="type",
        color="type",
        title="📅 Upcoming Rebalance Schedule",
        hover_data=['rebalance_date_str', 'data_cutoff_str']
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="Date",
        yaxis_title="Rebalance Type"
    )
    
    return fig, rebalance_dates

def create_performance_charts(results_df):
    """Create performance visualization charts"""
    if results_df.empty:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Momentum Distribution', 'Volatility vs Score', 'FITP Distribution', 'Top 10 Stocks'),
        specs=[[{"type": "histogram"}, {"type": "scatter"}],
               [{"type": "histogram"}, {"type": "bar"}]]
    )
    
    # Momentum distribution
    fig.add_trace(
        go.Histogram(x=results_df['Momentum'], name='Momentum', nbinsx=20),
        row=1, col=1
    )
    
    # Volatility vs Score scatter
    fig.add_trace(
        go.Scatter(
            x=results_df['Volatility'], 
            y=results_df['Score'],
            mode='markers+text',
            text=results_df['Symbol'],
            textposition="top center",
            name='Vol vs Score'
        ),
        row=1, col=2
    )
    
    # FITP distribution
    fig.add_trace(
        go.Histogram(x=results_df['FITP'], name='FITP', nbinsx=20),
        row=2, col=1
    )
    
    # Top 10 stocks bar chart
    top_10 = results_df.head(10)
    fig.add_trace(
        go.Bar(x=top_10['Symbol'], y=top_10['Score'], name='Top 10 Scores'),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=False, title_text="📊 Stock Analysis Dashboard")
    return fig

def display_github_status():
    """Display GitHub repository status"""
    if 'github_integration' not in st.session_state:
        st.session_state.github_integration = GitHubIntegration()
    
    status = st.session_state.github_integration.get_repo_status()
    
    if status["status"] == "ok":
        st.markdown('<div class="github-box">✅ GitHub Repository Connected</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if status["last_commit"]:
                st.markdown(f"""
                **Last Commit:** {status['last_commit']['hash']}  
                **Message:** {status['last_commit']['message']}  
                **Date:** {status['last_commit']['date']}
                """)
        
        with col2:
            if status["has_changes"]:
                st.warning("📝 Repository has uncommitted changes")
            else:
                st.success("✅ Repository is clean")
        
        if st.button("🔗 View Repository"):
            st.markdown(f"[Open Repository]({status['repo_url']})")
    
    elif status["status"] == "not_found":
        st.markdown('<div class="warning-box">⚠️ GitHub repository not found</div>', unsafe_allow_html=True)
        st.info("Please set up your data repository first using the setup guide.")
    
    else:
        st.markdown(f'<div class="warning-box">❌ Repository Error: {status["message"]}</div>', unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 Fyers Stock Scanner Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Advanced momentum-based stock screening with rebalance date intelligence")
    
    # Initialize scanner
    if 'scanner' not in st.session_state:
        st.session_state.scanner = EnhancedStockScanner()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Control Panel")
        
        # Authentication section
        st.subheader("🔐 Fyers Authentication")
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={FYERS_CONFIG['client_id']}&redirect_uri={FYERS_CONFIG['redirect_uri']}&response_type=code&state=None"
        st.markdown(f"**Step 1:** [🔗 Get Authorization Code]({auth_url})")
        
        auth_code = st.text_input(
            "**Step 2:** Enter Authorization Code:",
            type="password",
            help="Paste the authorization code from Fyers"
        )
        
        if st.button("🔑 Authenticate", type="primary"):
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
        
        # GitHub Configuration
        st.subheader("📂 GitHub Configuration")
        github_username = st.text_input(
            "GitHub Username:",
            value=GITHUB_CONFIG["username"],
            help="Your GitHub username for the data repository"
        )
        
        if github_username != GITHUB_CONFIG["username"]:
            GITHUB_CONFIG["username"] = github_username
            if 'github_integration' in st.session_state:
                st.session_state.github_integration.username = github_username
        
        # Display GitHub status
        display_github_status()
        
        # Scanner parameters
        st.subheader("📊 Scanner Parameters")
        strategy = st.selectbox("Strategy:", ["volatility", "fitp", "momentum"], help="Momentum scoring strategy")
        num_stocks = st.slider("Number of stocks:", 5, 50, 20)
        lookback_period = st.slider("Lookback period (months):", 3, 24, 12)
        last_month_exclusion = st.slider("Last month exclusion:", 0, 3, 0)
        
        # Store in session state for charts
        st.session_state.strategy = strategy
        st.session_state.num_stocks = num_stocks
        st.session_state.lookback_period = lookback_period
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Scanner", "📅 Rebalance Calendar", "📊 Analytics", "🔗 GitHub", "ℹ️ About"])
    
    with tab1:
        if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
            st.markdown('<div class="info-box">👆 Please authenticate with Fyers using the sidebar first</div>', unsafe_allow_html=True)
            
            # Show sample data format
            st.subheader("📋 Sample Data Format")
            sample_df = pd.DataFrame({
                "Symbol": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
                "Company Name": ["Reliance Industries", "Tata Consultancy Services", "Infosys", "HDFC Bank", "ICICI Bank"],
                "Industry": ["Oil & Gas", "IT Services", "IT Services", "Banking", "Banking"]
            })
            st.dataframe(sample_df, use_container_width=True)
            
        else:
            # Rebalance date selection
            st.subheader("📅 Select Rebalance Date")
            rebalance_dates = st.session_state.scanner.get_next_rebalance_dates(6)
            
            col1, col2 = st.columns(2)
            with col1:
                selected_rebalance = st.selectbox(
                    "Choose rebalance date:",
                    options=range(len(rebalance_dates)),
                    format_func=lambda x: f"{rebalance_dates[x]['rebalance_date'].strftime('%Y-%m-%d')} ({rebalance_dates[x]['type']})"
                )
            
            with col2:
                if selected_rebalance is not None:
                    selected_date_info = rebalance_dates[selected_rebalance]
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Data Cutoff Date</h4>
                        <h3>{selected_date_info['data_cutoff_date'].strftime('%Y-%m-%d')}</h3>
                        <p>Data will be fetched until this date</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Stock universe selection
            st.subheader("📁 Stock Universe")
            
            # Default stock list (embedded in code for Streamlit Cloud)
            default_symbols = [
                "360ONE", "AADHARHFC", "AARTIIND", "AAVAS", "ACE", "ABREL", "ABSLAMC", "ADANIENSOL", "ADANIREALTY", 
                "AFFLE", "AGARIND", "AGRITECH", "AHLEAST", "AIFL", "AIREN", "AKSHOPTFBR", "ALKYLAMINE", "ALLCARGO", 
                "ALOKINDS", "AMBER", "AMJLAND", "ANANTRAJ", "ANGELONE", "ANURAS", "APCOTEXIND", "APLAPOLLO", "APOLLOTYRE", 
                "APTUS", "ARMANFIN", "ARVSMART", "ASAHIINDIA", "ASHOKA", "ASTERDM", "ASTRAL", "ATUL", "AVANTIFEED", 
                "AWHCL", "AXISBANK", "BALAMINES", "BALRAMCHIN", "BANARISUG", "BANDHANBNK", "BASF", "BATAINDIA", 
                "BAYERCROP", "BBL", "BECTORFOOD", "BEML", "BERGEPAINT", "BHARATFORG", "BHARTIHEXA", "BHEL", 
                "BIKAJI", "BIRLACORPN", "BLUEDART", "BLUESTARCO", "BOFT", "BOMDYEING", "BPCL", "BSE", 
                "BSOFT", "CANFINHOME", "CAMS", "CARBORUNIV", "CARERATING", "CARTRADE", "CASTROLIND", "CCL", 
                "CEATLTD", "CENTRALBK", "CENTURYPLY", "CENTURYTEX", "CERA", "CHALET", "CHAMBLFERT", "CHENNPETRO", 
                "CHOLAHLDNG", "CHOLAFIN", "COCHINSHIP", "COFORGE", "COLPAL", "CONFIPET", "CORDSCABLE", "COROMANDEL", 
                "COSMOFIRST", "CRAFTSMAN", "CREDITACC", "CRISIL", "CROMPTON", "CUB", "CUMMINSIND", "CYIENT", 
                "DALMIASUG", "DATAPATTNS", "DCBBANK", "DCMSHRIRAM", "DEEPAKFERT", "DEEPAKNTR", "DELTACORP", "DEVYANI", 
                "DHANI", "DHANUKA", "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "EICHERMOT", 
                "EIDPARRY", "EIHOTEL", "ELECON", "ELGIEQUIP", "EMAMILTD", "ENDURANCE", "ENGINERSIN", "EQUITAS", 
                "ERIS", "ESABINDIA", "ESCORTS", "EXIDEIND", "FACT", "FDC", "FEDERALBNK", "FEDFINA", 
                "FELDVR", "FIEMIND", "FINPIPE", "FIVESTAR", "FORTIS", "FSL", "GALAXYSURF", "GARFIBRES", 
                "GESHIP", "GET&D", "GICRE", "GILLETTE", "GLAND", "GLAXO", "GLENMARK", "GLOBALVECT", 
                "GNFC", "GODFRYPHLP", "GODREJCP", "GODREJIND", "GODREJPROP", "GPPL", "GRANULES", "GRAPHITE", 
                "GRASIM", "GREAVESCOT", "GRINDWELL", "GRSE", "GSFC", "GSPL", "GUJALKALI", "GUJGASLTD", 
                "GULFOILLUB", "HAL", "HAPPSTMNDS", "HATHWAY", "HATSUN", "HAVELLS", "HCG", "HDFCAMC", 
                "HDFCLIFE", "HEG", "HEROMOTOCO", "HFCL", "HIKAL", "HINDALCO", "HINDCOPPER", "HINDPETRO", 
                "HINDUNILVR", "HLEGLAS", "HOMEFIRST", "HONASA", "HSCL", "HUDCO", "ICICIPRULI", "IDEA", 
                "IDFC", "IDFCFIRSTB", "IEX", "IFBIND", "IIFL", "INDHOTEL", "INDIACEM", "INDIAMART", 
                "INDIANB", "INDIGO", "INDOCO", "INDOSTAR", "INDUSINDBK", "INDUSTOWER", "INFIBEAM", "INFY", 
                "INGERRAND", "INOXLEISUR", "INSPIRISYS", "INTELLECT", "IOB", "IOLCP", "IONEXCHANG", "IRCON", 
                "IRFC", "ITC", "ITI", "J&KBANK", "JBCHEPHARM", "JKCEMENT", "JKLAKSHMI", "JKPAPER", 
                "JMFINANCIL", "JSL", "JSWENERGY", "JSWINFRA", "JUBLFOOD", "JUBLPHARMA", "JUSTDIAL", "JYOTHYLAB", 
                "KAJARIACER", "KALPATPOWR", "KALYANKJIL", "KAMATHOTEL", "KANSAINER", "KEC", "KEI", "KFINTECH", 
                "KIMS", "KIRLOSENG", "KIRLOSIND", "KNRCON", "KOLTEPATIL", "KRBL", "KPITTECH", "KSBL", 
                "KSB", "LAOPALA", "LATENTVIEW", "LAXMIMACH", "LCCINFOTEC", "LEMONTREE", "LEUCINE", "LGBBROSLTD", 
                "LICI", "LICHSGFIN", "LINDEINDIA", "LLOYDSME", "LT", "LTF", "LTTS", "LUPIN", 
                "LUXIND", "LXCHEM", "LYKALABS", "M&M", "M&MFIN", "MAHABANK", "MAHLOG", "MANAPPURAM", 
                "MARICO", "MARUTI", "MASTEK", "MAXHEALTH", "MAZAGON", "MCDOWELL-N", "MCX", "MEDPLUS", 
                "METROBRAND", "MFSL", "MGL", "MHRIL", "MIDHANI", "MMTC", "MOIL", "MOTHERSON", 
                "MPHASIS", "MRF", "MSUMI", "MTARTECH", "MUTHOOTFIN", "NAM-INDIA", "NATCOPHARM", "NAUKRI", 
                "NAVINFLUOR", "NBCC", "NCC", "NESTLEIND", "NETWEB", "NEWGEN", "NH", "NHPC", 
                "NIACL", "NIITLTD", "NMDC", "NOCIL", "NSLNISP", "NTPC", "NUVOCO", "NYKAA", 
                "OBEROIRLTY", "OFSS", "OIL", "ONGC", "PANATONE", "PATANJALI", "PAYTM", "PB", 
                "PEL", "PERSISTENT", "PETRONET", "PFC", "PFIZER", "PGHH", "PHOENIXLTD", "PIDILITIND", 
                "PIIND", "PNB", "PNBHOUSING", "PNCINFRA", "POLYCAB", "POONAWALLA", "POWERGRID", "POWERINDIA", 
                "PPSMPL", "PRAJIND", "PRESTIGE", "PRSMJOHNSN", "PTC", "PTL", "PVRINOX", "QUESS", 
                "RADICO", "RAILTEL", "RAJESHEXPO", "RALLIS", "RAMCOCEM", "RANEHOLDIN", "RBLBANK", "RCF", 
                "RECLTD", "REDINGTON", "RELAXO", "RELIANCE", "RENUKA", "REPCOHOME", "RESPONIND", "RVNL", 
                "SAFARI", "SAIL", "SANOFI", "SAPPHIRE", "SARDAEN", "SBICARD", "SBILIFE", "SCHAEFFLER", 
                "SCHNEIDER", "SCI", "SFL", "SGBL", "SHANKARA", "SHARDACROP", "SHILPAMED", "SHOPERSTOP", 
                "SHREECEM", "SHREYAS", "SHRIRAMFIN", "SHYAMMETL", "SIEMENS", "SIS", "SJVN", "SKFINDIA", 
                "SRF", "STARHEALTH", "STELCO", "SUBEXLTD", "SUNTECK", "SUNTV", "SUPRAJIT", "SUPRIYA", 
                "SURYAROSNI", "SUZLON", "SWANENERGY", "SYMPHONY", "SYNGENE", "TARSONS", "TATACOMM", "TATACONSUM", 
                "TATAELXSI", "TATAINVEST", "TATAMOTORS", "TATAPOWER", "TATATECH", "TCS", "TECHM", "THERMAX", 
                "THYROCARE", "TIPSINDLTD", "TITAGARH", "TITAN", "TNPETRO", "TRENT", "TRIDENT", "TRITURBINE", 
                "TTKPRESTIG", "TV18BRDCST", "TVSHLTD", "TVSSCS", "UBL", "ULTRACEMCO", "UNOMINDA", "UPL", 
                "UTIAMC", "UTTAMSUGAR", "VEDL", "VENKEYS", "VGUARD", "VINATIORGA", "VIPIND", "VMART", 
                "VOLTAMP", "VOLTAS", "VTL", "WELCORP", "WESTLIFE", "WHIRLPOOL", "WIPRO", "WOCKPHARMA", 
                "YESBANK", "ZEEL", "ZENSARTECH", "ZFCVINDIA", "ZOMATO", "ZYDUSWELL"
            ]
            
            # Stock universe options
            stock_source = st.radio(
                "Choose your stock universe:",
                ["📈 Default Nifty SmallCap 250", "📁 Upload Custom List", "✏️ Manual Selection"],
                horizontal=True
            )
            
            if stock_source == "📈 Default Nifty SmallCap 250":
                symbols = default_symbols
                st.success(f"✅ Using Nifty SmallCap 250 list ({len(symbols)} symbols)")
                
                # Show sample stocks
                with st.expander(f"📋 View stock list ({len(symbols)} symbols)"):
                    # Display in columns for better visualization
                    cols = st.columns(5)
                    for i, symbol in enumerate(symbols):
                        with cols[i % 5]:
                            st.write(f"• {symbol}")
                
            elif stock_source == "📁 Upload Custom List":
                uploaded_file = st.file_uploader("Upload CSV with 'Symbol' column", type="csv")
                
                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        if 'Symbol' in df.columns:
                            symbols = df['Symbol'].tolist()
                            st.success(f"✅ Loaded {len(symbols)} symbols from uploaded file")
                            st.dataframe(df.head(), use_container_width=True)
                        else:
                            st.error("❌ CSV file must have a 'Symbol' column")
                            symbols = default_symbols[:20]  # Fallback
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
                        symbols = default_symbols[:20]  # Fallback
                else:
                    st.info("📤 Please upload a CSV file")
                    symbols = default_symbols[:20]  # Show sample until upload
                    
            else:  # Manual Selection
                st.info("✏️ Enter stock symbols separated by commas")
                manual_symbols = st.text_area(
                    "Stock Symbols:",
                    value="RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK",
                    help="Enter stock symbols separated by commas"
                )
                
                if manual_symbols:
                    symbols = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()]
                    st.success(f"✅ {len(symbols)} symbols ready: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
                else:
                    symbols = default_symbols[:20]
            
            # Scan button
            if symbols and st.button("🔍 Start Stock Scan", type="primary"):
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
                            st.markdown('<div class="success-box">✅ Scan completed successfully!</div>', unsafe_allow_html=True)
                            
                            # Display results
                            st.subheader("🏆 Top Momentum Stocks")
                            
                            results_df = pd.DataFrame(results, columns=[
                                "Symbol", "Momentum", "Volatility", "FITP", "Score"
                            ])
                            
                            # ✅ IMPORTANT: Store in session state to persist across button clicks
                            st.session_state.results_df = results_df
                            st.session_state.scan_info = {
                                "cutoff_date": cutoff_date,
                                "rebalance_date": selected_date_info['rebalance_date'],
                                "total_symbols": len(symbols),
                                "strategy": strategy,
                                "completed": True  # Add this flag
                            }
                            st.session_state.scan_completed = True  # Add this flag
                            
                            # Format for display
                            display_df = results_df.copy()
                            display_df["Momentum"] = display_df["Momentum"].apply(lambda x: f"{x:.4f}")
                            display_df["Volatility"] = display_df["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                            display_df["FITP"] = display_df["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                            display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.4f}")
                            display_df.index = range(1, len(display_df) + 1)
                            
                            st.dataframe(display_df, use_container_width=True)
                            
                        else:
                            st.warning("⚠️ No stocks found matching the criteria")
                            
                    except Exception as e:
                        st.error(f"❌ Error during scan: {str(e)}")
                else:
                    st.warning("Please select a rebalance date")
    
    # GitHub Integration - MOVED OUTSIDE the if results block
    # Show GitHub Integration if we have completed scan results
    if hasattr(st.session_state, 'scan_completed') and st.session_state.scan_completed:
        st.subheader("🔗 GitHub Integration")
        
        # Debug information
        st.write(f"**Debug Info:**")
        st.write(f"- Scan completed: {st.session_state.scan_completed}")
        st.write(f"- Results available: {hasattr(st.session_state, 'results_df')}")
        if hasattr(st.session_state, 'results_df'):
            st.write(f"- Results rows: {len(st.session_state.results_df)}")
        
        if 'github_integration' not in st.session_state:
            st.session_state.github_integration = GitHubIntegration()
        
        # Get the scan info from session state
        if hasattr(st.session_state, 'scan_info'):
            scan_info = st.session_state.scan_info
            cutoff_date = scan_info['cutoff_date']
            strategy = scan_info['strategy']
            results_df = st.session_state.results_df
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Generate timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                github_filename = f"stock_scan_{cutoff_date.strftime('%Y%m%d')}_{strategy}_{timestamp}.csv"
                
                st.write(f"**Will create file:** `{github_filename}`")
                
                if st.button("📤 Push to GitHub", type="primary", key="push_github_persistent"):
                    st.write("🔵 Button clicked!")
                    
                    with st.spinner("Pushing to GitHub..."):
                        try:
                            success, message = st.session_state.github_integration.push_csv_to_github(
                                results_df, 
                                github_filename,
                                f"Stock scan results - {strategy} strategy - {cutoff_date.strftime('%Y-%m-%d')}"
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                                raw_url = st.session_state.github_integration.get_csv_url(github_filename, raw=True)
                                st.session_state.latest_csv_url = raw_url
                                st.session_state.latest_filename = github_filename
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                                
                        except Exception as e:
                            st.error(f"❌ Exception: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            with col2:
                latest_filename = "latest_stock_scan.csv"
                if st.button("🔄 Update Latest", key="update_latest_persistent"):
                    st.write("🔵 Update Latest clicked!")
                    
                    with st.spinner("Updating latest file..."):
                        try:
                            success, message = st.session_state.github_integration.push_csv_to_github(
                                results_df, 
                                latest_filename,
                                f"Update latest scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                                latest_url = st.session_state.github_integration.get_csv_url(latest_filename, raw=True)
                                st.session_state.latest_csv_url = latest_url
                                st.session_state.latest_filename = latest_filename
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                                
                        except Exception as e:
                            st.error(f"❌ Exception: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            with col3:
                if st.button("🔄 Clear Scan", key="clear_scan"):
                    # Clear the scan results
                    if 'scan_completed' in st.session_state:
                        del st.session_state.scan_completed
                    if 'results_df' in st.session_state:
                        del st.session_state.results_df
                    if 'scan_info' in st.session_state:
                        del st.session_state.scan_info
                    st.success("Scan results cleared!")
                    st.rerun()
            
            # Display current URLs if available
            if hasattr(st.session_state, 'latest_csv_url'):
                st.subheader("🌐 Access URLs")
                
                url_col1, url_col2 = st.columns(2)
                
                with url_col1:
                    st.markdown("**Raw CSV URL (for other apps):**")
                    st.code(st.session_state.latest_csv_url, language="text")
                    
                    # Test URL
                    if st.button("🧪 Test URL", key="test_url"):
                        try:
                            response = requests.get(st.session_state.latest_csv_url, timeout=10)
                            if response.status_code == 200:
                                st.success("✅ URL is accessible")
                                lines = response.text.split('\n')[:3]
                                st.text("Preview:")
                                for line in lines:
                                    st.text(line)
                            else:
                                st.error(f"❌ URL returned status code: {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Error testing URL: {str(e)}")
                
                with url_col2:
                    if hasattr(st.session_state, 'latest_filename'):
                        github_url = st.session_state.github_integration.get_csv_url(st.session_state.latest_filename, raw=False)
                        st.markdown("**GitHub View URL:**")
                        st.code(github_url, language="text")
                        
                        if st.button("🔗 Open in GitHub", key="open_github"):
                            st.markdown(f"[View file on GitHub]({github_url})")
    
    with tab2:
        st.subheader("📅 Rebalance Calendar & Trading Days")
        
        # Create and display calendar
        calendar_fig, rebalance_dates = create_rebalance_calendar()
        st.plotly_chart(calendar_fig, use_container_width=True)
        
        # Detailed rebalance schedule
        st.subheader("📋 Detailed Schedule")
        schedule_df = pd.DataFrame(rebalance_dates)
        schedule_df['Rebalance Date'] = schedule_df['rebalance_date'].dt.strftime('%Y-%m-%d (%A)')
        schedule_df['Data Cutoff'] = schedule_df['data_cutoff_date'].dt.strftime('%Y-%m-%d (%A)')
        schedule_df['Days Until'] = (schedule_df['rebalance_date'] - datetime.now(TIMEZONE)).dt.days
        
        display_schedule = schedule_df[['type', 'Rebalance Date', 'Data Cutoff', 'Days Until']].copy()
        display_schedule.columns = ['Type', 'Rebalance Date', 'Data Cutoff Date', 'Days Until']
        display_schedule.index = range(1, len(display_schedule) + 1)
        
        st.dataframe(display_schedule, use_container_width=True)
        
        # Holiday information
        st.subheader("🎭 Market Holidays 2025")
        if st.session_state.scanner.holidays:
            holidays_list = sorted(list(st.session_state.scanner.holidays))
            holidays_df = pd.DataFrame({
                'Date': [h.strftime('%Y-%m-%d (%A)') for h in holidays_list],
                'Days from Today': [(h - datetime.now().date()).days for h in holidays_list]
            })
            holidays_df.index = range(1, len(holidays_df) + 1)
            st.dataframe(holidays_df, use_container_width=True)
        else:
            st.info("No holiday data loaded")
    
    with tab3:
        st.subheader("📊 Analytics Dashboard")
        
        if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty:
            # Scan summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_momentum = st.session_state.results_df['Momentum'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📈 Avg Momentum</h4>
                    <h3>{avg_momentum:.4f}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_volatility = st.session_state.results_df['Volatility'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📊 Avg Volatility</h4>
                    <h3>{avg_volatility:.4f}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                top_score = st.session_state.results_df['Score'].max()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🏆 Top Score</h4>
                    <h3>{top_score:.4f}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                positive_momentum = (st.session_state.results_df['Momentum'] > 0).sum()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📈 Positive Momentum</h4>
                    <h3>{positive_momentum}/{len(st.session_state.results_df)}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Performance charts
            perf_fig = create_performance_charts(st.session_state.results_df)
            if perf_fig:
                st.plotly_chart(perf_fig, use_container_width=True)
        
        else:
            st.markdown('<div class="info-box">📊 Run a stock scan first to see analytics</div>', unsafe_allow_html=True)
    
    with tab4:
        st.subheader("🔗 GitHub Integration Management")
        
        # Initialize GitHub integration
        if 'github_integration' not in st.session_state:
            st.session_state.github_integration = GitHubIntegration()
        
        # Repository Status
        st.subheader("📊 Repository Status")
        status = st.session_state.github_integration.get_repo_status()
        
        if status["status"] == "ok":
            st.markdown('<div class="success-box">✅ Repository Connected</div>', unsafe_allow_html=True)
            st.markdown(f"**Repository:** {st.session_state.github_integration.username}/{st.session_state.github_integration.repo_name}")
            
            if status["last_commit"]:
                st.markdown(f"""
                **Last Commit:** {status['last_commit']['hash']}  
                **Message:** {status['last_commit']['message']}
                """)
        
        else:
            st.markdown('<div class="warning-box">⚠️ Repository not properly configured</div>', unsafe_allow_html=True)
        
        # Current URLs
        if hasattr(st.session_state, 'latest_filename'):
            st.subheader("🌐 Current URLs")
            filename = st.session_state.latest_filename
            raw_url = st.session_state.github_integration.get_csv_url(filename, raw=True)
            
            st.markdown("**Raw CSV URL (for other applications):**")
            st.code(raw_url, language="text")
        
        else:
            st.info("No files have been uploaded to GitHub yet. Run a scan first.")
    
    with tab5:
        st.subheader("ℹ️ About Fyers Stock Scanner Pro")
        
        st.markdown("""
        ### 🎯 Purpose
        This advanced stock scanning application helps you identify momentum-based investment opportunities 
        using sophisticated technical analysis, perfectly timed with rebalance dates.
        
        ### 🔬 Methodology
        
        **Momentum Calculation:**
        - Looks back 12 months (configurable) from the data cutoff date
        - Calculates price momentum excluding the last month to avoid recency bias
        - Uses closing prices for accuracy
        
        **Scoring Strategies:**
        1. **Volatility-Adjusted:** `Score = Momentum / Volatility`
        2. **FITP (Fraction in Trend Period):** `Score = Momentum × FITP`
        3. **Pure Momentum:** `Score = Momentum`
        
        **FITP Explained:**
        - For positive momentum: Fraction of days with positive returns
        - For negative momentum: Fraction of days with negative returns
        - Measures consistency of the trend
        
        ### 📅 Rebalance Intelligence
        - Automatically calculates proper trading days
        - Excludes weekends and market holidays
        - Ensures data cutoff is the last trading day before rebalance
        - Supports both month-start and mid-month rebalancing
        
        ### 🔧 Features
        - **Smart Caching:** Avoids re-downloading data for the same configuration
        - **Holiday Awareness:** Built-in 2025 market holiday calendar
        - **Multiple Export Formats:** CSV, Pickle, and summary reports
        - **Visual Analytics:** Interactive charts and performance metrics
        - **GitHub Integration:** Automatic CSV upload with direct URL access
        - **Cross-Platform Access:** URLs work with JavaScript, Python, Java, and more
        - **Session Persistence:** Scan results persist across page refreshes
        
        ### 🔗 GitHub Integration Benefits
        - **Automatic Upload:** Push CSV files directly to GitHub
        - **Direct URL Access:** Get raw URLs for immediate use in other applications
        - **Version Control:** All scans are tracked with timestamps
        - **Global Accessibility:** Access your data from anywhere
        - **API-like Access:** Use GitHub as a simple data API
        - **File Replacement:** Automatically overwrites existing files
        
        ### 📊 Data Sources
        - **Market Data:** Fyers API (real-time and historical)
        - **Stock Universe:** Configurable (default: Nifty SmallCap 250)
        - **Holidays:** NSE holiday calendar for 2025
        
        ### 🚀 Usage Workflow
        1. **Setup:** Configure GitHub repository in sidebar
        2. **Authenticate** with your Fyers account
        3. **Select** the next rebalance date
        4. **Upload** or use default stock list
        5. **Configure** strategy and parameters
        6. **Scan** and analyze results
        7. **Push to GitHub** for automated access
        8. **Use URLs** in your other applications
        
        ### ⚡ Performance Tips
        - Data is cached per configuration to speed up subsequent scans
        - Use the "Update Latest" feature for consistent file names
        - Test URLs before integrating with other applications
        - Monitor the rebalance calendar for optimal timing
        - Use "Clear Scan" to reset and start fresh
        
        ### 🔒 Security & Privacy
        - Authentication tokens are temporary and not stored
        - All data processing happens locally in your browser session
        - GitHub integration uses public repositories (recommended for data sharing)
        - No sensitive information is transmitted to external servers
        
        ### 📈 Best Practices
        - Run scans 1-2 days before rebalance dates
        - Compare different strategies for validation
        - Monitor consistency across multiple time periods
        - Consider market conditions when interpreting results
        - Keep your GitHub repository organized with clear naming conventions
        
        ### 🆕 Latest Updates (v3.1)
        - **Session State Management:** Scan results persist across button clicks
        - **Improved Error Handling:** Better debugging and error messages
        - **Enhanced GitHub Integration:** Automatic file replacement and URL generation
        - **Debug Information:** Real-time status updates during operations
        - **Cross-Platform URLs:** Direct access for JavaScript, Python, Java applications
        
        ---
        
        **Version:** 3.1 Pro with Enhanced Session Management | **Last Updated:** January 2025
        
        *Built with ❤️ for systematic momentum investing and seamless data integration*
        """)

if __name__ == "__main__":
    main()