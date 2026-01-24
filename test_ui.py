#!/usr/bin/env python3
"""
Test script for VidCompress UI
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import PySide6
        print("✅ PySide6 imported successfully")
    except ImportError as e:
        print(f"❌ PySide6 import failed: {e}")
        return False
    
    try:
        from vidcompress_ui import VidCompressUI, get_platform_adapter
        print("✅ VidCompress UI modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ VidCompress UI import failed: {e}")
        return False

def test_platform_adapter():
    """Test platform adapter detection"""
    try:
        from vidcompress_ui import get_platform_adapter
        adapter = get_platform_adapter()
        engines = adapter.detect_engines()
        print(f"✅ Platform adapter working. Available engines: {engines}")
        return True
    except Exception as e:
        print(f"❌ Platform adapter test failed: {e}")
        return False

def main():
    print("Testing VidCompress UI...")
    
    tests = [
        ("Import Test", test_imports),
        ("Platform Adapter Test", test_platform_adapter),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
            print(f"{test_name} PASSED")
        else:
            print(f"{test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! VidCompress UI is ready.")
        
        # Try to run UI if in test mode
        if len(sys.argv) > 1 and sys.argv[1] == "--run-ui":
            print("🚀 Starting UI...")
            try:
                from PySide6.QtWidgets import QApplication
                from vidcompress_ui import VidCompressUI
                
                app = QApplication(sys.argv)
                window = VidCompressUI()
                window.show()
                sys.exit(app.exec())
            except Exception as e:
                print(f"❌ UI failed to start: {e}")
    else:
        print("❌ Some tests failed. Please fix issues before running UI.")
        sys.exit(1)

if __name__ == "__main__":
    main()