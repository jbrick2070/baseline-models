"""Stage lane 1: wan_ti2v -- official sampling recipe vs ours, same everything.

Both arms are generated FROM THE SHIPPING ENGINE GRAPH (eng_wan_ti2v via the
grounded differ's loader), so weights, tiling, encoders, canvas and topology
are byte-identical by construction. Arm OFFICIAL then applies exactly the
three knobs the fleet diff surfaced: sampler uni_pc, steps 20, shift 8.
Arm OURS applies nothing. The contrast is the SAMPLING RECIPE AS A BUNDLE --
if it wins, decompose knob-by-knob afterwards; screening first, forensics
only on a win.
"""
import io, json, hashlib, sys, copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import diffomatic  # noqa: E402

PROMPT = ("1950s black and white cinematic close-up of a military officer's "
          "face, facing the camera, holding his gaze steady, only subtle "
          "breathing and a slight head movement, static locked-off camera, "
          "single continuous shot, no cut, no scene change, no camera move.")
FIXTURE = "portrait_16_9.png"

_loaded = diffomatic._build_engine_graph("eng_wan_ti2v")
# The rebuilt differ returns a LoadedGraph wrapper; the raw node dict is
# .graph_nodes ({id: {"class"/"class_type", "inputs"}}).
g = _loaded.graph_nodes if hasattr(_loaded, "graph_nodes") else _loaded

def to_api(graph):
    api = {}
    for nid, n in graph.items():
        api[str(nid)] = {"class_type": n.get("class", n.get("class_type")),
                         "inputs": dict(n.get("inputs", {}))}
    return api

base = to_api(g)

def find(api, cls):
    hits = [k for k, v in api.items() if v["class_type"] == cls]
    assert len(hits) == 1, (cls, hits)
    return hits[0]

li = find(base, "LoadImage"); base[li]["inputs"]["image"] = FIXTURE
ks = find(base, "KSampler")
ms = find(base, "ModelSamplingSD3")
# Positive prompt = first CLIPTextEncode feeding KSampler.positive.
pos_ref = base[ks]["inputs"]["positive"][0]
base[pos_ref]["inputs"]["text"] = PROMPT

arms = {"ours": {}, "official": {"sampler_name": "uni_pc", "steps": 20, "shift": 8}}
written = {}
for arm, knobs in arms.items():
    a = copy.deepcopy(base)
    if knobs:
        a[ks]["inputs"]["sampler_name"] = knobs["sampler_name"]
        a[ks]["inputs"]["steps"] = knobs["steps"]
        a[ms]["inputs"]["shift"] = knobs["shift"]
    p = HERE / f"arm_{arm}.json"
    txt = json.dumps(a, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    io.open(p, "w", encoding="utf-8", newline="\n").write(txt)
    written[arm] = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    print(f"[STAGED] {p.name}  sha256={written[arm][:16]}  nodes={len(a)}")

io.open(HERE / "ARMS.sha256", "w", encoding="utf-8", newline="\n").write(
    "".join(f"{h}  arm_{k}.json\n" for k, h in written.items()))
print("[CONTRAST] official-vs-ours = {KSampler.sampler_name, KSampler.steps, ModelSamplingSD3.shift} ONLY")
