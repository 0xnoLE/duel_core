"""
DuelSim Game Runner

This script provides a convenient way to run duels that can be spectated.
"""

import argparse
import json
import time
import random
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the duel simulation and spectator mode
from duelsim import run_duel_simulation
from spectator_mode import SpectatorServer

def generate_random_name():
    """Generate a random player name"""
    prefixes = ["Dark", "Light", "Swift", "Mighty", "Shadow", "Flame", "Ice", "Storm", "Ancient", "Mystic"]
    suffixes = ["Blade", "Fist", "Knight", "Warrior", "Mage", "Hunter", "Slayer", "Master", "Lord", "Champion"]
    return f"{random.choice(prefixes)}{random.choice(suffixes)}"

def run_duel(player1_name=None, player2_name=None, spectator_port=5555, max_ticks=150, 
             tick_duration=500, auto_start=False):
    """Run a duel with the specified parameters"""
    # Use random names if not provided
    player1_name = player1_name or generate_random_name()
    player2_name = player2_name or generate_random_name()
    
    print(f"{Fore.CYAN}Setting up duel: {Fore.YELLOW}{player1_name} {Fore.WHITE}vs {Fore.MAGENTA}{player2_name}")
    
    # Create and start the spectator server
    server = SpectatorServer(port=spectator_port)
    if not server.start():
        print(f"{Fore.RED}Failed to start spectator server. Exiting.")
        return
    
    print(f"{Fore.GREEN}Spectator server started on port {spectator_port}")
    print(f"{Fore.YELLOW}Waiting for spectators to connect...")
    
    # Wait for spectators if not auto-starting
    if not auto_start:
        input(f"{Fore.CYAN}Press Enter to start the duel...")
    else:
        # Wait a few seconds for spectators to connect
        for i in range(5, 0, -1):
            print(f"{Fore.YELLOW}Starting duel in {i} seconds...")
            time.sleep(1)
    
    try:
        # Custom player configurations
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
        
        print(f"{Fore.CYAN}Player 1: {json.dumps(player1_config)}")
        print(f"{Fore.MAGENTA}Player 2: {json.dumps(player2_config)}")
        
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
        server.set_battle_data(battle_data)
        
        # Lock betting when the duel starts
        server.betting_integration.lock_betting()
        
        print(f"{Fore.GREEN}Running duel simulation...")
        
        # Run the simulation
        result = run_duel_simulation(
            max_ticks=max_ticks,
            visualize=True,
            tick_duration_ms=tick_duration,
            player1_config=player1_config,
            player2_config=player2_config,
            enhanced_visuals=True
        )
        
        # Broadcast events
        for event in result.get('events', []):
            # Add a small delay to simulate real-time
            time.sleep(tick_duration / 1000)
            server.add_event(event)
        
        # Settle betting when the duel ends
        server.betting_integration.settle_duel(result.get('winner', 'Unknown'))
        
        print(f"\n{Fore.GREEN}Battle finished. Winner: {Fore.YELLOW}{result.get('winner', 'Unknown')}")
        print(f"{Fore.CYAN}Total events: {len(result.get('events', []))}")
        print(f"{Fore.YELLOW}Spectator server still running. Press Ctrl+C to stop.")
        
        # Keep server running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping spectator server...")
    finally:
        server.stop()

def main():
    """Main function to parse arguments and run a duel"""
    parser = argparse.ArgumentParser(description='Run a DuelSim duel with spectator support')
    parser.add_argument('--player1', type=str, help='Name for player 1')
    parser.add_argument('--player2', type=str, help='Name for player 2')
    parser.add_argument('--port', type=int, default=5556, help='Port for the spectator server')
    parser.add_argument('--max-ticks', type=int, default=150, help='Maximum number of ticks for the duel')
    parser.add_argument('--tick-duration', type=int, default=500, help='Duration of each tick in milliseconds')
    parser.add_argument('--auto-start', action='store_true', help='Start the duel automatically without waiting')
    
    args = parser.parse_args()
    
    run_duel(
        player1_name=args.player1,
        player2_name=args.player2,
        spectator_port=args.port,
        max_ticks=args.max_ticks,
        tick_duration=args.tick_duration,
        auto_start=args.auto_start
    )

if __name__ == "__main__":
    main() 