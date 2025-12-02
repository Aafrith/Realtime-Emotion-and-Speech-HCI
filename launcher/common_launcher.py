import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from pathlib import Path
import platform

# Import theme configuration
sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme_config

class ModuleLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - AI Control System")
        
        # DPI awareness (Windows) + Tk scaling
        try:
            if platform.system() == "Windows":
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            self.root.tk.call("tk", "scaling", 1.15)
        except Exception:
            pass
        
        # Load theme colors
        self.current_theme = theme_config.get_current_theme()
        self.colors = theme_config.get_theme_colors(self.current_theme)
        
        self.root.configure(bg=self.colors["bg_primary"])
        
        # Paths
        self.base_dir = Path(__file__).resolve().parent.parent
        venv_python = self.base_dir / ".venv" / "Scripts" / "python.exe"
        self.python = str(venv_python if venv_python.exists() else Path(sys.executable))
        
        # Processes
        self.procs = {}
        
        # Window sizing
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = int(sw * 0.7), int(sh * 0.8)
        x, y = (sw - ww) // 2, (sh - wh) // 2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        self.root.minsize(1000, 700)
        
        self._build_ui()
    
    def _build_ui(self):
        # Setup ttk styles
        self._setup_styles()
        
        # Main container with padding (matching modules)
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Build sections
        self._build_header(main_container)
        self._build_content(main_container)
        self._build_footer(main_container)
    
    def _setup_styles(self):
        """Setup ttk styles to match modules"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Frame styles
        style.configure("Dark.TFrame", background=self.colors["bg_secondary"])
        
        # Label styles
        style.configure("Dark.TLabel", background=self.colors["bg_secondary"], 
                       foreground=self.colors["text_primary"], font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.colors["bg_secondary"], 
                       foreground=self.colors["text_primary"], font=("Segoe UI", 18, "bold"))
    
    def _build_header(self, parent):
        """Modern header matching module design"""
        header = tk.Frame(parent, bg=self.colors["bg_secondary"], bd=0, relief=tk.FLAT, height=80)
        header.grid(row=0, column=0, sticky="nsew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        
        # Brand section
        brand_frame = tk.Frame(header, bg=self.colors["bg_secondary"])
        brand_frame.grid(row=0, column=0, padx=20, pady=20)
        
        # Icon
        icon_label = tk.Label(
            brand_frame,
            text="◉",
            font=("Segoe UI", 42, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["accent_primary"]
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Text branding
        text_brand = tk.Frame(brand_frame, bg=self.colors["bg_secondary"])
        text_brand.pack(side=tk.LEFT)
        
        title_label = tk.Label(
            text_brand,
            text="JARVIS",
            font=("Segoe UI", 32, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            text_brand,
            text="AI Control System",
            font=("Segoe UI", 11),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"]
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # Theme switcher button
        theme_btn_frame = tk.Frame(header, bg=self.colors["bg_secondary"])
        theme_btn_frame.grid(row=0, column=1, sticky="e", padx=20, pady=20)
        
        theme_icon = "🌙" if self.current_theme == "dark" else "☀️"
        theme_text = "Light Mode" if self.current_theme == "dark" else "Dark Mode"
        
        self.theme_btn = tk.Button(
            theme_btn_frame,
            text=f"{theme_icon} {theme_text}",
            command=self.toggle_theme_mode,
            bg=self.colors["accent_secondary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent_primary"],
            activeforeground=self.colors["text_primary"],
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            bd=0,
            padx=15,
            pady=8
        )
        self.theme_btn.pack()
    
    def _build_content(self, parent):
        """Main content area with module cards"""
        content = ttk.Frame(parent, style='Dark.TFrame')
        content.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)
        
        # Welcome section
        welcome_card = tk.Frame(content, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        welcome_card.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 20))
        
        welcome_inner = tk.Frame(welcome_card, bg=self.colors["bg_tertiary"])
        welcome_inner.pack(fill=tk.X, padx=20, pady=20)
        
        welcome_title = tk.Label(
            welcome_inner,
            text="Welcome to Jarvis",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"]
        )
        welcome_title.pack(anchor="w", pady=(0, 8))
        
        welcome_desc = tk.Label(
            welcome_inner,
            text="Experience seamless computer control through emotion recognition, hand gestures, and voice commands. Choose a module below to get started.",
            font=("Segoe UI", 10),
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_secondary"],
            wraplength=900,
            justify=tk.LEFT
        )
        welcome_desc.pack(anchor="w")
        
        # Modules section
        modules_header = ttk.Label(content, text="Control Modules", style='Title.TLabel')
        modules_header.grid(row=1, column=0, sticky="w", pady=(0, 15))
        
        # Modules grid
        modules_frame = ttk.Frame(content, style='Dark.TFrame')
        modules_frame.grid(row=2, column=0, sticky="nsew")
        modules_frame.grid_rowconfigure(0, weight=1)
        modules_frame.grid_columnconfigure(0, weight=1)
        modules_frame.grid_columnconfigure(1, weight=1)
        
        # Module 1: Emotion & Gesture
        self._create_module_card(
            modules_frame,
            row=0, col=0,
            icon="🎭",
            title="Emotion & Gesture Control",
            description="Control your computer through facial expressions and hand movements with real-time AI recognition.",
            features=[
                "Emotion state detection",
                "Hand gesture navigation",
                "Touchless interaction"
            ],
            button_text="Launch Emotion Module",
            accent_color=self.colors["accent_emotion"],
            command=self.launch_emotion
        )
        
        # Module 2: Voice Control
        self._create_module_card(
            modules_frame,
            row=0, col=1,
            icon="🎤",
            title="Voice Command Control",
            description="Control your computer hands-free with natural voice commands and wake word detection.",
            features=[
                "Wake word activation",
                "Natural language commands",
                "Background listening mode"
            ],
            button_text="Launch Voice Module",
            accent_color=self.colors["accent_speech"],
            command=self.launch_speech
        )
    
    def _create_module_card(self, parent, row, col, icon, title, description, 
                           features, button_text, accent_color, command):
        """Create clean module card matching module design"""
        # Card container with spacing
        card_padding = 10 if col == 0 else 0
        card = tk.Frame(parent, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=row, column=col, sticky="nsew", padx=(0, card_padding), pady=5)
        
        # Content
        content = tk.Frame(card, bg=self.colors["bg_tertiary"])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Header with icon
        header = tk.Frame(content, bg=self.colors["bg_tertiary"])
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Icon
        tk.Label(
            header,
            text=icon,
            font=("Segoe UI Emoji", 48),
            bg=self.colors["bg_tertiary"],
            fg=accent_color
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        # Title section
        title_section = tk.Frame(header, bg=self.colors["bg_tertiary"])
        title_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            title_section,
            text=title,
            font=("Segoe UI", 16, "bold"),
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            anchor="w"
        ).pack(fill=tk.X)
        
        # Description
        tk.Label(
            content,
            text=description,
            font=("Segoe UI", 9),
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_secondary"],
            justify=tk.LEFT,
            wraplength=400,
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 15))
        
        # Features
        features_frame = tk.Frame(content, bg=self.colors["bg_tertiary"])
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        for feature in features:
            feature_row = tk.Frame(features_frame, bg=self.colors["bg_tertiary"])
            feature_row.pack(fill=tk.X, pady=3)
            
            tk.Label(
                feature_row,
                text="▸",
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_tertiary"],
                fg=accent_color
            ).pack(side=tk.LEFT, padx=(0, 8))
            
            tk.Label(
                feature_row,
                text=feature,
                font=("Segoe UI", 9),
                bg=self.colors["bg_tertiary"],
                fg=self.colors["text_secondary"]
            ).pack(side=tk.LEFT)
        
        # Launch button
        btn = tk.Button(
            content,
            text=button_text,
            command=command,
            bg=accent_color,
            fg="#000000",
            activebackground=accent_color,
            activeforeground="#000000",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            bd=0
        )
        btn.pack(fill=tk.X, ipady=10)
        
        # Hover effects
        def on_enter(e):
            card.config(bg=self.colors["bg_hover"])
            content.config(bg=self.colors["bg_hover"])
            header.config(bg=self.colors["bg_hover"])
            title_section.config(bg=self.colors["bg_hover"])
            features_frame.config(bg=self.colors["bg_hover"])
            for child in features_frame.winfo_children():
                child.config(bg=self.colors["bg_hover"])
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.config(bg=self.colors["bg_hover"])
        
        def on_leave(e):
            card.config(bg=self.colors["bg_tertiary"])
            content.config(bg=self.colors["bg_tertiary"])
            header.config(bg=self.colors["bg_tertiary"])
            title_section.config(bg=self.colors["bg_tertiary"])
            features_frame.config(bg=self.colors["bg_tertiary"])
            for child in features_frame.winfo_children():
                child.config(bg=self.colors["bg_tertiary"])
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.config(bg=self.colors["bg_tertiary"])
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
    
    def _build_footer(self, parent):
        """Footer section matching module design"""
        footer = tk.Frame(parent, bg=self.colors["bg_secondary"], bd=0, relief=tk.FLAT, height=50)
        footer.grid(row=2, column=0, sticky="nsew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)
        
        # Status section
        status_frame = tk.Frame(footer, bg=self.colors["bg_secondary"])
        status_frame.pack(side=tk.LEFT, pady=15)
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 14),
            bg=self.colors["bg_secondary"],
            fg=self.colors["accent_primary"]
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status = tk.Label(
            status_frame,
            text="System Ready",
            font=("Segoe UI", 9),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"]
        )
        self.status.pack(side=tk.LEFT)
        
        # Version info
        tk.Label(
            footer,
            text="Jarvis v1.0",
            font=("Segoe UI", 9),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.RIGHT, pady=15)
    
    # ---------- Module Launch Actions ----------
    def launch_emotion(self):
        """Launch emotion & gesture module"""
        try:
            script = self.base_dir / "emotion_gesture" / "fullemotionmodule.py"
            if not script.exists():
                messagebox.showerror("Module Not Found", f"Cannot find emotion module:\n{script}")
                return
            if self._running("emotion"):
                messagebox.showinfo("Already Running", "Emotion & Gesture module is already running.")
                return

            proc = subprocess.Popen(
                [self.python, str(script)],
                cwd=str(script.parent),
                env=self._merged_env()
            )
            self.procs["emotion"] = proc
            self._set_status("Emotion module launched", self.colors["accent_emotion"])
            
            # Close the launcher after successful module launch
            self.root.after(500, self.root.destroy)
        except Exception as e:
            self._set_status("Failed to launch module", "#f85149")
            messagebox.showerror("Launch Error", f"Error: {str(e)}")

    def launch_speech(self):
        """Launch voice command module"""
        try:
            script = self.base_dir / "speech_control" / "run.py"
            if not script.exists():
                messagebox.showerror("Module Not Found", f"Cannot find speech module:\n{script}")
                return
            if self._running("speech"):
                messagebox.showinfo("Already Running", "Voice Command module is already running.")
                return

            proc = subprocess.Popen(
                [self.python, str(script)],
                cwd=str(script.parent),
                env=self._merged_env()
            )
            self.procs["speech"] = proc
            self._set_status("Voice module launched", self.colors["accent_speech"])
            
            # Close the launcher after successful module launch
            self.root.after(500, self.root.destroy)
        except Exception as e:
            self._set_status("Failed to launch module", "#f85149")
            messagebox.showerror("Launch Error", f"Error: {str(e)}")

    # ---------- Helpers ----------
    def toggle_theme_mode(self):
        """Toggle between dark and light theme"""
        new_theme = theme_config.toggle_theme()
        self.current_theme = new_theme
        self.colors = theme_config.get_theme_colors(new_theme)
        
        # Destroy all children and rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Rebuild UI
        self.root.configure(bg=self.colors["bg_primary"])
        self._build_ui()
    
    def _merged_env(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.base_dir) + os.pathsep + env.get("PYTHONPATH", "")
        return env

    def _running(self, key):
        return key in self.procs and self.procs[key].poll() is None

    def _set_status(self, msg, color=None):
        self.status.config(text=msg)
        if color:
            self.status_dot.config(fg=color)
        self.root.update_idletasks()

    def on_close(self):
        for p in self.procs.values():
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ModuleLauncherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()