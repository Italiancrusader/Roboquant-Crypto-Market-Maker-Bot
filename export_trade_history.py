import ccxt
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

# Initialize Bybit exchange via CCXT
exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'sandbox': False,
    'enableRateLimit': True,
})

class BybitTradeHistoryExporter:
    def __init__(self):
        self.trades_data = []
        self.symbols = []  # Will auto-discover symbols with trades
    
    def fetch_trade_history(self, days=4):
        """Fetch trade history for the last N days"""
        print(f"Fetching trade history for the last {days} days...")
        
        # Calculate timestamp for N days ago
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        since = int(start_time.timestamp() * 1000)  # Convert to milliseconds
        
        try:
            # Load markets to get all available symbols
            markets = exchange.load_markets()
            
            # Get all symbols that have trading pairs
            all_symbols = list(markets.keys())
            
            # Filter for symbols you might be trading (adjust as needed)
            target_symbols = [s for s in all_symbols if 'USDT' in s and ('ETH' in s or 'BTC' in s or 'SOL' in s)]
            
            print(f"Checking {len(target_symbols)} symbols for trades...")
            
            for symbol in target_symbols:
                try:
                    print(f"Fetching trades for {symbol}...")
                    
                    # Fetch trades for this symbol
                    trades = exchange.fetch_my_trades(symbol, since=since, limit=1000)
                    
                    if trades:
                        print(f"Found {len(trades)} trades for {symbol}")
                        self.symbols.append(symbol)
                        
                        for trade in trades:
                            trade_data = {
                                'symbol': symbol,
                                'id': trade['id'],
                                'timestamp': trade['timestamp'],
                                'datetime': trade['datetime'],
                                'side': trade['side'],
                                'amount': trade['amount'],
                                'price': trade['price'],
                                'cost': trade['cost'],
                                'fee_cost': trade.get('fee', {}).get('cost', 0),
                                'fee_currency': trade.get('fee', {}).get('currency', ''),
                                'order_id': trade.get('order', ''),
                                'type': trade.get('type', 'limit'),
                                'taker_or_maker': trade.get('takerOrMaker', 'unknown')
                            }
                            self.trades_data.append(trade_data)
                    
                except Exception as e:
                    # Skip symbols that don't have trades or cause errors
                    continue
            
            print(f"\n✅ Total trades found: {len(self.trades_data)}")
            print(f"Symbols with trades: {', '.join(self.symbols)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching trade history: {e}")
            return False
    
    def generate_html_report(self):
        """Generate HTML report of trade history"""
        if not self.trades_data:
            print("No trade data to generate report")
            return None
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(self.trades_data)
        
        # Sort by timestamp (newest first)
        df = df.sort_values('timestamp', ascending=False)
        
        # Calculate additional metrics
        total_trades = len(df)
        total_volume = df['cost'].sum()
        total_fees = df['fee_cost'].sum()
        buy_trades = len(df[df['side'] == 'buy'])
        sell_trades = len(df[df['side'] == 'sell'])
        
        # Group by symbol for summary
        symbol_summary = df.groupby('symbol').agg({
            'cost': 'sum',
            'fee_cost': 'sum',
            'amount': 'sum',
            'id': 'count'
        }).round(6)
        symbol_summary.columns = ['Total Volume (USDT)', 'Total Fees', 'Total Amount', 'Trade Count']
        
        # Group by day for daily breakdown
        df['date'] = pd.to_datetime(df['datetime']).dt.date
        daily_summary = df.groupby('date').agg({
            'cost': 'sum',
            'fee_cost': 'sum',
            'id': 'count'
        }).round(6)
        daily_summary.columns = ['Daily Volume (USDT)', 'Daily Fees', 'Trade Count']
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bybit Trade History Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #2a5298;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2a5298;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2a5298;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e6ff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e6ff;
        }}
        th {{
            background: #f8f9ff;
            font-weight: 600;
            color: #2a5298;
        }}
        tr:hover {{
            background: #f8f9ff;
        }}
        .buy {{
            color: #00c851;
            font-weight: bold;
        }}
        .sell {{
            color: #ff4444;
            font-weight: bold;
        }}
        .positive {{
            color: #00c851;
        }}
        .negative {{
            color: #ff4444;
        }}
        .scrollable {{
            max-height: 500px;
            overflow-y: auto;
            border-radius: 8px;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e6ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Bybit Trade History Report</h1>
            <p>Last 4 Days Trading Activity • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_trades:,}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${total_volume:,.2f}</div>
                    <div class="metric-label">Total Volume</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${total_fees:.4f}</div>
                    <div class="metric-label">Total Fees</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{buy_trades}/{sell_trades}</div>
                    <div class="metric-label">Buy/Sell Trades</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Summary by Symbol</h2>
                <div class="scrollable">
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Trade Count</th>
                                <th>Total Volume (USDT)</th>
                                <th>Total Amount</th>
                                <th>Total Fees</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Add symbol summary rows
        for symbol, row in symbol_summary.iterrows():
            html_content += f"""
                            <tr>
                                <td><strong>{symbol}</strong></td>
                                <td>{int(row['Trade Count'])}</td>
                                <td>${row['Total Volume (USDT)']:,.2f}</td>
                                <td>{row['Total Amount']:.6f}</td>
                                <td>${row['Total Fees']:.4f}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📅 Daily Breakdown</h2>
                <div class="scrollable">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Trade Count</th>
                                <th>Daily Volume (USDT)</th>
                                <th>Daily Fees</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Add daily summary rows
        for date, row in daily_summary.iterrows():
            html_content += f"""
                            <tr>
                                <td><strong>{date}</strong></td>
                                <td>{int(row['Trade Count'])}</td>
                                <td>${row['Daily Volume (USDT)']:,.2f}</td>
                                <td>${row['Daily Fees']:.4f}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Detailed Trade History</h2>
                <div class="scrollable">
                    <table>
                        <thead>
                            <tr>
                                <th>Date/Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Amount</th>
                                <th>Price</th>
                                <th>Total (USDT)</th>
                                <th>Fee</th>
                                <th>Type</th>
                                <th>Order ID</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Add detailed trade rows
        for _, trade in df.iterrows():
            side_class = "buy" if trade['side'] == 'buy' else "sell"
            dt = pd.to_datetime(trade['datetime']).strftime('%m/%d %H:%M:%S')
            
            html_content += f"""
                            <tr>
                                <td>{dt}</td>
                                <td><strong>{trade['symbol']}</strong></td>
                                <td class="{side_class}">{trade['side'].upper()}</td>
                                <td>{trade['amount']:.6f}</td>
                                <td>${trade['price']:,.2f}</td>
                                <td>${trade['cost']:,.2f}</td>
                                <td>${trade['fee_cost']:.4f}</td>
                                <td>{trade['type']}</td>
                                <td>{trade['order_id']}</td>
                            </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Report generated by Bybit Trade History Exporter • {len(self.trades_data)} total trades processed
        </div>
    </div>
</body>
</html>
        """
        
        # Save HTML file
        filename = f"bybit_trade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML report generated: {filename}")
        return filename
    
    def save_csv_export(self):
        """Save trade data as CSV for further analysis"""
        if not self.trades_data:
            return None
        
        df = pd.DataFrame(self.trades_data)
        filename = f"bybit_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ CSV export saved: {filename}")
        return filename

def main():
    """Main function to run the export"""
    print("🚀 Bybit Trade History Exporter")
    print("=" * 50)
    
    # Check if API credentials are set
    if not os.getenv('BYBIT_API_KEY') or not os.getenv('BYBIT_API_SECRET'):
        print("❌ Error: BYBIT_API_KEY and BYBIT_API_SECRET must be set in your .env file")
        return
    
    exporter = BybitTradeHistoryExporter()
    
    # Fetch trade history
    if exporter.fetch_trade_history(days=4):
        # Generate reports
        html_file = exporter.generate_html_report()
        csv_file = exporter.save_csv_export()
        
        print("\n" + "=" * 50)
        print("✅ Export completed successfully!")
        if html_file:
            print(f"📊 HTML Report: {html_file}")
        if csv_file:
            print(f"📈 CSV Export: {csv_file}")
    else:
        print("❌ Failed to fetch trade history")

if __name__ == "__main__":
    main() 