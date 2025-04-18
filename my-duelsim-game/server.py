"""
DuelSim Web Server

This module provides a simple HTTP server to serve the web client files
and forwards WebSocket connections to the spectator server.
"""

import os
import sys
import http.server
import socketserver
import threading
import webbrowser
import argparse
import socket
import json
from pathlib import Path
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the spectator mode and duel manager
from spectator_mode import SpectatorServer
from duel_manager import DuelManager

# Default ports
DEFAULT_HTTP_PORT = 8080
DEFAULT_SPECTATOR_PORT = 5556

class DuelSimHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for DuelSim"""
    
    def __init__(self, *args, duel_manager=None, **kwargs):
        self.duel_manager = duel_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        # Special paths
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Serve the simple client as the default
            with open('simple_client.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        
        elif self.path == '/client':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Serve the web client
            with open('web_client.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        
        elif self.path == '/test':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Serve the WebSocket test page
            with open('websocket_test.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        
        # API endpoint to start a duel
        elif self.path.startswith('/api/start-duel'):
            self._handle_start_duel()
            return
        
        # API endpoint to get duel status
        elif self.path == '/api/duel-status':
            if not self.duel_manager:
                self._send_json_response(500, {"error": "Duel manager not available"})
                return
            
            # Get current duel status
            current_duel = self.duel_manager.current_duel
            queue_size = self.duel_manager.duel_queue.qsize()
            
            # Send response
            self._send_json_response(200, {
                "current_duel": current_duel,
                "queue_size": queue_size
            })
            return
        
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        # Start duel endpoint
        if self.path == '/start-duel':
            self._handle_start_duel_post()
            return
        
        # Default response for unsupported POST endpoints
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def _handle_start_duel(self):
        """Handle a request to start a duel"""
        if not self.duel_manager:
            self._send_json_response(500, {"error": "Duel manager not available"})
            return
        
        # Parse query parameters
        import urllib.parse
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        player1 = params.get('player1', [''])[0] or None
        player2 = params.get('player2', [''])[0] or None
        
        try:
            max_ticks = int(params.get('max_ticks', ['150'])[0])
        except:
            max_ticks = 150
            
        try:
            tick_duration = int(params.get('tick_duration', ['500'])[0])
        except:
            tick_duration = 500
        
        # Queue the duel
        duel_config = self.duel_manager.queue_duel(
            player1_name=player1,
            player2_name=player2,
            max_ticks=max_ticks,
            tick_duration=tick_duration
        )
        
        # Send response
        self._send_json_response(200, {
            "status": "queued",
            "duel": {
                "player1": duel_config['player1_name'],
                "player2": duel_config['player2_name'],
                "queued_at": duel_config['queued_at']
            }
        })
    
    def _handle_start_duel_post(self):
        """Handle POST request to start a duel"""
        if not self.duel_manager:
            self._send_json_response(400, {'error': 'Duel manager not available'})
            return
        
        try:
            # Get random fighters for the duel
            fighters = self.duel_manager.get_random_fighters(2)
            if len(fighters) < 2:
                self._send_json_response(500, {'error': 'Not enough fighters available'})
                return
            
            # Start the duel
            duel_id = self.duel_manager.queue_duel(fighters[0], fighters[1])
            
            # Start the duel immediately
            self.duel_manager.start_next_duel()
            
            # Send success response
            self._send_json_response(200, {
                'status': 'success',
                'message': f'Duel queued: {fighters[0]} vs {fighters[1]}',
                'duel_id': duel_id
            })
        
        except Exception as e:
            self._send_json_response(500, {'error': str(e)})
    
    def _send_json_response(self, status_code, data):
        """Send a JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = json.dumps(data).encode('utf-8')
        self.wfile.write(response)
    
    def log_message(self, format, *args):
        """Override to provide colored logging"""
        sys.stderr.write("\033[92m[Web Server]\033[0m %s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def start_http_server(port=DEFAULT_HTTP_PORT, spectator_port=DEFAULT_SPECTATOR_PORT, duel_manager=None):
    """Start the HTTP server"""
    # Check if port is available, if not find another one
    if is_port_in_use(port):
        print(f"\033[93m[Web Server]\033[0m Port {port} is already in use.")
        new_port = find_available_port(port + 1)
        if new_port:
            print(f"\033[93m[Web Server]\033[0m Using port {new_port} instead.")
            port = new_port
        else:
            print(f"\033[91m[Web Server]\033[0m Could not find an available port. Exiting.")
            return False
    
    # Create handler with duel manager
    handler = lambda *args, **kwargs: DuelSimHTTPRequestHandler(*args, duel_manager=duel_manager, **kwargs)
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"\033[92m[Web Server]\033[0m Server started at http://localhost:{port}")
            print(f"\033[92m[Web Server]\033[0m Use http://localhost:{port}/client for the web client")
            print(f"\033[92m[Web Server]\033[0m Use http://localhost:{port}/test for WebSocket testing")
            print(f"\033[92m[Web Server]\033[0m WebSocket server running on port {spectator_port}")
            
            # Open the browser automatically to the web client
            webbrowser.open(f"http://localhost:{port}/client")
            
            # Update the WebSocket URL in the HTML files
            update_websocket_url(spectator_port)
            
            # Serve until interrupted
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\033[93m[Web Server]\033[0m Server stopped")
            
            return True
    except OSError as e:
        print(f"\033[91m[Web Server]\033[0m Error starting server: {e}")
        return False

def update_websocket_url(port):
    """Update the WebSocket URL in the HTML files to use the correct port"""
    try:
        # Update spectator.html
        with open('spectator.html', 'r') as f:
            content = f.read()
        
        # Replace the WebSocket URL with a more robust pattern
        pattern = r'const SERVER_URL = `ws://\$\{window\.location\.hostname\}:\d+`;'
        replacement = f'const SERVER_URL = `ws://${{window.location.hostname}}:{port}`;'
        content = re.sub(pattern, replacement, content)
        
        with open('spectator.html', 'w') as f:
            f.write(content)
        
        # Update websocket_test.html
        with open('websocket_test.html', 'r') as f:
            content = f.read()
        
        # Replace the WebSocket URL with a more robust pattern
        pattern = r'socket = new WebSocket\(`ws://\$\{window\.location\.hostname\}:\d+`\);'
        replacement = f'socket = new WebSocket(`ws://${{window.location.hostname}}:{port}`);'
        content = re.sub(pattern, replacement, content)
        
        with open('websocket_test.html', 'w') as f:
            f.write(content)
            
        print(f"\033[92m[Web Server]\033[0m Updated WebSocket URLs to use port {port}")
    except Exception as e:
        print(f"\033[93m[Web Server]\033[0m Warning: Could not update WebSocket URLs: {e}")

def start_spectator_server(port=DEFAULT_SPECTATOR_PORT):
    """Start the spectator server on the specified port"""
    # Check if port is available, if not find another one
    if is_port_in_use(port):
        print(f"\033[93m[Spectator Server]\033[0m Port {port} is already in use.")
        new_port = find_available_port(port + 1)
        if new_port:
            print(f"\033[93m[Spectator Server]\033[0m Using port {new_port} instead.")
            port = new_port
        else:
            print(f"\033[91m[Spectator Server]\033[0m Could not find an available port. Exiting.")
            return None, None
    
    # Start the spectator server
    try:
        server = SpectatorServer(port=port)
        if not server.start():
            print(f"\033[91m[Spectator Server]\033[0m Failed to start server.")
            return None, None
        
        return server, port
    except Exception as e:
        print(f"\033[91m[Spectator Server]\033[0m Error starting server: {e}")
        return None, None

def main():
    """Main function to start both servers"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start the DuelSim servers')
    parser.add_argument('--http-port', type=int, default=DEFAULT_HTTP_PORT,
                        help=f'Port for the HTTP server (default: {DEFAULT_HTTP_PORT})')
    parser.add_argument('--spectator-port', type=int, default=DEFAULT_SPECTATOR_PORT,
                        help=f'Port for the spectator server (default: {DEFAULT_SPECTATOR_PORT})')
    args = parser.parse_args()
    
    # Start the spectator server
    spectator_server, spectator_port = start_spectator_server(args.spectator_port)
    if spectator_server is None:
        return
    
    # Create the duel manager
    duel_manager = DuelManager(spectator_server)
    duel_manager.start()
    
    # Start the HTTP server
    start_http_server(args.http_port, spectator_port, duel_manager)
    
    # Stop the duel manager when done
    duel_manager.stop()

if __name__ == "__main__":
    main()
