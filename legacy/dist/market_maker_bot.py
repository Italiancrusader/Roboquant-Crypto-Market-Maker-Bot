#!/usr/bin/env python3
"""
Universal Market Making Bot - Roboquant
© 2025 Roboquant - Professional Cryptocurrency Trading Solutions
Supports multiple exchanges through CCXT
Website: https://roboquant.ai
"""

import ccxt
import time
import math
import json
import os
import sys
from datetime import datetime
from collections import deque
import statistics
import logging
from typing import Dict, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniversalMarketMaker:
    """Universal market maker supporting multiple exchanges"""
    
    SUPPORTED_EXCHANGES = {
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
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize the market maker with configuration"""
        self.config = self.load_config(config_path)
        self.exchange = None
        self.symbol = None
        self.price_history = deque(maxlen=self.config['strategy']['sigma_lookback'])
        self.inventory = 0
        self.pnl = 0
        self.trades_count = 0
        self.current_orders = {'bid': None, 'ask': None}
        self.volatility = 0.01
        self.running = False
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def initialize_exchange(self) -> None:
        """Initialize the exchange connection"""
        exchange_name = self.config['exchange']['name'].lower()
        
        if exchange_name not in self.SUPPORTED_EXCHANGES:
            raise ValueError(f"Exchange {exchange_name} not supported. Supported exchanges: {list(self.SUPPORTED_EXCHANGES.keys())}")
        
        exchange_class = self.SUPPORTED_EXCHANGES[exchange_name]
        
        # Build exchange config
        exchange_config = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'  # For perpetual contracts
            }
        }
        
        # Add API credentials if provided
        if self.config['exchange'].get('api_key'):
            exchange_config['apiKey'] = self.config['exchange']['api_key']
            exchange_config['secret'] = self.config['exchange']['api_secret']
        
        # Add special parameters for specific exchanges
        if exchange_name == 'hyperliquid':
            if self.config['exchange'].get('private_key'):
                exchange_config['privateKey'] = self.config['exchange']['private_key']
                exchange_config['walletAddress'] = self.config['exchange']['wallet_address']
        
        # Testnet/Sandbox mode
        if self.config['exchange'].get('testnet', False):
            exchange_config['sandbox'] = True
        
        # Initialize exchange
        self.exchange = exchange_class(exchange_config)
        
        # Load markets
        try:
            self.exchange.load_markets()
            logger.info(f"Successfully connected to {exchange_name}")
        except Exception as e:
            logger.error(f"Failed to connect to exchange: {e}")
            raise
    
    def validate_symbol(self) -> None:
        """Validate and set the trading symbol"""
        self.symbol = self.config['trading']['symbol']
        
        if self.symbol not in self.exchange.markets:
            available_symbols = [s for s in self.exchange.markets.keys() if 'USDT' in s or 'USD' in s]
            logger.error(f"Symbol {self.symbol} not found. Available symbols: {available_symbols[:10]}...")
            raise ValueError(f"Invalid symbol: {self.symbol}")
        
        market = self.exchange.markets[self.symbol]
        logger.info(f"Trading symbol: {self.symbol}")
        logger.info(f"Min order size: {market['limits']['amount']['min']}")
        logger.info(f"Price precision: {market['precision']['price']}")
    
    def set_leverage(self) -> None:
        """Set leverage for the trading pair"""
        leverage = self.config['trading'].get('leverage', 1)
        
        try:
            if hasattr(self.exchange, 'set_leverage'):
                self.exchange.set_leverage(leverage, self.symbol)
                logger.info(f"Leverage set to {leverage}x")
        except Exception as e:
            logger.warning(f"Could not set leverage: {e}")
    
    def calculate_volatility(self) -> float:
        """Calculate realized volatility from price history"""
        if len(self.price_history) < 2:
            return self.volatility
        
        returns = []
        for i in range(1, len(self.price_history)):
            ret = math.log(self.price_history[i] / self.price_history[i-1])
            returns.append(ret)
        
        if len(returns) > 1:
            self.volatility = statistics.stdev(returns) * math.sqrt(3600)
            self.volatility = max(self.volatility, 0.001)
        
        return self.volatility
    
    def calculate_reservation_price(self, mid_price: float) -> float:
        """Calculate reservation price based on inventory"""
        gamma = self.config['strategy']['gamma']
        T = self.config['strategy']['time_horizon']
        
        sigma = self.calculate_volatility()
        time_remaining = T - (time.time() % 3600) / 3600
        time_remaining = max(time_remaining, 0.01)
        
        reservation_price = mid_price - (self.inventory * gamma * sigma**2 * time_remaining)
        return reservation_price
    
    def calculate_optimal_spread(self, mid_price: float) -> float:
        """Calculate optimal bid-ask spread"""
        gamma = self.config['strategy']['gamma']
        k = self.config['strategy']['k']
        T = self.config['strategy']['time_horizon']
        
        sigma = self.calculate_volatility()
        time_remaining = T - (time.time() % 3600) / 3600
        time_remaining = max(time_remaining, 0.01)
        
        spread = gamma * sigma**2 * time_remaining + (2/gamma) * math.log(1 + gamma/k)
        
        min_spread = self.config['strategy']['min_spread']
        spread = max(spread, min_spread)
        spread = spread * mid_price
        
        max_spread = mid_price * self.config['strategy']['max_spread_percent']
        spread = min(spread, max_spread)
        
        return spread
    
    def calculate_quote_prices(self, mid_price: float) -> Tuple[float, float]:
        """Calculate optimal bid and ask prices"""
        reservation_price = self.calculate_reservation_price(mid_price)
        spread = self.calculate_optimal_spread(mid_price)
        
        bid_price = reservation_price - spread/2
        ask_price = reservation_price + spread/2
        
        # Ensure quotes don't cross the market
        max_bid_distance = self.config['strategy']['max_quote_distance_percent']
        bid_price = min(bid_price, mid_price * (1 - max_bid_distance))
        ask_price = max(ask_price, mid_price * (1 + max_bid_distance))
        
        # Round to exchange precision
        market = self.exchange.markets[self.symbol]
        price_precision = market['precision']['price']
        
        if isinstance(price_precision, int):
            bid_price = round(bid_price, price_precision)
            ask_price = round(ask_price, price_precision)
        else:
            # Handle tick size
            tick_size = float(price_precision)
            bid_price = round(bid_price / tick_size) * tick_size
            ask_price = round(ask_price / tick_size) * tick_size
        
        return bid_price, ask_price
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on configuration"""
        market = self.exchange.markets[self.symbol]
        min_size = market['limits']['amount']['min']
        
        # Base size from config
        if self.config['trading']['order_size_type'] == 'fixed':
            base_size = self.config['trading']['order_size']
        else:  # percentage of balance
            balance = self.get_available_balance()
            percentage = self.config['trading']['order_size_percent']
            base_size = (balance * percentage) / price
        
        # Inventory adjustment
        max_inventory = self.config['risk']['max_inventory_usd']
        inventory_value = abs(self.inventory * price)
        
        if inventory_value > max_inventory * 0.7:
            size_multiplier = 0.5
        elif inventory_value > max_inventory * 0.5:
            size_multiplier = 0.75
        else:
            size_multiplier = 1.0
        
        size = base_size * size_multiplier
        
        # Round to exchange precision
        amount_precision = market['precision']['amount']
        if isinstance(amount_precision, int):
            size = round(size, amount_precision)
        else:
            # Handle lot size
            lot_size = float(amount_precision)
            size = round(size / lot_size) * lot_size
        
        return max(size, min_size)
    
    def get_available_balance(self) -> float:
        """Get available balance in quote currency"""
        try:
            balance = self.exchange.fetch_balance()
            quote_currency = self.symbol.split('/')[1].split(':')[0]
            return balance.get(quote_currency, {}).get('free', 0)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0
    
    def cancel_all_orders(self) -> None:
        """Cancel all open orders"""
        try:
            if hasattr(self.exchange, 'cancel_all_orders'):
                self.exchange.cancel_all_orders(self.symbol)
            else:
                open_orders = self.exchange.fetch_open_orders(self.symbol)
                for order in open_orders:
                    self.exchange.cancel_order(order['id'], self.symbol)
            logger.info("All orders cancelled")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def place_orders(self, bid_price: float, ask_price: float, size: float) -> None:
        """Place bid and ask orders"""
        self.cancel_all_orders()
        
        try:
            # Place bid order
            bid_order = self.exchange.create_limit_order(
                self.symbol, 'buy', size, bid_price
            )
            self.current_orders['bid'] = bid_order
            logger.info(f"Bid placed: {size} @ {bid_price}")
        except Exception as e:
            logger.error(f"Error placing bid: {e}")
        
        try:
            # Place ask order
            ask_order = self.exchange.create_limit_order(
                self.symbol, 'sell', size, ask_price
            )
            self.current_orders['ask'] = ask_order
            logger.info(f"Ask placed: {size} @ {ask_price}")
        except Exception as e:
            logger.error(f"Error placing ask: {e}")
    
    def update_inventory(self) -> None:
        """Update inventory from recent trades"""
        try:
            since = int((time.time() - 300) * 1000)  # Last 5 minutes
            trades = self.exchange.fetch_my_trades(self.symbol, since=since, limit=50)
            
            for trade in trades:
                if trade['timestamp'] > since:
                    if trade['side'] == 'buy':
                        self.inventory += trade['amount']
                    else:
                        self.inventory -= trade['amount']
                    
                    self.trades_count += 1
                    
                    # Update PnL
                    fee = trade.get('fee', {}).get('cost', 0)
                    self.pnl -= fee
                    
                    logger.info(f"Trade: {trade['side']} {trade['amount']} @ {trade['price']}")
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
    
    def display_status(self, mid_price: float, bid_price: float, ask_price: float, size: float) -> None:
        """Display current bot status"""
        spread = ask_price - bid_price
        spread_bps = (spread / mid_price) * 10000
        balance = self.get_available_balance()
        
        print(f"\n{'='*60}")
        print(f"Exchange: {self.config['exchange']['name']} | Symbol: {self.symbol}")
        print(f"Mid Price: ${mid_price:.4f} | Spread: {spread_bps:.1f}bps")
        print(f"Volatility: {self.volatility:.3f} | Inventory: {self.inventory:.4f}")
        print(f"Bid: ${bid_price:.4f} | Ask: ${ask_price:.4f} | Size: {size:.4f}")
        print(f"Trades: {self.trades_count} | PnL: ${self.pnl:.2f}")
        print(f"Balance: ${balance:.2f}")
    
    def run(self) -> None:
        """Main bot loop"""
        logger.info("Starting Universal Market Maker Bot")
        
        # Initialize exchange
        self.initialize_exchange()
        self.validate_symbol()
        self.set_leverage()
        
        self.running = True
        update_frequency = self.config['strategy']['update_frequency']
        
        logger.info(f"Bot started - Update frequency: {update_frequency}s")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Fetch orderbook
                orderbook = self.exchange.fetch_order_book(self.symbol)
                if not orderbook['bids'] or not orderbook['asks']:
                    logger.warning("Empty orderbook, retrying...")
                    time.sleep(1)
                    continue
                
                # Calculate mid price
                best_bid = orderbook['bids'][0][0]
                best_ask = orderbook['asks'][0][0]
                mid_price = (best_bid + best_ask) / 2
                
                # Update price history
                self.price_history.append(mid_price)
                
                # Update inventory
                self.update_inventory()
                
                # Check risk limits
                inventory_value = abs(self.inventory * mid_price)
                max_inventory = self.config['risk']['max_inventory_usd']
                
                if inventory_value > max_inventory:
                    logger.warning(f"Inventory limit reached: ${inventory_value:.2f} > ${max_inventory}")
                    self.cancel_all_orders()
                    time.sleep(10)
                    continue
                
                # Calculate quotes
                bid_price, ask_price = self.calculate_quote_prices(mid_price)
                size = self.calculate_position_size(mid_price)
                
                # Display status
                self.display_status(mid_price, bid_price, ask_price, size)
                
                # Place orders
                self.place_orders(bid_price, ask_price, size)
                
                # Sleep until next update
                elapsed = time.time() - start_time
                sleep_time = max(0, update_frequency - elapsed)
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)
        
        # Cleanup
        self.cancel_all_orders()
        logger.info("Bot stopped")
    
    def stop(self) -> None:
        """Stop the bot"""
        self.running = False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Market Making Bot')
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Please copy config.example.json to config.json and update with your settings")
        sys.exit(1)
    
    # Create and run bot
    bot = UniversalMarketMaker(args.config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
