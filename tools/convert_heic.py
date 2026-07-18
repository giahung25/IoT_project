#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

def convert_heic_to_jpg(directory, remove_source=False):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    # Find HEIC files
    heic_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.heic', '.heif')):
                heic_files.append(os.path.join(root, file))

    if not heic_files:
        print("No HEIC/HEIF files found in the specified directory.")
        return

    print(f"Found {len(heic_files)} HEIC/HEIF file(s) to convert.")
    
    success_count = 0
    fail_count = 0

    for idx, heic_path in enumerate(heic_files, 1):
        # Generate output path by replacing extension with .jpg
        base_path, _ = os.path.splitext(heic_path)
        jpg_path = base_path + ".jpg"
        
        print(f"[{idx}/{len(heic_files)}] Converting: {os.path.basename(heic_path)} -> {os.path.basename(jpg_path)}... ", end="", flush=True)
        
        # Run heif-convert command
        cmd = ["heif-convert", heic_path, jpg_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print("SUCCESS")
            success_count += 1
            
            # Optionally remove source file
            if remove_source:
                os.remove(heic_path)
        except subprocess.CalledProcessError as e:
            print("FAILED")
            print(f"  Error details: {e.stderr.strip() or e.stdout.strip()}")
            fail_count += 1
        except Exception as e:
            print("FAILED")
            print(f"  Error: {e}")
            fail_count += 1

    print("\n--- Conversion Summary ---")
    print(f"Successfully converted: {success_count} file(s)")
    if fail_count > 0:
        print(f"Failed to convert: {fail_count} file(s)")
    if remove_source:
        print("Original HEIC/HEIF files have been deleted.")
    else:
        print("Original HEIC/HEIF files have been kept.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert HEIC/HEIF images to JPG using heif-convert.")
    parser.add_argument("directory", nargs="?", default="data/Dữ_liệu_Nấm_non", 
                        help="Target directory containing HEIC files (default: data/Dữ_liệu_Nấm_non)")
    parser.add_argument("--remove-source", action="store_true", 
                        help="Delete the original HEIC files after successful conversion")
    
    args = parser.parse_args()
    convert_heic_to_jpg(args.directory, args.remove_source)
