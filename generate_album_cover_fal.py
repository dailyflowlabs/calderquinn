import os
import sys
import json
import urllib.request
import fal_client
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FAL_KEY = "347f2fd3-fdd2-4fdc-8ac8-f35f96b66d73:d60ae62cd8ed31b35eb00dc6cbcdbf4e"
os.environ["FAL_KEY"] = FAL_KEY

lora_result_file = "scratch/calder_lora_result.json"
with open(lora_result_file) as f:
    lora_data = json.load(f)

lora_url = lora_data["diffusers_lora_file"]["url"]
print(f"[*] Loaded Calder Quinn FLUX LoRA: {lora_url[:60]}...")

out_dir = "scratch/album_cover"
os.makedirs(out_dir, exist_ok=True)
os.makedirs("images/album", exist_ok=True)
os.makedirs("music", exist_ok=True)

TRIGGER = "calder_quinn"
OUTFIT = "wearing a vintage faded dark olive green canvas chore jacket over a dark heather charcoal grey crewneck t-shirt, and vintage worn faded brown canvas baseball cap with distressed curved brim pulled low"

prompt = (
    f"Master album cover photograph for {TRIGGER}'s debut record 'Leave the Light in the Hollow'. "
    f"Cinematic medium portrait of {TRIGGER} with weathered handsome masculine features, heavy 5 o'clock shadow stubble beard, "
    f"dark hair peeking out beneath his cap. He is {OUTFIT}. "
    f"Calder is seated on the dropped tailgate of a dusty 1970s vintage pickup truck on an Appalachian mountain gravel road at deep blue twilight. "
    f"In his hands, he loosely holds a weathered vintage Martin D-28 acoustic guitar. "
    f"An old brass kerosene lantern rests on the truck tailgate, casting warm golden amber light and glowing rim reflections across his jawline, jacket texture, and hands. "
    f"In the background, mist and fog roll through the dark Appalachian pines and rolling hollow ridges under a stormy twilight dusk sky. "
    f"Raw, evocative 35mm film grain, moody Americana soul, rich contrast, masterpiece square album cover art."
)

print("[*] Generating master album cover image with fal.ai FLUX LoRA...", flush=True)
res = fal_client.subscribe(
    "fal-ai/flux-lora",
    arguments={
        "prompt": prompt,
        "loras": [
            {
                "path": lora_url,
                "scale": 0.95
            }
        ],
        "image_size": "square_hd",
        "num_inference_steps": 40,
        "guidance_scale": 4.0,
        "enable_safety_checker": False
    }
)

img_url = res["images"][0]["url"]
raw_img_path = f"{out_dir}/calder_album_raw.jpg"
print(f"[✓] Generated! Downloading from {img_url[:60]}...")
urllib.request.urlretrieve(img_url, raw_img_path)
print(f"[✓] Saved raw generated cover to {raw_img_path}")

