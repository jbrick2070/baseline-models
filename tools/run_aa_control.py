"""Render one arm TWICE and judge it against itself: the panel's noise floor.

Every A/B verdict on this programme assumes that when two clips are the same
recipe, the panel says TIE. Nothing had ever tested that. Without it there is
no way to tell a real effect from run-to-run nondeterminism plus rater
variance, which is exactly how lane 1's one "unanimous, clear" cell nearly
became a committed win.

The second run re-submits the BYTE-IDENTICAL graph that already ran, changing
only the output destination. It renders into a NEW directory rather than over
the first: the original frames are cited by sha256 in the lane receipts, and
re-running in place would destroy the record that cites them.

The correct result is TIE on every seat. Anything else means the instrument is
reading noise, and every margin it has ever reported is suspect.

usage: run_aa_control.py <submitted_graph.json> <output_prefix>
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

SERVER = "http://127.0.0.1:8000"
TIMEOUT_S = 60 * 60


def get_json(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    source = Path(argv[0]).resolve()
    prefix = argv[1]

    original = json.loads(io.open(source, encoding="utf-8").read())
    graph = json.loads(json.dumps(original))
    graph["save"]["inputs"]["filename_prefix"] = prefix + "/frame"

    changed = [k for k in graph
               if json.dumps(graph[k], sort_keys=True) != json.dumps(original[k], sort_keys=True)]
    if changed != ["save"]:
        print("[FAIL] rerun differs from the original in %s, not just the "
              "destination" % changed)
        return 1
    for node in graph:
        if node == "save":
            continue
        assert graph[node] == original[node]
    print("[A/A] re-submitting %s" % source.name)
    print("[A/A] identical in every node except save.filename_prefix")
    # Lane-agnostic knob echo: name whichever seed/strength literals exist.
    for node_id, input_name in (("ksampler", "seed"), ("ksampler", "sampler_name"),
                                ("ksampler", "steps"), ("modelsampling", "shift"),
                                ("noise", "noise_seed"), ("i2v", "strength"),
                                ("refine_i2v", "strength")):
        node = graph.get(node_id)
        if node and input_name in node.get("inputs", {}):
            print("[A/A] %s.%s = %s" % (node_id, input_name,
                                        node["inputs"][input_name]))

    started = time.time()
    try:
        queued = post_json("%s/prompt" % SERVER, {"prompt": graph})
    except urllib.error.HTTPError as exc:
        print("[FAIL] submit rejected: %s" % exc.read().decode("utf-8", "replace")[:800])
        return 1
    prompt_id = queued.get("prompt_id")
    print("[A/A] queued prompt_id=%s" % prompt_id)

    while True:
        if time.time() - started > TIMEOUT_S:
            print("[FAIL] timeout")
            return 1
        entry = get_json("%s/history/%s" % (SERVER, prompt_id)).get(prompt_id)
        if entry:
            status = (entry.get("status") or {})
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                break
        time.sleep(5)

    images = []
    for output in (entry.get("outputs") or {}).values():
        for image in output.get("images") or []:
            images.append(image)
    elapsed = round(time.time() - started, 1)
    print("[A/A] status=%s frames=%d elapsed=%ss"
          % (status.get("status_str"), len(images), elapsed))

    receipt = {
        "control": "A/A null",
        "source_graph": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "prompt_id": prompt_id,
        "status": status.get("status_str"),
        "frame_count": len(images),
        "elapsed_s": elapsed,
        "output_prefix": prefix,
        "note": ("Same recipe, same seed, same graph -- only the destination "
                 "differs. A panel that does not return TIE here is reading "
                 "noise."),
    }
    destination = source.parent / "AA_CONTROL.json"
    io.open(destination, "w", encoding="utf-8", newline="\n").write(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("[A/A] receipt -> %s" % destination)
    return 0 if status.get("status_str") == "success" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
