from duelsim import run_duel_simulation
import json
import random
import os
try:
    from tabulate import tabulate
except ImportError:
    print("Please install tabulate: pip install tabulate")
    exit()

class Tournament:
    def __init__(self, players, rules_config=None, rounds=3):
        self.players = players
        self.rules_config = rules_config
        self.rounds = rounds
        self.results = {}

        # Initialize scores
        for player in players:
            self.results[player["name"]] = {
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0
            }

    def run_match(self, player1, player2, match_id):
        """Run a single match between two players"""
        print(f"\n=== MATCH {match_id}: {player1['name']} vs {player2['name']} ===")

        # Use the imported run_duel_simulation function
        result = run_duel_simulation(
            max_ticks=150,
            visualize=False,  # Keep headless for tournaments usually
            player1_config=player1,
            player2_config=player2,
            rules_config=self.rules_config
        )

        # ... (rest of run_match remains the same) ...

    # ... (run_tournament and display_standings remain the same) ...


if __name__ == "__main__":
    # Define tournament participants
    players = [
        {"name": "Warrior", "hp": 110, "attack": 75, "strength": 80, "defense": 70},
        {"name": "Mage", "hp": 85, "attack": 90, "strength": 60, "defense": 50},
        {"name": "Rogue", "hp": 95, "attack": 85, "strength": 70, "defense": 60},
        {"name": "Paladin", "hp": 105, "attack": 70, "strength": 75, "defense": 80},
        {"name": "Ranger", "hp": 90, "attack": 80, "strength": 75, "defense": 65},
        {"name": "Monk", "hp": 100, "attack": 75, "strength": 70, "defense": 75}
    ]

    # Load custom rules (assuming custom_config.json exists)
    rules = None
    try:
        with open("custom_config.json", "r") as f:
            rules = json.load(f)
        print("Loaded custom rules from custom_config.json")
    except FileNotFoundError:
        print("custom_config.json not found, using default rules.")
    except json.JSONDecodeError:
        print("Error decoding custom_config.json, using default rules.")


    # Run tournament
    tournament = Tournament(players, rules, rounds=2)
    tournament.run_tournament() 