"""Render lane 6: every fixture, two arms, two seeds, sequentially, one server.

Derived from lane 4's runner, which is the shipped harness for a wan_ti2v class
swap; only the arm names, the output prefix, the preflight class list and the
declared contrast differ. Same receipts discipline as lanes 1-4: live
``/object_info`` preflight for every class and model filename, purity re-proved
on the graphs actually QUEUED (not merely on the staged files), outputs read
back from ``/history``, temporal stats per leg.

THE CONTRAST: ``vaedecode`` swaps ``VAEDecodeTiled`` -> ``VAEDecode``.

Best effort per the no-VRAM-ceremony ruling, and here the direction is worth
naming in advance: **tiled decode exists to hold the VRAM peak flat, so the
UNTILED candidate is the arm that may OOM**, and on a long clip it is the more
likely of the two to do so. An OOM on the candidate is a plain recorded fault
and marks that cell infeasible; it is not a project, and it is also a result --
"the compromise cannot be removed on this box" is a real answer to this lane.

The swap drops four tiling literals (``tile_size``, ``overlap``,
``temporal_size``, ``temporal_overlap``) because ``VAEDecode`` has no such
inputs. Each is named to the gate via ``--expect-drop``, which is only honoured
at a node that ALSO carries a declared class swap -- so the changed set still
equals the declared set exactly, and a key vanishing anywhere else still aborts
the lane.

Seed node is ``KSampler.seed``; the terminal is ``vaedecode`` and a
``SaveImage`` is appended identically to both arms (native 832x480 frames).

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
import temporal_stats  # noqa: E402

SERVER = "http://127.0.0.1:8000"
SEEDS = [42, 20260821]
ARMS = ["ours", "candidate"]
OUT_PREFIX = "baseline_output/lane6_wan_tiled_decode"
LEG_TIMEOUT_S = 2 * 60 * 60
# class -> file-carrying inputs to confirm against the live enum options.
# BOTH encoder loaders are listed: the arms load different classes, and a lane
# whose candidate file is missing must fail at preflight, not at submit.
MODEL_INPUTS = {
    "UnetLoaderGGUF": ["unet_name"],
    "CLIPLoaderGGUF": ["clip_name"],
    "VAELoader": ["vae_name"],
    "LoadImage": ["image"],
}


def get_json(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def enum_options(spec):
    """Selectable values of a combo input, legacy or V3 shape.

    Legacy: ``[[opt, ...], {...}]``. V3: ``["COMBO", {"options": [opt, ...]}]``
    -- LatentUpscaleModelLoader ships the V3 shape and the legacy-only reader
    called its installed model missing (lane 2 preflight, 2026-08-21).
    """
    if isinstance(spec, list) and spec:
        if isinstance(spec[0], list):
            return list(spec[0])
        if spec[0] == "COMBO" and len(spec) > 1 and isinstance(spec[1], dict):
            return list(spec[1].get("options") or [])
    return []


def preflight(graphs, object_info):
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
            for input_name in MODEL_INPUTS.get(class_type, []):
                wanted = node["inputs"].get(input_name)
                spec = ((object_info[class_type].get("input") or {}).get("required") or {})
                options = enum_options(spec.get(input_name))
                if not options:
                    faults.append("%s.%s exposes no selectable values"
                                  % (class_type, input_name))
                elif wanted not in options:
                    faults.append("%s.%s=%r is not installed (server offers %d)"
                                  % (class_type, input_name, wanted, len(options)))
    for class_type in sorted(seen):
        print("[OBJECT_INFO] %s: present" % class_type)
    return faults


def leg_prefix(fixture, arm, seed):
    return "%s/%s/%s_seed%d/frame" % (OUT_PREFIX, fixture, arm, seed)


def build_submission(fixture, arm, seed):
    graph = json.loads(io.open(HERE / fixture / ("arm_%s.json" % arm),
                               encoding="utf-8").read())
    graph["ksampler"]["inputs"]["seed"] = seed
    graph["save"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["vaedecode", 0],
                   "filename_prefix": leg_prefix(fixture, arm, seed)},
    }
    return graph


def gate_submissions(fixture, seed, submitted, receipts, manifest):
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
        'save.filename_prefix="%s"' % leg_prefix(fixture, "candidate", seed),
    ]
    argv = [str(paths["ours"]), str(paths["candidate"])]
    for item in declared:
        argv += ["--expect", item]
    # VAEDecodeTiled -> VAEDecode drops four tiling literals the target class
    # does not accept. Each is named, and the gate only honours a drop at a
    # node that also carries a declared class swap.
    argv += ["--expect-class", "vaedecode=VAEDecode"]
    for dropped in ("tile_size", "overlap", "temporal_size",
                    "temporal_overlap"):
        argv += ["--expect-drop", "vaedecode.%s" % dropped]
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
        except json.JSONDecodeError:
            # A restarting server can answer with an HTML error page; that is
            # a hiccup to ride out, not a reason to abandon the queued legs.
            time.sleep(10)
            continue
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status") or {}
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                return {"status": status.get("status_str", "unknown"),
                        "outputs": entry.get("outputs") or {},
                        "messages": status.get("messages") or []}
        time.sleep(10)


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

    # NO ADAPT ON THIS LANE. Lane 3 checked ManualSigmas here because its graphs
    # carried a sigma-injector swap; lane 4's graphs contain no such node (10
    # classes, none of them ManualSigmas). That check survived the byte-copy from
    # lane 3 into unchanged lines -- where a diff is blind -- and would have
    # aborted this lane on any server without an unrelated custom node.
    # Caught by two independent reviewers, 2026-08-21.

    plan = {}
    for fixture in wanted:
        for seed in SEEDS:
            for arm in ARMS:
                plan[(fixture, arm, seed)] = build_submission(fixture, arm, seed)

    named = {"%s_%s_%d" % k: g for k, g in plan.items()}
    faults = preflight(named, object_info)
    if faults:
        for fault in sorted(set(faults)):
            print("[FAIL] %s" % fault)
        print("[PREFLIGHT] FAILED -- nothing queued.")
        return 1
    print("[PREFLIGHT] PASSED -- every class and model filename is live on this server.")

    for fixture in wanted:
        receipts = HERE / fixture / "render"
        receipts.mkdir(parents=True, exist_ok=True)
        manifest = {}
        for seed in SEEDS:
            arms_for_seed = {arm: plan[(fixture, arm, seed)] for arm in ARMS}
            if not gate_submissions(fixture, seed, arms_for_seed, receipts, manifest):
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
                print("[LEG] %s  sha256=%s  encoder=%s seed=%s"
                      % (label, digest[:16],
                         graph["clip"]["inputs"]["clip_name"],
                         graph["ksampler"]["inputs"]["seed"]))
                started = time.time()
                try:
                    queued = post_json("%s/prompt" % SERVER, {"prompt": graph})
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", "replace")[:2000]
                    print("[FAULT] %s: submit rejected: %s" % (label, detail))
                    fixture_legs.append({"leg": label, "fixture": fixture,
                                         "arm": arm, "seed": seed,
                                         "sha256": digest, "status": "REJECTED",
                                         "detail": detail})
                    legs.append(fixture_legs[-1])
                    continue
                prompt_id = queued.get("prompt_id")
                print("[QUEUED] %s prompt_id=%s" % (label, prompt_id))
                result = wait_for_leg(prompt_id, started)
                elapsed = round(time.time() - started, 1)
                images = []
                for output in (result["outputs"] or {}).values():
                    images.extend(output.get("images") or [])
                print("[DONE] %s status=%s frames=%d elapsed=%ss"
                      % (label, result["status"], len(images), elapsed))
                if result["status"] != "success":
                    print("[FAULT] %s: %s"
                          % (label, json.dumps(result.get("messages"))[:1500]))
                record = {
                    "leg": label, "fixture": fixture, "arm": arm, "seed": seed,
                    "sha256": digest, "prompt_id": prompt_id,
                    "status": result["status"], "elapsed_s": elapsed,
                    "frame_count": len(images),
                    "subfolder": images[0]["subfolder"] if images else None,
                    "first_frame": images[0]["filename"] if images else None,
                    "last_frame": images[-1]["filename"] if images else None,
                    "messages": result.get("messages", []),
                }
                if result["status"] == "success" and record["subfolder"]:
                    stats = temporal_stats.leg_stats(
                        temporal_stats.COMFY_OUTPUT / record["subfolder"])
                    record["temporal"] = stats
                    # leg_stats returns {"error": ...} on a short/empty leg, so
                    # the delta keys are not guaranteed; reading them blind turns
                    # a recorded fault into a KeyError that kills the campaign.
                    if "error" in stats:
                        print("[TEMPORAL] %s UNAVAILABLE: %s"
                              % (label, stats["error"]))
                    else:
                        print("[TEMPORAL] %s mean=%.3f max=%.3f"
                              % (label, stats["mean_abs_delta"],
                                 stats["max_abs_delta"]))
                fixture_legs.append(record)
                legs.append(record)
                io.open(receipts / "RENDER.json", "w", encoding="utf-8",
                        newline="\n").write(
                    json.dumps({"server": SERVER, "fixture": fixture,
                                "seeds": SEEDS, "arms": ARMS,
                                "output_prefix": OUT_PREFIX, "fps": 25,
                                "legs": fixture_legs},
                               indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    ok = sum(1 for leg in legs if leg["status"] == "success")
    print("")
    print("[RENDER] %d/%d leg(s) succeeded." % (ok, len(legs)))
    for leg in legs:
        print("  %-30s %-10s frames=%s elapsed=%ss"
              % (leg["leg"], leg["status"], leg.get("frame_count"),
                 leg.get("elapsed_s")))
    return 0 if ok == len(legs) else 2


if __name__ == "__main__":
    sys.exit(main())
