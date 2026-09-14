import os
import zipfile
from PIL import Image

scratch_dir = "scratch/calder_dataset"
os.makedirs(scratch_dir, exist_ok=True)

# 1. Base Turnaround Images
base_images = {
    "images/01_calder_front_anchor.jpg": "01_calder_front_portrait.jpg",
    "images/02_calder_three_quarter.jpg": "02_calder_three_quarter.jpg",
    "images/03_calder_side_profile.jpg": "03_calder_side_profile.jpg",
    "images/04_calder_full_body.jpg": "04_calder_full_body.jpg",
    "images/05_calder_singing.jpg": "05_calder_singing_performance.jpg",
}

for src, name in base_images.items():
    img = Image.open(src)
    dest = os.path.join(scratch_dir, name)
    img.save(dest, quality=95)
    print(f"[✓] Copied {src} -> {dest} ({img.size})")

# 2. Targeted Crops for LoRA Face & Detail Learning
# 01 Front Anchor (896 x 1200) - Tight Face / Hazel Eyes & Stubble
img_01 = Image.open("images/01_calder_front_anchor.jpg")
crop_face = img_01.crop((230, 180, 670, 620))
crop_face.save(os.path.join(scratch_dir, "06_calder_tight_face_eyes.jpg"), quality=95)

# 02 Three Quarter Porch (896 x 1200) - 3/4 Face & Navy Cap
img_02 = Image.open("images/02_calder_three_quarter.jpg")
crop_34 = img_02.crop((230, 160, 710, 640))
crop_34.save(os.path.join(scratch_dir, "07_calder_three_quarter_face.jpg"), quality=95)

# 03 Side Profile (896 x 1200) - Profile Jawline, Ear & Cap
img_03 = Image.open("images/03_calder_side_profile.jpg")
crop_profile = img_03.crop((220, 140, 700, 620))
crop_profile.save(os.path.join(scratch_dir, "08_calder_profile_jawline.jpg"), quality=95)

# 05 Singing Barn (896 x 1200) - Passionate Vocal Expression
img_05 = Image.open("images/05_calder_singing.jpg")
crop_singing = img_05.crop((240, 60, 720, 540))
crop_singing.save(os.path.join(scratch_dir, "09_calder_singing_expression.jpg"), quality=95)

# 01 Torso & Guitar (896 x 1200) - Workwear, Hands & Acoustic Guitar
crop_torso = img_01.crop((120, 400, 780, 1060))
crop_torso.save(os.path.join(scratch_dir, "10_calder_chore_coat_guitar.jpg"), quality=95)

# 3. Create Training Dataset ZIP
zip_path = "scratch/calder_quinn_flux_dataset.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for fname in sorted(os.listdir(scratch_dir)):
        if fname.endswith(".jpg"):
            fpath = os.path.join(scratch_dir, fname)
            z.write(fpath, arcname=f"calder_dataset/{fname}")
            print(f"    Added to zip: {fname}")

zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
print(f"\n[🎉] Successfully created {zip_path} ({zip_size_mb:.2f} MB with 10 targeted reference images)")
