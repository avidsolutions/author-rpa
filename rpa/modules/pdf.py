"""PDF automation module for RPA framework."""

from pathlib import Path
from typing import List, Optional, Union

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from ..core.logger import LoggerMixin


class PDFModule(LoggerMixin):
    """Handle PDF file operations."""

    def extract_text(
        self,
        file_path: str,
        pages: Optional[List[int]] = None,
    ) -> str:
        """Extract text content from a PDF.

        Args:
            file_path: Path to PDF file
            pages: Specific page numbers to extract (0-indexed)

        Returns:
            Extracted text content
        """
        self.logger.info(f"Extracting text from: {file_path}")
        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            page_list = pages if pages else range(len(pdf.pages))

            for page_num in page_list:
                if 0 <= page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    text_parts.append(text)

        result = "\n\n".join(text_parts)
        self.logger.info(f"Extracted {len(result)} characters from PDF")
        return result

    def extract_tables(
        self,
        file_path: str,
        pages: Optional[List[int]] = None,
    ) -> List[List[List[str]]]:
        """Extract tables from a PDF.

        Args:
            file_path: Path to PDF file
            pages: Specific page numbers to extract from

        Returns:
            List of tables, each table is a list of rows
        """
        self.logger.info(f"Extracting tables from: {file_path}")
        all_tables = []

        with pdfplumber.open(file_path) as pdf:
            page_list = pages if pages else range(len(pdf.pages))

            for page_num in page_list:
                if 0 <= page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    all_tables.extend(tables)

        self.logger.info(f"Extracted {len(all_tables)} tables from PDF")
        return all_tables

    def merge(
        self,
        input_files: List[str],
        output_path: str,
    ) -> str:
        """Merge multiple PDFs into one.

        Args:
            input_files: List of PDF file paths
            output_path: Output file path

        Returns:
            Path to merged PDF
        """
        self.logger.info(f"Merging {len(input_files)} PDFs")
        merger = PdfMerger()

        for pdf_file in input_files:
            merger.append(pdf_file)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        merger.write(output_path)
        merger.close()

        self.logger.info(f"Created merged PDF: {output_path}")
        return output_path

    def split(
        self,
        input_file: str,
        output_dir: str,
        pages_per_file: int = 1,
    ) -> List[str]:
        """Split a PDF into multiple files.

        Args:
            input_file: Input PDF path
            output_dir: Directory for output files
            pages_per_file: Number of pages per output file

        Returns:
            List of created file paths
        """
        self.logger.info(f"Splitting PDF: {input_file}")
        reader = PdfReader(input_file)
        output_files = []

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        base_name = Path(input_file).stem

        for i in range(0, len(reader.pages), pages_per_file):
            writer = PdfWriter()

            for j in range(i, min(i + pages_per_file, len(reader.pages))):
                writer.add_page(reader.pages[j])

            output_path = Path(output_dir) / f"{base_name}_part{i // pages_per_file + 1}.pdf"
            with open(output_path, "wb") as f:
                writer.write(f)

            output_files.append(str(output_path))

        self.logger.info(f"Created {len(output_files)} PDF files")
        return output_files

    def extract_pages(
        self,
        input_file: str,
        output_path: str,
        pages: List[int],
    ) -> str:
        """Extract specific pages from a PDF.

        Args:
            input_file: Input PDF path
            output_path: Output PDF path
            pages: Page numbers to extract (0-indexed)

        Returns:
            Path to created PDF
        """
        self.logger.info(f"Extracting pages {pages} from {input_file}")
        reader = PdfReader(input_file)
        writer = PdfWriter()

        for page_num in pages:
            if 0 <= page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        self.logger.info(f"Created PDF with {len(pages)} pages: {output_path}")
        return output_path

    def rotate_pages(
        self,
        input_file: str,
        output_path: str,
        rotation: int = 90,
        pages: Optional[List[int]] = None,
    ) -> str:
        """Rotate pages in a PDF.

        Args:
            input_file: Input PDF path
            output_path: Output PDF path
            rotation: Rotation angle (90, 180, 270)
            pages: Specific pages to rotate (None = all)

        Returns:
            Path to created PDF
        """
        reader = PdfReader(input_file)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if pages is None or i in pages:
                page.rotate(rotation)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        self.logger.info(f"Rotated PDF pages: {output_path}")
        return output_path

    def add_watermark(
        self,
        input_file: str,
        output_path: str,
        watermark_text: str,
        opacity: float = 0.3,
    ) -> str:
        """Add a text watermark to a PDF.

        Args:
            input_file: Input PDF path
            output_path: Output PDF path
            watermark_text: Text to use as watermark
            opacity: Watermark opacity (0-1)

        Returns:
            Path to watermarked PDF
        """
        # Create watermark PDF
        watermark_path = "/tmp/watermark_temp.pdf"
        c = canvas.Canvas(watermark_path, pagesize=letter)
        c.saveState()
        c.setFillAlpha(opacity)
        c.setFont("Helvetica", 60)
        c.translate(letter[0] / 2, letter[1] / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, watermark_text)
        c.restoreState()
        c.save()

        # Apply watermark
        reader = PdfReader(input_file)
        watermark_reader = PdfReader(watermark_path)
        watermark_page = watermark_reader.pages[0]

        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        Path(watermark_path).unlink()
        self.logger.info(f"Added watermark to PDF: {output_path}")
        return output_path

    def get_info(self, file_path: str) -> dict:
        """Get PDF metadata and information.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict with PDF information
        """
        reader = PdfReader(file_path)
        metadata = reader.metadata or {}

        return {
            "path": file_path,
            "pages": len(reader.pages),
            "title": metadata.get("/Title", ""),
            "author": metadata.get("/Author", ""),
            "subject": metadata.get("/Subject", ""),
            "creator": metadata.get("/Creator", ""),
            "producer": metadata.get("/Producer", ""),
            "encrypted": reader.is_encrypted,
        }

    def create_from_text(
        self,
        text: str,
        output_path: str,
        title: Optional[str] = None,
    ) -> str:
        """Create a simple PDF from text content.

        Args:
            text: Text content
            output_path: Output PDF path
            title: Optional document title

        Returns:
            Path to created PDF
        """
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        if title:
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, height - inch, title)
            y_position = height - 1.5 * inch
        else:
            y_position = height - inch

        c.setFont("Helvetica", 12)
        lines = text.split("\n")

        for line in lines:
            if y_position < inch:
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = height - inch

            c.drawString(inch, y_position, line[:80])  # Truncate long lines
            y_position -= 14

        c.save()
        self.logger.info(f"Created PDF from text: {output_path}")
        return output_path

    def encrypt(
        self,
        input_file: str,
        output_path: str,
        password: str,
    ) -> str:
        """Encrypt a PDF with a password.

        Args:
            input_file: Input PDF path
            output_path: Output PDF path
            password: Password to set

        Returns:
            Path to encrypted PDF
        """
        reader = PdfReader(input_file)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        with open(output_path, "wb") as f:
            writer.write(f)

        self.logger.info(f"Created encrypted PDF: {output_path}")
        return output_path

    def decrypt(
        self,
        input_file: str,
        output_path: str,
        password: str,
    ) -> str:
        """Decrypt a password-protected PDF.

        Args:
            input_file: Input PDF path
            output_path: Output PDF path
            password: PDF password

        Returns:
            Path to decrypted PDF
        """
        reader = PdfReader(input_file)
        reader.decrypt(password)

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        self.logger.info(f"Created decrypted PDF: {output_path}")
        return output_path
