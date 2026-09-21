# -*- coding: utf-8 -*-
"""Rebuild offline_manifest.json — curated for visual quality.

Drops heavily fogged/low-detail orbit clips (package encode + model limits).
Never prefers *_up.mp4 as primary (upscale often adds mosaic).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

OPT = Path(__file__).resolve().parent
DEMO = OPT.parent
PROJECT = DEMO.parent

# Mid-frame Laplacian variance thresholds (measured on this package).
# Soft orbits look fogged / mosaicked in the player — exclude from default list.
ORBIT_MIN_SHARPNESS = 5.0
# Prefer these when present (already measured sharp enough).
ORBIT_KEEP = {
    "scenea_2v": 167.0,
    "scenea_4v": 7.2,
    "3a3bc11b9ebb7d44_00017": 16.2,
    "2c9018ef57c6b061_00019": 15.0,
    "45a00d135c5388fc_00012": 9.3,
}
# Known soft — keep out of default curated list.
ORBIT_DROP = {
    "demo",
    "59636f39d067119d_00000",
    "189f95593df3c7f1_00004",
    "4a763e1b87e495a7_00024",
    "0f2197967bb7fa43_00022",
    "357ddf77c7b83cae_00004",
}


def by_prefix(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in root.iterdir():
        if d.is_dir() and len(d.name) >= 2 and d.name[:2].isdigit():
            out[d.name[:2]] = d
    return out


def rel(p: Path) -> str:
    return Path(os.path.relpath(p, PROJECT)).as_posix()


def exists(p: Path | None) -> bool:
    return bool(p and p.exists() and p.stat().st_size > 0)


def pick_orbit(d03: Path, stem: str) -> tuple[Path | None, Path | None]:
    """Return (primary, alt). Prefer native over *_up to avoid upscale mosaic."""
    native = d03 / f"orbit_{stem}.mp4"
    up = d03 / f"orbit_{stem}_up.mp4"
    if exists(native):
        return native, up if exists(up) else None
    if exists(up):
        return up, None
    return None, None


def main() -> None:
    dirs = by_prefix(DEMO)
    d01, d02, d03, d04 = dirs["01"], dirs["02"], dirs["03"], dirs["04"]
    final = PROJECT / "03_最终成果包" / "lagernvs_final"
    scenes: list[dict] = []

    compare_dir = final / "02_top20_gt_pred"
    input_root = final / "07_input_views"
    hq_dir = d03 / "hq_from_still"
    hq_ids = [
        ("eae986c8f31081cc_00051", "eae986c8f31081cc_inputs", "HQ orbit · 6v 神经轨迹"),
        ("e9670b30a2c0e348_00001", "e9670b30a2c0e348_inputs", "HQ orbit · 6v 神经轨迹"),
        ("45a00d135c5388fc_00012", "45a00d135c5388fc_inputs", "HQ orbit · 6v 神经轨迹"),
        ("fbcd62ab8ff30b4f_00013", None, "HQ orbit · Pred 视差轨迹"),
        ("c1ad4232258e87c9_00014", None, "HQ orbit · Pred 视差轨迹"),
    ]
    for cid, inp_name, note in hq_ids:
        cmp = compare_dir / f"COMPARE_{cid}.png"
        if not exists(cmp):
            print("skip missing still", cid)
            continue
        inputs = []
        if inp_name:
            folder = input_root / inp_name
            if folder.exists():
                inputs = [rel(p) for p in sorted(folder.glob("in_*.png")) if exists(p)][:6]
        hq_orbit = hq_dir / f"orbit_hq_{cid}.mp4"
        video = rel(hq_orbit) if exists(hq_orbit) else None
        video_alt = None
        # optional soft legacy orbit as alt only
        if cid in ORBIT_KEEP:
            prim, _alt = pick_orbit(d03, cid)
            if prim and video:
                video_alt = rel(prim)
            elif prim and not video:
                video = rel(prim)
        has_orbit = bool(video)
        scenes.append(
            {
                "id": f"hq_{cid}",
                "title": cid,
                "group": "1 · HQ → Orbit",
                "mode": "video" if has_orbit else "still",
                "still": rel(cmp),
                "video": video,
                "video_alt": video_alt,
                "path_video": None,
                "inputs": inputs,
                "note": note + (f" · {len(inputs)} inputs" if inputs else "") + (" · 可 scrub" if has_orbit else ""),
                "quality": "hq",
                "w": 512,
                "h": 288 if has_orbit else 1090,
            }
        )

    sa_inputs = []
    for name in ["v1.jpg", "v2.jpg", "v3.jpg", "v4.jpg"]:
        p = d01 / "scene_a" / name
        if exists(p):
            sa_inputs.append(rel(p))

    # Sharpest orbit first
    if exists(d03 / "orbit_scenea_2v.mp4"):
        scenes.append(
            {
                "id": "scenea_2v",
                "title": "scene_a · 2 views（最清晰轨道）",
                "group": "2 · Orbit（已筛软糊）",
                "mode": "video",
                "still": None,
                "video": rel(d03 / "orbit_scenea_2v.mp4"),
                "video_alt": None,
                "path_video": rel(d04 / "scenea_2v_240f.mp4") if exists(d04 / "scenea_2v_240f.mp4") else None,
                "inputs": sa_inputs[:2],
                "note": "包内码率最高 · 优先演示",
                "quality": "good",
                "w": 640,
                "h": 408,
            }
        )

    # scenea_4v: use native (avoid upscale mosaic); keep _up as alt
    if exists(d03 / "orbit_scenea_4v.mp4"):
        scenes.append(
            {
                "id": "scenea_4v",
                "title": "scene_a · 4 views",
                "group": "2 · Orbit（已筛软糊）",
                "mode": "video",
                "still": None,
                "video": rel(d03 / "orbit_scenea_4v.mp4"),
                "video_alt": rel(d03 / "orbit_scenea_4v_up.mp4")
                if exists(d03 / "orbit_scenea_4v_up.mp4")
                else None,
                "path_video": rel(d04 / "scenea_4v_240f.mp4") if exists(d04 / "scenea_4v_240f.mp4") else None,
                "inputs": sa_inputs,
                "note": f"4 inputs · 原生编码（非放大）",
                "quality": "ok",
                "w": 640,
                "h": 584,
            }
        )

    for sid in [
        "3a3bc11b9ebb7d44_00017",
        "2c9018ef57c6b061_00019",
        "45a00d135c5388fc_00012",
    ]:
        prim, alt = pick_orbit(d03, sid)
        if not prim:
            print("skip missing orbit", sid)
            continue
        inp_dir = d02 / sid
        inputs = (
            [rel(p) for p in sorted(inp_dir.glob("input_*.png")) if exists(p)]
            if inp_dir.exists()
            else []
        )
        scenes.append(
            {
                "id": sid,
                "title": sid,
                "group": "2 · Orbit（已筛软糊）",
                "mode": "video",
                "still": None,
                "video": rel(prim),
                "video_alt": rel(alt) if alt else None,
                "path_video": None,
                "inputs": inputs,
                "note": f"清晰度合格 · {len(inputs)} inputs",
                "quality": "ok",
                "w": 640,
                "h": 640,
            }
        )

    # Intentionally omit ORBIT_DROP (demo + soft DL3DV) — fog/mosaic too severe for showcase.
    for dropped in sorted(ORBIT_DROP):
        print("curated-out soft orbit:", dropped)

    scenes = [s for s in scenes if s.get("still") or s.get("video")]

    page = Path(os.path.relpath(OPT / "offline_orbit_viewer.html", PROJECT)).as_posix()
    n_still = sum(1 for s in scenes if s.get("still"))
    n_video = sum(1 for s in scenes if s.get("video"))
    n_hq_orbit = sum(1 for s in scenes if str(s.get("id", "")).startswith("hq_") and s.get("video"))
    n_inputs = sum(len(s.get("inputs") or []) for s in scenes)
    manifest = {
        "title": "Interactive demo",
        "subtitle": (
            f"{len(scenes)} 场景 · {n_hq_orbit} 个 HQ 静帧已做成可 scrub Orbit · "
            f"另含合格环绕轨道"
        ),
        "page": page,
        "quality_note": (
            "HQ→Orbit：有 showcase 的用 512 神经相机轨迹；无轨迹的由 Pred 静帧合成视差。"
            "可随时切回 HQ Still 查看 GT|Pred。"
        ),
        "stats": {
            "scenes": len(scenes),
            "hq_stills": n_still,
            "orbit_clips": n_video,
            "hq_orbits": n_hq_orbit,
            "input_thumbs": n_inputs,
            "dropped_soft_orbits": sorted(ORBIT_DROP),
        },
        "scenes": scenes,
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    for out in (OPT / "offline_manifest.json", PROJECT / "offline_manifest.json", DEMO / "offline_manifest.json"):
        out.write_text(text, encoding="utf-8")
    print(f"scenes={len(scenes)} stills={n_still} orbits={sum(1 for s in scenes if s.get('video'))} inputs={n_inputs}")


if __name__ == "__main__":
    main()
