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
import base64
import hashlib
import struct
import re

# Initialize colorama for cross-platform color support
init(autoreset=True)

class WebSocketServer:
    """WebSocket server implementation"""
    
    def __init__(self, port=5556, ping_interval=30):
        self.port = port
        self.server_socket = None
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.running = False
        self.ping_interval = ping_interval
        self.battle_data = None
        self.betting_manager = None
        self.betting_integration = None
        
    def start(self):
        """Start the WebSocket server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"{Fore.GREEN}WebSocket server started on port {self.port}")
            
            # Start the thread that accepts new client connections
            self._accept_thread = threading.Thread(target=self._accept_clients)
            self._accept_thread.daemon = True
            self._accept_thread.start()
            
            # Start the keep-alive thread
            self.keep_alive_thread = threading.Thread(target=self._send_keep_alive)
            self.keep_alive_thread.daemon = True
            self.keep_alive_thread.start()
            
            return True
        except Exception as e:
            print(f"{Fore.RED}Error starting WebSocket server: {e}")
            return False
    
    def stop(self):
        """Stop the WebSocket server"""
        print(f"{Fore.YELLOW}Stopping WebSocket server...")
        self.running = False
        
        # Close the server socket
        if self.server_socket:
            try:
                if hasattr(self.server_socket, 'fileno') and self.server_socket.fileno() != -1:
                    self.server_socket.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno not in [107, 9, 10057]:
                    print(f"{Fore.RED}Error shutting down server socket: {e}")
            finally:
                self.server_socket.close()
                self.server_socket = None
        
        # Close all client connections
        with self.clients_lock:
            print(f"{Fore.YELLOW}Closing {len(self.clients)} client connections...")
            for client_socket in list(self.clients.keys()):
                try:
                    self._send_close_frame(client_socket)
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        print(f"{Fore.GREEN}WebSocket server stopped.")
    
    def _accept_clients(self):
        """Accept new client connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(60)
                
                # Start a thread to handle this client
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
            except OSError as e:
                if not self.running:
                    break
                print(f"{Fore.RED}Error accepting client: {e}")
                time.sleep(0.1)
    
    def _handle_client(self, client_socket, addr):
        """Handle a client connection"""
        try:
            # Handle WebSocket handshake
            if not self._handle_handshake(client_socket):
                print(f"{Fore.RED}WebSocket handshake failed for {addr}")
                client_socket.close()
                return
            
            # Add client to clients list
            with self.clients_lock:
                self.clients[client_socket] = {
                    'address': addr,
                    'connected_at': time.time(),
                    'last_ping': time.time()
                }
            
            print(f"{Fore.GREEN}New spectator connected: {addr}")
            
            # Send battle data if available
            if self.battle_data:
                try:
                    battle_info = json.dumps({
                        'type': 'battle_info',
                        'data': self.battle_data
                    })
                    self._send_message(client_socket, battle_info)
                    print(f"{Fore.CYAN}Sent battle data to new client: {addr}")
                except Exception as e:
                    print(f"{Fore.RED}Error sending battle data to new client: {e}")
            
            # Main client loop
            buffer = bytearray()
            while self.running:
                try:
                    # Use select to check if data is available
                    ready = select.select([client_socket], [], [], 1.0)
                    if ready[0]:
                        data = client_socket.recv(4096)
                        if not data:
                            print(f"{Fore.YELLOW}Client {addr} closed connection")
                            break
                        
                        buffer.extend(data)
                        
                        # Process WebSocket frames
                        while len(buffer) >= 2:
                            # Process a complete WebSocket frame
                            result, frame_length, message = self._decode_frame(buffer)
                            
                            if result is False:
                                # Need more data
                                break
                            
                            # Remove the processed frame from buffer
                            buffer = buffer[frame_length:]
                            
                            # Handle the frame
                            if result == 'close':
                                print(f"{Fore.YELLOW}Received close frame from {addr}")
                                self._send_close_frame(client_socket)
                                return
                            elif result == 'ping':
                                self._send_pong_frame(client_socket, message)
                            elif result == 'pong':
                                with self.clients_lock:
                                    if client_socket in self.clients:
                                        self.clients[client_socket]['last_ping'] = time.time()
                            elif result == 'text':
                                # Handle text message
                                try:
                                    if message == 'pong':
                                        with self.clients_lock:
                                            if client_socket in self.clients:
                                                self.clients[client_socket]['last_ping'] = time.time()
                                    else:
                                        print(f"{Fore.CYAN}Received from {addr}: {message[:50]}...")
                                        # Process client message here
                                except Exception as e:
                                    print(f"{Fore.RED}Error processing message from {addr}: {e}")
                
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    print(f"{Fore.YELLOW}Connection reset by {addr}")
                    break
                except OSError as e:
                    print(f"{Fore.RED}Socket error with {addr}: {e}")
                    break
        
        except Exception as e:
            print(f"{Fore.RED}Unexpected error in client handler for {addr}: {e}")
        
        finally:
            # Remove client from clients list
            with self.clients_lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"{Fore.YELLOW}Spectator disconnected: {addr}")
    
    def _handle_handshake(self, client_socket):
        """Handle WebSocket handshake"""
        try:
            # Receive HTTP request
            data = client_socket.recv(4096).decode('utf-8')
            
            # Check if it's a valid WebSocket handshake request
            if "Upgrade: websocket" not in data:
                print(f"{Fore.RED}Not a WebSocket handshake request")
                return False
            
            # Extract the Sec-WebSocket-Key
            key = re.search(r'Sec-WebSocket-Key: (.*)\r\n', data)
            if not key:
                print(f"{Fore.RED}No Sec-WebSocket-Key found")
                return False
            
            key = key.group(1).strip()
            
            # Create the response key
            response_key = self._generate_handshake_key(key)
            
            # Create handshake response
            handshake = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {response_key}\r\n"
                "\r\n"
            )
            
            # Send handshake response
            client_socket.sendall(handshake.encode('utf-8'))
            
            return True
        
        except Exception as e:
            print(f"{Fore.RED}Error in handshake: {e}")
            return False
    
    def _generate_handshake_key(self, key):
        """Generate the handshake response key"""
        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        hash_key = key + GUID
        sha1 = hashlib.sha1(hash_key.encode('utf-8')).digest()
        return base64.b64encode(sha1).decode('utf-8')
    
    def _decode_frame(self, buffer):
        """Decode a WebSocket frame"""
        if len(buffer) < 2:
            return False, 0, None
        
        # Get the first byte
        b1 = buffer[0]
        fin = (b1 & 0x80) != 0
        opcode = b1 & 0x0F
        
        # Get the second byte
        b2 = buffer[1]
        mask = (b2 & 0x80) != 0
        payload_len = b2 & 0x7F
        
        # Determine the header length
        header_len = 2
        if payload_len == 126:
            if len(buffer) < 4:
                return False, 0, None
            payload_len = struct.unpack(">H", buffer[2:4])[0]
            header_len = 4
        elif payload_len == 127:
            if len(buffer) < 10:
                return False, 0, None
            payload_len = struct.unpack(">Q", buffer[2:10])[0]
            header_len = 10
        
        # Check if we have enough data
        if mask:
            if len(buffer) < header_len + 4:
                return False, 0, None
            mask_key = buffer[header_len:header_len+4]
            header_len += 4
        
        # Check if we have the full frame
        if len(buffer) < header_len + payload_len:
            return False, 0, None
        
        # Extract the payload
        payload = buffer[header_len:header_len+payload_len]
        
        # Unmask the payload if needed
        if mask:
            payload = bytearray(payload)
            for i in range(len(payload)):
                payload[i] ^= mask_key[i % 4]
        
        # Handle different opcodes
        if opcode == 0x8:  # Close
            return 'close', header_len + payload_len, None
        elif opcode == 0x9:  # Ping
            return 'ping', header_len + payload_len, payload
        elif opcode == 0xA:  # Pong
            return 'pong', header_len + payload_len, payload
        elif opcode == 0x1:  # Text
            return 'text', header_len + payload_len, payload.decode('utf-8')
        elif opcode == 0x2:  # Binary
            return 'binary', header_len + payload_len, payload
        else:
            return 'unknown', header_len + payload_len, payload
    
    def _send_message(self, client_socket, message):
        """Send a text message to a client"""
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        # Create frame header
        header = bytearray()
        
        # Set fin and opcode (0x01 for text)
        header.append(0x81)
        
        # Set payload length
        if len(message) < 126:
            header.append(len(message))
        elif len(message) < 65536:
            header.append(126)
            header.extend(struct.pack(">H", len(message)))
        else:
            header.append(127)
            header.extend(struct.pack(">Q", len(message)))
        
        # Send the frame
        try:
            client_socket.sendall(header + message)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error sending message: {e}")
            return False
    
    def _send_ping_frame(self, client_socket):
        """Send a ping frame to a client"""
        try:
            # Simple ping frame (FIN=1, Opcode=9, Length=0)
            client_socket.sendall(b'\x89\x00')
            return True
        except Exception as e:
            print(f"{Fore.RED}Error sending ping: {e}")
            return False
    
    def _send_pong_frame(self, client_socket, payload=b''):
        """Send a pong frame to a client"""
        try:
            # Simple pong frame (FIN=1, Opcode=10, Length=len(payload))
            header = bytearray([0x8A, len(payload)])
            client_socket.sendall(header + payload)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error sending pong: {e}")
            return False
    
    def _send_close_frame(self, client_socket):
        """Send a close frame to a client"""
        try:
            # Simple close frame (FIN=1, Opcode=8, Length=2, Status=1000)
            client_socket.sendall(b'\x88\x02\x03\xe8')
            return True
        except Exception as e:
            print(f"{Fore.RED}Error sending close frame: {e}")
            return False
    
    def _send_keep_alive(self):
        """Send periodic ping frames to keep connections alive"""
        while self.running:
            try:
                with self.clients_lock:
                    current_time = time.time()
                    clients_to_remove = []
                    
                    for client_socket, client_info in list(self.clients.items()):
                        # Check if client hasn't responded to pings for too long
                        if current_time - client_info['last_ping'] > self.ping_interval * 2:
                            print(f"{Fore.YELLOW}Client {client_info['address']} timed out, removing")
                            clients_to_remove.append(client_socket)
                            continue
                        
                        # Send ping to client
                        if current_time - client_info['last_ping'] > self.ping_interval:
                            if not self._send_ping_frame(client_socket):
                                clients_to_remove.append(client_socket)
                    
                    # Remove disconnected clients
                    for client_socket in clients_to_remove:
                        try:
                            client_socket.close()
                        except:
                            pass
                        if client_socket in self.clients:
                            del self.clients[client_socket]
            
            except Exception as e:
                print(f"{Fore.RED}Error in keep-alive thread: {e}")
            
            # Sleep until next ping interval
            time.sleep(self.ping_interval / 2)
    
    def broadcast(self, message):
        """Broadcast a message to all connected clients"""
        with self.clients_lock:
            clients_to_remove = []
            client_count = len(self.clients)
            success_count = 0
            
            for client_socket, client_info in list(self.clients.items()):
                if self._send_message(client_socket, message):
                    success_count += 1
                else:
                    clients_to_remove.append(client_socket)
            
            # Remove disconnected clients
            for client_socket in clients_to_remove:
                try:
                    client_socket.close()
                except:
                    pass
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            if client_count > 0:
                print(f"{Fore.CYAN}Broadcast message to {success_count}/{client_count} clients")
    
    def set_battle_data(self, battle_data):
        """Set the current battle data and broadcast to clients"""
        self.battle_data = battle_data
        print(f"{Fore.CYAN}Battle data set: {battle_data['players'][0]['name']} vs {battle_data['players'][1]['name']}")
        
        # Broadcast battle info to all clients
        self.broadcast(json.dumps({
            'type': 'battle_info',
            'data': battle_data
        }))
    
    def add_event(self, event):
        """Add an event to the battle and broadcast it"""
        self.broadcast(json.dumps({
            'type': 'event',
            'data': event
        }))


# For backward compatibility, create a SpectatorServer class that inherits from WebSocketServer
class SpectatorServer(WebSocketServer):
    """Server that broadcasts duel events to connected spectators"""
    
    def __init__(self, port=5556):
        super().__init__(port=port)
        
        # Initialize betting manager (placeholder)
        class DummyBettingManager:
            def place_bet(self, *args, **kwargs):
                return {"success": False, "error": "Betting not implemented"}
            
            def get_user_balance(self, *args, **kwargs):
                return 0
            
            def get_user_bets(self, *args, **kwargs):
                return []
            
            def settle_duel(self, *args, **kwargs):
                return {"success": False, "error": "Betting not implemented"}
        
        class DummyBettingIntegration:
            def __init__(self, server, manager):
                self.spectator_server = server
                self.betting_manager = manager
                self.current_duel_id = None
                self.current_pool = None
            
            def lock_betting(self):
                pass
            
            def settle_duel(self, winner_name):
                pass
        
        self.betting_manager = DummyBettingManager()
        self.betting_integration = DummyBettingIntegration(self, self.betting_manager)

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