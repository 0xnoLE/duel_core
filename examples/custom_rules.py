"""
Example of running a duel with custom rules
"""
from duelsim import run_duel_simulation

# Custom rules configuration
custom_rules = {
    "allow_melee": True,
    "allow_ranged": False,  # Disable ranged attacks
    "allow_magic": False,   # Disable magic attacks
    "no_food": True,        # No healing
    "arena_size": {"width": 7, "height": 7},  # Larger arena
    "starting_positions": [[0, 0], [6, 6]]    # Start players further apart
}

# Custom player configurations
player1 = {
    "name": "Tank",
    "hp": 120,
    "attack": 70,
    "strength": 80,
    "defense": 80
}

player2 = {
    "name": "Striker",
    "hp": 80,
    "attack": 90,
    "strength": 90,
    "defense": 50
}

# Run simulation with custom settings
result = run_duel_simulation(
    max_ticks=200,
    visualize=True,
    tick_duration_ms=250,
    player1_config=player1,
    player2_config=player2,
    rules_config=custom_rules
)

# Print the result
print(f"Simulation completed with winner: {result['winner']}") 