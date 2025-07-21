import ccxt
import time
import math
import numpy as np
import os
from dotenv import load_dotenv
from collections import deque
import statistics

# Load environment variables
load_dotenv()

# Initialize Hyperliquid exchange via CCXT
exchange = ccxt.hyperliquid({
    'privateKey': os.getenv('HYPERLIQUID_API_SECRET', '0x900e87a409affffc14dcbbd20df9e76eb1dec7b70885185d4b907adb30880fc9'),
    'walletAddress': os.getenv('HYPERLIQUID_API_KEY', '0xdaB5795F1F5ae002d833c9021fbDD55F71567adb'),
    'sandbox': False,  # Set to True for testnet
    'enableRateLimit': True,
})

# Avellaneda-Stoikov Parameters
symbol = "XRP/USDC:USDC"  # XRP perpetual contract
leverage = 5  # 5x leverage
min_order_value = 10  # Minimum order value required by Hyperliquid ($10)

# Strategy Parameters
gamma = 0.1  # Risk aversion parameter (higher = more conservative)
k = 1.5  # Market impact parameter
alpha = 0.01  # Inventory penalty parameter
sigma_lookback = 100  # Number of price observations for volatility calculation
T = 1.0  # Time horizon (1 hour in hours)
dt = 1/3600  # Time step (1 second in hours)

# High-frequency parameters
update_frequency = 1  # Update quotes every 1 second
max_inventory = 100  # Maximum inventory in USDC value
target_inventory = 0  # Target inventory (neutral)

# Data storage
price_history = deque(maxlen=sigma_lookback)
inventory = 0  # Current inventory in XRP
last_mid_price = 0
volatility = 0.01  # Initial volatility estimate

