from fpdf import FPDF
from pathlib import Path
from datetime import datetime
import re
import os


class ReportPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            8,
            "Automatisierter Sicherheitsbericht",
            new_x="LMARGIN",
            new_y="NEXT",
            align="R",
        )
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Seite {self.page_no()}", align="C")


def normalize_text(text: str) -> str:
    if not text:
        return ""

    replacements = {
        "\u201e": '"',    # „
        "\u201c": '"',    # “
        "\u201d": '"',    # ”
        "\u2018": "'",    # ‘
        "\u2019": "'",    # ’
        "\u2013": "-",    # –
        "\u2014": "-",    # —
        "\u2026": "...",  # …
        "\u00a0": " ",    # non-breaking space
        "\u2022": "-",    # •
        "\u25cf": "-",    # ●
        "\u2713": "OK",   # ✓
        "\u2714": "OK",   # ✔
        "\u2717": "X",    # ✗
        "\u2718": "X",    # ✘
        "\u2192": "->",   # →
        "\u2264": "<=",   # ≤
        "\u2265": ">=",   # ≥
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def strip_simple_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = text.replace("```", "")
    return text


def to_latin1_safe(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def createReportPDF(result: str, output_path: str):
    if not result:
        raise ValueError("Kein Inhalt für den PDF-Bericht übergeben.")

    result = normalize_text(result)
    result = strip_simple_markdown(result)
    result = to_latin1_safe(result)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"[createReportPDF] output_path={output_file}", flush=True)
    print(f"[createReportPDF] output_dir exists={output_file.parent.exists()}", flush=True)

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # Titel
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(
        0,
        12,
        "Automatisierter Sicherheitsbericht",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(
        0,
        8,
        f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)

    for line in result.split("\n"):
        stripped = line.strip()

        if not stripped:
            pdf.ln(4)
            continue

        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 8, stripped[4:], new_x="LMARGIN", new_y="NEXT")

        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 9, stripped[3:], new_x="LMARGIN", new_y="NEXT")

        elif stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 10, stripped[2:], new_x="LMARGIN", new_y="NEXT")

        elif stripped.startswith("- "):
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, f"- {stripped[2:]}", new_x="LMARGIN", new_y="NEXT")

        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, stripped, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(output_file))

    print(f"[createReportPDF] PDF gespeichert: {output_file}", flush=True)
    print(f"[createReportPDF] Datei existiert: {output_file.exists()}", flush=True)
    print(f"[createReportPDF] Dateien im Zielordner: {os.listdir(output_file.parent)}", flush=True)