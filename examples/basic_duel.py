"""
Basic example of running a duel simulation
"""
from duelsim import run_duel_simulation

# Run a basic duel with default settings
result = run_duel_simulation(max_ticks=150, visualize=True, tick_duration_ms=300)

# Print the result
print(f"Simulation completed with winner: {result['winner']}")
print(f"Total ticks: {result['final_state']['ticks']}") 