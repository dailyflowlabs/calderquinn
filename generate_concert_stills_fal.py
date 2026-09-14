import os
import sys
import json
import urllib.request
import fal_client

FAL_KEY = "347f2fd3-fdd2-4fdc-8ac8-f35f96b66d73:d60ae62cd8ed31b35eb00dc6cbcdbf4e"
os.environ["FAL_KEY"] = FAL_KEY

lora_result_file = "scratch/calder_lora_result.json"
if not os.path.exists(lora_result_file):
    print(f"[-] LoRA weights not ready yet at {lora_result_file}")
    sys.exit(1)

with open(lora_result_file) as f:
    lora_data = json.load(f)

lora_url = lora_data["diffusers_lora_file"]["url"]
print(f"[*] Loaded Calder Quinn FLUX LoRA: {lora_url[:60]}...")

out_dir = "scratch/concert_stills"
os.makedirs(out_dir, exist_ok=True)

TRIGGER = "calder_quinn"
OUTFIT = "wearing the exact same faded dark olive green canvas chore jacket over a dark heather charcoal grey crewneck t-shirt, and vintage worn faded brown canvas baseball cap with distressed curved brim pulled low"
LIGHTING = "live outdoor summer festival night concert stage, warm amber tungsten spotlights and golden rim lights cutting through soft atmospheric stage haze, black Shure SM58 stage microphone on chrome stand, 9:16 vertical, authentic 35mm concert documentary photography"

stills = [
    {
        "name": "cut1_front_kitchen.jpg",
        "prompt": f"A raw 9:16 vertical concert photograph of {TRIGGER} performing live on an outdoor festival stage. Calder has rugged masculine features with heavy 5 o'clock shadow stubble beard, tousled dark wavy hair peeking under his cap. He is {OUTFIT}. Front waist-up medium shot, leaning in close to the chrome stage microphone, singing with quiet intense grit into the mic. {LIGHTING}."
    },
    {
        "name": "cut3_side_light.jpg",
        "prompt": f"A dramatic 9:16 vertical 90-degree side profile concert photograph of {TRIGGER} performing live on stage. Calder has a sharp chiseled jawline with heavy 5 o'clock shadow stubble, dark hair curling at his nape, cap brim low. He is {OUTFIT}. Singing passionately into the microphone with head tilted slightly. Golden stage spotlights and amber rim light tracing his jawline and cap through drifting stage smoke. {LIGHTING}."
    },
    {
        "name": "cut4_front_chest.jpg",
        "prompt": f"An intense 9:16 vertical high-impact concert photograph of {TRIGGER} belting the climax of a country anthem live on stage. Calder has rugged features, heavy stubble beard, and is {OUTFIT}. Holding the microphone close to his mouth with head tilted back, eyes closed, singing with full chest voice and raw passionate emotion. Bright warm amber backlights exploding into golden lens flare around his shoulders, drifting stage smoke. {LIGHTING}."
    },
    {
        "name": "cut6_side_quiet.jpg",
        "prompt": f"A dynamic 9:16 vertical three-quarter concert photograph of {TRIGGER} singing on stage at dusk. Calder has heavy 5 o'clock shadow stubble beard and is {OUTFIT}. Looking slightly off-camera as he sings an emotional lyric into the mic, warm amber stage spotlights and festival crowd bokeh. {LIGHTING}."
    },
    {
        "name": "cut7_front_outro.jpg",
        "prompt": f"A poignant 9:16 vertical concert broadcast photograph of {TRIGGER} at the final resolution of the song. Calder is {OUTFIT}, heavy 5 o'clock shadow stubble beard, looking directly toward the camera with quiet soul and vulnerability, stepping back slightly from the microphone as the last chord rings out, stage lights softening into warm amber twilight. {LIGHTING}."
    }
]

for s in stills:
    out_path = f"{out_dir}/{s['name']}"
    if os.path.exists(out_path):
        print(f"[✓] {s['name']} already exists, skipping.")
        continue
    print(f"[*] Generating {s['name']} with Calder FLUX LoRA...", flush=True)
    res = fal_client.subscribe(
        "fal-ai/flux-lora",
        arguments={
            "prompt": s["prompt"],
            "loras": [{"path": lora_url, "scale": 0.95}],
            "image_size": {"width": 896, "height": 1536},
            "num_inference_steps": 30,
            "guidance_scale": 3.0,
            "output_format": "jpeg"
        }
    )
    img_url = res["images"][0]["url"]
    urllib.request.urlretrieve(img_url, out_path)
    print(f"    [✓] Saved {s['name']} from {img_url[:50]}...")

print("\n[🎉] All concert stills generated with Calder Quinn FLUX LoRA!")
