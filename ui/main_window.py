import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
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
        
        # Preview State Variables
        self.preview_active = False
        self.preview_rect_id = None
        self.preview_text_id = None
        self.preview_text_content = ""
        self.preview_fontsize = 11
        self.preview_x = 0
        self.preview_y = 0
        self.preview_ui_rect = None
        self.preview_color_options = [(0,0,0), (0,0,255), (255,0,0)]
        self.preview_color_idx = 0
        self.preview_bold = False

        # Explicit reference to prevent Image Garbage Collection
        self.current_image = None 
        self.pil_image = None # Raw image for pixel sampling
        
        # Key Bindings
        self.bind("<Up>", self.handle_nudge_up)
        self.bind("<Down>", self.handle_nudge_down)
        self.bind("<Left>", self.handle_nudge_left)
        self.bind("<Right>", self.handle_nudge_right)
        self.bind("<plus>", self.handle_scale_up)
        self.bind("<minus>", self.handle_scale_down)
        self.bind("<=>", self.handle_scale_up) # for without shift
        self.bind("<Return>", self.handle_confirm)
        self.bind("<Escape>", self.handle_cancel)
        self.bind("<c>", self.handle_cycle_color)
        self.bind("<C>", self.handle_cycle_color)
        self.bind("<b>", self.handle_toggle_bold)
        self.bind("<B>", self.handle_toggle_bold)

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
            self.pil_image = self.pdf_service.get_page_image(self.app_state.current_page, dpi=150)
            
            # Convert to ImageTk.PhotoImage
            self.current_image = ImageTk.PhotoImage(self.pil_image)
            
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
        if self.preview_active:
            # If user clicks elsewhere during preview, cancel preview
            self.handle_cancel(None)
            
        # Adjust for canvas scrolling
        self.drag_start_x = self.canvas.canvasx(event.x)
        self.drag_start_y = self.canvas.canvasy(event.y)

    def on_canvas_drag(self, event):
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path or self.preview_active:
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
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path or self.preview_active:
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
        
        if text is not None and text.strip():
            self.preview_ui_rect = (self.drag_start_x, self.drag_start_y, cur_x, cur_y)
            self.preview_text_content = text
            
            # Extract dominant darkest color from the region
            extracted_color = (0, 0, 0)
            if self.pil_image:
                try:
                    x0, x1 = min(self.drag_start_x, cur_x), max(self.drag_start_x, cur_x)
                    y0, y1 = min(self.drag_start_y, cur_y), max(self.drag_start_y, cur_y)
                    # clamp to bounds
                    x0, y0 = max(0, x0), max(0, y0)
                    x1, y1 = min(self.pil_image.width, x1), min(self.pil_image.height, y1)
                    if x1 > x0 and y1 > y0:
                        crop = self.pil_image.crop((x0, y0, x1, y1)).convert("RGB")
                        pixels = list(crop.getdata())
                        if pixels:
                            darkest = min(pixels, key=lambda p: sum(p))
                            if sum(darkest) < 240 * 3: # Avoid pure white
                                extracted_color = darkest
                except Exception as e:
                    print(f"Color extraction failed: {e}")
                    
            self.preview_color_options = [extracted_color, (0,0,0), (0,0,255), (255,0,0)]
            self.preview_color_idx = 0
            hex_color = '#%02x%02x%02x' % self.preview_color_options[0]
            
            # Auto-calculate fontsize based on box height (approx 75%)
            height = abs(cur_y - self.drag_start_y)
            self.preview_fontsize = max(8, int(height * 0.75))
            
            # Start position: Bottom-Left of the box for "sw" anchor
            self.preview_x = min(self.drag_start_x, cur_x) + 2
            self.preview_y = max(self.drag_start_y, cur_y) - 2
            self.preview_bold = False
            
            # Draw Preview
            self.preview_rect_id = self.canvas.create_rectangle(
                self.drag_start_x, self.drag_start_y, cur_x, cur_y,
                fill="white", outline="white"
            )
            self.preview_text_id = self.canvas.create_text(
                self.preview_x, self.preview_y, 
                text=self.preview_text_content, anchor="sw", 
                font=("Malgun Gothic", -self.preview_fontsize, "normal"), fill=hex_color
            )
            self.preview_active = True
            
            # Change Title as a Hint
            self.title("HanPDF Editor - [미리보기 중] 방향키/크기 조절, 'C' 색상, 'B' 굵기, Enter 확정, Esc 취소")

    # --- Preview & Nudge Handlers ---
    def handle_nudge_up(self, event):
        if self.preview_active:
            self.preview_y -= 1
            self.canvas.coords(self.preview_text_id, self.preview_x, self.preview_y)
            
    def handle_nudge_down(self, event):
        if self.preview_active:
            self.preview_y += 1
            self.canvas.coords(self.preview_text_id, self.preview_x, self.preview_y)
            
    def handle_nudge_left(self, event):
        if self.preview_active:
            self.preview_x -= 1
            self.canvas.coords(self.preview_text_id, self.preview_x, self.preview_y)
            
    def handle_nudge_right(self, event):
        if self.preview_active:
            self.preview_x += 1
            self.canvas.coords(self.preview_text_id, self.preview_x, self.preview_y)
            
    def handle_scale_up(self, event):
        if self.preview_active:
            self.preview_fontsize += 1
            font_weight = "bold" if self.preview_bold else "normal"
            self.canvas.itemconfigure(self.preview_text_id, font=("Malgun Gothic", -self.preview_fontsize, font_weight))
            
    def handle_scale_down(self, event):
        if self.preview_active and self.preview_fontsize > 2:
            self.preview_fontsize -= 1
            font_weight = "bold" if self.preview_bold else "normal"
            self.canvas.itemconfigure(self.preview_text_id, font=("Malgun Gothic", -self.preview_fontsize, font_weight))
            
    def handle_cycle_color(self, event):
        if self.preview_active:
            self.preview_color_idx = (self.preview_color_idx + 1) % len(self.preview_color_options)
            hex_color = '#%02x%02x%02x' % self.preview_color_options[self.preview_color_idx]
            self.canvas.itemconfigure(self.preview_text_id, fill=hex_color)

    def handle_toggle_bold(self, event):
        if self.preview_active:
            self.preview_bold = not self.preview_bold
            font_weight = "bold" if self.preview_bold else "normal"
            self.canvas.itemconfigure(self.preview_text_id, font=("Malgun Gothic", -self.preview_fontsize, font_weight))
            
    def handle_confirm(self, event):
        if self.preview_active:
            try:
                # Tkinter의 anchor="sw"는 텍스트 박스의 가장 아래(Descent 포함)를 의미하지만,
                # PyMuPDF의 좌표는 글자의 기본선(Baseline)을 의미합니다.
                # 이 둘의 차이(Descent)만큼 y좌표를 위로 올려주어야 위치가 정확히 일치합니다.
                font_weight = "bold" if self.preview_bold else "normal"
                f = tkfont.Font(font=("Malgun Gothic", -self.preview_fontsize, font_weight))
                descent = f.metrics("descent")
                baseline_y = self.preview_y - descent

                EditorService.apply_overlay(
                    doc=self.pdf_service.doc,
                    page_num=self.app_state.current_page,
                    ui_rect=self.preview_ui_rect,
                    text=self.preview_text_content,
                    text_x=self.preview_x,
                    text_y=baseline_y,
                    ui_fontsize=self.preview_fontsize,
                    color=self.preview_color_options[self.preview_color_idx],
                    is_bold=self.preview_bold,
                    dpi=150
                )
            except Exception as e:
                messagebox.showerror("오류", f"오버레이 적용 중 오류 발생: {e}")
            finally:
                self.handle_cancel(None) # Clear UI
                self.render_page()       # Refresh
                
    def handle_cancel(self, event):
        if self.preview_active:
            self.canvas.delete(self.preview_rect_id)
            self.canvas.delete(self.preview_text_id)
            self.preview_active = False
            self.preview_rect_id = None
            self.preview_text_id = None
            self.title("HanPDF Editor - MVP")

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
