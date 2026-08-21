"""Render the reference-canvas retest: 2 legs, seed 20260821, best effort.

Same receipts pattern as the main lane: live /object_info preflight, the purity
gate re-run on the graphs actually queued, outputs read back from /history, and
the temporal metric written per leg. An OOM here is a plain recorded fault --
2.26x the pixels and 121 frames on the 8GB-tier GGUF is exactly where one would
appear, and the ruling says no forensics.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1].parent / "tools"))
import purity_gate  # noqa: E402
import temporal_stats  # noqa: E402

SERVER = "http://127.0.0.1:8000"
SEED = 20260821
OUT_PREFIX = "baseline_output/lane1_wan_ti2v/retest_refcanvas"
LEG_TIMEOUT_S = 2 * 60 * 60
MODEL_INPUTS = {"UnetLoaderGGUF": "unet_name", "CLIPLoaderGGUF": "clip_name",
                "VAELoader": "vae_name", "LoadImage": "image"}


def get_json(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    object_info = get_json("%s/object_info" % SERVER, timeout=300)
    print("[OBJECT_INFO] %d classes" % len(object_info))

    submissions = {}
    for arm in ("ours", "official"):
        graph = json.loads(io.open(HERE / ("arm_%s.json" % arm),
                                   encoding="utf-8").read())
        graph["ksampler"]["inputs"]["seed"] = SEED
        graph["save"] = {"class_type": "SaveImage",
                         "inputs": {"images": ["vaedecode", 0],
                                    "filename_prefix": "%s/%s_seed%d/frame"
                                    % (OUT_PREFIX, arm, SEED)}}
        submissions[arm] = graph

    faults = []
    for arm, graph in submissions.items():
        for node_id, node in graph.items():
            cls = node["class_type"]
            if cls not in object_info:
                faults.append("class %r absent" % cls)
                continue
            name = MODEL_INPUTS.get(cls)
            if name:
                spec = ((object_info[cls].get("input") or {}).get("required") or {})
                options = spec.get(name)
                options = options[0] if isinstance(options, list) and options else []
                if node["inputs"].get(name) not in options:
                    faults.append("%s.%s=%r not installed"
                                  % (cls, name, node["inputs"].get(name)))
    if faults:
        for fault in sorted(set(faults)):
            print("[FAIL] %s" % fault)
        return 1
    print("[PREFLIGHT] PASSED")

    receipts = HERE / "render"
    receipts.mkdir(exist_ok=True)
    manifest = {}
    for arm, graph in submissions.items():
        text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = receipts / ("submitted_%s_seed%d.json" % (arm, SEED))
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        manifest[path.name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    io.open(receipts / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join("%s  %s\n" % (manifest[n], n) for n in sorted(manifest)))

    argv = [str(receipts / ("submitted_ours_seed%d.json" % SEED)),
            str(receipts / ("submitted_official_seed%d.json" % SEED)),
            "--expect", 'ksampler.sampler_name="uni_pc"',
            "--expect", "ksampler.steps=20",
            "--expect", "modelsampling.shift=8.0",
            "--expect", 'save.filename_prefix="%s/official_seed%d/frame"'
            % (OUT_PREFIX, SEED)]
    if purity_gate.main(argv) != 0:
        print("[FAIL] submitted graphs are not pure. Nothing queued.")
        return 1

    legs = []
    for arm in ("ours", "official"):
        graph = submissions[arm]
        label = "retest/%s_seed%d" % (arm, SEED)
        digest = manifest["submitted_%s_seed%d.json" % (arm, SEED)]
        print("\n[LEG] %s sha256=%s latent=%sx%sx%s"
              % (label, digest[:16], graph["latent"]["inputs"]["width"],
                 graph["latent"]["inputs"]["height"],
                 graph["latent"]["inputs"]["length"]))
        started = time.time()
        try:
            prompt_id = post_json("%s/prompt" % SERVER,
                                  {"prompt": graph}).get("prompt_id")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1500]
            print("[FAULT] submit rejected: %s" % detail)
            legs.append({"leg": label, "arm": arm, "status": "REJECTED",
                         "detail": detail, "sha256": digest})
            continue
        print("[QUEUED] %s" % prompt_id)
        while True:
            if time.time() - started > LEG_TIMEOUT_S:
                result = {"status": "TIMEOUT", "outputs": {}, "messages": []}
                break
            try:
                entry = get_json("%s/history/%s" % (SERVER, prompt_id)).get(prompt_id)
            except (urllib.error.URLError, TimeoutError) as exc:
                result = {"status": "SERVER GONE: %s" % exc, "outputs": {},
                          "messages": []}
                break
            if entry:
                status = entry.get("status") or {}
                if status.get("completed") or status.get("status_str") in ("success", "error"):
                    result = {"status": status.get("status_str", "unknown"),
                              "outputs": entry.get("outputs") or {},
                              "messages": status.get("messages") or []}
                    break
            time.sleep(10)
        elapsed = round(time.time() - started, 1)
        images = []
        for output in (result["outputs"] or {}).values():
            images.extend(output.get("images") or [])
        print("[DONE] %s status=%s frames=%d elapsed=%ss"
              % (label, result["status"], len(images), elapsed))
        if result["status"] != "success":
            print("[FAULT] %s" % json.dumps(result.get("messages"))[:1200])
        record = {"leg": label, "arm": arm, "seed": SEED, "sha256": digest,
                  "prompt_id": prompt_id, "status": result["status"],
                  "elapsed_s": elapsed, "frame_count": len(images),
                  "subfolder": images[0]["subfolder"] if images else None,
                  "messages": result.get("messages", [])}
        if result["status"] == "success" and record["subfolder"]:
            record["temporal"] = temporal_stats.leg_stats(
                temporal_stats.COMFY_OUTPUT / record["subfolder"])
            print("[TEMPORAL] mean=%.3f max=%.3f"
                  % (record["temporal"]["mean_abs_delta"],
                     record["temporal"]["max_abs_delta"]))
        legs.append(record)
        io.open(receipts / "RENDER.json", "w", encoding="utf-8", newline="\n").write(
            json.dumps({"server": SERVER, "cell": "retest_refcanvas",
                        "seed": SEED, "fps": 24, "legs": legs},
                       indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    ok = sum(1 for leg in legs if leg["status"] == "success")
    print("\n[RETEST] %d/2 leg(s) succeeded." % ok)
    return 0 if ok == 2 else 2


if __name__ == "__main__":
    sys.exit(main())
