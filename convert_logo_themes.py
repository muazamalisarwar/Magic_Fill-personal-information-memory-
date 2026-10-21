import sys
import os
from PIL import Image, ImageEnhance, ImageOps

def process_logo(input_path, output_dir=None):
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_path)) or "."

    # Load image in RGBA
    img = Image.open(input_path).convert("RGBA")
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Extract channels
    r, g, b, a = img.split()

    # If alpha is completely opaque (e.g. JPG), create alpha from background luminance
    ext = os.path.splitext(input_path)[1].lower()
    has_meaningful_alpha = any(pixel < 250 for pixel in a.getdata()[:1000])

    # -------------------------------------------------------------
    # 1. WHITE MODE (Optimized for White / Light Backgrounds)
    # -------------------------------------------------------------
    # A) Color-enhanced for light mode: Deep contrast, sharp edges
    enhancer_color = ImageEnhance.Color(img)
    img_vibrant = enhancer_color.enhance(1.25)
    enhancer_contrast = ImageEnhance.Contrast(img_vibrant)
    img_light_theme = enhancer_contrast.enhance(1.15)
    light_mode_color_path = os.path.join(output_dir, f"{base_name}_for_white_mode.png")
    img_light_theme.save(light_mode_color_path, "PNG")
    print(f"✓ White Mode (Color):      {light_mode_color_path}")

    # B) Monochrome Black (Pure black silhouette with alpha mask)
    # Convert luminance to alpha or use existing alpha
    grayscale = img.convert("L")
    if not has_meaningful_alpha:
        # Invert grayscale so dark pixels become opaque
        alpha_mask = ImageOps.invert(grayscale)
    else:
        alpha_mask = a

    black_img = Image.new("RGBA", img.size, (15, 23, 42, 255)) # Dark slate/black
    black_img.putalpha(alpha_mask)
    mono_black_path = os.path.join(output_dir, f"{base_name}_monochrome_black.png")
    black_img.save(mono_black_path, "PNG")
    print(f"✓ White Mode (Monochrome): {mono_black_path}")

    # -------------------------------------------------------------
    # 2. BLACK MODE (Optimized for Black / Dark Backgrounds)
    # -------------------------------------------------------------
    # A) Color-enhanced for dark mode: Luminous glow, bright accents
    enhancer_brightness = ImageEnhance.Brightness(img)
    img_bright = enhancer_brightness.enhance(1.12)
    enhancer_contrast_dark = ImageEnhance.Contrast(img_bright)
    img_dark_theme = enhancer_contrast_dark.enhance(1.1)
    dark_mode_color_path = os.path.join(output_dir, f"{base_name}_for_black_mode.png")
    img_dark_theme.save(dark_mode_color_path, "PNG")
    print(f"✓ Black Mode (Color):      {dark_mode_color_path}")

    # B) Monochrome White (Pure white silhouette with alpha mask)
    if not has_meaningful_alpha:
        # Bright pixels become opaque white
        alpha_mask_white = grayscale
    else:
        alpha_mask_white = a

    white_img = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_img.putalpha(alpha_mask_white)
    mono_white_path = os.path.join(output_dir, f"{base_name}_monochrome_white.png")
    white_img.save(mono_white_path, "PNG")
    print(f"✓ Black Mode (Monochrome): {mono_white_path}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"automark-v1.0.0\public\images\magic_fill_logo.png"
    process_logo(target)
