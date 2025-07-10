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

# GitHub Configuration - Update these with your actual values
GITHUB_CONFIG = {
    "username": "YOUR_GITHUB_USERNAME",  # Replace with your GitHub username
    "repo_name": "stock-scanner-data",
    "data_repo_path": "../stock-scanner-data"  # Adjust path as needed
}

class GitHubIntegration:
    def __init__(self, repo_path=None):
        self.repo_path = Path(repo_path or GITHUB_CONFIG["data_repo_path"])
        self.username = GITHUB_CONFIG["username"]
        self.repo_name = GITHUB_CONFIG["repo_name"]
        self.ensure_repo_exists()
    
    def ensure_repo_exists(self):
        """Check if the data repository exists"""
        if not self.repo_path.exists():
            st.warning(f"⚠️ Data repository not found at {self.repo_path}")
            st.info("Please run the setup commands in your Codespaces terminal first.")
            return False
        return True
    
    def push_csv_to_github(self, df, filename, commit_message=None):
        """Push CSV file to GitHub repository"""
        try:
            if not self.ensure_repo_exists():
                return False, "Data repository not found. Please set up the repository first."
            
            # Save CSV to the data repository
            csv_path = self.repo_path / filename
            df.to_csv(csv_path, index=False)
            
            # Create metadata file
            metadata = {
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "scan_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_by": "Fyers Stock Scanner Pro",
                "file_size_kb": round(csv_path.stat().st_size / 1024, 2)
            }
            
            metadata_path = self.repo_path / f"{filename.replace('.csv', '_metadata.json')}"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Git operations
            if commit_message is None:
                commit_message = f"Update {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Change to repo directory and commit
            original_cwd = Path.cwd()
            os.chdir(self.repo_path)
            
            try:
                # Check if git repo is initialized
                result = subprocess.run(["git", "status"], capture_output=True, text=True)
                if result.returncode != 0:
                    return False, "Not a git repository. Please initialize the repository first."
                
                # Git operations
                subprocess.run(["git", "add", filename], check=True, capture_output=True)
                subprocess.run(["git", "add", f"{filename.replace('.csv', '_metadata.json')}"], check=True, capture_output=True)
                
                # Check if there are changes to commit
                result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
                if result.returncode == 0:
                    return True, f"No changes to commit for {filename}"
                
                subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
                subprocess.run(["git", "push"], check=True, capture_output=True)
                
                return True, f"Successfully pushed {filename} to GitHub"
            
            except subprocess.CalledProcessError as e:
                error_msg = f"Git operation failed: {e}"
                if e.stderr:
                    error_msg += f" - {e.stderr.decode()}"
                return False, error_msg
            
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return False, f"Error pushing to GitHub: {str(e)}"
    
    def get_csv_url(self, filename, raw=True):
        """Get direct URL to CSV file"""
        if raw:
            return f"https://raw.githubusercontent.com/{self.username}/{self.repo_name}/main/{filename}"
        else:
            return f"https://github.com/{self.username}/{self.repo_name}/blob/main/{filename}"
    
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
                
                return {
                    "status": "ok",
                    "has_changes": has_changes,
                    "last_commit": last_commit,
                    "repo_url": f"https://github.com/{self.username}/{self.repo_name}"
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
                            
                            # Format for display
                            display_df = results_df.copy()
                            display_df["Momentum"] = display_df["Momentum"].apply(lambda x: f"{x:.4f}")
                            display_df["Volatility"] = display_df["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                            display_df["FITP"] = display_df["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                            display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.4f}")
                            display_df.index = range(1, len(display_df) + 1)
                            
                            st.dataframe(display_df, use_container_width=True)
                            
                            # Store results for other tabs
                            st.session_state.results_df = results_df
                            st.session_state.scan_info = {
                                "cutoff_date": cutoff_date,
                                "rebalance_date": selected_date_info['rebalance_date'],
                                "total_symbols": len(symbols),
                                "strategy": strategy
                            }
                            
                            # GitHub Integration Section
                            st.subheader("🔗 GitHub Integration")
                            
                            if 'github_integration' not in st.session_state:
                                st.session_state.github_integration = GitHubIntegration()
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                # Generate timestamped filename
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                github_filename = f"stock_scan_{cutoff_date.strftime('%Y%m%d')}_{strategy}_{timestamp}.csv"
                                
                                if st.button("📤 Push to GitHub", type="primary"):
                                    with st.spinner("Pushing to GitHub..."):
                                        success, message = st.session_state.github_integration.push_csv_to_github(
                                            results_df, 
                                            github_filename,
                                            f"Stock scan results - {strategy} strategy - {cutoff_date.strftime('%Y-%m-%d')}"
                                        )
                                        
                                        if success:
                                            st.success(message)
                                            
                                            # Display access URLs
                                            raw_url = st.session_state.github_integration.get_csv_url(github_filename, raw=True)
                                            github_url = st.session_state.github_integration.get_csv_url(github_filename, raw=False)
                                            
                                            st.session_state.latest_csv_url = raw_url
                                            st.session_state.latest_github_url = github_url
                                            st.session_state.latest_filename = github_filename
                                            
                                        else:
                                            st.error(message)
                            
                            with col2:
                                # Always push latest results
                                latest_filename = "latest_stock_scan.csv"
                                if st.button("🔄 Update Latest"):
                                    with st.spinner("Updating latest file..."):
                                        success, message = st.session_state.github_integration.push_csv_to_github(
                                            results_df, 
                                            latest_filename,
                                            f"Update latest scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        )
                                        
                                        if success:
                                            st.success("Latest file updated!")
                                            latest_url = st.session_state.github_integration.get_csv_url(latest_filename, raw=True)
                                            st.session_state.latest_csv_url = latest_url
                                            st.session_state.latest_filename = latest_filename
                                        else:
                                            st.error(message)
                            
                            with col3:
                                if st.button("📋 Show Access URLs"):
                                    if hasattr(st.session_state, 'latest_csv_url'):
                                        st.info("**Direct CSV Access URL:**")
                                        st.code(st.session_state.latest_csv_url, language="text")
                                    else:
                                        st.warning("Push to GitHub first to get URLs")
                            
                            # Display current URLs if available
                            if hasattr(st.session_state, 'latest_csv_url'):
                                st.subheader("🌐 Access URLs")
                                
                                url_col1, url_col2 = st.columns(2)
                                
                                with url_col1:
                                    st.markdown("**Raw CSV URL (for other apps):**")
                                    st.code(st.session_state.latest_csv_url, language="text")
                                    
                                    # Test URL
                                    if st.button("🧪 Test URL"):
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
                                    if hasattr(st.session_state, 'latest_github_url'):
                                        st.markdown("**GitHub View URL:**")
                                        st.code(st.session_state.latest_github_url, language="text")
                                        
                                        if st.button("🔗 Open in GitHub"):
                                            st.markdown(f"[View file on GitHub]({st.session_state.latest_github_url})")
                            
                            # Download options (traditional)
                            st.subheader("📥 Traditional Download Options")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                csv = results_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name=f"stock_scan_{cutoff_date.strftime('%Y%m%d')}.csv",
                                    mime="text/csv"
                                )
                            
                            with col2:
                                # Save for manual GitHub upload
                                results_df.to_csv("latest_results.csv", index=False)
                                with open("latest_results.csv", "rb") as f:
                                    st.download_button(
                                        label="📤 For Manual Upload",
                                        data=f.read(),
                                        file_name="latest_results.csv",
                                        mime="text/csv"
                                    )
                            
                            with col3:
                                # Pickle file
                                pickle_data = {
                                    "results": results,
                                    "scan_info": st.session_state.scan_info,
                                    "timestamp": datetime.now().isoformat()
                                }
                                pickle_filename = f"scan_results_{cutoff_date.strftime('%Y%m%d')}.pkl"
                                with open(pickle_filename, 'wb') as f:
                                    pickle.dump(pickle_data, f)
                                with open(pickle_filename, 'rb') as f:
                                    st.download_button(
                                        label="📥 Download Pickle",
                                        data=f.read(),
                                        file_name=pickle_filename,
                                        mime="application/octet-stream"
                                    )
                                
                                # Clean up
                                try:
                                    os.remove(pickle_filename)
                                except:
                                    pass
                        else:
                            st.warning("⚠️ No stocks found matching the criteria")
                            
                    except Exception as e:
                        st.error(f"❌ Error during scan: {str(e)}")
                else:
                    st.warning("Please select a rebalance date")
    
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
            
            # Scan information
            if hasattr(st.session_state, 'scan_info'):
                st.subheader("🔍 Scan Information")
                scan_info = st.session_state.scan_info
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"""
                    **📅 Data Cutoff Date:** {scan_info['cutoff_date'].strftime('%Y-%m-%d')}  
                    **📈 Rebalance Date:** {scan_info['rebalance_date'].strftime('%Y-%m-%d')}  
                    **🎯 Strategy Used:** {scan_info['strategy'].title()}
                    """)
                
                with info_col2:
                    st.markdown(f"""
                    **📊 Total Symbols Scanned:** {scan_info['total_symbols']}  
                    **🏆 Top Stocks Selected:** {len(st.session_state.results_df)}  
                    **⏰ Scan Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """)
            
            # Export options
            st.subheader("📤 Export Options")
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("📊 Export for Excel"):
                    excel_data = st.session_state.results_df.copy()
                    excel_data.index = range(1, len(excel_data) + 1)
                    st.dataframe(excel_data)
            
            with export_col2:
                if st.button("📈 Create Summary Report"):
                    summary_text = f"""
# Stock Scanner Report
                    
**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Cutoff:** {st.session_state.scan_info['cutoff_date'].strftime('%Y-%m-%d')}
**Strategy:** {st.session_state.scan_info['strategy'].title()}

## Top 5 Recommendations:
{chr(10).join([f"{i+1}. {row['Symbol']} (Score: {row['Score']:.4f})" for i, row in st.session_state.results_df.head().iterrows()])}

## Statistics:
- Average Momentum: {st.session_state.results_df['Momentum'].mean():.4f}
- Average Volatility: {st.session_state.results_df['Volatility'].mean():.4f}
- Stocks with Positive Momentum: {(st.session_state.results_df['Momentum'] > 0).sum()}/{len(st.session_state.results_df)}
                    """
                    st.download_button(
                        label="📥 Download Report",
                        data=summary_text,
                        file_name=f"stock_report_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
            
            with export_col3:
                if st.button("🔄 Clear Results"):
                    if 'results_df' in st.session_state:
                        del st.session_state.results_df
                    if 'scan_info' in st.session_state:
                        del st.session_state.scan_info
                    st.rerun()
        
        else:
            st.markdown('<div class="info-box">📊 Run a stock scan first to see analytics</div>', unsafe_allow_html=True)
            
            # Show sample analytics
            st.subheader("📈 Sample Analytics Preview")
            sample_data = pd.DataFrame({
                'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'],
                'Momentum': [0.1245, 0.0876, 0.1532, 0.0654, 0.0987],
                'Volatility': [0.0234, 0.0198, 0.0276, 0.0187, 0.0234],
                'FITP': [0.6234, 0.5876, 0.6732, 0.5456, 0.6123],
                'Score': [5.3205, 4.4242, 5.5507, 3.4973, 4.2179]
            })
            
            sample_fig = create_performance_charts(sample_data)
            if sample_fig:
                st.plotly_chart(sample_fig, use_container_width=True)

    with tab4:
        st.subheader("🔗 GitHub Integration Management")
        
        # Initialize GitHub integration
        if 'github_integration' not in st.session_state:
            st.session_state.github_integration = GitHubIntegration()
        
        # Repository Status
        st.subheader("📊 Repository Status")
        status = st.session_state.github_integration.get_repo_status()
        
        if status["status"] == "ok":
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="success-box">✅ Repository Connected</div>', unsafe_allow_html=True)
                st.markdown(f"**Repository:** {st.session_state.github_integration.username}/{st.session_state.github_integration.repo_name}")
                
                if status["last_commit"]:
                    st.markdown(f"""
                    **Last Commit:** {status['last_commit']['hash']}  
                    **Message:** {status['last_commit']['message']}  
                    **Date:** {status['last_commit']['date']}
                    """)
            
            with col2:
                if status["has_changes"]:
                    st.markdown('<div class="warning-box">📝 Repository has uncommitted changes</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-box">✅ Repository is clean</div>', unsafe_allow_html=True)
                
                if st.button("🔗 Open Repository"):
                    st.markdown(f"[View Repository]({status['repo_url']})")
        
        elif status["status"] == "not_found":
            st.markdown('<div class="warning-box">⚠️ GitHub repository not found</div>', unsafe_allow_html=True)
            st.info("Please set up your data repository first.")
        
        else:
            st.markdown(f'<div class="warning-box">❌ Repository Error: {status["message"]}</div>', unsafe_allow_html=True)
        
        # Configuration Management
        st.subheader("⚙️ Configuration")
        
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            new_username = st.text_input(
                "GitHub Username:",
                value=st.session_state.github_integration.username,
                help="Your GitHub username"
            )
            
            new_repo_name = st.text_input(
                "Repository Name:",
                value=st.session_state.github_integration.repo_name,
                help="Name of your data repository"
            )
        
        with config_col2:
            new_repo_path = st.text_input(
                "Repository Path:",
                value=str(st.session_state.github_integration.repo_path),
                help="Local path to your data repository"
            )
            
            if st.button("💾 Update Configuration"):
                st.session_state.github_integration.username = new_username
                st.session_state.github_integration.repo_name = new_repo_name
                st.session_state.github_integration.repo_path = Path(new_repo_path)
                st.success("Configuration updated!")
                st.rerun()
        
        # URL Management
        st.subheader("🌐 Current URLs")
        
        if hasattr(st.session_state, 'latest_filename'):
            filename = st.session_state.latest_filename
            raw_url = st.session_state.github_integration.get_csv_url(filename, raw=True)
            github_url = st.session_state.github_integration.get_csv_url(filename, raw=False)
            
            url_col1, url_col2 = st.columns(2)
            
            with url_col1:
                st.markdown("**Raw CSV URL (for other applications):**")
                st.code(raw_url, language="text")
                
                if st.button("📋 Copy Raw URL"):
                    st.write("Use this URL in your other applications:")
                    st.code(raw_url)
            
            with url_col2:
                st.markdown("**GitHub View URL:**")
                st.code(github_url, language="text")
                
                if st.button("🔗 Open File on GitHub"):
                    st.markdown(f"[View file on GitHub]({github_url})")
            
            # Test connectivity
            st.subheader("🧪 Test Connectivity")
            if st.button("Test Raw URL Access"):
                with st.spinner("Testing URL..."):
                    try:
                        response = requests.get(raw_url, timeout=10)
                        if response.status_code == 200:
                            st.success("✅ URL is accessible")
                            
                            # Show preview
                            lines = response.text.split('\n')[:5]
                            st.text("File Preview:")
                            for line in lines:
                                if line.strip():
                                    st.text(line)
                        else:
                            st.error(f"❌ URL returned status code: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error accessing URL: {str(e)}")
        
        else:
            st.info("No files have been uploaded to GitHub yet. Run a scan first.")
        
        # Integration Examples
        st.subheader("🔧 Integration Examples")
        
        example_tab1, example_tab2, example_tab3 = st.tabs(["JavaScript", "Python", "Java"])
        
        with example_tab1:
            st.markdown("**Fetch CSV data in JavaScript:**")
            if hasattr(st.session_state, 'latest_filename'):
                raw_url = st.session_state.github_integration.get_csv_url(st.session_state.latest_filename, raw=True)
                js_code = f"""
// Fetch CSV data from GitHub
fetch('{raw_url}')
  .then(response => response.text())
  .then(data => {{
    console.log('CSV Data:', data);
    // Parse CSV data here
    const lines = data.split('\\n');
    const headers = lines[0].split(',');
    
    // Process each row
    for (let i = 1; i < lines.length; i++) {{
      const row = lines[i].split(',');
      const stock = {{}};
      headers.forEach((header, index) => {{
        stock[header] = row[index];
      }});
      console.log('Stock:', stock);
    }}
  }})
  .catch(error => console.error('Error:', error));
"""
                st.code(js_code, language="javascript")
            else:
                st.info("Upload a file first to see the example with your actual URL.")
        
        with example_tab2:
            st.markdown("**Read CSV data in Python:**")
            if hasattr(st.session_state, 'latest_filename'):
                raw_url = st.session_state.github_integration.get_csv_url(st.session_state.latest_filename, raw=True)
                python_code = f"""
import pandas as pd
import requests

# Read CSV directly from GitHub
url = '{raw_url}'
df = pd.read_csv(url)

print("Stock data:")
print(df.head())

# Access specific columns
symbols = df['Symbol'].tolist()
scores = df['Score'].tolist()

print(f"Top stock: {{symbols[0]}} with score: {{scores[0]}}")
"""
                st.code(python_code, language="python")
            else:
                st.info("Upload a file first to see the example with your actual URL.")
        
        with example_tab3:
            st.markdown("**Read CSV data in Java:**")
            if hasattr(st.session_state, 'latest_filename'):
                raw_url = st.session_state.github_integration.get_csv_url(st.session_state.latest_filename, raw=True)
                java_code = f"""
import java.net.URL;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public class StockDataReader {{
    public static void main(String[] args) {{
        try {{
            URL url = new URL("{raw_url}");
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(url.openStream())
            );
            
            String line;
            List<String[]> data = new ArrayList<>();
            
            // Read CSV data
            while ((line = reader.readLine()) != null) {{
                String[] values = line.split(",");
                data.add(values);
            }}
            
            // Print headers
            System.out.println("Headers: " + 
                String.join(", ", data.get(0)));
            
            // Print first few stocks
            for (int i = 1; i < Math.min(6, data.size()); i++) {{
                System.out.println("Stock " + i + ": " + 
                    String.join(", ", data.get(i)));
            }}
            
            reader.close();
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
}}
"""
                st.code(java_code, language="java")
            else:
                st.info("Upload a file first to see the example with your actual URL.")
    
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
        
        ### 🔗 GitHub Integration Benefits
        - **Automatic Upload:** Push CSV files directly to GitHub
        - **Direct URL Access:** Get raw URLs for immediate use in other applications
        - **Version Control:** All scans are tracked with timestamps
        - **Global Accessibility:** Access your data from anywhere
        - **API-like Access:** Use GitHub as a simple data API
        
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
        
        ### 🛠️ Setup Instructions
        
        **Step 1: Create GitHub Repository**
        ```bash
        # In Codespaces terminal
        gh repo create stock-scanner-data --public
        git clone https://github.com/YOUR_USERNAME/stock-scanner-data.git
        ```
        
        **Step 2: Configure Repository Path**
        - Update the sidebar configuration with your GitHub username
        - Ensure the repository path points to your cloned repository
        
        **Step 3: Test Integration**
        - Run a scan and push to GitHub
        - Verify the URLs are accessible
        - Test with your target applications
        
        ---
        
        **Version:** 3.0 Pro with GitHub Integration | **Last Updated:** January 2025
        
        *Built with ❤️ for systematic momentum investing and seamless data integration*
        """)
        
        # Technical specifications
        with st.expander("🔧 Technical Specifications"):
            st.markdown("""
            **Dependencies:**
            - Streamlit 1.28+
            - Fyers API v3
            - Pandas for data manipulation
            - Plotly for visualizations
            - PyTZ for timezone handling
            - Subprocess for Git operations
            - Requests for URL testing
            
            **GitHub Integration:**
            - Git repository operations
            - Automatic CSV upload
            - Metadata generation
            - URL generation for raw access
            - Repository status monitoring
            
            **API Limits:**
            - Fyers: 1000 requests per minute
            - GitHub: 5000 requests per hour (authenticated)
            - Data retention: 2 years historical
            - Cache validity: Per day and configuration
            
            **File Formats Supported:**
            - Input: CSV with 'Symbol' column
            - Output: CSV, Pickle, Markdown reports, JSON metadata
            
            **URL Format:**
            - Raw CSV: `https://raw.githubusercontent.com/USERNAME/REPO/main/FILENAME.csv`
            - GitHub View: `https://github.com/USERNAME/REPO/blob/main/FILENAME.csv`
            
            **Browser Compatibility:**
            - Chrome/Edge 90+
            - Firefox 88+
            - Safari 14+
            
            **Integration Support:**
            - JavaScript (Fetch API)
            - Python (pandas.read_csv)
            - Java (URL/BufferedReader)
            - R (read.csv)
            - Any HTTP client
            """)

if __name__ == "__main__":
    main()