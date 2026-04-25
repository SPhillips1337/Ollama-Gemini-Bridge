#!/bin/bash

# Ollama-Gemini Bridge Installation Script
# This script automates the setup of the bridge and its dependencies.

set -e

echo "----------------------------------------------------"
echo "🌟 Starting Ollama-Gemini Bridge Installation 🌟"
echo "----------------------------------------------------"

# 1. System Checks
echo "🔍 Checking system dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# Check Node.js/npx (required for standard MCP servers)
if ! command -v npx &> /dev/null; then
    echo "⚠️  Warning: npx (Node.js) is not installed. Standard MCP servers may not work."
fi

# Check Gemini CLI
if ! command -v gemini &> /dev/null; then
    echo "ℹ️  Gemini CLI not found. You can still use Direct API mode."
    GEMINI_CLI_FOUND=false
else
    echo "✅ Gemini CLI found."
    GEMINI_CLI_FOUND=true
fi

# 2. Python Environment Setup
echo "📦 Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "ℹ️  Virtual environment already exists."
fi

echo "📥 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed."

# 3. Interactive Configuration (.env)
echo "⚙️  Configuring environment variables..."

if [ -f ".env" ]; then
    echo "⚠️  A .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " OVERWRITE
    if [[ ! $OVERWRITE =~ ^[Yy]$ ]]; then
        echo "⏭️  Skipping .env configuration."
        SETUP_ENV=false
    else
        SETUP_ENV=true
    fi
else
    SETUP_ENV=true
fi

if [ "$SETUP_ENV" = true ]; then
    # Default values
    DEFAULT_TOKEN=$(LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 32 | head -n 1)
    DEFAULT_SERVERS="npx -y @modelcontextprotocol/server-everything,python3 $(pwd)/gemini_cli_mcp.py,python3 $(pwd)/mcp_memory_server.py"

    echo ""
    echo "--- Configuration ---"
    
    # Mode Selection
    echo "Select Inference Mode:"
    echo "1) Keyless (CLI) Mode - Uses your local 'gemini' CLI OAuth session."
    echo "2) Direct API Mode - Uses a Gemini API Key."
    read -p "Choice (1 or 2): " MODE_CHOICE

    if [ "$MODE_CHOICE" == "2" ]; then
        read -p "Enter your GEMINI_API_KEY: " API_KEY
    else
        API_KEY="your_gemini_api_key_here"
    fi

    # Auth Token
    read -p "Enter a secure BRIDGE_AUTH_TOKEN [Default: $DEFAULT_TOKEN]: " AUTH_TOKEN
    AUTH_TOKEN=${AUTH_TOKEN:-$DEFAULT_TOKEN}

    # MCP Servers
    echo "Default MCP Servers: $DEFAULT_SERVERS"
    read -p "Do you want to use these default servers? (Y/n): " USE_DEFAULTS
    if [[ $USE_DEFAULTS =~ ^[Nn]$ ]]; then
        read -p "Enter your comma-separated MCP_SERVERS commands: " MCP_SERVERS
    else
        MCP_SERVERS=$DEFAULT_SERVERS
    fi

    # Write to .env
    cat <<EOF > .env
GEMINI_API_KEY=$API_KEY
BRIDGE_AUTH_TOKEN=$AUTH_TOKEN
MCP_SERVERS=$MCP_SERVERS
EOF
    echo "✅ .env file generated successfully."
fi

# 4. Final Instructions
echo ""
echo "----------------------------------------------------"
echo "🎉 Installation Complete! 🎉"
echo "----------------------------------------------------"
echo "To start the bridge, run the following command:"
echo ""
echo "source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 11434"
echo ""
if [ "$MODE_CHOICE" != "2" ] && [ "$GEMINI_CLI_FOUND" = true ]; then
    echo "💡 Reminder: Make sure you are logged into the Gemini CLI by running: gemini login"
fi
echo "----------------------------------------------------"
