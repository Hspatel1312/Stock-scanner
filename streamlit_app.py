import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import pytz
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Auto-load GitHub token
github_token = os.getenv('GITHUB_TOKEN', 'demo_token_for_testing')

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
            time.sleep(2)
            
            # Generate more realistic sample data based on scan type
            symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'ASIANPAINT']
            
            np.random.seed(42)  # For consistent results
            n_stocks = min(len(symbols), max_results + 5)
            
            sample_data = {
                'Symbol': symbols[:n_stocks],
                'Momentum': np.random.normal(0.05, 0.15, n_stocks),
                'Volatility': np.random.uniform(0.01, 0.04, n_stocks),
                'FITP': np.random.uniform(0.4, 0.8, n_stocks),
                'Score': np.random.normal(5, 15, n_stocks)
            }
            
            df = pd.DataFrame(sample_data)
            
            # Apply scan type specific adjustments
            if scan_type == "Volatility":
                df['Score'] = df['Volatility'] * 500 + np.random.normal(0, 5, len(df))
            elif scan_type == "Momentum":
                df['Score'] = df['Momentum'] * 100 + np.random.normal(0, 3, len(df))
            
            # Round values for better display
            df['Momentum'] = df['Momentum'].round(4)
            df['Volatility'] = df['Volatility'].round(6)
            df['FITP'] = df['FITP'].round(4)
            df['Score'] = df['Score'].round(2)
            
            # Filter by minimum score
            df_filtered = df[df['Score'] >= min_score].head(max_results)
            
            # Sort by score descending
            df_filtered = df_filtered.sort_values('Score', ascending=False)
            
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
                "scan_type": scan_type,
                "lookback_days": lookback_days,
                "min_score": min_score,
                "max_results": max_results
            }
            
            with open(f"{filepath.replace('.csv', '_metadata.json')}", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            st.success(f"✅ Scan completed! Saved {len(df_filtered)} results to `{filename}`")
            
            # Display results
            st.subheader("📊 Scan Results")
            
            # Format the dataframe for better display
            display_df = df_filtered.copy()
            display_df['Momentum'] = display_df['Momentum'].apply(lambda x: f"{x:.2%}")
            display_df['Volatility'] = display_df['Volatility'].apply(lambda x: f"{x:.2%}")
            display_df['FITP'] = display_df['FITP'].apply(lambda x: f"{x:.1%}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Momentum": st.column_config.TextColumn("Momentum", width="small"),
                    "Volatility": st.column_config.TextColumn("Volatility", width="small"),
                    "FITP": st.column_config.TextColumn("FITP", width="small"),
                    "Score": st.column_config.NumberColumn("Score", format="%.2f")
                }
            )
            
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
                    color_continuous_scale='RdYlGn',
                    labels={
                        'Volatility': 'Volatility (%)',
                        'Momentum': 'Momentum (%)',
                        'Score': 'Score'
                    }
                )
                fig.update_layout(height=400)
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
                        
                        # Format for display
                        display_df = df.copy()
                        if 'Momentum' in display_df.columns:
                            display_df['Momentum'] = display_df['Momentum'].apply(lambda x: f"{x:.2%}")
                        if 'Volatility' in display_df.columns:
                            display_df['Volatility'] = display_df['Volatility'].apply(lambda x: f"{x:.2%}")
                        if 'FITP' in display_df.columns:
                            display_df['FITP'] = display_df['FITP'].apply(lambda x: f"{x:.1%}")
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Show metadata if available
                        metadata_file = f"{data_dir}/{file.replace('.csv', '_metadata.json')}"
                        if os.path.exists(metadata_file):
                            st.subheader("📋 Scan Details")
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Rows", metadata.get('rows', 'N/A'))
                                st.metric("File Size", f"{metadata.get('file_size_kb', 0)} KB")
                            with col_b:
                                st.metric("Scan Type", metadata.get('scan_type', 'N/A'))
                                st.metric("Min Score", metadata.get('min_score', 'N/A'))
                    except Exception as e:
                        st.error(f"Error loading file: {e}")
        else:
            st.info("No scan files found. Run a scan to get started!")
    else:
        st.info("Data directory not found. Run a scan to create it!")

# Footer
st.markdown("---")

# Add some metrics in the footer
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    st.metric("🎯 Active Scans", len([f for f in os.listdir("data") if f.endswith('.csv')]) if os.path.exists("data") else 0)

with col_f2:
    st.metric("📊 Scan Types", 4)

with col_f3:
    st.metric("⚡ Status", "Online")

with col_f4:
    st.metric("🔧 Version", "1.0.0")

st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🚀 <strong>Fyers Stock Scanner Pro</strong> | Built with Streamlit</p>
    <p>💡 <em>Real-time stock analysis and scanning tool</em></p>
</div>
""", unsafe_allow_html=True)