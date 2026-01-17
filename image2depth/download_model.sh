#!/bin/bash

# Script to download MiDaS depth estimation models

set -e

# Default model directory in user's local data directory
MODEL_DIR="${HOME}/.local/share/image2depth/models"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create model directory if it doesn't exist
mkdir -p "${MODEL_DIR}"

echo "=================================================="
echo "MiDaS Depth Estimation Model Download Script"
echo "=================================================="
echo ""
echo "Models will be saved to: ${MODEL_DIR}"
echo ""

# Function to download file
download_file() {
    local url=$1
    local output=$2
    
    echo "Downloading from: $url"
    echo "Saving to: $output"
    
    if command -v wget &> /dev/null; then
        wget -O "$output" "$url"
    elif command -v curl &> /dev/null; then
        curl -L -o "$output" "$url"
    else
        echo "Error: Neither wget nor curl is available"
        echo "Please install wget or curl to download models"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ Download completed successfully"
    else
        echo "✗ Download failed"
        exit 1
    fi
}

echo "Which model would you like to download?"
echo ""
echo "1) MiDaS Small v2.1 (256x256) - Recommended for Steam Deck"
echo "   - Size: ~10MB"
echo "   - Speed: Fast (15-20 FPS)"
echo "   - Accuracy: Good"
echo ""
echo "2) MiDaS Small v2.1 (384x384) - Balanced"
echo "   - Size: ~10MB"
echo "   - Speed: Medium (10-15 FPS)"
echo "   - Accuracy: Better"
echo ""
echo "3) Custom URL"
echo "   - Provide your own model URL"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        MODEL_NAME="midas_small_256.onnx"
        # Note: This is a placeholder URL - you'll need to find or create ONNX versions
        echo ""
        echo "WARNING: Pre-converted ONNX models may not be readily available."
        echo "You may need to convert PyTorch models to ONNX format yourself."
        echo ""
        echo "To convert MiDaS to ONNX:"
        echo "1. Clone MiDaS: git clone https://github.com/isl-org/MiDaS.git"
        echo "2. Follow ONNX export instructions in the repository"
        echo "3. Place the exported model at: ${MODEL_DIR}/${MODEL_NAME}"
        echo ""
        read -p "Do you have a custom URL for MiDaS small ONNX model? (y/n): " has_url
        if [ "$has_url" = "y" ]; then
            read -p "Enter URL: " custom_url
            download_file "$custom_url" "${MODEL_DIR}/${MODEL_NAME}"
        else
            echo "Please convert and place the model manually at: ${MODEL_DIR}/${MODEL_NAME}"
            exit 1
        fi
        ;;
    2)
        MODEL_NAME="midas_small_384.onnx"
        echo ""
        echo "WARNING: Pre-converted ONNX models may not be readily available."
        echo "You may need to convert PyTorch models to ONNX format yourself."
        echo ""
        read -p "Do you have a custom URL for MiDaS small ONNX model? (y/n): " has_url
        if [ "$has_url" = "y" ]; then
            read -p "Enter URL: " custom_url
            download_file "$custom_url" "${MODEL_DIR}/${MODEL_NAME}"
        else
            echo "Please convert and place the model manually at: ${MODEL_DIR}/${MODEL_NAME}"
            exit 1
        fi
        ;;
    3)
        read -p "Enter model URL: " custom_url
        read -p "Enter output filename (e.g., model.onnx): " MODEL_NAME
        download_file "$custom_url" "${MODEL_DIR}/${MODEL_NAME}"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Model location: ${MODEL_DIR}/${MODEL_NAME}"
echo ""
echo "To use the model:"
echo ""
echo "  # Standalone test:"
echo "  ./install/image2depth/lib/image2depth/depth_estimation_test \\"
echo "      --model ${MODEL_DIR}/${MODEL_NAME} \\"
echo "      --camera 0"
echo ""
echo "  # ROS2 node:"
echo "  ros2 run image2depth depth_estimation_node \\"
echo "      --ros-args -p model_path:=${MODEL_DIR}/${MODEL_NAME}"
echo ""
echo "=================================================="
echo ""
echo "Note: For production use, consider:"
echo "  1. Using ONNX Runtime for better performance"
echo "  2. Quantizing the model to INT8 for faster inference"
echo "  3. Testing different input sizes (256x256 vs 384x384)"
echo ""
