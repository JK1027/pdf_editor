import customtkinter as ctk
from ui.main_window import MainWindow

def main():
    # Set default appearance mode and color theme
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    # Create the main window and start the event loop
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
