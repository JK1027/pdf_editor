import fitz
import os

class EditorService:
    @staticmethod
    def apply_overlay(doc: fitz.Document, page_num: int, ui_rect: tuple, text: str, dpi: int = 150):
        """
        ui_rect: (x0, y0, x1, y1) in canvas pixels.
        Converts to PDF points (72 DPI) and applies whiteout + text.
        """
        if not doc or page_num < 0 or page_num >= len(doc):
            return

        page = doc[page_num]
        
        # Scaling factor from UI (e.g. 150 DPI) to PDF (72 DPI)
        scale = 72.0 / dpi
        x0, y0, x1, y1 = [v * scale for v in ui_rect]
        
        # Ensure coordinates are in correct min/max order
        rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        
        # 1. White-out (Draw a white rectangle)
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
        
        # 2. Insert Text
        if text.strip():
            font_path = r"C:\Windows\Fonts\malgun.ttf"
            if not os.path.exists(font_path):
                # Fallback to default if malgun is not found
                font_path = None
                
            # Positioning text slightly below the top-left corner of the rect
            # Assuming fontsize 11, y-offset around 11 points for the baseline
            text_point = fitz.Point(rect.x0 + 2, rect.y0 + 11)
            
            if font_path:
                # Insert using specific TrueType Font (for Korean support)
                page.insert_text(text_point, text, fontname="malgun", fontfile=font_path, fontsize=11, color=(0, 0, 0))
            else:
                # Basic ASCII fallback
                page.insert_text(text_point, text, fontsize=11, color=(0, 0, 0))

    @staticmethod
    def save_pdf(doc: fitz.Document, original_path: str) -> str:
        if not doc or not original_path:
            return ""
            
        base, ext = os.path.splitext(original_path)
        new_path = f"{base}_수정본{ext}"
        
        # Save changes incrementally if possible, else save to new file
        doc.save(new_path)
        return new_path
