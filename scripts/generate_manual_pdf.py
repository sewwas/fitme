#!/usr/bin/env python3
"""
Fit Me Fitness Club — Complete User Manual PDF Generator
Converts the full 20-section user manual into a multi-page, executive-ready PDF.
"""

import os
import sys
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y'
    with running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"Generated User Manual PDF with {num_pages} pages.")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        width, height = A4

        # Page 1 is the cover — suppress running top header
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(HexColor("#0F172A"))
            self.drawString(36, height - 24, "FIT ME FITNESS CLUB — SYSTEM USER MANUAL")
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#64748B"))
            self.drawString(235, height - 24, "|   Pitigala, Sri Lanka · Complete Operational Guide")
            
            self.setStrokeColor(HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, height - 28, width - 36, height - 28)

        # Running Footer across all pages
        self.setStrokeColor(HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(36, 28, width - 36, 28)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(HexColor("#64748B"))
        self.drawString(36, 17, "Fit Me Fitness Club · Confidential Operational Manual · Tel: 070 762 7878 · hellofitme@outlook.com")

        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(width - 36, 17, page_str)

        self.restoreState()


def clean_text(text):
    """Sanitize inline markdown and XML entities for ReportLab Paragraphs"""
    t = text.replace('&', '&amp;')
    t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.*?)\*', r'<i>\1</i>', t)
    t = re.sub(r'`(.*?)`', r'<font face="Courier" color="#334155">\1</font>', t)
    return t


