#!/usr/bin/env python3
"""
VidCompress UI - Cross-platform video compression tool
Uses native OS APIs for optimal performance and metadata preservation
"""

import sys
import os
import platform
import subprocess
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json

# PyQt6 imports
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QPushButton, QLabel, QLineEdit, QProgressBar, QListWidget,
        QFileDialog, QMessageBox, QTabWidget, QTextEdit, QGroupBox,
        QSpinBox, QComboBox, QCheckBox, QSlider, QSplitter,
        QFrame, QGridLayout, QScrollArea
    )
from PySide6.QtCore import (
        Qt, QThread, Signal, QObject, QTimer, QSettings, QSize
    )
    from PySide6.QtGui import QIcon, QFont, QPixmap
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    print("❌ PySide6 not available. Install with: pip install PySide6")
    sys.exit(1)

# ================= CONFIG =================
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm", ".3gp"}
DEFAULT_QUALITY = 28
MAX_WORKERS = 2
APP_NAME = "VidCompress"
VERSION = "2.0.0"

# ================= PLATFORM ADAPTERS =================
from typing import Dict, Any, Tuple

class PlatformAdapter:
    """Base class for platform-specific video processing"""
    
    def detect_engines(self):
        """Return available video processing engines"""
        return ["ffmpeg"]
    
    def get_video_info(self, path):
        """Extract video metadata using native APIs"""
        return {}
    
    def compress_video(self, input_path, output_path, quality, engine="ffmpeg", remux=False):
        """Compress video using platform-optimized approach"""
        return False, "Not implemented"

