import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

raw_path = "scratch/album_cover/calder_album_raw.jpg"
im = Image.open(raw_path).convert("RGB")

TARGET_SIZE = 3000
im_3000 = im.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
enhancer = ImageEnhance.Sharpness(im_3000)
im_3000 = enhancer.enhance(1.15)

# Self-Titled Cover: Just "CALDER QUINN" with elegant tracking
im_selftitled = im_3000.copy()

title_font_path = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
title_text = "CALDER QUINN"
title_size = 155
font_title = ImageFont.truetype(title_font_path, title_size)
tracking = 32

chars = list(text := title_text)
total_w = 0
char_widths = []
for c in chars:
    bbox = font_title.getbbox(c)
    w = bbox[2] - bbox[0]
    char_widths.append(w)
    total_w += w + tracking
total_w -= tracking

start_x = (TARGET_SIZE - total_w) // 2
cur_x = start_x
y = 150

# Subtle top vignette for readability
vignette = Image.new("RGBA", (TARGET_SIZE, 500), (0, 0, 0, 0))
v_draw = ImageDraw.Draw(vignette)
for vy in range(500):
    alpha = int(150 * (1.0 - (vy / 500.0) ** 1.5))
    v_draw.line([(0, vy), (TARGET_SIZE, vy)], fill=(8, 10, 14, alpha))

im_selftitled.paste(vignette, (0, 0), vignette)
draw = ImageDraw.Draw(im_selftitled)

for idx, c in enumerate(chars):
    # Shadow
    draw.text((cur_x + 5, y + 5), c, font=font_title, fill=(10, 12, 16, 230))
    # Fill
    draw.text((cur_x, y), c, font=font_title, fill=(252, 248, 242))
    cur_x += char_widths[idx] + tracking

out_path = "images/album/Calder_Quinn_Self_Titled_3000x3000.jpg"
im_selftitled.save(out_path, quality=96, subsampling=0)
im_selftitled.save("music/Calder_Quinn_3000x3000.jpg", quality=96, subsampling=0)
im_selftitled.save("images/album/leave_the_light_in_the_hollow_cover.jpg", quality=94, subsampling=0)
im_selftitled.save("images/album/calder_quinn_album_cover.jpg", quality=94, subsampling=0)

# Copy to brain
im_selftitled.save("/Users/benroberts/.gemini/antigravity/brain/d950058e-1dd5-49b0-bc15-a19dd99f7372/Calder_Quinn_Self_Titled_3000x3000.jpg", quality=96, subsampling=0)

print("[✓] Self-titled 3000x3000 album cover created successfully.")
