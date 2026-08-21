"""Can the local IMAGE engines be graph-diffed at all? A structural probe.

The 2026-08-21 fleet sweep covered `registered_video_engines: 30` and nothing
else, because `diffomatic_fleet.ENGINE_ROOT` is pinned to
`nodes/_otr_video_engines`. The operator asked whether TTS, image and music get
diffed too. The answer splits, and this probe establishes the image half.

**AUDIO CANNOT BE GRAPH-DIFFED AT ALL.** `eng_kokoro`, `eng_bark`,
`eng_chatterbox`, `eng_musicgen`, `eng_stable_audio*` contain no `class_type`,
no graph and no builder -- they import their model and run it directly in
Python. There is no ComfyUI graph to compare against an official template, so a
graph differ has nothing to bite on. That is a structural fact, not a gap to
close, and it is why this probe covers image only.

**IMAGE CAN BE**, but not through `build_api_graph` as it stands. Two reasons,
both found by reading the engines:

1. Their builders are named per-family -- `_build_zimage_graph`,
   `_build_flux_graph`, `_build_lumina_graph`, `_build_klein_graph` -- not
   `_build_graph`. (The `builder_name` parameter added for lane 5 covers this.)
2. They take `(params, wire)`, NOT the video fixture's
   `(plan, length, width, height)`. `params` comes from a sibling method that
   takes the fixture's `request` -- e.g. `_zimage_params(request)`.

So the image contract is a TWO-STEP build. This probe does that step and
reports what each engine's graph actually contains, so a real image fleet diff
can be scoped against evidence instead of guesswork.

Writes nothing but a receipt; renders nothing; touches no GPU.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diffomatic  # noqa: E402

OUT = HERE.parent / "receipts" / "image_fleet_probe.json"

# builder -> the params method that feeds it, discovered by reading the engines.
BUILDERS = {
    "z_image_turbo": ("_build_zimage_graph", "_zimage_params"),
    "flux_gen1": ("_build_flux_graph", "_flux_params"),
    "lumina_image": ("_build_lumina_graph", "_lumina_params"),
    "flux2_klein": ("_build_klein_graph", "_klein_params"),
}


def probe():
    import importlib
    results = {}
    with diffomatic._isolated_otr_nodes(diffomatic.OTR_ROOT):
        registry = importlib.import_module("nodes._otr_image_engines.registry")
        try:
            bridge = importlib.import_module(
                "nodes._otr_video_engines.wrapper_bridge")
            wire = bridge.Wire
        except Exception as exc:  # pragma: no cover - reported, not raised
            return {"error": "cannot import wrapper_bridge.Wire: %r" % exc}

        for name, (builder_name, params_name) in sorted(BUILDERS.items()):
            entry = {"builder": builder_name, "params_method": params_name}
            try:
                engine = registry.get_engine(name)
            except Exception as exc:
                entry["status"] = "engine unresolved: %r" % exc
                results[name] = entry
                continue

            builder = getattr(engine, builder_name, None)
            params_fn = getattr(engine, params_name, None)
            if builder is None:
                entry["status"] = "no builder %r" % builder_name
                results[name] = entry
                continue
            if params_fn is None:
                found = [m for m in dir(engine)
                         if m.endswith("_params") and not m.startswith("__")]
                entry["status"] = "no params method %r" % params_name
                entry["params_methods_present"] = sorted(found)
                results[name] = entry
                continue

            try:
                fixture = diffomatic._builder_fixture(engine)
            except Exception as exc:
                # The differ REFUSES to invent a fixture, correctly. The
                # video fixture needs a declared render_canvas; image
                # engines take width/height per request instead, so they
                # need their own grounded fixture contract.
                entry["status"] = "no usable fixture: %s: %s" % (
                    type(exc).__name__, exc)
                results[name] = entry
                continue
            try:
                params = params_fn(fixture["request"])
            except Exception as exc:
                entry["status"] = "params build failed: %s: %s" % (
                    type(exc).__name__, exc)
                results[name] = entry
                continue

            try:
                graph = builder(params, wire)
            except Exception as exc:
                entry["status"] = "graph build failed: %s: %s" % (
                    type(exc).__name__, exc)
                entry["param_keys"] = sorted(params) if hasattr(params, "keys") else None
                results[name] = entry
                continue

            logical = sorted({str(n.get("class")) for n in graph.values()
                              if isinstance(n, dict)})
            entry.update({
                "status": "ok",
                "nodes": len(graph),
                "logical_classes": logical,
                "param_keys": sorted(params) if hasattr(params, "keys") else None,
            })
            results[name] = entry
    return results


def main() -> int:
    results = probe()
    if "error" in results and not any(isinstance(v, dict) for v in results.values()):
        print("[BLOCKED] %s" % results["error"])
        return 1
    print("%-16s %-8s %s" % ("engine", "status", "detail"))
    for name in sorted(results):
        e = results[name]
        if e.get("status") == "ok":
            print("%-16s %-8s %d nodes | %s"
                  % (name, "OK", e["nodes"], ", ".join(e["logical_classes"][:8])))
        else:
            print("%-16s %-8s %s" % (name, "BLOCKED", e.get("status")))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps({
        "probe": "can the local image engines be graph-diffed",
        "audio_finding": ("audio engines are NOT graph-based -- eng_kokoro, "
                          "eng_bark, eng_chatterbox, eng_musicgen, "
                          "eng_stable_audio* import their model and run it in "
                          "Python. No ComfyUI graph exists to diff. Structural, "
                          "not a gap."),
        "image_contract": ("two-step: params = engine.<family>_params(request), "
                           "then graph = engine.<family>_build_graph(params, wire). "
                           "Builders are family-named, so build_api_graph needs "
                           "its builder_name argument plus a params step."),
        "cloud_engines_excluded": ("cloud_flux_pro, cloud_krea_2_turbo, "
                                   "cloud_luma_photon_flash, cloud_nano_banana_2, "
                                   "cloud_seedream_2, google_image, ideo carry no "
                                   "graph builder at all -- they are API calls."),
        "results": results,
    }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("\n[RECEIPT] %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
