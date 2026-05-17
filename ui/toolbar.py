import customtkinter as ctk
from typing import Callable

class Toolbar(ctk.CTkFrame):
    def __init__(self, master, on_open_file: Callable, on_mode_change: Callable, on_save: Callable, **kwargs):
        super().__init__(master, width=200, **kwargs)
        self.pack_propagate(False) # Keep width fixed

        # Title
        self.title_label = ctk.CTkLabel(self, text="HanPDF Editor", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 30), padx=10)

        # Open File Button
        self.open_btn = ctk.CTkButton(self, text="파일 열기", command=on_open_file)
        self.open_btn.pack(pady=10, padx=20, fill="x")

        # Mode Selection
        self.mode_label = ctk.CTkLabel(self, text="모드 선택")
        self.mode_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.mode_var = ctk.StringVar(value="뷰어")
        self.mode_segmented = ctk.CTkSegmentedButton(
            self, 
            values=["뷰어", "편집"],
            variable=self.mode_var,
            command=on_mode_change
        )
        self.mode_segmented.pack(pady=5, padx=20, fill="x")

        # Spacer
        self.spacer = ctk.CTkLabel(self, text="")
        self.spacer.pack(pady=10, expand=True, fill="y")

        # Save Button
        self.save_btn = ctk.CTkButton(self, text="저장 (Save As)", command=on_save, fg_color="green", hover_color="darkgreen")
        self.save_btn.pack(pady=(10, 20), padx=20, fill="x")
