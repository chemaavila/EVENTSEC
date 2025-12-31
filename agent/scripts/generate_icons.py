"""
Generate agent icons from the shared favicon.

Outputs:
- assets/icons/eventsec-agent.png  (PNG for Linux/preview)
- assets/icons/eventsec-agent.ico  (Windows)
- assets/icons/eventsec-agent.icns (macOS, only if iconutil is available)

Requirements: CairoSVG, Pillow. macOS .icns generation also needs the
system tool `iconutil` (available on macOS).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
import cairosvg


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_FAVICON = ROOT.parent / "frontend" / "public" / "favicon.svg"
OUT_DIR = ROOT / "assets" / "icons"

# Sizes to render from SVG. Includes the set required for ICO and macOS iconsets.
PNG_SIZES = [16, 24, 32, 48, 64, 128, 256, 512, 1024]


def ensure_sources() -> None:
    if not FRONTEND_FAVICON.exists():
        raise FileNotFoundError(f"Favicon not found at {FRONTEND_FAVICON}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def render_pngs() -> list[Path]:
    rendered: list[Path] = []
    for size in PNG_SIZES:
        target = OUT_DIR / f"eventsec-{size}.png"
        cairosvg.svg2png(
            url=str(FRONTEND_FAVICON),
            write_to=str(target),
            output_width=size,
            output_height=size,
        )
        rendered.append(target)
    # Keep a friendly default PNG for Linux/preview.
    default_png = OUT_DIR / "eventsec-agent.png"
    shutil.copy2(rendered[PNG_SIZES.index(256)], default_png)
    return rendered


def build_ico(pngs: list[Path]) -> Path:
    ico_path = OUT_DIR / "eventsec-agent.ico"
    sizes = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    base_png = next(p for p in pngs if p.name == "eventsec-256.png")
    with Image.open(base_png) as img:
        img.save(ico_path, format="ICO", sizes=sizes)
    return ico_path


def build_icns(pngs: list[Path]) -> Path | None:
    if sys.platform != "darwin":
        return None
    iconutil = shutil.which("iconutil")
    if not iconutil:
        print("Skipping .icns generation (iconutil not found).")
        return None

    iconset_dir = OUT_DIR / "eventsec.iconset"
    iconset_dir.mkdir(parents=True, exist_ok=True)

    def copy_size(src_size: int, name: str) -> None:
        src = OUT_DIR / f"eventsec-{src_size}.png"
        shutil.copy2(src, iconset_dir / name)

    # macOS expects specific names inside the iconset
    copy_size(16, "icon_16x16.png")
    copy_size(32, "icon_16x16@2x.png")
    copy_size(32, "icon_32x32.png")
    copy_size(64, "icon_32x32@2x.png")
    copy_size(128, "icon_128x128.png")
    copy_size(256, "icon_128x128@2x.png")
    copy_size(256, "icon_256x256.png")
    copy_size(512, "icon_256x256@2x.png")
    copy_size(512, "icon_512x512.png")
    copy_size(1024, "icon_512x512@2x.png")

    icns_path = OUT_DIR / "eventsec-agent.icns"
    subprocess.run([iconutil, "-c", "icns", "-o", icns_path, iconset_dir], check=True)

    shutil.rmtree(iconset_dir, ignore_errors=True)
    return icns_path


def main() -> None:
    ensure_sources()
    pngs = render_pngs()
    ico = build_ico(pngs)
    icns = build_icns(pngs)
    print(f"Generated PNG assets in {OUT_DIR}")
    print(f"ICO written to {ico}")
    if icns:
        print(f"ICNS written to {icns}")
    else:
        print("ICNS skipped (non-macOS or iconutil missing).")


if __name__ == "__main__":
    main()
