#!/usr/bin/env python3
"""
WMS System Startup Script
Quick launcher for all WMS applications
"""

import subprocess
import sys
import webbrowser
import time
from threading import Thread

def start_web_app():
    """Start main WMS web application"""
    print("🚀 Starting Main WMS Web App on http://localhost:5000")
    subprocess.run([sys.executable, "wms_web_app.py"])

def start_ai_app():
    """Start AI data layer application"""  
    print("🤖 Starting AI Interface on http://localhost:5001")
    subprocess.run([sys.executable, "simple_ai_app.py"])

def start_desktop_app():
    """Start desktop GUI application"""
    print("💻 Starting Desktop GUI Application")
    subprocess.run([sys.executable, "sku_msku_gui_mapper.py"])

def main():
    print("=" * 60)
    print("🏭 WMS (Warehouse Management System) Launcher")
    print("=" * 60)
    print()
    print("Choose how to run the WMS system:")
    print()
    print("1. 🌐 Web Interface (Main WMS)")
    print("2. 🤖 AI Interface (Natural Language Queries)")  
    print("3. 💻 Desktop GUI (File Processing)")
    print("4. 🚀 Start Both Web Apps (Recommended)")
    print("5. ❌ Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            start_web_app()
            break
        elif choice == "2":
            start_ai_app()
            break
        elif choice == "3":
            start_desktop_app()
            break
        elif choice == "4":
            print("🚀 Starting both web applications...")
            print("📊 Main WMS: http://localhost:5000")
            print("🤖 AI Interface: http://localhost:5001")
            print()
            
            # Start both apps in separate threads
            web_thread = Thread(target=start_web_app, daemon=True)
            ai_thread = Thread(target=start_ai_app, daemon=True)
            
            web_thread.start()
            time.sleep(2)
            ai_thread.start()
            
            # Open browsers
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:5000")
                time.sleep(1)
                webbrowser.open("http://localhost:5001")
            except:
                pass
                
            print("✅ Both applications started!")
            print("Press Ctrl+C to stop all applications")
            
            try:
                web_thread.join()
            except KeyboardInterrupt:
                print("\n🛑 Stopping applications...")
                sys.exit(0)
            break
        elif choice == "5":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
