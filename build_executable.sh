#!/bin/bash
# Build a standalone executable for the current platform into binaries/.
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt pyinstaller

pyinstaller --onefile --name hyperliquid-mm --distpath binaries --clean run_bot.py

# Desktop app (needs a Python with Tk support; skipped otherwise)
if python -c "import tkinter" &>/dev/null; then
    if [ "$(uname)" = "Darwin" ]; then
        pyinstaller --windowed --name HyperliquidMM --icon assets/icon.icns --distpath binaries run_gui.py
        rm -rf binaries/HyperliquidMM  # keep only the .app bundle
    else
        pyinstaller --onefile --windowed --name HyperliquidMM --icon assets/icon.ico --distpath binaries run_gui.py
    fi
else
    echo "NOTE: this Python lacks tkinter — skipped the GUI app."
    echo "      (macOS: brew install python-tk, or use the python.org installer)"
fi

echo ""
echo "Built into binaries/:"
ls binaries/
echo ""
echo "Note: executables are per-platform. Build on each OS you target, or use"
echo "the GitHub Actions workflow (.github/workflows/build.yml) for all three."
