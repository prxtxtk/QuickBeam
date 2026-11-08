import socket
import io
import sys
import qrcode

def get_lan_ip() -> str:
    """Discovers the primary local network IP via UDP routing probe without sending packets."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def _enable_utf8_console():
    """Makes the block-drawing QR glyphs printable on legacy Windows code pages."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

def render_ascii_qr(url: str):
    """Prints an inverted ANSI QR code directly to the terminal stdout."""
    _enable_utf8_console()
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=True)
    print("\n" + buf.getvalue())
    print(f"[*] QuickBeam Access Point: {url}\n")
