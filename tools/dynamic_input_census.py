"""Census: every V3 dynamic input on the live server, and every OTR engine
graph that feeds one.

Written because ONE of these (ResizeImageMaskNode.resize_type, a
COMFY_DYNAMICCOMBO_V3) silently killed all twelve lane 2 legs: the engine
authors it as a nested dict, the in-process bridge accepts that, and the HTTP
prompt format wants dot-flattened keys -- the dict left the argument unmapped
and the node raised TypeError. The operator's question: how many MORE of these
are waiting in graphs we have not submitted yet?

Two passes:
  1. /object_info sweep -- every node class exposing a dynamic io_type
     (DYNAMICCOMBO / DYNAMICSLOT / AUTOGROW / MATCHTYPE), so future preflights
     know the full population.
  2. Engine sweep -- build every OTR engine graph the differ can build and
     report every dict-valued input literal: each one is a submission that
     would have failed exactly like lane 2 did before the flattener.

usage: dynamic_input_census.py [--server http://127.0.0.1:8000]
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import diffomatic  # noqa: E402

DYNAMIC_TYPES = ("COMFY_DYNAMICCOMBO_V3", "COMFY_DYNAMICSLOT_V3",
                 "COMFY_AUTOGROW_V3", "COMFY_MATCHTYPE_V3")
# Engines the assembly line and its candidate list touch, checked first;
# everything else the registries expose is swept after.
PRIORITY = ("eng_wan_ti2v", "eng_ltx25", "eng_ltx_video", "eng_ltx_av",
            "eng_wan_i2v")


def server_census(server: str) -> dict:
    with urllib.request.urlopen("%s/object_info" % server, timeout=300) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    hits = {}
    for class_type, spec in info.items():
        for section in ("required", "optional"):
            for input_name, decl in ((spec.get("input") or {}).get(section) or {}).items():
                if isinstance(decl, list) and decl and decl[0] in DYNAMIC_TYPES:
                    hits.setdefault(class_type, []).append(
                        {"input": input_name, "io_type": decl[0], "section": section})
    return hits


def engine_dict_inputs(identifier: str):
    api, _prov = diffomatic.build_api_graph(identifier)
    # build_api_graph now FLATTENS dynamic dicts, so re-read the raw builder
    # output to see what the engine actually authors.
    with diffomatic.resolved_engine(identifier) as engine:
        raw, _fixture = diffomatic._invoke_graph_builder(engine)
    found = []
    for node_id, node in raw.items():
        for input_name, value in (node.get("inputs") or {}).items():
            if isinstance(value, dict):
                found.append({"node": str(node_id), "class": api[str(node_id)]["class_type"],
                              "input": str(input_name), "value": value})
    return found


def main(argv):
    server = "http://127.0.0.1:8000"
    if len(argv) == 2 and argv[0] == "--server":
        server = argv[1]

    print("=== PASS 1: dynamic inputs registered on the live server ===")
    try:
        hits = server_census(server)
    except Exception as exc:
        hits = {}
        print("[WARN] server census unavailable (%s); engine pass still runs" % exc)
    for class_type in sorted(hits):
        for entry in hits[class_type]:
            print("  %-34s %-18s %s (%s)" % (class_type, entry["input"],
                                             entry["io_type"], entry["section"]))
    print("  -> %d class(es) carry dynamic inputs" % len(hits))

    print("\n=== PASS 2: OTR engine graphs that author dict-valued inputs ===")
    with diffomatic._isolated_otr_nodes(diffomatic.OTR_ROOT):
        import importlib
        names = []
        for kind in ("video", "image"):
            try:
                registry = importlib.import_module("nodes._otr_%s_engines.registry" % kind)
                for name in registry.all_engine_names():
                    names.append("%s:%s" % (kind, name))
            except Exception as exc:
                print("[WARN] %s registry: %s" % (kind, exc))
    ordered = [n for n in names if any(p.replace("eng_", "") in n for p in PRIORITY)]
    ordered += [n for n in names if n not in ordered]

    exposed = {}
    for identifier in ordered:
        try:
            found = engine_dict_inputs(identifier)
        except Exception as exc:
            print("  %-26s UNBUILDABLE: %s" % (identifier, str(exc)[:90]))
            continue
        if found:
            exposed[identifier] = found
            for f in found:
                print("  %-26s %s(%s).%s = %s"
                      % (identifier, f["class"], f["node"], f["input"],
                         json.dumps(f["value"])[:80]))
        else:
            print("  %-26s clean (no dict-valued inputs)" % identifier)

    print("\n=== VERDICT ===")
    if exposed:
        print("%d engine(s) author dynamic-dict inputs; each would have failed "
              "over the API before the flattener:" % len(exposed))
        for identifier in exposed:
            print("  - %s" % identifier)
    else:
        print("No engine beyond ltx25 authors dict-valued inputs today.")

    out = TOOLS.parent / "receipts" / "dynamic_input_census.json"
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"server_dynamic_classes": hits,
                    "engine_dict_inputs": exposed}, indent=2, sort_keys=True,
                   default=str) + "\n")
    print("[RECEIPT] %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
