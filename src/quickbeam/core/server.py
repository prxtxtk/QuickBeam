import io
import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from quickbeam.engine.converters import ConverterEngine

app = FastAPI(title="QuickBeam Server")
engine = ConverterEngine()

STATIC_HTML_PATH = Path(__file__).parent.parent / "static" / "index.html"

def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".quickbeam_write_probe"
        probe.write_bytes(b"")
        probe.unlink()
        return True
    except OSError:
        return False

def resolve_receive_dir() -> Path:
    """Pick the first writable landing folder for raw transfers.

    Downloads is preferred, but Windows Defender's Controlled Folder Access (or a
    restricted profile) can deny writes there for unsigned executables, so several
    unprotected fallbacks are tried before giving up.
    """
    exe_dir = Path(sys.executable).resolve().parent
    local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    candidates = [
        Path.home() / "Downloads",
        local_appdata / "QuickBeam" / "Received",
        Path.home() / "QuickBeam Received",
        exe_dir / "received",
        Path(tempfile.gettempdir()) / "QuickBeam Received",
    ]
    for candidate in candidates:
        if _is_writable_dir(candidate):
            return candidate
    # Last resort: the OS temp directory; the caller surfaces any write error.
    return Path(tempfile.gettempdir())

def _safe_filename(name: str) -> str:
    """Strips directory components and characters that are invalid on Windows."""
    candidate = Path(name or "file").name
    for bad in '<>:"/\\|?*':
        candidate = candidate.replace(bad, "_")
    candidate = candidate.strip().strip(".") or "file"
    return candidate

def _unique_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    for index in range(1, 1000):
        candidate = directory / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
    return target

def _save_raw(content: bytes, original_name: str) -> dict:
    dest_dir = resolve_receive_dir()
    out_path = _unique_path(dest_dir, _safe_filename(original_name))
    try:
        out_path.write_bytes(content)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save {out_path.name} to {dest_dir}: {exc}",
        )
    print(f"[+] Saved {out_path.name} -> {out_path}", flush=True)
    return {"name": out_path.name, "path": str(out_path)}

@app.get("/", response_class=HTMLResponse)
def index_route():
    with open(STATIC_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/upload")
async def upload_route(files: list[UploadFile], action: str = Form("raw")):
    if action == "raw":
        saved = [_save_raw(await f.read(), f.filename) for f in files]
        destination = str(Path(saved[0]["path"]).parent) if saved else ""
        return {
            "status": "saved",
            "count": len(saved),
            "destination": destination,
            "files": saved,
        }

    elif action == "images_to_pdf":
        buffers = [io.BytesIO(await f.read()) for f in files]
        res = engine.images_to_pdf(buffers)
        return Response(content=res.getvalue(), media_type="application/pdf", 
                        headers={"Content-Disposition": "attachment; filename=merged.pdf"})

    elif action == "csv_to_xlsx":
        buf = io.BytesIO(await files[0].read())
        res = engine.csv_to_xlsx(buf)
        return Response(content=res.getvalue(), 
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        headers={"Content-Disposition": "attachment; filename=converted.xlsx"})

    elif action == "md_to_pdf":
        buf = io.BytesIO(await files[0].read())
        res = engine.markdown_to_pdf(buf)
        return Response(content=res.getvalue(), media_type="application/pdf", 
                        headers={"Content-Disposition": "attachment; filename=document.pdf"})

    elif action == "docx_to_md":
        buf = io.BytesIO(await files[0].read())
        res = engine.docx_to_markdown(buf)
        return Response(content=res.getvalue(), media_type="text/markdown", 
                        headers={"Content-Disposition": "attachment; filename=document.md"})

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
