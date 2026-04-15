#!/bin/bash
# DXF Generator Chatbot - Startup Script

echo "======================================"
echo "  DXF Generator Chatbot"
echo "======================================"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: Conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda"
    exit 1
fi

# Source conda
source ~/miniconda3/etc/profile.d/conda.sh

# Check if environment exists
if ! conda env list | grep -q "dxfgen"; then
    echo "Creating conda environment..."
    conda env create -f environment.yml
fi

# Activate environment
echo "Activating conda environment: dxfgen"
conda activate dxfgen

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "Warning: .env file not found!"
    echo "Please create .env file with your OpenAI API key:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your API key"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Check if text_to_dxf exists
if [ ! -d "backend/text_to_dxf" ]; then
    echo ""
    echo "Warning: text_to_dxf not found!"
    echo "Cloning text_to_dxf repository..."
    git clone https://github.com/GreatDevelopers/text_to_dxf.git backend/text_to_dxf
fi

# Create output directory
mkdir -p output

echo ""
echo "Starting Flask server..."
echo "Access the chatbot at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m backend.server
