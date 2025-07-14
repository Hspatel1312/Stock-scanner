import streamlit as st
import pandas as pd
import os
import subprocess
import json
from datetime import datetime, timedelta
import pytz
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Auto-load GitHub token
def load_github_token():
    """Load GitHub token from ~/.jshrc file or environment"""
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    
    # Try to load from ~/.jshrc file
    try:
        jshrc_path = os.path.expanduser('~/.jshrc')
        if os.path.exists(jshrc_path):
            with open(jshrc_path, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if 'GITHUB_TOKEN=' in line:
                        token = line.split('GITHUB_TOKEN=')[1].strip()
                        os.environ['GITHUB_TOKEN'] = token
                        return token
    except Exception as e:
        st.error(f"Error loading token from ~/.jshrc: {e}")
    
    return None

# Load token at startup
github_token = load_github_token()

# Page config
st.set_page_config(
    page_title="Fyers Stock Scanner Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .scan-button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">📈 Fyers Stock Scanner Pro</h1>', unsafe_allow_html=True)

# Check GitHub token status
if github_token:
    st.success("✅ GitHub token loaded successfully!")
else:
    st.error("❌ GitHub token not found!")
    st.info("💡 **Setup Instructions:**")
    st.code("""
# Run these commands in terminal:
export GITHUB_TOKEN=your_token_here
echo export GITHUB_TOKEN=your_token_here > ~/.jshrc
source ~/.jshrc
    """)
    st.stop()

# Sidebar
with st.sidebar:
    st.header("🔧 Scanner Settings")
    
    # Token status
    st.markdown("### 🔑 Authentication")
    if github_token:
        st.markdown('<p class="status-success">✅ Token Active</p>', unsafe_allow_html=True)
        # Show masked token
        masked_token = github_token[:8] + "..." + github_token[-4:] if len(github_token) > 12 else "***"
        st.text(f"Token: {masked_token}")
    else:
        st.markdown('<p class="status-error">❌ No Token</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scan parameters
    st.markdown("### 📊 Scan Parameters")
    
    scan_type = st.selectbox(
        "Scan Type",
        ["Volatility", "Momentum", "Volume", "Custom"],
        index=0
    )
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=5,
        max_value=100,
        value=30,
        step=5
    )
    
    min_score = st.slider(
        "Minimum Score",
        min_value=-50.0,
        max_value=50.0,
        value=0.0,
        step=1.0
    )
    
    max_results = st.slider(
        "Max Results",
        min_value=5,
        max_value=100,
        value=20,
        step=5
    )

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Stock Scanner")
    
    # Scan button
    if st.button("🚀 Run Stock Scan", type="primary", use_container_width=True):
        with st.spinner("🔍 Scanning stocks..."):
            # Simulate stock scanning (replace with actual Fyers API calls)
            import time
            time.sleep(2)
            
            # Generate sample data
            sample_data = {
                'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'],
                'Momentum': [0.15, -0.08, 0.12, 0.18, 0.22],
                'Volatility': [0.025, 0.018, 0.032, 0.015, 0.020],
                'FITP': [0.65, 0.58, 0.72, 0.68, 0.75],
                'Score': [12.5, -5.2, 8.9, 15.3, 18.7]
            }
            
            df = pd.DataFrame(sample_data)
            
            # Filter by minimum score
            df_filtered = df[df['Score'] >= min_score].head(max_results)
            
            # Save to data folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_scan_{timestamp}_{scan_type.lower()}.csv"
            filepath = f"data/{filename}"
            
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Save CSV
            df_filtered.to_csv(filepath, index=False)
            
            # Save metadata
            metadata = {
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "rows": len(df_filtered),
                "columns": list(df_filtered.columns),
                "scan_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_by": "Fyers Stock Scanner Pro",
                "file_size_kb": round(os.path.getsize(filepath) / 1024, 2),
                "replaced_existing": False
            }
            
            with open(f"{filepath.replace('.csv', '_metadata.json')}", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            st.success(f"✅ Scan completed! Saved {len(df_filtered)} results to `{filename}`")
            
            # Display results
            st.subheader("📊 Scan Results")
            st.dataframe(df_filtered, use_container_width=True)
            
            # Create visualization
            if len(df_filtered) > 0:
                fig = px.scatter(
                    df_filtered,
                    x='Volatility',
                    y='Momentum',
                    size='Score',
                    color='Score',
                    hover_name='Symbol',
                    title=f"{scan_type} Scan Results",
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("📁 Recent Scans")
    
    # List recent scan files
    data_dir = "data"
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and 'stock_scan' in f]
        csv_files.sort(reverse=True)  # Most recent first
        
        if csv_files:
            st.write(f"Found {len(csv_files)} recent scans:")
            
            for i, file in enumerate(csv_files[:10]):  # Show last 10
                # Extract timestamp from filename
                try:
                    parts = file.split('_')
                    if len(parts) >= 3:
                        date_part = parts[2]
                        time_part = parts[3].replace('.csv', '')
                        dt = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                        time_str = dt.strftime("%m/%d %H:%M")
                    else:
                        time_str = "Unknown"
                except:
                    time_str = "Unknown"
                
                if st.button(f"📄 {time_str}", key=f"file_{i}"):
                    # Load and display the selected file
                    try:
                        df = pd.read_csv(f"{data_dir}/{file}")
                        st.subheader(f"📊 {file}")
                        st.dataframe(df, use_container_width=True)
                        
                        # Show metadata if available
                        metadata_file = f"{data_dir}/{file.replace('.csv', '_metadata.json')}"
                        if os.path.exists(metadata_file):
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            st.json(metadata)
                    except Exception as e:
                        st.error(f"Error loading file: {e}")
        else:
            st.info("No scan files found. Run a scan to get started!")
    else:
        st.info("Data directory not found. Run a scan to create it!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🚀 <strong>Fyers Stock Scanner Pro</strong> | Built with Streamlit</p>
    <p>💡 <em>Real-time stock analysis and scanning tool</em></p>
</div>
""", unsafe_allow_html=True)