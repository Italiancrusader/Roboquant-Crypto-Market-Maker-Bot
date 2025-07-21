# Universal Market Making Bot

A professional cryptocurrency market making bot that supports multiple exchanges and uses the Avellaneda-Stoikov strategy for optimal quote placement.

## 🚀 Quick Start Guide

### Supported Exchanges
- Binance
- Bybit
- OKX
- KuCoin
- Gate.io
- MEXC
- Bitget
- Hyperliquid
- Phemex
- Huobi
- Kraken

### Prerequisites
- Python 3.8 or higher
- API keys from your chosen exchange
- Some USDT/USD in your exchange account

## 📦 Installation

### Option 1: Local Installation

1. **Install Python** (if not already installed)
   - Windows: Download from [python.org](https://python.org)
   - Mac: `brew install python3`
   - Linux: `sudo apt install python3 python3-pip`

2. **Install the bot**
   ```bash
   # Extract the bot files to a folder
   cd market-maker-bot
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Copy `config.example.json` to `config.json`
   - Edit `config.json` with your settings (see Configuration section)

4. **Run the bot**
   ```bash
   python market_maker_bot.py
   ```

### Option 2: AWS/Cloud Server Installation

1. **Launch an EC2 instance** (or any VPS)
   - Recommended: t3.micro or t3.small
   - OS: Amazon Linux 2023, Ubuntu 20.04/22.04, or similar

2. **Connect to your server**
   
   For Amazon Linux:
   ```bash
   ssh -i your-key.pem ec2-user@your-server-ip
   ```
   
   For Ubuntu:
   ```bash
   ssh -i your-key.pem ubuntu@your-server-ip
   ```

3. **Install Python and dependencies**
   
   For Amazon Linux 2023:
   ```bash
   # Update system
   sudo yum update -y
   
   # Install Python 3 and development tools
   sudo yum install python3 python3-pip python3-devel gcc -y
   
   # Install screen for background processes
   sudo yum install screen -y
   ```
   
   For Ubuntu:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip screen -y
   ```

4. **Upload and setup the bot**
   
   Option A - Using SCP from your local machine:
   ```bash
   # From your local machine (not on the server)
   scp -i your-key.pem -r dist/* ec2-user@your-server-ip:~/
   ```
   
   Option B - Using wget/curl on the server:
   ```bash
   # On the server
   mkdir market-maker-bot
   cd market-maker-bot
   
   # Download files (if hosted somewhere)
   # Or use SFTP client like FileZilla
   ```

5. **Install Python dependencies**
   ```bash
   cd market-maker-bot
   
   # Create virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate
   
   # Install requirements
   pip3 install -r requirements.txt
   ```

6. **Configure the bot**
   ```bash
   # Run the configuration wizard
   python3 config_wizard.py
   
   # Or copy and edit the example config
   cp config.example.json config.json
   nano config.json  # or vim config.json
   ```

7. **Run the bot in background**
   ```bash
   # Using screen (recommended)
   screen -S marketmaker
   python3 market_maker_bot.py
   
   # Detach with Ctrl+A then D
   # Reattach with: screen -r marketmaker
   
   # Alternative: Using nohup
   nohup python3 market_maker_bot.py > bot.log 2>&1 &
   ```

8. **Set up auto-start (optional)**
   
   For Amazon Linux with systemd:
   ```bash
   sudo nano /etc/systemd/system/marketmaker.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Market Making Bot
   After=network.target
   
   [Service]
   Type=simple
   User=ec2-user
   WorkingDirectory=/home/ec2-user/market-maker-bot
   Environment="PATH=/home/ec2-user/market-maker-bot/venv/bin"
   ExecStart=/home/ec2-user/market-maker-bot/venv/bin/python /home/ec2-user/market-maker-bot/market_maker_bot.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Then enable:
   ```bash
   sudo systemctl enable marketmaker
   sudo systemctl start marketmaker
   sudo systemctl status marketmaker
   ```

## ⚙️ Configuration

Edit `config.json` with your settings:

### Exchange Settings
```json
"exchange": {
  "name": "bybit",              // Your exchange
  "api_key": "your-api-key",    // Your API key
  "api_secret": "your-secret",  // Your API secret
  "testnet": false              // Use testnet for testing
}
```

### Trading Settings
```json
"trading": {
  "symbol": "ETH/USDT:USDT",    // Trading pair
  "leverage": 5,                 // Leverage (1-20)
  "order_size_type": "percentage",
  "order_size_percent": 0.01     // 1% of balance per order
}
```

### Strategy Parameters

#### Conservative Settings (Recommended for beginners)
```json
"strategy": {
  "gamma": 0.5,                  // High risk aversion
  "k": 1.0,                      // Normal market impact
  "update_frequency": 5,         // Update every 5 seconds
  "max_spread_percent": 0.005    // 0.5% max spread
}
```

#### Balanced Settings
```json
"strategy": {
  "gamma": 0.1,                  // Moderate risk
  "k": 1.5,                      // Moderate market impact
  "update_frequency": 2,         // Update every 2 seconds
  "max_spread_percent": 0.003    // 0.3% max spread
}
```

#### Aggressive Settings (Experienced users only)
```json
"strategy": {
  "gamma": 0.01,                 // Low risk aversion
  "k": 3.0,                      // High market impact
  "update_frequency": 0.5,       // Update every 0.5 seconds
  "max_spread_percent": 0.002    // 0.2% max spread
}
```

### Risk Management
```json
"risk": {
  "max_inventory_usd": 1000,     // Max position size
  "stop_loss_percent": 0.05,     // 5% stop loss
  "daily_loss_limit_usd": 50     // Stop if lose $50/day
}
```

## 🔑 Getting Exchange API Keys

### Binance
1. Log in to Binance
2. Go to Account → API Management
3. Create new API
4. Enable "Enable Futures" permission
5. Save your API key and secret

### Bybit
1. Log in to Bybit
2. Go to Account & Security → API
3. Create new key
4. Select "Derivatives API v3"
5. Enable "Orders" and "Positions" permissions

### Other Exchanges
Similar process - create API key with trading permissions for futures/derivatives.

## 📊 Understanding the Display

```
============================================================
Exchange: Bybit | Symbol: ETH/USDT:USDT
Mid Price: $3245.50 | Spread: 3.2bps
Volatility: 0.015 | Inventory: 0.5 ETH
Bid: $3244.00 | Ask: $3247.00 | Size: 0.01
Trades: 42 | PnL: $12.50
Balance: $1000.00 USDT
```

- **Mid Price**: Current market price
- **Spread**: Your bid-ask spread in basis points
- **Volatility**: Market volatility (higher = wider spreads)
- **Inventory**: Your current position
- **Trades**: Number of completed trades
- **PnL**: Profit/Loss (negative = fees paid)

## 🛡️ Safety Features

1. **Inventory Limits**: Bot stops trading if position too large
2. **Stop Loss**: Automatic position closing on large losses
3. **Rate Limiting**: Prevents API bans
4. **Error Handling**: Continues running on temporary errors

## 🚨 Important Warnings

1. **Start Small**: Test with small amounts first
2. **Monitor Closely**: Check the bot regularly
3. **Understand Risks**: Market making can lose money
4. **Use Stop Loss**: Always set risk limits
5. **Test First**: Use testnet/paper trading initially

## 📈 Tips for Success

1. **Choose Liquid Pairs**: ETH, BTC have best liquidity
2. **Start Conservative**: Use high gamma (0.5+) initially
3. **Monitor Inventory**: Don't let positions get too large
4. **Watch Fees**: Ensure spreads cover exchange fees
5. **Adjust Parameters**: Tune based on market conditions

## 🔧 Troubleshooting

### "API key invalid"
- Check API key and secret are correct
- Ensure API has trading permissions
- Check if using correct network (mainnet vs testnet)

### "Insufficient balance"
- Add funds to your exchange account
- Reduce order_size_percent
- Check you have USDT/USD, not just crypto

### "Symbol not found"
- Check symbol format (e.g., "ETH/USDT:USDT" for Bybit)
- Ensure exchange supports this trading pair
- Try spot format if perpetual fails: "ETH/USDT"

### Bot stops immediately
- Check logs in `market_maker.log`
- Verify Python version: `python --version`
- Reinstall requirements: `pip install -r requirements.txt --upgrade`

## 📞 Support

For issues or questions:
1. Check the logs in `market_maker.log`
2. Review your configuration
3. Ensure exchange API is working
4. Try with smaller amounts or testnet first

## ⚖️ Disclaimer

This bot is provided as-is for educational purposes. Cryptocurrency trading carries significant risks. You can lose money. Always:
- Understand the strategy before using
- Start with small amounts
- Never invest more than you can afford to lose
- Monitor the bot regularly
- Have proper risk management

## 📝 License

MIT License - See LICENSE file for details
