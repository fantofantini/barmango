#!/bin/bash
# Mobile Delivery Manager — Start Script

echo ""
echo "🚚  Mobile Delivery Manager"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌  Python 3 is required. Install from https://python.org"
    exit 1
fi

# Install Flask if needed
python3 -c "import flask" 2>/dev/null || {
    echo "📦  Installing Flask..."
    pip3 install flask flask-cors
}

echo "✅  Starting backend on http://localhost:5000"
echo "🌐  Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
python3 server/app.py
