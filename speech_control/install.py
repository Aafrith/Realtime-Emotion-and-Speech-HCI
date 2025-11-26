#!/usr/bin/env python3
"""
Enhanced installation script for Speech Recognition Desktop Application
"""

import subprocess
import sys
import os
import platform

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def install_system_dependencies():
    """Install system-specific dependencies"""
    system = platform.system().lower()
    
    print(f"Detected system: {system}")
    
    if system == "linux":
        print("Installing Linux dependencies...")
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", 
                          "python3-pyaudio", "portaudio19-dev", "python3-tk",
                          "espeak", "espeak-data", "libespeak1", "libespeak-dev",
                          "alsa-utils", "pulseaudio"], check=True)
            print("✅ Linux system dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not install system dependencies: {e}")
            print("Please install manually: sudo apt-get install python3-pyaudio portaudio19-dev python3-tk")
            
    elif system == "darwin":  # macOS
        print("Installing macOS dependencies...")
        try:
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            subprocess.run(["brew", "install", "portaudio"], check=True)
            print("✅ macOS system dependencies installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Warning: Homebrew not found or portaudio installation failed")
            print("Please install Homebrew and run: brew install portaudio")
            
    elif system == "windows":
        print("✅ Windows detected - pip should handle most dependencies")

def main():
    """Main installation function"""
    print("🎤 AI Speech Recognition Assistant - Installation")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
        
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install system dependencies
    install_system_dependencies()
    
    # Python packages to install
    packages = [
        "SpeechRecognition==3.10.0",
        "pyttsx3==2.90",
        "pyaudio",
    ]
    
    # Install Python packages
    print("\n📦 Installing Python packages...")
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Summary
    print("\n" + "=" * 60)
    if failed_packages:
        print("⚠️  Installation completed with some failures:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\nYou may need to install these manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        print("\nFor PyAudio issues on Windows, try:")
        print("   pip install pipwin")
        print("   pipwin install pyaudio")
    else:
        print("✅ All packages installed successfully!")
    
    print("\n🚀 Installation complete!")
    print("Run the application with: python run.py")
    
    # Create desktop shortcut (Windows)
    if platform.system().lower() == "windows":
        try:
            create_windows_shortcut()
        except Exception as e:
            print(f"⚠️  Could not create desktop shortcut: {e}")

def create_windows_shortcut():
    """Create a desktop shortcut on Windows"""
    import winshell
    from win32com.client import Dispatch
    
    desktop = winshell.desktop()
    path = os.path.join(desktop, "Speech Recognition Assistant.lnk")
    target = os.path.join(os.getcwd(), "run.py")
    wDir = os.getcwd()
    icon = target
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = sys.executable
    shortcut.Arguments = f'"{target}"'
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()
    
    print("✅ Desktop shortcut created")

if __name__ == "__main__":
    main()
