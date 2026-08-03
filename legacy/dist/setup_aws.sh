#!/bin/bash

echo "========================================"
echo "   Roboquant Market Maker Bot"
echo "   AWS/VPS Setup Script"
echo "   © 2025 Roboquant"
echo "========================================"
echo ""
echo "This script will set up Roboquant bot on your AWS/Linux server"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Please install manually."
    exit 1
fi

# Update system and install dependencies based on OS
if [[ "$OS" == "amzn" ]] || [[ "$OS" == "amazonlinux" ]]; then
    echo "Detected Amazon Linux"
    echo ""
    echo "1. Updating system packages..."
    sudo yum update -y
    
    echo ""
    echo "2. Installing Python and required tools..."
    sudo yum install -y python3 python3-pip python3-devel gcc screen
elif [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    echo "Detected Ubuntu/Debian"
    echo ""
    echo "1. Updating system packages..."
    sudo apt update -y
    
    echo ""
    echo "2. Installing Python and required tools..."
    sudo apt install -y python3 python3-pip python3-venv screen
else
    echo "Unsupported OS: $OS"
    echo "Please install Python 3, pip, and screen manually."
    exit 1
fi

# Create bot directory
echo ""
echo "3. Setting up bot directory..."
mkdir -p ~/market-maker-bot
cd ~/market-maker-bot

# Copy files (assuming they're in current directory)
echo ""
echo "4. Copying bot files..."
cp market_maker_bot.py ~/market-maker-bot/
cp config_wizard.py ~/market-maker-bot/
cp requirements.txt ~/market-maker-bot/
cp config.example.json ~/market-maker-bot/
cp start_bot.sh ~/market-maker-bot/
chmod +x ~/market-maker-bot/start_bot.sh

# Create virtual environment
echo ""
echo "5. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo ""
echo "6. Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service (optional)
echo ""
echo "7. Creating systemd service for auto-start (optional)..."

# Determine the correct user home directory
if [[ "$OS" == "amzn" ]] || [[ "$OS" == "amazonlinux" ]]; then
    SERVICE_USER="ec2-user"
    HOME_DIR="/home/ec2-user"
else
    SERVICE_USER="$USER"
    HOME_DIR="/home/$USER"
fi

sudo tee /etc/systemd/system/market-maker-bot.service > /dev/null <<EOF
[Unit]
Description=Market Making Bot
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$HOME_DIR/market-maker-bot
Environment="PATH=$HOME_DIR/market-maker-bot/venv/bin"
ExecStart=$HOME_DIR/market-maker-bot/venv/bin/python $HOME_DIR/market-maker-bot/market_maker_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "========================================"
echo "Roboquant Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Configure the bot: python3 config_wizard.py"
echo "2. Run the bot:"
echo "   - Interactive: ./start_bot.sh"
echo "   - Background: screen -S marketmaker ./start_bot.sh"
echo "   - As service: sudo systemctl enable market-maker-bot && sudo systemctl start market-maker-bot"
echo ""
echo "To monitor the bot:"
echo "   - Screen: screen -r marketmaker"
echo "   - Service logs: sudo journalctl -u market-maker-bot -f"
echo ""
echo "For Amazon Linux users:"
echo "   - Default user is 'ec2-user'"
echo "   - Files are in /home/ec2-user/market-maker-bot"
echo ""
