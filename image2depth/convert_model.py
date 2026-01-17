#!/usr/bin/env python3
"""
MiDaS Model Conversion Script

This script downloads MiDaS models and converts them to ONNX format
for use with the image2depth module.
"""

import os
import sys
import argparse
import urllib.request
from pathlib import Path

def download_file(url, output_path):
    """Download a file with progress reporting."""
    print(f"Downloading from: {url}")
    print(f"Saving to: {output_path}")
    
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\rProgress: {percent}%")
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, output_path, progress_hook)
        print("\n✓ Download completed")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

def convert_to_onnx(model_path, output_path, input_size=(256, 256)):
    """Convert PyTorch model to ONNX format."""
    try:
        import torch
        import torch.onnx
    except ImportError:
        print("Error: PyTorch is not installed")
        print("Install with: pip install torch torchvision")
        return False
    
    print(f"\nConverting model to ONNX...")
    print(f"  Input: {model_path}")
    print(f"  Output: {output_path}")
    print(f"  Input size: {input_size[0]}x{input_size[1]}")
    
    try:
        # Load model
        print("Loading PyTorch model...")
        model = torch.load(model_path, map_location='cpu')
        
        # Handle different model structures
        if isinstance(model, dict):
            if 'model' in model:
                model = model['model']
            elif 'state_dict' in model:
                # Need to load architecture first
                print("Error: Model requires architecture definition")
                print("Please use the official MiDaS conversion script")
                return False
        
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randn(1, 3, input_size[0], input_size[1])
        
        # Export to ONNX
        print("Exporting to ONNX...")
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        print(f"✓ Model exported successfully to: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        print("\nNote: MiDaS model conversion can be complex.")
        print("Consider using the official conversion tools from:")
        print("https://github.com/isl-org/MiDaS")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Download and convert MiDaS depth estimation models to ONNX format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and convert MiDaS small model
  %(prog)s --model small --output ~/.local/share/image2depth/models/midas_small.onnx

  # Convert existing PyTorch model
  %(prog)s --convert model-small.pt --output midas_small.onnx --size 256

  # Download only (no conversion)
  %(prog)s --model small --output model-small.pt --no-convert

Note: For best results, use the official MiDaS repository for conversion:
      https://github.com/isl-org/MiDaS
        """
    )
    
    parser.add_argument(
        '--model',
        choices=['small', 'v2_1'],
        help='MiDaS model to download'
    )
    
    parser.add_argument(
        '--convert',
        type=str,
        help='Path to existing PyTorch model to convert'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output file path'
    )
    
    parser.add_argument(
        '--size',
        type=int,
        default=256,
        choices=[256, 384, 512],
        help='Input size for the model (default: 256)'
    )
    
    parser.add_argument(
        '--no-convert',
        action='store_true',
        help='Download only, do not convert to ONNX'
    )
    
    args = parser.parse_args()
    
    if not args.model and not args.convert:
        parser.error("Either --model or --convert must be specified")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, mode=0o755)
        print(f"Created directory: {output_dir}")
    
    # Handle download
    if args.model:
        # Define model URLs
        model_urls = {
            'small': 'https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.pt',
            'v2_1': 'https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21-small-70d6b9c8.pt'
        }
        
        url = model_urls[args.model]
        
        if args.no_convert:
            # Download directly to output path
            if not download_file(url, args.output):
                return 1
        else:
            # Download to user's cache directory (safer than /tmp)
            cache_dir = os.path.expanduser("~/.cache/image2depth")
            os.makedirs(cache_dir, mode=0o700, exist_ok=True)
            temp_path = os.path.join(cache_dir, f"midas_{args.model}.pt")
            
            if not download_file(url, temp_path):
                return 1
            
            # Convert to ONNX
            if not convert_to_onnx(temp_path, args.output, (args.size, args.size)):
                return 1
            
            # Clean up temp file
            os.remove(temp_path)
    
    # Handle conversion only
    elif args.convert:
        if not os.path.exists(args.convert):
            print(f"Error: Model file not found: {args.convert}")
            return 1
        
        if not convert_to_onnx(args.convert, args.output, (args.size, args.size)):
            return 1
    
    print("\n" + "="*50)
    print("Setup Complete!")
    print("="*50)
    print(f"\nModel saved to: {args.output}")
    print("\nTo test the model:")
    print(f"  ./install/image2depth/lib/image2depth/depth_estimation_test \\")
    print(f"      --model {args.output} \\")
    print(f"      --camera 0")
    print("\nTo use with ROS2:")
    print(f"  ros2 run image2depth depth_estimation_node \\")
    print(f"      --ros-args -p model_path:={args.output}")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
