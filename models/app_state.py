from dataclasses import dataclass
from typing import Optional

@dataclass
class AppState:
    current_pdf_path: Optional[str] = None
    current_page: int = 0
    total_pages: int = 0
    scaling_factor: float = 1.0
    mode: str = "viewer"  # 'viewer' or 'edit'

    # Undo/Redo 아키텍처용 데이터 구조
    action_history: list = None
    redo_history: list = None

    def __post_init__(self):
        if self.action_history is None:
            self.action_history = []
        if self.redo_history is None:
            self.redo_history = []

    def reset(self):
        self.current_pdf_path = None
        self.current_page = 0
        self.total_pages = 0
        self.mode = "viewer"
        self.action_history.clear()
        self.redo_history.clear()
