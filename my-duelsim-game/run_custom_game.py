"""
Custom game runner that works with the installed duelsim package
"""
from duelsim import run_duel_simulation
import json
import os

def load_custom_config(filename="custom_config.json"):
    """Load custom configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {filename}, using default config")
        return {}

def run_custom_game():
    """Run a game with custom configuration"""
    # Load custom configuration
    config = load_custom_config()

    # Custom player configurations
    player1_config = {
        "name": "0xEC",
        "hp": 99,
        "attack": 99,
        "strength": 99,
        "defense": 99
    }

    player2_config = {
        "name": "noLE",
        "hp": 99,
        "attack": 99,
        "strength":99,
        "defense": 99
    }

    # Run the simulation using the imported function
    result = run_duel_simulation(
        max_ticks=200,
        visualize=True,
        tick_duration_ms=250,
        player1_config=player1_config,
        player2_config=player2_config,
        rules_config=config
    )

    # Save the result to a file
    with open("game_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nCustom game finished. Winner: {result['winner']}")
    print(f"Result saved to game_result.json")

    return result

if __name__ == "__main__":
    run_custom_game() 