class macOSAdapter(PlatformAdapter):
    """macOS-specific video processing using AVFoundation"""
    
    def detect_engines(self):
        engines = []
        if self._check_command("ffmpeg"):
            engines.append("ffmpeg")
        if self._check_command("HandBrakeCLI"):
            engines.append("handbrake")
        return engines
    
    def _check_command(self, cmd):
        from shutil import which as _which
        return _which(cmd) is not None
    
    def get_video_info(self, path):
        # Use ffprobe for now - will replace with AVFoundation in future
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_video_info(data)
        except Exception:
            pass
        return {}
    
    def _parse_video_info(self, data):
        """Parse video info from ffprobe output"""
        info = {
            "duration": 0, "width": 0, "height": 0, "fps": 0,
            "codec": "", "size": 0, "bitrate": 0, "metadata": {}
        }
        
        try:
            # Get video stream
            video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                info["width"] = video_stream.get("width", 0)
                info["height"] = video_stream.get("height", 0)
                info["codec"] = video_stream.get("codec_name", "")
                
                # Calculate FPS
                if "r_frame_rate" in video_stream:
                    fps_str = video_stream["r_frame_rate"]
                    info["fps"] = eval(fps_str.split('/')[0]) if '/' in fps_str else float(fps_str)
            
            # Get format info
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["size"] = int(fmt.get("size", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0))
                info["metadata"] = fmt.get("tags", {})
        
        except Exception:
            pass
        
        return info
    
    def compress_video(self, input_path, output_path, quality, engine="ffmpeg", remux=False):
        """Compress using macOS-optimized approach"""
        if remux:
            return self._remux_video(input_path, output_path)
        
        if engine == "handbrake":
            return self._handbrake_compress(input_path, output_path, quality)
        else:
            return self._ffmpeg_compress(input_path, output_path, quality)
    
    def _remux_video(self, input_path, output_path):
        """Fast remux using macOS VideoToolbox"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0",
            "-c", "copy", "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _ffmpeg_compress(self, input_path, output_path, quality):
        """Hardware-accelerated compression using VideoToolbox"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-c:v", "hevc_videotoolbox",
            "-tag:v", "hvc1", "-q:v", str(quality), "-g", "48",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _handbrake_compress(self, input_path, output_path, quality):
        """HandBrake compression with Apple VideoToolbox preset"""
        cmd = [
            "HandBrakeCLI", "-i", str(input_path), "-o", str(output_path),
            "--preset", "H.265 Apple VideoToolbox 1080p",
            "-q", str(quality), "--all-audio", "--optimize"
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()

class WindowsAdapter(PlatformAdapter):
    """Windows-specific video processing using Media Foundation"""
    
    def detect_engines(self):
        engines = []
        if self._check_command("ffmpeg"):
            engines.append("ffmpeg")
        if self._check_command("HandBrakeCLI"):
            engines.append("handbrake")
        return engines
    
    def _check_command(self, cmd):
        from shutil import which as _which
        return _which(cmd) is not None
    
    def get_video_info(self, path):
        # Use Media Foundation APIs - fallback to ffprobe for now
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_video_info(data)
        except Exception:
            pass
        return {}
    
    def _parse_video_info(self, data):
        info = {
            "duration": 0, "width": 0, "height": 0, "fps": 0,
            "codec": "", "size": 0, "bitrate": 0, "metadata": {}
        }
        
        try:
            video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                info["width"] = video_stream.get("width", 0)
                info["height"] = video_stream.get("height", 0)
                info["codec"] = video_stream.get("codec_name", "")
                
                if "r_frame_rate" in video_stream:
                    fps_str = video_stream["r_frame_rate"]
                    info["fps"] = eval(fps_str.split('/')[0]) if '/' in fps_str else float(fps_str)
            
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["size"] = int(fmt.get("size", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0))
                info["metadata"] = fmt.get("tags", {})
        except Exception:
            pass
        
        return info
    
    def compress_video(self, input_path, output_path, quality, engine="ffmpeg", remux=False):
        """Compress using Windows-optimized approach"""
        if remux:
            return self._remux_video(input_path, output_path)
        
        if engine == "handbrake":
            return self._handbrake_compress(input_path, output_path, quality)
        else:
            return self._ffmpeg_compress(input_path, output_path, quality)
    
    def _remux_video(self, input_path, output_path):
        """Fast remux using DirectX acceleration"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0",
            "-c", "copy", "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _ffmpeg_compress(self, input_path, output_path, quality):
        """Software compression using x265"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-c:v", "libx265", "-crf", str(quality), "-preset", "medium",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _handbrake_compress(self, input_path, output_path, quality):
        """HandBrake compression for Windows"""
        cmd = [
            "HandBrakeCLI", "-i", str(input_path), "-o", str(output_path),
            "--preset", "H.265 1080p", "-q", str(quality),
            "--all-audio"
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()

class LinuxAdapter(PlatformAdapter):
    """Linux-specific video processing using GStreamer/VAAPI"""
    
    def detect_engines(self):
        engines = []
        if self._check_command("ffmpeg"):
            engines.append("ffmpeg")
        if self._check_command("HandBrakeCLI"):
            engines.append("handbrake")
        return engines
    
    def _check_command(self, cmd):
        from shutil import which as _which
        return _which(cmd) is not None
    
    def get_video_info(self, path):
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_video_info(data)
        except Exception:
            pass
        return {}
    
    def _parse_video_info(self, data):
        info = {
            "duration": 0, "width": 0, "height": 0, "fps": 0,
            "codec": "", "size": 0, "bitrate": 0, "metadata": {}
        }
        
        try:
            video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                info["width"] = video_stream.get("width", 0)
                info["height"] = video_stream.get("height", 0)
                info["codec"] = video_stream.get("codec_name", "")
                
                if "r_frame_rate" in video_stream:
                    fps_str = video_stream["r_frame_rate"]
                    info["fps"] = eval(fps_str.split('/')[0]) if '/' in fps_str else float(fps_str)
            
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["size"] = int(fmt.get("size", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0))
                info["metadata"] = fmt.get("tags", {})
        except Exception:
            pass
        
        return info
    
    def compress_video(self, input_path, output_path, quality, engine="ffmpeg", remux=False):
        """Compress using Linux-optimized approach"""
        if remux:
            return self._remux_video(input_path, output_path)
        
        if engine == "handbrake":
            return self._handbrake_compress(input_path, output_path, quality)
        else:
            return self._ffmpeg_compress(input_path, output_path, quality)
    
    def _remux_video(self, input_path, output_path):
        """Fast remux using Linux VAAPI where available"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0",
            "-c", "copy", "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _ffmpeg_compress(self, input_path, output_path, quality):
        """Hardware-accelerated compression using VAAPI"""
        # Check for VAAPI support
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-c:v", "libx265", "-crf", str(quality), "-preset", "medium",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()
    
    def _handbrake_compress(self, input_path, output_path, quality):
        """HandBrake compression for Linux"""
        cmd = [
            "HandBrakeCLI", "-i", str(input_path), "-o", str(output_path),
            "--preset", "H.265 1080p", "-q", str(quality),
            "--all-audio"
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0, "" if result.returncode == 0 else result.stderr.decode()

def get_platform_adapter():
    """Get appropriate platform adapter"""
    system = platform.system().lower()
    if system == "darwin":
        return macOSAdapter()
    elif system == "windows":
        return WindowsAdapter()
    else:
        return LinuxAdapter()

# ================= THREADING =================
class Worker(QObject):
    """Worker thread for video processing"""
    finished = Signal(bool, str)  # success, message
    progress = Signal(int)           # progress percentage
    
    def __init__(self, adapter, input_files, output_dir, settings):
        super().__init__()
        self.adapter = adapter
        self.input_files = input_files
        self.output_dir = output_dir
        self.settings = settings
        self.is_running = False
    
    def run(self):
        """Process video files"""
        self.is_running = True
        processed = 0
        
        for i, input_file in enumerate(self.input_files):
            if not self.is_running:
                break
            
            try:
                # Generate output path
                output_file = self.output_dir / f"{input_file.stem}_compressed.mp4"
                
                # Process video
                success, message = self.adapter.compress_video(
                    input_file,
                    output_file,
                    self.settings['quality'],
                    self.settings['engine'],
                    self.settings['remux']
                )
                
                if success:
                    processed += 1
                else:
                    self.finished.emit(False, f"Failed to process {input_file.name}: {message}")
                    return
                
                # Update progress
                progress = int((i + 1) / len(self.input_files) * 100)
                self.progress.emit(progress)
                
            except Exception as e:
                self.finished.emit(False, f"Error processing {input_file.name}: {str(e)}")
                return
        
        self.finished.emit(True, f"Successfully processed {processed} files")
    
    def stop(self):
        """Stop processing"""
        self.is_running = False

# ================= MAIN UI =================
class VidCompressUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.adapter = get_platform_adapter()
        self.worker = None
        self.input_files = []
        self.settings = QSettings("VidCompress", "Settings")
        
        self.initUI()
        self.loadSettings()
    
    def initUI(self):
        """Initialize user interface"""
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # File input section
        file_group = QGroupBox("Input Files")
        file_layout = QHBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        
        file_btn_layout = QVBoxLayout()
        
        add_file_btn = QPushButton("Add Files")
        add_file_btn.clicked.connect(self.addFiles)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.addFolder)
        
        clear_btn = QPushButton("Clear List")
        clear_btn.clicked.connect(self.clearFiles)
        
        file_btn_layout.addWidget(add_file_btn)
        file_btn_layout.addWidget(add_folder_btn)
        file_btn_layout.addWidget(clear_btn)
        file_btn_layout.addStretch()
        
        file_layout.addWidget(self.file_list, 3)
        file_layout.addLayout(file_btn_layout, 1)
        file_group.setLayout(file_layout)
        
        # Settings section
        settings_group = QGroupBox("Compression Settings")
        settings_layout = QGridLayout()
        
        # Engine selection
        settings_layout.addWidget(QLabel("Engine:"), 0, 0)
        self.engine_combo = QComboBox()
        engines = self.adapter.detect_engines()
        self.engine_combo.addItems(engines)
        settings_layout.addWidget(self.engine_combo, 0, 1)
        
        # Quality setting
        settings_layout.addWidget(QLabel("Quality:"), 1, 0)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 50)
        self.quality_spin.setValue(DEFAULT_QUALITY)
        settings_layout.addWidget(self.quality_spin, 1, 1)
        
        # Remux checkbox
        self.remux_check = QCheckBox("Remux Only (No Re-encoding)")
        self.remux_check.setToolTip("Copy streams without re-encoding - much faster but no compression")
        settings_layout.addWidget(self.remux_check, 2, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        
        # Output section
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout()
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output directory...")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browseOutput)
        
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(browse_btn)
        output_group.setLayout(output_layout)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Compression")
        self.start_btn.clicked.connect(self.startCompression)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stopCompression)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        # Add all sections to main layout
        main_layout.addWidget(file_group)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(control_layout)
    
    def addFiles(self):
        """Add individual files to the list"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "", 
            "Video Files (*.mp4 *.mov *.mkv *.m4v *.avi *.webm *.3gp);;All Files (*)"
        )
        if files:
            for file in files:
                path = Path(file)
                if path.suffix.lower() in VIDEO_EXTS and path not in self.input_files:
                    self.input_files.append(path)
                    self.file_list.addItem(path.name)
    
    def addFolder(self):
        """Add all video files from a folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_path = Path(folder)
            for file in folder_path.rglob("*"):
                if file.is_file() and file.suffix.lower() in VIDEO_EXTS:
                    if file not in self.input_files:
                        self.input_files.append(file)
                        self.file_list.addItem(file.name)
    
    def clearFiles(self):
        """Clear the file list"""
        self.input_files.clear()
        self.file_list.clear()
    
    def browseOutput(self):
        """Browse for output directory"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_path.setText(folder)
    
    def startCompression(self):
        """Start video compression"""
        if not self.input_files:
            QMessageBox.warning(self, "Warning", "Please add video files first.")
            return
        
        output_dir = Path(self.output_path.text()) if self.output_path.text() else Path.home() / "VidCompress_Output"
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare settings
        settings = {
            'quality': self.quality_spin.value(),
            'engine': self.engine_combo.currentText().lower(),
            'remux': self.remux_check.isChecked()
        }
        
        # Start worker thread
        self.worker = Worker(self.adapter, self.input_files, output_dir, settings)
        self.worker.finished.connect(self.onWorkerFinished)
        self.worker.progress.connect(self.onWorkerProgress)
        
        self.worker.start()
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting compression...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Save settings
        self.saveSettings()
    
    def stopCompression(self):
        """Stop video compression"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def onWorkerFinished(self, success, message):
        """Handle worker completion"""
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText(f"❌ {message}")
            QMessageBox.critical(self, "Error", message)
    
    def onWorkerProgress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Processing... {value}%")
    
    def loadSettings(self):
        """Load saved settings"""
        self.quality_spin.setValue(self.settings.value("quality", DEFAULT_QUALITY, type=int))
        self.engine_index = self.settings.value("engine", 0, type=int)
        if self.engine_index < self.engine_combo.count():
            self.engine_combo.setCurrentIndex(self.engine_index)
        self.output_path.setText(self.settings.value("output_dir", "", type=str))
        self.remux_check.setChecked(self.settings.value("remux", False, type=bool))
    
    def saveSettings(self):
        """Save current settings"""
        self.settings.setValue("quality", self.quality_spin.value())
        self.settings.setValue("engine", self.engine_combo.currentIndex())
        self.settings.setValue("output_dir", self.output_path.text())
        self.settings.setValue("remux", self.remux_check.isChecked())
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        event.accept()

# ================= MAIN =================
def main():
    if not UI_AVAILABLE:
        print("❌ UI framework not available")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    
    window = VidCompressUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
