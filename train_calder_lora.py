import os
import sys
import time
import json
import fal_client

FAL_KEY = "347f2fd3-fdd2-4fdc-8ac8-f35f96b66d73:d60ae62cd8ed31b35eb00dc6cbcdbf4e"
os.environ["FAL_KEY"] = FAL_KEY

zip_path = "scratch/calder_quinn_flux_dataset.zip"
if not os.path.exists(zip_path):
    print(f"[-] Dataset zip not found at {zip_path}")
    sys.exit(1)

print("[*] STEP 1: Uploading Calder Quinn training dataset to FAL CDN...")
dataset_url = fal_client.upload_file(zip_path)
print(f"[✓] Dataset uploaded: {dataset_url}")

print("\n[*] STEP 2: Submitting FLUX LoRA Fast Training job to fal-ai/flux-lora-fast-training...")
job_handle = fal_client.submit(
    "fal-ai/flux-lora-fast-training",
    arguments={
        "images_data_url": dataset_url,
        "trigger_word": "calder_quinn",
        "is_style": False
    }
)

req_id = job_handle.request_id
print(f"[✓] Submitted! Request ID: {req_id}")

job_meta = {
    "request_id": req_id,
    "dataset_url": dataset_url,
    "trigger_word": "calder_quinn",
    "timestamp": time.time()
}
with open("scratch/calder_training_job.json", "w") as f:
    json.dump(job_meta, f, indent=2)

print("\n[*] STEP 3: Polling training progress...")
start_time = time.time()
endpoint = "fal-ai/flux-lora-fast-training"

while True:
    try:
        status = fal_client.status(endpoint, req_id, with_logs=True)
        elapsed = int(time.time() - start_time)
        status_name = type(status).__name__
        print(f"[{elapsed}s] Status: {status_name}", flush=True)

        if hasattr(status, "logs") and status.logs:
            for log in status.logs[-2:]:
                msg = log.get("message", "") if isinstance(log, dict) else str(log)
                print(f"   -> {msg.strip()}", flush=True)

        if status_name == "Completed":
            result = fal_client.result(endpoint, req_id)
            print("\n[🎉] Calder Quinn FLUX LoRA Training Completed Successfully!")
            print(json.dumps(result, indent=2))
            with open("scratch/calder_lora_result.json", "w") as f:
                json.dump(result, f, indent=2)
            break
        elif status_name in ["Failed", "Error"]:
            print(f"[-] Training Failed: {status}")
            sys.exit(1)
    except Exception as e:
        print(f"   [!] Notice: {e}", flush=True)
    time.sleep(15)
