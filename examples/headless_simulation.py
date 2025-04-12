"""
Example of running a headless simulation (no visualization)
"""
from duelsim import run_duel_simulation
import json

# Run 10 simulations and collect statistics
winners = {"Fighter1": 0, "Fighter2": 0, "draw": 0}
total_ticks = 0

for i in range(10):
    print(f"Running simulation {i+1}/10...")
    result = run_duel_simulation(max_ticks=150, visualize=False)
    winners[result["winner"]] += 1
    total_ticks += result["final_state"]["ticks"]

# Print statistics
print("\nSimulation Statistics:")
print(f"Fighter1 wins: {winners['Fighter1']}")
print(f"Fighter2 wins: {winners['Fighter2']}")
print(f"Draws: {winners['draw']}")
print(f"Average simulation length: {total_ticks/10:.1f} ticks")

# Save the last result to a file
with open("last_simulation.json", "w") as f:
    json.dump(result, f, indent=2) 