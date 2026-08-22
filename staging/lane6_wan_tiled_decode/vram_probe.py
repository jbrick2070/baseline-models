"""Lane 6's missing half: what does REMOVING tiled decode cost in VRAM?

The lane measured the quality side and found no seam plus a 4-5x temporal cost
to tiling. It did not measure the cost side at all, and the operator cannot rule
on a trade with one half missing. Tiling exists for VRAM; nobody has priced
removing it on this box.

TWO THINGS THE LANE ITSELF GOT WRONG THAT THIS FIXES:

  * The leg timings were confounded. ComfyUI served the second arm of each pair
    the cached KSampler output, so the ~180s-vs-18s split measured "sampled"
    against "did not sample", not tiled against untiled. Here each arm runs on
    its OWN FRESH SERVER, so neither can inherit a cache or another arm's
    residency.
  * No per-arm peak was taken. Here an NVML sampler runs for the whole
    submission window, so the peak spans encode, sample and decode.

Run: vram_probe.py ours     (then reboot the server)
     vram_probe.py candidate
Each invocation probes ONE arm and appends to VRAM_PROBE.json, because a clean
comparison needs a fresh process per arm and that cannot be done in one run.
"""
from __future__ import annotations

import io
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "ComfyUI-OldTimeRadio" / "scripts"))

SERVER = "http://127.0.0.1:8000"
FIXTURE = "crowd"
SEED = 42
OUT = HERE / "VRAM_PROBE.json"


class Peak:
    """Machine-wide VRAM peak in MiB across a window."""

    def __init__(self, interval_s: float = 0.2) -> None:
        self._i = interval_s
        self._stop = threading.Event()
        self.peak = 0
        self.baseline = 0
        self._t: threading.Thread | None = None

    def _read(self) -> int:
        try:
            import pynvml
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            return int(pynvml.nvmlDeviceGetMemoryInfo(h).used // (1024 * 1024))
        except Exception:
            return 0

    def _run(self) -> None:
        try:
            import pynvml
            pynvml.nvmlInit()
        except Exception:
            return
        self.baseline = self._read()
        self.peak = self.baseline
        while not self._stop.is_set():
            self.peak = max(self.peak, self._read())
            self._stop.wait(self._i)

    def start(self):
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        time.sleep(1.0)          # let the baseline land before submitting
        return self

    def stop(self) -> tuple[int, int]:
        self._stop.set()
        if self._t:
            self._t.join(timeout=5)
        return self.baseline, self.peak


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arm = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if arm not in ("ours", "candidate"):
        raise SystemExit("usage: vram_probe.py ours|candidate")

    graph_path = HERE / FIXTURE / f"arm_{arm}.json"
    graph = json.loads(io.open(graph_path, encoding="utf-8").read())

    # Seed and a UNIQUE save prefix, so nothing can be served from cache and the
    # frames do not collide with the lane's own render.
    for node in graph.values():
        if node["class_type"] == "KSampler":
            node["inputs"]["seed"] = SEED
    graph["save"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["vaedecode", 0],
                   "filename_prefix": f"baseline_output/lane6_vram_probe/"
                                      f"{arm}/frame"},
    }

    print(f"[ARM] {arm}  graph={graph_path.name}")
    peak = Peak().start()
    t0 = time.time()
    data = json.dumps({"prompt": graph}).encode("utf-8")
    req = urllib.request.Request(SERVER + "/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        pid = json.loads(r.read().decode("utf-8"))["prompt_id"]
    print(f"[QUEUED] {pid}")
    while True:
        time.sleep(5)
        with urllib.request.urlopen(f"{SERVER}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode("utf-8"))
        if pid in hist:
            status = hist[pid].get("status", {}).get("status_str", "?")
            break
    base, pk = peak.stop()
    elapsed = round(time.time() - t0, 1)
    rec = {"arm": arm, "fixture": FIXTURE, "seed": SEED, "status": status,
           "baseline_mib": base, "peak_mib": pk, "delta_mib": pk - base,
           "elapsed_s": elapsed, "prompt_id": pid}
    print(json.dumps(rec, indent=2))

    all_recs = []
    if OUT.exists():
        all_recs = json.loads(io.open(OUT, encoding="utf-8").read())
    all_recs = [r for r in all_recs if r.get("arm") != arm] + [rec]
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(all_recs, indent=2, sort_keys=True) + "\n")

    if len({r["arm"] for r in all_recs}) == 2:
        o = next(r for r in all_recs if r["arm"] == "ours")
        c = next(r for r in all_recs if r["arm"] == "candidate")
        print("\n=== BOTH ARMS PROBED ===")
        print(f"  tiled    peak {o['peak_mib']} MiB  (delta {o['delta_mib']})"
              f"  {o['elapsed_s']}s")
        print(f"  untiled  peak {c['peak_mib']} MiB  (delta {c['delta_mib']})"
              f"  {c['elapsed_s']}s")
        print(f"  removing tiling costs {c['peak_mib'] - o['peak_mib']:+d} MiB "
              f"and {c['elapsed_s'] - o['elapsed_s']:+.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
