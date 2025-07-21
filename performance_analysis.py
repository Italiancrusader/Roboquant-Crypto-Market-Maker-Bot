import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import seaborn as sns
import base64
from io import BytesIO
import os
import glob

# Set style for better looking plots
plt.style.use('default')
sns.set_palette("husl")

class TradingPerformanceAnalyzer:
    def __init__(self, csv_file=None):
        self.csv_file = csv_file
        self.trades_df = None
        self.performance_metrics = {}
        self.equity_curve = None
        self.drawdown_series = None
        
    def load_data(self):
        """Load trade data from CSV file"""
        if self.csv_file is None:
            # Find the most recent CSV file
            csv_files = glob.glob("bybit_trades_*.csv")
            if not csv_files:
                raise FileNotFoundError("No trade CSV files found")
            self.csv_file = max(csv_files, key=os.path.getctime)
            print(f"Using most recent CSV file: {self.csv_file}")
        
        self.trades_df = pd.read_csv(self.csv_file)
        self.trades_df['datetime'] = pd.to_datetime(self.trades_df['datetime'])
        self.trades_df = self.trades_df.sort_values('datetime')
        
        print(f"Loaded {len(self.trades_df)} trades from {self.csv_file}")
        return self.trades_df
    
    def calculate_trade_pnl(self):
        """Calculate P&L for each trade pair (buy/sell)"""
        # Group trades by symbol and calculate running position
        pnl_data = []
        
        for symbol in self.trades_df['symbol'].unique():
            symbol_trades = self.trades_df[self.trades_df['symbol'] == symbol].copy()
            
            position = 0
            avg_price = 0
            
            for _, trade in symbol_trades.iterrows():
                if trade['side'] == 'buy':
                    # Opening or adding to long position
                    if position >= 0:
                        # Adding to long position
                        avg_price = (avg_price * position + trade['price'] * trade['amount']) / (position + trade['amount'])
                        position += trade['amount']
                    else:
                        # Closing short position
                        pnl_amount = min(abs(position), trade['amount'])
                        pnl = pnl_amount * (avg_price - trade['price'])
                        
                        pnl_data.append({
                            'datetime': trade['datetime'],
                            'symbol': symbol,
                            'pnl': pnl,
                            'trade_id': trade['id'],
                            'side': 'close_short',
                            'amount': pnl_amount,
                            'entry_price': avg_price,
                            'exit_price': trade['price'],
                            'fee': trade['fee_cost']
                        })
                        
                        position += trade['amount']  # Reduce short position
                        if position > 0:
                            avg_price = trade['price']
                        
                else:  # sell
                    # Opening short or closing long position
                    if position <= 0:
                        # Adding to short position
                        avg_price = (avg_price * abs(position) + trade['price'] * trade['amount']) / (abs(position) + trade['amount'])
                        position -= trade['amount']
                    else:
                        # Closing long position
                        pnl_amount = min(position, trade['amount'])
                        pnl = pnl_amount * (trade['price'] - avg_price)
                        
                        pnl_data.append({
                            'datetime': trade['datetime'],
                            'symbol': symbol,
                            'pnl': pnl,
                            'trade_id': trade['id'],
                            'side': 'close_long',
                            'amount': pnl_amount,
                            'entry_price': avg_price,
                            'exit_price': trade['price'],
                            'fee': trade['fee_cost']
                        })
                        
                        position -= trade['amount']  # Reduce long position
                        if position < 0:
                            avg_price = trade['price']
        
        self.pnl_df = pd.DataFrame(pnl_data)
        if len(self.pnl_df) > 0:
            self.pnl_df['net_pnl'] = self.pnl_df['pnl'] - self.pnl_df['fee']
        
        return self.pnl_df
    
    def calculate_equity_curve(self):
        """Calculate equity curve from trades"""
        if self.pnl_df is None or len(self.pnl_df) == 0:
            # Fallback: simple calculation based on volume and fees
            self.trades_df['simple_pnl'] = 0  # We don't have entry/exit pairs, so assume break-even on price
            self.trades_df['net_pnl'] = -self.trades_df['fee_cost']  # Only account for fees
            
            self.equity_curve = self.trades_df.groupby('datetime')['net_pnl'].sum().cumsum()
            starting_balance = 1000  # Assume starting balance
            self.equity_curve = starting_balance + self.equity_curve
        else:
            # Use calculated P&L
            daily_pnl = self.pnl_df.groupby(self.pnl_df['datetime'].dt.date)['net_pnl'].sum()
            self.equity_curve = daily_pnl.cumsum()
            starting_balance = 1000  # Assume starting balance
            self.equity_curve = starting_balance + self.equity_curve
        
        return self.equity_curve
    
    def calculate_drawdown(self):
        """Calculate drawdown series"""
        if self.equity_curve is None:
            self.calculate_equity_curve()
        
        # Calculate running maximum
        running_max = self.equity_curve.expanding().max()
        
        # Calculate drawdown
        self.drawdown_series = (self.equity_curve - running_max) / running_max * 100
        
        return self.drawdown_series
    
    def calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        if self.pnl_df is None or len(self.pnl_df) == 0:
            # Fallback metrics based on fees only
            total_trades = len(self.trades_df)
            total_volume = self.trades_df['cost'].sum()
            total_fees = self.trades_df['fee_cost'].sum()
            
            self.performance_metrics = {
                'total_trades': total_trades,
                'total_volume': total_volume,
                'total_fees': total_fees,
                'net_pnl': -total_fees,
                'gross_pnl': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'trading_days': (self.trades_df['datetime'].max() - self.trades_df['datetime'].min()).days,
                'avg_trades_per_day': 0
            }
        else:
            # Full metrics calculation
            winning_trades = self.pnl_df[self.pnl_df['net_pnl'] > 0]
            losing_trades = self.pnl_df[self.pnl_df['net_pnl'] < 0]
            
            total_trades = len(self.pnl_df)
            win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
            
            gross_profit = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 0
            net_pnl = gross_profit - gross_loss
            
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
            
            # Calculate drawdown
            if self.drawdown_series is None:
                self.calculate_drawdown()
            max_drawdown = abs(self.drawdown_series.min()) if len(self.drawdown_series) > 0 else 0
            
            # Calculate Sharpe ratio (simplified)
            if len(self.pnl_df) > 1:
                returns = self.pnl_df['net_pnl'].pct_change().dropna()
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            trading_days = (self.pnl_df['datetime'].max() - self.pnl_df['datetime'].min()).days
            avg_trades_per_day = total_trades / max(trading_days, 1)
            
            self.performance_metrics = {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'net_pnl': net_pnl,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'trading_days': trading_days,
                'avg_trades_per_day': avg_trades_per_day
            }
        
        return self.performance_metrics
    
    def create_charts(self):
        """Create performance charts"""
        # Set up the figure
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Equity Curve
        ax1 = plt.subplot(2, 2, 1)
        if self.equity_curve is not None and len(self.equity_curve) > 0:
            self.equity_curve.plot(ax=ax1, color='#2E86AB', linewidth=2)
            ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Account Value ($)')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
        
        # 2. Drawdown Chart
        ax2 = plt.subplot(2, 2, 2)
        if self.drawdown_series is not None and len(self.drawdown_series) > 0:
            self.drawdown_series.plot(ax=ax2, color='#F24236', linewidth=2, kind='area', alpha=0.6)
            ax2.set_title('Drawdown (%)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Drawdown (%)')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Trade P&L Distribution
        ax3 = plt.subplot(2, 2, 3)
        if self.pnl_df is not None and len(self.pnl_df) > 0:
            self.pnl_df['net_pnl'].hist(bins=20, ax=ax3, color='#A23B72', alpha=0.7, edgecolor='black')
            ax3.axvline(x=0, color='red', linestyle='--', alpha=0.8)
            ax3.set_title('P&L Distribution', fontsize=14, fontweight='bold')
            ax3.set_xlabel('P&L ($)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)
        
        # 4. Daily P&L
        ax4 = plt.subplot(2, 2, 4)
        if self.pnl_df is not None and len(self.pnl_df) > 0:
            daily_pnl = self.pnl_df.groupby(self.pnl_df['datetime'].dt.date)['net_pnl'].sum()
            colors = ['green' if x > 0 else 'red' for x in daily_pnl]
            daily_pnl.plot(kind='bar', ax=ax4, color=colors, alpha=0.7)
            ax4.set_title('Daily P&L', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Date')
            ax4.set_ylabel('Daily P&L ($)')
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save chart to base64 for HTML embedding
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_data
    
    def generate_html_report(self):
        """Generate comprehensive HTML performance report"""
        # Calculate all metrics
        self.calculate_trade_pnl()
        self.calculate_equity_curve()
        self.calculate_drawdown()
        self.calculate_performance_metrics()
        
        # Create charts
        chart_data = self.create_charts()
        
        # Get summary statistics
        metrics = self.performance_metrics
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Performance Report</title>
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
        .metric-value.positive {{
            color: #00c851;
        }}
        .metric-value.negative {{
            color: #ff4444;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-container img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
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
        .risk-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .risk-card {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
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
            <h1>📈 Trading Performance Report</h1>
            <p>Comprehensive Analysis • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>🎯 Key Performance Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('net_pnl', 0) > 0 else 'negative'}">${metrics.get('net_pnl', 0):.2f}</div>
                        <div class="metric-label">Net P&L</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('total_trades', 0):,}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('win_rate', 0) > 50 else 'negative'}">{metrics.get('win_rate', 0):.1f}%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('profit_factor', 0) > 1 else 'negative'}">{metrics.get('profit_factor', 0):.2f}</div>
                        <div class="metric-label">Profit Factor</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value negative">{metrics.get('max_drawdown', 0):.2f}%</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('sharpe_ratio', 0):.2f}</div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.get('avg_win', 0):.2f}</div>
                        <div class="metric-label">Average Win</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.get('avg_loss', 0):.2f}</div>
                        <div class="metric-label">Average Loss</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Performance Charts</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart_data}" alt="Performance Charts">
                </div>
            </div>
            
            <div class="section">
                <h2>⚠️ Risk Analysis</h2>
                <div class="risk-metrics">
                    <div class="risk-card">
                        <strong>Trading Period</strong><br>
                        {metrics.get('trading_days', 0)} days
                    </div>
                    <div class="risk-card">
                        <strong>Trades per Day</strong><br>
                        {metrics.get('avg_trades_per_day', 0):.1f}
                    </div>
                    <div class="risk-card">
                        <strong>Winning Trades</strong><br>
                        {metrics.get('winning_trades', 0)} trades
                    </div>
                    <div class="risk-card">
                        <strong>Losing Trades</strong><br>
                        {metrics.get('losing_trades', 0)} trades
                    </div>
                    <div class="risk-card">
                        <strong>Gross Profit</strong><br>
                        ${metrics.get('gross_profit', 0):.2f}
                    </div>
                    <div class="risk-card">
                        <strong>Gross Loss</strong><br>
                        ${metrics.get('gross_loss', 0):.2f}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Performance Summary</h2>
                <div style="background: #f8f9ff; padding: 20px; border-radius: 10px;">
                    <h3>Overall Assessment</h3>
                    <p><strong>Trading Strategy:</strong> High-frequency market making on ETH/USDT perpetual futures</p>
                    <p><strong>Performance Period:</strong> {metrics.get('trading_days', 0)} days with {metrics.get('total_trades', 0)} total trades</p>
                    <p><strong>Risk Level:</strong> {'Low' if metrics.get('max_drawdown', 0) < 5 else 'Medium' if metrics.get('max_drawdown', 0) < 15 else 'High'} (Max DD: {metrics.get('max_drawdown', 0):.2f}%)</p>
                    <p><strong>Profitability:</strong> {'Profitable' if metrics.get('net_pnl', 0) > 0 else 'Unprofitable'} with {metrics.get('win_rate', 0):.1f}% win rate</p>
                    
                    <h3>Key Insights</h3>
                    <ul>
                        <li>{'✅' if metrics.get('profit_factor', 0) > 1 else '❌'} Profit Factor: {metrics.get('profit_factor', 0):.2f} ({'Profitable' if metrics.get('profit_factor', 0) > 1 else 'Needs Improvement'})</li>
                        <li>{'✅' if metrics.get('win_rate', 0) > 50 else '❌'} Win Rate: {metrics.get('win_rate', 0):.1f}% ({'Good' if metrics.get('win_rate', 0) > 60 else 'Average' if metrics.get('win_rate', 0) > 40 else 'Low'})</li>
                        <li>{'✅' if metrics.get('sharpe_ratio', 0) > 1 else '❌'} Risk-Adjusted Returns: {metrics.get('sharpe_ratio', 0):.2f} Sharpe Ratio</li>
                        <li>{'✅' if metrics.get('max_drawdown', 0) < 10 else '❌'} Drawdown Control: {metrics.get('max_drawdown', 0):.2f}% maximum drawdown</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Report generated by Trading Performance Analyzer • Data from {os.path.basename(self.csv_file) if self.csv_file else 'Unknown'} • {metrics.get('total_trades', 0)} trades analyzed
        </div>
    </div>
</body>
</html>
        """
        
        # Save HTML file
        filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Performance report generated: {filename}")
        return filename

def main():
    """Main function to run the performance analysis"""
    print("🚀 Trading Performance Analyzer")
    print("=" * 50)
    
    analyzer = TradingPerformanceAnalyzer()
    
    try:
        # Load data
        analyzer.load_data()
        
        # Generate comprehensive report
        report_file = analyzer.generate_html_report()
        
        print("\n" + "=" * 50)
        print("✅ Performance analysis completed!")
        print(f"📊 Performance Report: {report_file}")
        
        # Print key metrics to console
        metrics = analyzer.performance_metrics
        print(f"\n📈 Quick Summary:")
        print(f"   Net P&L: ${metrics.get('net_pnl', 0):.2f}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"   Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"   Total Trades: {metrics.get('total_trades', 0)}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main() 