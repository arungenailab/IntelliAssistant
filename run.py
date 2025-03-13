import os
import sys
import subprocess
import threading
import time
import webbrowser

def run_flask():
    """Run the Flask backend server"""
    print("Starting Flask backend server...")
    # Import app inside the function to avoid circular imports
    from api import app
    app.run(debug=True, port=5000, use_reloader=False)

def run_react():
    """Run the React frontend development server"""
    print("Starting React frontend development server...")
    os.chdir("frontend")
    subprocess.run(["npm", "start"], shell=True)

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("Waiting for Flask server to start...")
    time.sleep(2)  # Give Flask a moment to start
    
    # Open the browser to the React app
    webbrowser.open("http://localhost:3000")
    
    # Start React in the main thread
    run_react()
