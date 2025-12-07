import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import json
import sqlite3
import speech_recognition as sr
import pyttsx3
import subprocess
import platform
import webbrowser
import time
from datetime import datetime
import os
import socket
import sys
from pathlib import Path

# Import theme configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from launcher import theme_config

# Import AI personality module
from ai_personality import AIPersonality

# Hand-gesture stack
import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# PIL for embedding webcam frames in Tk
from PIL import Image, ImageTk


# =========================
#   Modern, Responsive UI
# =========================
class ModernDarkSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 AI Speech + 🖐️ Hand Gesture Mouse Control")

        # DPI awareness (Windows) + Tk scaling
        try:
            if platform.system() == "Windows":
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            self.root.tk.call("tk", "scaling", 1.15)
        except Exception:
            pass

        # Theme configuration
        self.current_theme = theme_config.get_current_theme()
        self.colors = theme_config.get_theme_colors()

        # App state
        self.current_tab = "control"
        self.wake_word_active = False
        self.continuous_listening = False
        self.is_processing = False

        # Status vars
        self.status_var = tk.StringVar(value="Initializing…")
        self.current_command_var = tk.StringVar(value="Starting system…")
        self.wake_word_status_var = tk.StringVar(value="🟡 Initializing…")
        self.gesture_status_var = tk.StringVar(value="🟥 Gesture: OFF")

        # refs set later
        self.logs_text = None
        self.history_tree = None
        self.commands_tree = None
        self.gesture_video_label = None
        self._gesture_ui_after = None
        self._last_gesture_image = None

        # Back-end components
        self.setup_components()

        # UI
        self._setup_styles()
        self._build_layout()

        # geometry
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = int(sw * 0.85), int(sh * 0.85)
        x, y = (sw - ww) // 2, (sh - wh) // 2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        self.root.minsize(1200, 800)

        # responsive wraplength updates
        self.root.bind("<Configure>", self._on_resize)

        # auto-start listening
        self.root.after(1200, self.auto_start_voice_control)

    # ------------------------
    # Setup / Styles
    # ------------------------
    def setup_components(self):
        try:
            self.db_manager = DatabaseManager()
            self.speech_engine = EnhancedSpeechEngine()
            self.command_processor = EnhancedCommandProcessor()
            self.system_controller = EnhancedSystemController()
            self.ai_personality = AIPersonality()  # Add AI personality
            
            # Track last opened context (for context-aware search)
            self.last_opened_context = None

            # Gesture controller with UI callbacks and frame queue for embedded preview
            self.gesture_controller = HandGestureController(
                on_started=lambda: self._gesture_ui(True),
                on_stopped=lambda: self._gesture_ui(False),
                on_error=lambda msg: self.safe_log_message(f"🛑 Gesture error: {msg}")
            )

            self.settings = {
                "confidence_threshold": 0.7,
                "voice_feedback": True,
                "auto_execute": True,
                "wake_word_enabled": True,
                "wake_word": "nova",
                "wake_word_sensitivity": 0.6,
                "command_timeout": 5,
                # camera preferences
                "camera_index": 0,
                "camera_width": 640,
                "camera_height": 480,
            }
            self.load_settings()
        except Exception as e:
            print(f"Error initializing components: {e}")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        # Frame styles
        style.configure("Dark.TFrame", background=self.colors["bg_secondary"])
        style.configure("Surface.TFrame", background=self.colors["bg_secondary"])
        style.configure("Canvas.TFrame", background=self.colors["bg_tertiary"])
        # Label styles
        style.configure("Dark.TLabel", background=self.colors["bg_secondary"], foreground=self.colors["text_primary"], font=("Segoe UI", 10))
        style.configure("Primary.TLabel", background=self.colors["bg_secondary"], foreground=self.colors["text_primary"])
        style.configure("Muted.TLabel", background=self.colors["bg_secondary"], foreground=self.colors["text_secondary"])
        style.configure("Title.TLabel", background=self.colors["bg_secondary"], foreground=self.colors["text_primary"], font=("Segoe UI", 18, "bold"))
        # Button styles
        style.configure("Dark.TButton", background=self.colors["bg_hover"], foreground=self.colors["text_primary"], font=("Segoe UI", 9), padding=8)
        style.map("Dark.TButton", background=[("active", "#444444"), ("pressed", "#555555")])
        style.configure("Gesture.TButton", background=self.colors["accent_secondary"], foreground=self.colors["text_primary"], font=("Segoe UI", 9), padding=8)
        style.map("Gesture.TButton", background=[("active", "#3a5a8c"), ("pressed", "#4a6a9c")])
        # Treeview styles
        style.configure("Dark.Treeview",
                        background=self.colors["bg_tertiary"],
                        fieldbackground=self.colors["bg_tertiary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1, relief="solid", rowheight=28)
        style.configure("Dark.Treeview.Heading",
                        background=self.colors["bg_secondary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1, relief="solid", font=("Segoe UI", 11, "bold"))
        # Notebook styles
        style.configure("TNotebook", background=self.colors["bg_secondary"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg_tertiary"], foreground=self.colors["text_primary"], padding=(14, 8))
        style.map("TNotebook.Tab", background=[("selected", self.colors["bg_hover"])])
        # Scrollbar styles
        style.configure("Dark.Vertical.TScrollbar",
                        background=self.colors["bg_secondary"],
                        troughcolor=self.colors["bg_tertiary"],
                        arrowcolor=self.colors["text_secondary"])
        self.root.configure(bg=self.colors["bg_primary"])

    # ------------------------
    # Layout
    # ------------------------
    def _build_layout(self):
        # Main container (matching emotion module pattern)
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Store reference to main container
        self.main_container = main_container

        # Header
        header = tk.Frame(main_container, bg=self.colors["bg_secondary"], bd=0, relief=tk.FLAT, height=90)
        header.grid(row=0, column=0, sticky="nsew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=0)

        title = ttk.Label(header,
                         text="🎤 AI Speech Assistant + 🖐️ Hand Gesture Mouse Control",
                         style='Title.TLabel')
        subtitle = ttk.Label(header,
                            text="Say 'Nova' to activate • Use the button or voice to control the virtual mouse",
                            style='Dark.TLabel',
                            font=("Segoe UI", 10))
        title.grid(row=0, column=0, sticky="w", padx=0, pady=(0, 5))
        subtitle.grid(row=1, column=0, sticky="w", padx=0, pady=(0, 0))

        # Back to Dashboard button
        dashboard_btn = ttk.Button(
            header,
            text="🏠 Back to Dashboard",
            style='Gesture.TButton',
            command=self.back_to_dashboard
        )
        dashboard_btn.grid(row=0, column=2, sticky="e", padx=0, pady=0)
        
        status_card = tk.Frame(header, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        status_card.grid(row=0, column=1, rowspan=2, sticky="nse", padx=(15, 15), pady=0)
        tk.Label(status_card, text="System Status", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).pack(padx=12, pady=(10, 6))
        self.wake_status_label = tk.Label(status_card, textvariable=self.wake_word_status_var,
                                          font=("Segoe UI", 10),
                                          bg=self.colors["bg_tertiary"], fg=self.colors["accent_warning"])
        self.wake_status_label.pack(padx=12, pady=(0, 5))
        self.gesture_status_label = tk.Label(status_card, textvariable=self.gesture_status_var,
                                             font=("Segoe UI", 10),
                                             bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"])
        self.gesture_status_label.pack(padx=12, pady=(0, 10))

        # Paned split
        paned = ttk.Panedwindow(main_container, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=0, pady=(15, 0))

        # Sidebar
        self.sidebar = ttk.Frame(paned, style='Dark.TFrame')
        paned.add(self.sidebar, weight=1)

        # Main
        self.main = ttk.Frame(paned, style='Dark.TFrame')
        paned.add(self.main, weight=3)

        # Sidebar content
        self.sidebar.grid_rowconfigure(3, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        ttk.Label(self.sidebar, text="🎙️ Voice Control Center",
                 style='Title.TLabel').grid(
            row=0, column=0, sticky="w", padx=15, pady=(0, 15)
        )

        # Control card
        control_card = tk.Frame(self.sidebar, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        control_card.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        control_card.grid_columnconfigure(0, weight=1)
        tk.Label(control_card, text="🎯 Voice Control System", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self.system_indicator = tk.Label(control_card, text="🟡 AUTO-STARTING", font=("Segoe UI", 11),
                                         bg=self.colors["bg_tertiary"], fg=self.colors["accent_warning"])
        self.system_indicator.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        btns = tk.Frame(control_card, bg=self.colors["bg_tertiary"])
        btns.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))
        for i in range(4):
            btns.grid_columnconfigure(i, weight=1)

        self.system_toggle_btn = tk.Button(
            btns, text="🔴 Stop Voice", font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent_danger"], fg="white", activebackground="#b62b29",
            relief=tk.FLAT, bd=0, height=2, cursor="hand2",
            command=self.toggle_voice_system)
        self.system_toggle_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.manual_btn = tk.Button(
            btns, text="🎤 Manual", font=("Segoe UI", 9, "bold"),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"], activebackground="#444444",
            relief=tk.FLAT, bd=0, height=2, cursor="hand2",
            command=self.manual_listen)
        self.manual_btn.grid(row=0, column=1, sticky="ew", padx=5)

        self.stop_listening_btn = tk.Button(
            btns, text="⏹️ Stop", font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent_warning"], fg="white", activebackground=self.colors["accent_danger"],
            relief=tk.FLAT, bd=0, height=2, cursor="hand2",
            command=self.stop_continuous_listening, state="disabled")
        self.stop_listening_btn.grid(row=0, column=2, sticky="ew", padx=5)

        # Hand Gesture toggle button
        self.gesture_toggle_btn = tk.Button(
            btns, text="🖐️ Gesture: OFF", font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent_secondary"], fg=self.colors["text_primary"], activebackground="#3a5a8c",
            relief=tk.FLAT, bd=0, height=2, cursor="hand2",
            command=self.toggle_gesture)
        self.gesture_toggle_btn.grid(row=0, column=3, sticky="ew", padx=(5, 0))

        # Status card
        status_card2 = tk.Frame(self.sidebar, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        status_card2.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        status_card2.grid_columnconfigure(0, weight=1)
        tk.Label(status_card2, text="📊 Current Status", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        status_box = tk.Frame(status_card2, bg=self.colors["bg_hover"], bd=0, relief=tk.FLAT)
        status_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        status_box.grid_columnconfigure(0, weight=1)
        tk.Label(status_box, textvariable=self.status_var,
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["accent_primary"]).grid(row=0, column=0, sticky="w", padx=10, pady=8)

        cmd_box = tk.Frame(status_card2, bg=self.colors["bg_hover"], bd=0, relief=tk.FLAT)
        cmd_box.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))
        cmd_box.grid_columnconfigure(0, weight=1)
        self.command_label = tk.Label(cmd_box, textvariable=self.current_command_var,
                                      font=("Segoe UI", 9), wraplength=360,
                                      bg=self.colors["bg_hover"], fg=self.colors["text_primary"], justify="left")
        self.command_label.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        # Quick Commands
        qc_card = tk.Frame(self.sidebar, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        qc_card.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 0))
        qc_card.grid_rowconfigure(2, weight=1)
        qc_card.grid_columnconfigure(0, weight=1)
        tk.Label(qc_card, text="⚡ Quick Test Commands", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))
        tk.Label(qc_card, text="Speak after activation (or click to simulate):", font=("Segoe UI", 9, "italic"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_secondary"]).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
        canvas = tk.Canvas(qc_card, bg=self.colors["bg_tertiary"], highlightthickness=0)
        vs = ttk.Scrollbar(qc_card, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
        self.qc_frame = tk.Frame(canvas, bg=self.colors["bg_tertiary"])
        self.qc_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.qc_frame, anchor="nw")
        canvas.configure(yscrollcommand=vs.set)
        canvas.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=(0, 12))
        vs.grid(row=2, column=1, sticky="ns", padx=(0, 10), pady=(0, 12))
        self._populate_quick_commands(self.qc_frame)

        # Main: tabs
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)
        ttk.Label(self.main, text="Control & Monitoring", style='Title.TLabel').grid(row=0, column=0, sticky="w", padx=15, pady=(0, 15))

        self.notebook = ttk.Notebook(self.main)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))

        self.tab_control = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.tab_commands = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.tab_history = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.tab_settings = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.tab_logs = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.tab_gesture = ttk.Frame(self.notebook, style='Dark.TFrame')

        self.notebook.add(self.tab_control, text="🎛️ Control")
        self.notebook.add(self.tab_commands, text="📋 Commands")
        self.notebook.add(self.tab_history, text="📊 History")
        self.notebook.add(self.tab_settings, text="⚙️ Settings")
        self.notebook.add(self.tab_logs, text="📝 Logs")
        self.notebook.add(self.tab_gesture, text="🖐️ Virtual Mouse")  

        self._build_tab_control()
        self._build_tab_commands()
        self._build_tab_history()
        self._build_tab_settings()
        self._build_tab_logs()
        self._build_tab_gesture()  

        # Footer
        footer = tk.Frame(main_container, bg=self.colors["bg_secondary"], bd=0, relief=tk.FLAT, height=40)
        footer.grid(row=2, column=0, sticky="nsew")
        footer.grid_propagate(False)
        self.status_bar_var = tk.StringVar(value="Auto-starting voice control system…")
        tk.Label(footer, textvariable=self.status_bar_var,
                 bg=self.colors["bg_secondary"], fg=self.colors["text_primary"], font=("Segoe UI", 9)).pack(side="left", padx=0)
        tk.Label(footer, text="v6.2 — Voice + Embedded Gesture", bg=self.colors["bg_secondary"],
                 fg=self.colors["text_muted"], font=("Segoe UI", 9)).pack(side="right", padx=0)

    def _populate_quick_commands(self, parent):
        commands = [
            ("🌐 Open Chrome", "open chrome"),
            ("🦊 Open Firefox", "open firefox"),
            ("📝 Open Notepad", "open notepad"),
            ("🔢 Open Calculator", "open calculator"),
            ("📁 File Explorer", "open explorer"),
            ("📥 Open Downloads", "open downloads"),
            ("📄 Open Documents", "open documents"),
            ("🖼️ Open Pictures", "open pictures"),
            ("🔍 Search Python", "search for python tutorials"),
            ("🔊 Volume Up", "volume up"),
            ("🔇 Volume Down", "volume down"),
            ("🔒 Lock Computer", "lock computer"),
            ("📧 Open Gmail", "open gmail"),
            ("🎵 Open Spotify", "open spotify"),
            ("📷 Screenshot", "take screenshot"),
            ("⚙️ Settings", "open settings"),
            ("🌡️ Weather", "check weather"),
            ("📰 News", "check news"),
            ("⏰ Time", "what time is it"),
            ("📅 Date", "what date is it"),
            ("📺 YouTube", "open youtube"),
            ("🗂️ Show Desktop", "show desktop"),
            ("📉 Minimize All", "minimize all"),
            ("🎮 Task Manager", "task manager"),
            # UPDATED quick commands
            ("🖐️ Enable Mouse", "enable mouse"),
            ("🖐️ Disable Mouse", "disable mouse"),
        ]
        for text, cmd in commands:
            b = tk.Button(parent, text=text, anchor="w",
                          font=("Segoe UI", 9),
                          bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                          activebackground="#444444", activeforeground="white",
                          relief=tk.FLAT, bd=0, padx=10, pady=8,
                          command=lambda c=cmd: self.test_command(c), cursor="hand2")
            b.pack(fill="x", padx=6, pady=3)

    # ------------------------
    # Tabs
    # ------------------------
    def _build_tab_control(self):
        f = self.tab_control
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.instructions_label = tk.Label(
            card,
            text=("How to Use:\n"
                  "1) System listens for wake word automatically.\n"
                  "2) Say 'Nova' to enable continuous mode.\n"
                  "3) Speak commands directly (e.g., 'open Chrome', 'volume up').\n"
                  "4) Use the button or voice commands to start the Virtual Mouse.\n"
                  "   • In the '🖐️ Virtual Mouse' tab: live camera is embedded.\n"
                  "   • Raise all five fingers to toggle gesture tracking ON/OFF.\n"
                  "   • Thumb+Index short hold = left click; long hold = drag.\n"
                  "   • Index+Pinky (rock sign) = right click.\n"
                  "   • Index+Middle+Ring (no pinky) = scroll."),
            justify="left", anchor="w",
            font=("Segoe UI", 9),
            bg=self.colors["bg_tertiary"], fg=self.colors["text_secondary"], padx=15, pady=15
        )
        self.instructions_label.pack(fill="x")

        card2 = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card2.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        card2.grid_rowconfigure(1, weight=1)
        card2.grid_columnconfigure(0, weight=1)
        tk.Label(card2, text="📈 Recent Activity", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))
        self.activity_scroll = scrolledtext.ScrolledText(
            card2, font=("Consolas", 9),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            selectbackground=self.colors["accent_secondary"],
            relief=tk.FLAT, bd=0
        )
        self.activity_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
        self.load_recent_activity(self.activity_scroll)

    def _build_tab_commands(self):
        f = self.tab_commands
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        ttk.Label(f, text="📋 Available Voice Commands", style='Title.TLabel').grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        columns = ("Command", "Pattern", "Type", "Status")
        self.commands_tree = ttk.Treeview(card, columns=columns, show="headings", style="Dark.Treeview")
        for col in columns:
            self.commands_tree.heading(col, text=col)
            self.commands_tree.column(col, width=180, anchor="w")
        vs = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.commands_tree.yview, style="Dark.Vertical.TScrollbar")
        self.commands_tree.configure(yscrollcommand=vs.set)
        self.commands_tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        vs.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        self.load_commands()

    def _build_tab_history(self):
        f = self.tab_history
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        header = ttk.Frame(f, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        ttk.Label(header, text="📊 Command History", style='Title.TLabel').pack(side="left")
        refresh_btn = tk.Button(header, text="🔄 Refresh", font=("Segoe UI", 9),
                  bg=self.colors["accent_secondary"], fg="white",
                  activebackground="#3a5a8c", bd=0, relief=tk.FLAT,
                  command=self.load_history, cursor="hand2", padx=12, pady=6)
        refresh_btn.pack(side="right")
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        columns = ("Time", "Command", "Status", "Confidence")
        self.history_tree = ttk.Treeview(card, columns=columns, show="headings", style="Dark.Treeview")
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=200, anchor="w")
        vs = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.history_tree.yview, style="Dark.Vertical.TScrollbar")
        self.history_tree.configure(yscrollcommand=vs.set)
        self.history_tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        vs.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        self.load_history()

    def _build_tab_settings(self):
        f = self.tab_settings
        f.grid_columnconfigure(1, weight=1)
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=15)
        card.grid_columnconfigure(1, weight=1)

        tk.Label(card, text="🎤 Speech Recognition Settings", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 12))

        tk.Label(card, text="Confidence Threshold", font=("Segoe UI", 10),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=1, column=0, sticky="w", padx=12, pady=(8, 4))
        self.confidence_var = tk.DoubleVar(value=self.settings["confidence_threshold"])
        conf_scale = tk.Scale(card, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                              variable=self.confidence_var, length=360,
                              bg=self.colors["bg_tertiary"], troughcolor=self.colors["bg_hover"],
                              fg=self.colors["text_primary"], highlightthickness=0)
        conf_scale.grid(row=1, column=1, sticky="w", padx=12, pady=(8, 4))

        # camera settings
        tk.Label(card, text="📷 Camera Index", font=("Segoe UI", 10),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=2, column=0, sticky="w", padx=12, pady=(8, 4))
        self.camera_index_var = tk.IntVar(value=int(self.settings.get("camera_index", 0)))
        tk.Spinbox(card, from_=0, to=10, textvariable=self.camera_index_var, width=6,
                   font=("Segoe UI", 10), bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                   insertbackground=self.colors["text_primary"]).grid(row=2, column=1, sticky="w", padx=12, pady=(8, 4))

        tk.Label(card, text="Resolution (WxH)", font=("Segoe UI", 10),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=3, column=0, sticky="w", padx=12, pady=(8, 4))
        self.camera_w_var = tk.IntVar(value=int(self.settings.get("camera_width", 640)))
        self.camera_h_var = tk.IntVar(value=int(self.settings.get("camera_height", 480)))
        res_frame = tk.Frame(card, bg=self.colors["bg_tertiary"])
        res_frame.grid(row=3, column=1, sticky="w", padx=12, pady=(8, 4))
        tk.Entry(res_frame, textvariable=self.camera_w_var, width=8,
                 font=("Segoe UI", 10), bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 insertbackground=self.colors["text_primary"]).pack(side="left")
        tk.Label(res_frame, text=" x ", font=("Segoe UI", 10),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).pack(side="left")
        tk.Entry(res_frame, textvariable=self.camera_h_var, width=8,
                 font=("Segoe UI", 10), bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 insertbackground=self.colors["text_primary"]).pack(side="left")

        # Wake word setting
        tk.Label(card, text="Wake Word", font=("Segoe UI", 10),
                 bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"]).grid(row=4, column=0, sticky="w", padx=12, pady=(8, 4))
        self.wake_word_var = tk.StringVar(value=self.settings.get("wake_word", "nova"))
        self.wake_word_entry = tk.Entry(card, textvariable=self.wake_word_var, width=20,
                                        font=("Segoe UI", 10), bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                                        insertbackground=self.colors["text_primary"])
        self.wake_word_entry.grid(row=4, column=1, sticky="w", padx=12, pady=(8, 4))

        self.voice_feedback_var = tk.BooleanVar(value=self.settings["voice_feedback"])
        tk.Checkbutton(card, text="Enable Voice Feedback", variable=self.voice_feedback_var,
                       bg=self.colors["bg_tertiary"], fg=self.colors["text_primary"],
                       selectcolor=self.colors["bg_hover"], activebackground=self.colors["bg_tertiary"]).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 8)
        )

        tk.Button(card, text="💾 Save Settings", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent_primary"], fg="white",
                  activebackground="#1b6d2e", bd=0, relief=tk.FLAT, padx=16, pady=10,
                  cursor="hand2", command=self.save_settings).grid(row=6, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))

    def _build_tab_logs(self):
        f = self.tab_logs
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        header = ttk.Frame(f, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        ttk.Label(header, text="📝 System Logs", style='Title.TLabel').pack(side="left")
        clear_btn = tk.Button(header, text="🗑️ Clear Logs", font=("Segoe UI", 9),
                  bg=self.colors["accent_danger"], fg="white",
                  activebackground="#b12a27", bd=0, relief=tk.FLAT,
                  command=self.clear_logs, cursor="hand2", padx=12, pady=6)
        clear_btn.pack(side="right")
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.logs_text = scrolledtext.ScrolledText(
            card, font=("Consolas", 9),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            selectbackground=self.colors["accent_secondary"],
            relief=tk.FLAT, bd=0
        )
        self.logs_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.safe_log_message("System initialized successfully")
        self.safe_log_message("Speech recognition engine ready")
        self.safe_log_message("Command processor online")
        self.safe_log_message("Database connection established")

    def _build_tab_gesture(self):
        """Embedded Virtual Mouse view."""
        f = self.tab_gesture
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(f, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        ttk.Label(header, text="🖐️ Virtual Mouse — Live", style='Title.TLabel').pack(side="left")

        # Video container
        card = tk.Frame(f, bg=self.colors["bg_tertiary"], bd=1, relief=tk.SOLID)
        card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self.gesture_video_label = tk.Label(card, bg=self.colors["bg_tertiary"])
        self.gesture_video_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Info footer
        info = tk.Label(f, text=("Raise all five fingers to toggle gesture tracking ON/OFF • "
                                 "Thumb+Index short hold=LeftClick / long=Drag • "
                                 "Index+Pinky=RightClick • Index+Middle+Ring=Scroll"),
                        bg=self.colors["bg_secondary"], fg=self.colors["text_secondary"], font=("Segoe UI", 9))
        info.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

    # ------------------------
    # Responsiveness helpers
    # ------------------------
    def _on_resize(self, event):
        try:
            if hasattr(self, "command_label") and self.command_label.winfo_exists():
                w = max(self.command_label.winfo_width() - 24, 240)
                self.command_label.configure(wraplength=w)
            if hasattr(self, "instructions_label") and self.instructions_label.winfo_exists():
                w2 = max(self.instructions_label.winfo_width() - 24, 480)
                self.instructions_label.configure(wraplength=w2)
        except Exception:
            pass

    # ------------------------
    # Voice control
    # ------------------------
    def auto_start_voice_control(self):
        try:
            self.safe_log_message("🚀 Auto-starting voice control system…")
            self.start_voice_control()
        except Exception as e:
            self.safe_log_message(f"❌ Error auto-starting: {e}")

    def toggle_voice_system(self):
        if self.wake_word_active:
            self.stop_voice_control()
        else:
            self.start_voice_control()

    def start_voice_control(self):
        self.wake_word_active = True
        self.system_toggle_btn.config(text="🔴 Stop Voice", bg=self.colors["accent_danger"])
        self.update_system_status("🟡 WAITING FOR WAKE WORD", self.colors["accent_warning"])
        self.status_var.set("Listening for Wake Word")
        self.current_command_var.set(f"Say '{self.settings['wake_word'].upper()}' to activate continuous listening…")
        self.status_bar_var.set(f"🎯 Say '{self.settings['wake_word'].upper()}' to activate")
        self.wake_word_thread = threading.Thread(target=self.wake_word_worker, daemon=True)
        self.wake_word_thread.start()
        self.safe_log_message("🟢 System started — listening for wake word")

    def stop_voice_control(self):
        self.wake_word_active = False
        self.continuous_listening = False
        self.system_toggle_btn.config(text="🟢 Start Voice", bg=self.colors["accent_primary"])
        self.stop_listening_btn.config(state="disabled")
        self.update_system_status("🔴 INACTIVE", self.colors["accent_danger"])
        self.status_var.set("Stopped")
        self.current_command_var.set("Click 'Start Voice' to begin")
        self.status_bar_var.set("Voice control system stopped")
        self.safe_log_message("🔴 System stopped")

    def wake_word_worker(self):
        self.safe_log_message(f"👂 Listening for wake word: '{self.settings['wake_word'].upper()}'...")
        consecutive_errors = 0
        
        while self.wake_word_active and not self.continuous_listening:
            try:
                result = self.speech_engine.listen_for_wake_word(self.settings["wake_word"], timeout=3)
                if result:
                    text, confidence = result
                    self.safe_log_message(f"🎯 Wake word detected: '{text}' (confidence: {confidence:.2f})")
                    if confidence >= self.settings["wake_word_sensitivity"]:
                        self.activate_continuous_listening()
                        break
                    else:
                        self.safe_log_message(f"⚠️ Wake word confidence too low: {confidence:.2f} < {self.settings['wake_word_sensitivity']}")
                
                consecutive_errors = 0  # Reset error counter on success
                time.sleep(0.05)  # Reduced sleep for faster response
            except Exception as e:
                consecutive_errors += 1
                self.safe_log_message(f"❌ Wake word error ({consecutive_errors}): {e}")
                if consecutive_errors >= 5:
                    self.safe_log_message("⚠️ Too many errors. Restarting wake word detection...")
                    consecutive_errors = 0
                    time.sleep(2)
                else:
                    time.sleep(0.5)

    def activate_continuous_listening(self):
        self.continuous_listening = True
        self.stop_listening_btn.config(state="normal")
        self.update_system_status("🟢 CONTINUOUS LISTENING", self.colors["accent_primary"])
        self.status_var.set("Continuous Listening Active")
        self.current_command_var.set("Listening continuously for commands…")
        self.status_bar_var.set("🎤 Continuous listening active — Speak commands directly")
        if self.settings["voice_feedback"]:
            threading.Thread(target=lambda: self.speech_engine.speak("Yes? Continuous listening activated."), daemon=True).start()
        threading.Thread(target=self.continuous_listening_worker, daemon=True).start()
        self.safe_log_message("🟢 Continuous listening activated")

    def continuous_listening_worker(self):
        while self.continuous_listening and self.wake_word_active:
            try:
                if not self.is_processing:
                    result = self.speech_engine.listen_for_command(timeout=self.settings["command_timeout"])
                    if result:
                        text, confidence = result
                        self.safe_log_message(f"🎤 Command: '{text}' (conf: {confidence:.2f})")
                        if confidence >= self.settings["confidence_threshold"]:
                            self.process_command(text, confidence)
                        else:
                            self.safe_log_message(f"⚠️ Low confidence: {confidence:.2f}")
                time.sleep(0.2)
            except Exception as e:
                self.safe_log_message(f"❌ Listening error: {e}")
                time.sleep(1)
        self.safe_log_message("🔴 Continuous listening stopped")

    def stop_continuous_listening(self):
        self.continuous_listening = False
        self.stop_listening_btn.config(state="disabled")
        if self.wake_word_active:
            self.update_system_status("🟡 WAITING FOR WAKE WORD", self.colors["accent_warning"])
            self.status_var.set("Listening for Wake Word")
            self.current_command_var.set(f"Say '{self.settings['wake_word'].upper()}' to activate…")
            self.status_bar_var.set(f"🎯 Say '{self.settings['wake_word'].upper()}' to activate")
            self.wake_word_thread = threading.Thread(target=self.wake_word_worker, daemon=True)
            self.wake_word_thread.start()
            self.safe_log_message("🟡 Returned to wake word mode")

    def manual_listen(self):
        if not self.is_processing:
            self.safe_log_message("🎤 Manual listening…")
            self.current_command_var.set("Manual mode — Speak your command now…")
            self.status_bar_var.set("🎤 Manual listening — Speak your command")
            threading.Thread(target=self.manual_listening_worker, daemon=True).start()

    def manual_listening_worker(self):
        try:
            self.is_processing = True
            result = self.speech_engine.listen_for_command(timeout=10)
            if result:
                text, confidence = result
                self.safe_log_message(f"🎤 Manual: '{text}' (conf: {confidence:.2f})")
                if confidence >= self.settings["confidence_threshold"]:
                    self.process_command(text, confidence)
                else:
                    self.safe_log_message(f"⚠️ Low confidence: {confidence:.2f}")
                    if self.settings["voice_feedback"]:
                        threading.Thread(target=lambda: self.speech_engine.speak("Sorry, I didn't catch that clearly."), daemon=True).start()
            else:
                self.safe_log_message("⏰ Manual listening timeout")
        except Exception as e:
            self.safe_log_message(f"❌ Manual error: {e}")
        finally:
            self.is_processing = False
            if self.continuous_listening:
                self.current_command_var.set("Listening continuously for commands…")
                self.status_bar_var.set("🎤 Continuous listening active — Speak commands directly")
            elif self.wake_word_active:
                self.current_command_var.set(f"Say '{self.settings['wake_word'].upper()}' to activate…")
                self.status_bar_var.set(f"🎯 Say '{self.settings['wake_word'].upper()}' to activate")
            else:
                self.current_command_var.set("Click 'Start Voice' or use 'Manual'")
                self.status_bar_var.set("System inactive — Use controls to interact")

    def process_command(self, text, confidence):
        try:
            self.is_processing = True
            self.current_command_var.set(f"Processing: '{text}'")
            self.status_bar_var.set(f"🧠 Processing: {text}")
            history_id = self.db_manager.add_command_history(text, confidence)
            command_result = self.command_processor.process_command(text)
            
            # Handle conversational commands with AI personality
            if command_result["action"] == "conversation":
                conv_type = command_result["parameters"].get("type", "")
                response, emotion = self.ai_personality.get_greeting_response(conv_type)
                self.safe_log_message(f"💬 {text} → {response}")
                if self.settings["voice_feedback"]:
                    threading.Thread(target=lambda: self.speech_engine.speak(response, emotion), daemon=True).start()
                self.db_manager.update_command_status(history_id, "success")
                return
            
            if command_result["action"] != "unknown":
                success = self.execute_command(command_result)
                status = "success" if success else "failed"
                self.db_manager.update_command_status(history_id, status)
                
                # Generate friendly AI response
                if self.settings["voice_feedback"]:
                    action_type = command_result["action"]
                    action_data = self._get_action_description(command_result)
                    response, emotion = self.ai_personality.get_action_response(action_type, action_data, success)
                    threading.Thread(target=lambda: self.speech_engine.speak(response, emotion), daemon=True).start()
                
                self.safe_log_message(f"✅ {text} — {status}")
            else:
                self.db_manager.update_command_status(history_id, "unknown")
                if self.settings["voice_feedback"]:
                    response, emotion = self.ai_personality.get_unknown_command_response()
                    threading.Thread(target=lambda: self.speech_engine.speak(response, emotion), daemon=True).start()
                self.safe_log_message(f"❌ Unknown command: {text}")
        except Exception as e:
            self.safe_log_message(f"❌ Processing error: {e}")
        finally:
            self.is_processing = False
            if self.notebook.index(self.notebook.select()) == 2 and self.history_tree:
                self.load_history()
    
    def _get_action_description(self, command_result):
        """Extract action description for friendly responses"""
        action = command_result["action"]
        params = command_result["parameters"]
        
        if action == "application":
            if params.get("close"):
                return "application_close"
            return params.get("app", "application")
        elif action == "system":
            sys_action = params.get("action", "")
            if sys_action == "volume":
                direction = params.get("direction", "up")
                return f"volume_{direction}"
            elif sys_action == "brightnesscontrol":
                direction = params.get("direction", "up")
                return f"brightness_{direction}"
            return sys_action
        elif action == "gesture":
            state = params.get("state", "toggle")
            if state == "on":
                return "gesture_enabled"
            elif state == "off":
                return "gesture_disabled"
        elif action == "file":
            file_action = params.get("action", "")
            if "folder" in file_action:
                return "folder_created" if "create" in file_action else "folder_opened"
            return "file_created"
        elif action == "window":
            return params.get("action", "window")
        elif action == "scroll":
            return "scroll"
        elif action == "typing":
            return "typing"
        elif action == "selection":
            return "selection"
        elif action == "navigation":
            direction = params.get("direction", "")
            return f"arrow_{direction}" if direction else "navigation"
        
        return action

    def execute_command(self, command_result):
        try:
            action = command_result["action"]
            params = command_result["parameters"]

            if action == "application":
                if params.get("close"):
                    return self.system_controller.close_application(params.get("app", ""))
                else:
                    # Reset context when opening non-web apps
                    app = params.get("app", "")
                    if app not in ['chrome', 'firefox', 'edge', 'browser']:
                        self.last_opened_context = None
                    return self.system_controller.open_application(app)

            if action == "web":
                # Pass context if available
                context = getattr(self, 'last_opened_context', None)
                return self.system_controller.web_search(params, context)

            if action == "system":
                return self.system_controller.execute_system_command(params)

            if action == "file":
                return self.system_controller.file_operation(params)

            if action == "media":
                return self.system_controller.media_control(params)

            if action == "network":
                return self.system_controller.network_operation(params)

            if action == "utility":
                return self.system_controller.utility_operation(params)

            # hand-gesture mouse controller
            if action == "gesture":
                state = params.get("state")
                if state == "on":
                    return self.start_gesture()
                elif state == "off":
                    return self.stop_gesture()
                else:
                    return self.stop_gesture() if self.gesture_controller.is_running() else self.start_gesture()

            # window management
            if action == "window":
                return self.system_controller.window_operation(params)

            # page scrolling
            if action == "scroll":
                direction = params.get("direction", "down")
                return self.system_controller.scroll_page(direction)

            # typing/dictation
            if action == "typing":
                return self.system_controller.typing_operation(params)

            # text selection
            if action == "selection":
                return self.system_controller.selection_operation(params)

            # arrow key navigation
            if action == "navigation":
                return self.system_controller.navigation_operation(params)

            return False
        except Exception as e:
            self.safe_log_message(f"❌ Execution error: {e}")
            return False

    # ------------------------
    # Gesture button + helpers (embedded)
    # ------------------------
    def toggle_gesture(self):
        if self.gesture_controller.is_running():
            self.stop_gesture()
        else:
            self.start_gesture()

    def start_gesture(self):
        cam_index = int(self.camera_index_var.get()) if hasattr(self, "camera_index_var") else int(self.settings.get("camera_index", 0))
        cam_w = int(self.camera_w_var.get()) if hasattr(self, "camera_w_var") else int(self.settings.get("camera_width", 640))
        cam_h = int(self.camera_h_var.get()) if hasattr(self, "camera_h_var") else int(self.settings.get("camera_height", 480))

        # Provide a frame queue to the controller so it pushes frames back
        ok, err = self.gesture_controller.start(camera_index=cam_index, width=cam_w, height=cam_h, frame_consumer=self._on_gesture_frame)
        if not ok:
            self.safe_log_message(f"🛑 Could not start hand gesture mouse: {err}")
            messagebox.showerror("Camera / Permission Error", f"Could not access the webcam.\n\nDetails:\n{err}\n\nTips:\n• Close other apps using the camera\n• Try a different Camera Index in Settings\n• Allow camera access in OS privacy settings", parent=self.root)
            return False
        self.safe_log_message("🖐️ Hand-gesture mouse: started")
        if self.settings.get("voice_feedback"):
            threading.Thread(target=lambda: self.speech_engine.speak("Hand gesture mouse enabled"), daemon=True).start()
        # Switch to the Gesture tab to show the view
        try:
            idx = self.notebook.tabs().index(self.notebook.select())
        except Exception:
            idx = 0
        for i, tab_id in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab_id, "text").startswith("🖐️"):
                self.notebook.select(i)
                break
        return True

    def stop_gesture(self):
        ok = self.gesture_controller.stop()
        if ok:
            self.safe_log_message("🖐️ Hand-gesture mouse: stopped")
            if self.settings.get("voice_feedback"):
                threading.Thread(target=lambda: self.speech_engine.speak("Hand gesture mouse disabled"), daemon=True).start()
        # stop UI update loop if running
        if self._gesture_ui_after is not None:
            try:
                self.root.after_cancel(self._gesture_ui_after)
            except Exception:
                pass
            self._gesture_ui_after = None
        return ok

    def _gesture_ui(self, running: bool):
        # Update header chip + button style
        if running:
            self.gesture_status_var.set("🟩 Gesture: ON")
            self.gesture_status_label.config(fg=self.colors["accent_primary"])
            self.gesture_toggle_btn.config(text="🖐️ Gesture: ON", bg=self.colors["accent_primary"], fg="white")
        else:
            self.gesture_status_var.set("🟥 Gesture: OFF")
            self.gesture_status_label.config(fg=self.colors["text_primary"])
            self.gesture_toggle_btn.config(text="🖐️ Gesture: OFF", bg=self.colors["bg_hover"], fg=self.colors["text_primary"])

    def _on_gesture_frame(self, frame_bgr):
        """Called (from worker thread) with latest BGR frame. We enqueue UI update on main thread."""
        if self.gesture_video_label is None or not self.gesture_video_label.winfo_exists():
            return

        # Convert BGR -> RGB -> ImageTk and show in label safely on main thread
        def _update():
            # Check if label still exists
            if not self.gesture_video_label.winfo_exists():  # type: ignore
                return
            # Fit label size while preserving AR
            lbl_w = max(self.gesture_video_label.winfo_width(), 320)  # type: ignore
            lbl_h = max(self.gesture_video_label.winfo_height(), 240)  # type: ignore
            # Convert to PIL Image
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            # Use Image.Resampling.LANCZOS for newer PIL versions, fallback to Image.LANCZOS
            try:
                img.thumbnail((lbl_w, lbl_h), Image.Resampling.LANCZOS)
            except AttributeError:
                img.thumbnail((lbl_w, lbl_h), Image.LANCZOS)  # type: ignore
            imgtk = ImageTk.PhotoImage(image=img)
            self.gesture_video_label.configure(image=imgtk)  # type: ignore
            # Keep a reference to avoid garbage collection
            self._last_gesture_image = imgtk

        # throttle UI updates to ~30 FPS using after
        if self._gesture_ui_after is None:
            _update()
            self._gesture_ui_after = self.root.after(33, self._clear_gesture_after_flag)
        # else: we already scheduled a draw; next frame will schedule again

    def _clear_gesture_after_flag(self):
        self._gesture_ui_after = None

    # ------------------------
    # Utilities & DB bindings
    # ------------------------
    def test_command(self, text):
        self.safe_log_message(f"🧪 Testing command: {text}")
        self.process_command(text, 1.0)

    def update_system_status(self, text, color):
        try:
            self.system_indicator.config(text=text, fg=color)
            self.wake_word_status_var.set(text)
            self.wake_status_label.config(fg=color)
        except Exception:
            pass

    def safe_log_message(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        if self.logs_text and self.logs_text.winfo_exists():
            try:
                self.logs_text.insert(tk.END, line)
                self.logs_text.see(tk.END)
            except tk.TclError:
                pass
        print(line.strip())

    def load_commands(self):
        if not self.commands_tree or not self.commands_tree.winfo_exists():
            return
        try:
            for i in self.commands_tree.get_children():
                self.commands_tree.delete(i)
            for cmd in self.db_manager.get_all_commands():
                self.commands_tree.insert("", "end", values=(cmd["name"], cmd["pattern"], cmd["type"], "🟢 Active"))
        except Exception:
            pass

    def load_history(self):
        if not self.history_tree or not self.history_tree.winfo_exists():
            return
        try:
            for i in self.history_tree.get_children():
                self.history_tree.delete(i)
            for item in self.db_manager.get_command_history():
                icon = "✅" if item["status"] == "success" else "❌" if item["status"] == "failed" else "⏳"
                self.history_tree.insert("", "end", values=(
                    item["timestamp"], item["command"], f"{icon} {item['status']}", f"{item['confidence']:.2f}" if item["confidence"] else "N/A"
                ))
        except Exception:
            pass

    def load_recent_activity(self, widget):
        try:
            hist = self.db_manager.get_command_history(20)
            if not hist:
                widget.insert(tk.END, "No recent activity. Say 'Nova' to activate continuous listening.\n")
                widget.configure(state="disabled")
                return
            for item in hist:
                ts = item["timestamp"]
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    ts = dt.strftime("%H:%M:%S")
                except Exception:
                    pass
                icon = "✅" if item["status"] == "success" else "❌" if item["status"] == "failed" else "⏳"
                widget.insert(tk.END, f"[{ts}] {icon} Command: \"{item['command']}\"\n")
            widget.see(tk.END)
            widget.configure(state="disabled")
        except Exception as e:
            widget.insert(tk.END, f"Error loading activity: {e}\n")
            widget.configure(state="disabled")

    def save_settings(self):
        try:
            self.settings["confidence_threshold"] = self.confidence_var.get()
            self.settings["voice_feedback"] = self.voice_feedback_var.get()
            self.settings["wake_word"] = self.wake_word_entry.get().lower()
            # camera prefs
            self.settings["camera_index"] = int(self.camera_index_var.get())
            self.settings["camera_width"] = int(self.camera_w_var.get())
            self.settings["camera_height"] = int(self.camera_h_var.get())

            self.db_manager.save_settings(self.settings)
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!", parent=self.root)
            self.safe_log_message("⚙️ Settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}", parent=self.root)
            self.safe_log_message(f"❌ Settings save error: {e}")

    def load_settings(self):
        try:
            s = self.db_manager.load_settings()
            if s:
                self.settings.update(s)
        except Exception as e:
            self.safe_log_message(f"⚠️ Settings load error: {e}")

    def clear_logs(self):
        if self.logs_text and self.logs_text.winfo_exists():
            try:
                self.logs_text.delete(1.0, tk.END)
                self.safe_log_message("🗑️ Logs cleared")
            except tk.TclError:
                pass

    def back_to_dashboard(self):
        """Return to the main dashboard launcher"""
        response = messagebox.askyesno(
            "Back to Dashboard",
            "Return to the main dashboard?\n\nThis will close the voice control module."
        )
        
        if response:
            # Stop all services
            self.wake_word_active = False
            self.continuous_listening = False
            if hasattr(self, "gesture_controller") and self.gesture_controller.is_running():
                self.gesture_controller.stop()
            if hasattr(self, "speech_engine"):
                self.speech_engine.cleanup()
            if hasattr(self, 'db'):
                self.save_settings()
            
            # Launch dashboard
            try:
                base_dir = Path(__file__).resolve().parent.parent
                launcher_script = base_dir / "launcher" / "common_launcher.py"
                venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
                python_exec = str(venv_python if venv_python.exists() else Path(sys.executable))
                
                subprocess.Popen(
                    [python_exec, str(launcher_script)],
                    cwd=str(launcher_script.parent)
                )
                
                # Close this window
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch dashboard: {e}")

    def on_closing(self):
        try:
            self.wake_word_active = False
            self.continuous_listening = False
            if hasattr(self, "gesture_controller") and self.gesture_controller.is_running():
                self.gesture_controller.stop()
            if hasattr(self, "speech_engine"):
                self.speech_engine.cleanup()
        except Exception:
            pass
        self.root.destroy()


# ==============================
# Hand Gesture Mouse Controller
# ==============================
class CameraStream:
    def __init__(self, src=0, width=640, height=480):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW if platform.system() == "Windows" else 0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {src}")
        self.queue = queue.Queue(maxsize=1)
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            if not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Exception:
                    pass
            self.queue.put(frame)

    def read(self):
        try:
            return self.queue.get(timeout=0.5)
        except queue.Empty:
            return None

    def release(self):
        self.running = False
        try:
            self.cap.release()
        except Exception:
            pass


class HandGestureController:
    """Start/stop a background thread that runs Virtual Mouse and streams annotated frames via callback."""
    def __init__(self, on_started=None, on_stopped=None, on_error=None):
        self.thread = None
        self.running = False
        self.stream = None
        self.on_started = on_started or (lambda: None)
        self.on_stopped = on_stopped or (lambda: None)
        self.on_error = on_error or (lambda _msg: None)
        self._lock = threading.Lock()
        self._frame_consumer = None

    def is_running(self):
        with self._lock:
            return self.running

    def start(self, camera_index=0, width=640, height=480, frame_consumer=None):
        with self._lock:
            if self.running:
                return True, None
            self._frame_consumer = frame_consumer
            try:
                self.stream = CameraStream(src=camera_index, width=width, height=height)
            except Exception as e:
                self.stream = None
                return False, str(e)
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        self.on_started()
        return True, None

    def stop(self):
        with self._lock:
            if not self.running:
                return True
            self.running = False
        try:
            if self.stream:
                self.stream.release()
                self.stream = None
        except Exception:
            pass
        self.on_stopped()
        return True

    def _run(self):
        try:
            mp_hands = mp.solutions.hands  # type: ignore
            mp_drawing = mp.solutions.drawing_utils  # type: ignore

            screen_w, screen_h = pyautogui.size()
            mid_screen_y = screen_h // 2

            smooth_factor = 0.5
            prev_mouse_x, prev_mouse_y = 0, 0

            is_active = False
            last_toggle_time = 0

            left_gesture_start = None
            dragging = False
            CLICK_HOLD_TIME = 0.5

            right_click_start = None
            right_click_active = False
            last_right_click_time = 0
            RIGHT_CLICK_HOLD = 0.3
            RIGHT_CLICK_COOLDOWN = 1.0

            SCROLL_INTERVAL = 0.15
            V_DEADZONE = max(30, int(screen_h * 0.05))
            last_scroll_time = 0.0

            def landmarks_to_array(lm_list):
                return np.array([[lm.x, lm.y, lm.z] for lm in lm_list])

            def finger_extended_np(lms, tip_idx, pip_idx):
                return lms[tip_idx, 1] < lms[pip_idx, 1]

            def thumb_really_extended_np(lms):
                tip = lms[mp_hands.HandLandmark.THUMB_TIP.value]
                ip = lms[mp_hands.HandLandmark.THUMB_IP.value]
                index_tip = lms[mp_hands.HandLandmark.INDEX_FINGER_TIP.value]
                return tip[0] < ip[0] and abs(tip[0] - index_tip[0]) > 0.08

            def five_fingers_extended(lms):
                tips = [8, 12, 16, 20]
                pips = [6, 10, 14, 18]
                return all(finger_extended_np(lms, t, p) for t, p in zip(tips, pips)) and thumb_really_extended_np(lms)

            with mp_hands.Hands(
                model_complexity=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6,
                max_num_hands=1
            ) as hands:
                last_push = 0
                push_interval = 0.02  # ~50 fps max push to UI

                # Ensure stream is initialized
                if self.stream is None:
                    print("Error: Camera stream not initialized")
                    return

                while self.is_running():
                    frame = self.stream.read()
                    if frame is None:
                        continue

                    frame = cv2.flip(frame, 1)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb_frame)
                    now = time.time()

                    if results.multi_hand_landmarks:
                        hand_landmarks = results.multi_hand_landmarks[0]
                        lms = landmarks_to_array(hand_landmarks.landmark)
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        # Toggle tracking with 5 fingers
                        if five_fingers_extended(lms) and (now - last_toggle_time > 1.5):
                            is_active = not is_active
                            print("Virtual Mouse " + ("Activated" if is_active else "Deactivated"))
                            last_toggle_time = now

                        if is_active:
                            index_ext = finger_extended_np(lms, 8, 6)
                            middle_ext = finger_extended_np(lms, 12, 10)
                            ring_ext = finger_extended_np(lms, 16, 14)
                            pinky_ext = finger_extended_np(lms, 20, 18)
                            thumb_ext = thumb_really_extended_np(lms)

                            # cursor movement
                            index_tip = lms[mp_hands.HandLandmark.INDEX_FINGER_TIP.value]
                            target_x = int(index_tip[0] * screen_w)
                            target_y = int(index_tip[1] * screen_h)

                            if index_ext:
                                mouse_x = int(prev_mouse_x + (target_x - prev_mouse_x) * smooth_factor)
                                mouse_y = int(prev_mouse_y + (target_y - prev_mouse_y) * smooth_factor)
                                if abs(mouse_x - prev_mouse_x) > 2 or abs(mouse_y - prev_mouse_y) > 2:
                                    pyautogui.moveTo(mouse_x, mouse_y)
                                    prev_mouse_x, prev_mouse_y = mouse_x, mouse_y

                            # left click / drag
                            left_click_gesture = thumb_ext and index_ext and not middle_ext and not ring_ext and not pinky_ext
                            if left_click_gesture:
                                if left_gesture_start is None:
                                    left_gesture_start = now
                                elif not dragging and (now - left_gesture_start > CLICK_HOLD_TIME):
                                    pyautogui.mouseDown()
                                    dragging = True
                                    print("Drag Start")
                            else:
                                if left_gesture_start is not None:
                                    hold_time = now - left_gesture_start
                                    left_gesture_start = None
                                    if dragging:
                                        pyautogui.mouseUp()
                                        dragging = False
                                        print("Drag End")
                                    elif hold_time <= CLICK_HOLD_TIME:
                                        pyautogui.click()
                                        print("Left Click")

                            # right click (rock sign)
                            rock_sign = index_ext and pinky_ext and not middle_ext and not ring_ext and not thumb_ext
                            if rock_sign:
                                if right_click_start is None:
                                    right_click_start = now
                                elif (not right_click_active
                                      and (now - right_click_start > RIGHT_CLICK_HOLD)
                                      and (now - last_right_click_time > RIGHT_CLICK_COOLDOWN)):
                                    pyautogui.click(button="right")
                                    right_click_active = True
                                    last_right_click_time = now
                                    print("Right Click (Rock Sign)")
                            else:
                                right_click_start = None
                                right_click_active = False

                            # vertical scroll
                            if index_ext and middle_ext and ring_ext and not pinky_ext and (now - last_scroll_time >= SCROLL_INTERVAL):
                                avg_y = np.mean([lms[8, 1], lms[12, 1], lms[16, 1]])
                                finger_y_screen = int(avg_y * screen_h)
                                dy = finger_y_screen - mid_screen_y
                                if abs(dy) > V_DEADZONE:
                                    pyautogui.scroll(-50 if dy > 0 else 50)
                                    print("Scroll Down" if dy > 0 else "Scroll Up")
                                last_scroll_time = now
                    else:
                        try:
                            prev_mouse_x, prev_mouse_y = pyautogui.position()
                        except Exception:
                            pass

                    # Push frame to UI at limited rate
                    t = time.time()
                    if self._frame_consumer and (t - last_push) >= push_interval:
                        last_push = t
                        # annotate status on frame corner
                        color = (0, 200, 0) if is_active else (0, 0, 200)
                        txt = "ACTIVE" if is_active else "IDLE (show 5 fingers to toggle)"
                        cv2.rectangle(frame, (8, 8), (310, 40), (20, 20, 20), -1)
                        cv2.putText(frame, f"Gesture: {txt}", (16, 32),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
                        try:
                            self._frame_consumer(frame)
                        except Exception:
                            pass
        except Exception as e:
            self.on_error(str(e))
        finally:
            try:
                if self.stream:
                    self.stream.release()
            except Exception:
                pass
            with self._lock:
                self.running = False
            self.on_stopped()


# =========================
#   Engines / Controllers
# =========================
class EnhancedSpeechEngine:
    def __init__(self):
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Optimize recognizer settings for better wake word detection
            self.recognizer.energy_threshold = 300  # Lower for more sensitivity
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 0.8  # Wait 0.8s of silence before considering phrase complete
            self.recognizer.operation_timeout = None  # No operation timeout
            self.recognizer.phrase_threshold = 0.3  # Minimum phrase duration
            self.recognizer.non_speaking_duration = 0.5  # Non-speaking duration required to consider phrase complete
            
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            
            if len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            self.tts_engine.setProperty("rate", 165)
            self.tts_engine.setProperty("volume", 0.9)
            
            # Initial ambient noise adjustment
            print("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"Speech engine initialization error: {e}")

    def listen_for_wake_word(self, wake_word, timeout=3):
        try:
            with self.microphone as source:
                # Brief ambient adjustment before each listen
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
            
            # Try Google Speech Recognition with retry
            try:
                text = str(self.recognizer.recognize_google(audio)).lower()
            except sr.RequestError:
                # Network error, try once more
                try:
                    text = str(self.recognizer.recognize_google(audio)).lower()
                except:
                    return None
            
            # More flexible wake word matching
            wake_parts = wake_word.lower().strip().split()
            text_clean = text.strip()
            
            # Exact match
            if wake_word.lower() in text_clean:
                return (text, 0.95)
            
            # Partial match: all words present
            if all(part in text_clean for part in wake_parts):
                return (text, 0.85)
            
            # Fuzzy match: most words present
            matches = sum(1 for part in wake_parts if part in text_clean)
            if matches >= len(wake_parts) - 1 and matches > 0:
                return (text, 0.75)
            
            return None
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Wake word error: {e}")
            return None

    def listen_for_command(self, timeout=5):
        try:
            with self.microphone as source:
                # Quick ambient adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=6)
            
            # Try Google Speech Recognition with retry
            try:
                text = str(self.recognizer.recognize_google(audio)).lower()
            except sr.RequestError:
                # Network error, try once more
                try:
                    text = str(self.recognizer.recognize_google(audio)).lower()
                except:
                    return None
            
            return (text, 0.85)
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Command listening error: {e}")
            return None

    def speak(self, text, emotion="neutral", interruptible=True):
        """Enhanced speak with emotion-based voice modulation and interrupt capability"""
        try:
            # Adjust voice properties based on emotion for more natural responses
            original_rate = self.tts_engine.getProperty('rate')
            original_volume = self.tts_engine.getProperty('volume')
            
            if emotion == "excited":
                self.tts_engine.setProperty('rate', 180)
                self.tts_engine.setProperty('volume', 0.95)
            elif emotion == "friendly":
                self.tts_engine.setProperty('rate', 165)
                self.tts_engine.setProperty('volume', 0.9)
            elif emotion == "calm":
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.85)
            elif emotion == "serious":
                self.tts_engine.setProperty('rate', 145)
                self.tts_engine.setProperty('volume', 0.9)
            
            if interruptible:
                # For long text, check for interruption every few words
                words = text.split()
                chunk_size = 10  # Speak 10 words at a time
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i+chunk_size])
                    self.tts_engine.say(chunk)
                    self.tts_engine.runAndWait()
                    # Short pause to check for interruption
                    import time
                    time.sleep(0.1)
            else:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            
            # Restore original settings
            self.tts_engine.setProperty('rate', original_rate)
            self.tts_engine.setProperty('volume', original_volume)
        except Exception:
            pass
    
    def stop_speaking(self):
        """Stop current speech immediately"""
        try:
            self.tts_engine.stop()
        except Exception:
            pass

    def cleanup(self):
        try:
            self.tts_engine.stop()
        except Exception:
            pass


