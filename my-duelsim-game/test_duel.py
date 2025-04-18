"""
Test script to run a duel and verify WebSocket communication
"""

import os
import sys
import time
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spectator_mode import SpectatorServer
from duel_manager import DuelManager
from fighters import FIGHTER_CLASSES

def main():
    """Run a test duel"""
    print("Starting test duel...")
    
    # Start the spectator server
    server = SpectatorServer(port=5556)
    if not server.start():
        print("Failed to start spectator server")
        return
    
    print("Spectator server started on port 5556")
    
    # Create the duel manager
    duel_manager = DuelManager(server)
    duel_manager.start()
    
    print("Duel manager started")
    
    # Get random fighters
    fighter_names = list(FIGHTER_CLASSES.keys())
    random.shuffle(fighter_names)
    player1 = fighter_names[0]
    player2 = fighter_names[1]
    
    print(f"Starting duel: {player1} vs {player2}")
    
    # Queue and start the duel
    duel_id = duel_manager.queue_duel(player1, player2)
    
    # Start the duel
    if duel_manager.start_next_duel():
        print(f"Duel started with ID: {duel_id}")
    else:
        print("Failed to start duel")
        duel_manager.stop()
        server.stop()
        return
    
    print("Waiting for duel to complete...")
    
    # Wait for the duel to complete
    while duel_manager.current_duel:
        time.sleep(1)
    
    print("Duel completed")
    
    # Clean up
    duel_manager.stop()
    server.stop()
    
    print("Test completed")

if __name__ == "__main__":
    main() 