"""Render lane 1: every fixture, two arms, two seeds, sequentially on one server.

Best-effort per the operator's 2026-08-21 ruling -- there is no VRAM ceremony
here. An OOM is recorded as a plain fault on that leg and the lane continues;
it is not a forensic project.

The staged arms carry no terminal node, because the shipping engine reads its
IMAGE batch straight off the decoder in-process. A ``SaveImage`` is therefore
appended IDENTICALLY to both arms so frames can be judged at native pixels with
no codec in the path. Only its ``filename_prefix`` differs between legs, which
is a destination and cannot reach the sampler -- and the submitted graphs are
re-gated against that exact declaration before anything is queued, so purity is
proven on what RAN rather than on what was staged.

Every class and every model filename is confirmed present in the LIVE
``/object_info`` before submit, and every output is read back from ``/history``
rather than globbed off disk.

usage: render_arms.py [fixture_key ...]      (default: every staged fixture)
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
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import purity_gate  # noqa: E402

SERVER = "http://127.0.0.1:8000"
SEEDS = [42, 20260821]
ARMS = ["ours", "official"]
OUT_PREFIX = "baseline_output/lane1_wan_ti2v"
LEG_TIMEOUT_S = 60 * 60
MODEL_INPUTS = {
    "UnetLoaderGGUF": "unet_name",
    "CLIPLoaderGGUF": "clip_name",
    "VAELoader": "vae_name",
    "LoadImage": "image",
}


def get_json(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def enum_options(spec):
    if isinstance(spec, list) and spec and isinstance(spec[0], list):
        return list(spec[0])
    return []


def preflight(graphs, object_info):
    """Every executed class and every named file must exist on THIS server."""
    faults = []
    seen = set()
    for graph in graphs.values():
        for node_id, node in graph.items():
            class_type = node["class_type"]
            if class_type not in object_info:
                faults.append(
                    "class %r (node %r) absent from /object_info" % (class_type, node_id))
                continue
            seen.add(class_type)
            input_name = MODEL_INPUTS.get(class_type)
            if not input_name:
                continue
            wanted = node["inputs"].get(input_name)
            spec = ((object_info[class_type].get("input") or {}).get("required") or {})
            options = enum_options(spec.get(input_name))
            if not options:
                faults.append("%s.%s exposes no selectable values"
                              % (class_type, input_name))
            elif wanted not in options:
                faults.append("%s.%s=%r is not installed (server offers %d value(s))"
                              % (class_type, input_name, wanted, len(options)))
    for class_type in sorted(seen):
        print("[OBJECT_INFO] %s: present" % class_type)
    return faults


def leg_prefix(fixture, subdir, arm, seed):
    parts = [OUT_PREFIX]
    if subdir:
        parts.append(subdir)
    parts.append("%s_seed%d" % (arm, seed))
    return "/".join(parts) + "/frame"


def build_submission(fixture, subdir, arm, seed):
    path = HERE / fixture / ("arm_%s.json" % arm)
    graph = json.loads(io.open(path, encoding="utf-8").read())
    graph["ksampler"]["inputs"]["seed"] = seed
    graph["save"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["vaedecode", 0],
            "filename_prefix": leg_prefix(fixture, subdir, arm, seed),
        },
    }
    return graph


def gate_submissions(fixture, subdir, seed, submitted, receipts, manifest):
    """Re-prove purity on what is actually about to be QUEUED.

    The submitted graphs get their own ``ARMS.sha256`` beside them, so identity
    is proven on the bytes that were sent rather than only on staging.
    """
    paths = {}
    for arm, graph in submitted.items():
        path = receipts / ("submitted_%s_seed%d.json" % (arm, seed))
        text = json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        manifest[path.name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        paths[arm] = path
    io.open(receipts / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
        "".join("%s  %s\n" % (manifest[n], n) for n in sorted(manifest)))
    declared = [
        'ksampler.sampler_name="uni_pc"',
        "ksampler.steps=20",
        "modelsampling.shift=8.0",
        'save.filename_prefix="%s"' % leg_prefix(fixture, subdir, "official", seed),
    ]
    argv = [str(paths["ours"]), str(paths["official"])]
    for item in declared:
        argv += ["--expect", item]
    print("[SUBMIT GATE] %s seed %d" % (fixture, seed))
    return purity_gate.main(argv) == 0


def wait_for_leg(prompt_id, started):
    while True:
        if time.time() - started > LEG_TIMEOUT_S:
            return {"status": "TIMEOUT", "outputs": {}, "messages": []}
        try:
            history = get_json("%s/history/%s" % (SERVER, prompt_id))
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"status": "SERVER GONE: %s" % exc, "outputs": {}, "messages": []}
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status") or {}
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                return {"status": status.get("status_str", "unknown"),
                        "outputs": entry.get("outputs") or {},
                        "messages": status.get("messages") or []}
        time.sleep(5)


def main():
    lane = json.loads(io.open(HERE / "LANE.json", encoding="utf-8").read())
    wanted = sys.argv[1:] or sorted(lane["fixtures"])
    unknown = [k for k in wanted if k not in lane["fixtures"]]
    if unknown:
        print("[FAIL] unknown fixture(s): %s" % unknown)
        return 1

    print("[SERVER] %s" % SERVER)
    print("[FIXTURES] %s" % ", ".join(wanted))
    object_info = get_json("%s/object_info" % SERVER, timeout=300)
    print("[OBJECT_INFO] %d classes registered" % len(object_info))

    plan = {}
    for fixture in wanted:
        subdir = lane["fixtures"][fixture]["output_subdir"]
        for seed in SEEDS:
            for arm in ARMS:
                plan[(fixture, arm, seed)] = build_submission(fixture, subdir, arm, seed)

    named = {}
    for (fixture, arm, seed), graph in plan.items():
        named["%s_%s_%d" % (fixture, arm, seed)] = graph
    faults = preflight(named, object_info)
    if faults:
        for fault in faults:
            print("[FAIL] %s" % fault)
        print("[PREFLIGHT] FAILED -- nothing queued.")
        return 1
    print("[PREFLIGHT] PASSED -- every class and model filename is live on this server.")

    for fixture in wanted:
        subdir = lane["fixtures"][fixture]["output_subdir"]
        receipts = HERE / fixture / "render"
        receipts.mkdir(parents=True, exist_ok=True)
        manifest = {}
        for seed in SEEDS:
            arms_for_seed = {arm: plan[(fixture, arm, seed)] for arm in ARMS}
            if not gate_submissions(fixture, subdir, seed, arms_for_seed,
                                    receipts, manifest):
                print("[FAIL] %s seed %d is not pure. Nothing queued." % (fixture, seed))
                return 1

    legs = []
    for fixture in wanted:
        receipts = HERE / fixture / "render"
        fixture_legs = []
        for seed in SEEDS:
            for arm in ARMS:
                graph = plan[(fixture, arm, seed)]
                text = json.dumps(graph, indent=2, sort_keys=True,
                                  ensure_ascii=False) + "\n"
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                label = "%s/%s_seed%d" % (fixture, arm, seed)
                print("")
                print("[LEG] %s  sha256=%s  sampler=%s steps=%s shift=%s seed=%s"
                      % (label, digest[:16],
                         graph["ksampler"]["inputs"]["sampler_name"],
                         graph["ksampler"]["inputs"]["steps"],
                         graph["modelsampling"]["inputs"]["shift"],
                         graph["ksampler"]["inputs"]["seed"]))
                started = time.time()
                try:
                    queued = post_json("%s/prompt" % SERVER, {"prompt": graph})
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", "replace")[:2000]
                    print("[FAULT] %s: submit rejected: %s" % (label, detail))
                    fixture_legs.append({"leg": label, "fixture": fixture, "arm": arm,
                                         "seed": seed, "sha256": digest,
                                         "status": "REJECTED", "detail": detail})
                    continue
                prompt_id = queued.get("prompt_id")
                print("[QUEUED] %s prompt_id=%s" % (label, prompt_id))
                result = wait_for_leg(prompt_id, started)
                elapsed = round(time.time() - started, 1)
                images = []
                for output in (result["outputs"] or {}).values():
                    for image in output.get("images") or []:
                        images.append(image)
                print("[DONE] %s status=%s frames=%d elapsed=%ss"
                      % (label, result["status"], len(images), elapsed))
                if result["status"] != "success":
                    print("[FAULT] %s: %s"
                          % (label, json.dumps(result.get("messages"))[:1500]))
                fixture_legs.append({
                    "leg": label, "fixture": fixture, "arm": arm, "seed": seed,
                    "sha256": digest, "prompt_id": prompt_id,
                    "status": result["status"], "elapsed_s": elapsed,
                    "frame_count": len(images),
                    "subfolder": images[0]["subfolder"] if images else None,
                    "first_frame": images[0]["filename"] if images else None,
                    "last_frame": images[-1]["filename"] if images else None,
                    "messages": result.get("messages", []),
                })
                legs.append(fixture_legs[-1])
                io.open(receipts / "RENDER.json", "w", encoding="utf-8",
                        newline="\n").write(
                    json.dumps({"server": SERVER, "fixture": fixture, "seeds": SEEDS,
                                "arms": ARMS, "output_prefix": OUT_PREFIX,
                                "fps": 25, "legs": fixture_legs},
                               indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    ok = sum(1 for leg in legs if leg["status"] == "success")
    print("")
    print("[RENDER] %d/%d leg(s) succeeded." % (ok, len(legs)))
    for leg in legs:
        print("  %-34s %-10s frames=%s elapsed=%ss"
              % (leg["leg"], leg["status"], leg.get("frame_count"),
                 leg.get("elapsed_s")))
    return 0 if ok == len(legs) else 2


if __name__ == "__main__":
    sys.exit(main())
