import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import ImageTk
from models.app_state import AppState
from ui.toolbar import Toolbar
from services.pdf_service import PDFService
import threading

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("HanPDF Editor - MVP")
        self.geometry("1200x800")
        
        # State
        self.app_state = AppState()
        self.pdf_service = PDFService()

        # Layout Grid Configuration (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Toolbar
        self.toolbar = Toolbar(
            self,
            on_open_file=self.handle_open_file,
            on_mode_change=self.handle_mode_change,
            on_save=self.handle_save
        )
        self.toolbar.grid(row=0, column=0, sticky="nsew")

        # 2. Main Area (Canvas + Navigation)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Canvas Area (for PDF Images)
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # We use a standard tkinter canvas inside the CTkFrame to draw images/rectangles
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="gray20", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal", command=self.canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Explicit reference to prevent Image Garbage Collection
        self.current_image = None 
        self.pil_image = None # Raw image for pixel sampling
        
        # Delegate overlay editing to CanvasEditor
        from ui.canvas_editor import CanvasEditor
        self.canvas_editor = CanvasEditor(
            parent=self,
            canvas=self.canvas,
            app_state=self.app_state,
            on_confirm_callback=self.handle_overlay_confirm,
            on_cancel_callback=self.handle_overlay_cancel
        )

        # Bottom Navigation Area
        self.nav_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.nav_frame.grid(row=1, column=0, sticky="ew")
        
        self.prev_btn = ctk.CTkButton(self.nav_frame, text="< 이전", width=80, command=self.handle_prev_page)
        self.prev_btn.pack(side="left", padx=20, pady=10)

        self.page_label = ctk.CTkLabel(self.nav_frame, text="페이지: 0 / 0")
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(self.nav_frame, text="다음 >", width=80, command=self.handle_next_page)
        self.next_btn.pack(side="right", padx=20, pady=10)

    # --- Event Handlers ---
    def handle_open_file(self):
        file_path = filedialog.askopenfilename(
            title="PDF 파일 열기",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not file_path:
            return
            
        try:
            self.pdf_service.open_pdf(file_path)
            self.app_state.current_pdf_path = file_path
            self.app_state.current_page = 0
            self.app_state.total_pages = self.pdf_service.get_page_count()
            self.render_page()
        except Exception as e:
            print(f"Failed to open PDF: {e}")

    def render_page(self):
        if not self.app_state.current_pdf_path:
            return

        # Show Loading Indicator
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() / 2 if self.canvas.winfo_width() > 10 else 400,
            self.canvas.winfo_height() / 2 if self.canvas.winfo_height() > 10 else 300,
            text="페이지를 불러오는 중...", fill="white", font=("Malgun Gothic", 16)
        )
        
        page_num = self.app_state.current_page
        
        def _load_task():
            try:
                pil_image = self.pdf_service.get_page_image(page_num, dpi=150)
                # 메인 스레드에서 UI 업데이트를 수행하도록 스케줄링
                self.after(0, lambda: self._on_page_rendered(pil_image, page_num))
            except Exception as e:
                self.after(0, lambda: print(f"Failed to render page: {e}"))
                
        # 백그라운드 스레드에서 무거운 이미지 변환 작업 수행
        threading.Thread(target=_load_task, daemon=True).start()

    def _on_page_rendered(self, pil_image, page_num):
        # 만약 스레드가 도는 사이에 사용자가 페이지를 바꿨다면 무시
        if self.app_state.current_page != page_num:
            return
            
        try:
            self.pil_image = pil_image
            
            # Convert to ImageTk.PhotoImage
            self.current_image = ImageTk.PhotoImage(self.pil_image)
            
            # Clear canvas and draw
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.current_image, anchor="nw")
            
            # Update scrollregion so that the image is fully scrollable if canvas scrollbars are added later
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            self.canvas_editor.set_image(self.pil_image)
            self.update_page_label()
            
        except Exception as e:
            print(f"Failed to update UI after rendering: {e}")

    def handle_mode_change(self, value):
        self.app_state.mode = "viewer" if value == "뷰어" else "edit"
        print(f"Mode changed to: {self.app_state.mode}")

    def handle_overlay_confirm(self, data):
        try:
            self.pdf_service.apply_overlay(
                page_num=self.app_state.current_page,
                ui_rect=data['ui_rect'],
                text=data['text'],
                text_x=data['text_x'],
                text_y=data['text_y'],
                ui_fontsize=data['ui_fontsize'],
                color=data['color'],
                is_bold=data['is_bold'],
                dpi=150
            )
        except Exception as e:
            messagebox.showerror("오류", f"오버레이 적용 중 오류 발생: {e}")
        finally:
            self.render_page()

    def handle_overlay_cancel(self):
        self.title("HanPDF Editor - MVP")

    def handle_save(self):
        if not self.pdf_service.doc or not self.app_state.current_pdf_path:
            messagebox.showwarning("저장 불가", "열려있는 PDF 파일이 없습니다.")
            return
            
        try:
            new_path = self.pdf_service.save_pdf(self.app_state.current_pdf_path)
            messagebox.showinfo("저장 완료", f"다음 경로에 저장되었습니다:\n{new_path}")
        except Exception as e:
            messagebox.showerror("저장 오류", f"파일 저장 중 오류가 발생했습니다: {e}")

    def handle_prev_page(self):
        if self.app_state.current_page > 0:
            self.app_state.current_page -= 1
            self.render_page()

    def handle_next_page(self):
        if self.app_state.current_page < self.app_state.total_pages - 1:
            self.app_state.current_page += 1
            self.render_page()

    def update_page_label(self):
        # UI shows 1-indexed page number
        current = self.app_state.current_page + 1 if self.app_state.total_pages > 0 else 0
        self.page_label.configure(text=f"페이지: {current} / {self.app_state.total_pages}")
