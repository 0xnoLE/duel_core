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
        print("Duel manager started")
    
    def stop(self):
        """Stop the duel manager"""
        self.running = False
        print("Duel manager stopped")
    
    def queue_duel(self, player1_name=None, player2_name=None, max_ticks=150, tick_duration=500):
        """Queue a duel between two players"""
        player1_name = player1_name or self._generate_random_name()
        player2_name = player2_name or self._generate_random_name()
        duel_id = f"0x{random.randint(0, 255):02X}"
        duel_config = {
            'id': duel_id,
            'player1_name': player1_name,
            'player2_name': player2_name,
            'max_ticks': max_ticks,
            'tick_duration': tick_duration,
            'queued_at': time.time()
        }
        self.duel_queue.put(duel_config)
        print(f"Queued duel {duel_id}: {player1_name} vs {player2_name}")
        return duel_id
    
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
        try:
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
            
            # Check if we have active spectators before starting
            active_spectators = len(self.spectator_server.clients) if hasattr(self.spectator_server, 'clients') else 0
            if active_spectators == 0:
                print("Warning: No active spectators. Waiting for connections...")
                # Wait a bit for spectators to connect
                for i in range(5):
                    time.sleep(1)
                    active_spectators = len(self.spectator_server.clients) if hasattr(self.spectator_server, 'clients') else 0
                    if active_spectators > 0:
                        print(f"Spectators connected ({active_spectators}). Starting duel...")
                        break
            
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
            print(f"Error running duel: {e}")
            import traceback
            traceback.print_exc()
            
            # Broadcast error event
            self.spectator_server.broadcast(json.dumps({
                'type': 'duel_error',
                'data': {
                    'message': f"Error running duel: {e}",
                    'timestamp': time.time()
                }
            }))
        
        finally:
            # Always clear current duel
            self.current_duel = None
    
    def _generate_random_name(self):
        """Generate a random player name"""
        prefixes = ["Dark", "Light", "Swift", "Mighty", "Shadow", "Flame", "Ice", "Storm", "Ancient", "Mystic"]
        suffixes = ["Blade", "Fist", "Knight", "Warrior", "Mage", "Hunter", "Slayer", "Master", "Lord", "Champion"]
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def get_random_fighters(self, count=2):
        """Get a list of random fighter names"""
        import random
        from fighters import FIGHTER_CLASSES
        
        # Get all available fighter names
        fighter_names = list(FIGHTER_CLASSES.keys())
        
        # Shuffle and return the requested number
        random.shuffle(fighter_names)
        return fighter_names[:min(count, len(fighter_names))]

    def start_next_duel(self):
        """Start the next duel in the queue"""
        if self.current_duel:
            print("A duel is already in progress")
            return False
        
        try:
            # Get the next duel from the queue
            if self.duel_queue.empty():
                print("No duels in queue")
                return False
            
            duel_config = self.duel_queue.get(block=False)
            
            # Create fighters
            player1_name = duel_config.get('player1_name')
            player2_name = duel_config.get('player2_name')
            
            # Check if we have valid fighter names
            if not player1_name or not player2_name:
                print(f"Invalid fighter names: {player1_name} vs {player2_name}")
                return False
            
            # Get fighter classes
            from fighters import FIGHTER_CLASSES
            
            # Check if the fighter names are valid
            if player1_name not in FIGHTER_CLASSES:
                print(f"Unknown fighter class: {player1_name}")
                return False
            
            if player2_name not in FIGHTER_CLASSES:
                print(f"Unknown fighter class: {player2_name}")
                return False
            
            # Create fighter instances
            player1 = FIGHTER_CLASSES[player1_name]()
            player2 = FIGHTER_CLASSES[player2_name]()
            
            # Set initial positions
            player1.position = [0, 0]
            player2.position = [4, 4]
            
            # Set up the duel
            self.current_duel = {
                'id': duel_config.get('id'),
                'players': [player1, player2],
                'max_ticks': duel_config.get('max_ticks', 150),
                'tick_duration': duel_config.get('tick_duration', 500),
                'current_tick': 0,
                'started_at': time.time(),
                'events': []
            }
            
            # Broadcast battle start event
            self._broadcast_battle_start()
            
            # Start the duel thread and pass duel_config
            self.duel_thread = threading.Thread(target=self._run_duel, args=(duel_config,))
            self.duel_thread.daemon = True
            self.duel_thread.start()
            
            return True
        
        except Exception as e:
            print(f"Error starting duel: {e}")
            import traceback
            traceback.print_exc()
            return False 

    def _broadcast_battle_start(self):
        """Broadcast the start of a battle"""
        if not self.current_duel or not self.spectator_server:
            return

        player1 = self.current_duel['players'][0]
        player2 = self.current_duel['players'][1]

        battle_data = {
            'type': 'battle_start',
            'data': {
                'duel_id': self.current_duel['id'],
                'players': [player1.to_dict(), player2.to_dict()],
                'arena_size': {'width': 5, 'height': 5}, # Assuming 5x5 arena
                'max_ticks': self.current_duel['max_ticks'],
                'timestamp': time.time()
            }
        }
        self.spectator_server.broadcast(json.dumps(battle_data))
        print(f"Broadcasted battle_start for duel {self.current_duel['id']}")

    def _broadcast_tick_event(self, event):
         """Broadcast a single tick event"""
         if not self.spectator_server:
             return

         # Add player state to the event for the client
         if self.current_duel:
             player1 = self.current_duel['players'][0]
             player2 = self.current_duel['players'][1]
             event['player_state'] = {
                 player1.name: player1.to_dict(),
                 player2.name: player2.to_dict()
             }

         tick_data = {
             'type': 'battle_tick',
             'data': event
         }
         self.spectator_server.broadcast(json.dumps(tick_data))

    def _broadcast_battle_end(self, winner_name):
        """Broadcast the end of a battle"""
        if not self.spectator_server:
             return

        end_data = {
            'type': 'battle_end',
            'data': {
                'duel_id': self.current_duel['id'] if self.current_duel else 'unknown',
                'winner': winner_name,
                'timestamp': time.time()
            }
        }
        self.spectator_server.broadcast(json.dumps(end_data))
        print(f"Broadcasted battle_end. Winner: {winner_name}") 