class EnhancedCommandProcessor:
    def __init__(self):
        self.load_enhanced_patterns()

    def load_enhanced_patterns(self):
        # IMPORTANT: Pattern order matters! Specific patterns MUST come before generic ones
        # Order: typing → selection → web → window → scroll → conversation → system → application → rest
        self.patterns = {
            # 1. TYPING - Most specific, check first
            "typing": [
                (r"type (.+)", "type_text"),
                (r"write (.+)", "type_text"),
                (r"enter (.+)", "type_text"),
                (r"new line", "new_line"),
                (r"new paragraph", "new_paragraph"),
                (r"press enter", "press_enter"),
                (r"press tab", "press_tab"),
                (r"press space", "press_space"),
                (r"backspace", "backspace"),
                (r"delete", "delete_key"),
            ],
            
            # 2. SELECTION - Specific text selection
            "selection": [
                (r"select next (word|line|character)", "select_next"),
                (r"select previous (word|line|character)", "select_previous"),
                (r"(select|choose) next", "select_next"),
                (r"(select|choose) previous", "select_previous"),
                (r"select all", "select_all"),
            ],
            
            # 3. WEB - Website opening and search (BEFORE application)
            "web": [
                # Website opening (must come before search to take priority)
                (r"open youtube", "open_website"),
                (r"open facebook", "open_website"),
                (r"open twitter", "open_website"),
                (r"open instagram", "open_website"),
                (r"open linkedin", "open_website"),
                (r"open whatsapp web", "open_website"),
                (r"open whatsapp", "open_website"),
                (r"open github", "open_website"),
                (r"open gmail", "open_website"),
                (r"open amazon", "open_website"),
                (r"open netflix", "open_website"),
                (r"open spotify", "open_website"),
                (r"open reddit", "open_website"),
                (r"open pinterest", "open_website"),
                (r"open tiktok", "open_website"),
                (r"open snapchat", "open_website"),
                (r"open telegram", "open_website"),
                (r"open discord", "open_website"),
                (r"open slack", "open_website"),
                (r"open medium", "open_website"),
                (r"open quora", "open_website"),
                (r"open stack overflow", "open_website"),
                (r"open maps", "open_website"),
                (r"google maps", "open_website"),
                (r"open drive", "open_website"),
                (r"google drive", "open_website"),
                # Web search (comes after website opening)
                (r"search for (.+)", "web_search"),
                (r"search (.+)", "web_search"),
                (r"google (.+)", "web_search"),
                (r"look up (.+)", "web_search"),
                (r"browse (.+)", "web_search"),
                (r"find (.+)", "web_search"), 
                (r"show me (.+)", "web_search"),
                (r"check weather", "web_search"),
                (r"check news", "web_search"),
            ],
            
            # 4. WINDOW - Window and tab management (BEFORE navigation)
            "window": [
                # Window switching (Alt+Tab)
                (r"switch to (\w+)", "switch_to_window"),
                (r"change to (\w+)", "switch_to_window"),
                (r"go to next window", "next_window"),
                (r"go to previous window", "previous_window"),
                (r"(switch|change) window", "next_window"),
                (r"next window", "next_window"),
                (r"previous window", "previous_window"),
                # Window operations
                (r"minimize (window|the window|this window)", "minimize_window"),
                (r"maximize (window|the window|this window)", "maximize_window"),
                (r"close (window|the window|this window)", "close_window"),
                # Tab operations (Ctrl+Tab) - Fix table/tab misrecognition
                (r"close (tab|table)", "close_tab"),
                (r"close this (tab|table)", "close_tab"),
                (r"go to next (tab|table)", "switch_tab"),
                (r"go to previous (tab|table)", "previous_tab"),
                (r"switch (tab|table)", "switch_tab"),
                (r"next (tab|table)", "switch_tab"),
                (r"change (tab|table)", "switch_tab"),
                (r"change previous (tab|table)", "previous_tab"),
                (r"previous (tab|table)", "previous_tab"),
                (r"new (tab|table)", "new_tab"),
                (r"open new (tab|table)", "new_tab"),
            ],
            
            # 5. SCROLL - Page scrolling
            "scroll": [
                (r"scroll (up|down)", "scroll_page"),
                (r"(page|scroll) (up|down)", "scroll_page"),
                (r"scroll to (top|bottom)", "scroll_extreme"),
            ],
            
            # 6. CONVERSATION - Friendly responses
            "conversation": [
                (r"(hello|hi|hey|greetings)", "greeting"),
                (r"how are you", "how_are_you"),
                (r"what(s| is) your name", "my_name"),
                (r"(thank you|thanks|thank)", "thanks"),
                (r"(goodbye|bye|see you)", "goodbye"),
                (r"(help|what can you do)", "help"),
                (r"(who made you|who created you)", "creator"),
                (r"tell me a joke", "joke"),
            ],
            
            # 7. SYSTEM - System commands (volume, brightness, time, etc.) - BEFORE utility
            "system": [
                (r"volume up", "volume_control"),
                (r"volume down", "volume_control"),
                (r"(increase|raise) (the )?volume", "volume_control"),
                (r"(decrease|lower) (the )?volume", "volume_control"),
                (r"turn (the )?volume (up|down)", "volume_control"), 
                (r"make it (louder|quieter)", "volume_control"),  
                (r"(mute|unmute)", "mute_control"),
                (r"brightness up", "brightness_control"),
                (r"brightness down", "brightness_control"),
                (r"(increase|decrease) brightness", "brightness_control"),
                (r"lock (computer|screen)", "lock_system"),
                (r"shutdown|shut down", "shutdown"),
                (r"restart|reboot", "restart"),
                (r"sleep|hibernate", "sleep"),
                (r"take screenshot", "screenshot"),
                # TIME/DATE - Must come BEFORE utility to avoid calculator conflict
                (r"what time is it", "tell_time"),
                (r"^time$", "tell_time"),
                (r"tell (me )?(the )?time", "tell_time"),
                (r"current time", "tell_time"),
                (r"what date is it", "tell_date"),
                (r"^date$", "tell_date"),
                (r"tell (me )?(the )?date", "tell_date"),
                (r"current date", "tell_date"),
                (r"today's date", "tell_date"),
                (r"minimize all", "minimize_all"),
                (r"show desktop", "show_desktop"),
                (r"task manager", "task_manager"),
                (r"check internet", "check_internet"),
                (r"empty (the )?recycle bin", "empty_recycle"),
            ],
            
            # 8. APPLICATION - Open/close applications (AFTER web patterns)
            "application": [
                (r"open (\w+)", "open_app"),
                (r"launch (\w+)", "open_app"),
                (r"start (\w+)", "open_app"),
                (r"run (\w+)", "open_app"),
                (r"close (\w+)", "close_app"),
            ],
            
            # 9. FILE - File operations
            "file": [
                (r"create folder (.+)", "create_folder"),
                (r"(create|make) (a )?file (.+)", "create_file"),
                (r"open (desktop|documents|downloads|pictures|music|videos)", "open_folder"),
                (r"go to (desktop|documents|downloads|pictures|music|videos)", "open_folder"),
                (r"open (file explorer|explorer)", "open_explorer"),
            ],
            
            # 10. MEDIA - Media controls + YouTube navigation
            "media": [
                # YouTube video play commands
                (r"^play$", "play_video"),  # Single word 'play' for YouTube
                (r"play (this|video|it)", "play_video"),
                (r"play first (one|video|song|result)", "play_video"),
                (r"play (the )?video", "play_video"),
                
                # YouTube selection/navigation
                (r"select first (one|video|result|song)", "select_first"),
                (r"select (down|up|next|previous)", "navigate_result"),
                (r"(go |move |scroll )?down", "next_result"),
                (r"(go |move |scroll )?up", "previous_result"),
                (r"next (result|video|one)", "next_result"),
                (r"previous (result|video|one)", "previous_result"),
                (r"scroll (down|up)", "scroll_media"),
                
                # Regular media controls
                (r"(play|start|resume) (music|song|audio)", "play_music"),
                (r"(pause|stop) (music|song|audio)", "pause_music"),
                (r"(next|skip) (song|track)", "next_song"),
                (r"(previous|back|last) (song|track)", "previous_song"),
                (r"stop (playing |the )?music", "stop_music"),
            ],
            
            # 11. NETWORK - Network operations
            "network": [
                (r"connect wifi", "connect_wifi"),
                (r"disconnect wifi", "disconnect_wifi"),
                (r"show ip", "show_ip"),
                (r"network settings", "network_settings"),
            ],
            
            # 12. UTILITY - Utility operations (math only, NOT time/date)
            "utility": [
                (r"set timer (.+)", "set_timer"),
                (r"set alarm (.+)", "set_alarm"),
                # CALCULATOR - Only match actual math operations
                (r"calculate (.+)", "calculate"),
                (r"(add|subtract|multiply|divide|sum|minus|plus|times) (.+)", "calculate"),
                (r"what('s| is) (\d+.*[+\-*/].+)", "calculate"),  # Only math expressions
                (r"solve (.+)", "calculate"),
                (r"copy (.+)", "copy_text"),
                (r"paste", "paste_text"),
                (r"(read|speak|say) (.+)", "read_text"),
            ],
            
            # 13. GESTURE - Gesture control
            "gesture": [
                (r"(enable|start|turn on) (gesture|mouse|virtual mouse)", "gesture_on"),
                (r"(disable|stop|turn off) (gesture|mouse|virtual mouse)", "gesture_off"),
                (r"(toggle|switch) (gesture|mouse)", "gesture_toggle"),
            ],
            
            # 14. NAVIGATION - Arrow keys (LAST, most generic)
            "navigation": [
                (r"^right$", "arrow_right"),
                (r"^left$", "arrow_left"),
                (r"^up$", "arrow_up"),
                (r"^down$", "arrow_down"),
                (r"arrow right", "arrow_right"),
                (r"arrow left", "arrow_left"),
                (r"arrow up", "arrow_up"),
                (r"arrow down", "arrow_down"),
                (r"press right", "arrow_right"),
                (r"press left", "arrow_left"),
                (r"press up", "arrow_up"),
                (r"press down", "arrow_down"),
            ],
        }

    def process_command(self, text):
        import re
        t = text.lower().strip()
        for cat, pats in self.patterns.items():
            for pattern, action in pats:
                m = re.search(pattern, t)
                if m:
                    return self._build(cat, action, m, t)
        return {"action": "unknown", "parameters": {}, "confidence": 0.1}

    def _build(self, cat, action, m, original):
        if cat == "conversation":
            return {"action": "conversation", "parameters": {"type": action, "original": original}, "confidence": 0.95}
        if cat == "application":
            if action == "close_app":
                app = m.group(1) if m.groups() else "unknown"
                return {"action": "application", "parameters": {"app": app, "close": True}, "confidence": 0.9}
            app = m.group(1) if m.groups() else "unknown"
            return {"action": "application", "parameters": {"app": app}, "confidence": 0.9}
        if cat == "web":
            if action == "open_website":
                # Comprehensive site mapping for social media and popular sites
                site_map = {
                    "youtube": "youtube.com",
                    "facebook": "facebook.com",
                    "twitter": "twitter.com",
                    "instagram": "instagram.com",
                    "linkedin": "linkedin.com",
                    "whatsapp": "web.whatsapp.com",
                    "github": "github.com",
                    "gmail": "gmail.com",
                    "amazon": "amazon.com",
                    "netflix": "netflix.com",
                    "spotify": "spotify.com",
                    "reddit": "reddit.com",
                    "pinterest": "pinterest.com",
                    "tiktok": "tiktok.com",
                    "snapchat": "snapchat.com",
                    "telegram": "web.telegram.org",
                    "discord": "discord.com",
                    "slack": "slack.com",
                    "medium": "medium.com",
                    "quora": "quora.com",
                    "stack overflow": "stackoverflow.com",
                    "stackoverflow": "stackoverflow.com",
                    "maps": "maps.google.com",
                    "drive": "drive.google.com",
                }
                q = None
                # Check for exact matches in the original command
                original_lower = original.lower()
                for k, v in site_map.items():
                    if k in original_lower:
                        q = v
                        break
                if q is None:
                    q = m.group(1) if m.groups() else original
                return {"action": "web", "parameters": {"query": q, "is_website": True}, "confidence": 0.95}
            elif "weather" in original:
                q = "weather forecast"
            elif "news" in original:
                q = "latest news"
            else:
                q = m.group(1) if m.groups() else original
            return {"action": "web", "parameters": {"query": q, "is_website": False}, "confidence": 0.9}
        if cat == "system":
            if "volume" in action:
                direction = "up" if ("up" in original or "increase" in original) else "down"
                return {"action": "system", "parameters": {"action": "volume", "direction": direction}, "confidence": 0.9}
            return {"action": "system", "parameters": {"action": action.replace("_", "")}, "confidence": 0.9}
        if cat == "file":
            if action == "create_folder":
                name = m.group(1) if m.groups() else "New Folder"
                return {"action": "file", "parameters": {"action": "create_folder", "filename": name}, "confidence": 0.9}
            if action == "open_folder":
                folder = m.group(1) if m.groups() else "desktop"
                return {"action": "file", "parameters": {"action": "open_folder", "folder": folder}, "confidence": 0.9}
        if cat == "media":
            return {"action": "media", "parameters": {"action": action}, "confidence": 0.9}
        if cat == "network":
            return {"action": "network", "parameters": {"action": action}, "confidence": 0.9}
        if cat == "utility":
            value = m.group(1) if m.groups() else None
            return {"action": "utility", "parameters": {"action": action, "value": value}, "confidence": 0.9}
        if cat == "gesture":
            intent = "on" if "on" in action else "off" if "off" in action else "toggle"
            return {"action": "gesture", "parameters": {"state": intent}, "confidence": 0.95}
        if cat == "window":
            if action == "switch_to_window":
                app_name = m.group(1) if m.groups() else "unknown"
                return {"action": "window", "parameters": {"action": action, "app": app_name}, "confidence": 0.9}
            return {"action": "window", "parameters": {"action": action}, "confidence": 0.9}
        if cat == "typing":
            if "type_text" in action or "type_text" in action:
                text = m.group(1) if m.groups() else ""
                return {"action": "typing", "parameters": {"action": action, "text": text}, "confidence": 0.9}
            return {"action": "typing", "parameters": {"action": action}, "confidence": 0.9}
        if cat == "selection":
            unit = "character"
            if m.groups():
                unit = m.group(1) if "word" in original or "line" in original or "character" in original else "character"
            direction = "next" if "next" in action else "previous" if "previous" in action else "all"
            return {"action": "selection", "parameters": {"action": action, "unit": unit, "direction": direction}, "confidence": 0.9}
        if cat == "navigation":
            # Determine arrow direction from action or original text
            if "right" in action or "right" in original or "next" in original:
                arrow_dir = "right"
            elif "left" in action or "left" in original or "back" in original:
                arrow_dir = "left"
            elif "up" in action or "up" in original:
                arrow_dir = "up"
            elif "down" in action or "down" in original:
                arrow_dir = "down"
            else:
                arrow_dir = "right"  # default
            return {"action": "navigation", "parameters": {"direction": arrow_dir}, "confidence": 0.95}
        if cat == "scroll":
            if "extreme" in action:
                direction = "top" if "top" in original else "bottom"
            else:
                direction = "up" if "up" in original else "down"
            return {"action": "scroll", "parameters": {"direction": direction}, "confidence": 0.9}
        return {"action": "unknown", "parameters": {}, "confidence": 0.1}


