#!/usr/bin/env python3
"""Render the reviewed Musia answers and unedited native evidence as a PDF."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer


def render(source, output, screenshots):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Copy", fontName="Helvetica", fontSize=10,
                              leading=14, spaceAfter=9, textColor=colors.HexColor("#263034")))
    styles["Heading1"].fontSize = 20
    styles["Heading1"].leading = 25
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceBefore = 12
    content = []
    for block in source.read_text().strip().split("\n\n"):
        if block.startswith("# "):
            style, block = "Heading1", block[2:]
        elif block.startswith("## "):
            style, block = "Heading2", block[3:]
        else:
            style = "Copy"
        content.append(Paragraph(escape(block).replace("\n- ", "<br/>- "), styles[style]))
    for path, caption in screenshots:
        content.extend([PageBreak(), Paragraph("Native evidence", styles["Heading1"]),
                        Paragraph(escape(caption), styles["Copy"]), Spacer(1, 8)])
        pic = Image(str(path))
        scale = min(470 / pic.imageWidth, 640 / pic.imageHeight)
        pic.drawWidth = pic.imageWidth * scale
        pic.drawHeight = pic.imageHeight * scale
        content.append(pic)

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#586469"))
        canvas.drawString(42, 24, "Musia | App 6816265930 | October 6, 2026")
        canvas.drawRightString(A4[0] - 42, 24, str(doc.page))

    output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output), pagesize=A4, leftMargin=42, rightMargin=42,
                      topMargin=40, bottomMargin=42, title="Musia - App Review Answers",
                      author="LazyingArt LLC").build(content, onFirstPage=footer, onLaterPages=footer)
    output.chmod(0o600)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--screenshot", nargs=2, action="append", default=[], metavar=("PNG", "CAPTION"))
    args = p.parse_args()
    render(args.source, args.output, [(Path(path), caption) for path, caption in args.screenshot])
