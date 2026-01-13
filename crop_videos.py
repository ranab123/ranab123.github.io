#!/usr/bin/env python3
"""
Script to crop videos to frame boundaries.
Uses ffmpeg for fast cropping.
"""

import os
import subprocess

INPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/project-gallery"
OUTPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/modified-videos"

# Vertical crop coordinates (for videos where height > width)
# Based on 737x883 base size
VERTICAL_CROP = {
    'x': 54,
    'y': 50,
    'w': 683 - 54,  # 629
    'h': 819 - 50,  # 769
    'base_w': 737,
    'base_h': 883,
}

# Horizontal crop coordinates (for videos where width > height)
# Based on 883x737 base size
HORIZONTAL_CROP = {
    'x': 50,
    'y': 54,
    'w': 820 - 50,  # 770
    'h': 683 - 54,  # 629
    'base_w': 883,
    'base_h': 737,
}


def get_video_dimensions(video_path):
    """Get video width and height using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    width, height = map(int, result.stdout.strip().split(','))
    return width, height


def crop_video(input_path, output_path):
    """Crop a video to the frame boundaries."""
    width, height = get_video_dimensions(input_path)
    print(f"  Dimensions: {width}x{height}")
    
    # Determine orientation and get crop params
    if height > width:  # Vertical
        crop = VERTICAL_CROP
        orientation = "VERTICAL"
    else:  # Horizontal
        crop = HORIZONTAL_CROP
        orientation = "HORIZONTAL"
    
    print(f"  Orientation: {orientation}")
    
    # Scale crop coordinates to actual video size
    scale_x = width / crop['base_w']
    scale_y = height / crop['base_h']
    
    crop_x = int(crop['x'] * scale_x)
    crop_y = int(crop['y'] * scale_y)
    crop_w = int(crop['w'] * scale_x)
    crop_h = int(crop['h'] * scale_y)
    
    print(f"  Crop: x={crop_x}, y={crop_y}, w={crop_w}, h={crop_h}")
    
    # Output as MP4 (no transparency needed since we're just cropping)
    output_mp4 = output_path.rsplit('.', 1)[0] + '.mp4'
    
    # FFmpeg crop command
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', f'crop={crop_w}:{crop_h}:{crop_x}:{crop_y}',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-an',  # No audio
        output_mp4
    ]
    
    print(f"  Cropping...")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Saved: {output_mp4}")
    return output_mp4


def process_all_videos():
    """Process all video files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    video_extensions = ('.mp4', '.mov', '.webm', '.avi')
    video_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(video_extensions)]
    
    print(f"Found {len(video_files)} videos to process\n")
    
    for i, filename in enumerate(video_files):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        print(f"\n[{i + 1}/{len(video_files)}] Processing: {filename}")
        
        try:
            crop_video(input_path, output_path)
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: {e.stderr.decode() if e.stderr else e}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Output saved to: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = os.path.join(OUTPUT_DIR, os.path.basename(input_file))
        print(f"Processing single file: {input_file}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        crop_video(input_file, output_file)
    else:
        process_all_videos()