def build_manual_pdf(md_file_path, output_filename="FitMe_Complete_User_Manual.pdf"):
    pdf_path = os.path.abspath(output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    c_primary = HexColor("#0F172A")    # Deep Slate
    c_accent = HexColor("#059669")     # Emerald Green
    c_indigo = HexColor("#3730A3")     # Indigo
    c_muted = HexColor("#475569")      # Slate 600
    c_light = HexColor("#F8FAFC")      # Slate 50
    c_border = HexColor("#CBD5E1")     # Slate 300
    c_callout = HexColor("#EFF6FF")    # Soft Blue
    c_callout_border = HexColor("#3B82F6")

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=c_accent,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_muted
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_indigo,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=c_muted,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=HexColor("#1E293B"),
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=HexColor("#1E293B"),
        leftIndent=12,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.5,
        textColor=HexColor("#0F172A")
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=HexColor("#1E293B")
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=HexColor("#1E3A8A")
    )

    story = []

    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Cover Header
    logo_path = 'logo.jpeg'
    if not os.path.exists(logo_path):
        logo_path = 'wger/core/static/images/logos/logo-512.png'

    logo_img = None
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=64, height=42)

    header_data = [
        [
            logo_img if logo_img else Paragraph("<b>FIT ME</b>", h1_style),
            [
                Paragraph("FIT ME FITNESS CLUB — COMPLETE USER MANUAL", title_style),
                Paragraph("Train with Purpose &amp; Move with Confidence", subtitle_style),
                Paragraph("<b>Location:</b> Pitigala, Sri Lanka &nbsp;|&nbsp; <b>Version:</b> 2026 Enterprise Edition<br/>"
                          "<b>Contact:</b> hellofitme@outlook.com &nbsp;|&nbsp; <b>Hotline:</b> 070 762 7878", meta_style),
            ]
        ]
    ]

    header_table = Table(header_data, colWidths=[70, 453])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=4, spaceAfter=8))

    # Process markdown lines
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table(tbl_lines):
        if not tbl_lines:
            return
        parsed_rows = []
        for line in tbl_lines:
            # Skip separator line (e.g. |---|---|)
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', line):
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            parsed_rows.append(cells)

        if not parsed_rows:
            return

        num_cols = max(len(r) for r in parsed_rows)
        # Normalize columns
        for r in parsed_rows:
            while len(r) < num_cols:
                r.append("")

        total_width = 523
        col_w = total_width / num_cols
        widths = [col_w] * num_cols

        # Optimize 2, 3, or 4 column tables
        if num_cols == 2:
            widths = [140, 383]
        elif num_cols == 3:
            widths = [100, 150, 273]
        elif num_cols == 4:
            widths = [80, 110, 130, 203]

        formatted_table_data = []
        # Header row
        header_row = [Paragraph(clean_text(c), th_style) for c in parsed_rows[0]]
        formatted_table_data.append(header_row)

        for r in parsed_rows[1:]:
            row_data = [Paragraph(clean_text(c), td_style) for c in r]
            formatted_table_data.append(row_data)

        tbl = Table(formatted_table_data, colWidths=widths)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_primary),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light]),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 5))

    def flush_code(lines):
        if not lines:
            return
        code_text = "<br/>".join(lines).replace(' ', '&nbsp;')
        code_para = Paragraph(f"<font face='Courier' size='7'>{code_text}</font>", code_style)
        tbl = Table([[code_para]], colWidths=[523])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#F1F5F9")),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 5))

    skip_first_title = True
    while i < len(lines):
        line = lines[i].rstrip('\r\n')

        # Code block handler
        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                flush_code(code_lines)
                code_lines = []
            else:
                if in_table:
                    flush_table(table_lines)
                    table_lines = []
                    in_table = False
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            safe_c = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            code_lines.append(safe_c)
            i += 1
            continue

        # Table handler
        if '|' in line and not line.strip().startswith('>'):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        else:
            if in_table:
                flush_table(table_lines)
                table_lines = []
                in_table = False

        # Headings
        if line.startswith("# "):
            if skip_first_title:
                skip_first_title = False
                i += 1
                continue
            story.append(Paragraph(clean_text(line[2:].strip()), title_style))
        elif line.startswith("## "):
            story.append(Spacer(1, 4))
            story.append(Paragraph(clean_text(line[3:].strip()), h1_style))
        elif line.startswith("### "):
            story.append(Paragraph(clean_text(line[4:].strip()), h2_style))
        elif line.startswith("#### "):
            story.append(Paragraph(clean_text(line[5:].strip()), h3_style))
        elif line.startswith("> "):
            # Callout block
            callout_text = clean_text(line[2:].replace('[!IMPORTANT]', '<b>IMPORTANT:</b>').replace('[!NOTE]', '<b>NOTE:</b>').replace('[!TIP]', '<b>TIP:</b>').replace('[!WARNING]', '<b>WARNING:</b>'))
            callout_para = Paragraph(callout_text, callout_style)
            c_tbl = Table([[callout_para]], colWidths=[523])
            c_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_callout),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBEFORE', (0, 0), (0, -1), 2.5, c_callout_border),
            ]))
            story.append(c_tbl)
            story.append(Spacer(1, 4))
        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph(f"• &nbsp; {clean_text(line[2:].strip())}", bullet_style))
        elif re.match(r'^\d+\.\s', line):
            num = line.split('.')[0]
            rest = line[len(num)+2:].strip()
            story.append(Paragraph(f"<b>{num}.</b> &nbsp; {clean_text(rest)}", bullet_style))
        elif line.strip() == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=4, spaceAfter=4))
        elif line.strip() == "":
            pass
        else:
            story.append(Paragraph(clean_text(line), body_style))

        i += 1

    if in_table:
        flush_table(table_lines)
    if in_code_block:
        flush_code(code_lines)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated manual PDF at: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_md = os.path.normpath(os.path.join(script_dir, '..', 'USER_MANUAL.md'))
    fallback_md = r"C:\Users\sewwa\.gemini\antigravity-ide\brain\b4644981-51ba-4061-9643-46a08ef2e032\fitme_user_manual.md"
    default_md = local_md if os.path.exists(local_md) else fallback_md

    md_file = sys.argv[1] if len(sys.argv) > 1 else default_md
    out_file = sys.argv[2] if len(sys.argv) > 2 else "FitMe_Complete_User_Manual.pdf"
    build_manual_pdf(md_file, out_file)

