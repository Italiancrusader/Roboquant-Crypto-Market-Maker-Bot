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

# Initialize Bybit exchange via CCXT
exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'sandbox': False,  # Set to True for testnet
    'enableRateLimit': True,
})

# Avellaneda-Stoikov Parameters for Bybit ETH
symbol = "ETH/USDT:USDT"  # ETH perpetual contract on Bybit
leverage = 5  # 5x leverage

# Strategy Parameters - ULTRA AGGRESSIVE SETTINGS
gamma = 0.01  # Risk aversion parameter (ULTRA LOW = maximum aggression)
k = 5.0  # Market impact parameter (VERY HIGH = ultra tight spreads)
alpha = 0.001  # Inventory penalty parameter (ULTRA LOW = maximum aggression)
sigma_lookback = 20  # Number of price observations (VERY SHORT = ultra reactive)
T = 0.1  # Time horizon (6 minutes = ultra aggressive)
dt = 1/3600  # Time step (1 second in hours)

# High-frequency parameters - ULTRA AGGRESSIVE
update_frequency = 0.5  # Update quotes every 0.5 seconds (ULTRA AGGRESSIVE)
max_inventory_usd = 200  # Maximum inventory in USD value (VERY HIGH = ultra aggressive)
target_inventory = 0  # Target inventory (neutral)

# Data storage
price_history = deque(maxlen=sigma_lookback)
inventory = 0  # Current inventory in ETH
last_mid_price = 0
volatility = 0.01  # Initial volatility estimate
min_order_size = 0.001  # Minimum order size for ETH on Bybit

