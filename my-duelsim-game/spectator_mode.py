"""
Spectator Mode for DuelSim

This module provides functionality for spectating duels in real-time.
It will serve as the foundation for future social features and betting.
"""

import os
import time
import json
import argparse
import threading
import socket
import select
import queue
from datetime import datetime
from colorama import init, Fore, Back, Style
from duelsim import run_duel_simulation
from duelsim.utils.enhanced_visualizer import EnhancedVisualizer
from future_paths.betting_system.betting_integration import BettingManager, BettingSpectatorIntegration
import uuid

# Initialize colorama for cross-platform color support
init(autoreset=True)

class SpectatorServer:
    """Server that broadcasts duel events to connected spectators"""
    
    def __init__(self, host='localhost', port=5555):
        """Initialize the spectator server"""
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.client_info = {}  # Store client info like user_id
        self.running = False
        self.event_queue = queue.Queue()
        self.battle_data = None
        self.current_tick = 0
        
        # Initialize betting manager
        self.betting_manager = BettingManager()
        self.betting_integration = BettingSpectatorIntegration(self, self.betting_manager)
        
    def start(self):
        """Start the spectator server"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.setblocking(0)  # Non-blocking mode
            
            self.running = True
            print(f"{Fore.GREEN}Spectator server started on {self.host}:{self.port}")
            
            # Start client handler thread
            client_thread = threading.Thread(target=self._handle_clients)
            client_thread.daemon = True
            client_thread.start()
            
            return True
        except Exception as e:
            print(f"{Fore.RED}Failed to start spectator server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        self.running = False
        print(f"{Fore.YELLOW}Stopping spectator server...")
        
        # Close all client connections
        clients_copy = self.clients.copy()  # Make a copy to avoid modification during iteration
        for client in clients_copy:
            try:
                client.close()
            except:
                pass
        
        # Clear the client list
        self.clients.clear()
        
        # Close the server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Wait for the client handler thread to finish
        if self.client_handler_thread and self.client_handler_thread.is_alive():
            self.client_handler_thread.join(timeout=1.0)
        
        print(f"{Fore.GREEN}Spectator server stopped")
        return True
    
    def _handle_clients(self):
        """Handle client connections and messages"""
        try:
            # Create a list of sockets to monitor
            input_list = [self.server_socket]
            
            while self.running:
                # Use a timeout to prevent blocking indefinitely
                try:
                    # Use select with a timeout to avoid blocking forever
                    readable, _, exceptional = select.select(input_list, [], input_list, 0.5)
                except (ValueError, select.error) as e:
                    # Handle invalid file descriptors
                    if "file descriptor" in str(e).lower():
                        # Clean up invalid sockets
                        input_list = [s for s in input_list if s is not None and s.fileno() >= 0]
                        # Make sure server socket is still in the list if it's valid
                        if self.server_socket and self.server_socket.fileno() >= 0 and self.server_socket not in input_list:
                            input_list.append(self.server_socket)
                        time.sleep(0.1)
                        continue
                    else:
                        raise
                
                # Handle readable sockets
                for sock in readable:
                    # New connection
                    if sock == self.server_socket:
                        client_socket, addr = sock.accept()
                        client_socket.setblocking(0)
                        input_list.append(client_socket)
                        self.clients.append(client_socket)
                        
                        # Initialize client info
                        self.client_info[client_socket] = {
                            "user_id": str(uuid.uuid4()),
                            "connected_at": datetime.now().isoformat(),
                            "is_websocket": False  # Will be set to True during WebSocket handshake
                        }
                        
                        print(f"{Fore.GREEN}New spectator connected: {addr}")
                        
                        # Send welcome message
                        self._send_welcome_message(client_socket)
                        
                        # Send battle info if available
                        if self.battle_data:
                            self._send_battle_info(client_socket)
                    
                    # Client message
                    else:
                        try:
                            data = sock.recv(4096)
                            if data:
                                # Process the data
                                self._process_client_message(sock, data)
                            else:
                                # Empty data means client disconnected
                                self._remove_client(sock, input_list)
                        except Exception as e:
                            print(f"{Fore.RED}Error receiving from client: {e}")
                            self._remove_client(sock, input_list)
                
                # Handle exceptional sockets
                for sock in exceptional:
                    print(f"{Fore.YELLOW}Exceptional condition on socket")
                    self._remove_client(sock, input_list)
                
                # Process events in the queue
                self._process_event_queue()
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
        
        except Exception as e:
            print(f"{Fore.RED}Error in client handler: {e}")
            import traceback
            traceback.print_exc()
    
    def _remove_client(self, client_socket, input_list):
        """Remove a client from the server"""
        try:
            addr = client_socket.getpeername()
            print(f"{Fore.YELLOW}Spectator disconnected: {addr}")
        except:
            pass
        
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        
        if client_socket in input_list:
            input_list.remove(client_socket)
        
        try:
            client_socket.close()
        except:
            pass
    
    def _process_client_message(self, client_socket, data):
        """Process a message from a client"""
        try:
            # Check if this is a WebSocket client
            if client_socket in self.client_info and self.client_info[client_socket].get("is_websocket", False):
                # Decode WebSocket frame
                message = self._decode_websocket_frame(data, client_socket)
                if message is None:
                    return
            else:
                # Regular client
                message = data.decode('utf-8').strip()
            
            # Check if this is an HTTP request
            if message.startswith('GET ') or message.startswith('POST '):
                self._handle_http_request(client_socket, message)
                return
            
            # Get or create user ID for this client
            if client_socket not in self.client_info:
                self.client_info[client_socket] = {
                    "user_id": str(uuid.uuid4()),
                    "connected_at": datetime.now().isoformat()
                }
            
            user_id = self.client_info[client_socket]["user_id"]
            
            # Simple command processing
            if message.startswith('/'):
                command_parts = message[1:].split()
                command = command_parts[0].lower()
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                # Betting commands
                if command in ['bet', 'odds', 'balance', 'mybets']:
                    self.betting_integration.process_betting_command(
                        client_socket, user_id, command, args
                    )
                    return
                
                # Other commands
                if command == 'info':
                    # Send battle info
                    self._send_battle_info(client_socket)
                
                elif command == 'stats':
                    # Send spectator stats
                    stats = {
                        'spectators': len(self.clients),
                        'current_tick': self.current_tick,
                        'timestamp': datetime.now().isoformat()
                    }
                    self._send_to_client(client_socket, json.dumps({
                        'type': 'stats',
                        'data': stats
                    }))
                
                elif command == 'help':
                    # Send help info
                    help_text = {
                        'commands': [
                            '/info - Get battle information',
                            '/stats - Get spectator statistics',
                            '/help - Show this help message',
                            '/bet <player> <amount> - Place a bet on a player',
                            '/odds - See current betting odds',
                            '/balance - Check your betting balance',
                            '/mybets - See your active bets'
                        ]
                    }
                    self._send_to_client(client_socket, json.dumps({
                        'type': 'help',
                        'data': help_text
                    }))
            
            # Chat message
            else:
                # In a real implementation, you would add username, timestamp, etc.
                chat_message = {
                    'sender': str(client_socket.getpeername()),
                    'user_id': user_id,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Broadcast to all clients
                self.broadcast(json.dumps({
                    'type': 'chat',
                    'data': chat_message
                }))
        
        except Exception as e:
            print(f"{Fore.RED}Error processing client message: {e}")
    
    def _handle_http_request(self, client_socket, request):
        """Handle an HTTP request from a web browser"""
        try:
            # Check if this is a WebSocket upgrade request
            if "Upgrade: websocket" in request and "Sec-WebSocket-Key:" in request:
                # Extract the WebSocket key
                websocket_key = None
                for line in request.split('\r\n'):
                    if line.startswith("Sec-WebSocket-Key:"):
                        websocket_key = line.split(": ")[1].strip()
                        break
                
                if websocket_key:
                    # Perform WebSocket handshake
                    import base64
                    import hashlib
                    
                    # Compute the WebSocket accept key
                    magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                    accept_key = base64.b64encode(
                        hashlib.sha1((websocket_key + magic_string).encode()).digest()
                    ).decode()
                    
                    # Send the WebSocket handshake response
                    handshake = (
                        "HTTP/1.1 101 Switching Protocols\r\n"
                        "Upgrade: websocket\r\n"
                        "Connection: Upgrade\r\n"
                        f"Sec-WebSocket-Accept: {accept_key}\r\n"
                        "\r\n"
                    )
                    client_socket.send(handshake.encode())
                    
                    # Mark this client as a WebSocket connection
                    self.client_info[client_socket] = {"is_websocket": True}
                    
                    # Send initial battle info if available
                    if self.battle_data:
                        self._send_battle_info_ws(client_socket)
                    
                    print(f"{Fore.GREEN}WebSocket connection established")
                    return
            
            # Regular HTTP response with a web interface
            html = """<!DOCTYPE html>
            <html>
            <head>
                <title>DuelSim Spectator Mode</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f0f0; }
                    .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                    h1 { color: #333; }
                    .info { background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .error { background-color: #f8e8e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .success { background-color: #e8f8e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .button { display: inline-block; background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; margin-right: 10px; cursor: pointer; }
                    #battle-area { border: 1px solid #ccc; padding: 10px; margin-top: 20px; min-height: 300px; }
                    .player { margin-bottom: 10px; padding: 10px; border-radius: 5px; }
                    .player1 { background-color: #e8f4f8; }
                    .player2 { background-color: #f8e8e8; }
                    .health-bar { height: 20px; background-color: #ddd; border-radius: 10px; margin-top: 5px; }
                    .health-fill { height: 100%; background-color: #4CAF50; border-radius: 10px; transition: width 0.3s; }
                    #events { max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-top: 20px; }
                    .event { margin-bottom: 5px; padding: 5px; border-radius: 3px; }
                    .attack { background-color: #ffeeee; }
                    .movement { background-color: #eeeeff; }
                    .victory { background-color: #eeffee; font-weight: bold; }
                    .connection-status { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
                    .connected { background-color: #e8f8e8; }
                    .disconnected { background-color: #f8e8e8; }
                    .connecting { background-color: #f8f8e8; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>DuelSim Spectator Mode</h1>
                    
                    <div id="connection-status" class="connection-status disconnected">
                        <p>Status: <span id="status-text">Disconnected</span></p>
                    </div>
                    
                    <div class="info">
                        <p>This is a web-based spectator interface for DuelSim.</p>
                        <p>Connect to the WebSocket server to see real-time battle updates.</p>
                        <button id="connect-btn" class="button">Connect</button>
                        <button id="disconnect-btn" class="button" style="display: none;">Disconnect</button>
                    </div>
                    
                    <div id="battle-area">
                        <h2>Current Battle</h2>
                        <div id="no-battle" style="display: block;">
                            <p>No battle in progress. Please wait for a battle to start.</p>
                        </div>
                        
                        <div id="battle-info" style="display: none;">
                            <div class="player player1">
                                <h3 id="player1-name">Player 1</h3>
                                <div class="health-bar">
                                    <div id="player1-health" class="health-fill" style="width: 100%;"></div>
                                </div>
                                <p id="player1-stats">HP: 100/100</p>
                            </div>
                            
                            <div class="player player2">
                                <h3 id="player2-name">Player 2</h3>
                                <div class="health-bar">
                                    <div id="player2-health" class="health-fill" style="width: 100%;"></div>
                                </div>
                                <p id="player2-stats">HP: 100/100</p>
                            </div>
                            
                            <div id="events">
                                <h3>Battle Events</h3>
                                <div id="event-list"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    // WebSocket connection
                    let socket = null;
                    let connected = false;
                    
                    // DOM elements
                    const statusText = document.getElementById('status-text');
                    const connectionStatus = document.getElementById('connection-status');
                    const connectBtn = document.getElementById('connect-btn');
                    const disconnectBtn = document.getElementById('disconnect-btn');
                    const noBattle = document.getElementById('no-battle');
                    const battleInfo = document.getElementById('battle-info');
                    const player1Name = document.getElementById('player1-name');
                    const player2Name = document.getElementById('player2-name');
                    const player1Health = document.getElementById('player1-health');
                    const player2Health = document.getElementById('player2-health');
                    const player1Stats = document.getElementById('player1-stats');
                    const player2Stats = document.getElementById('player2-stats');
                    const eventList = document.getElementById('event-list');
                    
                    // Connect to WebSocket server
                    function connect() {
                        if (socket && socket.readyState <= 1) {
                            return; // Already connecting or connected
                        }
                        
                        statusText.textContent = 'Connecting...';
                        connectionStatus.className = 'connection-status connecting';
                        
                        try {
                            // Create WebSocket connection
                            socket = new WebSocket(`ws://${window.location.hostname}:{port}`);
                            
                            // Connection opened
                            socket.addEventListener('open', function(event) {
                                connected = true;
                                statusText.textContent = 'Connected';
                                connectionStatus.className = 'connection-status connected';
                                connectBtn.style.display = 'none';
                                disconnectBtn.style.display = 'inline-block';
                                
                                // Add connected event
                                addEvent({
                                    type: 'info',
                                    message: 'Connected to server'
                                });
                            });
                            
                            // Connection closed
                            socket.addEventListener('close', function(event) {
                                connected = false;
                                statusText.textContent = 'Disconnected';
                                connectionStatus.className = 'connection-status disconnected';
                                connectBtn.style.display = 'inline-block';
                                disconnectBtn.style.display = 'none';
                                
                                // Add disconnected event
                                addEvent({
                                    type: 'error',
                                    message: 'Disconnected from server'
                                });
                            });
                            
                            // Connection error
                            socket.addEventListener('error', function(event) {
                                statusText.textContent = 'Error';
                                connectionStatus.className = 'connection-status disconnected';
                                
                                // Add error event
                                addEvent({
                                    type: 'error',
                                    message: 'Connection error'
                                });
                            });
                            
                            // Listen for messages
                            socket.addEventListener('message', function(event) {
                                try {
                                    const message = JSON.parse(event.data);
                                    
                                    // Handle different message types
                                    if (message.type === 'battle_info') {
                                        handleBattleInfo(message.data);
                                    } else if (message.type === 'event') {
                                        handleEvent(message.data);
                                    } else if (message.type === 'battle_start') {
                                        handleBattleStart(message.data);
                                    } else if (message.type === 'battle_end') {
                                        handleBattleEnd(message.data);
                                    }
                                } catch (error) {
                                    console.error('Error parsing message:', error);
                                }
                            });
                        } catch (error) {
                            statusText.textContent = 'Connection Failed';
                            connectionStatus.className = 'connection-status disconnected';
                            console.error('WebSocket connection error:', error);
                        }
                    }
                    
                    // Disconnect from server
                    function disconnect() {
                        if (socket) {
                            socket.close();
                        }
                    }
                    
                    // Handle battle info
                    function handleBattleInfo(data) {
                        // Store battle data
                        battleData = data;
                        
                        // Show battle info
                        noBattle.style.display = 'none';
                        battleInfo.style.display = 'block';
                        
                        // Update player info
                        updatePlayerInfo();
                        
                        // Add battle info event
                        addEvent({
                            type: 'info',
                            message: `Battle info received: ${data.players[0].name} vs ${data.players[1].name}`
                        });
                    }
                    
                    // Handle event
                    function handleEvent(event) {
                        // Add event to list
                        addEvent(event);
                        
                        // Update battle state based on event
                        if (event.type === 'attack' && battleData) {
                            // Update HP for the target player
                            for (let i = 0; i < battleData.players.length; i++) {
                                if (battleData.players[i].name === event.target) {
                                    battleData.players[i].hp = Math.max(0, battleData.players[i].hp - event.damage);
                                    updatePlayerInfo();
                                    break;
                                }
                            }
                        }
                    }
                    
                    // Add event to the event list
                    function addEvent(event) {
                        const div = document.createElement('div');
                        div.className = `event ${event.type || ''}`;
                        div.textContent = event.message || JSON.stringify(event);
                        eventList.appendChild(div);
                        eventList.scrollTop = eventList.scrollHeight;
                    }
                    
                    // Handle battle start
                    function handleBattleStart(data) {
                        // Store battle data
                        battleData = data;
                        
                        // Show battle info
                        noBattle.style.display = 'none';
                        battleInfo.style.display = 'block';
                        
                        // Update player info
                        updatePlayerInfo();
                        
                        // Add battle start event
                        addEvent({
                            type: 'info',
                            message: `Battle started: ${data.players[0].name} vs ${data.players[1].name}`
                        });
                    }
                    
                    // Handle battle end
                    function handleBattleEnd(data) {
                        // Add battle end event
                        addEvent({
                            type: 'victory',
                            message: `Battle ended. Winner: ${data.winner}`
                        });
                    }
                    
                    // Update player info
                    function updatePlayerInfo() {
                        if (!battleData || !battleData.players || battleData.players.length < 2) {
                            return;
                        }
                        
                        const player1 = battleData.players[0];
                        const player2 = battleData.players[1];
                        
                        player1Name.textContent = player1.name;
                        player2Name.textContent = player2.name;
                        
                        const player1HealthPercent = Math.max(0, Math.min(100, (player1.hp / player1.max_hp) * 100));
                        const player2HealthPercent = Math.max(0, Math.min(100, (player2.hp / player2.max_hp) * 100));
                        
                        player1Health.style.width = `${player1HealthPercent}%`;
                        player2Health.style.width = `${player2HealthPercent}%`;
                        
                        player1Stats.textContent = `HP: ${player1.hp}/${player1.max_hp}`;
                        player2Stats.textContent = `HP: ${player2.hp}/${player2.max_hp}`;
                    }
                    
                    // Event listeners
                    connectBtn.addEventListener('click', connect);
                    disconnectBtn.addEventListener('click', disconnect);
                    
                    // Auto-connect on page load
                    window.addEventListener('load', connect);
                </script>
            </body>
            </html>""".replace("{port}", str(self.port))
            
            # Send HTTP response
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(html)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{html}"
            )
            client_socket.send(response.encode())
        
        except Exception as e:
            print(f"{Fore.RED}Error handling HTTP request: {e}")
            try:
                # Send a simple error response
                error_response = (
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: text/plain\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    f"Error: {str(e)}"
                )
                client_socket.send(error_response.encode())
            except:
                pass
    
    def _send_welcome_message(self, client_socket):
        """Send a welcome message to a newly connected client"""
        try:
            # Check if this is a WebSocket client
            if client_socket in self.client_info and self.client_info[client_socket].get("is_websocket", False):
                # Send welcome message as JSON
                welcome_message = {
                    'type': 'welcome',
                    'data': {
                        'message': 'Welcome to DuelSim Spectator Mode!',
                        'server_time': time.time(),
                        'server_version': '1.0.0',
                        'connected_clients': len(self.clients)
                    }
                }
                self._send_websocket_message(client_socket, json.dumps(welcome_message))
            else:
                # Send plain text welcome message
                welcome_message = "Welcome to DuelSim Spectator Mode! Type /help for available commands."
                client_socket.send((welcome_message + '\n').encode('utf-8'))
        except Exception as e:
            print(f"{Fore.RED}Error sending welcome message: {e}")
    
    def _send_battle_info(self, client_socket):
        """Send battle information to a client"""
        if not self.battle_data:
            self._send_to_client(client_socket, json.dumps({
                'type': 'error',
                'data': {'message': 'No battle in progress'}
            }))
            return
        
        # Extract relevant battle info
        battle_info = {
            'players': [
                {
                    'name': self.battle_data['players'][0]['name'],
                    'hp': self.battle_data['players'][0]['hp'],
                    'max_hp': self.battle_data['players'][0]['max_hp'],
                    'position': self.battle_data['players'][0]['position']
                },
                {
                    'name': self.battle_data['players'][1]['name'],
                    'hp': self.battle_data['players'][1]['hp'],
                    'max_hp': self.battle_data['players'][1]['max_hp'],
                    'position': self.battle_data['players'][1]['position']
                }
            ],
            'arena_size': self.battle_data.get('arena_size', {'width': 5, 'height': 5}),
            'current_tick': self.current_tick,
            'max_ticks': self.battle_data.get('max_ticks', 150)
        }
        
        self._send_to_client(client_socket, json.dumps({
            'type': 'battle_info',
            'data': battle_info
        }))
    
    def _send_to_client(self, client_socket, message):
        """Send a message to a specific client"""
        try:
            # Check if this is a WebSocket client
            if client_socket in self.client_info and self.client_info[client_socket].get("is_websocket", False):
                self._send_websocket_message(client_socket, message)
            else:
                client_socket.send((message + '\n').encode('utf-8'))
        except Exception as e:
            print(f"{Fore.RED}Error sending to client: {e}")
            # Remove client on error
            self._remove_client(client_socket, [self.server_socket] + self.clients)
    
    def _send_websocket_message(self, client_socket, message):
        """Send a message to a WebSocket client"""
        try:
            # Prepare the WebSocket frame
            # Text frame, FIN bit set
            frame = bytearray([0x81])
            
            # Set payload length
            payload_bytes = message.encode('utf-8')
            payload_length = len(payload_bytes)
            
            if payload_length < 126:
                frame.append(payload_length)
            elif payload_length < 65536:
                frame.append(126)
                frame.extend(payload_length.to_bytes(2, byteorder='big'))
            else:
                frame.append(127)
                frame.extend(payload_length.to_bytes(8, byteorder='big'))
            
            # Add payload
            frame.extend(payload_bytes)
            
            # Send the frame
            client_socket.send(frame)
        except Exception as e:
            print(f"{Fore.RED}Error sending WebSocket message: {e}")
            self._remove_client(client_socket, [self.server_socket] + self.clients)
    
    def _send_battle_info_ws(self, client_socket):
        """Send battle information to a WebSocket client"""
        try:
            if not self.battle_data:
                return
            
            # Create a message with the battle data
            message = {
                'type': 'battle_info',
                'data': self.battle_data
            }
            
            # Send as WebSocket message
            self._send_websocket_message(client_socket, json.dumps(message))
        except Exception as e:
            print(f"{Fore.RED}Error sending battle info via WebSocket: {e}")
    
    def broadcast(self, message):
        """Broadcast a message to all connected clients"""
        # Make a copy of the clients list to avoid modification during iteration
        clients_copy = self.clients.copy()
        
        for client in clients_copy:
            try:
                # Check if the socket is still valid
                if client.fileno() < 0:
                    self._remove_client(client, None)
                    continue
                
                # Send the message
                if isinstance(message, str):
                    # For text messages
                    if self._is_websocket(client):
                        self._send_websocket_message(client, message)
                    else:
                        client.send((message + '\n').encode('utf-8'))
                else:
                    # For binary messages
                    client.send(message)
            except Exception as e:
                print(f"{Fore.RED}Error broadcasting to client: {e}")
                self._remove_client(client, None)
    
    def _process_event_queue(self):
        """Process events in the queue safely"""
        try:
            # Process a limited number of events per cycle to prevent blocking
            max_events_per_cycle = 10
            events_processed = 0
            
            while not self.event_queue.empty() and events_processed < max_events_per_cycle:
                try:
                    event = self.event_queue.get(block=False)
                    
                    # Increment tick counter for certain events
                    if event.get('type') in ['attack', 'movement', 'special']:
                        self.current_tick += 1
                    
                    # Broadcast the event
                    self.broadcast(json.dumps({
                        'type': 'event',
                        'data': event
                    }))
                    
                    events_processed += 1
                    
                    # Small delay to prevent flooding clients
                    time.sleep(0.05)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"{Fore.RED}Error processing event queue: {e}")
    
    def set_battle_data(self, battle_data):
        """Set the current battle data and notify clients"""
        self.battle_data = battle_data
        self.current_tick = 0
        
        # Broadcast battle info to all clients
        self.broadcast(json.dumps({
            'type': 'battle_info',
            'data': battle_data
        }))
        
        print(f"{Fore.GREEN}Battle data set: {battle_data['players'][0]['name']} vs {battle_data['players'][1]['name']}")
    
    def add_event(self, event):
        """Add an event to the queue for broadcasting"""
        # Update player state based on event
        if event.get('type') == 'attack':
            # Update HP for the target player
            target = event.get('target')
            damage = event.get('damage', 0)
            
            for player in self.battle_data['players']:
                if player['name'] == target:
                    player['hp'] = max(0, player['hp'] - damage)
        
        elif event.get('type') == 'movement':
            # Update position for the moving player
            actor = event.get('actor')
            to_position = event.get('to_position')
            
            if actor and to_position:
                for player in self.battle_data['players']:
                    if player['name'] == actor:
                        player['position'] = to_position
        
        # Add event to queue
        self.event_queue.put(event)
        
        # Increment tick counter for certain events
        if event.get('type') in ['attack', 'movement', 'special']:
            self.current_tick += 1

    def _decode_websocket_frame(self, data, client_socket=None):
        """Decode a WebSocket frame and return the message"""
        try:
            # Basic WebSocket frame decoding
            if len(data) < 2:
                return None
            
            # Check FIN bit and opcode
            fin = (data[0] & 0x80) != 0
            opcode = data[0] & 0x0F
            
            # Handle different opcodes
            if opcode == 0x8:  # Close frame
                return None
            elif opcode == 0x9 and client_socket:  # Ping frame
                # Send pong frame
                self._send_websocket_pong(client_socket)
                return None
            elif opcode not in [0x1, 0x0]:  # Not a text or continuation frame
                return None
            
            # Get payload length
            mask = (data[1] & 0x80) != 0
            payload_length = data[1] & 0x7F
            
            # Determine header length
            header_length = 2
            if payload_length == 126:
                header_length += 2
                payload_length = int.from_bytes(data[2:4], byteorder='big')
            elif payload_length == 127:
                header_length += 8
                payload_length = int.from_bytes(data[2:10], byteorder='big')
            
            # Get masking key if present
            masking_key = None
            if mask:
                masking_key = data[header_length:header_length+4]
                header_length += 4
            
            # Get payload
            payload = data[header_length:header_length+payload_length]
            
            # Unmask payload if needed
            if mask and masking_key:
                unmasked = bytearray(payload_length)
                for i in range(payload_length):
                    unmasked[i] = payload[i] ^ masking_key[i % 4]
                payload = unmasked
            
            # Return decoded message
            return payload.decode('utf-8')
        
        except Exception as e:
            print(f"{Fore.RED}Error decoding WebSocket frame: {e}")
            return None

    def _send_websocket_pong(self, client_socket):
        """Send a WebSocket pong frame"""
        try:
            # Create pong frame (opcode 0xA)
            pong_frame = bytearray([0x8A, 0x00])
            client_socket.send(pong_frame)
        except Exception as e:
            print(f"{Fore.RED}Error sending WebSocket pong: {e}")

class SpectatorClient:
    """Client for connecting to a spectator server"""
    
    def __init__(self, host='localhost', port=5555):
        """Initialize the spectator client"""
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.running = False
        self.battle_data = None
        self.events = []
        self.visualizer = None
        
    def connect(self):
        """Connect to the spectator server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            print(f"{Fore.GREEN}Connected to spectator server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to spectator server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the spectator server"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.connected = False
        print(f"{Fore.YELLOW}Disconnected from spectator server")
    
    def _receive_messages(self):
        """Receive and process messages from the server"""
        buffer = ""
        
        while self.running:
            try:
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    # Server closed connection
                    break
                
                # Add to buffer and process complete messages
                buffer += data.decode('utf-8')
                
                # Process complete messages (separated by newlines)
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self._process_message(message)
                
            except Exception as e:
                print(f"{Fore.RED}Error receiving messages: {e}")
                break
        
        # Disconnected
        self.connected = False
        print(f"{Fore.YELLOW}Lost connection to spectator server")
    
    def _process_message(self, message):
        """Process a message from the server"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            message_data = data.get('data')
            
            if message_type == 'battle_start':
                # New battle started
                self.battle_data = message_data
                self.events = []
                print(f"{Fore.CYAN}New battle started: {message_data['players'][0]['name']} vs {message_data['players'][1]['name']}")
                
                # Initialize visualizer if needed
                if not self.visualizer:
                    arena_size = message_data.get('arena_size', {'width': 5, 'height': 5})
                    self.visualizer = EnhancedVisualizer(
                        width=arena_size['width'],
                        height=arena_size['height']
                    )
            
            elif message_type == 'event':
                # Battle event
                self.events.append(message_data)
                
                # Display event
                self._display_event(message_data)
            
            elif message_type == 'battle_info':
                # Battle information
                self.battle_data = message_data
                print(f"{Fore.CYAN}Battle info received:")
                print(f"  Players: {message_data['players'][0]['name']} vs {message_data['players'][1]['name']}")
                print(f"  Tick: {message_data['current_tick']}/{message_data['max_ticks']}")
            
            elif message_type == 'chat':
                # Chat message
                sender = message_data.get('sender', 'Unknown')
                chat_message = message_data.get('message', '')
                print(f"{Fore.MAGENTA}{sender}: {Fore.WHITE}{chat_message}")
            
            elif message_type == 'stats':
                # Spectator stats
                print(f"{Fore.CYAN}Spectator stats:")
                print(f"  Spectators: {message_data.get('spectators', 0)}")
                print(f"  Current tick: {message_data.get('current_tick', 0)}")
            
            elif message_type == 'help':
                # Help information
                print(f"{Fore.CYAN}Available commands:")
                for command in message_data.get('commands', []):
                    print(f"  {command}")
            
            elif message_type == 'error':
                # Error message
                print(f"{Fore.RED}Error: {message_data.get('message', 'Unknown error')}")
        
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error decoding message: {message}")
        except Exception as e:
            print(f"{Fore.RED}Error processing message: {e}")
    
    def _display_event(self, event):
        """Display a battle event using the visualizer"""
        if not self.visualizer or not self.battle_data:
            return
        
        event_type = event.get('type', '')
        message = event.get('message', '')
        
        # Update player data if available
        if 'players' in event:
            self.battle_data['players'] = event['players']
        
        # Create player objects for visualization
        class PlayerObj:
            def __init__(self, data):
                self.name = data['name']
                self.hp = data['hp']
                self.max_hp = data['max_hp']
                self.position = tuple(data['position'])
        
        player1 = PlayerObj(self.battle_data['players'][0])
        player2 = PlayerObj(self.battle_data['players'][1])
        
        # Render arena
        self.visualizer.render_arena([player1, player2])
        
        # Render event based on type
        if event_type == 'attack':
            attacker = player1 if event.get('actor') == player1.name else player2
            defender = player2 if attacker == player1 else player1
            damage = event.get('damage', 0)
            is_critical = 'critical' in message.lower()
            
            self.visualizer.render_attack(attacker, defender, damage, is_critical)
        
        elif event_type == 'movement':
            self.visualizer.render_event('movement', message)
        
        elif event_type == 'special':
            player = player1 if event.get('actor') == player1.name else player2
            move_name = event.get('move_name', 'Special Move')
            
            self.visualizer.render_special_move(player, move_name)
        
        elif event_type == 'victory' or 'wins' in message.lower():
            winner_name = event.get('winner', '')
            winner = player1 if winner_name == player1.name else player2
            
            self.visualizer.render_victory(winner)
        
        else:
            # Generic event
            self.visualizer.render_event(event_type, message)
    
    def send_message(self, message):
        """Send a message to the server"""
        if not self.connected:
            print(f"{Fore.RED}Not connected to spectator server")
            return False
        
        try:
            self.socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"{Fore.RED}Error sending message: {e}")
            self.connected = False
            return False

def run_spectator_server(port=5555):
    """Run a spectator server for a duel"""
    # Create and start the spectator server
    server = SpectatorServer(port=port)
    if not server.start():
        return
    
    try:
        # Run a duel simulation
        print(f"{Fore.CYAN}Running duel simulation with spectator mode...")
        
        # Custom player configurations
        player1_config = {
            "name": "0xEC",
            "hp": 99,
            "attack": 99,
            "strength": 99,
            "defense": 99,
            "position": [0, 0]
        }

        player2_config = {
            "name": "noLE",
            "hp": 99,
            "attack": 99,
            "strength": 99,
            "defense": 99,
            "position": [4, 4]
        }
        
        # Run the simulation
        result = run_duel_simulation(
            max_ticks=150,
            visualize=True,
            tick_duration_ms=500,  # Slower for spectators to follow
            player1_config=player1_config,
            player2_config=player2_config,
            enhanced_visuals=True
        )
        
        # Set battle data for the server
        battle_data = {
            'players': [
                {
                    'name': player1_config['name'],
                    'hp': player1_config['hp'],
                    'max_hp': player1_config['hp'],
                    'position': player1_config['position']
                },
                {
                    'name': player2_config['name'],
                    'hp': player2_config['hp'],
                    'max_hp': player2_config['hp'],
                    'position': player2_config['position']
                }
            ],
            'arena_size': {'width': 5, 'height': 5},
            'max_ticks': 150
        }
        server.set_battle_data(battle_data)
        
        # Lock betting when the duel starts
        server.betting_integration.lock_betting()
        
        # Broadcast events
        for event in result.get('events', []):
            # Add a small delay to simulate real-time
            time.sleep(0.5)
            server.add_event(event)
        
        # Settle betting when the duel ends
        server.betting_integration.settle_duel(result.get('winner', 'Unknown'))
        
        # Broadcast battle end
        server.broadcast(json.dumps({
            'type': 'battle_end',
            'data': {
                'winner': result.get('winner', 'Unknown'),
                'duration': len(result.get('events', [])),
                'timestamp': datetime.now().isoformat()
            }
        }))
        
        print(f"\n{Fore.GREEN}Battle finished. Winner: {result.get('winner', 'Unknown')}")
        print(f"{Fore.YELLOW}Spectator server still running. Press Ctrl+C to stop.")
        
        # Keep server running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping spectator server...")
    finally:
        server.stop()

def run_spectator_client(host='localhost', port=5555):
    """Run a spectator client to watch a duel"""
    # Create and connect the spectator client
    client = SpectatorClient(host=host, port=port)
    if not client.connect():
        return
    
    try:
        print(f"{Fore.CYAN}Connected as spectator. Waiting for battle...")
        print(f"{Fore.CYAN}Type messages to chat, or commands starting with '/'")
        
        # Main client loop
        while client.connected:
            # Get user input
            user_input = input()
            
            # Send to server
            if user_input:
                client.send_message(user_input)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Disconnecting from spectator server...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DuelSim Spectator Mode")
    parser.add_argument("--server", action="store_true", help="Run as spectator server")
    parser.add_argument("--client", action="store_true", help="Run as spectator client")
    parser.add_argument("--host", default="localhost", help="Server hostname (for client mode)")
    parser.add_argument("--port", type=int, default=5555, help="Server port")
    
    args = parser.parse_args()
    
    if args.server:
        run_spectator_server(port=args.port)
    elif args.client:
        run_spectator_client(host=args.host, port=args.port)
    else:
        print(f"{Fore.YELLOW}Please specify --server or --client mode")
        parser.print_help() 