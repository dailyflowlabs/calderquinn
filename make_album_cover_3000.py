import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

raw_path = "scratch/album_cover/calder_album_raw.jpg"
im = Image.open(raw_path).convert("RGB")

# 1. High-fidelity upscale to 3000x3000
TARGET_SIZE = 3000
im_3000 = im.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)

# Subtle sharpness enhancement for 3000x3000 detail
enhancer = ImageEnhance.Sharpness(im_3000)
im_3000 = enhancer.enhance(1.15)

# Save pure photography master 3000x3000
out_art_only = "images/album/Calder_Quinn_Leave_the_Light_in_the_Hollow_ArtOnly_3000x3000.jpg"
im_3000.save(out_art_only, quality=96, subsampling=0)
print(f"[✓] Saved Art-Only 3000x3000 to {out_art_only}")

# 2. Build Typography Master (Calder Quinn - Leave the Light in the Hollow)
im_typed = im_3000.copy()
draw = ImageDraw.Draw(im_typed)

# Find suitable fonts
title_font_path = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
sub_font_path = "/System/Library/Fonts/Supplemental/Georgia.ttf"

# Top title: CALDER QUINN
# We will draw with letter-spacing (tracking)
title_text = "CALDER QUINN"
title_size = 135
font_title = ImageFont.truetype(title_font_path, title_size)

sub_text = "LEAVE THE LIGHT IN THE HOLLOW"
sub_size = 62
font_sub = ImageFont.truetype(sub_font_path, sub_size)

def draw_tracked_text_center(draw, y, text, font, tracking, fill_color, shadow_color=None, shadow_offset=(3, 3)):
    chars = list(text)
    # Calculate total width with tracking
    total_w = 0
    char_widths = []
    for c in chars:
        bbox = font.getbbox(c)
        w = bbox[2] - bbox[0]
        char_widths.append(w)
        total_w += w + tracking
    total_w -= tracking  # remove last tracking
    
    start_x = (TARGET_SIZE - total_w) // 2
    cur_x = start_x
    
    for idx, c in enumerate(chars):
        if shadow_color:
            draw.text((cur_x + shadow_offset[0], y + shadow_offset[1]), c, font=font, fill=shadow_color)
        draw.text((cur_x, y), c, font=font, fill=fill_color)
        cur_x += char_widths[idx] + tracking

# Draw subtle top vignette for contrast
vignette = Image.new("RGBA", (TARGET_SIZE, 450), (0, 0, 0, 0))
v_draw = ImageDraw.Draw(vignette)
for y in range(450):
    alpha = int(140 * (1.0 - (y / 450.0) ** 1.5))
    v_draw.line([(0, y), (TARGET_SIZE, y)], fill=(8, 10, 14, alpha))

im_typed.paste(vignette, (0, 0), vignette)
draw = ImageDraw.Draw(im_typed)

# Draw Calder Quinn (top center)
draw_tracked_text_center(
    draw, 
    y=120, 
    text=title_text, 
    font=font_title, 
    tracking=26, 
    fill_color=(250, 246, 238), 
    shadow_color=(10, 12, 16, 220), 
    shadow_offset=(4, 4)
)

# Draw Subtitle with amber accent
draw_tracked_text_center(
    draw, 
    y=275, 
    text=sub_text, 
    font=font_sub, 
    tracking=18, 
    fill_color=(235, 175, 100), 
    shadow_color=(10, 12, 16, 200), 
    shadow_offset=(3, 3)
)

out_master = "images/album/Calder_Quinn_Leave_the_Light_in_the_Hollow_3000x3000.jpg"
im_typed.save(out_master, quality=96, subsampling=0)
print(f"[✓] Saved Official Master 3000x3000 with Typography to {out_master}")

# Copy to music/ directory for distribution
im_typed.save("music/Calder_Quinn_Leave_the_Light_in_the_Hollow_3000x3000.jpg", quality=96, subsampling=0)
# Update web cover image
im_typed.save("images/album/leave_the_light_in_the_hollow_cover.jpg", quality=92, subsampling=0)
print(f"[✓] Updated web assets and music distribution cover.")

