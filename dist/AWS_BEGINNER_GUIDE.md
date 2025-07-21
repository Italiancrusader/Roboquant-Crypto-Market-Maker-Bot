# Complete Beginner's Guide: Installing Market Maker Bot on AWS Amazon Linux

This guide assumes you have ZERO technical experience. Follow each step exactly as shown.

## Part 1: Getting Started with AWS

### Step 1: Create an AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click the orange "Create an AWS Account" button
3. Enter your email and choose a password
4. Select "Personal" account type
5. Enter your credit card (you won't be charged if you stay in free tier)
6. Verify your phone number
7. Select "Basic support - Free"

### Step 2: Launch Your Server

1. **Login to AWS**
   - Go to [console.aws.amazon.com](https://console.aws.amazon.com)
   - Enter your email and password

2. **Find EC2 Service**
   - In the search bar at the top, type "EC2"
   - Click on "EC2" (Virtual Servers in the Cloud)

3. **Start Creating Your Server**
   - Click the orange "Launch instance" button

4. **Configure Your Server** (follow these EXACT settings):
   
   **Name and tags:**
   - Name: `MarketMakerBot`
   
   **Application and OS Images:**
   - Make sure "Amazon Linux" tab is selected
   - Choose "Amazon Linux 2023 AMI" (should be selected by default)
   - Architecture: 64-bit (x86)
   
   **Instance type:**
   - Select `t3.micro` (it says "Free tier eligible")
   
   **Key pair (login):**
   - Click "Create new key pair"
   - Key pair name: `market-maker-key`
   - Key pair type: RSA (default)
   - Private key file format: .pem (default)
   - Click "Create key pair"
   - **IMPORTANT**: Your browser will download a file called `market-maker-key.pem`
   - **SAVE THIS FILE IN A SAFE PLACE!** You cannot download it again!
   
   **Network settings:**
   - Leave everything as default
   
   **Configure storage:**
   - Leave as default (8 GiB)
   
   **Advanced details:**
   - Leave everything as default

5. **Launch Your Server**
   - Click the orange "Launch instance" button at the bottom
   - You'll see "Success" message
   - Click "View all instances"

6. **Wait for Server to Start**
   - Find your instance in the list
   - Wait until "Instance state" shows "Running" (takes 1-2 minutes)
   - Click on your instance ID (starts with i-)
   - Find and copy your "Public IPv4 address" (looks like: 54.123.45.67)
   - **Write this IP address down!**

## Part 2: Connect to Your Server

### For Windows Users

#### Step A: Download Required Software

1. **Download PuTTY** (this lets you connect to your server)
   - Go to [www.chiark.greenend.org.uk/~sgtatham/putty/latest.html](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)
   - Under "MSI (Windows Installer)", click on "64-bit x86"
   - Run the installer and click "Next" until it's installed

2. **Convert Your Key File**
   - Open Start Menu and search for "PuTTYgen" and open it
   - Click "Load"
   - Change file type dropdown from "PuTTY Private Key Files" to "All Files"
   - Find and select your `market-maker-key.pem` file (probably in Downloads)
   - Click "Open"
   - Click "OK" on the success message
   - Click "Save private key"
   - Click "Yes" to save without passphrase
   - Save it as `market-maker-key.ppk` in your Documents folder
   - Close PuTTYgen

3. **Connect to Your Server**
   - Open PuTTY (search for it in Start Menu)
   - In "Host Name" box, type: `ec2-user@YOUR-IP-ADDRESS`
     - Replace YOUR-IP-ADDRESS with the IP you wrote down (e.g., `ec2-user@54.123.45.67`)
   - Make sure Port is `22`
   - In the left menu, click: Connection → SSH → Auth → Credentials
   - Click "Browse" next to "Private key file"
   - Select your `market-maker-key.ppk` file
   - Click "Open" at the bottom
   - When it asks about trust, click "Accept"
   - You should see: `[ec2-user@ip-xxx-xxx-xxx-xxx ~]$`
   - **Success! You're connected!**

### For Mac Users

1. **Open Terminal**
   - Press Command + Space
   - Type "Terminal"
   - Press Enter

2. **Fix Key Permissions**
   - Type this command (replace USERNAME with your Mac username):
   ```
   chmod 400 /Users/USERNAME/Downloads/market-maker-key.pem
   ```
   - Press Enter

3. **Connect to Server**
   - Type this command (replace YOUR-IP with your server's IP):
   ```
   ssh -i ~/Downloads/market-maker-key.pem ec2-user@YOUR-IP
   ```
   - Press Enter
   - Type "yes" when asked about authenticity
   - Press Enter
   - **Success! You're connected!**

## Part 3: Install the Bot

Now you're connected to your server. Copy and paste these commands ONE AT A TIME:

### Step 1: Update System
```bash
sudo yum update -y
```
- Paste this command and press Enter
- Wait for it to finish (about 1 minute)
- You'll see the prompt again when done

### Step 2: Install Required Software
```bash
sudo yum install -y python3 python3-pip git screen
```
- Paste and press Enter
- Wait for it to finish (about 30 seconds)

### Step 3: Download the Bot
```bash
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
```
- Paste and press Enter
- You'll see "Cloning into..." message

### Step 4: Go to Bot Folder
```bash
cd Roboquant-Crypto-Market-Maker-Bot/dist
```
- Paste and press Enter

### Step 5: Install Python Packages
```bash
pip3 install -r requirements.txt
```
- Paste and press Enter
- This takes 2-3 minutes
- You'll see lots of text scrolling - this is normal

## Part 4: Configure the Bot

### Step 1: Create Your Configuration
```bash
cp config.example.json config.json
```
- Paste and press Enter

### Step 2: Edit Configuration
```bash
nano config.json
```
- Paste and press Enter
- You'll see a text editor with the configuration

### Step 3: Update Your Settings

Use arrow keys to move around. You need to change these lines:

1. **Exchange Name** (line 3):
   - Change `"name": "bybit"` to your exchange
   - Options: binance, bybit, okx, kucoin, gate, mexc, bitget

2. **API Key** (line 4):
   - Change `"api_key": "YOUR_API_KEY_HERE"`
   - Delete YOUR_API_KEY_HERE and type your actual API key

3. **API Secret** (line 5):
   - Change `"api_secret": "YOUR_API_SECRET_HERE"`
   - Delete YOUR_API_SECRET_HERE and type your actual API secret

4. **Trading Pair** (line 10):
   - Change `"symbol": "ETH/USDT:USDT"` if you want a different pair
   - Common options: "BTC/USDT:USDT", "ETH/USDT:USDT"

5. **For Beginners - Make it SAFE** (around line 20):
   - Change `"gamma": 0.1` to `"gamma": 0.5`
   - Change `"leverage": 5` to `"leverage": 1`
   - Change `"order_size_percent": 0.01` to `"order_size_percent": 0.005`

### Step 4: Save Your Changes
1. Press `Ctrl + O` (letter O, not zero)
2. Press `Enter`
3. Press `Ctrl + X` to exit

## Part 5: Run the Bot

### Step 1: Start Screen (keeps bot running when you disconnect)
```bash
screen -S marketmaker
```
- Paste and press Enter
- Screen will clear - this is normal

### Step 2: Run the Bot
```bash
python3 market_maker_bot.py
```
- Paste and press Enter
- You should see the bot starting!
- It will show your balance and start placing orders

### Step 3: Detach from Screen (so bot keeps running)
- Press `Ctrl + A` (hold both keys)
- Then press `D` (just D, not Ctrl+D)
- You'll see "[detached from...]"
- The bot is now running in the background!

### Step 4: Exit Server
```bash
exit
```
- Type exit and press Enter
- You can close PuTTY/Terminal now

## Part 6: Check Your Bot Later

### To See Your Bot Again:

1. **Connect to server** (same as Part 2)

2. **Reattach to bot**:
   ```bash
   screen -r marketmaker
   ```

3. **To stop the bot**: Press `Ctrl + C`

4. **To see logs**:
   ```bash
   cat market_maker.log
   ```

## Getting API Keys from Exchanges

### Binance
1. Login to Binance.com
2. Click your profile icon (top right)
3. Click "API Management"
4. Click "Create API"
5. Choose "System generated"
6. Enter label: "MarketMaker"
7. Pass security verification
8. **IMPORTANT**: Enable "Enable Futures" permission
9. Save your API Key and Secret somewhere safe!

### Bybit
1. Login to Bybit.com
2. Hover over your profile (top right)
3. Click "API"
4. Click "Create New Key"
5. Choose "System-generated API Keys"
6. Select "Derivatives API v3"
7. Enable these permissions:
   - Orders
   - Positions
8. Complete 2FA verification
9. Save your API Key and Secret somewhere safe!

## Important Safety Tips

1. **Start with $50-100** to test
2. **Check the bot every few hours** at first
3. **Never share your .pem file or API keys**
4. **Stop your AWS instance when not using** to save money:
   - Go to AWS Console → EC2
   - Select your instance
   - Click "Instance state" → "Stop instance"

## Troubleshooting

### "Permission denied" when connecting
- Make sure you typed `ec2-user@` before the IP address
- Check your .pem or .ppk file is correct

### "Command not found"
- Make sure you're in the right folder:
  ```bash
  cd ~/Roboquant-Crypto-Market-Maker-Bot/dist
  ```

### Bot won't start
- Check config.json for typos
- Make sure API keys are correct
- Ensure you have USDT in your exchange account

### Need Help?
- The bot creates a log file: `market_maker.log`
- Check it for error messages:
  ```bash
  tail -20 market_maker.log
  ```

## Costs
- **AWS t3.micro**: Free for 12 months (new AWS accounts)
- After free tier: ~$8/month
- **Remember**: Stop your instance when not trading!

## Next Steps
Once comfortable, you can:
1. Increase order sizes gradually
2. Try different trading pairs
3. Adjust strategy parameters
4. Run multiple bots on different exchanges

Good luck with your trading! Remember to start small and monitor closely.
