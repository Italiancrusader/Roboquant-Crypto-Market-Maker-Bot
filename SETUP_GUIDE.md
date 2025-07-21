# Hyperliquid Trading Bot Setup Guide

## Step 1: Create API Wallet on Hyperliquid

1. **Go to Hyperliquid Web Interface**
   - Visit https://app.hyperliquid.xyz/
   - Connect your main wallet

2. **Navigate to API Section**
   - Look for the "API" tab in the interface
   - You should see a section for creating API wallets

3. **Create New API Wallet**
   - Enter a name for your API wallet (e.g., "Trading Bot")
   - Click "Generate" to create the API wallet
   - **IMPORTANT**: Save the generated private key securely!

4. **Authorize API Wallet**
   - Click "Authorize API Wallet" 
   - This gives the API wallet permission to trade on your behalf
   - The API wallet CANNOT withdraw funds - only trade

## Step 2: Update Bot Configuration

1. **Edit the `.env` file** with your API wallet details:
   ```
   HYPERLIQUID_API_KEY=0x[YOUR_API_WALLET_ADDRESS]
   HYPERLIQUID_API_SECRET=0x[YOUR_API_WALLET_PRIVATE_KEY]
   WALLET_ADDRESS=0x[YOUR_MAIN_ACCOUNT_ADDRESS]
   ```

2. **Replace the placeholders:**
   - `YOUR_API_WALLET_ADDRESS`: The address generated for your API wallet
   - `YOUR_API_WALLET_PRIVATE_KEY`: The private key for your API wallet
   - `YOUR_MAIN_ACCOUNT_ADDRESS`: Your main Hyperliquid account address

## Step 3: Fund Your Account

- Deposit USDC to your main Hyperliquid account
- The API wallet will use your main account's balance for trading
- Minimum recommended: $100+ for testing

## Step 4: Run the Bot

1. **Activate virtual environment:**
   ```bash
   newenv\bin\Activate.ps1
   ```

2. **Start the bot:**
   ```bash
   python bot.py
   ```

## Bot Configuration

- **Trading Pair**: ETH/USDC perpetual futures
- **Leverage**: 5x
- **Trade Budget**: $15 per trade
- **Risk Management**: 2% stop-loss, 3% take-profit

## Important Notes

- **API Wallet Security**: The API wallet can only trade, not withdraw
- **Separate from Deposit Wallet**: Your main deposit wallet remains secure
- **Test First**: Start with small amounts to test the bot
- **Monitor**: Always monitor the bot's performance

## Troubleshooting

- **"User does not exist" error**: API wallet not properly authorized
- **"Insufficient balance" error**: Need more USDC in main account
- **Connection errors**: Check internet connection and Hyperliquid status

## Support

If you encounter issues:
1. Check the bot logs for specific error messages
2. Verify API wallet is properly authorized on Hyperliquid
3. Ensure sufficient balance in main account
