import os
import sys
import subprocess

renders_dir = "scratch/hedra_renders"
conformed_dir = "scratch/conformed_cuts"
os.makedirs(conformed_dir, exist_ok=True)
os.makedirs("videos", exist_ok=True)

cuts = [
    # 0:00 - 0:04.50 (4.50s) Cut 1: Front mic pre-chorus build
    {
        "id": "cut1_front_kitchen",
        "file": f"{renders_dir}/cut1_front_kitchen.mp4",
        "start": 0.0,
        "duration": 4.50,
        "desc": "Front Stage Mic — Pre-Chorus Build"
    },
    # 0:04.50 - 0:08.30 (3.80s) Cut 2: Crowd Pan (Kling)
    {
        "id": "cut2_crowd_pan",
        "file": "scratch/kling_crowd_pan.mp4",
        "start": 0.0,
        "duration": 3.80,
        "desc": "Amphitheater Crowd Sweep — Tension Peak"
    },
    # 0:08.30 - 0:15.00 (6.70s) Cut 3: Side Profile Chorus Drop
    {
        "id": "cut3_side_light",
        "file": f"{renders_dir}/cut3_side_light.mp4",
        "start": 0.0,
        "duration": 6.70,
        "desc": "Side Profile — 'Leave the Light in the Hollow'"
    },
    # 0:15.00 - 0:21.50 (6.50s) Cut 4: Frontal Climax Belt
    {
        "id": "cut4_front_chest",
        "file": f"{renders_dir}/cut4_front_chest.mp4",
        "start": 0.0,
        "duration": 6.50,
        "desc": "Frontal Climax — 'I Throw My Whole Damn Chest At Heaven!'"
    },
    # 0:21.50 - 0:26.00 (4.50s) Cut 5: Crowd Roar / Stage POV (Kling)
    {
        "id": "cut5_crowd_roar",
        "file": "scratch/kling_crowd_pan.mp4",
        "start": 0.5,
        "duration": 4.50,
        "desc": "Crowd Roar & Stage Energy — Band Drop"
    },
    # 0:26.00 - 0:30.50 (4.50s) Cut 6: Side Profile Quiet Hook
    {
        "id": "cut6_side_quiet",
        "file": f"{renders_dir}/cut6_side_quiet.mp4",
        "start": 0.0,
        "duration": 4.50,
        "desc": "Side Profile — 'If I Go Quiet I Disappear'"
    },
    # 0:30.50 - 0:38.50 (8.00s) Cut 7: Frontal Outro & Ring-out
    {
        "id": "cut7_front_outro",
        "file": f"{renders_dir}/cut7_front_outro.mp4",
        "start": 0.0,
        "duration": 8.00,
        "desc": "Frontal Outro — 'And I Crawl Back In' & Acoustic Fade"
    }
]

# Step 1: Conform each cut to exact resolution and fps
print("[*] STEP 1: Conforming video segments...", flush=True)
conformed_files = []

for i, c in enumerate(cuts):
    out_file = f"{conformed_dir}/seg_{i:02d}_{c['id']}.mp4"
    if not os.path.exists(c["file"]):
        print(f"[-] Missing source file for {c['id']}: {c['file']}")
        sys.exit(1)
        
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(c["start"]),
        "-t", str(c["duration"]),
        "-i", c["file"],
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-an",
        out_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    conformed_files.append(out_file)
    print(f"  [+] Segment {i+1}/{len(cuts)}: {c['desc']} ({c['duration']}s)")

# Step 2: Concat list
concat_list = f"{conformed_dir}/concat.txt"
with open(concat_list, "w") as f:
    for cf in conformed_files:
        f.write(f"file '{os.path.abspath(cf)}'\n")

video_raw = f"{conformed_dir}/video_stitched_raw.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c", "copy",
    video_raw
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Step 3: Mux master audio
final_master = "videos/Calder_Quinn_LeaveTheLightInTheHollow_38s_Concert_Master.mp4"
master_audio = "scratch/concert_audio/master_concert_38.5s.mp3"

print(f"[*] Muxing master audio: {master_audio} -> {final_master}...", flush=True)
cmd_mux = [
    "ffmpeg", "-y",
    "-i", video_raw,
    "-i", master_audio,
    "-c:v", "h264_videotoolbox",
    "-b:v", "7500k",
    "-c:a", "aac",
    "-b:a", "320k",
    "-movflags", "+faststart",
    "-shortest",
    final_master
]
subprocess.run(cmd_mux, check=True)

# Generate high-res video thumbnail
thumb_path = "videos/Calder_Quinn_LeaveTheLightInTheHollow_Thumbnail.jpg"
cmd_thumb = [
    "ffmpeg", "-y",
    "-ss", "16.5",
    "-i", final_master,
    "-vframes", "1",
    "-q:v", "2",
    thumb_path
]
subprocess.run(cmd_thumb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

print(f"\n[🎉 MASTERPIECE CREATED!]")
print(f"  -> Video: {final_master}")
print(f"  -> Thumbnail: {thumb_path}")

dur_cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", final_master]
res_dur = subprocess.check_output(dur_cmd).decode().strip()
print(f"[✓] Final Master Duration: {res_dur}s")
