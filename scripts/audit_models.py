"""
Audit installed models under C:\\ComfyUI-Models and map against baseline coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

MODEL_ROOT = Path("C:/ComfyUI-Models")
EXTENSIONS = {".safetensors", ".gguf", ".pt", ".pth", ".bin", ".ckpt", ".onnx"}

def scan_models(root: Path = MODEL_ROOT) -> dict[str, list[dict]]:
    categories: dict[str, list[dict]] = {}
    if not root.exists():
        return categories

    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in EXTENSIONS:
            rel = p.relative_to(root)
            top_dir = rel.parts[0] if len(rel.parts) > 1 else "root"
            size_gb = p.stat().st_size / (1024 ** 3)
            info = {
                "name": p.name,
                "relative_path": str(rel).replace("\\", "/"),
                "size_gb": round(size_gb, 2),
                "extension": p.suffix.lower(),
            }
            categories.setdefault(top_dir, []).append(info)

    for cat in categories:
        categories[cat].sort(key=lambda x: x["relative_path"])
    return categories


def main() -> None:
    models = scan_models()
    total_files = sum(len(items) for items in models.values())
    total_gb = sum(item["size_gb"] for items in models.values() for item in items)
    print(f"Scanned {total_files} model files ({total_gb:.2f} GB) under {MODEL_ROOT}")
    for cat, items in sorted(models.items()):
        cat_gb = sum(i["size_gb"] for i in items)
        print(f"\n[{cat}] ({len(items)} files, {cat_gb:.2f} GB):")
        for item in items:
            print(f"  {item['size_gb']:6.2f} GB | {item['relative_path']}")


if __name__ == "__main__":
    main()
