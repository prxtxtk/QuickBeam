import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from quickbeam.engine.converters import ConverterEngine
from harness.fixtures import generate_fixtures

def run():
    print("[*] Launching QuickBeam Test Harness Profiler...")
    fixtures = generate_fixtures()
    engine = ConverterEngine()
    
    tests = [
        ("Markdown -> PDF", lambda: engine.markdown_to_pdf(fixtures["md"])),
        ("CSV -> XLSX (10,000 rows)", lambda: engine.csv_to_xlsx(fixtures["csv"])),
        ("Image -> PDF Packing", lambda: engine.images_to_pdf([fixtures["img"]]))
    ]
    
    all_passed = True
    for name, func in tests:
        tracemalloc.start()
        t0 = time.perf_counter()
        
        try:
            res = func()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            kb = len(res.getvalue()) / 1024
            peak_mb = peak / (1024 * 1024)
            
            assert kb > 0, "Empty payload produced."
            assert peak_mb < 50.0, f"Memory threshold exceeded: {peak_mb:.2f} MB"
            
            print(f"  [PASS] {name:<26} | Time: {elapsed_ms:>6.1f}ms | Output: {kb:>7.1f} KB | Peak RAM: {peak_mb:>5.2f} MB")
        except Exception as e:
            tracemalloc.stop()
            print(f"  [FAIL] {name:<26} | Error: {str(e)}")
            all_passed = False
            
    if not all_passed:
        sys.exit(1)
    print("\n[+] Verification Complete: All engine conversions conform to < 50 MB RAM.")

if __name__ == "__main__":
    run()
