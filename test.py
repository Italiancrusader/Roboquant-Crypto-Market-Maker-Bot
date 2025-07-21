import ccxt
import hyperliquid_exchange  # your custom file

exchange = hyperliquid_exchange.hyperliquid({
    'apiKey': 'YOUR_KEY',
    'secret': 'YOUR_SECRET',
    # possibly more config
})

# Then you can do:
bars = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
print(bars)
