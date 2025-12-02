"""
Centralized theme configuration for all modules
"""
import json
from pathlib import Path

THEME_FILE = Path(__file__).parent / "current_theme.json"

THEMES = {
    "dark": {
        "bg_primary": "#1a1a1a",
        "bg_secondary": "#1a1a1a",
        "bg_tertiary": "#2a2a2a",
        "bg_hover": "#333333",
        "bg_input": "#2a2a2a",
        "accent_primary": "#238636",
        "accent_secondary": "#2a4a7c",
        "accent_danger": "#da3633",
        "accent_warning": "#fb8500",
        "accent_emotion": "#00ff88",
        "accent_speech": "#58a6ff",
        "text_primary": "#ffffff",
        "text_secondary": "#c9d1d9",
        "text_muted": "#8b949e",
        "border": "#30363d",
        "scrollbar_bg": "#2a2a2a",
        "scrollbar_fg": "#8b949e",
        "tree_bg": "#2a2a2a",
        "tree_field": "#2a2a2a",
        "tree_fg": "#ffffff",
        "tree_heading": "#1a1a1a",
    },
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f6f8fa",
        "bg_tertiary": "#ffffff",
        "bg_hover": "#e8eaed",
        "bg_input": "#ffffff",
        "accent_primary": "#2da44e",
        "accent_secondary": "#0969da",
        "accent_danger": "#cf222e",
        "accent_warning": "#fb8500",
        "accent_emotion": "#00b359",
        "accent_speech": "#0969da",
        "text_primary": "#24292f",
        "text_secondary": "#57606a",
        "text_muted": "#6e7781",
        "border": "#d0d7de",
        "scrollbar_bg": "#f6f8fa",
        "scrollbar_fg": "#6e7781",
        "tree_bg": "#ffffff",
        "tree_field": "#ffffff",
        "tree_fg": "#24292f",
        "tree_heading": "#f6f8fa",
    }
}

def get_current_theme():
    """Get the current theme name"""
    try:
        if THEME_FILE.exists():
            with open(THEME_FILE, 'r') as f:
                data = json.load(f)
                return data.get('theme', 'dark')
    except Exception:
        pass
    return 'dark'

def set_current_theme(theme_name):
    """Save the current theme name"""
    try:
        with open(THEME_FILE, 'w') as f:
            json.dump({'theme': theme_name}, f)
    except Exception as e:
        print(f"Error saving theme: {e}")

def get_theme_colors(theme_name=None):
    """Get colors for a specific theme or current theme"""
    if theme_name is None:
        theme_name = get_current_theme()
    return THEMES.get(theme_name, THEMES['dark'])

def toggle_theme():
    """Toggle between dark and light theme"""
    current = get_current_theme()
    new_theme = 'light' if current == 'dark' else 'dark'
    set_current_theme(new_theme)
    return new_theme
