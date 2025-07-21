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

### Option 2: AWS Amazon Linux - Complete Beginner Guide

**📚 For an even more detailed step-by-step guide with screenshots and troubleshooting, see [AWS_BEGINNER_GUIDE.md](AWS_BEGINNER_GUIDE.md)**

#### Step 1: Create an AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the signup process (you'll need a credit card)

#### Step 2: Launch Your Server (EC2 Instance)

1. **Login to AWS Console**
   - Go to [console.aws.amazon.com](https://console.aws.amazon.com)
   - Search for "EC2" in the search bar and click on it

2. **Click "Launch Instance"** (orange button)

3. **Configure your server:**
   - **Name**: Type "MarketMakerBot" (or any name you like)
   - **Application and OS Images**: 
     - Click on "Amazon Linux"
     - Select "Amazon Linux 2023 AMI" (should be selected by default)
   - **Instance type**: 
     - Select "t3.micro" (it's free tier eligible)
   - **Key pair**:
     - Click "Create new key pair"
     - Key pair name: "market-maker-key" (or any name)
     - Key pair type: RSA
     - Private key format: .pem
     - Click "Create key pair"
     - **IMPORTANT**: Save this file safely! You need it to connect to your server
   - **Network settings**:
     - Leave everything as default
   - Click **"Launch instance"** (orange button at bottom)

4. **Wait for your server to start**
   - Click "View all instances"
   - Wait until "Instance state" shows "Running" (about 1-2 minutes)
   - Note down your "Public IPv4 address" (looks like: 18.185.28.165)

#### Step 3: Connect to Your Server

**For Windows Users:**

1. **Download PuTTY**
   - Go to [putty.org](https://www.putty.org/download.html)
   - Download "putty.exe" and "puttygen.exe"

2. **Convert your key file**
   - Open PuTTYgen
   - Click "Load" and select your .pem file (the one you downloaded)
   - Click "Save private key" (ignore the warning)
   - Save it as "market-maker-key.ppk"

3. **Connect with PuTTY**
   - Open PuTTY
   - Host Name: `ec2-user@YOUR-IP-ADDRESS` (replace YOUR-IP-ADDRESS with your server's IP)
   - Port: 22
   - Connection type: SSH
   - In the left menu: Connection → SSH → Auth → Credentials
   - Browse and select your .ppk file
   - Click "Open"
   - Click "Accept" on the security alert

**For Mac/Linux Users:**

1. **Open Terminal**
   - Mac: Press Cmd+Space, type "Terminal", press Enter
   - Linux: Press Ctrl+Alt+T

2. **Set key permissions**
   ```bash
   chmod 400 ~/Downloads/market-maker-key.pem
   ```

3. **Connect to server**
   ```bash
   ssh -i ~/Downloads/market-maker-key.pem ec2-user@YOUR-IP-ADDRESS
   ```
   (Replace YOUR-IP-ADDRESS with your server's IP)

#### Step 4: Install the Bot

Once connected to your server, copy and paste these commands one by one:

1. **Update the system**
   ```bash
   sudo yum update -y
   ```
   (Wait for it to complete - about 1-2 minutes)

2. **Install required software**
   ```bash
   sudo yum install -y python3 python3-pip git screen
   ```

3. **Download the bot**
   ```bash
   git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
   cd Roboquant-Crypto-Market-Maker-Bot/dist
   ```

4. **Install Python packages**
   ```bash
   pip3 install -r requirements.txt
   ```
   (This will take 2-3 minutes)

#### Step 5: Configure the Bot

1. **Copy the example configuration**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit the configuration**
   ```bash
   nano config.json
   ```

3. **Update these settings:**
   - Change `"name": "bybit"` to your exchange (binance, bybit, okx, etc.)
   - Change `"api_key": "YOUR_API_KEY_HERE"` to your actual API key
   - Change `"api_secret": "YOUR_API_SECRET_HERE"` to your actual API secret
   - Change `"symbol": "ETH/USDT:USDT"` to your preferred trading pair
   
   **To edit in nano:**
   - Use arrow keys to move around
   - Delete text and type your changes
   - Press `Ctrl+O` then `Enter` to save
   - Press `Ctrl+X` to exit

#### Step 6: Run the Bot

1. **Start a screen session** (this keeps the bot running when you disconnect)
   ```bash
   screen -S marketmaker
   ```

2. **Run the bot**
   ```bash
   python3 market_maker_bot.py
   ```

3. **Detach from screen** (so bot keeps running)
   - Press `Ctrl+A` then press `D`
   - You'll see "[detached from ...]"

4. **Disconnect from server**
   ```bash
   exit
   ```

#### Step 7: Monitor Your Bot

To check on your bot later:

1. **Reconnect to your server** (same as Step 3)

2. **Reattach to the bot**
   ```bash
   screen -r marketmaker
   ```

3. **To stop the bot**
   - Press `Ctrl+C`

4. **To see the log file**
   ```bash
   cat market_maker.log
   ```

#### Important Tips for Beginners

1. **Start Small**: Test with $50-100 first
2. **Use Conservative Settings**: In config.json, set:
   ```json
   "gamma": 0.5,
   "leverage": 1,
   "order_size_percent": 0.005
   ```
3. **Monitor Regularly**: Check your bot every few hours initially
4. **Keep Your Keys Safe**: Never share your .pem file or API keys
5. **Stop Instance When Not Using**: In AWS Console, select your instance and click "Stop instance" to save money

#### Troubleshooting

**"Permission denied" when connecting:**
- Make sure you're using `ec2-user` as the username
- Check that your .pem file has correct permissions

**"Command not found":**
- Make sure you're in the right directory: `cd ~/Roboquant-Crypto-Market-Maker-Bot/dist`

**Bot won't start:**
- Check your config.json for typos
- Make sure your API keys are correct
- Ensure you have funds in your exchange account

**Need to edit config again:**
```bash
cd ~/Roboquant-Crypto-Market-Maker-Bot/dist
nano config.json
```

#### Getting Exchange API Keys

**For Binance:**
1. Login to Binance
2. Click profile icon → API Management
3. Create API → System generated
4. Enter a label like "MarketMaker"
5. Complete verification
6. Enable "Enable Futures" permission
7. Save your API Key and Secret

**For Bybit:**
1. Login to Bybit
2. Account & Security → API
3. Create New Key
4. Select "System-generated API Keys"
5. Enable "Derivatives API v3" permissions
6. Enable "Orders" and "Positions"
7. Save your API Key and Secret

#### Costs

- **AWS t3.micro**: ~$8/month (or free for 12 months with free tier)
- **To minimize costs**: Stop your instance when not trading
- **Monitor usage**: Check AWS billing dashboard regularly

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
