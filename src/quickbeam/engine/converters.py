import io
import csv
import zipfile
import xml.etree.ElementTree as ET
from typing import List
from PIL import Image
import img2pdf
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pillow_heif import register_heif_opener

register_heif_opener()

class ConverterEngine:
    @staticmethod
    def docx_to_markdown(source: io.BytesIO) -> io.BytesIO:
        """Parses DOCX as an in-memory ZIP archive and extracts structured Markdown."""
        with zipfile.ZipFile(source) as z:
            xml_data = z.read("word/document.xml")
        tree = ET.fromstring(xml_data)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        output = []
        for p in tree.iterfind('.//w:p', ns):
            p_style = p.find('.//w:pStyle', ns)
            val = p_style.attrib.get(f"{{{ns['w']}}}val", "") if p_style is not None else ""
            texts = [node.text for node in p.iterfind('.//w:t', ns) if node.text]
            line = "".join(texts).strip()
            if not line:
                continue
            if "Heading1" in val:
                output.append(f"# {line}\n")
            elif "Heading2" in val:
                output.append(f"## {line}\n")
            else:
                output.append(f"{line}\n")
        return io.BytesIO("\n".join(output).encode("utf-8"))

    @staticmethod
    def markdown_to_pdf(source: io.BytesIO) -> io.BytesIO:
        """Converts Markdown text into a formatted PDF using pure-Python fpdf2."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        
        text = source.getvalue().decode("utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 10, line[2:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=11)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 8, line[3:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=11)
            elif line:
                pdf.multi_cell(0, 6, line)
            pdf.ln(1)
            
        out = io.BytesIO()
        pdf.output(out)
        out.seek(0)
        return out

    @staticmethod
    def csv_to_xlsx(source: io.BytesIO) -> io.BytesIO:
        """Transforms a CSV stream into an auto-styled XLSX workbook."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Export"
        reader = csv.reader(io.StringIO(source.getvalue().decode("utf-8", errors="ignore")))
        
        for r_idx, row in enumerate(reader, start=1):
            ws.append(row)
            if r_idx == 1:
                for cell in ws[1]:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
                    
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max(max_len + 3, 12)

        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return out

    @staticmethod
    def images_to_pdf(sources: List[io.BytesIO]) -> io.BytesIO:
        """Normalizes EXIF orientation and packs HEIC/JPG/PNG images into a single PDF."""
        normalized_jpegs = []
        for src in sources:
            img = Image.open(src)
            if hasattr(img, "_getexif") and img._getexif():
                exif = img._getexif()
                orientation = exif.get(0x0112)
                if orientation == 3: img = img.rotate(180, expand=True)
                elif orientation == 6: img = img.rotate(270, expand=True)
                elif orientation == 8: img = img.rotate(90, expand=True)
            rgb = img.convert("RGB")
            buf = io.BytesIO()
            rgb.save(buf, format="JPEG", quality=85)
            normalized_jpegs.append(buf.getvalue())
        return io.BytesIO(img2pdf.convert(normalized_jpegs))
