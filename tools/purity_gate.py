"""Prove two staged A/B arms differ by EXACTLY the knobs the lane declared.

Bible 12.121: an uncontrolled second variable sends every arm of a visual A/B
to the same wrong verdict, and single-variable discipline is routinely applied
to the graph delta while the shared inputs drift. This is the mechanical half
of that rule -- verify arm purity with a deterministic diff, not a model pass.

It is deliberately structural rather than textual: a text diff cannot tell a
reordered key from a changed one, and cannot tell a changed literal from a
rewired link. Any wiring difference is a topology change and fails the gate
outright, whatever the lane declared.

Usage:
    python purity_gate.py <arm_a.json> <arm_b.json> --contrast <STAGING.json>
    python purity_gate.py a.json b.json --expect node.input=value [...]

Exit 0 = pure; the lane may render. Exit 1 = ABORT THE LANE.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path


def _is_wire(value) -> bool:
    """A ComfyUI API link: ``[node_id, output_slot]``."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
    )


def _walk(value, path: str, out: dict) -> None:
    """Flatten one input into ``{dotted path: leaf}``, wires kept whole."""
    if _is_wire(value):
        out[path] = ("WIRE", f"{value[0]}:{value[1]}")
        return
    if isinstance(value, dict):
        if not value:
            out[path] = ("LITERAL", "{}")
            return
        for key in sorted(value):
            _walk(value[key], f"{path}.{key}", out)
        return
    if isinstance(value, list):
        if not value:
            out[path] = ("LITERAL", "[]")
            return
        for index, item in enumerate(value):
            _walk(item, f"{path}[{index}]", out)
        return
    out[path] = ("LITERAL", value)


def flatten(graph: dict) -> dict:
    flat = {}
    for node_id in sorted(graph):
        node = graph[node_id]
        flat[f"{node_id}.__class__"] = ("CLASS", node.get("class_type"))
        for key in sorted(node.get("inputs") or {}):
            _walk(node["inputs"][key], f"{node_id}.{key}", flat)
    return flat


def load(path: Path) -> dict:
    graph = json.loads(io.open(path, encoding="utf-8").read())
    if not isinstance(graph, dict) or not graph:
        raise SystemExit(f"[FAIL] {path.name}: not a non-empty API graph")
    for node_id, node in graph.items():
        if not isinstance(node, dict) or "class_type" not in node:
            raise SystemExit(f"[FAIL] {path.name}: node {node_id!r} is not API-shaped")
    return graph