class AvellanedaStoikovMM:
    def __init__(self):
        self.current_orders = {'bid': None, 'ask': None}
        self.last_quote_time = 0
        self.pnl = 0
        self.trades_count = 0
        
    def calculate_volatility(self):
        """Calculate realized volatility from price history"""
        global volatility
        if len(price_history) < 2:
            return volatility
        
        returns = []
        for i in range(1, len(price_history)):
            ret = math.log(price_history[i] / price_history[i-1])
            returns.append(ret)
        
        if len(returns) > 1:
            volatility = statistics.stdev(returns) * math.sqrt(3600)  # Annualized hourly volatility
            volatility = max(volatility, 0.001)  # Minimum volatility
        
        return volatility
    
    def calculate_reservation_price(self, mid_price):
        """Calculate reservation price based on inventory"""
        global inventory
        q = inventory  # Current inventory
        sigma = self.calculate_volatility()
        
        # Reservation price adjustment for inventory risk
        reservation_price = mid_price - (q * gamma * sigma**2 * (T - time.time() % 3600 / 3600))
        return reservation_price
    
    def calculate_optimal_spread(self, mid_price):
        """Calculate optimal bid-ask spread using Avellaneda-Stoikov formula"""
        sigma = self.calculate_volatility()
        
        # Optimal spread calculation
        spread = gamma * sigma**2 * (T - time.time() % 3600 / 3600) + (2/gamma) * math.log(1 + gamma/k)
        
        # Ensure minimum spread for profitability
        min_spread = 0.0001  # Minimum spread
        spread = max(spread, min_spread)
        
        # Scale spread based on market conditions
        spread = spread * mid_price
        
        return spread
    
    def calculate_quote_prices(self, mid_price):
        """Calculate optimal bid and ask prices"""
        reservation_price = self.calculate_reservation_price(mid_price)
        spread = self.calculate_optimal_spread(mid_price)
        
        # Calculate bid and ask around reservation price
        bid_price = reservation_price - spread/2
        ask_price = reservation_price + spread/2
        
        # Ensure quotes are reasonable relative to mid price
        max_spread_pct = 0.01  # Maximum 1% spread
        max_spread = mid_price * max_spread_pct
        
        if ask_price - bid_price > max_spread:
            half_max_spread = max_spread / 2
            bid_price = mid_price - half_max_spread
            ask_price = mid_price + half_max_spread
        
        return bid_price, ask_price
    
    def calculate_position_size(self, price):
        """Calculate position size based on minimum order value and risk limits"""
        base_size = min_order_value / price
        
        # Adjust size based on current inventory to mean-revert
        global inventory
        inventory_adjustment = 1.0
        if abs(inventory * price) > max_inventory * 0.5:
            inventory_adjustment = 0.5  # Reduce size when inventory is high
        
        size = base_size * inventory_adjustment
        return round(size, 4)
    
    def cancel_existing_orders(self):
        """Cancel existing orders"""
        try:
            open_orders = exchange.fetch_open_orders(symbol)
            for order in open_orders:
                exchange.cancel_order(order['id'], symbol)
                print(f"Cancelled order {order['id']}")
        except Exception as e:
            print(f"Error cancelling orders: {e}")
    
    def place_quotes(self, bid_price, ask_price, size):
        """Place bid and ask orders"""
        self.cancel_existing_orders()
        
        bid_order = None
        ask_order = None
        
        try:
            # Place bid order
            bid_order = exchange.create_limit_order(symbol, 'buy', size, bid_price)
            if bid_order:
                print(f"✅ Bid placed: {size} XRP @ ${bid_price:.4f}")
                self.current_orders['bid'] = bid_order
        except Exception as e:
            print(f"Error placing bid: {e}")
        
        try:
            # Place ask order  
            ask_order = exchange.create_limit_order(symbol, 'sell', size, ask_price)
            if ask_order:
                print(f"✅ Ask placed: {size} XRP @ ${ask_price:.4f}")
                self.current_orders['ask'] = ask_order
        except Exception as e:
            print(f"Error placing ask: {e}")
        
        return bid_order, ask_order
    
    def update_inventory(self):
        """Update inventory based on recent trades"""
        global inventory
        try:
            recent_trades = exchange.fetch_my_trades(symbol, limit=10)
            for trade in recent_trades:
                if trade['timestamp'] > (time.time() - 60) * 1000:  # Last minute
                    if trade['side'] == 'buy':
                        inventory += trade['amount']
                    else:
                        inventory -= trade['amount']
                    
                    self.trades_count += 1
                    self.pnl += trade['fee']  # Track fees as cost
                    print(f"Trade executed: {trade['side']} {trade['amount']} @ ${trade['price']:.4f}")
        except Exception as e:
            print(f"Error updating inventory: {e}")
    
    def run_strategy(self):
        """Main strategy loop"""
        global last_mid_price, inventory
        
        print("🚀 Starting Avellaneda-Stoikov High-Frequency Market Maker for XRP")
        print(f"Risk aversion (γ): {gamma}")
        print(f"Market impact (k): {k}")
        print(f"Update frequency: {update_frequency}s")
        
        # Set leverage
        try:
            exchange.set_leverage(leverage, symbol)
            print(f"Leverage set to {leverage}x for {symbol}")
        except Exception as e:
            print(f"Error setting leverage: {e}")
        
        while True:
            try:
                start_time = time.time()
                
                # Fetch market data
                orderbook = exchange.fetch_order_book(symbol)
                if not orderbook or not orderbook['bids'] or not orderbook['asks']:
                    print("No orderbook data, retrying...")
                    time.sleep(1)
                    continue
                
                # Calculate mid price
                best_bid = orderbook['bids'][0][0]
                best_ask = orderbook['asks'][0][0]
                mid_price = (best_bid + best_ask) / 2
                
                # Update price history for volatility calculation
                price_history.append(mid_price)
                last_mid_price = mid_price
                
                # Update inventory from recent trades
                self.update_inventory()
                
                # Calculate optimal quotes
                bid_price, ask_price = self.calculate_quote_prices(mid_price)
                size = self.calculate_position_size(mid_price)
                
                # Calculate metrics
                sigma = self.calculate_volatility()
                spread = ask_price - bid_price
                spread_bps = (spread / mid_price) * 10000
                
                # Display status
                print(f"\n{'='*60}")
                print(f"XRP Mid: ${mid_price:.4f} | Spread: {spread_bps:.1f}bps | Vol: {sigma:.3f}")
                print(f"Inventory: {inventory:.4f} XRP (${inventory * mid_price:.2f})")
                print(f"Bid: ${bid_price:.4f} | Ask: ${ask_price:.4f} | Size: {size:.4f}")
                print(f"Trades: {self.trades_count} | PnL: ${self.pnl:.2f}")
                
                # Check account balance
                try:
                    balance = exchange.fetch_balance()
                    print(f"Available: ${balance['USDC']['free']:.2f} USDC")
                except Exception as e:
                    print(f"Balance check error: {e}")
                
                # Place quotes
                self.place_quotes(bid_price, ask_price, size)
                
                # High-frequency timing
                elapsed = time.time() - start_time
                sleep_time = max(0, update_frequency - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping market maker...")
                self.cancel_existing_orders()
                break
            except Exception as e:
                print(f"Strategy error: {e}")
                time.sleep(1)

# Run the market maker
if __name__ == "__main__":
    try:
        mm = AvellanedaStoikovMM()
        mm.run_strategy()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"🚨 Fatal error: {e}")
