"""
WebSocket Server Implementation for DuelSim

This module provides a proper WebSocket server implementation that handles
the WebSocket protocol correctly, including handshake and framing.
"""

import socket
import threading
import json
import time
import select
import base64
import hashlib
import struct
import re
from colorama import Fore, init

# Initialize colorama
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
    
    def _handle_handshake(self, client_socket):
        """Handle WebSocket handshake"""
        data = client_socket.recv(1024).decode('utf-8')
        
        if not data:
            return False
        
        # Extract the WebSocket key
        key = ''
        for line in data.split('\r\n'):
            if line.startswith('Sec-WebSocket-Key:'):
                key = line.split(':', 1)[1].strip()
                break
        
        if not key:
            return False
        
        # Create the WebSocket accept key
        accept_key = base64.b64encode(
            hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('utf-8')).digest()
        ).decode('utf-8')
        
        # Send the handshake response
        response = (
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {accept_key}\r\n'
            '\r\n'
        )
        
        client_socket.sendall(response.encode('utf-8'))
        return True
    
    def _decode_frame(self, data):
        """Decode a WebSocket frame"""
        if len(data) < 2:
            return False, 0, None
        
        # Get the first byte
        b1 = data[0]
        fin = (b1 & 0x80) != 0
        opcode = b1 & 0x0F
        
        # Get the second byte
        b2 = data[1]
        mask = (b2 & 0x80) != 0
        payload_len = b2 & 0x7F
        
        # Determine the header length
        header_len = 2
        if payload_len == 126:
            if len(data) < 4:
                return False, 0, None
            payload_len = struct.unpack(">H", data[2:4])[0]
            header_len = 4
        elif payload_len == 127:
            if len(data) < 10:
                return False, 0, None
            payload_len = struct.unpack(">Q", data[2:10])[0]
            header_len = 10
        
        # Check if we have enough data
        if mask:
            if len(data) < header_len + 4:
                return False, 0, None
            mask_key = data[header_len:header_len+4]
            header_len += 4
        
        # Check if we have the full frame
        if len(data) < header_len + payload_len:
            return False, 0, None
        
        # Extract the payload
        payload = data[header_len:header_len+payload_len]
        
        # Unmask the payload if needed
        if mask:
            payload = bytearray(payload)
            for i in range(len(payload)):
                payload[i] ^= mask_key[i % 4]
        
        # Handle different opcodes
        if opcode == 0x8:  # Close
            return 'close', header_len + payload_len, payload
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
                                        # Handle command
                                        command = message[1:]  # Remove the leading '/'
                                        
                                        if command == 'info':
                                            # Send battle info
                                            if self.battle_data:
                                                battle_info = json.dumps({
                                                    'type': 'battle_info',
                                                    'data': self.battle_data
                                                })
                                                self._send_message(client_socket, battle_info)
                                                print(f"{Fore.CYAN}Sent battle info to client on request")
                                        
                                        elif command == 'attack':
                                            # Simulate an attack event
                                            event = {
                                                'type': 'attack',
                                                'actor': self.battle_data['players'][0]['name'],
                                                'target': self.battle_data['players'][1]['name'],
                                                'tick': int(time.time()),
                                                'message': f"{self.battle_data['players'][0]['name']} attacks {self.battle_data['players'][1]['name']}!"
                                            }
                                            self.add_event(event)
                                            print(f"{Fore.CYAN}Simulated attack event")
                                        
                                        elif command == 'damage':
                                            # Simulate a damage event
                                            event = {
                                                'type': 'damage',
                                                'target': self.battle_data['players'][1]['name'],
                                                'damage': 10,
                                                'tick': int(time.time()),
                                                'message': f"{self.battle_data['players'][1]['name']} takes 10 damage!"
                                            }
                                            self.add_event(event)
                                            
                                            # Update battle data
                                            self.battle_data['players'][1]['hp'] -= 10
                                            self.set_battle_data(self.battle_data)
                                            print(f"{Fore.CYAN}Simulated damage event")
                                except Exception as e:
                                    print(f"{Fore.RED}Error processing message: {e}")
                
                except socket.timeout:
                    # Socket timeout, continue loop
                    continue
                except ConnectionResetError:
                    print(f"{Fore.YELLOW}Connection reset by {addr}")
                    break
                except OSError as e:
                    print(f"{Fore.RED}Socket error with {addr}: {e}")
                    break
        
        except Exception as e:
            print(f"{Fore.RED}Error handling client {addr}: {e}")
        
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
    
    def _send_message(self, client_socket, message):
        """Send a text message to a client"""
        if not isinstance(message, bytes):
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