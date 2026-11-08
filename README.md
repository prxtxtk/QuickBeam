# QuickBeam

**A zero-install file bridge between your phone and your PC — over nothing but your local Wi-Fi.**

QuickBeam starts a tiny HTTP server on your computer, prints a QR code in the terminal, and serves a mobile-friendly page to any phone on the same network. Drop files in, run a pure-Python conversion, and get them back. No app install, no cloud, no account, no scratch files.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Binary](https://img.shields.io/badge/binary-23.5%20MB-blue)
![Peak RAM](https://img.shields.io/badge/engine%20RAM-%3C50%20MB-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-lightgrey)

---

## Why

Moving a photo off an iPhone, merging a handful of screenshots into one PDF, or turning a CSV into something Excel-friendly usually means emailing it to yourself, wiring up a USB cable, or installing an app. QuickBeam is a single executable: run it, scan the QR, use the page, close it. Nothing is uploaded anywhere, and nothing lingers on disk.

## What it does

- **Scan → send.** A terminal QR code opens the bridge on any phone on the same LAN. No install, no login.
- **Five actions.** Raw transfer to the PC, images → PDF, Markdown → PDF, CSV → Excel, DOCX → Markdown.
- **Real photo formats.** HEIC from iPhones, plus JPEG/PNG, with EXIF orientation normalized before packing into a PDF.
- **In-memory conversions.** Every transformation runs through `io.BytesIO`; only raw transfers and the final download touch disk.
- **Tiny footprint.** Single executable under 25 MB, and the conversion engine stays under 50 MB of Python heap.
- **Zero configuration.** LAN IP is discovered automatically, and the port falls back across `8080–8090`.

## How it works

```
  Phone browser                          PC (this project)
┌───────────────┐   HTTP over LAN   ┌──────────────────────────────┐
│  zero-install │ ────────────────▶ │  FastAPI + uvicorn           │
│  mobile page  │                   │  GET  /            → UI      │
│               │ ◀──────────────── │  POST /api/upload  → actions │
└───────────────┘   file / result   └──────────────┬───────────────┘
                                                    │ io.BytesIO
                                          ┌─────────▼──────────┐
                                          │  ConverterEngine   │
                                          │  fpdf2 · img2pdf   │
                                          │  openpyxl · Pillow │
                                          └────────────────────┘
```

1. `quickbeam` binds `0.0.0.0` on the first free port in `8080–8090`.
2. It prints an ANSI QR code and the phone URL for the detected LAN address.
3. The phone opens the bundled single-file web app.
4. Uploads are parsed by FastAPI, transformed in memory, and streamed back.

## Demo

```console
$ .\QuickBeam.cmd
============================================================
 QuickBeam file bridge - keep this window open
============================================================

  █████████████████████████████
  █ ▄▄▄▄▄ █▀█ ▄▀▄ █▀▀▄ █▄▄▄▄▄ █
  █ █   █ █▀▀▀ ▀ █ █▄▀  █   █ █
  █ █▄▄▄█ █▀█ ▄▀▄▀▄▀▄█  █▄▄▄█ █
  █▄▄▄▄▄▄▄█ ▀▄▀ █▄▀ ▄▀█ ▄▄▄▄▄▄▄█
  █████████████████████████████

[*] QuickBeam is listening on 0.0.0.0:8080
[*] Phone URL: http://192.168.1.23:8080
[*] Keep this window open. Press Ctrl+C to stop the bridge.
```

Scan the code, pick files, choose an action, tap **Beam to Computer**.

## Quick start

### Windows executable

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install . pyinstaller

python scripts\build_binary.py            # onefile  → dist\quickbeam.exe   (23.5 MB)
python scripts\build_binary.py --onedir   # folder   → dist\onedir\quickbeam\quickbeam.exe
```

Then **double-click `QuickBeam.cmd`**. It prefers the folder build (it starts without unpacking itself), keeps the console open, and falls back to the onefile build if the folder one is missing.

> A onefile executable unpacks itself into `%TEMP%` on every start. On machines where that is locked down, use the `--onedir` build — the launcher picks it automatically.

If Windows asks about the firewall, allow QuickBeam on **private networks**. If the prompt never appeared, run `Allow-Firewall.cmd` once and accept the UAC prompt.

### From source (any OS with Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install .
python -m quickbeam.main
```

On macOS/Linux, activate with `source .venv/bin/activate`; everything except the `.cmd` helpers is cross-platform.

## Using it

Once the page is open on the phone, select files and an action:

| Action | Input | Output | Delivered to |
| --- | --- | --- | --- |
| **None (Raw Transfer to PC)** | any files | unchanged | PC, first writable folder |
| **Merge Images → PDF** | HEIC / JPEG / PNG | `merged.pdf` | phone |
| **Markdown → PDF** | `.md` / `.txt` | `document.pdf` | phone |
| **CSV → Excel** | `.csv` | `converted.xlsx` (styled header) | phone |
| **DOCX → Markdown** | `.docx` | `document.md` | phone |

The action is auto-selected from the file type, so a photo opens ready to merge and a `.csv` opens ready to convert.

### Where received files go

Raw transfers are saved to the first writable location:

1. `C:\Users\<you>\Downloads`
2. `%LOCALAPPDATA%\QuickBeam\Received`
3. `C:\Users\<you>\QuickBeam Received`
4. a `received` folder next to the executable

The phone page and the console both report the exact path (`[+] Saved photo.jpg -> …`). Existing files are never overwritten; a ` (1)` suffix is added. Converted files are **not** stored on the PC — they are downloaded to the phone.

## CLI

```
quickbeam [--host HOST] [--port PORT] [--no-qr] [--diagnose]
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `0.0.0.0` | Bind address |
| `--port` | first free `8080–8090` | Preferred port |
| `--no-qr` | off | Skip the terminal QR code |
| `--diagnose` | off | Print environment checks (LAN IP, UI asset, temp writability, free port) and exit |

```powershell
.\QuickBeam.cmd --diagnose
```

## Project layout

```
quickbeam/
├── pyproject.toml
├── README.md
├── QuickBeam.cmd              # double-click launcher (Windows)
├── Allow-Firewall.cmd         # one-time firewall helper (Windows, self-elevating)
├── src/quickbeam/
│   ├── main.py                # CLI, port fallback, QR, uvicorn
│   ├── core/
│   │   ├── network.py         # LAN IP probe + ASCII QR rendering
│   │   └── server.py          # FastAPI routes + receive-folder selection
│   ├── engine/
│   │   └── converters.py      # in-memory DOCX/MD/CSV/image transforms
│   └── static/
│       └── index.html         # the entire mobile web app
├── harness/
│   ├── fixtures.py            # synthetic payloads (10k-row CSV, 2048×1536 image)
│   └── harness_runner.py      # tracemalloc profiler
├── scripts/
│   └── build_binary.py        # PyInstaller onefile / onedir
└── dist/                      # build output (not committed)
```

## Benchmarks

`python harness/harness_runner.py` profiles each converter with `tracemalloc`:

| Conversion | Time | Output | Peak Python heap |
| --- | --- | --- | --- |
| Markdown → PDF | ~11 ms | 1.2 KB | 0.30 MB |
| CSV → XLSX (10,000 rows) | ~6.2 s | 172.4 KB | 15.17 MB |
| Image → PDF packing (2048×1536) | ~36 ms | 50.0 KB | 0.15 MB |

Peak RAM is the Python allocation peak for the conversion itself, measured by `tracemalloc`; C-side buffers (Pillow, JPEG codecs) sit outside that counter. Timings are from a Windows laptop and will vary.

## Building

```powershell
python scripts\build_binary.py             # onefile
python scripts\build_binary.py --onedir    # folder build
```

The onefile build stays under 25 MB by excluding payloads this app never uses:

- `pikepdf` and `lxml` — img2pdf falls back to its pure-Python internal PDF engine.
- `websockets`, `watchfiles`, `httptools`, `yaml` — optional uvicorn accelerators.
- Pillow's AVIF, Tk, and FreeType plugins — the phone flows never touch them.
- `--optimize 2` strips docstrings and asserts from bundled bytecode.

HEIC support is kept intact (`pillow-heif`, `libheif`, `libde265`, `libx265`); FastAPI's `opentelemetry` import is required and cannot be dropped.

## Design constraints

| Constraint | Target | Result |
| --- | --- | --- |
| Peak conversion RAM | < 50 MB | 15.17 MB worst case (10k-row CSV) |
| Standalone binary | < 25 MB | 23.46 MB (24,601,154 bytes) |
| Dependencies | no headless browser, LibreOffice, or Pandoc | pure Python |
| Intermediate files | none | `io.BytesIO` throughout |
| Configuration | none | auto LAN IP + `8080–8090` fallback |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Console flashes and closes | Run `QuickBeam.cmd` (it pauses on exit). For details: `QuickBeam.cmd --diagnose`. |
| Phone shows "site can't be reached" | Allow inbound TCP 8080–8090: run `Allow-Firewall.cmd` as admin, and make sure the hotspot/Wi-Fi profile is **Private**. |
| Still unreachable | Disable VPNs on the phone and the PC; some hotspots have client isolation. Check both devices are on the same network. |
| Phone URL shows a VPN address | Disconnect the VPN; `--diagnose` prints the address QuickBeam will advertise. |
| "Transferred" but nothing on the PC | Conversions download to the phone. Only **None (Raw Transfer to PC)** saves on the PC — the page reports where. |
| Raw transfer fails / downloads are blocked | Windows Defender **Controlled Folder Access** may block unsigned apps. Allow `quickbeam.exe` under Ransomware protection, or use the fallback folder the page reports. |
| Port already in use | QuickBeam tries `8080–8090`; or pass `--port 8091`. |
| Onefile won't start | Build the folder variant (`--onedir`) — it needs no `%TEMP%` extraction. |

## Security and privacy

- **Trusted networks only.** There is no authentication, no TLS, and no rate limiting. Anyone who can reach the port while QuickBeam runs can upload and read the returned files.
- **Never expose it to the internet.** Do not port-forward `8080–8090` or run it on public Wi-Fi.
- **No third-party services.** Files are processed on your machine; nothing is uploaded to a cloud.
- **Disk writes** happen only for raw transfers and for the onefile executable's own extraction. Conversions are held in memory.
- **Filenames are sanitized**, directory components are stripped, and collisions are renamed rather than overwritten.

## Limitations / roadmap

- Single-user, single-session; no auth or session tokens.
- No upload size cap — a huge file is buffered in RAM (the engine fixtures are what the 50 MB budget covers).
- Windows is the packaged target; source runs elsewhere but the `.cmd` helpers are Windows-only.
- Possible next steps: signed releases, upload limits, an optional PIN, and a small settings page for the receive folder.

## Built with

FastAPI · uvicorn · qrcode · fpdf2 · img2pdf · openpyxl · Pillow · pillow-heif · PyInstaller

