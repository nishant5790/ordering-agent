#!/usr/bin/env python3
"""
Simple runner script for the Multi-Agent Order Chatbot System
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import streamlit
        import openai
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def run_streamlit():
    """Run the Streamlit application"""
    try:
        print("🚀 Starting Multi-Agent Order Chatbot System...")
        print("📱 Opening Streamlit application...")
        print("🌐 The app will open in your default browser")
        print("🔗 URL: http://localhost:8501")
        print("\nPress Ctrl+C to stop the application")
        print("-" * 50)
        
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")

def main():
    """Main function"""
    print("🤖 Multi-Agent Order Chatbot System")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("❌ main.py not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main()
