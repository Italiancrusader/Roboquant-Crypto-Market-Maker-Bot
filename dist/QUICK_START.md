# 🚀 QUICK START GUIDE

## For Windows Users

1. **Double-click `start_bot.bat`**
   - This will check for Python, install dependencies, and start the configuration wizard

2. **Configure your bot** (if first time)
   - Select your exchange
   - Enter your API credentials
   - Choose Conservative settings to start
   - Click "Save Configuration"

3. **Bot will start automatically**
   - Watch the console for trading activity
   - Press Ctrl+C to stop

## For Mac/Linux Users

1. **Open Terminal in the bot folder**

2. **Make the script executable**
   ```bash
   chmod +x start_bot.sh
   ```

3. **Run the bot**
   ```bash
   ./start_bot.sh
   ```

4. **Configure and run** (same as Windows)

## For Cloud/VPS Users

1. **Upload all files to your server**

2. **Run the setup script**
   ```bash
   chmod +x setup_aws.sh
   ./setup_aws.sh
   ```

3. **Configure the bot**
   ```bash
   python3 config_wizard.py
   ```

4. **Start the bot**
   ```bash
   screen -S marketmaker
   ./start_bot.sh
   ```

5. **Detach screen** with `Ctrl+A` then `D`

## 🎯 First Time Setup Checklist

- [ ] Have your exchange API keys ready
- [ ] Start with Conservative settings
- [ ] Use a small amount to test (e.g., $50-100)
- [ ] Monitor the bot for the first hour
- [ ] Check the logs if anything goes wrong

## ⚡ Need Help?

1. Check `README.md` for detailed instructions
2. Look at `market_maker.log` for error messages
3. Run the Configuration Wizard again to change settings
4. Test your connection using the "Test Connection" button

## 🛑 Emergency Stop

- **Windows**: Press `Ctrl+C` in the console
- **Mac/Linux**: Press `Ctrl+C` in terminal
- **Cloud**: `screen -r marketmaker` then `Ctrl+C`

Remember: Start small, monitor closely, and increase gradually!
