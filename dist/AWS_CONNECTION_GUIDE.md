# AWS EC2 Connection & Setup Guide

## Quick Connection Steps

### 1. Prepare Your Key File

**Windows:**
- Save your `.pem` file in a safe location (e.g., `C:\Users\YourName\aws-keys\`)
- No special permissions needed on Windows

**Mac/Linux:**
```bash
chmod 400 your-key-name.pem
```

### 2. Connect to Your Instance

**For Amazon Linux EC2:**
```bash
ssh -i your-key-name.pem ec2-user@YOUR-PUBLIC-IP
```

**For Ubuntu EC2:**
```bash
ssh -i your-key-name.pem ubuntu@YOUR-PUBLIC-IP
```

**Example with your instance:**
```bash
ssh -i your-key.pem ec2-user@18.185.28.165
```

### 3. Windows Users - Connection Options

**Option A: Windows PowerShell/Terminal (Windows 10/11)**
```powershell
ssh -i C:\path\to\your-key.pem ec2-user@18.185.28.165
```

**Option B: Using PuTTY**
1. Download PuTTY and PuTTYgen from [putty.org](https://www.putty.org/)
2. Convert .pem to .ppk:
   - Open PuTTYgen
   - Click "Load" and select your .pem file
   - Click "Save private key" as .ppk
3. Connect with PuTTY:
   - Host: `18.185.28.165`
   - Port: 22
   - Connection type: SSH
   - Connection → SSH → Auth → Browse for your .ppk file
   - Click "Open"
   - Login as: `ec2-user`

## Setting Up the Bot on Amazon Linux

### Step 1: Connect and Update
```bash
# Connect
ssh -i your-key.pem ec2-user@18.185.28.165

# Update system
sudo yum update -y
```

### Step 2: Install Required Software
```bash
# Install Python and tools
sudo yum install -y python3 python3-pip python3-devel gcc screen git

# Verify installation
python3 --version
```

### Step 3: Transfer Bot Files

**Option A - Using SCP (from your local machine):**
```bash
# From your local machine (where the dist folder is)
scp -i your-key.pem -r dist/* ec2-user@18.185.28.165:~/
```

**Option B - Using Git (if hosted on GitHub):**
```bash
# On the EC2 instance
git clone https://github.com/yourusername/market-maker-bot.git
cd market-maker-bot
```

**Option C - Using FileZilla (GUI):**
1. Download FileZilla
2. File → Site Manager → New Site
3. Protocol: SFTP
4. Host: 18.185.28.165
5. Logon Type: Key file
6. User: ec2-user
7. Key file: Browse to your .pem file
8. Connect and drag files to server

### Step 4: Set Up the Bot
```bash
# Create directory if needed
mkdir -p ~/market-maker-bot
cd ~/market-maker-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure the bot (GUI won't work over SSH)
cp config.example.json config.json
nano config.json  # Edit with your API keys
```

### Step 5: Run the Bot

**Option 1 - Using Screen (Recommended):**
```bash
# Start a new screen session
screen -S marketmaker

# Run the bot
python3 market_maker_bot.py

# Detach from screen: Press Ctrl+A, then D
# Reattach later: screen -r marketmaker
```

**Option 2 - Using nohup:**
```bash
nohup python3 market_maker_bot.py > bot.log 2>&1 &

# View logs
tail -f bot.log
```

**Option 3 - As a System Service:**
```bash
# Run the setup script
chmod +x setup_aws.sh
./setup_aws.sh

# Or manually create service
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
ExecStart=/home/ec2-user/market-maker-bot/venv/bin/python /home/ec2-user/market-maker-bot/market_maker_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable marketmaker
sudo systemctl start marketmaker
sudo systemctl status marketmaker
```

## Monitoring Your Bot

### View Logs
```bash
# If using screen
screen -r marketmaker

# If using systemd
sudo journalctl -u marketmaker -f

# If using nohup
tail -f bot.log

# Bot's own log file
tail -f market_maker.log
```

### Check if Bot is Running
```bash
# Check process
ps aux | grep market_maker_bot

# Check system service
sudo systemctl status marketmaker
```

### Stop the Bot
```bash
# If in screen
screen -r marketmaker
# Then Ctrl+C

# If using systemd
sudo systemctl stop marketmaker

# If using nohup
pkill -f market_maker_bot.py
```

## Security Best Practices

1. **Secure Your Keys**
   - Never share your .pem file
   - Store it securely on your local machine
   - Set proper permissions: `chmod 400 your-key.pem`

2. **Update Security Group**
   - Only allow SSH from your IP
   - In AWS Console: EC2 → Security Groups → Edit inbound rules
   - Change SSH source from 0.0.0.0/0 to your IP

3. **Keep System Updated**
   ```bash
   sudo yum update -y
   ```

4. **Monitor Access**
   ```bash
   # Check login history
   last
   
   # Check current connections
   who
   ```

## Troubleshooting

### "Permission denied (publickey)"
- Check you're using correct username: `ec2-user` for Amazon Linux
- Verify key file path is correct
- Ensure key permissions: `chmod 400 your-key.pem`

### "Connection timed out"
- Check instance is running in AWS Console
- Verify Security Group allows SSH (port 22) from your IP
- Check if you're behind a firewall

### "No such file or directory"
- Ensure you're in the correct directory
- Use full paths when unsure
- List files with `ls -la` to verify

### Bot Won't Start
- Check Python version: `python3 --version` (need 3.8+)
- Verify all files uploaded correctly
- Check config.json is valid JSON
- Look at error messages in logs

## Useful Commands

```bash
# Check disk space
df -h

# Check memory usage
free -m

# Check running processes
top

# Exit SSH session
exit

# Copy files from server to local
scp -i your-key.pem ec2-user@18.185.28.165:~/market_maker.log ./
```

## Cost Optimization

- Stop instance when not using: AWS Console → Instance → Stop
- Use t3.micro for testing (free tier eligible)
- Set up CloudWatch alarms for billing alerts
- Consider spot instances for non-critical testing

Remember: Always test with small amounts first!