class BybitAvellanedaStoikovMM:
    def __init__(self):
        self.current_orders = {'bid': None, 'ask': None}
        self.last_quote_time = 0
        self.pnl = 0
        self.trades_count = 0
        self.min_order_size = 0.001  # Will be updated from market info
        
    def get_market_info(self):
        """Get market information and minimum order size"""
        try:
            markets = exchange.load_markets()
            market = markets[symbol]
            self.min_order_size = market['limits']['amount']['min'] or 0.001
            print(f"Market info loaded - Min order size: {self.min_order_size} ETH")
            return market
        except Exception as e:
            print(f"Error loading market info: {e}")
            return None
        
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
        
        # Time remaining in current hour
        time_remaining = T - (time.time() % 3600) / 3600
        time_remaining = max(time_remaining, 0.01)  # Minimum time remaining
        
        # Reservation price adjustment for inventory risk
        reservation_price = mid_price - (q * gamma * sigma**2 * time_remaining)
        return reservation_price
    
    def calculate_optimal_spread(self, mid_price):
        """Calculate optimal bid-ask spread using Avellaneda-Stoikov formula"""
        sigma = self.calculate_volatility()
        
        # Time remaining in current hour
        time_remaining = T - (time.time() % 3600) / 3600
        time_remaining = max(time_remaining, 0.01)  # Minimum time remaining
        
        # Optimal spread calculation
        spread = gamma * sigma**2 * time_remaining + (2/gamma) * math.log(1 + gamma/k)
        
        # Ensure minimum spread for profitability
        min_spread = 0.0001  # Minimum spread
        spread = max(spread, min_spread)
        
        # Scale spread based on market conditions
        spread = spread * mid_price
        
        # Ensure reasonable maximum spread - ULTRA AGGRESSIVE
        max_spread = mid_price * 0.002  # Maximum 0.2% spread (ULTRA TIGHT)
        spread = min(spread, max_spread)
        
        return spread
    
    def calculate_quote_prices(self, mid_price):
        """Calculate optimal bid and ask prices"""
        reservation_price = self.calculate_reservation_price(mid_price)
        spread = self.calculate_optimal_spread(mid_price)
        
        # Calculate bid and ask around reservation price
        bid_price = reservation_price - spread/2
        ask_price = reservation_price + spread/2
        
        # Ensure quotes don't cross the market - ULTRA AGGRESSIVE
        bid_price = min(bid_price, mid_price * 0.9995)  # Even closer to mid
        ask_price = max(ask_price, mid_price * 1.0005)  # Even closer to mid
        
        return bid_price, ask_price
    
    def calculate_position_size(self, price):
        """Calculate position size based on minimum order size and risk limits"""
        # Use minimum order size as base
        base_size = max(self.min_order_size, 0.001)
        
        # Adjust size based on current inventory to mean-revert
        global inventory
        inventory_adjustment = 1.0
        
        inventory_value = abs(inventory * price)
        if inventory_value > max_inventory_usd * 0.5:
            inventory_adjustment = 0.5  # Reduce size when inventory is high
        
        size = base_size * inventory_adjustment
        
        # Round to appropriate precision
        size = round(size, 3)
        
        return max(size, self.min_order_size)
    
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
        # Cancel existing orders first
        self.cancel_existing_orders()
        
        bid_order = None
        ask_order = None
        
        try:
            # Place bid order with Bybit-specific parameters
            bid_order = exchange.create_limit_order(
                symbol, 'buy', size, bid_price,
                params={'positionIdx': 0}  # One-way mode
            )
            if bid_order:
                print(f"✅ Bid placed: {size} ETH @ ${bid_price:.2f}")
                self.current_orders['bid'] = bid_order
        except Exception as e:
            print(f"Error placing bid: {e}")
        
        try:
            # Place ask order with Bybit-specific parameters
            ask_order = exchange.create_limit_order(
                symbol, 'sell', size, ask_price,
                params={'positionIdx': 0}  # One-way mode
            )
            if ask_order:
                print(f"✅ Ask placed: {size} ETH @ ${ask_price:.2f}")
                self.current_orders['ask'] = ask_order
        except Exception as e:
            print(f"Error placing ask: {e}")
        
        return bid_order, ask_order
    
    def update_inventory(self):
        """Update inventory based on recent trades"""
        global inventory
        try:
            recent_trades = exchange.fetch_my_trades(symbol, limit=20)
            for trade in recent_trades:
                # Only count trades from the last 5 minutes
                if trade['timestamp'] > (time.time() - 300) * 1000:
                    if trade['side'] == 'buy':
                        inventory += trade['amount']
                    else:
                        inventory -= trade['amount']
                    
                    self.trades_count += 1
                    fee_cost = trade.get('fee', {}).get('cost', 0)
                    self.pnl -= fee_cost  # Subtract fees from PnL
                    print(f"Trade executed: {trade['side']} {trade['amount']} @ ${trade['price']:.2f}")
        except Exception as e:
            print(f"Error updating inventory: {e}")
    
    def get_account_balance(self):
        """Get account balance"""
        try:
            # Fetch balance with derivatives account type
            balance = exchange.fetch_balance(params={'type': 'swap'})
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            # If swap balance is 0, try unified account
            if usdt_balance == 0:
                balance = exchange.fetch_balance(params={'type': 'unified'})
                usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            # If still 0, try default balance
            if usdt_balance == 0:
                balance = exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                
            return usdt_balance
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0
    
    def set_position_mode(self):
        """Set position mode to one-way mode"""
        try:
            # Set position mode to one-way (0) instead of hedge mode
            response = exchange.set_position_mode(False, symbol)  # False = one-way mode
            print("Position mode set to one-way")
            return True
        except Exception as e:
            print(f"Error setting position mode: {e}")
            return False
    
    def run_strategy(self):
        """Main strategy loop"""
        global last_mid_price, inventory
        
        print("🚀 Starting Avellaneda-Stoikov High-Frequency Market Maker for ETH on Bybit")
        print(f"Risk aversion (γ): {gamma}")
        print(f"Market impact (k): {k}")
        print(f"Update frequency: {update_frequency}s")
        
        # Get market info
        market_info = self.get_market_info()
        if not market_info:
            print("Failed to load market info, using defaults")
        
        # Set position mode to one-way
        self.set_position_mode()
        
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
                    time.sleep(2)
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
                
                # Get account balance
                balance = self.get_account_balance()
                
                # Display status
                print(f"\n{'='*70}")
                print(f"ETH Mid: ${mid_price:.2f} | Spread: {spread_bps:.1f}bps | Vol: {sigma:.3f}")
                print(f"Inventory: {inventory:.3f} ETH (${inventory * mid_price:.2f})")
                print(f"Bid: ${bid_price:.2f} | Ask: ${ask_price:.2f} | Size: {size:.3f}")
                print(f"Trades: {self.trades_count} | PnL: ${self.pnl:.2f}")
                print(f"Balance: ${balance:.2f} USDT")
                
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
                time.sleep(2)

# Run the market maker
if __name__ == "__main__":
    try:
        mm = BybitAvellanedaStoikovMM()
        mm.run_strategy()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"🚨 Fatal error: {e}")
