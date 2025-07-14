#!/usr/bin/env python3
"""
Fyers Stock Scanner Pro - Simple Web Version
A lightweight stock scanner that works without external dependencies
"""

import http.server
import socketserver
import json
import os
import csv
import random
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import webbrowser

class StockScannerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_main_page()
        elif parsed_path.path == '/scan':
            self.handle_scan(parsed_path.query)
        elif parsed_path.path == '/api/files':
            self.serve_file_list()
        elif parsed_path.path.startswith('/data/'):
            self.serve_data_file(parsed_path.path)
        else:
            super().do_GET()
    
    def serve_main_page(self):
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fyers Stock Scanner Pro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
            margin-bottom: 30px;
        }
        .scanner-panel, .sidebar {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .results-table th,
        .results-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e1e5e9;
        }
        .results-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .file-item {
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .file-item:hover {
            background: #e9ecef;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Fyers Stock Scanner Pro</h1>
            <p>Advanced Stock Analysis & Scanning Tool</p>
            <div class="status-badge status-success">✅ System Online</div>
        </div>
        
        <div class="main-content">
            <div class="scanner-panel">
                <h2>🎯 Stock Scanner</h2>
                <form id="scanForm">
                    <div class="form-group">
                        <label for="scanType">Scan Type</label>
                        <select id="scanType" class="form-control">
                            <option value="volatility">Volatility</option>
                            <option value="momentum">Momentum</option>
                            <option value="volume">Volume</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="lookbackDays">Lookback Period (days)</label>
                        <input type="range" id="lookbackDays" class="form-control" min="5" max="100" value="30">
                        <span id="lookbackValue">30</span> days
                    </div>
                    
                    <div class="form-group">
                        <label for="minScore">Minimum Score</label>
                        <input type="range" id="minScore" class="form-control" min="-50" max="50" value="0">
                        <span id="minScoreValue">0</span>
                    </div>
                    
                    <div class="form-group">
                        <label for="maxResults">Max Results</label>
                        <input type="range" id="maxResults" class="form-control" min="5" max="100" value="20">
                        <span id="maxResultsValue">20</span>
                    </div>
                    
                    <button type="submit" class="btn">🚀 Run Stock Scan</button>
                </form>
                
                <div id="results"></div>
            </div>
            
            <div class="sidebar">
                <h3>📁 Recent Scans</h3>
                <div id="fileList">
                    <div class="loading">Loading files...</div>
                </div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" id="totalScans">0</div>
                <div class="metric-label">Total Scans</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">4</div>
                <div class="metric-label">Scan Types</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">Online</div>
                <div class="metric-label">Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">1.0.0</div>
                <div class="metric-label">Version</div>
            </div>
        </div>
    </div>

    <script>
        // Update range input displays
        document.getElementById('lookbackDays').addEventListener('input', function() {
            document.getElementById('lookbackValue').textContent = this.value;
        });
        
        document.getElementById('minScore').addEventListener('input', function() {
            document.getElementById('minScoreValue').textContent = this.value;
        });
        
        document.getElementById('maxResults').addEventListener('input', function() {
            document.getElementById('maxResultsValue').textContent = this.value;
        });
        
        // Handle form submission
        document.getElementById('scanForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const params = new URLSearchParams();
            params.append('scan_type', document.getElementById('scanType').value);
            params.append('lookback_days', document.getElementById('lookbackDays').value);
            params.append('min_score', document.getElementById('minScore').value);
            params.append('max_results', document.getElementById('maxResults').value);
            
            document.getElementById('results').innerHTML = '<div class="loading">🔍 Scanning stocks...</div>';
            
            fetch('/scan?' + params.toString())
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                    loadFileList();
                })
                .catch(error => {
                    document.getElementById('results').innerHTML = '<div style="color: red;">Error: ' + error.message + '</div>';
                });
        });
        
        function displayResults(data) {
            if (data.error) {
                document.getElementById('results').innerHTML = '<div style="color: red;">Error: ' + data.error + '</div>';
                return;
            }
            
            let html = '<h3>📊 Scan Results</h3>';
            html += '<p>✅ Scan completed! Found ' + data.results.length + ' stocks</p>';
            
            if (data.results.length > 0) {
                html += '<table class="results-table">';
                html += '<thead><tr><th>Symbol</th><th>Momentum</th><th>Volatility</th><th>FITP</th><th>Score</th></tr></thead>';
                html += '<tbody>';
                
                data.results.forEach(stock => {
                    html += '<tr>';
                    html += '<td>' + stock.Symbol + '</td>';
                    html += '<td>' + (stock.Momentum * 100).toFixed(2) + '%</td>';
                    html += '<td>' + (stock.Volatility * 100).toFixed(2) + '%</td>';
                    html += '<td>' + (stock.FITP * 100).toFixed(1) + '%</td>';
                    html += '<td>' + stock.Score.toFixed(2) + '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
            }
            
            document.getElementById('results').innerHTML = html;
        }
        
        function loadFileList() {
            fetch('/api/files')
                .then(response => response.json())
                .then(files => {
                    let html = '';
                    if (files.length === 0) {
                        html = '<div class="loading">No scan files found</div>';
                    } else {
                        files.forEach(file => {
                            html += '<div class="file-item" onclick="loadFile(\'' + file.name + '\')">';
                            html += '📄 ' + file.display_name;
                            html += '</div>';
                        });
                    }
                    document.getElementById('fileList').innerHTML = html;
                    document.getElementById('totalScans').textContent = files.length;
                });
        }
        
        function loadFile(filename) {
            fetch('/data/' + filename)
                .then(response => response.text())
                .then(data => {
                    // Parse CSV and display
                    const lines = data.trim().split('\\n');
                    const headers = lines[0].split(',');
                    const rows = lines.slice(1).map(line => line.split(','));
                    
                    let html = '<h3>📊 ' + filename + '</h3>';
                    html += '<table class="results-table">';
                    html += '<thead><tr>';
                    headers.forEach(header => {
                        html += '<th>' + header + '</th>';
                    });
                    html += '</tr></thead><tbody>';
                    
                    rows.forEach(row => {
                        html += '<tr>';
                        row.forEach(cell => {
                            html += '<td>' + cell + '</td>';
                        });
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('results').innerHTML = html;
                });
        }
        
        // Load file list on page load
        loadFileList();
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def handle_scan(self, query_string):
        params = parse_qs(query_string)
        scan_type = params.get('scan_type', ['volatility'])[0]
        lookback_days = int(params.get('lookback_days', [30])[0])
        min_score = float(params.get('min_score', [0])[0])
        max_results = int(params.get('max_results', [20])[0])
        
        # Generate sample data
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'ASIANPAINT']
        
        results = []
        for symbol in symbols[:max_results + 5]:
            momentum = random.uniform(-0.1, 0.2)
            volatility = random.uniform(0.01, 0.04)
            fitp = random.uniform(0.4, 0.8)
            
            if scan_type == 'volatility':
                score = volatility * 500 + random.uniform(-5, 5)
            elif scan_type == 'momentum':
                score = momentum * 100 + random.uniform(-3, 3)
            else:
                score = random.uniform(-20, 30)
            
            if score >= min_score:
                results.append({
                    'Symbol': symbol,
                    'Momentum': round(momentum, 4),
                    'Volatility': round(volatility, 6),
                    'FITP': round(fitp, 4),
                    'Score': round(score, 2)
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['Score'], reverse=True)
        results = results[:max_results]
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_scan_{timestamp}_{scan_type}.csv"
        
        os.makedirs('data', exist_ok=True)
        filepath = f"data/{filename}"
        
        with open(filepath, 'w', newline='') as csvfile:
            if results:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        response_data = {
            'success': True,
            'results': results,
            'filename': filename,
            'scan_type': scan_type,
            'count': len(results)
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def serve_file_list(self):
        files = []
        if os.path.exists('data'):
            for filename in os.listdir('data'):
                if filename.endswith('.csv') and 'stock_scan' in filename:
                    # Extract timestamp for display
                    try:
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            date_part = parts[2]
                            time_part = parts[3].replace('.csv', '')
                            dt = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                            display_name = dt.strftime("%m/%d %H:%M")
                        else:
                            display_name = filename
                    except:
                        display_name = filename
                    
                    files.append({
                        'name': filename,
                        'display_name': display_name
                    })
        
        files.sort(key=lambda x: x['name'], reverse=True)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(files).encode())
    
    def serve_data_file(self, path):
        filename = path.replace('/data/', '')
        filepath = f"data/{filename}"
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(content.encode())
        else:
            self.send_response(404)
            self.end_headers()

def main():
    PORT = int(os.environ.get('PORT', 8501))
    
    print(f"🚀 Starting Fyers Stock Scanner Pro on port {PORT}")
    print(f"📈 Access the application at: http://localhost:{PORT}")
    
    with socketserver.TCPServer(("", PORT), StockScannerHandler) as httpd:
        print(f"✅ Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()