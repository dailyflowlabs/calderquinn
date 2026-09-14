import os
import sys
import time
import json
import base64
import urllib.request
import urllib.error
import subprocess

API_KEY = os.environ.get("KLING_API_KEY", "api-key-kling-ZBCskxkg6NOVQFbhMbvln6tZ274M-izFbnoRdE8j0kE")
BASE_URL = "https://api.klingai.com"

scratch_dir = "scratch/kling_renders"
os.makedirs(scratch_dir, exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("scratch/audio_slices", exist_ok=True)

# Master Audio Slicing (30.0 seconds from 36.0s to 66.0s)
master_audio = "scratch/audio_slices/master_chorus_30s.mp3"
if not os.path.exists(master_audio):
    cmd = [
        "ffmpeg", "-y",
        "-ss", "36.0", "-t", "30.0",
        "-i", "music/Leave the Light in the Hollow.mp3",
        "-vn", "-c:a", "libmp3lame", "-b:a", "320k",
        master_audio
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("[✓] Master 30s chorus audio sliced.")

# Base shots definition
shots = [
    {
        "name": "shot_01_tailgate_intro",
        "image": "images/01_calder_front_anchor.jpg",
        "prompt": "Cinematic slow push-in on rugged country singer sitting on vintage truck tailgate, strumming acoustic guitar with weathered hands, looking into camera with soulful expression, dusk light, 24fps.",
        "duration": "5",
        "output": f"{scratch_dir}/shot_01_tailgate_intro.mp4",
        "task_id": "928356255586979847" # already submitted test
    },
    {
        "name": "shot_02_barn_belt",
        "image": "images/05_calder_singing.jpg",
        "prompt": "Close-up action shot of rugged country singer passionately belting an emotional chorus, head moving with rhythm, singing passionately with head tilted, warm tungsten barn backlights glowing softly, cinematic depth of field, 24fps.",
        "duration": "5",
        "output": f"{scratch_dir}/shot_02_barn_belt.mp4"
    },
    {
        "name": "shot_03_profile_twilight",
        "image": "images/03_calder_side_profile.jpg",
        "prompt": "Dramatic 90-degree side profile of rugged country singer singing into the evening air, subtle head bounce to rhythm, breeze moving shaggy hair under distressed baseball cap, warm golden dusk glow on jawline and stubble, cinematic 24fps.",
        "duration": "5",
        "output": f"{scratch_dir}/shot_03_profile_twilight.mp4"
    },
    {
        "name": "shot_04_truck_strum",
        "image": "images/04_calder_full_body.jpg",
        "prompt": "Cinematic medium wide shot of country singer leaning against vintage pickup truck on dirt road at dusk, strumming acoustic guitar with raw energy, tapping boot in dirt, barn string lights glowing in distance, 24fps.",
        "duration": "5",
        "output": f"{scratch_dir}/shot_04_truck_strum.mp4"
    },
    {
        "name": "shot_05_tailgate_climax",
        "image": "images/01_calder_front_anchor.jpg",
        "prompt": "Intense close-up portrait of rugged country singer delivering final emotional chorus line, direct gaze into camera, singing passionately, warm evening amber rim lighting, authentic 35mm grain, 24fps.",
        "duration": "5",
        "output": f"{scratch_dir}/shot_05_tailgate_climax.mp4"
    }
]

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def submit_task(shot):
    if shot.get("task_id"):
        print(f"[*] {shot['name']} already submitted (Task ID: {shot['task_id']})")
        return shot["task_id"]
    
    print(f"[*] Submitting {shot['name']} ({shot['image']})...", flush=True)
    img_b64 = image_to_base64(shot["image"])
    payload = {
        "model_name": "kling-v1",
        "mode": "std",
        "image": img_b64,
        "prompt": shot["prompt"],
        "duration": shot.get("duration", "5"),
        "cfg_scale": 0.5
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/videos/image2video",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 0:
                tid = data["data"]["task_id"]
                print(f"    [+] {shot['name']} -> Task ID: {tid}", flush=True)
                shot["task_id"] = tid
                return tid
            else:
                print(f"    [-] Submission error: {data}", flush=True)
                return None
    except Exception as e:
        print(f"    [-] Request failed for {shot['name']}: {e}", flush=True)
        return None

# Submit all shots
submitted = {}
for s in shots:
    tid = submit_task(s)
    if tid:
        submitted[tid] = s
    time.sleep(1.5)

job_file = f"{scratch_dir}/submitted_shots.json"
with open(job_file, "w") as f:
    json.dump(submitted, f, indent=2)

print(f"\n[✓] All {len(submitted)} shots submitted to Kling AI! Polling for renders...", flush=True)

# Polling loop
video_urls = {}
pending = dict(submitted)
start_time = time.time()

while pending:
    for tid, s in list(pending.items()):
        req = urllib.request.Request(
            f"{BASE_URL}/v1/videos/image2video/{tid}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                st = data.get("data", {}).get("task_status")
                name = s["name"]
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] [{name}] Status: {st}", flush=True)
                
                if st == "succeed":
                    v_url = data["data"]["task_result"]["videos"][0]["url"]
                    video_urls[name] = v_url
                    print(f"    [✓] {name} complete! Downloading to {s['output']}...", flush=True)
                    urllib.request.urlretrieve(v_url, s["output"])
                    del pending[tid]
                elif st in ["failed", "canceled"]:
                    msg = data.get("data", {}).get("task_status_msg", "Unknown")
                    print(f"    [-] {name} failed: {msg}", flush=True)
                    del pending[tid]
        except Exception as e:
            print(f"    [!] Error polling {s['name']}: {e}", flush=True)
        time.sleep(2)
    
    if pending:
        time.sleep(12)

with open(f"{scratch_dir}/video_urls.json", "w") as f:
    json.dump(video_urls, f, indent=2)

print("\n[🎉] All shots rendered successfully! Assembling master cut...", flush=True)

# Step 2: Multi-cam rhythm assembly
cuts = [
    # 0:00 - 0:05.5: Pre-chorus intro ("I can hold it in the kitchen, I can hold it in the truck...")
    {"file": f"{scratch_dir}/shot_01_tailgate_intro.mp4", "start": 0.0, "duration": 5.0, "desc": "Tailgate Intro Push-In"},
    
    # 0:05.0 - 0:08.0: Truck Strum transition ("...hits the ridgeline...")
    {"file": f"{scratch_dir}/shot_04_truck_strum.mp4", "start": 0.0, "duration": 3.0, "desc": "Wide Truck Strum Tension"},
    
    # 0:08.0 - 0:15.0: Chorus Hook Drop ("I leave the light in the hollow, so I know where the dark begins...")
    {"file": f"{scratch_dir}/shot_02_barn_belt.mp4", "start": 0.0, "duration": 5.0, "desc": "Passionate Barn Vocal Belt 1"},
    
    # 0:13.0 - 0:17.0: Side Profile Twilight ("...where the dark begins...")
    {"file": f"{scratch_dir}/shot_03_profile_twilight.mp4", "start": 0.5, "duration": 4.0, "desc": "Side Profile Hollow Dusk"},
    
    # 0:17.0 - 0:24.0: Explosive Belt ("I throw my whole damn chest at heaven, just to hear it throw it back again!")
    {"file": f"{scratch_dir}/shot_02_barn_belt.mp4", "start": 0.5, "duration": 4.5, "desc": "Passionate Barn Vocal Belt 2"},
    
    # 0:21.5 - 0:26.5: Direct Tailgate Gaze Climax ("If I go quiet I disappear...")
    {"file": f"{scratch_dir}/shot_05_tailgate_climax.mp4", "start": 0.0, "duration": 4.5, "desc": "Tailgate Intimate Climax"},
    
    # 0:26.0 - 0:30.0: Outro Resolution ("Leave the light in the hollow... and I crawl back in")
    {"file": f"{scratch_dir}/shot_03_profile_twilight.mp4", "start": 1.0, "duration": 4.0, "desc": "Twilight Fade Out"}
]

temp_cuts_dir = f"{scratch_dir}/temp_cuts"
os.makedirs(temp_cuts_dir, exist_ok=True)

temp_files = []
for i, c in enumerate(cuts):
    seg_path = f"{temp_cuts_dir}/cut_{i:02d}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(c["start"]),
        "-t", str(c["duration"]),
        "-i", c["file"],
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        seg_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    temp_files.append(seg_path)
    print(f"  [+] Segment {i+1}/{len(cuts)}: {c['desc']} ({c['duration']}s)")

concat_txt = f"{temp_cuts_dir}/concat.txt"
with open(concat_txt, "w") as f:
    for tf in temp_files:
        f.write(f"file '{os.path.abspath(tf)}'\n")

video_stitched = f"{scratch_dir}/video_stitched.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_txt,
    "-c", "copy",
    video_stitched
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

final_master = "videos/calder_quinn_leave_the_light_in_the_hollow_30s_master.mp4"
print(f"[*] Muxing master audio with faststart to {final_master}...", flush=True)

cmd_mux = [
    "ffmpeg", "-y",
    "-i", video_stitched,
    "-i", master_audio,
    "-c:v", "h264_videotoolbox",
    "-b:v", "6500k",
    "-c:a", "aac",
    "-b:a", "256k",
    "-movflags", "+faststart",
    "-shortest",
    final_master
]
subprocess.run(cmd_mux, check=True)

print(f"\n[🚀 FINISHED!] Master Video Created: {final_master}")
dur_cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", final_master]
res_dur = subprocess.check_output(dur_cmd).decode().strip()
print(f"[✓] Verified Master Duration: {res_dur}s")
