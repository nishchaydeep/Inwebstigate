"""
Inwebstigate - AI-Powered Web Investigation Tool

Main entry point for the Flask web application.
"""

from app import app, socketio
from config import Config
import webbrowser
import threading
import time


def open_browser():
    """Open browser after a short delay."""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5001')


def main():
    """Main entry point."""
    print("🔍 Inwebstigate - AI-Powered Web Investigation")
    print("=" * 60)
    print(f"LLM Provider: {Config.LLM_PROVIDER.upper()}")
    if Config.LLM_PROVIDER == 'ollama':
        print(f"Model: {Config.OLLAMA_MODEL}")
    else:
        print(f"Model: {Config.GROQ_MODEL}")
    print(f"Max Navigation Depth: {Config.MAX_NAVIGATION_DEPTH}")
    print("=" * 60)
    print("\n🌐 Starting web server...")
    print("📊 Your browser will open automatically at http://localhost:5001")
    print("\n💡 To change models, edit the .env or sample.env file")
    print("⏹  Press Ctrl+C to stop the server\n")
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask app with SocketIO
    try:
        socketio.run(app, debug=False, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

