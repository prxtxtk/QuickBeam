import argparse
import subprocess
import sys
from pathlib import Path


def package(onedir: bool = False):
    root = Path(__file__).parent.parent
    static_asset = root / "src" / "quickbeam" / "static" / "index.html"
    entry = root / "src" / "quickbeam" / "main.py"
    dist_path = root / "dist" / "onedir" if onedir else root / "dist"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir" if onedir else "--onefile",
        "--name", "quickbeam",
        "--clean",
        "--noconfirm",
        "--optimize", "2",
        "--workpath", str(root / "build" / ("onedir" if onedir else "onefile")),
        "--specpath", str(root / "build" / ("onedir" if onedir else "onefile")),
        "--distpath", str(dist_path),
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pytest",
        # img2pdf falls back to its pure-Python internal PDF engine when pikepdf is
        # absent, so the qpdf/lxml payload is dead weight for this app.
        "--exclude-module", "pikepdf",
        "--exclude-module", "lxml",
        # uvicorn's optional accelerators are not required at runtime.
        "--exclude-module", "websockets",
        "--exclude-module", "watchfiles",
        "--exclude-module", "httptools",
        "--exclude-module", "yaml",
        # AVIF, Tk, and FreeType imaging paths are never used by the phone flows.
        "--exclude-module", "PIL._avif",
        "--exclude-module", "PIL.AvifImagePlugin",
        "--exclude-module", "PIL._imagingft",
        "--exclude-module", "PIL._imagingtk",
        "--exclude-module", "PIL.ImageTk",
        "--exclude-module", "PIL.ImageQt",
        "--exclude-module", "PIL.ImageGrab",
        "--exclude-module", "PIL.ImageShow",
        "--add-data", f"{static_asset};quickbeam/static" if sys.platform == "win32" else f"{static_asset}:quickbeam/static",
        str(entry)
    ]
    if onedir:
        # The folder build never extracts at runtime, so it also works on machines
        # where the onefile bootloader cannot create its temporary directory.
        print("[*] Building the folder variant that needs no runtime extraction.")

    print(f"[*] Compiling with PyInstaller: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    if onedir:
        print("[+] Packaging finished. Run ./dist/onedir/quickbeam/quickbeam.exe")
    else:
        print("[+] Packaging finished. Check ./dist/quickbeam.exe")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the QuickBeam standalone executable.")
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Build the folder variant (no runtime extraction) instead of the onefile binary.",
    )
    args = parser.parse_args()
    package(onedir=args.onedir)
