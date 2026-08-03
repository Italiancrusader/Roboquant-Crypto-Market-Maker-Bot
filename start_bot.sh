#!/bin/bash
# One-click launcher for the Hyperliquid A-S market maker (Mac/Linux).
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  Hyperliquid A-S Market Maker"
echo "========================================"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "  macOS:         brew install python3"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

if ! python -c "import ccxt, dotenv" &>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

if [ ! -f "config.json" ]; then
    cp config.example.json config.json
    echo ""
    echo "Created config.json from the example (testnet mode, ETH/USDC)."
    echo "Edit it to change symbol, sizes, or risk limits."
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "Created .env — you MUST edit it with your wallet address and API"
    echo "wallet private key before the bot can trade."
    echo "Tip: run './start_bot.sh --dry-run' first; it needs no credentials."
fi

echo ""
echo "Starting bot (Ctrl+C to stop; it cancels its orders on exit)..."
echo ""
exec python run_bot.py "$@"
