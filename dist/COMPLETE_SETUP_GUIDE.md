Roboquant Universal Market Making Bot - Complete Setup Guide

Copyright 2025 Roboquant - Professional Cryptocurrency Trading Solutions
Website: roboquant.ai

This guide covers all installation methods: Windows, Mac, Linux, and AWS cloud servers.

Table of Contents

1. Prerequisites
2. Supported Exchanges
3. Local Installation
   - Windows Setup
   - Mac Setup
   - Linux Setup
4. AWS Cloud Installation
   - Creating AWS Account
   - Launching EC2 Instance
   - Connecting to Your Server
   - Installing the Bot on AWS
5. Configuration
   - Getting API Keys
   - Configuring the Bot
   - Strategy Settings
6. Running the Bot
7. Monitoring and Management
8. Troubleshooting
9. Safety Guidelines

Prerequisites

- Python 3.8 or higher
- Exchange account with API access
- Some USDT/USD in your exchange account
- Basic computer skills (ability to use command line)

Supported Exchanges

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

Local Installation

Windows Setup

Step 1: Install Python
1. Download Python from python.org/downloads/
2. Run the installer
3. IMPORTANT: Check "Add Python to PATH" during installation
4. Click "Install Now"

Step 2: Download the Bot
1. Go to https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot
2. Click the green "Code" button then "Download ZIP"
3. Extract the ZIP file to a folder (e.g., C:\TradingBot)
4. Navigate to the dist folder

Step 3: Install Dependencies
1. Open Command Prompt (Win+R, type cmd, press Enter)
2. Navigate to the bot folder:
   cd C:\TradingBot\dist
3. Install requirements:
   pip install -r requirements.txt

Step 4: Configure and Run
1. Double-click configure_bot.bat to open the configuration wizard
2. Or copy config.example.json to config.json and edit manually
3. Double-click start_bot.bat to run the bot

Mac Setup

Step 1: Install Python (if needed)
1. Open Terminal (Cmd+Space, type "Terminal")
2. Check if Python is installed:
   python3 --version
3. If not installed, install via Homebrew:
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install python3

Step 2: Download the Bot
1. Clone the repository:
   git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
   cd Roboquant-Crypto-Market-Maker-Bot/dist
2. Or download ZIP from GitHub and extract

Step 3: Install Dependencies
pip3 install -r requirements.txt

Step 4: Configure and Run
1. Copy example config:
   cp config.example.json config.json
2. Edit config:
   nano config.json
3. Run the bot:
   python3 market_maker_bot.py

Linux Setup

Step 1: Install Python and Git
Ubuntu/Debian:
sudo apt update
sudo apt install python3 python3-pip git

Fedora/RHEL:
sudo dnf install python3 python3-pip git

Step 2: Download the Bot
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot/dist

Step 3: Install Dependencies
pip3 install -r requirements.txt

Step 4: Configure and Run
cp config.example.json config.json
nano config.json
python3 market_maker_bot.py

AWS Cloud Installation

Creating AWS Account

1. Go to aws.amazon.com
2. Click "Create an AWS Account"
3. Enter email and password
4. Choose "Personal" account type
5. Enter payment information (required, but free tier available)
6. Verify phone number
7. Select "Basic support - Free"

Note: AWS offers 12 months of free tier for new accounts, including 750 hours/month of t3.micro instances.

Launching EC2 Instance

1. Login to AWS Console
   - Go to console.aws.amazon.com
   - Search for "EC2" and click it

2. Launch Instance
   - Click orange "Launch instance" button
   - Name: MarketMakerBot
   - OS: Select "Amazon Linux 2023 AMI"
   - Instance type: t3.micro (free tier eligible)
   - Key pair: 
     - Click "Create new key pair"
     - Name: market-maker-key
     - Type: RSA
     - Format: .pem
     - SAVE THE DOWNLOADED FILE SAFELY!
   - Leave other settings as default
   - Click "Launch instance"

3. Wait for Instance
   - Click "View all instances"
   - Wait for "Running" status
   - Note your Public IPv4 address

Connecting to Your Server

Windows (Using PuTTY)

1. Download PuTTY
   - Go to putty.org/download.html
   - Download and install PuTTY

2. Convert Key
   - Open PuTTYgen
   - Click "Load" then Select your .pem file
   - Click "Save private key" then Save as .ppk

3. Connect
   - Open PuTTY
   - Host: ec2-user@YOUR-IP-ADDRESS
   - Port: 22
   - Connection SSH Auth Browse Select .ppk file
   - Click "Open"

Mac/Linux

1. Set Key Permissions
   chmod 400 ~/Downloads/market-maker-key.pem

2. Connect
   ssh -i ~/Downloads/market-maker-key.pem ec2-user@YOUR-IP-ADDRESS

Installing the Bot on AWS

Once connected to your EC2 instance:

