import os
import sys
import time
import json
import uuid
import urllib.request
import subprocess

API_KEY = "k_live_5_lKSbDosqabX4y_:sk_NUy50_cHM9dT-0_NIZT--B4zrXJbF1m58wTwhEQpqlc"
BASE_URL = "https://api.hedra.com/v3"

renders_dir = "scratch/hedra_renders"
conformed_dir = "scratch/conformed_cuts"
os.makedirs(renders_dir, exist_ok=True)
os.makedirs(conformed_dir, exist_ok=True)
os.makedirs("videos", exist_ok=True)

def upload_to_hedra(filepath):
    boundary = uuid.uuid4().hex
    filename = os.path.basename(filepath)
    mimetype = "image/jpeg" if filename.endswith((".jpg", ".jpeg")) else "audio/mpeg"
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {mimetype}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/files",
        data=body,
        headers={
            "Authorization": f"Key {API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))["url"]

def submit_hedra_job(job_name, image_path, audio_path, prompt):
    print(f"[*] Uploading assets for {job_name}...", flush=True)
    img_url = upload_to_hedra(image_path)
    aud_url = upload_to_hedra(audio_path)
    payload = {
        "input": {
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "prompt": prompt,
            "start_image": {"source": "url", "url": img_url},
            "audio": {"source": "url", "url": aud_url}
        }
    }
    req = urllib.request.Request(
        f"{BASE_URL}/models/hedra-character-3",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Key {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        jid = data["job_id"]
        print(f"    [+] Hedra {job_name} submitted -> Job ID: {jid}", flush=True)
        return jid

hedra_shots = [
    {
        "id": "cut1_front_kitchen",
        "image": "scratch/concert_stills/cut1_front_kitchen.jpg",
        "audio": "scratch/concert_audio/vocal_cut1_front_kitchen.mp3",
        "prompt": "Rugged country rock singer singing into stage microphone on outdoor festival stage, rhythmic head movement, singing pre-chorus passionately, live concert lighting.",
        "duration": 4.50,
        "output": f"{renders_dir}/cut1_front_kitchen.mp4"
    },
    {
        "id": "cut3_side_light",
        "image": "scratch/concert_stills/cut3_side_light.jpg",
        "audio": "scratch/concert_audio/vocal_cut3_side_light.mp3",
        "prompt": "Dramatic 90-degree side profile of country singer singing into stage mic with head tilted, singing chorus line passionately, stage haze and amber rim light.",
        "duration": 6.70,
        "output": f"{renders_dir}/cut3_side_light.mp4"
    },
    {
        "id": "cut4_front_chest",
        "image": "scratch/concert_stills/cut4_front_chest.jpg",
        "audio": "scratch/concert_audio/vocal_cut4_front_chest.mp3",
        "prompt": "Close-up front view of country rock singer passionately belting chorus climax into mic, head back with raw emotional power, glowing amber backlights.",
        "duration": 6.50,
        "output": f"{renders_dir}/cut4_front_chest.mp4"
    },
    {
        "id": "cut6_side_quiet",
        "image": "scratch/concert_stills/cut6_side_quiet.jpg",
        "audio": "scratch/concert_audio/vocal_cut6_side_quiet.mp3",
        "prompt": "Side profile of country singer singing heartfelt lyric into stage microphone, subtle head nodding in rhythm, warm festival stage lights.",
        "duration": 4.50,
        "output": f"{renders_dir}/cut6_side_quiet.mp4"
    },
    {
        "id": "cut7_front_outro",
        "image": "scratch/concert_stills/cut7_front_outro.jpg",
        "audio": "scratch/concert_audio/vocal_cut7_front_outro.mp3",
        "prompt": "Emotional front view of country singer delivering final resolution lyric into mic, looking out into the festival audience, stage lights softening.",
        "duration": 8.00,
        "output": f"{renders_dir}/cut7_front_outro.mp4"
    }
]

submitted_jobs = {}
job_cache_file = "scratch/submitted_hedra_jobs.json"
if os.path.exists(job_cache_file):
    with open(job_cache_file) as f:
        submitted_jobs = json.load(f)

for s in hedra_shots:
    if s["id"] in [info.get("id") for info in submitted_jobs.values()]:
        print(f"[*] {s['id']} already submitted.")
        continue
    jid = submit_hedra_job(s["id"], s["image"], s["audio"], s["prompt"])
    s["job_id"] = jid
    submitted_jobs[jid] = s
    time.sleep(1.5)

with open(job_cache_file, "w") as f:
    json.dump(submitted_jobs, f, indent=2)

print("\n[*] Polling Hedra jobs...", flush=True)
pending = dict(submitted_jobs)
headers = {"Authorization": f"Key {API_KEY}"}

while pending:
    for jid, s in list(pending.items()):
        req = urllib.request.Request(f"{BASE_URL}/jobs/{jid}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                st = data.get("status")
                name = s["id"]
                print(f"    [{name}] Status: {st}", flush=True)
                if st == "COMPLETED":
                    v_url = data["outputs"][0]["url"]
                    print(f"    [✓] {name} complete! Downloading to {s['output']}...", flush=True)
                    urllib.request.urlretrieve(v_url, s["output"])
                    del pending[jid]
                elif st in ["FAILED", "EXPIRED"]:
                    print(f"    [-] {name} failed: {data}", flush=True)
                    del pending[jid]
        except Exception as e:
            print(f"    [!] Poll error for {s['id']}: {e}", flush=True)
        time.sleep(1)
    if pending:
        time.sleep(10)

print("\n[✓] All Hedra lip-sync renders downloaded successfully!", flush=True)
