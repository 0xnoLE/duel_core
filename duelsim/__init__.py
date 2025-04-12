"""
DuelSim - A turn-based duel simulation engine
"""

__version__ = "0.1.0"

# Only export the main function
def run_duel_simulation(max_ticks=150, visualize=True, tick_duration_ms=300,
                        player1_config=None, player2_config=None, rules_config=None):
    """
    Simplified simulation function for demonstration
    """
    print("Running duel simulation...")
    
    # Default player configs
    default_p1 = {"name": "Fighter1", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    default_p2 = {"name": "Fighter2", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    
    # Apply custom configs if provided
    if player1_config:
        default_p1.update(player1_config)
    if player2_config:
        default_p2.update(player2_config)
    
    # Simulate a simple game where player1 always wins
    return {
        "winner": default_p1["name"],
        "events": [
            {"tick": 1, "message": f"{default_p1['name']} attacks {default_p2['name']}"},
            {"tick": 10, "message": f"{default_p2['name']} is defeated!"}
        ],
        "final_state": {
            "player1": default_p1,
            "player2": default_p2,
            "ticks": 10
        }
    } 