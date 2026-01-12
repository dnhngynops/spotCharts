#!/bin/bash

# Setup script for Spotify Charts automation

echo "🎵 Spotify Charts Automation Setup"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your credentials:"
    echo "   - Spotify API credentials"
    echo "   - Google Drive folder ID"
    echo "   - Email configuration"
    echo "   - Playlist IDs (4 editorial playlists)"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check for Google Drive credentials
if [ ! -f credentials/google-drive-credentials.json ]; then
    echo "⚠️  Google Drive credentials not found!"
    echo "   Please download OAuth 2.0 credentials from Google Cloud Console"
    echo "   and place them in: credentials/google-drive-credentials.json"
    echo ""
fi

echo "===================================="
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Add Google Drive credentials to credentials/google-drive-credentials.json"
echo "3. Run: source venv/bin/activate && python main.py"
echo ""

