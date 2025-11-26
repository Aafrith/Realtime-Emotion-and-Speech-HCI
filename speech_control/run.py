
"""
Startup script for Speech Recognition Desktop Application
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = [
        'speech_recognition',
        'pyttsx3',
        'requests'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules

def show_dependency_error(missing_modules):
    """Show error dialog for missing dependencies"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    message = "Missing required dependencies:\n\n"
    message += "\n".join(f"• {module}" for module in missing_modules)
    message += "\n\nPlease run: python install.py"
    
    messagebox.showerror("Missing Dependencies", message)
    root.destroy()

def check_microphone():
    """Check if microphone is available"""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        mic = sr.Microphone()
        return True
    except Exception as e:
        return False

def main():
    """Main startup function"""
    print("🎤 Starting Speech Recognition Desktop Application...")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print("❌ Missing dependencies:")
        for module in missing:
            print(f"   - {module}")
        print("\nPlease run: python install.py")
        show_dependency_error(missing)
        return
    
    # Check microphone
    if not check_microphone():
        print("⚠️  Warning: Microphone may not be available")
        print("   Please check your microphone settings")
    
    # Import and run main application
    try:
        from main import main as run_app
        print("✅ Starting application...")
        run_app()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        
        # Show error dialog
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Application Error", f"Failed to start application:\n\n{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()
