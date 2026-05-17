import fitz  # PyMuPDF
from PIL import Image
from services.editor_service import EditorService

class PDFService:
    def __init__(self):
        self.doc = None

    def open_pdf(self, path: str):
        if self.doc:
            self.close()
        self.doc = fitz.open(path)

    def get_page_image(self, page_num: int, dpi: int = 150) -> Image.Image:
        """Returns a PIL Image for the given page number (0-indexed)."""
        if not self.doc:
            raise ValueError("No PDF document is open.")
        if page_num < 0 or page_num >= len(self.doc):
            raise IndexError("Page number out of range.")

        page = self.doc[page_num]
        
        # Calculate matrix for DPI. Default fitz DPI is 72.
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert fitz pixmap to PIL Image
        # "RGB" since alpha=False
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img

    def get_page_count(self) -> int:
        if not self.doc:
            return 0
        return len(self.doc)

    def apply_overlay(self, page_num: int, ui_rect: tuple, text: str, text_x: float, text_y: float, ui_fontsize: int, color: tuple = (0, 0, 0), is_bold: bool = False, dpi: int = 150):
        if not self.doc:
            raise ValueError("No PDF document is open.")
        EditorService.apply_overlay(self.doc, page_num, ui_rect, text, text_x, text_y, ui_fontsize, color, is_bold, dpi)

    def save_pdf(self, original_path: str) -> str:
        if not self.doc:
            raise ValueError("No PDF document is open.")
        return EditorService.save_pdf(self.doc, original_path)

    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None
