"""
Script to balance equipment generation in DuelSim
Creates more competitive matchups by limiting stat differences
"""
import os
import sys
import json
import random
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

print(f"{Fore.GREEN}=== Equipment Balance Script ==={Style.RESET_ALL}")

def balance_equipment_stats(items, max_stat_value=25):
    """
    Balance equipment stats to create more competitive matchups
    
    Args:
        items: List of equipment items
        max_stat_value: Maximum value for any single stat on an item
    
    Returns:
        Balanced list of items
    """
    print(f"{Fore.CYAN}Balancing equipment stats...{Style.RESET_ALL}")
    
    balanced_items = []
    
    for item in items:
        # Create a copy of the item
        balanced_item = item.copy()
        
        # Balance the stats
        if "stats" in balanced_item:
            balanced_stats = {}
            for stat, value in balanced_item["stats"].items():
                # Cap the stat value
                balanced_value = min(value, max_stat_value)
                
                # Add some randomness to create variety but maintain balance
                variation = random.uniform(0.8, 1.2)
                balanced_value = round(balanced_value * variation)
                
                # Ensure minimum value of 1
                balanced_value = max(1, balanced_value)
                
                balanced_stats[stat] = balanced_value
            
            balanced_item["stats"] = balanced_stats
        
        balanced_items.append(balanced_item)
    
    print(f"{Fore.GREEN}Successfully balanced {len(balanced_items)} items{Style.RESET_ALL}")
    return balanced_items

def adjust_win_probability_calculation():
    """
    Provide instructions to adjust the win probability calculation
    to create more balanced matchups
    """
    print(f"{Fore.YELLOW}To create more balanced matchups, you should also modify the win probability calculation.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Add the following function to master_duel.py:{Style.RESET_ALL}")
    
    print(f"""
def compute_balanced_win_probability(player1, player2):
    \"\"\"
    Calculate win probability with a more balanced approach
    that prevents extreme probabilities of 0 or 1
    \"\"\"
    # Get base stats
    p1_attack = getattr(player1, 'attack', 0)
    p1_defense = getattr(player1, 'defense', 0)
    p1_hp = getattr(player1, 'hp', 0)
    p1_strength = getattr(player1, 'strength', 0)
    
    p2_attack = getattr(player2, 'attack', 0)
    p2_defense = getattr(player2, 'defense', 0)
    p2_hp = getattr(player2, 'hp', 0)
    p2_strength = getattr(player2, 'strength', 0)
    
    # Calculate offensive and defensive power
    p1_offense = p1_attack * 0.7 + p1_strength * 0.3
    p1_defense_power = p1_defense * 0.7 + p1_hp * 0.3
    
    p2_offense = p2_attack * 0.7 + p2_strength * 0.3
    p2_defense_power = p2_defense * 0.7 + p2_hp * 0.3
    
    # Calculate overall power
    p1_power = p1_offense * 0.6 + p1_defense_power * 0.4
    p2_power = p2_offense * 0.6 + p2_defense_power * 0.4
    
    # Calculate power difference
    total_power = p1_power + p2_power
    if total_power == 0:
        # Equal chance if both have zero power
        return 0.5, 0.5, 0
    
    # Calculate normalized power difference
    power_diff = (p1_power - p2_power) / total_power
    
    # Apply sigmoid function to get probability between 0.1 and 0.9
    # This ensures no probability is ever exactly 0 or 1
    p1_prob = 0.5 + (0.4 * power_diff)
    
    # Ensure probability is between 0.1 and 0.9
    p1_prob = max(0.1, min(0.9, p1_prob))
    p2_prob = 1 - p1_prob
    
    return p1_prob, p2_prob, power_diff
""")

try:
    # Load existing items
    print(f"{Fore.CYAN}Loading items from items_1337.json...{Style.RESET_ALL}")
    with open("items_1337.json", "r") as f:
        items = json.load(f)
    
    print(f"{Fore.GREEN}Loaded {len(items)} items{Style.RESET_ALL}")
    
    # Balance the items
    balanced_items = balance_equipment_stats(items)
    
    # Save balanced items
    with open("balanced_items_1337.json", "w") as f:
        json.dump(balanced_items, f, indent=2)
    
    print(f"{Fore.GREEN}Saved balanced items to balanced_items_1337.json{Style.RESET_ALL}")
    print(f"{Fore.GREEN}To use these balanced items, update your code to load from 'balanced_items_1337.json'{Style.RESET_ALL}")
    
    # Provide instructions for win probability calculation
    adjust_win_probability_calculation()
    
except FileNotFoundError:
    print(f"{Fore.RED}Error: items_1337.json not found{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Run fix_items.py first to generate the items file{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}Error balancing items: {e}{Style.RESET_ALL}")
    import traceback
    traceback.print_exc()

print(f"{Fore.GREEN}=== Balance Script Completed ==={Style.RESET_ALL}") 