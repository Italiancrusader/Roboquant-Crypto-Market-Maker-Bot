import ccxt

exchange = ccxt.hyperliquid({'enableRateLimit': True})
markets = exchange.load_markets()
eth_market = markets['ETH/USDC:USDC']

print('ETH Market Info:')
print(f'Min Amount: {eth_market["limits"]["amount"]["min"]}')
print(f'Amount Step: {eth_market["precision"]["amount"]}')
print(f'Price Step: {eth_market["precision"]["price"]}')
print(f'Market Info: {eth_market["info"]}')
