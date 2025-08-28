import sys
import os
import hashlib
import subprocess
import logging
from PIL import Image, UnidentifiedImageError

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension
    
def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        print(f"Error getting file size: {e}", file=sys.stderr)
        return -1

def get_sdata_version(file_path, file_size):
    if not file_path.lower().endswith('.sdat'):
        return "NA"

    if file_size < 16:
        return "0"
    
    version_signatures = {
        b"SDATA 4.0.0.W\x00\x00\x00": "4.0",
        b"SDATA 2.4.0.W\x00\x00\x00": "2.4",
        b"SDATA 2.2.0.W\x00\x00\x00": "2.2",
        b"SDATA 3.3.0.W\x00\x00\x00": "3.3",
    }

    try:
        with open(file_path, 'rb') as file:
            file.seek(-16, 2)
            end_bytes = file.read(16)
            for signature, version in version_signatures.items():
                if end_bytes == signature:
                    return version
            return "0"
    except Exception as e:
        print(f"Error checking SDATA version: {e}", file=sys.stderr)
        return "ERROR"

def calculate_sha1(file_path):
    try:
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                sha1.update(chunk)
        return sha1.hexdigest().upper() 
    except Exception as e:
        print(f"Error calculating SHA1: {e}", file=sys.stderr)
        return "ERROR"

def check_file_for_missing_bytes(file_path):
    try:
        with open(file_path, 'rb') as file:
            file.seek(0, 2) 
            file_size = file.tell()
            remainder = file_size % 16
            if remainder != 0:
                missing_bytes = 16 - remainder
                return missing_bytes
            else:
                return 0
    except Exception as e:
        print(f"Error checking for missing bytes: {e}", file=sys.stderr)
        return -1
        
        
def is_image_corrupt(filepath):
    try:
        with Image.open(filepath) as img:
            img.verify()  # Verifies the integrity of the file without loading it.
        with Image.open(filepath) as img:
            img.load()    # Attempt to load the image to catch deeper corruptions.
    except (IOError, SyntaxError, UnidentifiedImageError, ValueError, AttributeError):
        return 1  # Corrupt image
    return 0  # Image is okay

# List of specific errors to look for
specific_errors = [
    "moov atom not found",
    "contradictory STSC and STCO",
    "error reading header",
    "Invalid data found when processing input",
    "corrupt",
    "error",
    "invalid",
    "malformed",
    "missing",
    "missing picture in access unit with size 5",
    "partial file"
]

def log_and_print(message, log_only=True):
    logging.info(message)

def extract_error_summary(output):
    detailed_lines = []

    for line in output.splitlines():
        for error in specific_errors:
            if error.lower() in line.lower():
                if line not in detailed_lines:  # Prevent duplicate lines
                    detailed_lines.append(line)
    return detailed_lines

def analyze_video(file_path, ffprobe_path):
    
    cmd = [ffprobe_path, '-v', 'error', '-show_entries', 'format', '-show_entries', 'stream', '-show_entries', 'frame', '-print_format', 'json', file_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    detailed_lines = extract_error_summary(result.stderr)
    
    if detailed_lines:
        relative_path = os.path.relpath(file_path, os.getcwd())
        log_and_print(f"{relative_path}:")
        
        if len(detailed_lines) == 1 and "missing picture in access unit with size 5" in detailed_lines[0]:
            log_and_print("Only error found is 'missing picture in access unit with size 5'. Skipping...")
            log_and_print("-----------------------------------------------")
            return 0  # Return 0 if this is the only error

        for line in detailed_lines:
            log_and_print(f"{line}")
        log_and_print("-----------------------------------------------")
        return 1  # Return 1 for other errors

    return 0  # Return 0 if no errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: file_analysis.exe <file_path> [ffprobe_path]", file=sys.stderr)
        sys.exit(1)
        
    file_path = sys.argv[1]
    file_extension = get_file_extension(file_path)
    file_size = get_file_size(file_path)
    sdata_version = get_sdata_version(file_path, file_size)
    sha1 = calculate_sha1(file_path)
    missing_bytes = check_file_for_missing_bytes(file_path)
    
    image_corruption_check = "NA"
    if file_extension.lower() in ['.png', '.jpg', '.jpeg', '.dds']:
     image_corruption_check = is_image_corrupt(file_path)
    
    # Default ffprobe path within a "bin" directory in the current directory
    current_dir = os.getcwd()
    default_ffprobe_path = os.path.join(current_dir, 'bin', 'ffprobe.exe')
    
    # Check if an alternative ffprobe path is provided and valid; otherwise, use the default
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        ffprobe_path = sys.argv[2]
    else:
        ffprobe_path = default_ffprobe_path
    
    video_corruption_check = "NA"
    if file_extension.lower() in ['.mp4', '.m4v']:
        # Set up logging only if an MP4 file is found
        log_file_path = 'log_VIDEO_ANALYSIS.log'

        logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(message)s')

        video_corruption_check = analyze_video(file_path, ffprobe_path)
        
    if any(check == -1 for check in [file_size, missing_bytes]) or any(check == "ERROR" for check in [sdata_version, sha1]):
        sys.exit(1)

    print(f"{file_extension}\t{file_size}\t{sdata_version}\t{sha1}\t{missing_bytes}\t{image_corruption_check}\t{video_corruption_check}")