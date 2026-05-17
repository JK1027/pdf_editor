import fitz
import os
from utils.resource import get_resource_path

class EditorService:
    @staticmethod
    def apply_overlay(doc: fitz.Document, page_num: int, ui_rect: tuple, text: str, text_x: float, text_y: float, ui_fontsize: int, color: tuple = (0, 0, 0), is_bold: bool = False, dpi: int = 150):
        """
        ui_rect: (x0, y0, x1, y1) in canvas pixels.
        text_x, text_y: Anchor Point (Bottom-Left baseline) in UI pixels.
        color: RGB tuple (0~255, 0~255, 0~255)
        is_bold: If True, uses bold font.
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
            if is_bold:
                sys_font_path = r"C:\Windows\Fonts\malgunbd.ttf"
                bundled_font_path = get_resource_path(os.path.join("assets", "fonts", "malgunbd.ttf"))
                fontname = "malgunbd"
            else:
                sys_font_path = r"C:\Windows\Fonts\malgun.ttf"
                bundled_font_path = get_resource_path(os.path.join("assets", "fonts", "malgun.ttf"))
                fontname = "malgun"
                
            # Fallback 로직: 내장 폰트 -> 시스템 폰트 -> 없음(기본)
            if os.path.exists(bundled_font_path):
                font_path = bundled_font_path
            elif os.path.exists(sys_font_path):
                font_path = sys_font_path
            else:
                font_path = None
                
            # Both Tkinter anchor="sw" and PyMuPDF Point use the Bottom-Left baseline.
            # So we can just scale the UI point directly!
            text_point = fitz.Point(text_x * scale, text_y * scale)
            pdf_fontsize = ui_fontsize * scale
            
            # Convert RGB 0~255 tuple to PyMuPDF's 0.0~1.0 float tuple
            pdf_color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
            
            if font_path:
                # Insert using specific TrueType Font (for Korean support)
                page.insert_text(text_point, text, fontname=fontname, fontfile=font_path, fontsize=pdf_fontsize, color=pdf_color)
            else:
                # Basic ASCII fallback
                page.insert_text(text_point, text, fontsize=pdf_fontsize, color=pdf_color)

    @staticmethod
    def save_pdf(doc: fitz.Document, original_path: str) -> str:
        if not doc or not original_path:
            return ""
            
        base, ext = os.path.splitext(original_path)
        new_path = f"{base}_수정본{ext}"
        
        # Save changes incrementally if possible, else save to new file
        doc.save(new_path)
        return new_path
