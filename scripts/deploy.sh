#!/bin/bash
set -e

APP_NAME="backend"
APP_DIR="$HOME/website/backend"

echo "🚀 Backend deployment started..."

cd $APP_DIR

echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "♻️ Restarting backend..."
pm2 reload $APP_NAME || pm2 start app.py --name $APP_NAME --interpreter python3

pm2 save

echo "✅ Backend deployment completed!"
