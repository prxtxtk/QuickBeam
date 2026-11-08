import argparse
import socket
import sys
import traceback

import uvicorn
from quickbeam.core.network import get_lan_ip, render_ascii_qr
from quickbeam.core.server import app

def find_available_port(start_port: int = 8080, max_port: int = 8090) -> int:
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # A bind probe is the only reliable conflict check on Windows:
            # connect_ex(("0.0.0.0", port)) always fails with WSAEADDRNOTAVAIL.
            try:
                s.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    return start_port

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="quickbeam",
        description="Ephemeral LAN file bridge and in-memory document transformer.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=0, help="Preferred port (default: first free in 8080-8090)")
    parser.add_argument("--no-qr", action="store_true", help="Do not draw the terminal QR code")
    parser.add_argument("--diagnose", action="store_true", help="Run environment checks, print results, and exit")
    return parser.parse_args(argv)

def _print_startup_report(host: str, port: int):
    ip = get_lan_ip()
    print(f"[*] QuickBeam is listening on {host}:{port}", flush=True)
    print(f"[*] Phone URL: http://{ip}:{port}", flush=True)
    print("[*] Keep this window open. Press Ctrl+C to stop the bridge.", flush=True)

def _diagnose() -> int:
    import tempfile
    from pathlib import Path

    from quickbeam.core.server import STATIC_HTML_PATH

    print("[*] QuickBeam diagnostics")
    print(f"    frozen       : {getattr(sys, 'frozen', False)}")
    print(f"    executable   : {sys.executable}")
    print(f"    python       : {sys.version.split()[0]}")
    print(f"    lan ip       : {get_lan_ip()}")
    print(f"    mobile ui    : {STATIC_HTML_PATH} (exists={STATIC_HTML_PATH.exists()})")

    temp_dir = tempfile.gettempdir()
    try:
        probe = Path(temp_dir) / "quickbeam_probe.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        writable = True
    except Exception as exc:
        writable = f"NO ({exc})"
    print(f"    temp dir     : {temp_dir} (writable={writable})")

    port = find_available_port()
    print(f"    free port    : {port}")
    return 0

def _pause_if_double_clicked():
    """Keep the console window open so a startup failure is actually readable."""
    if not getattr(sys, "frozen", False):
        return
    try:
        input("\nPress Enter to close this window...")
    except Exception:
        pass

def _run(argv=None) -> int:
    args = parse_args(argv)
    if args.diagnose:
        return _diagnose()

    ip = get_lan_ip()
    port = args.port or find_available_port(8080, 8090)
    url = f"http://{ip}:{port}"
    if not args.no_qr:
        render_ascii_qr(url)
    _print_startup_report(args.host, port)
    uvicorn.run(app, host=args.host, port=port, log_level="warning")
    return 0

def entrypoint(argv=None):
    try:
        _run(argv)
    except KeyboardInterrupt:
        print("\n[*] QuickBeam stopped.", flush=True)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("\n[!] QuickBeam could not start. See the error above.", flush=True)
        _pause_if_double_clicked()
        raise SystemExit(1)

if __name__ == "__main__":
    entrypoint()