1. Update System and Install Requirements
   sudo yum update -y
   sudo yum install -y python3 python3-pip git screen

2. Clone the Repository
   git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
   cd Roboquant-Crypto-Market-Maker-Bot/dist

3. Install Python Dependencies
   pip3 install -r requirements.txt

4. Configure the Bot
   cp config.example.json config.json
   nano config.json

5. Run in Background with Screen
   screen -S marketmaker
   python3 market_maker_bot.py
   - Detach: Ctrl+A then D
   - Reattach: screen -r marketmaker

Configuration

Getting API Keys

Binance
1. Login to Binance.com
2. Profile icon API Management
3. Create API System generated
4. Label: "MarketMaker"
5. Enable "Enable Futures" permission
6. Save API Key and Secret

Bybit
1. Login to Bybit.com
2. Account & Security API
3. Create New Key
4. System-generated API Keys
5. Enable "Derivatives API v3"
6. Enable "Orders" and "Positions"
7. Save API Key and Secret

Other Exchanges
Similar process - create API key with futures/derivatives trading permissions.

Configuring the Bot

Edit config.json with your settings:

{
  "exchange": {
    "name": "bybit",
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "testnet": false
  },
  "trading": {
    "symbol": "ETH/USDT:USDT",
    "leverage": 5,
    "order_size_type": "percentage",
    "order_size_percent": 0.01,
    "order_size": 0.001
  },
  "strategy": {
    "gamma": 0.1,
    "k": 1.5,
    "time_horizon": 1.0,
    "sigma_lookback": 100,
    "update_frequency": 1,
    "min_spread": 0.0001,
    "max_spread_percent": 0.01,
    "max_quote_distance_percent": 0.005
  },
  "risk": {
    "max_inventory_usd": 1000,
    "max_position_size_usd": 100,
    "stop_loss_percent": 0.05,
    "daily_loss_limit_usd": 50
  }
}

Strategy Settings

Conservative (Beginners)
- gamma: 0.5 (high risk aversion)
- leverage: 1 (no leverage)
- order_size_percent: 0.005 (0.5% of balance)
- update_frequency: 5 (update every 5 seconds)

Balanced
- gamma: 0.1
- leverage: 5
- order_size_percent: 0.01
- update_frequency: 2

Aggressive
- gamma: 0.01
- leverage: 10
- order_size_percent: 0.02
- update_frequency: 0.5

Running the Bot

Local (Windows)
start_bot.bat

Local (Mac/Linux)
./start_bot.sh
or
python3 market_maker_bot.py

AWS/Cloud
screen -S marketmaker
python3 market_maker_bot.py
Detach with Ctrl+A, D

Monitoring and Management

View Logs
tail -f market_maker.log

Check Status
The bot displays:
- Current price and spread
- Inventory and balance
- Number of trades
- Profit/Loss

Stop the Bot
- Local: Ctrl+C
- Screen: Reattach and Ctrl+C
- Service: sudo systemctl stop marketmaker

Troubleshooting

Common Issues

"Module not found"
pip3 install -r requirements.txt --upgrade

"API key invalid"
- Check API key and secret are correct
- Ensure futures/derivatives trading is enabled
- Check if using correct network (mainnet vs testnet)

"Insufficient balance"
- Add USDT to your futures account
- Reduce order_size_percent
- Check minimum order requirements

"Symbol not found"
- Check symbol format (e.g., "ETH/USDT:USDT" for perpetuals)
- Verify exchange supports the trading pair

AWS: "git: command not found"
sudo yum install -y git

Getting Help
1. Check market_maker.log for detailed errors
2. Verify configuration in config.json
3. Test with small amounts first
4. Use testnet if available

Safety Guidelines

For Beginners
1. Start Small: Test with $50-100
2. Use Conservative Settings
3. Monitor Closely: Check every few hours initially
4. Set Stop Losses: Always use risk management
5. Understand the Strategy: Read about market making

Risk Management
- Set appropriate max_inventory_usd
- Use stop_loss_percent
- Configure daily_loss_limit_usd
- Start with low leverage or no leverage
- Never invest more than you can afford to lose

Security
- Never share API keys or .pem files
- Use API restrictions (IP whitelist if available)
- Regularly monitor your exchange account
- Keep your server/computer secure
- Use strong passwords

AWS Cost Management
- Stop EC2 instance when not trading
- Monitor AWS billing dashboard
- Use t3.micro for free tier benefits
- Set up billing alerts

Support

For issues:
1. Check this guide thoroughly
2. Review error messages in logs
3. Ensure all prerequisites are met
4. Test with minimal settings first

Copyright 2025 Roboquant - Professional Cryptocurrency Trading Solutions
Website: https://roboquant.ai

Remember: Cryptocurrency trading carries significant risks. This bot is for educational purposes. Always trade responsibly.
