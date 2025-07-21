<p align="center">
  <img src="Asset 3.svg" alt="Roboquant Logo" width="200"/>
</p>

<h1 align="center">Roboquant Universal Market Making Bot</h1>
<h3 align="center">Complete Setup & Installation Guide</h3>

<p align="center">
  <strong>© 2025 Roboquant - Professional Cryptocurrency Trading Solutions</strong><br>
  <a href="https://roboquant.ai">roboquant.ai</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Exchanges-11+-orange.svg" alt="Exchanges">
</p>

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [✅ Prerequisites](#-prerequisites)
- [🏦 Supported Exchanges](#-supported-exchanges)
- [💻 Local Installation](#-local-installation)
  - [Windows Setup](#windows-setup)
  - [Mac Setup](#mac-setup)
  - [Linux Setup](#linux-setup)
- [☁️ AWS Cloud Installation](#️-aws-cloud-installation)
  - [Creating AWS Account](#creating-aws-account)
  - [Launching EC2 Instance](#launching-ec2-instance)
  - [Connecting to Your Server](#connecting-to-your-server)
  - [Installing the Bot on AWS](#installing-the-bot-on-aws)
- [⚙️ Configuration](#️-configuration)
  - [Getting API Keys](#getting-api-keys)
  - [Configuring the Bot](#configuring-the-bot)
  - [Strategy Settings](#strategy-settings)
- [▶️ Running the Bot](#️-running-the-bot)
- [📊 Monitoring and Management](#-monitoring-and-management)
- [🔧 Troubleshooting](#-troubleshooting)
- [⚠️ Safety Guidelines](#️-safety-guidelines)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot/dist

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp config.example.json config.json
# Edit config.json with your API keys

# 4. Run
python market_maker_bot.py
```

---

## ✅ Prerequisites

| Requirement | Details |
|------------|---------|
| **Python** | Version 3.8 or higher |
| **Exchange Account** | With API access enabled |
| **Capital** | Some USDT/USD in futures account |
| **Skills** | Basic command line knowledge |

---

## 🏦 Supported Exchanges

<table>
<tr>
<td align="center"><strong>Binance</strong></td>
<td align="center"><strong>Bybit</strong></td>
<td align="center"><strong>OKX</strong></td>
<td align="center"><strong>KuCoin</strong></td>
</tr>
<tr>
<td align="center"><strong>Gate.io</strong></td>
<td align="center"><strong>MEXC</strong></td>
<td align="center"><strong>Bitget</strong></td>
<td align="center"><strong>Hyperliquid</strong></td>
</tr>
<tr>
<td align="center"><strong>Phemex</strong></td>
<td align="center"><strong>Huobi</strong></td>
<td align="center"><strong>Kraken</strong></td>
<td align="center">More coming...</td>
</tr>
</table>

---

## 💻 Local Installation

### Windows Setup

<details>
<summary><b>📌 Click to expand Windows instructions</b></summary>

#### 🔹 Step 1: Install Python
1. Download Python from [python.org](https://python.org/downloads/)
2. Run the installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"

#### 🔹 Step 2: Download the Bot
1. Go to the [GitHub Repository](https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot)
2. Click the green "Code" button → "Download ZIP"
3. Extract the ZIP file to a folder (e.g., `C:\TradingBot`)
4. Navigate to the `dist` folder

#### 🔹 Step 3: Install Dependencies
Open Command Prompt (Win+R, type `cmd`, press Enter):
```cmd
cd C:\TradingBot\dist
pip install -r requirements.txt
```

#### 🔹 Step 4: Configure and Run
1. Double-click `configure_bot.bat` to open the configuration wizard
2. Or copy `config.example.json` to `config.json` and edit manually
3. Double-click `start_bot.bat` to run the bot

</details>

### Mac Setup

<details>
<summary><b>📌 Click to expand Mac instructions</b></summary>

#### 🔹 Step 1: Install Python (if needed)
Open Terminal (Cmd+Space, type "Terminal"):
```bash
# Check if Python is installed
python3 --version

# If not installed, install via Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
```

#### 🔹 Step 2: Download the Bot
```bash
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot/dist
```

#### 🔹 Step 3: Install Dependencies
```bash
pip3 install -r requirements.txt
```

#### 🔹 Step 4: Configure and Run
```bash
cp config.example.json config.json
nano config.json  # Edit your settings
python3 market_maker_bot.py
```

</details>

### Linux Setup

<details>
<summary><b>📌 Click to expand Linux instructions</b></summary>

#### 🔹 Step 1: Install Python and Git

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip git
```

#### 🔹 Step 2-4: Same as Mac
Follow the same steps as Mac setup above.

</details>

---

## ☁️ AWS Cloud Installation

### Creating AWS Account

<details>
<summary><b>📌 Click to expand AWS account creation</b></summary>

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Enter email and password
4. Choose "Personal" account type
5. Enter payment information (required, but free tier available)
6. Verify phone number
7. Select "Basic support - Free"

> 💡 **Tip**: AWS offers 12 months of free tier for new accounts!

</details>

### Launching EC2 Instance

<details>
<summary><b>📌 Click to expand EC2 setup</b></summary>

#### 1️⃣ Access EC2 Dashboard
- Login to [AWS Console](https://console.aws.amazon.com)
- Search for "EC2" and click it

#### 2️⃣ Launch Instance
- Click orange "Launch instance" button
- Configure:
  - **Name**: `MarketMakerBot`
  - **OS**: Amazon Linux 2023 AMI
  - **Instance type**: `t3.micro` (free tier eligible)
  - **Key pair**: 
    - Click "Create new key pair"
    - Name: `market-maker-key`
    - Type: RSA
    - Format: .pem
    - 🔐 **SAVE THE DOWNLOADED FILE SAFELY!**
  - Leave other settings as default
  - Click "Launch instance"

#### 3️⃣ Wait for Instance
- Click "View all instances"
- Wait for "Running" status
- Note your Public IPv4 address

</details>

### Connecting to Your Server

<details>
<summary><b>📌 Click to expand connection instructions</b></summary>

#### 🖥️ Windows (Using PuTTY)

1. **Download PuTTY** from [putty.org](https://www.putty.org/download.html)
2. **Convert Key**:
   - Open PuTTYgen
   - Click "Load" → Select your .pem file
   - Click "Save private key" → Save as .ppk
3. **Connect**:
   - Open PuTTY
   - Host: `ec2-user@YOUR-IP-ADDRESS`
   - Port: 22
   - Connection → SSH → Auth → Browse → Select .ppk file
   - Click "Open"

#### 🍎 Mac/Linux

```bash
# Set key permissions
chmod 400 ~/Downloads/market-maker-key.pem

# Connect
ssh -i ~/Downloads/market-maker-key.pem ec2-user@YOUR-IP-ADDRESS
```

</details>

### Installing the Bot on AWS

Once connected to your EC2 instance:

```bash
# 1. Update system and install requirements
sudo yum update -y
sudo yum install -y python3 python3-pip git screen

# 2. Clone the repository
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot/dist

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Configure the bot
cp config.example.json config.json
nano config.json

# 5. Run in background with screen
screen -S marketmaker
python3 market_maker_bot.py
# Detach: Ctrl+A then D
# Reattach: screen -r marketmaker
```

---

## ⚙️ Configuration

### Getting API Keys

<details>
<summary><b>🔑 Binance API Setup</b></summary>

1. Login to Binance.com
2. Profile icon → API Management
3. Create API → System generated
4. Label: "MarketMaker"
5. Enable "Enable Futures" permission
6. Save API Key and Secret

</details>

<details>
<summary><b>🔑 Bybit API Setup</b></summary>

1. Login to Bybit.com
2. Account & Security → API
3. Create New Key
4. System-generated API Keys
5. Enable "Derivatives API v3"
6. Enable "Orders" and "Positions"
7. Save API Key and Secret

</details>

### Configuring the Bot

Create your `config.json`:

```json
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
```

### Strategy Settings

| Profile | Risk Level | Best For | Settings |
|---------|-----------|----------|----------|
| **🟢 Conservative** | Low | Beginners | `gamma`: 0.5<br>`leverage`: 1<br>`order_size_percent`: 0.005<br>`update_frequency`: 5 |
| **🟡 Balanced** | Medium | Most Users | `gamma`: 0.1<br>`leverage`: 5<br>`order_size_percent`: 0.01<br>`update_frequency`: 2 |
| **🔴 Aggressive** | High | Experienced | `gamma`: 0.01<br>`leverage`: 10<br>`order_size_percent`: 0.02<br>`update_frequency`: 0.5 |

---

## ▶️ Running the Bot

### 🖥️ Local (Windows)
```cmd
start_bot.bat
```

### 🍎 Local (Mac/Linux)
```bash
./start_bot.sh
# or
python3 market_maker_bot.py
```

### ☁️ AWS/Cloud
```bash
screen -S marketmaker
python3 market_maker_bot.py
# Detach with Ctrl+A, D
```

---

## 📊 Monitoring and Management

### 📈 Real-time Monitoring
```bash
# View logs
tail -f market_maker.log

# Bot displays:
# ✓ Current price and spread
# ✓ Inventory and balance
# ✓ Number of trades
# ✓ Profit/Loss
```

### 🛑 Stopping the Bot
- **Local**: Press `Ctrl+C`
- **Screen**: Reattach and `Ctrl+C`
- **Service**: `sudo systemctl stop marketmaker`

---

## 🔧 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **"Module not found"** | `pip3 install -r requirements.txt --upgrade` |
| **"API key invalid"** | • Check API credentials<br>• Enable futures trading<br>• Verify mainnet/testnet |
| **"Insufficient balance"** | • Add USDT to futures account<br>• Reduce `order_size_percent`<br>• Check minimum order size |
| **"Symbol not found"** | • Check format: `ETH/USDT:USDT`<br>• Verify exchange support |
| **AWS: "git not found"** | `sudo yum install -y git` |

### 💡 Getting Help
1. Check `market_maker.log` for detailed errors
2. Verify configuration in `config.json`
3. Test with small amounts first
4. Use testnet if available

---

## ⚠️ Safety Guidelines

### 🛡️ For Beginners
1. **Start Small**: Test with $50-100
2. **Use Conservative Settings**
3. **Monitor Closely**: Check every few hours initially
4. **Set Stop Losses**: Always use risk management
5. **Understand the Strategy**: Read about market making

### 📊 Risk Management
- ✅ Set appropriate `max_inventory_usd`
- ✅ Use `stop_loss_percent`
- ✅ Configure `daily_loss_limit_usd`
- ✅ Start with low leverage or no leverage
- ✅ Never invest more than you can afford to lose

### 🔒 Security Best Practices
- 🚫 Never share API keys or .pem files
- 🔐 Use API restrictions (IP whitelist)
- 👀 Regularly monitor your exchange account
- 🛡️ Keep your server/computer secure
- 🔑 Use strong passwords

### 💰 AWS Cost Management
- ⏸️ Stop EC2 instance when not trading
- 📊 Monitor AWS billing dashboard
- 🆓 Use t3.micro for free tier benefits
- 🔔 Set up billing alerts

---

<p align="center">
  <strong>© 2025 Roboquant - Professional Cryptocurrency Trading Solutions</strong><br>
  <a href="https://roboquant.ai">Website</a> • 
  <a href="https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot">GitHub</a>
</p>

<p align="center">
  <em>⚠️ Cryptocurrency trading carries significant risks. This bot is for educational purposes. Always trade responsibly.</em>
</p>
