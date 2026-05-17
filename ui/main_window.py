import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import ImageTk
from models.app_state import AppState
from ui.toolbar import Toolbar
from services.pdf_service import PDFService
from services.editor_service import EditorService

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
        
        # Canvas Event Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Drag State Variables
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.temp_rect_id = None

        # Explicit reference to prevent Image Garbage Collection
        self.current_image = None 

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

        try:
            pil_image = self.pdf_service.get_page_image(self.app_state.current_page, dpi=150)
            
            # Convert to ImageTk.PhotoImage
            self.current_image = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and draw
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.current_image, anchor="nw")
            
            # Update scrollregion so that the image is fully scrollable if canvas scrollbars are added later
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            self.update_page_label()
            
        except Exception as e:
            print(f"Failed to render page: {e}")

    def handle_mode_change(self, value):
        self.app_state.mode = "viewer" if value == "뷰어" else "edit"
        print(f"Mode changed to: {self.app_state.mode}")

    def on_canvas_press(self, event):
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path:
            return
        # Adjust for canvas scrolling if scrollbars are added later. For now, event.x/y is fine.
        self.drag_start_x = self.canvas.canvasx(event.x)
        self.drag_start_y = self.canvas.canvasy(event.y)

    def on_canvas_drag(self, event):
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path:
            return
            
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if self.temp_rect_id:
            self.canvas.delete(self.temp_rect_id)
            
        self.temp_rect_id = self.canvas.create_rectangle(
            self.drag_start_x, self.drag_start_y, cur_x, cur_y,
            outline="blue", dash=(4, 4), width=2
        )

    def on_canvas_release(self, event):
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path:
            return
            
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if self.temp_rect_id:
            self.canvas.delete(self.temp_rect_id)
            self.temp_rect_id = None
            
        # Ignore accidental tiny clicks
        if abs(cur_x - self.drag_start_x) < 5 or abs(cur_y - self.drag_start_y) < 5:
            return
            
        # Prompt for text
        dialog = ctk.CTkInputDialog(text="오버레이할 텍스트를 입력하세요:", title="White-out 텍스트 입력")
        text = dialog.get_input()
        
        if text is not None:
            ui_rect = (self.drag_start_x, self.drag_start_y, cur_x, cur_y)
            try:
                EditorService.apply_overlay(
                    doc=self.pdf_service.doc,
                    page_num=self.app_state.current_page,
                    ui_rect=ui_rect,
                    text=text,
                    dpi=150
                )
                self.render_page() # Re-render to show changes
            except Exception as e:
                messagebox.showerror("오류", f"오버레이 적용 중 오류 발생: {e}")

    def handle_save(self):
        if not self.pdf_service.doc or not self.app_state.current_pdf_path:
            messagebox.showwarning("저장 불가", "열려있는 PDF 파일이 없습니다.")
            return
            
        try:
            new_path = EditorService.save_pdf(self.pdf_service.doc, self.app_state.current_pdf_path)
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