def verify_manifest(manifest: Path, arms: dict[str, Path]) -> tuple[list[str], list[str]]:
    """Confirm the staged bytes still hash to what staging recorded.

    Returns ``(log lines, failures)``.  The failures are returned rather than
    merely printed because an arm whose bytes no longer match its manifest is
    the exact fault the downstream receipts assume was checked -- printing it
    while passing the gate would be worse than not checking at all.
    """
    lines, failures = [], []
    if not manifest.exists():
        return ([f"[FAIL] no {manifest.name}; arm identity is unproven"],
                [f"[FAIL] no {manifest.name}; arm identity is unproven"])
    recorded = {}
    for line in io.open(manifest, encoding="utf-8").read().splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            recorded[name.strip()] = digest
    for path in arms.values():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = recorded.get(path.name)
        if expected is None:
            failures.append(f"[FAIL] {path.name} is absent from {manifest.name}")
        elif expected != actual:
            failures.append(
                f"[FAIL] {path.name} sha256 {actual[:16]} != recorded {expected[:16]}")
        else:
            lines.append(f"[OK]   {path.name} sha256 {actual[:16]} matches {manifest.name}")
    return lines, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm_a")
    parser.add_argument("arm_b")
    parser.add_argument("--contrast", help="STAGING.json carrying declared_contrast")
    parser.add_argument("--expect", action="append", default=[],
                        help="declared delta as path=json_value")
    parser.add_argument("--expect-class", action="append", default=[],
                        dest="expect_class", metavar="NODE=ClassName",
                        help="declared NODE CLASS swap at exactly one node, e.g. "
                             "clip=CLIPLoader. Every OTHER class change still "
                             "fails, and wiring changes still fail unconditionally.")
    parser.add_argument("--expect-drop", action="append", default=[],
                        dest="expect_drop", metavar="NODE.key",
                        help="an input the declared class swap legitimately "
                             "REMOVES, e.g. vaedecode.tile_size. Only honoured "
                             "at a node that also carries --expect-class; a key "
                             "vanishing anywhere else is still a hard fail.")
    args = parser.parse_args(argv)

    path_a, path_b = Path(args.arm_a).resolve(), Path(args.arm_b).resolve()
    graph_a, graph_b = load(path_a), load(path_b)

    declared: dict = {}
    if args.contrast:
        receipt = json.loads(io.open(args.contrast, encoding="utf-8").read())
        declared = dict(receipt.get("declared_contrast") or {})
    for item in args.expect:
        key, _, raw = item.partition("=")
        declared[key] = json.loads(raw)

    # A declared CLASS swap is the contrast on a loader/precision lane. It stays
    # OPT-IN and node-specific: the default remains "any class change aborts the
    # lane", because an UNdeclared class change is exactly the uncontrolled
    # second variable Bible 12.121 was promoted for.
    declared_classes: dict = {}
    for item in args.expect_class:
        node, _, class_name = item.partition("=")
        if not node or not class_name:
            raise SystemExit("[FAIL] --expect-class wants NODE=ClassName, got %r" % item)
        declared_classes[f"{node}.__class__"] = class_name

    # A declared class swap between classes with DIFFERENT input signatures
    # legitimately drops keys -- VAEDecodeTiled -> VAEDecode loses tile_size,
    # overlap, temporal_size and temporal_overlap because the target class has
    # no such inputs. Carrying one across would not be a smaller contrast, it
    # would be an invalid graph. (Lane 4 never hit this because CLIPLoaderGGUF
    # and CLIPLoader share a key set.)
    #
    # Two deliberate constraints keep this from becoming a hole:
    #   * each dropped key must be named EXPLICITLY, so the changed set still
    #     equals the declared set exactly; and
    #   * a drop is only honoured at a node that ALSO carries a declared class
    #     swap. A key vanishing anywhere else stays a hard fail, because that
    #     is the uncontrolled second variable Bible 12.121 was promoted for.
    declared_drops: set = set()
    for item in args.expect_drop:
        node = item.split(".", 1)[0]
        if f"{node}.__class__" not in declared_classes:
            raise SystemExit(
                "[FAIL] --expect-drop %r names a node with no declared class "
                "swap; a key that vanishes without one is a staging fault, "
                "not a contrast" % item)
        declared_drops.add(item)

    if not declared and not declared_classes:
        raise SystemExit("[FAIL] no declared contrast set; refusing to pass a lane blind")

    print(f"[ARM A] {path_a}")
    print(f"[ARM B] {path_b}")
    manifest_lines, manifest_failures = verify_manifest(
        path_a.parent / "ARMS.sha256", {"a": path_a, "b": path_b})
    for line in manifest_lines:
        print(line)

    flat_a, flat_b = flatten(graph_a), flatten(graph_b)
    only_a = sorted(set(flat_a) - set(flat_b))
    only_b = sorted(set(flat_b) - set(flat_a))
    changed = sorted(k for k in set(flat_a) & set(flat_b) if flat_a[k] != flat_b[k])

    failures = list(manifest_failures)
    for key in only_a:
        if key in declared_drops:
            print(f"[OK]   declared DROP {key} = {flat_a[key][1]!r} "
                  f"(absent in B by the declared class swap)")
            continue
        failures.append(f"[FAIL] present only in A: {key} = {flat_a[key][1]!r}")
    for key in only_b:
        failures.append(f"[FAIL] present only in B: {key} = {flat_b[key][1]!r}")

    for key in changed:
        kind_a, value_a = flat_a[key]
        kind_b, value_b = flat_b[key]
        if kind_a == "WIRE" or kind_b == "WIRE":
            failures.append(f"[FAIL] TOPOLOGY differs at {key}: {value_a!r} -> {value_b!r}")
        elif kind_a == "CLASS" or kind_b == "CLASS":
            if declared_classes.get(key) == value_b:
                print(f"[OK]   declared CLASS swap {key}: {value_a!r} -> {value_b!r}")
            else:
                failures.append(
                    f"[FAIL] NODE CLASS differs at {key}: {value_a!r} -> {value_b!r}")
        elif key not in declared:
            failures.append(f"[FAIL] UNDECLARED delta at {key}: {value_a!r} -> {value_b!r}")
        elif value_b != declared[key]:
            failures.append(
                f"[FAIL] {key} moved to {value_b!r}, but the lane declared {declared[key]!r}")
        else:
            print(f"[OK]   declared delta {key}: {value_a!r} -> {value_b!r}")

    for key in sorted(set(declared) - set(changed)):
        failures.append(f"[FAIL] declared delta {key} did not change between the arms")
    for key in sorted(set(declared_classes) - set(changed)):
        failures.append(f"[FAIL] declared CLASS swap {key} did not change between the arms")

    print(f"[COUNT] nodes A={len(graph_a)} B={len(graph_b)} | "
          f"leaves A={len(flat_a)} B={len(flat_b)} | changed={len(changed)}")

    if failures:
        print()
        for line in failures:
            print(line)
        print(f"\n[PURITY GATE] FAILED -- {len(failures)} fault(s). ABORT THE LANE.")
        return 1
    swaps = (f" plus the declared CLASS swap(s) {sorted(declared_classes)}"
             if declared_classes else "")
    print(f"\n[PURITY GATE] PASSED -- changed-parameter set is EXACTLY "
          f"{sorted(declared)} ({len(declared)} knob(s)){swaps}; "
          f"everything else is identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
