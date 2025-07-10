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

# Modern CSS with contemporary design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main-container {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        font-weight: 400;
        margin-bottom: 0;
    }
    
    /* Status Cards */
    .status-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.1);
    }
    
    .status-success {
        border-left: 4px solid #10B981;
        background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%);
    }
    
    .status-warning {
        border-left: 4px solid #F59E0B;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
    }
    
    .status-error {
        border-left: 4px solid #EF4444;
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
    }
    
    .status-info {
        border-left: 4px solid #3B82F6;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    }
    
    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        font-weight: 500;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Primary Button Variant */
    .primary-btn button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    
    .primary-btn button:hover {
        background: linear-gradient(135deg, #0D9488 0%, #047857 100%) !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Warning Button Variant */
    .warning-btn button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3) !important;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
    }
    
    /* Tables */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }
    
    /* Animation for scan results */
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .scan-results {
        animation: slideInUp 0.6s ease-out;
    }
    
    /* GitHub Integration Section */
    .github-section {
        background: linear-gradient(135deg, #24292e 0%, #586069 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin: 2rem 0;
        box-shadow: 0 8px 24px rgba(36, 41, 46, 0.2);
    }
    
    .github-section h3 {
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .metric-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
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
GITHUB_CSV_FILENAME = "nifty_smallcap_momentum_scan.csv"  # Fixed filename
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
    "data_repo_path": get_repo_path(),
    "data_folder": "data"
}

# Nifty SmallCap 250 Stock List (from CSV)
NIFTY_SMALLCAP_250_SYMBOLS = [
    "360ONE", "AADHARHFC", "AARTIIND", "AAVAS", "ACE", "ABREL", "ABSLAMC", "AEGISLOG", 
    "AFFLE", "AKUMS", "APLLTD", "ALKYLAMINE", "ALOKINDS", "ARE&M", "AMBER", "ANANDRATHI", 
    "ANANTRAJ", "ANGELONE", "APARINDS", "APTUS", "ARMANFIN", "ASAHIINDIA", "ASHOKA", "ASTERDM", 
    "ASTRAL", "ATUL", "AVANTIFEED", "AWHCL", "BALAMINES", "BALRAMCHIN", "BANARISUG", "BASF", 
    "BATAINDIA", "BAYERCROP", "BBL", "BECTORFOOD", "BEML", "BERGEPAINT", "BHARATFORG", "BHARTIHEXA", 
    "BHEL", "BIKAJI", "BIRLACORPN", "BLUEDART", "BLUESTARCO", "BOFT", "BOMDYEING", "BSE", 
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
# Cache files
*.pkl
__pycache__/
.streamlit/

# Data files (optional - uncomment to ignore)
# data/*.csv
"""
        
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
        
        return True
    
    def push_csv_to_github(self, df, commit_message=None):
        """Push CSV file to GitHub - Always replaces the same file"""
        try:
            if not self.ensure_repo_exists():
                return False, "Repository not found or data folder creation failed."
            
            # Always use the same filename - this will replace existing file
            csv_path = self.data_folder / GITHUB_CSV_FILENAME
            df.to_csv(csv_path, index=False)
            
            # Create metadata file
            metadata = {
                "filename": GITHUB_CSV_FILENAME,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "scan_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_by": "Fyers Stock Scanner Pro",
                "file_size_kb": round(csv_path.stat().st_size / 1024, 2),
                "is_replacement": csv_path.exists()
            }
            
            metadata_path = self.data_folder / f"{GITHUB_CSV_FILENAME.replace('.csv', '_metadata.json')}"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Git operations
            if commit_message is None:
                commit_message = f"Update momentum scan results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Change to repo directory and commit
            original_cwd = Path.cwd()
            
            try:
                os.chdir(self.repo_path)
                
                # Check if git repo is initialized
                result = subprocess.run(["git", "status"], capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    return False, f"Not a git repository: {result.stderr}"
                
                # Configure git user if not set
                subprocess.run(["git", "config", "user.email", "streamlit-app@example.com"], 
                             capture_output=True, timeout=10)
                subprocess.run(["git", "config", "user.name", "Streamlit App"], 
                             capture_output=True, timeout=10)
                
                # Git operations - add the fixed filename
                subprocess.run(["git", "add", f"data/{GITHUB_CSV_FILENAME}"], 
                              check=True, capture_output=True, timeout=30)
                subprocess.run(["git", "add", f"data/{GITHUB_CSV_FILENAME.replace('.csv', '_metadata.json')}"], 
                              check=True, capture_output=True, timeout=30)
                
                # Check if there are changes to commit
                diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"], 
                                           capture_output=True, timeout=30)
                if diff_result.returncode == 0:
                    return True, f"File {GITHUB_CSV_FILENAME} is already up to date (no changes to commit)"
                
                # Commit changes
                subprocess.run(["git", "commit", "-m", commit_message], 
                              check=True, capture_output=True, timeout=30)
                
                # Push changes
                subprocess.run(["git", "push"], 
                              check=True, capture_output=True, timeout=60)
                
                return True, f"Successfully updated {GITHUB_CSV_FILENAME} on GitHub"
            
            except subprocess.TimeoutExpired:
                return False, "Git operation timed out. Please try again."
            
            except subprocess.CalledProcessError as e:
                error_msg = f"Git operation failed: {e}"
                if e.stderr:
                    stderr_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                    error_msg += f" - {stderr_msg}"
                
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
    
    def get_csv_url(self, raw=True):
        """Get direct URL to the fixed CSV file"""
        if raw:
            return f"https://raw.githubusercontent.com/{self.username}/{self.repo_name}/main/data/{GITHUB_CSV_FILENAME}"
        else:
            return f"https://github.com/{self.username}/{self.repo_name}/blob/main/data/{GITHUB_CSV_FILENAME}"
    
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
                
                # Check if our main file exists
                csv_exists = (self.data_folder / GITHUB_CSV_FILENAME).exists()
                
                return {
                    "status": "ok",
                    "has_changes": has_changes,
                    "last_commit": last_commit,
                    "repo_url": f"https://github.com/{self.username}/{self.repo_name}",
                    "csv_exists": csv_exists,
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
        """Load holidays from embedded data"""
        try:
            # Default holidays for 2025
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
            
            return set(pd.to_datetime(default_holidays).date)
        except Exception as e:
            st.warning(f"Using minimal holidays due to error: {str(e)}")
            return set()
    
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

def display_status_card(status_type, title, message, icon=""):
    """Display a modern status card"""
    card_class = f"status-card status-{status_type}"
    st.markdown(f"""
    <div class="{card_class}">
        <h4>{icon} {title}</h4>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Modern Hero Header
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">🚀 Fyers Stock Scanner Pro</h1>
        <p class="hero-subtitle">Advanced momentum-based stock screening with intelligent rebalancing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize scanner
    if 'scanner' not in st.session_state:
        st.session_state.scanner = EnhancedStockScanner()
    
    # Initialize GitHub integration
    if 'github_integration' not in st.session_state:
        st.session_state.github_integration = GitHubIntegration()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Control Panel")
        
        # Authentication section
        st.subheader("🔐 Fyers Authentication")
        auth_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={FYERS_CONFIG['client_id']}&redirect_uri={FYERS_CONFIG['redirect_uri']}&response_type=code&state=None"
        
        st.markdown(f"""
        **Step 1:** [🔗 Get Authorization Code]({auth_url})
        
        **Step 2:** Enter the code below:
        """)
        
        auth_code = st.text_input(
            "Authorization Code:",
            type="password",
            help="Paste the authorization code from Fyers",
            placeholder="Enter your auth code here..."
        )
        
        if st.button("🔑 Authenticate", type="primary", use_container_width=True):
            if auth_code:
                with st.spinner("🔄 Authenticating with Fyers..."):
                    if st.session_state.scanner.authenticate_fyers(auth_code):
                        st.success("✅ Authentication successful!")
                        st.session_state.authenticated = True
                    else:
                        st.error("❌ Authentication failed!")
                        st.session_state.authenticated = False
            else:
                st.warning("⚠️ Please enter authorization code")
        
        # Show authentication status
        if hasattr(st.session_state, 'authenticated'):
            if st.session_state.authenticated:
                display_status_card("success", "Authentication", "Successfully connected to Fyers API", "✅")
            else:
                display_status_card("error", "Authentication", "Please authenticate with Fyers", "❌")
        
        st.divider()
        
        # Scanner parameters
        st.subheader("📊 Scanner Configuration")
        
        strategy = st.selectbox(
            "🎯 Strategy:",
            ["volatility", "fitp", "momentum"],
            help="Choose the momentum scoring strategy"
        )
        
        num_stocks = st.slider(
            "📈 Number of stocks:",
            min_value=5,
            max_value=50,
            value=20,
            help="Number of top stocks to return"
        )
        
        lookback_period = st.slider(
            "📅 Lookback period (months):",
            min_value=3,
            max_value=24,
            value=12,
            help="How many months to look back for momentum calculation"
        )
        
        last_month_exclusion = st.slider(
            "🚫 Last month exclusion:",
            min_value=0,
            max_value=3,
            value=0,
            help="Exclude last N months to avoid recency bias"
        )
        
        # GitHub status
        st.divider()
        st.subheader("📂 GitHub Integration")
        
        status = st.session_state.github_integration.get_repo_status()
        if status["status"] == "ok":
            display_status_card("success", "Repository", f"Connected to {GITHUB_CONFIG['username']}/{GITHUB_CONFIG['repo_name']}", "✅")
            if status["csv_exists"]:
                csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                st.markdown(f"""
                **📁 Current file:** `{GITHUB_CSV_FILENAME}`  
                **🔗 Direct URL:** [Access CSV]({csv_url})
                """)
        else:
            display_status_card("warning", "Repository", status.get("message", "Repository not configured"), "⚠️")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Scanner", "📅 Calendar", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
            display_status_card("info", "Getting Started", "Please authenticate with Fyers using the sidebar to begin scanning stocks", "👈")
            
            # Show preview of what's available
            st.subheader("📋 Nifty SmallCap 250 Stock Universe")
            st.info(f"✨ This scanner uses the official Nifty SmallCap 250 list with {len(NIFTY_SMALLCAP_250_SYMBOLS)} stocks")
            
            # Display sample stocks in a nice grid
            col1, col2, col3, col4, col5 = st.columns(5)
            sample_stocks = NIFTY_SMALLCAP_250_SYMBOLS[:25]  # Show first 25
            
            for i, symbol in enumerate(sample_stocks):
                with [col1, col2, col3, col4, col5][i % 5]:
                    st.code(symbol)
            
            if len(NIFTY_SMALLCAP_250_SYMBOLS) > 25:
                st.caption(f"... and {len(NIFTY_SMALLCAP_250_SYMBOLS) - 25} more stocks")
                
        else:
            # Rebalance date selection
            st.subheader("📅 Select Rebalance Date")
            rebalance_dates = st.session_state.scanner.get_next_rebalance_dates(6)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_rebalance = st.selectbox(
                    "Choose your next rebalance date:",
                    options=range(len(rebalance_dates)),
                    format_func=lambda x: f"{rebalance_dates[x]['rebalance_date'].strftime('%Y-%m-%d')} ({rebalance_dates[x]['type']})",
                    help="Select when you plan to rebalance your portfolio"
                )
            
            with col2:
                if selected_rebalance is not None:
                    selected_date_info = rebalance_dates[selected_rebalance]
                    cutoff_date = selected_date_info['data_cutoff_date']
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📊 Data Cutoff Date</div>
                        <div class="metric-value">{cutoff_date.strftime('%Y-%m-%d')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Scan section
            st.subheader("🚀 Start Your Momentum Scan")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                **Strategy:** {strategy.title()}  
                **Stocks to analyze:** {len(NIFTY_SMALLCAP_250_SYMBOLS)} (Nifty SmallCap 250)  
                **Top results:** {num_stocks}  
                **Lookback period:** {lookback_period} months  
                """)
            
            with col2:
                scan_button = st.button(
                    "🔍 Start Scan",
                    type="primary",
                    use_container_width=True,
                    help="Begin momentum analysis of all stocks"
                )
            
            # Scan execution
            if scan_button and selected_rebalance is not None:
                selected_date_info = rebalance_dates[selected_rebalance]
                cutoff_date = selected_date_info['data_cutoff_date']
                
                try:
                    with st.spinner("🔄 Running momentum analysis..."):
                        results = st.session_state.scanner.scan_stocks(
                            symbols=NIFTY_SMALLCAP_250_SYMBOLS,
                            cutoff_date=cutoff_date,
                            strategy=strategy,
                            num_stocks=num_stocks,
                            lookback_period=lookback_period,
                            last_month_exclusion=last_month_exclusion
                        )
                    
                    if results:
                        # Store results in session state
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
                        
                        # Success message with animation
                        st.markdown("""
                        <div class="scan-results">
                        """, unsafe_allow_html=True)
                        
                        display_status_card("success", "Scan Complete!", f"Found {len(results)} high-momentum stocks", "🎉")
                        
                        # Results display
                        st.subheader("🏆 Top Momentum Stocks")
                        
                        # Format results for display
                        display_df = results_df.copy()
                        display_df["Momentum"] = display_df["Momentum"].apply(lambda x: f"{x:.4f}")
                        display_df["Volatility"] = display_df["Volatility"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                        display_df["FITP"] = display_df["FITP"].apply(lambda x: f"{x:.4f}" if x is not None else "N/A")
                        display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.4f}")
                        display_df.index = range(1, len(display_df) + 1)
                        
                        st.dataframe(display_df, use_container_width=True, height=400)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    else:
                        display_status_card("warning", "No Results", "No stocks found matching the criteria", "⚠️")
                        
                except Exception as e:
                    display_status_card("error", "Scan Error", f"Error during scan: {str(e)}", "❌")
            
            # GitHub Integration Section (only show if we have results)
            # GitHub Integration Section (only show if we have results)
            if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty:
                st.divider()
                
                # GitHub integration section
                st.markdown("""
                <div class="github-section">
                    <h3>🔗 Push to GitHub</h3>
                    <p>Save your scan results to GitHub for easy access from other applications</p>
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
                        with st.spinner("🔄 Uploading to GitHub..."):
                            try:
                                success, message = st.session_state.github_integration.push_csv_to_github(
                                    st.session_state.results_df,
                                    f"Momentum scan - {strategy} strategy - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                )
                                
                                if success:
                                    display_status_card("success", "Upload Success", message, "✅")
                                    
                                    # Show direct URL
                                    csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                                    st.markdown(f"""
                                    **🌐 Direct CSV URL:**
                                    ```
                                    {csv_url}
                                    ```
                                    """)
                                    
                                    # Test URL button
                                    if st.button("🧪 Test URL", key="test_csv_url"):
                                        try:
                                            response = requests.get(csv_url, timeout=10)
                                            if response.status_code == 200:
                                                display_status_card("success", "URL Test", "CSV URL is accessible and working", "✅")
                                                st.text("Preview (first 3 lines):")
                                                lines = response.text.split('\n')[:3]
                                                for line in lines:
                                                    st.code(line)
                                            else:
                                                display_status_card("error", "URL Test", f"URL returned status code: {response.status_code}", "❌")
                                        except Exception as e:
                                            display_status_card("error", "URL Test", f"Error testing URL: {str(e)}", "❌")
                                    
                                    st.balloons()
                                else:
                                    display_status_card("error", "Upload Failed", message, "❌")
                                    
                            except Exception as e:
                                display_status_card("error", "Upload Error", f"Unexpected error: {str(e)}", "❌")
                
                # Show current file status if it exists
                status = st.session_state.github_integration.get_repo_status()
                if status["status"] == "ok" and status.get("csv_exists"):
                    st.subheader("📄 Current File Status")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_url = st.session_state.github_integration.get_csv_url(raw=True)
                        github_url = st.session_state.github_integration.get_csv_url(raw=False)
                        
                        st.markdown(f"""
                        **📁 File:** `{GITHUB_CSV_FILENAME}`  
                        **🔗 Raw URL:** [Direct CSV Access]({csv_url})  
                        **👁️ GitHub View:** [View on GitHub]({github_url})  
                        """)
                    
                    with col2:
                        if status.get("last_commit"):
                            commit = status["last_commit"]
                            st.markdown(f"""
                            **📝 Last Update:** {commit['hash']}  
                            **💬 Message:** {commit['message'][:50]}...  
                            **📅 Date:** {commit['date'][:16]}  
                            """)
                
                # URL usage examples
                with st.expander("💡 How to use the CSV URL in other applications"):
                    csv_url_example = st.session_state.github_integration.get_csv_url(raw=True) if hasattr(st.session_state, "github_integration") else "YOUR_CSV_URL"
                    
                    st.markdown(f"""
                    **Python:**
                    ```python
                    import pandas as pd
                    df = pd.read_csv('{csv_url_example}')
                    print(df.head())
                    ```
                    
                    **JavaScript:**
                    ```javascript
                    fetch('{csv_url_example}')
                        .then(response => response.text())
                        .then(data => console.log(data));
                    ```
                    
                    **R:**
                    ```r
                    library(readr)
                    df <- read_csv('{csv_url_example}')
                    head(df)
                    ```
                    
                    **Excel/Google Sheets:**
                    - Use "Data > From Web" and paste the raw URL
                    - The data will refresh automatically when you update the file
                    
                    **curl:**
                    ```bash
                    curl -o momentum_stocks.csv '{csv_url_example}'
                    ```
                    
                    **Power BI:**
                    ```
                    Get Data > Web > Enter the raw CSV URL
                    ```
                    
                    **Tableau:**
                    ```
                    Connect > To a Server > Web Data Connector > Enter URL
                    ```
                    """)
            
            elif hasattr(st.session_state, 'authenticated') and st.session_state.authenticated:
                display_status_card("info", "Ready to Scan", "Complete a momentum scan to enable GitHub integration", "🔍")
    
    with tab2:
        st.subheader("📅 Rebalance Calendar & Trading Days")
        
        # Create and display calendar
        calendar_fig, rebalance_dates = create_rebalance_calendar()
        st.plotly_chart(calendar_fig, use_container_width=True)
        
        # Detailed rebalance schedule
        st.subheader("📋 Upcoming Schedule")
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
            holidays_df = holidays_df[holidays_df['Days from Today'] >= 0]  # Only future holidays
            holidays_df.index = range(1, len(holidays_df) + 1)
            st.dataframe(holidays_df, use_container_width=True)
        else:
            display_status_card("info", "Holiday Data", "No holiday data loaded", "📅")
    
    with tab3:
        st.subheader("📊 Analytics Dashboard")
        
        if hasattr(st.session_state, 'results_df') and not st.session_state.results_df.empty:
            # Scan summary metrics
            st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
            
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
                    <div class="metric-label">📈 Positive Momentum</div>
                    <div class="metric-value">{positive_momentum}/{len(st.session_state.results_df)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Performance charts
            perf_fig = create_performance_charts(st.session_state.results_df)
            if perf_fig:
                st.plotly_chart(perf_fig, use_container_width=True)
            
            # Additional analysis
            st.subheader("🔍 Detailed Analysis")
            
            # Top performers breakdown
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
            display_status_card("info", "No Data", "Run a stock scan first to see detailed analytics", "📊")
    
    with tab4:
        st.subheader("ℹ️ About Fyers Stock Scanner Pro")
        
        st.markdown("""
        ### 🎯 Purpose
        This advanced stock scanning application identifies momentum-based investment opportunities 
        using sophisticated technical analysis, perfectly synchronized with your rebalancing schedule.
        
        ### 🔬 Methodology
        
        **📈 Momentum Calculation:**
        - Analyzes price momentum over configurable lookback periods (default: 12 months)
        - Uses data cutoff dates aligned with rebalancing schedules
        - Excludes recent periods to avoid recency bias
        - Calculated as: `(End Price - Start Price) / Start Price`
        
        **🎯 Scoring Strategies:**
        1. **Volatility-Adjusted:** `Score = Momentum / Volatility`
           - Rewards consistent momentum over erratic performance
        2. **FITP (Fraction in Trend Period):** `Score = Momentum × FITP`
           - Considers consistency of trend direction
        3. **Pure Momentum:** `Score = Momentum`
           - Simple momentum ranking
        
        **📊 FITP Explained:**
        - For positive momentum: Percentage of days with positive returns
        - For negative momentum: Percentage of days with negative returns
        - Measures trend consistency and reliability
        
        ### 📅 Smart Rebalancing
        - **Trading Day Intelligence:** Automatically excludes weekends and holidays
        - **Proper Cutoff Dates:** Ensures data availability before rebalance execution
        - **Flexible Scheduling:** Supports month-start and mid-month rebalancing
        - **Holiday Awareness:** Built-in NSE holiday calendar for 2025
        
        ### 🏗️ Key Features
        
        **🔄 Performance Optimizations:**
        - Smart caching system prevents redundant data downloads
        - Session state management for persistent results
        - Efficient API usage with rate limiting
        
        **🎨 Modern UI/UX:**
        - Contemporary design with smooth animations
        - Responsive layout for all screen sizes
        - Intuitive status cards and progress indicators
        - Professional color scheme and typography
        
        **🔗 GitHub Integration:**
        - **Single File Strategy:** Always updates the same file (`{GITHUB_CSV_FILENAME}`)
        - **Direct URLs:** Instant access for other applications
        - **Cross-Platform:** Works with Python, JavaScript, Java, R, etc.
        - **Version Control:** Automatic commit tracking
        - **Global Access:** Your data available anywhere
        
        ### 📊 Data Sources
        - **Market Data:** Fyers API (NSE real-time and historical)
        - **Stock Universe:** Official Nifty SmallCap 250 list ({len(NIFTY_SMALLCAP_250_SYMBOLS)} stocks)
        - **Holidays:** NSE official holiday calendar
        
        ### 🚀 Quick Start Guide
        
        1. **🔐 Authentication**
           - Click the Fyers auth link in the sidebar
           - Copy the authorization code
           - Paste it back in the app
        
        2. **📅 Select Date**
           - Choose your next rebalance date
           - The app calculates the proper data cutoff automatically
        
        3. **⚙️ Configure**
           - Select your preferred momentum strategy
           - Adjust parameters as needed
        
        4. **🔍 Scan**
           - Click "Start Scan" to analyze all 250 stocks
           - Wait for the momentum calculations to complete
        
        5. **📤 Export**
           - Push results to GitHub with one click
           - Get direct URL for use in other applications
        
        ### 💡 Pro Tips
        
        **📊 Strategy Selection:**
        - Use **Volatility-Adjusted** for stable, consistent momentum
        - Use **FITP** when trend consistency matters most
        - Use **Pure Momentum** for simple ranking by returns
        
        **⏰ Timing:**
        - Run scans 1-2 days before your rebalance date
        - Monitor the calendar tab for upcoming dates
        - Consider market conditions when interpreting results
        
        **🔗 GitHub Usage:**
        - The same file is always updated (no duplicates)
        - Use the raw URL in your other applications
        - File format is standard CSV with clear column headers
        
        ### 🔒 Security & Privacy
        - Authentication tokens are temporary and session-based
        - No sensitive data is permanently stored
        - All processing happens in your browser session
        - GitHub integration uses standard Git protocols
        
        ### 📈 Best Practices
        - **Diversification:** Don't rely on momentum alone
        - **Risk Management:** Consider position sizing
        - **Market Context:** Factor in overall market conditions
        - **Regular Updates:** Maintain consistent rebalancing schedule
        - **Backtesting:** Validate strategies before implementation
        
        ### 🆕 Latest Updates (v4.0)
        
        **🎨 UI/UX Improvements:**
        - Complete modern redesign with contemporary aesthetics
        - Smooth animations and micro-interactions
        - Better mobile responsiveness
        - Professional status cards and notifications
        
        **🔗 GitHub Enhancements:**
        - Simplified single-file strategy
        - Removed redundant "Update Latest" button
        - Better error handling and status reporting
        - Direct URL generation and testing
        
        **📊 Data Accuracy:**
        - Updated to official Nifty SmallCap 250 list
        - Improved caching mechanism
        - Better error handling for missing data
        
        **⚡ Performance:**
        - Faster scanning with optimized algorithms
        - Better memory management
        - Reduced API calls through smart caching
        
        ---
        
        **Version:** 4.0 Professional | **Updated:** January 2025  
        **Data Source:** NSE via Fyers API | **Stock Universe:** Nifty SmallCap 250
        
        *Built with ❤️ for systematic momentum investing*
        """)

if __name__ == "__main__":
    main()