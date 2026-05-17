from dataclasses import dataclass
from typing import Optional

@dataclass
class AppState:
    current_pdf_path: Optional[str] = None
    current_page: int = 0
    total_pages: int = 0
    scaling_factor: float = 1.0
    mode: str = "viewer"  # 'viewer' or 'edit'

    def reset(self):
        self.current_pdf_path = None
        self.current_page = 0
        self.total_pages = 0
        self.mode = "viewer"
