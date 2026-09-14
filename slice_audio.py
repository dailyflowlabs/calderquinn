import os
import subprocess

audio_dir = "scratch/concert_audio"
os.makedirs(audio_dir, exist_ok=True)

# Master 38.5s concert segment (35.5s to 74.0s)
master_audio = f"{audio_dir}/master_concert_38.5s.mp3"
cmd_master = [
    "ffmpeg", "-y",
    "-ss", "35.50", "-t", "38.50",
    "-i", "music/Leave the Light in the Hollow.mp3",
    "-vn", "-c:a", "libmp3lame", "-b:a", "320k",
    master_audio
]
subprocess.run(cmd_master, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[✓] Created master audio: {master_audio}")

# Vocal slices for Hedra character lip-sync
slices = [
    # Cut 1: Front mic pre-chorus (35.50s to 40.00s / 4.50s)
    {"name": "vocal_cut1_front_kitchen", "start": "35.50", "duration": "4.50"},
    # Cut 3: Side profile chorus start (43.80s to 50.50s / 6.70s)
    {"name": "vocal_cut3_side_light", "start": "43.80", "duration": "6.70"},
    # Cut 4: Frontal stage climax belt (50.50s to 57.00s / 6.50s)
    {"name": "vocal_cut4_front_chest", "start": "50.50", "duration": "6.50"},
    # Cut 6: Side profile hook (61.50s to 66.00s / 4.50s)
    {"name": "vocal_cut6_side_quiet", "start": "61.50", "duration": "4.50"},
    # Cut 7: Frontal outro & ring-out (66.00s to 74.00s / 8.00s)
    {"name": "vocal_cut7_front_outro", "start": "66.00", "duration": "8.00"}
]

for s in slices:
    out_path = f"{audio_dir}/{s['name']}.mp3"
    cmd = [
        "ffmpeg", "-y",
        "-ss", s["start"], "-t", s["duration"],
        "-i", "music/Leave the Light in the Hollow.mp3",
        "-vn", "-c:a", "libmp3lame", "-b:a", "320k",
        out_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  [+] Sliced {s['name']} ({s['start']} -> {s['duration']}s)")

print("\n[✓] All concert audio stems ready!")
