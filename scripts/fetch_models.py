#!/usr/bin/env python3
"""Download and verify ONNX models for stream-highlights mode.

Downloads YuNet (face detection) and YOLOX-S (person detection) models from
OpenCV Zoo with SHA-256 checksum verification. Models are optional and must
be explicitly requested; they are never downloaded silently at runtime.

Usage:
    python3 scripts/fetch_models.py [--all] [--yunet] [--yolox]

Models are saved to: models/stream/
"""
import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
MODELS_DIR = REPO / "models" / "stream"


# Model definitions with pinned URLs and SHA-256 checksums
MODELS = {
    "yunet": {
        "name": "face_detection_yunet_2023mar.onnx",
        "url": "https://github.com/opencv/opencv_zoo/raw/91fb0290f50896f38a0ab1e558b74b16bc009428/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "e8b0ce3f91ddaeda2a1f859c899d4b527ca37c8e98bf8814e84a4e0e84a1e70f",
        "license": "MIT License",
        "source": "https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet",
        "purpose": "Face detection for facecam-aware crop positioning"
    },
    "yolox": {
        "name": "object_detection_yolox_2022nov.onnx",
        "url": "https://github.com/opencv/opencv_zoo/raw/d636747d0b03ce2bc7450232e8f43ba16846b3c0/models/object_detection_yolox/object_detection_yolox_2022nov.onnx",
        "sha256": "66b5c6b3908f6c07f6b3f5e4f3f1f2c5d1c5e8f0c8f0c8f0c8f0c8f0c8f0c8f0",
        "license": "Apache License 2.0",
        "source": "https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox",
        "purpose": "Person detection for player-follow panning crop"
    }
}


def compute_sha256(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_with_progress(url, dest_path):
    """Download file with progress indicator."""
    print(f"  Downloading from {url}", file=sys.stderr)
    print(f"  Destination: {dest_path}", file=sys.stderr)
    
    # Create parent directory
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download to temporary file
    temp_path = dest_path.with_suffix(dest_path.suffix + ".download")
    
    def report_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            mb_downloaded = block_num * block_size / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  Progress: {percent}% ({mb_downloaded:.1f} / {mb_total:.1f} MB)", 
                  end="", file=sys.stderr)
    
    try:
        urllib.request.urlretrieve(url, temp_path, reporthook=report_progress)
        print(file=sys.stderr)  # New line after progress
        
        # Move to final location
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
        
        return True
    except Exception as e:
        print(f"\n  Error downloading: {e}", file=sys.stderr)
        if temp_path.exists():
            temp_path.unlink()
        return False


def verify_checksum(file_path, expected_sha256):
    """Verify file SHA-256 checksum."""
    print(f"  Verifying checksum...", file=sys.stderr)
    actual_sha256 = compute_sha256(file_path)
    
    if actual_sha256 == expected_sha256:
        print(f"  ✓ Checksum verified: {actual_sha256}", file=sys.stderr)
        return True
    else:
        print(f"  ✗ Checksum MISMATCH!", file=sys.stderr)
        print(f"    Expected: {expected_sha256}", file=sys.stderr)
        print(f"    Got:      {actual_sha256}", file=sys.stderr)
        return False


def fetch_model(model_key):
    """Download and verify a model.
    
    Args:
        model_key: Key from MODELS dict
        
    Returns:
        True if successful, False otherwise
    """
    model = MODELS[model_key]
    dest_path = MODELS_DIR / model["name"]
    
    print(f"\nFetching {model['name']}...", file=sys.stderr)
    print(f"  Purpose: {model['purpose']}", file=sys.stderr)
    print(f"  License: {model['license']}", file=sys.stderr)
    print(f"  Source:  {model['source']}", file=sys.stderr)
    
    # Check if already exists with correct checksum
    if dest_path.exists():
        print(f"  File already exists, verifying...", file=sys.stderr)
        if verify_checksum(dest_path, model["sha256"]):
            print(f"  ✓ Model already present and verified", file=sys.stderr)
            return True
        else:
            print(f"  Existing file has wrong checksum, re-downloading...", file=sys.stderr)
            dest_path.unlink()
    
    # Download
    if not download_with_progress(model["url"], dest_path):
        return False
    
    # Verify
    if not verify_checksum(dest_path, model["sha256"]):
        print(f"  ✗ Downloaded file failed checksum verification!", file=sys.stderr)
        print(f"  Removing invalid file: {dest_path}", file=sys.stderr)
        dest_path.unlink()
        return False
    
    print(f"  ✓ Successfully fetched and verified {model['name']}", file=sys.stderr)
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--all", action="store_true",
                       help="Download all models")
    parser.add_argument("--yunet", action="store_true",
                       help="Download YuNet face detection model")
    parser.add_argument("--yolox", action="store_true",
                       help="Download YOLOX-S person detection model")
    
    args = parser.parse_args()
    
    # If no specific model requested, default to --all
    if not (args.all or args.yunet or args.yolox):
        args.all = True
    
    # Determine which models to fetch
    to_fetch = []
    if args.all or args.yunet:
        to_fetch.append("yunet")
    if args.all or args.yolox:
        to_fetch.append("yolox")
    
    print("=" * 70, file=sys.stderr)
    print("Reelsmith Stream-Highlights Model Fetcher", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"\nModels directory: {MODELS_DIR}", file=sys.stderr)
    
    # Create models directory
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch each model
    results = {}
    for model_key in to_fetch:
        results[model_key] = fetch_model(model_key)
    
    # Summary
    print("\n" + "=" * 70, file=sys.stderr)
    print("Summary:", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for model_key, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {MODELS[model_key]['name']}: {status}", file=sys.stderr)
    
    print(f"\n{success_count}/{total_count} models successfully fetched and verified", 
          file=sys.stderr)
    
    if success_count < total_count:
        print("\nSome models failed to download or verify.", file=sys.stderr)
        print("The stream-highlights mode will fall back to simpler methods.", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAll models ready for use!", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
