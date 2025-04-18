import os
import time
import threading
import subprocess
import webbrowser
import socket

def start_server():
    print("Starting server...")
    server_process = subprocess.Popen(["python", "server.py"])
    return server_process

def run_duel():
    print("Waiting for server to start...")
    time.sleep(3)  # Give the server time to start
    
    print("Running duel...")
    # Use the same port as the server.py is using
    duel_process = subprocess.Popen(["python", "run_duel.py", 
                                     "--player1", "TestFighter1", 
                                     "--player2", "TestFighter2",
                                     "--port", "5556",  # Explicitly set the port
                                     "--auto-start"])  # Auto-start to avoid waiting for Enter
    return duel_process

def open_browser():
    print("Opening browser...")
    time.sleep(1)  # Give the server a bit more time
    
    # Try port 8080 first, but fall back to 8081 if needed
    try:
        # Check if port 8080 is responding
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex(('localhost', 8080))
        s.close()
        
        if result == 0:
            # Port 8080 is open
            webbrowser.open("http://localhost:8080")
        else:
            # Try port 8081
            webbrowser.open("http://localhost:8081")
    except:
        # Default to 8081 if there's any error
        webbrowser.open("http://localhost:8081")

def main():
    try:
        server_process = start_server()
        open_browser()
        duel_process = run_duel()
        
        # Wait for the duel to finish
        duel_process.wait()
        
        print("Test complete! Check the browser to see if events were displayed correctly.")
        input("Press Enter to exit...")
        
    finally:
        # Clean up processes
        if 'server_process' in locals():
            server_process.terminate()
        if 'duel_process' in locals() and duel_process.poll() is None:
            duel_process.terminate()

if __name__ == "__main__":
    main()
