#!/usr/bin/env python3
"""
Script to remove white background outside of frame from videos.
Processes each frame individually using the same logic as the image script.
Outputs as WebM with transparency support.
"""

from PIL import Image, ImageDraw
import os
import sys
import subprocess
import tempfile
import shutil
import numpy as np

# Directories
INPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/project-gallery"
OUTPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/modified-videos"

# Frame coordinates for horizontal videos (width > height)
# These need to be scaled based on actual video dimensions
HORIZONTAL_FRAME_BASE = [
    (54, 61),    # top-left
    (56, 668),   # bottom-left
    (804, 668),  # bottom-right
    (804, 61),   # top-right
]
HORIZONTAL_BASE_SIZE = (883, 737)

# Frame coordinates for vertical videos (height > width)
VERTICAL_FRAME_BASE = [
    (61, 50),    # top-left
    (61, 807),   # bottom-left
    (674, 807),  # bottom-right
    (670, 58),   # top-right
]
VERTICAL_BASE_SIZE = (737, 883)

# White threshold
WHITE_THRESHOLD = 250


def scale_frame_points(base_points, base_size, actual_size):
    """Scale frame coordinates from base size to actual video size."""
    scale_x = actual_size[0] / base_size[0]
    scale_y = actual_size[1] / base_size[1]
    return [(int(x * scale_x), int(y * scale_y)) for x, y in base_points]


def is_white_pixel(r, g, b, threshold=WHITE_THRESHOLD):
    """Check if a pixel is white (or near-white)."""
    return r >= threshold and g >= threshold and b >= threshold


def process_frame(img, frame_points):
    """
    Remove white pixels outside the frame polygon from a single frame.
    Returns processed RGBA image.
    """
    img = img.convert("RGBA")
    width, height = img.size
    
    # Create frame mask
    frame_mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(frame_mask)
    draw.polygon(frame_points, fill=255)
    
    # Convert to numpy for faster processing
    img_array = np.array(img)
    mask_array = np.array(frame_mask)
    
    # Process pixels outside frame
    for y in range(height):
        for x in range(width):
            if mask_array[y, x] == 0:  # Outside frame
                r, g, b, a = img_array[y, x]
                if is_white_pixel(r, g, b):
                    img_array[y, x, 3] = 0  # Make transparent
    
    return Image.fromarray(img_array, 'RGBA')


def get_video_info(video_path):
    """Get video dimensions and frame rate using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    parts = result.stdout.strip().split(',')
    width = int(parts[0])
    height = int(parts[1])
    # Parse frame rate (might be like "30/1" or "29.97")
    fps_str = parts[2]
    if '/' in fps_str:
        num, den = fps_str.split('/')
        fps = float(num) / float(den)
    else:
        fps = float(fps_str)
    return width, height, fps


def process_video(input_path, output_path):
    """
    Process a video by removing white background from each frame.
    """
    print(f"  Getting video info...")
    width, height, fps = get_video_info(input_path)
    print(f"  Dimensions: {width}x{height}, FPS: {fps:.2f}")
    
    # Determine orientation and get scaled frame points
    if width > height:  # Horizontal
        frame_points = scale_frame_points(HORIZONTAL_FRAME_BASE, HORIZONTAL_BASE_SIZE, (width, height))
        print(f"  Orientation: HORIZONTAL")
    else:  # Vertical
        frame_points = scale_frame_points(VERTICAL_FRAME_BASE, VERTICAL_BASE_SIZE, (width, height))
        print(f"  Orientation: VERTICAL")
    
    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp()
    frames_input = os.path.join(temp_dir, "input")
    frames_output = os.path.join(temp_dir, "output")
    os.makedirs(frames_input)
    os.makedirs(frames_output)
    
    try:
        # Extract frames
        print(f"  Extracting frames...")
        extract_cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', f'fps={fps}',
            os.path.join(frames_input, 'frame_%05d.png')
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True)
        
        # Get list of frames
        frame_files = sorted([f for f in os.listdir(frames_input) if f.endswith('.png')])
        total_frames = len(frame_files)
        print(f"  Processing {total_frames} frames...")
        
        # Process each frame
        for i, frame_file in enumerate(frame_files):
            if (i + 1) % 30 == 0 or i == 0 or i == total_frames - 1:
                print(f"    Frame {i + 1}/{total_frames}")
            
            input_frame_path = os.path.join(frames_input, frame_file)
            output_frame_path = os.path.join(frames_output, frame_file)
            
            # Load, process, and save frame
            img = Image.open(input_frame_path)
            processed = process_frame(img, frame_points)
            processed.save(output_frame_path, 'PNG')
        
        # Reassemble into WebM with transparency
        print(f"  Reassembling video...")
        output_webm = output_path.rsplit('.', 1)[0] + '.webm'
        
        reassemble_cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', os.path.join(frames_output, 'frame_%05d.png'),
            '-c:v', 'libvpx-vp9',
            '-pix_fmt', 'yuva420p',
            '-b:v', '2M',
            '-auto-alt-ref', '0',
            output_webm
        ]
        subprocess.run(reassemble_cmd, check=True, capture_output=True)
        
        print(f"  Saved: {output_webm}")
        return output_webm
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)


def process_all_videos():
    """Process all video files in the input directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    video_extensions = ('.mp4', '.mov', '.webm', '.avi')
    video_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(video_extensions)]
    
    print(f"Found {len(video_files)} videos to process\n")
    
    for i, filename in enumerate(video_files):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        print(f"\n[{i + 1}/{len(video_files)}] Processing: {filename}")
        
        try:
            process_video(input_path, output_path)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Output saved to: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Process a specific file
        input_file = sys.argv[1]
        output_file = os.path.join(OUTPUT_DIR, os.path.basename(input_file))
        print(f"Processing single file: {input_file}")
        process_video(input_file, output_file)
    else:
        process_all_videos()


