"""
DuelSim Duel Manager

This module manages duels that can be started from the web interface.
"""

import threading
import time
import random
import json
import queue
from colorama import Fore

from duelsim import run_duel_simulation

class DuelManager:
    """Manages duels for the web interface"""
    
    def __init__(self, spectator_server):
        """Initialize the duel manager"""
        self.spectator_server = spectator_server
        self.current_duel = None
        self.duel_thread = None
        self.duel_queue = queue.Queue()
        self.running = False
        
        # Start the duel processor thread
        self.processor_thread = threading.Thread(target=self._process_duels)
        self.processor_thread.daemon = True
        self.processor_thread.start()
    
    def start(self):
        """Start the duel manager"""
        self.running = True
        print(f"{Fore.GREEN}Duel manager started")
    
    def stop(self):
        """Stop the duel manager"""
        self.running = False
        print(f"{Fore.YELLOW}Duel manager stopped")
    
    def queue_duel(self, player1_name=None, player2_name=None, max_ticks=150, tick_duration=500):
        """Queue a duel to be run"""
        # Generate random names if not provided
        player1_name = player1_name or self._generate_random_name()
        player2_name = player2_name or self._generate_random_name()
        
        duel_config = {
            'player1_name': player1_name,
            'player2_name': player2_name,
            'max_ticks': max_ticks,
            'tick_duration': tick_duration,
            'queued_at': time.time()
        }
        
        self.duel_queue.put(duel_config)
        print(f"{Fore.CYAN}Duel queued: {player1_name} vs {player2_name}")
        
        # Broadcast duel queued event
        self.spectator_server.broadcast(json.dumps({
            'type': 'duel_queued',
            'data': {
                'player1': player1_name,
                'player2': player2_name,
                'position': self.duel_queue.qsize(),
                'estimated_start': time.time() + (self.duel_queue.qsize() * 60)  # Rough estimate
            }
        }))
        
        return duel_config
    
    def _process_duels(self):
        """Process duels from the queue"""
        while True:
            try:
                if not self.running:
                    time.sleep(1)
                    continue
                
                # Check if there's a duel in the queue and we're not currently running one
                if not self.duel_queue.empty() and self.current_duel is None:
                    duel_config = self.duel_queue.get()
                    self._run_duel(duel_config)
                
                time.sleep(0.5)
            except Exception as e:
                print(f"{Fore.RED}Error in duel processor: {e}")
                time.sleep(1)
    
    def _run_duel(self, duel_config):
        """Run a duel with the specified configuration"""
        self.current_duel = duel_config
        
        # Extract configuration
        player1_name = duel_config['player1_name']
        player2_name = duel_config['player2_name']
        max_ticks = duel_config['max_ticks']
        tick_duration = duel_config['tick_duration']
        
        print(f"{Fore.CYAN}Starting duel: {player1_name} vs {player2_name}")
        
        # Broadcast duel starting event
        self.spectator_server.broadcast(json.dumps({
            'type': 'duel_starting',
            'data': {
                'player1': player1_name,
                'player2': player2_name,
                'max_ticks': max_ticks,
                'tick_duration': tick_duration,
                'starting_in': 5  # Seconds
            }
        }))
        
        # Wait a few seconds before starting
        time.sleep(5)
        
        try:
            # Create player configurations
            player1_config = {
                "name": player1_name,
                "hp": random.randint(80, 120),
                "attack": random.randint(70, 100),
                "strength": random.randint(70, 100),
                "defense": random.randint(70, 100),
                "position": [0, 0]
            }

            player2_config = {
                "name": player2_name,
                "hp": random.randint(80, 120),
                "attack": random.randint(70, 100),
                "strength": random.randint(70, 100),
                "defense": random.randint(70, 100),
                "position": [4, 4]
            }
            
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
                'max_ticks': max_ticks
            }
            self.spectator_server.set_battle_data(battle_data)
            
            # Lock betting when the duel starts
            self.spectator_server.betting_integration.lock_betting()
            
            # Broadcast duel started event
            self.spectator_server.broadcast(json.dumps({
                'type': 'duel_started',
                'data': {
                    'player1': player1_config,
                    'player2': player2_config,
                    'max_ticks': max_ticks
                }
            }))
            
            # Run the simulation
            result = run_duel_simulation(
                max_ticks=max_ticks,
                visualize=False,  # Don't visualize in the console
                tick_duration_ms=tick_duration,
                player1_config=player1_config,
                player2_config=player2_config,
                enhanced_visuals=False
            )
            
            # Broadcast events
            for event in result.get('events', []):
                # Add a small delay to simulate real-time
                time.sleep(tick_duration / 1000)
                self.spectator_server.add_event(event)
            
            # Settle betting when the duel ends
            self.spectator_server.betting_integration.settle_duel(result.get('winner', 'Unknown'))
            
            # Broadcast duel ended event
            self.spectator_server.broadcast(json.dumps({
                'type': 'duel_ended',
                'data': {
                    'winner': result.get('winner', 'Unknown'),
                    'duration': len(result.get('events', [])),
                    'timestamp': time.time()
                }
            }))
            
            print(f"{Fore.GREEN}Duel finished: {player1_name} vs {player2_name}")
            print(f"{Fore.YELLOW}Winner: {result.get('winner', 'Unknown')}")
            
        except Exception as e:
            print(f"{Fore.RED}Error running duel: {e}")
            
            # Broadcast error event
            self.spectator_server.broadcast(json.dumps({
                'type': 'duel_error',
                'data': {
                    'message': f"Error running duel: {e}",
                    'timestamp': time.time()
                }
            }))
        
        finally:
            # Clear current duel
            self.current_duel = None
    
    def _generate_random_name(self):
        """Generate a random player name"""
        prefixes = ["Dark", "Light", "Swift", "Mighty", "Shadow", "Flame", "Ice", "Storm", "Ancient", "Mystic"]
        suffixes = ["Blade", "Fist", "Knight", "Warrior", "Mage", "Hunter", "Slayer", "Master", "Lord", "Champion"]
        return f"{random.choice(prefixes)}{random.choice(suffixes)}" 