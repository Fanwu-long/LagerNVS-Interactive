# -*- coding: utf-8 -*-
"""Build scrubbable orbit clips for HQ still scenes.

Priority:
1) Re-encode existing 512 showcase neural path videos (true NVS trajectory).
2) If missing, synthesize a parallax orbit from the Pred half of COMPARE_*.png.
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[2]
FINAL = PROJECT / "03_最终成果包" / "lagernvs_final"
SHOWCASE = FINAL / "04_showcase_videos_512"
COMPARE = FINAL / "02_top20_gt_pred"
OUT = PROJECT / "07_交互式渲染演示" / "03_环绕轨道视频_orbit_v4" / "hq_from_still"
SRC_SHOWCASE_FALLBACK = Path(r"d:\新建文件夹\LagerNVS\03_最终成果包\lagernvs_final\04_showcase_videos_512")

HQ_IDS = [
    "45a00d135c5388fc_00012",
    "eae986c8f31081cc_00051",
    "e9670b30a2c0e348_00001",
    "c1ad4232258e87c9_00014",
    "fbcd62ab8ff30b4f_00013",
]


def scene_key(cid: str) -> str:
    return cid.split("_")[0] if "_" in cid else cid


def find_showcase(cid: str) -> Path | None:
    key = scene_key(cid)
    roots = [SHOWCASE, SRC_SHOWCASE_FALLBACK]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(sorted(root.glob(f"{key}_6v_*.mp4")))
        candidates.extend(sorted(root.glob(f"{key}_2v_*.mp4")))
        candidates.extend(sorted(root.glob(f"{key}_*.mp4")))
    # prefer 6v then larger file
    def rank(p: Path) -> tuple:
        name = p.name
        pref = 0 if "_6v_" in name else (1 if "_2v_" in name else 2)
        return (pref, -p.stat().st_size)

    if not candidates:
        return None
    return sorted(set(candidates), key=rank)[0]


def reencode_showcase(src: Path, dst: Path) -> None:
    """Copy frames and write a higher-bitrate H264 for scrubbing."""
    frames = list(iio.imiter(src))
    if not frames:
        raise RuntimeError(f"empty video {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(
        dst,
        np.stack(frames, axis=0),
        fps=20,
        codec="libx264",
        quality=8,  # imageio-ffmpeg: lower = better for some backends; also pass output_params
        output_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )


def pred_half(compare_png: Path) -> Image.Image:
    im = Image.open(compare_png).convert("RGB")
    w, h = im.size
    # COMPARE is stacked GT|Pred vertically in this package
    pred = im.crop((0, h // 2, w, h))
    return pred


def synth_orbit_from_still(pred: Image.Image, dst: Path, n_frames: int = 120) -> None:
    """Parallax pan over Pred — scrubbable stand-in when no neural orbit exists."""
    pred = pred.convert("RGB")
    # work on a slightly larger canvas for edge room
    base_w, base_h = pred.size
    scale = 1.18
    big = pred.resize((int(base_w * scale), int(base_h * scale)), Image.Resampling.LANCZOS)
    bw, bh = big.size
    out_w, out_h = base_w - (base_w % 2), base_h - (base_h % 2)
    frames = []
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        # smooth back-and-forth (ease)
        phase = 0.5 - 0.5 * math.cos(2 * math.pi * t)
        max_dx = bw - out_w
        max_dy = max(bh - out_h, 1)
        x = int(phase * max_dx)
        y = int(0.35 * max_dy + 0.15 * max_dy * math.sin(2 * math.pi * t))
        crop = big.crop((x, y, x + out_w, y + out_h))
        frames.append(np.asarray(crop))
    dst.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(
        dst,
        np.stack(frames, axis=0),
        fps=24,
        codec="libx264",
        output_params=["-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # ensure showcase available inside final package
    if not SHOWCASE.exists() and SRC_SHOWCASE_FALLBACK.exists():
        SHOWCASE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SRC_SHOWCASE_FALLBACK, SHOWCASE, dirs_exist_ok=True)
        print("copied showcase into package")

    meta = []
    for cid in HQ_IDS:
        dst = OUT / f"orbit_hq_{cid}.mp4"
        show = find_showcase(cid)
        cmp = COMPARE / f"COMPARE_{cid}.png"
        if show:
            print(f"[showcase] {cid} <- {show.name}")
            reencode_showcase(show, dst)
            meta.append({"id": cid, "source": "showcase", "file": str(dst.relative_to(PROJECT)).replace("\\", "/"), "from": show.name})
        elif cmp.exists():
            print(f"[synth-pred] {cid} <- {cmp.name}")
            synth_orbit_from_still(pred_half(cmp), dst)
            meta.append({"id": cid, "source": "synth_pred", "file": str(dst.relative_to(PROJECT)).replace("\\", "/"), "from": cmp.name})
        else:
            print(f"[skip] {cid}")
            continue
        print(f"  -> {dst.name} {dst.stat().st_size/1e6:.2f}MB")

    (OUT / "README.txt").write_text(
        "HQ stills -> orbit clips\n"
        "- source=showcase: true neural camera path from 04_showcase_videos_512 (re-encoded)\n"
        "- source=synth_pred: parallax scrub from COMPARE Pred half (no GPU re-render)\n",
        encoding="utf-8",
    )
    import json

    (OUT / "build_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("done", len(meta), "orbits")


if __name__ == "__main__":
    main()
