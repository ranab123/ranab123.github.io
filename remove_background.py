#!/usr/bin/env python3
"""
Script to remove white background outside of frame from images and videos.
Only removes pure white (or near-white) pixels outside the frame polygon.
"""

from PIL import Image, ImageDraw
import os
import sys
import subprocess
import numpy as np

# Directories
INPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/project-gallery"
OUTPUT_DIR = "/Users/ranabanankhah/Desktop/rana-personal-site/assets/images/modified-project-gallery"

# Frame coordinates for horizontal images/videos (883 x 737)
HORIZONTAL_FRAME = [
    (54, 61),    # top-left
    (56, 668),   # bottom-left
    (804, 668),  # bottom-right
    (804, 61),   # top-right
]

# Frame coordinates for vertical images/videos (737 x 883)
VERTICAL_FRAME = [
    (61, 50),    # top-left
    (61, 807),   # bottom-left
    (674, 807),  # bottom-right
    (670, 58),   # top-right
]

# White threshold - pixels with R, G, B all above this are considered "white"
WHITE_THRESHOLD = 250


def is_white_pixel(r, g, b, threshold=WHITE_THRESHOLD):
    """Check if a pixel is white (or near-white)."""
    return r >= threshold and g >= threshold and b >= threshold


def get_frame_points(width, height):
    """Get the appropriate frame points based on dimensions."""
    if width > height:  # Horizontal
        return HORIZONTAL_FRAME, "HORIZONTAL"
    else:  # Vertical
        return VERTICAL_FRAME, "VERTICAL"


def create_mask_image(width, height, frame_points, output_path):
    """
    Create a black and white mask image.
    White = inside frame (keep), Black = outside frame (check for white pixels)
    """
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(frame_points, fill=255)
    mask.save(output_path)
    return output_path


def remove_white_background_image(input_path, output_path):
    """
    Remove white pixels outside the frame polygon from an image.
    """
    # Open image and convert to RGBA
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    
    frame_points, orientation = get_frame_points(width, height)
    print(f"  Detected: {orientation} ({width}x{height})")
    
    # Create a mask image to identify "inside frame" areas
    frame_mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(frame_mask)
    draw.polygon(frame_points, fill=255)
    
    # Convert to numpy arrays for faster pixel manipulation
    img_array = np.array(img)
    mask_array = np.array(frame_mask)
    
    # Process each pixel
    for y in range(height):
        for x in range(width):
            if mask_array[y, x] == 0:  # Outside frame
                r, g, b, a = img_array[y, x]
                if is_white_pixel(r, g, b):
                    img_array[y, x, 3] = 0  # Set alpha to 0
    
    # Convert back to PIL Image and save
    result = Image.fromarray(img_array, 'RGBA')
    result.save(output_path, 'PNG')
    print(f"  Saved: {output_path}")


def remove_white_background_video(input_path, output_path):
    """
    Remove white pixels outside the frame polygon from a video.
    Outputs as WebM with transparency support.
    """
    # First, get video dimensions using ffprobe
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0',
        input_path
    ]
    
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split(','))
    except Exception as e:
        print(f"  ERROR getting video dimensions: {e}")
        return
    
    frame_points, orientation = get_frame_points(width, height)
    print(f"  Detected: {orientation} ({width}x{height})")
    
    # Create a temporary mask image for ffmpeg
    mask_path = "/tmp/frame_mask.png"
    
    # Create inverted mask: white outside frame (areas to make transparent if white)
    # For ffmpeg alphamerge, we need: white = transparent, black = opaque
    # But we only want white PIXELS to become transparent, not everything outside
    
    # Create the mask
    mask = Image.new('L', (width, height), 255)  # Start with white (transparent)
    draw = ImageDraw.Draw(mask)
    draw.polygon(frame_points, fill=0)  # Inside frame = black (opaque)
    mask.save(mask_path)
    
    # Change output to webm for transparency support
    output_webm = output_path.rsplit('.', 1)[0] + '.webm'
    
    # FFmpeg command to remove white background outside the frame
    # Using colorkey to make white pixels transparent, then alphamerge with mask
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-i', mask_path,
        '-filter_complex',
        # Make white pixels transparent using colorkey
        f'[0:v]colorkey=white:0.1:0.1[ck];'
        # Create alpha from mask (invert it so outside is transparent base)
        f'[1:v]format=gray,geq=lum=\'if(gt(lum(X,Y),128),0,255)\':a=255[mask];'
        # Combine: use colorkey result but only apply transparency outside frame
        f'[ck][mask]alphamerge[out]',
        '-map', '[out]',
        '-c:v', 'libvpx-vp9',
        '-pix_fmt', 'yuva420p',
        '-b:v', '2M',
        '-an',  # No audio for now
        output_webm
    ]
    
    try:
        print(f"  Processing video with ffmpeg...")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"  Saved: {output_webm}")
    except subprocess.CalledProcessError as e:
        print(f"  ERROR processing video: {e.stderr.decode() if e.stderr else e}")
        # Try alternative simpler approach - just colorkey
        simple_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', 'colorkey=white:0.1:0.1',
            '-c:v', 'libvpx-vp9',
            '-pix_fmt', 'yuva420p',
            '-b:v', '2M',
            '-an',
            output_webm
        ]
        try:
            print(f"  Trying simpler approach...")
            subprocess.run(simple_cmd, check=True, capture_output=True)
            print(f"  Saved: {output_webm}")
        except subprocess.CalledProcessError as e2:
            print(f"  ERROR: {e2.stderr.decode() if e2.stderr else e2}")


def process_all_files():
    """Process all images and videos in the input directory."""
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all files
    files = os.listdir(INPUT_DIR)
    image_files = [f for f in files if f.lower().endswith('.png') and '-transparent' not in f]
    video_files = [f for f in files if f.lower().endswith(('.mp4', '.mov', '.webm'))]
    
    print(f"Found {len(image_files)} images and {len(video_files)} videos\n")
    
    # Process images
    print("=" * 50)
    print("PROCESSING IMAGES")
    print("=" * 50)
    for filename in image_files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        print(f"\nProcessing: {filename}")
        try:
            remove_white_background_image(input_path, output_path)
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Process videos
    print("\n" + "=" * 50)
    print("PROCESSING VIDEOS")
    print("=" * 50)
    for filename in video_files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        print(f"\nProcessing: {filename}")
        try:
            remove_white_background_video(input_path, output_path)
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Output saved to: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--images-only":
        # Process only images
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        files = os.listdir(INPUT_DIR)
        image_files = [f for f in files if f.lower().endswith('.png') and '-transparent' not in f]
        print(f"Processing {len(image_files)} images only...\n")
        for filename in image_files:
            input_path = os.path.join(INPUT_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename)
            print(f"Processing: {filename}")
            try:
                remove_white_background_image(input_path, output_path)
            except Exception as e:
                print(f"  ERROR: {e}")
    else:
        process_all_files()
