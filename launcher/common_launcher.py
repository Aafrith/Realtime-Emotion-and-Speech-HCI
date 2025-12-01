import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from pathlib import Path

class ModuleLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - AI Control System")
        self.root.minsize(1100, 750)
        self.root.geometry("1200x800")
        
        # Professional Dark Theme Palette
        self.bg_dark = "#0d1117"
        self.bg_secondary = "#161b22"
        self.card_bg = "#1c2128"
        self.card_hover = "#21262d"
        self.accent_blue = "#58a6ff"
        self.accent_purple = "#a371f7"
        self.accent_green = "#3fb950"
        self.text_primary = "#f0f6fc"
        self.text_secondary = "#8b949e"
        self.text_muted = "#6e7681"
        self.border_dark = "#30363d"
        self.border_subtle = "#21262d"
        
        self.root.configure(bg=self.bg_dark)
        
        # Paths
        self.base_dir = Path(__file__).resolve().parent.parent
        venv_python = self.base_dir / ".venv" / "Scripts" / "python.exe"
        self.python = str(venv_python if venv_python.exists() else Path(sys.executable))
        
        # Processes
        self.procs = {}
        
        self._build_ui()
    
    def _build_ui(self):
        # Main scrollable container
        main_container = tk.Frame(self.root, bg=self.bg_dark)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(main_container, bg=self.bg_dark, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', configure_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Content wrapper
        content = tk.Frame(scrollable_frame, bg=self.bg_dark)
        content.pack(fill=tk.BOTH, expand=True, padx=50, pady=40)
        
        # Build sections
        self._build_header(content)
        self._build_hero_section(content)
        self._build_modules_section(content)
        self._build_status_section(content)
        self._build_footer(content)
    
    def _build_header(self, parent):
        """Modern header with branding"""
        header_bg = tk.Frame(parent, bg=self.bg_dark)
        header_bg.pack(fill=tk.X, pady=(0, 40))
        
        # Logo and brand
        brand_frame = tk.Frame(header_bg, bg=self.bg_dark)
        brand_frame.pack(anchor="center")
        
        # Icon
        icon_label = tk.Label(
            brand_frame,
            text="◉",
            font=("Segoe UI", 56, "bold"),
            bg=self.bg_dark,
            fg=self.accent_blue
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Text branding
        text_brand = tk.Frame(brand_frame, bg=self.bg_dark)
        text_brand.pack(side=tk.LEFT)
        
        tk.Label(
            text_brand,
            text="J A R V I S",
            font=("Segoe UI", 48, "bold"),
            bg=self.bg_dark,
            fg=self.text_primary
        ).pack(anchor="w")
        
        tk.Label(
            text_brand,
            text="AI-Powered Multimodal Control System",
            font=("Segoe UI", 12),
            bg=self.bg_dark,
            fg=self.text_secondary
        ).pack(anchor="w", pady=(2, 0))
    
    def _build_hero_section(self, parent):
        """Hero section with project overview"""
        hero = tk.Frame(parent, bg=self.card_bg, bd=0)
        hero.pack(fill=tk.X, pady=(0, 35))
        
        # Add subtle border effect
        border_frame = tk.Frame(hero, bg=self.border_dark, height=1)
        border_frame.pack(fill=tk.X, side=tk.TOP)
        
        inner = tk.Frame(hero, bg=self.card_bg)
        inner.pack(fill=tk.X, padx=40, pady=35)
        
        # Title
        tk.Label(
            inner,
            text="Welcome to the Future of Interaction",
            font=("Segoe UI", 24, "bold"),
            bg=self.card_bg,
            fg=self.text_primary
        ).pack(anchor="w", pady=(0, 15))
        
        # Description
        desc_text = (
            "Jarvis revolutionizes how you interact with your computer through advanced AI technology. "
            "Experience seamless control using facial emotions, hand gestures, and voice commands. "
            "Built with privacy in mind—all processing happens locally on your device."
        )
        
        tk.Label(
            inner,
            text=desc_text,
            font=("Segoe UI", 11),
            bg=self.card_bg,
            fg=self.text_secondary,
            justify=tk.LEFT,
            wraplength=1000
        ).pack(anchor="w", pady=(0, 25))
        
        # Feature badges
        badges_frame = tk.Frame(inner, bg=self.card_bg)
        badges_frame.pack(fill=tk.X)
        
        badges = [
            ("⚡", "Real-time", "Instant AI processing"),
            ("🔒", "Secure", "100% local & private"),
            ("🎯", "Accurate", "Advanced ML models"),
            ("🌐", "Universal", "Works on any PC")
        ]
        
        for icon, title, desc in badges:
            self._create_badge(badges_frame, icon, title, desc)
    
    def _create_badge(self, parent, icon, title, description):
        """Create feature badge"""
        badge = tk.Frame(parent, bg=self.bg_secondary, bd=0)
        badge.pack(side=tk.LEFT, padx=(0, 15), pady=5)
        
        inner = tk.Frame(badge, bg=self.bg_secondary)
        inner.pack(padx=20, pady=15)
        
        tk.Label(
            inner,
            text=icon,
            font=("Segoe UI Emoji", 24),
            bg=self.bg_secondary,
            fg=self.accent_blue
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        text_frame = tk.Frame(inner, bg=self.bg_secondary)
        text_frame.pack(side=tk.LEFT)
        
        tk.Label(
            text_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        ).pack(anchor="w")
        
        tk.Label(
            text_frame,
            text=description,
            font=("Segoe UI", 9),
            bg=self.bg_secondary,
            fg=self.text_muted
        ).pack(anchor="w")
    
    def _build_modules_section(self, parent):
        """Control modules section"""
        # Section header
        header_frame = tk.Frame(parent, bg=self.bg_dark)
        header_frame.pack(fill=tk.X, pady=(10, 25))
        
        tk.Label(
            header_frame,
            text="Control Modules",
            font=("Segoe UI", 26, "bold"),
            bg=self.bg_dark,
            fg=self.text_primary
        ).pack(side=tk.LEFT)
        
        tk.Label(
            header_frame,
            text="Choose a module to launch",
            font=("Segoe UI", 11),
            bg=self.bg_dark,
            fg=self.text_secondary
        ).pack(side=tk.LEFT, padx=(15, 0))
        
        # Modules grid
        modules_grid = tk.Frame(parent, bg=self.bg_dark)
        modules_grid.pack(fill=tk.BOTH, expand=True)
        modules_grid.columnconfigure(0, weight=1, uniform="modules")
        modules_grid.columnconfigure(1, weight=1, uniform="modules")
        
        # Module 1: Emotion & Gesture
        self._create_premium_card(
            modules_grid,
            row=0, col=0,
            icon="🎭",
            title="Emotion & Gesture Control",
            subtitle="Visual AI Recognition",
            description=(
                "Transform your facial expressions and hand movements into computer commands. "
                "Powered by MediaPipe and custom-trained ML models for accurate emotion detection."
            ),
            features=[
                "7 emotion states recognition",
                "Real-time hand tracking",
                "Gesture-based navigation",
                "Touchless interaction"
            ],
            requirements="Requires: Webcam",
            button_text="Launch Module",
            accent_color=self.accent_blue,
            command=self.launch_emotion
        )
        
        # Module 2: Voice Control
        self._create_premium_card(
            modules_grid,
            row=0, col=1,
            icon="🎤",
            title="Voice Command Control",
            subtitle="Speech AI Recognition",
            description=(
                "Control your computer hands-free with natural voice commands. "
                "Features wake word detection and continuous listening for seamless interaction."
            ),
            features=[
                "Custom wake word support",
                "Natural language commands",
                "Background listening mode",
                "Multi-language support"
            ],
            requirements="Requires: Microphone",
            button_text="Launch Module",
            accent_color=self.accent_purple,
            command=self.launch_speech
        )
    
    def _create_premium_card(self, parent, row, col, icon, title, subtitle, 
                            description, features, requirements, button_text, 
                            accent_color, command):
        """Create premium module card"""
        # Card container
        card_container = tk.Frame(parent, bg=self.bg_dark)
        card_container.grid(row=row, column=col, sticky="nsew", padx=(0, 20 if col == 0 else 0), pady=10)
        
        card = tk.Frame(
            card_container,
            bg=self.card_bg,
            bd=0,
            highlightbackground=self.border_dark,
            highlightthickness=1
        )
        card.pack(fill=tk.BOTH, expand=True)
        
        # Content padding
        content = tk.Frame(card, bg=self.card_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header section
        header = tk.Frame(content, bg=self.card_bg)
        header.pack(fill=tk.X, pady=(0, 20))
        
        # Icon circle
        icon_frame = tk.Frame(header, bg=self.bg_secondary, width=70, height=70)
        icon_frame.pack(side=tk.LEFT, padx=(0, 18))
        icon_frame.pack_propagate(False)
        
        tk.Label(
            icon_frame,
            text=icon,
            font=("Segoe UI Emoji", 32),
            bg=self.bg_secondary,
            fg=accent_color
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Title section
        title_section = tk.Frame(header, bg=self.card_bg)
        title_section.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            title_section,
            text=title,
            font=("Segoe UI", 18, "bold"),
            bg=self.card_bg,
            fg=self.text_primary
        ).pack(anchor="w")
        
        tk.Label(
            title_section,
            text=subtitle,
            font=("Segoe UI", 10),
            bg=self.card_bg,
            fg=accent_color
        ).pack(anchor="w", pady=(2, 0))
        
        # Description
        tk.Label(
            content,
            text=description,
            font=("Segoe UI", 10),
            bg=self.card_bg,
            fg=self.text_secondary,
            justify=tk.LEFT,
            wraplength=420
        ).pack(fill=tk.X, pady=(0, 20))
        
        # Features list
        features_container = tk.Frame(content, bg=self.card_bg)
        features_container.pack(fill=tk.X, pady=(0, 20))
        
        for feature in features:
            feature_row = tk.Frame(features_container, bg=self.card_bg)
            feature_row.pack(fill=tk.X, pady=4)
            
            tk.Label(
                feature_row,
                text="▸",
                font=("Segoe UI", 12, "bold"),
                bg=self.card_bg,
                fg=accent_color
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(
                feature_row,
                text=feature,
                font=("Segoe UI", 10),
                bg=self.card_bg,
                fg=self.text_secondary
            ).pack(side=tk.LEFT)
        
        # Requirements
        req_frame = tk.Frame(content, bg=self.bg_secondary)
        req_frame.pack(fill=tk.X, pady=(10, 20))
        
        tk.Label(
            req_frame,
            text=requirements,
            font=("Segoe UI", 9),
            bg=self.bg_secondary,
            fg=self.text_muted
        ).pack(padx=12, pady=8)
        
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
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            bd=0
        )
        btn.pack(fill=tk.X, ipady=12)
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=self._lighten_color(accent_color))
            card.config(bg=self.card_hover, highlightbackground=accent_color)
            content.config(bg=self.card_hover)
            header.config(bg=self.card_hover)
            title_section.config(bg=self.card_hover)
            features_container.config(bg=self.card_hover)
            for child in features_container.winfo_children():
                child.config(bg=self.card_hover)
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.config(bg=self.card_hover)
        
        def on_leave(e):
            btn.config(bg=accent_color)
            card.config(bg=self.card_bg, highlightbackground=self.border_dark)
            content.config(bg=self.card_bg)
            header.config(bg=self.card_bg)
            title_section.config(bg=self.card_bg)
            features_container.config(bg=self.card_bg)
            for child in features_container.winfo_children():
                child.config(bg=self.card_bg)
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.config(bg=self.card_bg)
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
    
    def _lighten_color(self, hex_color):
        """Lighten a hex color"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(min(255, int(c * 1.2)) for c in rgb)
        return f"#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}"
    
    def _build_status_section(self, parent):
        """Status bar section"""
        status_container = tk.Frame(parent, bg=self.card_bg, bd=0)
        status_container.pack(fill=tk.X, pady=(35, 0))
        
        # Border
        tk.Frame(status_container, bg=self.border_dark, height=1).pack(fill=tk.X, side=tk.TOP)
        
        inner = tk.Frame(status_container, bg=self.card_bg)
        inner.pack(fill=tk.X, padx=30, pady=20)
        
        # Status indicator
        indicator_frame = tk.Frame(inner, bg=self.card_bg)
        indicator_frame.pack(side=tk.LEFT)
        
        self.status_dot = tk.Label(
            indicator_frame,
            text="●",
            font=("Segoe UI", 16),
            bg=self.card_bg,
            fg=self.accent_green
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            indicator_frame,
            text="System Status:",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.text_primary
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.status = tk.Label(
            indicator_frame,
            text="Ready to launch",
            font=("Segoe UI", 10),
            bg=self.card_bg,
            fg=self.text_secondary
        )
        self.status.pack(side=tk.LEFT)
    
    def _build_footer(self, parent):
        """Footer section"""
        footer = tk.Frame(parent, bg=self.bg_dark)
        footer.pack(fill=tk.X, pady=(35, 20))
        
        # Separator line
        tk.Frame(footer, bg=self.border_subtle, height=1).pack(fill=tk.X, pady=(0, 25))
        
        # Info text
        tk.Label(
            footer,
            text="💡 Make sure your webcam and microphone are properly connected before launching modules",
            font=("Segoe UI", 9),
            bg=self.bg_dark,
            fg=self.text_muted
        ).pack(pady=(0, 10))
        
        tk.Label(
            footer,
            text="Jarvis v1.0  •  Multimodal AI Control System  •  Built for seamless interaction",
            font=("Segoe UI", 9),
            bg=self.bg_dark,
            fg=self.text_muted
        ).pack()
    
    # ---------- Actions (UNCHANGED) ----------
    def launch_emotion(self):
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
            self._set_status("Emotion & Gesture Control active", "#3fb950")
            
            # Close the launcher after successful module launch
            self.root.after(500, self.root.destroy)
        except Exception as e:
            self._set_status("Failed to launch Emotion module", "#f85149")
            messagebox.showerror("Launch Error", f"Error: {str(e)}")

    def launch_speech(self):
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
            self._set_status("Voice Command Control active", "#3fb950")
            
            # Close the launcher after successful module launch
            self.root.after(500, self.root.destroy)
        except Exception as e:
            self._set_status("Failed to launch Speech module", "#f85149")
            messagebox.showerror("Launch Error", f"Error: {str(e)}")

    # ---------- Helpers ----------
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