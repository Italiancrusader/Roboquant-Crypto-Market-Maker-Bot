#!/usr/bin/env python3
"""
Configuration Wizard for Market Making Bot
Simple GUI to help users configure the bot without editing JSON
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys

class ConfigWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Market Making Bot Configuration Wizard")
        self.root.geometry("800x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_exchange_tab()
        self.create_trading_tab()
        self.create_strategy_tab()
        self.create_risk_tab()
        
        # Create buttons
        button_frame = tk.Frame(root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(button_frame, text="Save Configuration", command=self.save_config, 
                 bg='green', fg='white', font=('Arial', 12)).pack(side='left', padx=5)
        tk.Button(button_frame, text="Load Existing Config", command=self.load_config,
                 bg='blue', fg='white', font=('Arial', 12)).pack(side='left', padx=5)
        tk.Button(button_frame, text="Test Connection", command=self.test_connection,
                 bg='orange', fg='white', font=('Arial', 12)).pack(side='left', padx=5)
        tk.Button(button_frame, text="Exit", command=root.quit,
                 bg='red', fg='white', font=('Arial', 12)).pack(side='right', padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to configure your bot")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, 
                             relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Variables
        self.config_vars = {}
        
    def create_exchange_tab(self):
        """Create exchange configuration tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Exchange Settings")
        
        # Title
        tk.Label(tab, text="Exchange Configuration", font=('Arial', 16, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10)
        
        # Exchange selection
        tk.Label(tab, text="Select Exchange:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.exchange_var = tk.StringVar(value="bybit")
        exchanges = ["binance", "bybit", "okx", "kucoin", "gate", "mexc", 
                    "bitget", "hyperliquid", "phemex", "huobi", "kraken"]
        exchange_menu = ttk.Combobox(tab, textvariable=self.exchange_var, values=exchanges, width=30)
        exchange_menu.grid(row=1, column=1, padx=5, pady=5)
        exchange_menu.bind('<<ComboboxSelected>>', self.on_exchange_change)
        
        # API Key
        tk.Label(tab, text="API Key:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.api_key_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.api_key_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        # API Secret
        tk.Label(tab, text="API Secret:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.api_secret_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.api_secret_var, width=40, show='*').grid(row=3, column=1, padx=5, pady=5)
        
        # Special fields for Hyperliquid
        self.hl_frame = tk.Frame(tab)
        self.hl_frame.grid(row=4, column=0, columnspan=2, pady=10)
        tk.Label(self.hl_frame, text="Private Key:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.private_key_var = tk.StringVar()
        tk.Entry(self.hl_frame, textvariable=self.private_key_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.hl_frame, text="Wallet Address:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.wallet_address_var = tk.StringVar()
        tk.Entry(self.hl_frame, textvariable=self.wallet_address_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        self.hl_frame.grid_remove()  # Hide by default
        
        # Testnet
        self.testnet_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab, text="Use Testnet (for testing)", variable=self.testnet_var).grid(
            row=5, column=0, columnspan=2, pady=10)
        
        # Instructions
        instructions = """
Instructions:
1. Select your exchange from the dropdown
2. Enter your API credentials
3. For most exchanges, you need API Key and Secret
4. For Hyperliquid, use Private Key and Wallet Address
5. Enable Testnet for testing with fake money
        """
        tk.Label(tab, text=instructions, justify='left', bg='light yellow').grid(
            row=6, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        
    def create_trading_tab(self):
        """Create trading configuration tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Trading Settings")
        
        # Title
        tk.Label(tab, text="Trading Configuration", font=('Arial', 16, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10)
        
        # Symbol
        tk.Label(tab, text="Trading Pair:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.symbol_var = tk.StringVar(value="ETH/USDT:USDT")
        symbol_menu = ttk.Combobox(tab, textvariable=self.symbol_var, width=30)
        symbol_menu['values'] = ["BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT", 
                                "SOL/USDT:USDT", "XRP/USDT:USDT", "DOGE/USDT:USDT"]
        symbol_menu.grid(row=1, column=1, padx=5, pady=5)
        
        # Leverage
        tk.Label(tab, text="Leverage:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.leverage_var = tk.IntVar(value=5)
        leverage_scale = tk.Scale(tab, from_=1, to=20, orient='horizontal', 
                                 variable=self.leverage_var, length=200)
        leverage_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # Order size type
        tk.Label(tab, text="Order Size Type:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.order_type_var = tk.StringVar(value="percentage")
        tk.Radiobutton(tab, text="Percentage of Balance", variable=self.order_type_var, 
                      value="percentage").grid(row=3, column=1, sticky='w')
        tk.Radiobutton(tab, text="Fixed Amount", variable=self.order_type_var, 
                      value="fixed").grid(row=4, column=1, sticky='w')
        
        # Order size percentage
        tk.Label(tab, text="Order Size (% of balance):").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        self.order_percent_var = tk.DoubleVar(value=1.0)
        percent_scale = tk.Scale(tab, from_=0.1, to=10.0, resolution=0.1, orient='horizontal',
                                variable=self.order_percent_var, length=200)
        percent_scale.grid(row=5, column=1, padx=5, pady=5)
        
        # Fixed order size
        tk.Label(tab, text="Fixed Order Size:").grid(row=6, column=0, sticky='e', padx=5, pady=5)
        self.order_size_var = tk.DoubleVar(value=0.001)
        tk.Entry(tab, textvariable=self.order_size_var, width=20).grid(row=6, column=1, padx=5, pady=5, sticky='w')
        
        # Instructions
        instructions = """
Tips:
• Popular pairs: BTC, ETH, BNB have best liquidity
• Start with low leverage (1-5x) until comfortable
• Use 0.5-2% of balance per order for safety
• Fixed size is useful for consistent position sizing
        """
        tk.Label(tab, text=instructions, justify='left', bg='light yellow').grid(
            row=7, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        
    def create_strategy_tab(self):
        """Create strategy configuration tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Strategy Settings")
        
        # Title
        tk.Label(tab, text="Strategy Parameters", font=('Arial', 16, 'bold')).grid(
            row=0, column=0, columnspan=3, pady=10)
        
        # Preset buttons
        preset_frame = tk.Frame(tab)
        preset_frame.grid(row=1, column=0, columnspan=3, pady=10)
        tk.Button(preset_frame, text="Conservative", command=lambda: self.load_preset('conservative'),
                 bg='green', fg='white').pack(side='left', padx=5)
        tk.Button(preset_frame, text="Balanced", command=lambda: self.load_preset('balanced'),
                 bg='blue', fg='white').pack(side='left', padx=5)
        tk.Button(preset_frame, text="Aggressive", command=lambda: self.load_preset('aggressive'),
                 bg='red', fg='white').pack(side='left', padx=5)
        
        # Gamma (risk aversion)
        tk.Label(tab, text="Risk Aversion (gamma):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.gamma_var = tk.DoubleVar(value=0.1)
        gamma_scale = tk.Scale(tab, from_=0.01, to=1.0, resolution=0.01, orient='horizontal',
                              variable=self.gamma_var, length=200)
        gamma_scale.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(tab, text="Lower = More aggressive").grid(row=2, column=2, sticky='w')
        
        # K (market impact)
        tk.Label(tab, text="Market Impact (k):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.k_var = tk.DoubleVar(value=1.5)
        k_scale = tk.Scale(tab, from_=0.5, to=5.0, resolution=0.1, orient='horizontal',
                          variable=self.k_var, length=200)
        k_scale.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(tab, text="Higher = Tighter spreads").grid(row=3, column=2, sticky='w')
        
        # Update frequency
        tk.Label(tab, text="Update Frequency (seconds):").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        self.update_freq_var = tk.DoubleVar(value=2.0)
        freq_scale = tk.Scale(tab, from_=0.5, to=10.0, resolution=0.5, orient='horizontal',
                             variable=self.update_freq_var, length=200)
        freq_scale.grid(row=4, column=1, padx=5, pady=5)
        tk.Label(tab, text="How often to update quotes").grid(row=4, column=2, sticky='w')
        
        # Max spread
        tk.Label(tab, text="Max Spread (%):").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        self.max_spread_var = tk.DoubleVar(value=0.5)
        spread_scale = tk.Scale(tab, from_=0.1, to=2.0, resolution=0.1, orient='horizontal',
                               variable=self.max_spread_var, length=200)
        spread_scale.grid(row=5, column=1, padx=5, pady=5)
        tk.Label(tab, text="Maximum bid-ask spread").grid(row=5, column=2, sticky='w')
        
        # Other parameters
        tk.Label(tab, text="Time Horizon (hours):").grid(row=6, column=0, sticky='e', padx=5, pady=5)
        self.time_horizon_var = tk.DoubleVar(value=1.0)
        tk.Entry(tab, textvariable=self.time_horizon_var, width=10).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(tab, text="Volatility Lookback:").grid(row=7, column=0, sticky='e', padx=5, pady=5)
        self.lookback_var = tk.IntVar(value=100)
        tk.Entry(tab, textvariable=self.lookback_var, width=10).grid(row=7, column=1, sticky='w', padx=5, pady=5)
        
    def create_risk_tab(self):
        """Create risk management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Risk Management")
        
        # Title
        tk.Label(tab, text="Risk Management Settings", font=('Arial', 16, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10)
        
        # Max inventory
        tk.Label(tab, text="Max Inventory (USD):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.max_inventory_var = tk.DoubleVar(value=1000)
        tk.Entry(tab, textvariable=self.max_inventory_var, width=20).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Max position size
        tk.Label(tab, text="Max Position Size (USD):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.max_position_var = tk.DoubleVar(value=100)
        tk.Entry(tab, textvariable=self.max_position_var, width=20).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # Stop loss
        tk.Label(tab, text="Stop Loss (%):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.stop_loss_var = tk.DoubleVar(value=5.0)
        stop_scale = tk.Scale(tab, from_=1.0, to=20.0, resolution=0.5, orient='horizontal',
                             variable=self.stop_loss_var, length=200)
        stop_scale.grid(row=3, column=1, padx=5, pady=5)
        
        # Daily loss limit
        tk.Label(tab, text="Daily Loss Limit (USD):").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        self.daily_limit_var = tk.DoubleVar(value=50)
        tk.Entry(tab, textvariable=self.daily_limit_var, width=20).grid(row=4, column=1, sticky='w', padx=5, pady=5)
        
        # Warning
        warning = """
⚠️ IMPORTANT RISK WARNINGS:

• Start with SMALL amounts to test
• Monitor the bot regularly
• Set conservative limits initially
• Never risk more than you can afford to lose
• Test on testnet first if available
• Market making can result in losses

The bot will automatically stop if:
- Inventory exceeds maximum
- Daily loss limit is reached
- Stop loss is triggered
        """
        warning_label = tk.Label(tab, text=warning, justify='left', bg='light coral', 
                                font=('Arial', 10, 'bold'))
        warning_label.grid(row=5, column=0, columnspan=2, padx=10, pady=20, sticky='ew')
        
    def on_exchange_change(self, event=None):
        """Handle exchange selection change"""
        if self.exchange_var.get() == 'hyperliquid':
            self.hl_frame.grid()
        else:
            self.hl_frame.grid_remove()
    
    def load_preset(self, preset_type):
        """Load preset strategy parameters"""
        if preset_type == 'conservative':
            self.gamma_var.set(0.5)
            self.k_var.set(1.0)
            self.update_freq_var.set(5.0)
            self.max_spread_var.set(0.5)
            self.leverage_var.set(2)
            self.order_percent_var.set(0.5)
            messagebox.showinfo("Preset Loaded", "Conservative settings loaded - Good for beginners")
        elif preset_type == 'balanced':
            self.gamma_var.set(0.1)
            self.k_var.set(1.5)
            self.update_freq_var.set(2.0)
            self.max_spread_var.set(0.3)
            self.leverage_var.set(5)
            self.order_percent_var.set(1.0)
            messagebox.showinfo("Preset Loaded", "Balanced settings loaded - Good for most users")
        elif preset_type == 'aggressive':
            self.gamma_var.set(0.01)
            self.k_var.set(3.0)
            self.update_freq_var.set(0.5)
            self.max_spread_var.set(0.2)
            self.leverage_var.set(10)
            self.order_percent_var.set(2.0)
            messagebox.showinfo("Preset Loaded", "Aggressive settings loaded - For experienced users only!")
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            "exchange": {
                "name": self.exchange_var.get(),
                "api_key": self.api_key_var.get(),
                "api_secret": self.api_secret_var.get(),
                "testnet": self.testnet_var.get()
            },
            "trading": {
                "symbol": self.symbol_var.get(),
                "leverage": self.leverage_var.get(),
                "order_size_type": self.order_type_var.get(),
                "order_size_percent": self.order_percent_var.get() / 100,
                "order_size": self.order_size_var.get()
            },
            "strategy": {
                "gamma": self.gamma_var.get(),
                "k": self.k_var.get(),
                "time_horizon": self.time_horizon_var.get(),
                "sigma_lookback": self.lookback_var.get(),
                "update_frequency": self.update_freq_var.get(),
                "min_spread": 0.0001,
                "max_spread_percent": self.max_spread_var.get() / 100,
                "max_quote_distance_percent": 0.005
            },
            "risk": {
                "max_inventory_usd": self.max_inventory_var.get(),
                "max_position_size_usd": self.max_position_var.get(),
                "stop_loss_percent": self.stop_loss_var.get() / 100,
                "daily_loss_limit_usd": self.daily_limit_var.get()
            }
        }
        
        # Add Hyperliquid specific fields if needed
        if self.exchange_var.get() == 'hyperliquid':
            config["exchange"]["private_key"] = self.private_key_var.get()
            config["exchange"]["wallet_address"] = self.wallet_address_var.get()
        
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved to config.json")
            self.status_var.set("Configuration saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        """Load existing configuration"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            # Load values
            self.exchange_var.set(config['exchange']['name'])
            self.api_key_var.set(config['exchange'].get('api_key', ''))
            self.api_secret_var.set(config['exchange'].get('api_secret', ''))
            self.testnet_var.set(config['exchange'].get('testnet', False))
            
            self.symbol_var.set(config['trading']['symbol'])
            self.leverage_var.set(config['trading']['leverage'])
            self.order_type_var.set(config['trading']['order_size_type'])
            self.order_percent_var.set(config['trading']['order_size_percent'] * 100)
            self.order_size_var.set(config['trading']['order_size'])
            
            self.gamma_var.set(config['strategy']['gamma'])
            self.k_var.set(config['strategy']['k'])
            self.time_horizon_var.set(config['strategy']['time_horizon'])
            self.lookback_var.set(config['strategy']['sigma_lookback'])
            self.update_freq_var.set(config['strategy']['update_frequency'])
            self.max_spread_var.set(config['strategy']['max_spread_percent'] * 100)
            
            self.max_inventory_var.set(config['risk']['max_inventory_usd'])
            self.max_position_var.set(config['risk']['max_position_size_usd'])
            self.stop_loss_var.set(config['risk']['stop_loss_percent'] * 100)
            self.daily_limit_var.set(config['risk']['daily_loss_limit_usd'])
            
            # Load Hyperliquid fields if present
            if config['exchange']['name'] == 'hyperliquid':
                self.private_key_var.set(config['exchange'].get('private_key', ''))
                self.wallet_address_var.set(config['exchange'].get('wallet_address', ''))
                self.on_exchange_change()
            
            messagebox.showinfo("Success", "Configuration loaded from config.json")
            self.status_var.set("Configuration loaded successfully")
        except FileNotFoundError:
            messagebox.showwarning("Warning", "No config.json found. Please configure settings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def test_connection(self):
        """Test exchange connection"""
        self.status_var.set("Testing connection...")
        self.root.update()
        
        # Create a test window
        test_window = tk.Toplevel(self.root)
        test_window.title("Connection Test")
        test_window.geometry("500x400")
        
        # Create text widget for output
        output_text = scrolledtext.ScrolledText(test_window, wrap=tk.WORD, width=60, height=20)
        output_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Test connection
        try:
            import ccxt
            
            output_text.insert(tk.END, f"Testing connection to {self.exchange_var.get()}...\n\n")
            
            # Get exchange class
            exchange_name = self.exchange_var.get().lower()
            exchange_classes = {
                'binance': ccxt.binance,
                'bybit': ccxt.bybit,
                'okx': ccxt.okx,
                'kucoin': ccxt.kucoin,
                'gate': ccxt.gate,
                'mexc': ccxt.mexc,
                'bitget': ccxt.bitget,
                'hyperliquid': ccxt.hyperliquid,
                'phemex': ccxt.phemex,
                'huobi': ccxt.huobi,
                'kraken': ccxt.kraken
            }
            
            if exchange_name not in exchange_classes:
                output_text.insert(tk.END, f"❌ Exchange {exchange_name} not supported\n")
                return
            
            # Create exchange instance
            exchange_config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            }
            
            if self.api_key_var.get():
                exchange_config['apiKey'] = self.api_key_var.get()
                exchange_config['secret'] = self.api_secret_var.get()
            
            if exchange_name == 'hyperliquid' and self.private_key_var.get():
                exchange_config['privateKey'] = self.private_key_var.get()
                exchange_config['walletAddress'] = self.wallet_address_var.get()
            
            if self.testnet_var.get():
                exchange_config['sandbox'] = True
            
            exchange = exchange_classes[exchange_name](exchange_config)
            
            # Test 1: Load markets
            output_text.insert(tk.END, "1. Loading markets... ")
            markets = exchange.load_markets()
            output_text.insert(tk.END, f"✅ Success! Found {len(markets)} markets\n\n")
            
            # Test 2: Check symbol
            symbol = self.symbol_var.get()
            output_text.insert(tk.END, f"2. Checking symbol {symbol}... ")
            if symbol in markets:
                market = markets[symbol]
                output_text.insert(tk.END, f"✅ Found!\n")
                output_text.insert(tk.END, f"   Min order size: {market['limits']['amount']['min']}\n")
                output_text.insert(tk.END, f"   Price precision: {market['precision']['price']}\n\n")
            else:
                output_text.insert(tk.END, f"❌ Not found!\n")
                output_text.insert(tk.END, f"   Available similar symbols:\n")
                similar = [s for s in markets.keys() if 'USDT' in s][:5]
                for s in similar:
                    output_text.insert(tk.END, f"   - {s}\n")
                output_text.insert(tk.END, "\n")
            
            # Test 3: Fetch ticker
            output_text.insert(tk.END, f"3. Fetching ticker... ")
            ticker = exchange.fetch_ticker(symbol)
            output_text.insert(tk.END, f"✅ Success!\n")
            output_text.insert(tk.END, f"   Current price: ${ticker['last']:.2f}\n")
            output_text.insert(tk.END, f"   24h volume: ${ticker['quoteVolume']:.0f}\n\n")
            
            # Test 4: Check balance (if API keys provided)
            if self.api_key_var.get():
                output_text.insert(tk.END, "4. Checking balance... ")
                try:
                    balance = exchange.fetch_balance()
                    quote_currency = symbol.split('/')[1].split(':')[0]
                    available = balance.get(quote_currency, {}).get('free', 0)
                    output_text.insert(tk.END, f"✅ Success!\n")
                    output_text.insert(tk.END, f"   Available {quote_currency}: {available:.2f}\n\n")
                except Exception as e:
                    output_text.insert(tk.END, f"❌ Failed: {str(e)}\n\n")
            
            output_text.insert(tk.END, "✅ Connection test completed successfully!\n")
            output_text.insert(tk.END, "You're ready to start the bot.\n")
            self.status_var.set("Connection test successful!")
            
        except Exception as e:
            output_text.insert(tk.END, f"\n❌ Connection test failed:\n{str(e)}\n")
            self.status_var.set("Connection test failed")
        
        # Add close button
        tk.Button(test_window, text="Close", command=test_window.destroy).pack(pady=5)


def main():
    root = tk.Tk()
    app = ConfigWizard(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
