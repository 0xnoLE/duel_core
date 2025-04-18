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

# Import the WebSocket server implementation
from websocket_server import WebSocketServer

# Initialize colorama for cross-platform color support
init(autoreset=True)

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