class EnhancedSystemController:
    def __init__(self):
        self.system = platform.system().lower()

    def open_application(self, app_name):
        try:
            app = app_name.lower()
            if self.system == "windows":
                cmds = {
                    "chrome": "start chrome", "firefox": "start firefox", "edge": "start msedge",
                    "notepad": "notepad", "calculator": "calc", "explorer": "explorer",
                    "word": "start winword", "excel": "start excel", "powerpoint": "start powerpnt",
                    "outlook": "start outlook", "skype": "start skype", "teams": "start msteams",
                    "discord": "start discord", "spotify": "start spotify", "vlc": "start vlc",
                    "vscode": "code", "cmd": "start cmd", "powershell": "start powershell",
                    "paint": "start mspaint", "settings": "start ms-settings:",
                }
            elif self.system == "darwin":
                cmds = {"chrome": 'open -a "Google Chrome"', "firefox": 'open -a "Firefox"',
                        "safari": 'open -a "Safari"', "notepad": 'open -a "TextEdit"',
                        "calculator": 'open -a "Calculator"', "explorer": 'open -a "Finder"',
                        "spotify": 'open -a "Spotify"', "vscode": 'open -a "Visual Studio Code"'}
            else:
                cmds = {"chrome": "google-chrome", "firefox": "firefox", "notepad": "gedit",
                        "calculator": "gnome-calculator", "explorer": "nautilus", "vscode": "code"}
            command = cmds.get(app, app)
            subprocess.Popen(str(command), shell=True)
            return True
        except Exception as e:
            print(f"Error opening application: {e}")
            return False

    def execute_system_command(self, parameters):
        try:
            action = parameters.get('action')
            if action == 'volume':
                direction = parameters.get('direction', 'up')
                return self.adjust_volume(direction)
            elif action == 'mute':
                return self.toggle_mute()
            elif action == 'lock':
                return self.lock_system()
            elif action == 'shutdown':
                return self.shutdown_system()
            elif action == 'restart':
                return self.restart_system()
            elif action == 'sleep':
                return self.sleep_system()
            elif action == 'screenshot':
                return self.take_screenshot()
            elif action == 'telltime':
                return self.tell_time()
            elif action == 'telldate':
                return self.tell_date()
            elif action == 'minimizeall':
                return self.minimize_all_windows()
            elif action == 'showdesktop':
                return self.show_desktop()
            elif action == 'taskmanager':
                return self.open_task_manager()
            elif action == 'checkinternet':
                return self.check_internet_connection()
        except Exception as e:
            print(f"Error executing system command: {e}")
            return False

    def web_search(self, parameters, context=None):
        """Handle both website opening and context-aware searches (YouTube vs Google)"""
        try:
            if isinstance(parameters, dict):
                query = parameters.get('query', '')
                is_website = parameters.get('is_website', False)
            else:
                # Backwards compatibility
                query = parameters
                is_website = False
            
            # If it's a direct website (like youtube.com)
            if is_website or query.endswith('.com') or query.endswith('.org') or query.endswith('.net'):
                # Remove 'www.' if present and ensure proper URL format
                clean_query = query.replace('www.', '')
                if not clean_query.startswith('http'):
                    url = f"https://{clean_query}"
                else:
                    url = clean_query
                    
                # Track context for future searches
                if 'youtube' in clean_query:
                    self.last_opened_context = 'youtube'
                else:
                    self.last_opened_context = 'web'
            else:
                # Context-aware search: Check if YouTube was recently opened
                if context == 'youtube' or (hasattr(self, 'last_opened_context') and self.last_opened_context == 'youtube'):
                    # Search within YouTube
                    search_query = query.replace(' ', '+')
                    url = f"https://www.youtube.com/results?search_query={search_query}"
                    webbrowser.open(url)
                    
                    # Wait for page to load and auto-focus first result
                    time.sleep(3)  # Give page time to fully load
                    
                    # Click on the page first to ensure focus
                    pyautogui.click()
                    time.sleep(0.3)
                    
                    # Press Tab multiple times to reach first video result
                    for _ in range(4):
                        pyautogui.press('tab')
                        time.sleep(0.1)
                    
                    return True
                else:
                    # It's a Google search
                    search_query = query.replace(' ', '+')
                    url = f"https://www.google.com/search?q={search_query}"
                    self.last_opened_context = 'google'
            
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Error performing web search: {e}")
            return False

    def file_operation(self, parameters):
        try:
            action = parameters.get('action')
            if action == 'create_folder':
                return self.create_folder(parameters.get('filename', 'New Folder'))
            elif action == 'open_folder':
                return self.open_folder(parameters.get('folder', 'desktop'))
        except Exception as e:
            print(f"Error in file operation: {e}"); return False

    def media_control(self, parameters):
        try:
            action = parameters.get('action')
            
            # YouTube video controls
            if action == 'play_video':
                # Press Enter to play selected video
                pyautogui.press('enter')
                return True
            elif action == 'select_first':
                # Tab to first result (in case not already there)
                for _ in range(4):
                    pyautogui.press('tab')
                    time.sleep(0.05)
                return True
            elif action == 'navigate_result':
                # Handle 'select down/up' commands
                direction = parameters.get('query', '').lower()
                if 'down' in direction or 'next' in direction:
                    pyautogui.press('tab')  # Tab to next
                elif 'up' in direction or 'previous' in direction:
                    pyautogui.hotkey('shift', 'tab')  # Shift+Tab to previous
                return True
            elif action == 'next_result':
                # Navigate to next result (Tab key for YouTube)
                pyautogui.press('tab')
                return True
            elif action == 'previous_result':
                # Navigate to previous result (Shift+Tab for YouTube)
                pyautogui.hotkey('shift', 'tab')
                return True
            elif action == 'scroll_media':
                # Scroll page
                direction = parameters.get('direction', 'down')
                if direction == 'down':
                    pyautogui.scroll(-3)
                else:
                    pyautogui.scroll(3)
                return True
            
            # Regular media controls
            if self.system == 'windows':
                if action in ('play_music', 'pause_music'):
                    subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys([char]179)']); return True
                if action == 'next_song':
                    subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys([char]176)']); return True
                if action == 'previous_song':
                    subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys([char]177)']); return True
                if action == 'stop_music':
                    subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys([char]178)']); return True
        except Exception as e:
            print(f"Error in media control: {e}"); return False

    def network_operation(self, parameters):
        try:
            action = parameters.get('action')
            if action == 'show_ip': return self.show_ip_address()
            elif action == 'check_internet': return self.check_internet_connection()
            elif action == 'network_settings': return self.open_network_settings()
        except Exception as e:
            print(f"Error in network operation: {e}"); return False

    def utility_operation(self, parameters):
        try:
            action = parameters.get('action'); value = parameters.get('value')
            if action == 'calculate': return self.calculate(value)
        except Exception as e:
            print(f"Error in utility operation: {e}"); return False

    def window_operation(self, parameters):
        """Handle window management operations"""
        try:
            action = parameters.get('action', '')
            if action == 'minimize_window':
                return self.minimize_window()
            elif action == 'maximize_window':
                return self.maximize_window()
            elif action == 'close_window':
                return self.close_window()
            elif action == 'switch_tab':
                return self.switch_tab('next')
            elif action == 'previous_tab':
                return self.switch_tab('previous')
            elif action == 'new_tab':
                return self.new_tab()
            elif action == 'close_tab':
                return self.close_tab()
            elif action == 'next_window':
                return self.next_window()
            elif action == 'previous_window':
                return self.previous_window()
            elif action == 'switch_to_window':
                app_name = parameters.get('app', '')
                return self.switch_to_window(app_name)
            return False
        except Exception as e:
            print(f"Error in window operation: {e}"); return False

    def adjust_volume(self, direction):
        try:
            if self.system == 'windows':
                # Use pyautogui for reliable volume control
                if direction == 'up':
                    for _ in range(2):  # Press twice for noticeable change
                        pyautogui.press('volumeup')
                        time.sleep(0.05)
                else:
                    for _ in range(2):
                        pyautogui.press('volumedown')
                        time.sleep(0.05)
            elif self.system == 'darwin':  # macOS
                amount = '10' if direction == 'up' else '-10'
                subprocess.run(['osascript', '-e', f'set volume output volume (output volume of (get volume settings) + {amount})'])
            elif self.system == 'linux':
                amount = '5%+' if direction == 'up' else '5%-'
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', amount])
            return True
        except Exception as e:
            print(f"Volume control error: {e}"); return False

    def toggle_mute(self):
        try:
            if self.system == 'windows':
                subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys([char]173)'])
            return True
        except Exception as e:
            print(f"Mute toggle error: {e}"); return False

    def lock_system(self):
        try:
            if self.system == 'windows':
                subprocess.run(['rundll32.exe','user32.dll,LockWorkStation'])
            return True
        except Exception as e:
            print(f"Lock system error: {e}"); return False

    def shutdown_system(self):
        try:
            if self.system == 'windows':
                subprocess.run(['shutdown','/s','/t','0'])
            return True
        except Exception as e:
            print(f"Shutdown error: {e}"); return False

    def restart_system(self):
        try:
            if self.system == 'windows':
                subprocess.run(['shutdown','/r','/t','0'])
            return True
        except Exception as e:
            print(f"Restart error: {e}"); return False

    def sleep_system(self):
        try:
            if self.system == 'windows':
                subprocess.run(['rundll32.exe','powrprof.dll,SetSuspendState','0,1,0'])
            return True
        except Exception as e:
            print(f"Sleep error: {e}"); return False

    def take_screenshot(self):
        try:
            if self.system == 'windows':
                subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys("{PRTSC}")'])
            return True
        except Exception as e:
            print(f"Screenshot error: {e}"); return False

    def tell_time(self):
        try:
            print(f"Current time is {datetime.now().strftime('%I:%M %p')}"); return True
        except Exception as e:
            print(f"Tell time error: {e}"); return False

    def tell_date(self):
        try:
            print(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"); return True
        except Exception as e:
            print(f"Tell date error: {e}"); return False

    def minimize_all_windows(self):
        try:
            if self.system == 'windows':
                subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys("^{ESC}")'])
                time.sleep(0.1)
                subprocess.run(['powershell','-c','(New-Object -comObject WScript.Shell).SendKeys("{d}")'])
            return True
        except Exception as e:
            print(f"Minimize all error: {e}"); return False

    def show_desktop(self):
        try:
            if self.system == 'windows':
                subprocess.run(['powershell','-c','Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^{ESC}d")'])
            return True
        except Exception as e:
            print(f"Show desktop error: {e}"); return False

    def open_task_manager(self):
        try:
            if self.system == 'windows':
                subprocess.Popen(['taskmgr']); return True
        except Exception as e:
            print(f"Task manager error: {e}"); return False

    def check_internet_connection(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3); print("Internet connection is active"); return True
        except OSError:
            print("No internet connection"); return False

    def create_folder(self, folder_name):
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(os.path.join(desktop, folder_name), exist_ok=True)
            print(f"Created folder: {folder_name}"); return True
        except Exception as e:
            print(f"Create folder error: {e}"); return False

    def open_folder(self, folder_name):
        try:
            folders = {
                'desktop': os.path.join(os.path.expanduser("~"), "Desktop"),
                'documents': os.path.join(os.path.expanduser("~"), "Documents"),
                'downloads': os.path.join(os.path.expanduser("~"), "Downloads"),
                'pictures': os.path.join(os.path.expanduser("~"), "Pictures"),
                'music': os.path.join(os.path.expanduser("~"), "Music"),
                'videos': os.path.join(os.path.expanduser("~"), "Videos"),
            }
            path = folders.get(folder_name.lower())
            if path:
                if self.system == 'windows': subprocess.Popen(['explorer', path])
                elif self.system == 'darwin': subprocess.Popen(['open', path])
                else: subprocess.Popen(['nautilus', path])
                return True
            return False
        except Exception as e:
            print(f"Open folder error: {e}"); return False

    def show_ip_address(self):
        try:
            print(f"Your IP address is: {socket.gethostbyname(socket.gethostname())}"); return True
        except Exception as e:
            print(f"Show IP error: {e}"); return False

    def open_network_settings(self):
        try:
            if self.system == 'windows':
                subprocess.Popen(['ms-settings:network']); return True
        except Exception as e:
            print(f"Network settings error: {e}"); return False

    def calculate(self, expression):
        try:
            if self.system == 'windows': subprocess.Popen(['calc'])
            print(f"Calculating: {expression}"); return True
        except Exception as e:
            print(f"Calculate error: {e}"); return False
    
    def empty_recycle_bin(self):
        """Empty the recycle bin"""
        try:
            if self.system == 'windows':
                subprocess.run(['powershell', '-c', 
                            'Clear-RecycleBin -Force'], check=False)
                return True
        except Exception as e:
            print(f"Empty recycle bin error: {e}")
            return False

    def adjust_brightness(self, direction):
        """Adjust screen brightness"""
        try:
            # Try using keyboard shortcuts (most reliable cross-platform)
            if direction == 'up':
                pyautogui.press('brightnessup')
            else:
                pyautogui.press('brightnessdown')
            return True
        except Exception as e:
            print(f"Brightness control error: {e}")
            # Fallback: Try screen-brightness-control if installed
            try:
                import screen_brightness_control as sbc  # type: ignore
                current = sbc.get_brightness()[0]
                new_brightness = current + 10 if direction == 'up' else current - 10
                new_brightness = max(0, min(100, new_brightness))
                sbc.set_brightness(new_brightness)
                return True
            except:
                return False

    def close_application(self, app_name):
        """Close a running application"""
        try:
            if self.system == 'windows':
                # Map common app names to their process names
                app_map = {
                    'chrome': 'chrome.exe',
                    'firefox': 'firefox.exe',
                    'edge': 'msedge.exe',
                    'notepad': 'notepad.exe',
                    'calculator': 'CalculatorApp.exe',
                    'spotify': 'Spotify.exe',
                    'vscode': 'Code.exe',
                    'word': 'WINWORD.EXE',
                    'excel': 'EXCEL.EXE',
                    'powerpoint': 'POWERPNT.EXE',
                }
                process_name = app_map.get(app_name.lower(), f'{app_name}.exe')
                result = subprocess.run(['taskkill', '/IM', process_name, '/F'], 
                                      check=False, capture_output=True, text=True)
                return 'SUCCESS' in result.stdout or result.returncode == 0
            elif self.system == 'darwin':  # macOS
                subprocess.run(['pkill', '-f', app_name])
                return True
            elif self.system == 'linux':
                subprocess.run(['pkill', app_name])
                return True
        except Exception as e:
            print(f"Error closing application: {e}")
            return False
    
    def minimize_window(self):
        """Minimize the current active window"""
        try:
            if self.system == 'windows':
                pyautogui.hotkey('win', 'down')
            elif self.system == 'darwin':
                pyautogui.hotkey('command', 'm')
            elif self.system == 'linux':
                pyautogui.hotkey('super', 'h')
            return True
        except Exception as e:
            print(f"Error minimizing window: {e}")
            return False
    
    def maximize_window(self):
        """Maximize the current active window"""
        try:
            if self.system == 'windows':
                pyautogui.hotkey('win', 'up')
            elif self.system == 'darwin':
                # macOS uses green button, simulate with keyboard
                pyautogui.hotkey('ctrl', 'command', 'f')
            elif self.system == 'linux':
                pyautogui.hotkey('super', 'up')
            return True
        except Exception as e:
            print(f"Error maximizing window: {e}")
            return False
    
    def close_window(self):
        """Close the current active window"""
        try:
            if self.system == 'windows' or self.system == 'linux':
                pyautogui.hotkey('alt', 'f4')
            elif self.system == 'darwin':
                pyautogui.hotkey('command', 'w')
            return True
        except Exception as e:
            print(f"Error closing window: {e}")
            return False
    
    def switch_tab(self, direction='next'):
        """Switch browser/application tabs with improved reliability"""
        try:
            if self.system == 'windows' or self.system == 'linux':
                if direction == 'next':
                    # Use Ctrl+Tab for next tab
                    pyautogui.keyDown('ctrl')
                    time.sleep(0.05)
                    pyautogui.press('tab')
                    time.sleep(0.05)
                    pyautogui.keyUp('ctrl')
                else:
                    # Use Ctrl+Shift+Tab for previous tab
                    pyautogui.keyDown('ctrl')
                    pyautogui.keyDown('shift')
                    time.sleep(0.05)
                    pyautogui.press('tab')
                    time.sleep(0.05)
                    pyautogui.keyUp('shift')
                    pyautogui.keyUp('ctrl')
            elif self.system == 'darwin':
                if direction == 'next':
                    pyautogui.hotkey('command', 'option', 'right')
                else:
                    pyautogui.hotkey('command', 'option', 'left')
            time.sleep(0.1)  # Small delay for system to process
            return True
        except Exception as e:
            print(f"Error switching tab: {e}")
            return False
    
    def new_tab(self):
        """Open a new tab"""
        try:
            if self.system == 'windows' or self.system == 'linux':
                pyautogui.hotkey('ctrl', 't')
            elif self.system == 'darwin':
                pyautogui.hotkey('command', 't')
            return True
        except Exception as e:
            print(f"Error opening new tab: {e}")
            return False
    
    def close_tab(self):
        """Close the current tab"""
        try:
            if self.system == 'windows' or self.system == 'linux':
                pyautogui.hotkey('ctrl', 'w')
            elif self.system == 'darwin':
                pyautogui.hotkey('command', 'w')
            return True
        except Exception as e:
            print(f"Error closing tab: {e}")
            return False
    
    def scroll_page(self, direction, amount=3):
        """Scroll the current page/window"""
        try:
            if direction == 'up':
                pyautogui.scroll(amount * 100)  # Positive = scroll up
            elif direction == 'down':
                pyautogui.scroll(-amount * 100)  # Negative = scroll down
            elif direction == 'top':
                if self.system == 'windows' or self.system == 'linux':
                    pyautogui.hotkey('ctrl', 'home')
                elif self.system == 'darwin':
                    pyautogui.hotkey('command', 'up')
            elif direction == 'bottom':
                if self.system == 'windows' or self.system == 'linux':
                    pyautogui.hotkey('ctrl', 'end')
                elif self.system == 'darwin':
                    pyautogui.hotkey('command', 'down')
            return True
        except Exception as e:
            print(f"Error scrolling: {e}")
            return False
    
    def next_window(self):
        """Switch to next window using Alt+Tab"""
        try:
            if self.system == 'windows' or self.system == 'linux':
                # Hold Alt, press Tab, then release Alt
                pyautogui.keyDown('alt')
                time.sleep(0.1)
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.keyUp('alt')
            elif self.system == 'darwin':
                pyautogui.keyDown('command')
                time.sleep(0.1)
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.keyUp('command')
            time.sleep(0.15)  # Allow system to process window switch
            return True
        except Exception as e:
            print(f"Error switching window: {e}")
            return False
    
    def previous_window(self):
        """Switch to previous window"""
        try:
            if self.system == 'windows':
                pyautogui.hotkey('alt', 'shift', 'tab')
            elif self.system == 'darwin':
                pyautogui.hotkey('command', 'shift', 'tab')
            elif self.system == 'linux':
                pyautogui.hotkey('alt', 'shift', 'tab')
            return True
        except Exception as e:
            print(f"Error switching to previous window: {e}")
            return False
    
    def switch_to_window(self, app_name):
        """Switch to a specific application window"""
        try:
            if self.system == 'windows':
                # On Windows, we can use Alt+Tab multiple times or use taskbar
                # For simplicity, just open the app (will bring to front if already open)
                self.open_application(app_name)
            elif self.system == 'darwin':
                # macOS can switch using application name
                subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'])
            return True
        except Exception as e:
            print(f"Error switching to {app_name}: {e}")
            return False
    
    def typing_operation(self, parameters):
        """Handle typing/dictation operations"""
        try:
            action = parameters.get('action', '')
            text = parameters.get('text', '')
            
            if action == 'type_text' or action == 'write' or action == 'enter':
                # Type the text
                pyautogui.write(text, interval=0.05)
                return True
            elif action == 'new_line':
                pyautogui.press('enter')
                return True
            elif action == 'new_paragraph':
                pyautogui.press('enter')
                pyautogui.press('enter')
                return True
            elif action == 'press_enter':
                pyautogui.press('enter')
                return True
            elif action == 'press_tab':
                pyautogui.press('tab')
                return True
            elif action == 'press_space':
                pyautogui.press('space')
                return True
            elif action == 'backspace':
                pyautogui.press('backspace')
                return True
            elif action == 'delete_key':
                pyautogui.press('delete')
                return True
            return False
        except Exception as e:
            print(f"Error in typing operation: {e}")
            return False
    
    def selection_operation(self, parameters):
        """Handle text selection operations"""
        try:
            action = parameters.get('action', '')
            unit = parameters.get('unit', 'character')
            direction = parameters.get('direction', 'next')
            
            if action == 'select_all':
                if self.system == 'windows' or self.system == 'linux':
                    pyautogui.hotkey('ctrl', 'a')
                elif self.system == 'darwin':
                    pyautogui.hotkey('command', 'a')
                return True
            
            # Select next/previous
            if 'next' in action or direction == 'next':
                if unit == 'word':
                    if self.system == 'windows' or self.system == 'linux':
                        pyautogui.hotkey('ctrl', 'shift', 'right')
                    elif self.system == 'darwin':
                        pyautogui.hotkey('option', 'shift', 'right')
                elif unit == 'line':
                    if self.system == 'windows' or self.system == 'linux':
                        pyautogui.hotkey('shift', 'down')
                    elif self.system == 'darwin':
                        pyautogui.hotkey('shift', 'down')
                else:  # character
                    pyautogui.hotkey('shift', 'right')
            elif 'previous' in action or direction == 'previous':
                if unit == 'word':
                    if self.system == 'windows' or self.system == 'linux':
                        pyautogui.hotkey('ctrl', 'shift', 'left')
                    elif self.system == 'darwin':
                        pyautogui.hotkey('option', 'shift', 'left')
                elif unit == 'line':
                    if self.system == 'windows' or self.system == 'linux':
                        pyautogui.hotkey('shift', 'up')
                    elif self.system == 'darwin':
                        pyautogui.hotkey('shift', 'up')
                else:  # character
                    pyautogui.hotkey('shift', 'left')
            
            return True
        except Exception as e:
            print(f"Error in selection operation: {e}")
            return False
    
    def navigation_operation(self, parameters):
        """Handle arrow key navigation for menus/profiles/selections"""
        try:
            direction = parameters.get('direction', 'right')
            
            # Press the arrow key
            if direction == 'right':
                pyautogui.press('right')
            elif direction == 'left':
                pyautogui.press('left')
            elif direction == 'up':
                pyautogui.press('up')
            elif direction == 'down':
                pyautogui.press('down')
            
            return True
        except Exception as e:
            print(f"Error in navigation operation: {e}")
            return False


# =========================
# Database
# =========================
class DatabaseManager:
    def __init__(self):
        self.db_path = "speech_recognition.db"
        self.init_database()

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                type TEXT NOT NULL,
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_text TEXT NOT NULL,
                confidence REAL,
                status TEXT DEFAULT 'pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )""")
            conn.commit(); conn.close()
        except Exception as e:
            print(f"DB init error: {e}")

    def get_all_commands(self):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            cur.execute("SELECT * FROM commands"); rows = cur.fetchall(); conn.close()
            return [{"id": r[0], "name": r[1], "pattern": r[2], "type": r[3], "parameters": r[4]} for r in rows]
        except Exception as e:
            print(f"Get commands error: {e}"); return []

    def add_command_history(self, text, conf):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            cur.execute("INSERT INTO command_history (command_text, confidence) VALUES (?,?)", (text, conf))
            hid = cur.lastrowid; conn.commit(); conn.close(); return hid
        except Exception as e:
            print(f"Add history error: {e}"); return None

    def update_command_status(self, hid, status):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            cur.execute("UPDATE command_history SET status=? WHERE id=?", (status, hid))
            conn.commit(); conn.close()
        except Exception as e:
            print(f"Update status error: {e}")

    def get_command_history(self, limit=50):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            cur.execute("SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cur.fetchall(); conn.close()
            return [{"id": r[0], "command": r[1], "confidence": r[2], "status": r[3], "timestamp": r[4]} for r in rows]
        except Exception as e:
            print(f"Get history error: {e}"); return []

    def save_settings(self, settings):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            for k, v in settings.items():
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (k, json.dumps(v)))
            conn.commit(); conn.close()
        except Exception as e:
            print(f"Save settings error: {e}")

    def load_settings(self):
        try:
            conn = sqlite3.connect(self.db_path); cur = conn.cursor()
            cur.execute("SELECT * FROM settings"); rows = cur.fetchall(); conn.close()
            return {k: json.loads(v) for k, v in rows}
        except Exception as e:
            print(f"Load settings error: {e}"); return {}


# =========================
#   App entry
# =========================
def main():
    try:
        root = tk.Tk()
        app = ModernDarkSpeechApp(root)
        try:
            root.iconbitmap("icon.ico")
        except Exception:
            pass
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Startup error: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{e}")


if __name__ == "__main__":
    main()
