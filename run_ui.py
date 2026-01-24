#!/usr/bin/env python3
"""
VidCompress UI Launcher
Simplifies launching the UI application with proper dependency handling
"""

import sys
import subprocess
import platform
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    system = platform.system().lower()
    
    print("📦 Installing VidCompress dependencies...")
    
    if system == "windows":
        # Windows - use pip with user flag
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user",
                "PySide6", "PySide6-Addons", "Pillow"
            ], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run:")
            print("pip install --user PySide6 PySide6-Addons Pillow")
            return False
    
    elif system == "darwin":  # macOS
        try:
            # Check for Homebrew
            result = subprocess.run(["which", "brew"], capture_output=True)
            if result.returncode == 0:
                print("🍺 Using Homebrew to install dependencies...")
                subprocess.run(["brew", "install", "ffmpeg", "handbrake"], check=False)
            
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user",
                "PySide6", "PySide6-Addons", "Pillow"
            ], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies.")
            return False
    
    else:  # Linux
        try:
            print("🐧 Using apt to install system dependencies...")
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "ffmpeg", "libavcodec-dev", "libavformat-dev"
            ], check=False)
            
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user",
                "PySide6", "PySide6-Addons", "Pillow"
            ], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies.")
            return False
    
    print("✅ Dependencies installed successfully!")
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    try:
        import PySide6
        print("✅ PySide6 available")
    except ImportError:
        missing.append("PySide6")
    
    try:
        from PIL import Image
        print("✅ Pillow available")
    except ImportError:
        missing.append("Pillow")
    
    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], 
                    capture_output=True, check=True)
        print("✅ FFmpeg available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("FFmpeg (system)")
    
    return missing

def launch_ui():
    """Launch the main UI application"""
    try:
        # Add current directory to Python path
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from vidcompress_ui import main as ui_main
        ui_main()
    except ImportError as e:
        print(f"❌ Failed to import UI: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to launch UI: {e}")
        return False
    
    return True

def main():
    """Main launcher logic"""
    print("🎬 VidCompress UI Launcher v2.0")
    print("=" * 40)
    
    # Check dependencies first
    missing_deps = check_dependencies()
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        
        answer = input("\nWould you like to install them? (y/N): ").lower().strip()
        if answer in ['y', 'yes']:
            if not install_dependencies():
                print("\n❌ Failed to install dependencies. Please install manually.")
                sys.exit(1)
        else:
            print("\n❌ Please install missing dependencies and try again.")
            sys.exit(1)
    
    print("\n🚀 Launching VidCompress UI...")
    
    if launch_ui():
        print("\n✅ VidCompress UI started successfully!")
    else:
        print("\n❌ Failed to launch VidCompress UI.")
        sys.exit(1)

if __name__ == "__main__":
    main()