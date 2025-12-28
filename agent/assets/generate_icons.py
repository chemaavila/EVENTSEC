import shutil
import subprocess
from pathlib import Path

from PIL import Image

SVG = Path(__file__).resolve().parent / "logo.svg"
PNG = Path(__file__).resolve().parent / "logo.png"
ICO = Path(__file__).resolve().parent / "logo.ico"
ICNS = Path(__file__).resolve().parent / "logo.icns"


def generate_png(size: int) -> Path | None:
    try:
        import cairosvg

        png_data = cairosvg.svg2png(url=str(SVG), output_width=size, output_height=size)
        png_path = Path(__file__).resolve().parent / f"logo_{size}.png"
        png_path.write_bytes(png_data)
        return png_path
    except Exception:
        return None


def ensure_png():
    if PNG.exists():
        return
    png = generate_png(256)
    if not png:
        print("Warning: cairosvg not available; PNG fallback cannot be generated.")
    else:
        png.rename(PNG)


def generate_ico():
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    frames = []
    for size in sizes:
        png_path = generate_png(size[0])
        if png_path:
            frames.append(Image.open(png_path).resize(size).convert("RGBA"))
    if frames:
        frames[0].save(ICO, format="ICO", sizes=sizes)


def generate_icns():
    iconset = Path(__file__).resolve().parent / "logo.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(exist_ok=True)
    sizes = [16, 32, 64, 128, 256]
    for size in sizes:
        png_path = generate_png(size)
        if not png_path:
            continue
        png = Image.open(png_path)
        target = iconset / f"icon_{size}x{size}.png"
        png.resize((size, size)).save(target, format="PNG")
        retina = iconset / f"icon_{size}x{size}@2x.png"
        png.resize((size * 2, size * 2)).save(retina, format="PNG")
    if not shutil.which("iconutil"):
        print("iconutil not available; skipping .icns creation.")
        return
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ICNS)], check=False)


def main():
    ensure_png()
    generate_ico()
    generate_icns()


if __name__ == "__main__":
    main()

