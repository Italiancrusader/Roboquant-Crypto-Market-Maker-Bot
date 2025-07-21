<div align="center">
  <img src="dist/Asset 3.svg" alt="Roboquant Logo" width="200"/>
  
  # Roboquant Universal Market Making Bot
  
  **Professional Cryptocurrency Trading Solutions**
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Exchanges](https://img.shields.io/badge/Exchanges-11+-orange.svg)](#supported-exchanges)
  [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux%20%7C%20AWS-lightgrey.svg)](#installation)
  
  *Advanced market making bot using the Avellaneda-Stoikov strategy*
  
  [🚀 Quick Start](#quick-start) • [📖 Documentation](#documentation) • [⚙️ Configuration](#configuration) • [🛡️ Safety](#safety-guidelines)
</div>

---

## 🌟 Features

- **🤖 Automated Market Making** - Professional Avellaneda-Stoikov strategy implementation
- **🏦 Multi-Exchange Support** - Works with 11+ major cryptocurrency exchanges
- **⚡ Easy Setup** - One-click launchers for Windows, Mac, and Linux
- **☁️ Cloud Ready** - AWS deployment scripts included
- **🎯 Risk Management** - Built-in stop losses and position limits
- **📊 Real-time Monitoring** - Live P&L tracking and performance metrics
- **🔧 GUI Configuration** - User-friendly setup wizard
- **📱 Cross-Platform** - Runs on Windows, Mac, Linux, and cloud servers

## 🏦 Supported Exchanges

<div align="center">

| Exchange | Status | Futures | Testnet |
|----------|--------|---------|---------|
| **Binance** | ✅ | ✅ | ✅ |
| **Bybit** | ✅ | ✅ | ✅ |
| **OKX** | ✅ | ✅ | ✅ |
| **KuCoin** | ✅ | ✅ | ❌ |
| **Gate.io** | ✅ | ✅ | ✅ |
| **MEXC** | ✅ | ✅ | ❌ |
| **Bitget** | ✅ | ✅ | ✅ |
| **Hyperliquid** | ✅ | ✅ | ✅ |
| **Phemex** | ✅ | ✅ | ✅ |
| **Huobi** | ✅ | ✅ | ❌ |
| **Kraken** | ✅ | ✅ | ❌ |

</div>

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Exchange account with API access
- Some USDT/USD in your futures account

### Installation

#### Windows
```cmd
# Download and extract the repository
# Navigate to the dist folder
cd dist

# Install dependencies
pip install -r requirements.txt

# Configure the bot
configure_bot.bat

# Start trading
start_bot.bat
```

#### Mac/Linux
```bash
# Clone the repository
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot/dist

# Install dependencies
pip3 install -r requirements.txt

# Configure the bot
cp config.example.json config.json
nano config.json

# Start trading
./start_bot.sh
```

#### AWS/Cloud
```bash
# Use our automated setup script
wget https://raw.githubusercontent.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot/master/dist/setup_aws.sh
chmod +x setup_aws.sh
./setup_aws.sh
```

## ⚙️ Configuration

### Strategy Profiles

| Profile | Risk Level | Best For | Leverage | Order Size |
|---------|-----------|----------|----------|------------|
| **🟢 Conservative** | Low | Beginners | 1-2x | 0.5% |
| **🟡 Balanced** | Medium | Most Users | 3-5x | 1.0% |
| **🔴 Aggressive** | High | Experienced | 5-10x | 2.0% |

### Key Parameters

- **`gamma`** - Risk aversion (0.01-1.0, lower = more aggressive)
- **`leverage`** - Position leverage (1-20x)
- **`order_size_percent`** - Order size as % of balance
- **`update_frequency`** - Quote update frequency in seconds
- **`max_inventory_usd`** - Maximum inventory in USD
- **`stop_loss_percent`** - Stop loss threshold

## 📊 Performance

The bot implements the **Avellaneda-Stoikov market making strategy**, which:

- ✅ Dynamically adjusts spreads based on market volatility
- ✅ Manages inventory risk through optimal quote placement
- ✅ Adapts to market conditions in real-time
- ✅ Minimizes adverse selection costs

## 📖 Documentation

- **[📋 Complete Setup Guide](dist/COMPLETE_SETUP_GUIDE.md)** - Detailed installation instructions
- **[🌐 Interactive HTML Guide](dist/setup_guide.html)** - Visual setup guide
- **[📁 Files Overview](dist/FILES_INCLUDED.txt)** - Package contents
- **[⚖️ License](dist/LICENSE)** - MIT License

## 🛡️ Safety Guidelines

> **⚠️ Important**: Cryptocurrency trading carries significant risks. You can lose money.

### For Beginners
1. **Start Small** - Test with $50-100
2. **Use Conservative Settings** - Low leverage, small position sizes
3. **Monitor Closely** - Check the bot regularly
4. **Set Stop Losses** - Always use risk management
5. **Understand the Strategy** - Learn about market making

### Risk Management
- Set appropriate `max_inventory_usd` limits
- Use `stop_loss_percent` for downside protection
- Configure `daily_loss_limit_usd`
- Start with low or no leverage
- Never risk more than you can afford to lose

### Security
- 🔐 Never share API keys
- 🌐 Use IP restrictions when possible
- 👀 Monitor your exchange account regularly
- 🔒 Keep your server/computer secure

## 🚀 Getting Started

1. **Choose Your Platform**
   - [Windows Setup](#windows) - Double-click installers
   - [Mac/Linux Setup](#maclinux) - Terminal commands
   - [AWS Cloud Setup](#awscloud) - Automated scripts

2. **Get API Keys**
   - Create API keys on your chosen exchange
   - Enable futures/derivatives trading
   - Save keys securely

3. **Configure the Bot**
   - Use the GUI wizard or edit JSON manually
   - Choose a strategy profile
   - Set risk limits

4. **Start Trading**
   - Run the bot with provided launchers
   - Monitor performance
   - Adjust settings as needed

## 📈 Monitoring

The bot provides real-time information:
- Current market price and spread
- Inventory and balance
- Number of trades executed
- Profit/Loss tracking
- Risk metrics

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install -r requirements.txt --upgrade` |
| "API key invalid" | Check credentials and enable futures trading |
| "Insufficient balance" | Add USDT to futures account |
| "Symbol not found" | Verify symbol format (e.g., "ETH/USDT:USDT") |

### Getting Help
1. Check the [Complete Setup Guide](dist/COMPLETE_SETUP_GUIDE.md)
2. Review `market_maker.log` for errors
3. Test with small amounts first
4. Use testnet if available

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](dist/LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software. Always trade responsibly and never invest more than you can afford to lose.

---

<div align="center">
  
  **© 2025 Roboquant - Professional Cryptocurrency Trading Solutions**
  
  [Website](https://roboquant.ai) • [Documentation](dist/COMPLETE_SETUP_GUIDE.md) • [Support](mailto:support@roboquant.ai)
  
  *Made with ❤️ for the crypto trading community*
  
</div>
