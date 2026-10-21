#!/usr/bin/env python3
"""
Magic Fill - Universal Logo Converter for White Mode & Black Mode
Converts any logo (PNG, JPG, WEBP) into optimized assets for:
  - White Mode (Light Backgrounds): High-contrast color with transparent background & Monochrome Dark (#0F172A)
  - Black Mode (Dark Backgrounds): Luminous neon glow with transparent background & Monochrome Pure White (#FFFFFF)
"""

import sys
import os
import argparse
from PIL import Image, ImageEnhance, ImageOps

def extract_alpha_if_dark_bg(img: Image.Image) -> Image.Image:
    """
    If the logo has a dark/black solid background (like AI-generated square icons),
    intelligently key out the dark background while preserving glowing edges, sparks, and transparency.
    """
    img = img.convert("RGBA")
    r, g, b, orig_a = img.split()
    gray = img.convert("L")
    
    # Sample border pixels to detect if background is dark
    w, h = img.size
    border_samples = [
        gray.getpixel((w//2, 10)),
        gray.getpixel((w//2, h-10)),
        gray.getpixel((10, h//2)),
        gray.getpixel((w-10, h//2)),
        gray.getpixel((w//4, h//4)),
        gray.getpixel((3*w//4, h//4))
    ]
    avg_border_lum = sum(border_samples) / len(border_samples)
    
    # If border is relatively dark (< 60) and mostly opaque, extract transparent foreground
    if avg_border_lum < 65 and min(orig_a.getextrema()) > 200:
        bg_thresh = max(35, int(avg_border_lum + 8))
        high_thresh = bg_thresh + 45
        
        lum_bytes = gray.tobytes()
        orig_a_bytes = orig_a.tobytes()
        new_a = bytearray(len(lum_bytes))
        
        for i in range(len(lum_bytes)):
            l = lum_bytes[i]
            oa = orig_a_bytes[i]
            if oa == 0 or l <= bg_thresh:
                new_a[i] = 0
            elif l >= high_thresh:
                new_a[i] = oa
            else:
                factor = (l - bg_thresh) / (high_thresh - bg_thresh)
                new_a[i] = int(oa * factor)
                
        # Clean corner artifacts
        for y in range(h):
            for x in range(w):
                if (x + y < 130) or (x < 25) or (y < 25) or (x > w - 25) or (y > h - 25):
                    idx = y * w + x
                    if new_a[idx] < 75:
                        new_a[idx] = 0
                        
        clean_alpha = Image.frombytes("L", (w, h), bytes(new_a))
        img.putalpha(clean_alpha)
        
    return img

def convert_for_white_mode(img: Image.Image, base_output_path: str):
    """
    White Mode (Light Theme / White Background):
    1. Color Version: Deepened contrast & high color saturation on transparent background
    2. Monochrome Dark: Elegant slate-black (#0F172A) silhouette
    """
    processed = extract_alpha_if_dark_bg(img)
    _, _, _, a = processed.split()
    
    # 1. Vibrant Color on Transparent BG
    enhancer_contrast = ImageEnhance.Contrast(processed)
    img_contrast = enhancer_contrast.enhance(1.25)
    enhancer_color = ImageEnhance.Color(img_contrast)
    img_vibrant = enhancer_color.enhance(1.3)
    
    color_path = f"{base_output_path}_white_mode.png"
    img_vibrant.save(color_path, "PNG")
    print(f"  [OK] White Mode (Vibrant Color):   {color_path}")
    
    # 2. Monochrome Slate Black (#0F172A)
    dark_slate = Image.new("RGBA", processed.size, (15, 23, 42, 255))
    dark_slate.putalpha(a)
    mono_path = f"{base_output_path}_white_mode_mono.png"
    dark_slate.save(mono_path, "PNG")
    print(f"  [OK] White Mode (Monochrome Dark): {mono_path}")
    
    return color_path, mono_path

def convert_for_black_mode(img: Image.Image, base_output_path: str):
    """
    Black Mode (Dark Theme / Black Background):
    1. Neon Color Version: Brightened highlights & luminous bloom on transparent background
    2. Monochrome White: Crisp pure white (#FFFFFF) silhouette
    """
    processed = extract_alpha_if_dark_bg(img)
    _, _, _, a = processed.split()
    
    # 1. Glowing Neon Color on Transparent BG
    enhancer_bright = ImageEnhance.Brightness(processed)
    img_bright = enhancer_bright.enhance(1.2)
    enhancer_contrast = ImageEnhance.Contrast(img_bright)
    img_neon = enhancer_contrast.enhance(1.15)
    enhancer_color = ImageEnhance.Color(img_neon)
    img_neon = enhancer_color.enhance(1.2)
    
    color_path = f"{base_output_path}_black_mode.png"
    img_neon.save(color_path, "PNG")
    print(f"  [OK] Black Mode (Neon Color):      {color_path}")
    
    # 2. Monochrome Pure White (#FFFFFF)
    pure_white = Image.new("RGBA", processed.size, (255, 255, 255, 255))
    pure_white.putalpha(a)
    mono_path = f"{base_output_path}_black_mode_mono.png"
    pure_white.save(mono_path, "PNG")
    print(f"  [OK] Black Mode (Monochrome White): {mono_path}")
    
    return color_path, mono_path

def main():
    parser = argparse.ArgumentParser(description="Convert any logo for White Mode and Black Mode.")
    parser.add_argument("input", nargs="?", default="for_dark_mode.jpg", help="Path to the input logo image (e.g. for_dark_mode.jpg)")
    parser.add_argument("--mode", choices=["white", "black", "both"], default="both", 
                        help="Convert for: 'white' (light bg), 'black' (dark bg), or 'both' (default)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)
        
    img = Image.open(args.input)
    base_name = os.path.splitext(args.input)[0]
    
    print(f"\nProcessing logo: '{args.input}' (Size: {img.size[0]}x{img.size[1]})")
    
    if args.mode in ("white", "both"):
        print("\nConverting for White Mode (Light Backgrounds):")
        convert_for_white_mode(img, base_name)
        
    if args.mode in ("black", "both"):
        print("\nConverting for Black Mode (Dark Backgrounds):")
        convert_for_black_mode(img, base_name)
        
    print("\nConversion complete! All output files saved with full transparency.\n")

if __name__ == "__main__":
    main()
