"""Reusable in-memory fixtures for the QuickBeam verification harness."""

import io
import csv

from PIL import Image


def generate_fixtures():
    fixtures = {}

    # 1. Markdown fixture
    fixtures["md"] = io.BytesIO(b"# Harness Spec\n\nTesting pure Python PDF engine.\n## Section 2\nStream validation.")

    # 2. 10,000-row CSV stress fixture
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["ID", "Timestamp", "Metric", "Status"])
    for i in range(10000):
        writer.writerow([i, "2026-11-08T08:34:00Z", 100.0 + (i % 7), "NOMINAL"])
    fixtures["csv"] = io.BytesIO(csv_buf.getvalue().encode("utf-8"))

    # 3. High-res synthetic image
    img = Image.new("RGB", (2048, 1536), color=(40, 80, 120))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG")
    img_buf.seek(0)
    fixtures["img"] = img_buf

    return fixtures
