import customtkinter as ctk
import tkinter.font as tkfont

class CanvasEditor:
    def __init__(self, parent, canvas, app_state, on_confirm_callback, on_cancel_callback=None):
        self.parent = parent
        self.canvas = canvas
        self.app_state = app_state
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        self.pil_image = None
        
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

        # Canvas Event Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Key Bindings to Parent
        self.parent.bind("<Up>", self.handle_nudge_up)
        self.parent.bind("<Down>", self.handle_nudge_down)
        self.parent.bind("<Left>", self.handle_nudge_left)
        self.parent.bind("<Right>", self.handle_nudge_right)
        self.parent.bind("<plus>", self.handle_scale_up)
        self.parent.bind("<minus>", self.handle_scale_down)
        self.parent.bind("<=>", self.handle_scale_up) # for without shift
        self.parent.bind("<Return>", self.handle_confirm)
        self.parent.bind("<Escape>", self.handle_cancel)
        self.parent.bind("<c>", self.handle_cycle_color)
        self.parent.bind("<C>", self.handle_cycle_color)
        self.parent.bind("<b>", self.handle_toggle_bold)
        self.parent.bind("<B>", self.handle_toggle_bold)

    def set_image(self, pil_image):
        self.pil_image = pil_image

    def on_canvas_press(self, event):
        if self.app_state.mode != "edit" or not self.app_state.current_pdf_path:
            return
        if self.preview_active:
            self.handle_cancel(None)
            
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
            
        if abs(cur_x - self.drag_start_x) < 5 or abs(cur_y - self.drag_start_y) < 5:
            return
            
        dialog = ctk.CTkInputDialog(text="오버레이할 텍스트를 입력하세요:", title="White-out 텍스트 입력")
        text = dialog.get_input()
        
        if text is not None and text.strip():
            self.preview_ui_rect = (self.drag_start_x, self.drag_start_y, cur_x, cur_y)
            self.preview_text_content = text
            
            # Extract color
            extracted_color = (0, 0, 0)
            if self.pil_image:
                try:
                    x0, x1 = min(self.drag_start_x, cur_x), max(self.drag_start_x, cur_x)
                    y0, y1 = min(self.drag_start_y, cur_y), max(self.drag_start_y, cur_y)
                    x0, y0 = max(0, x0), max(0, y0)
                    x1, y1 = min(self.pil_image.width, x1), min(self.pil_image.height, y1)
                    if x1 > x0 and y1 > y0:
                        crop = self.pil_image.crop((x0, y0, x1, y1)).convert("RGB")
                        pixels = list(crop.getdata())
                        if pixels:
                            darkest = min(pixels, key=lambda p: sum(p))
                            if sum(darkest) < 240 * 3:
                                extracted_color = darkest
                except Exception as e:
                    print(f"Color extraction failed: {e}")
                    
            self.preview_color_options = [extracted_color, (0,0,0), (0,0,255), (255,0,0)]
            self.preview_color_idx = 0
            hex_color = '#%02x%02x%02x' % self.preview_color_options[0]
            
            # Font calculation
            height = abs(cur_y - self.drag_start_y)
            self.preview_fontsize = max(8, int(height * 0.75))
            
            self.preview_x = min(self.drag_start_x, cur_x) + 2
            self.preview_y = max(self.drag_start_y, cur_y) - 2
            self.preview_bold = False
            
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
            self.parent.title("HanPDF Editor - [미리보기 중] 방향키/크기 조절, 'C' 색상, 'B' 굵기, Enter 확정, Esc 취소")

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
            self._update_font()
            
    def handle_scale_down(self, event):
        if self.preview_active and self.preview_fontsize > 2:
            self.preview_fontsize -= 1
            self._update_font()
            
    def handle_cycle_color(self, event):
        if self.preview_active:
            self.preview_color_idx = (self.preview_color_idx + 1) % len(self.preview_color_options)
            hex_color = '#%02x%02x%02x' % self.preview_color_options[self.preview_color_idx]
            self.canvas.itemconfigure(self.preview_text_id, fill=hex_color)

    def handle_toggle_bold(self, event):
        if self.preview_active:
            self.preview_bold = not self.preview_bold
            self._update_font()

    def _update_font(self):
        font_weight = "bold" if self.preview_bold else "normal"
        self.canvas.itemconfigure(self.preview_text_id, font=("Malgun Gothic", -self.preview_fontsize, font_weight))

    def handle_confirm(self, event):
        if self.preview_active:
            try:
                font_weight = "bold" if self.preview_bold else "normal"
                f = tkfont.Font(font=("Malgun Gothic", -self.preview_fontsize, font_weight))
                descent = f.metrics("descent")
                baseline_y = self.preview_y - descent

                data = {
                    "ui_rect": self.preview_ui_rect,
                    "text": self.preview_text_content,
                    "text_x": self.preview_x,
                    "text_y": baseline_y,
                    "ui_fontsize": self.preview_fontsize,
                    "color": self.preview_color_options[self.preview_color_idx],
                    "is_bold": self.preview_bold
                }
                if self.on_confirm_callback:
                    self.on_confirm_callback(data)
            finally:
                self.handle_cancel(None)
                
    def handle_cancel(self, event):
        if self.preview_active:
            self.canvas.delete(self.preview_rect_id)
            self.canvas.delete(self.preview_text_id)
            self.preview_active = False
            self.preview_rect_id = None
            self.preview_text_id = None
            if self.on_cancel_callback:
                self.on_cancel_callback()
            else:
                self.parent.title("HanPDF Editor - MVP")
