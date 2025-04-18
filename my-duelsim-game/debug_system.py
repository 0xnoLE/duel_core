#!/usr/bin/env python3
"""
DuelSim System Debugger

This script helps debug the entire DuelSim system by:
1. Starting the HTTP server
2. Starting the spectator server
3. Opening a browser to the debug page
4. Running a duel simulation
5. Monitoring WebSocket connections and messages
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
import socket
import json
import signal
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Debug the DuelSim system')
parser.add_argument('--http-port', type=int, default=8080, help='HTTP server port')
parser.add_argument('--ws-port', type=int, default=5556, help='WebSocket server port')
parser.add_argument('--player1', type=str, default='Ranger', help='Player 1 name')
parser.add_argument('--player2', type=str, default='Berserker', help='Player 2 name')
parser.add_argument('--no-browser', action='store_true', help='Do not open browser')
parser.add_argument('--debug-page', action='store_true', help='Open WebSocket debug page')
args = parser.parse_args()

# Global variables
processes = []

def start_server():
    """Start the HTTP and WebSocket servers"""
    print(f"Starting server on HTTP port {args.http_port} and WebSocket port {args.ws_port}...")
    
    # Check if server.py exists
    if not os.path.exists('server.py'):
        print("Error: server.py not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    # Start the server with the specified ports
    server_process = subprocess.Popen([
        sys.executable, 'server.py',
        '--http-port', str(args.http_port),
        '--ws-port', str(args.ws_port)
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    processes.append(server_process)
    
    # Wait for server to start
    for _ in range(30):  # Wait up to 3 seconds
        try:
            # Try to connect to the HTTP server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', args.http_port))
                print(f"HTTP server is running on port {args.http_port}")
                break
        except (ConnectionRefusedError, socket.error):
            time.sleep(0.1)
    else:
        print("Warning: Could not confirm HTTP server is running")
    
    # Start a thread to monitor server output
    def monitor_output():
        for line in server_process.stdout:
            print(f"[SERVER] {line.strip()}")
    
    threading.Thread(target=monitor_output, daemon=True).start()
    
    return server_process

def open_browser_windows():
    """Open browser windows to the web client and debug page"""
    if args.no_browser:
        return
    
    time.sleep(1)  # Give the server a bit more time to start
    
    if args.debug_page:
        # Open the WebSocket debug page
        debug_url = f"http://localhost:{args.http_port}/websocket_debug.html"
        print(f"Opening WebSocket debug page: {debug_url}")
        webbrowser.open(debug_url)
    else:
        # Open the main web client
        client_url = f"http://localhost:{args.http_port}"
        print(f"Opening web client: {client_url}")
        webbrowser.open(client_url)

def run_duel():
    """Run a duel simulation"""
    print(f"Running duel: {args.player1} vs {args.player2}...")
    
    # Check if run_duel.py exists
    if os.path.exists('run_duel.py'):
        duel_script = 'run_duel.py'
    elif os.path.exists('main.py'):
        duel_script = 'main.py'
    else:
        print("Error: Neither run_duel.py nor main.py found. Cannot run duel.")
        return None
    
    # Start the duel
    duel_process = subprocess.Popen([
        sys.executable, duel_script,
        '--player1', args.player1,
        '--player2', args.player2,
        '--spectator', 'true',  # Enable spectator mode
        '--spectator-port', str(args.ws_port)  # Use the same WebSocket port
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    processes.append(duel_process)
    
    # Start a thread to monitor duel output
    def monitor_output():
        for line in duel_process.stdout:
            print(f"[DUEL] {line.strip()}")
    
    threading.Thread(target=monitor_output, daemon=True).start()
    
    return duel_process

def cleanup():
    """Clean up all processes"""
    print("\nCleaning up...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()

def main():
    """Main function"""
    try:
        # Start the server
        server_process = start_server()
        
        # Open browser windows
        open_browser_windows()
        
        # Run a duel
        duel_process = run_duel()
        
        # Wait for user to press Enter
        print("\nPress Enter to exit...")
        input()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        cleanup()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    main() 