"""
Script to fix the item loading in master_duel.py
"""
import os
import sys
import json
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

print(f"{Fore.GREEN}=== Item Loading Fix Script ==={Style.RESET_ALL}")

# Create a minimal items file
try:
    print(f"{Fore.CYAN}Creating a minimal items file...{Style.RESET_ALL}")
    
    # Create items with proper types based on the error output
    items = []
    
    # Create items for each slot and type
    slots = ["weapon", "head", "body", "legs", "hands", "feet", "ring", "amulet"]
    weapon_types = ["melee_weapon", "ranged_weapon", "magic_weapon"]
    armor_slots = ["head", "body", "legs", "hands", "feet"]
    jewelry_slots = ["ring", "amulet"]
    rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]
    
    item_id = 1
    for slot in slots:
        # Determine the appropriate type for this slot
        if slot == "weapon":
            for weapon_type in weapon_types:
                for rarity in rarities:
                    item = {
                        "name": f"{rarity.capitalize()} {weapon_type.replace('_', ' ').title()} {item_id}",
                        "slot": slot,
                        "type": weapon_type,
                        "rarity": rarity,
                        "level": 1,
                        "stats": {"attack": 5 + rarities.index(rarity) * 5, "strength": 3 + rarities.index(rarity) * 3},
                        "special_effects": []
                    }
                    items.append(item)
                    item_id += 1
        elif slot in armor_slots:
            item_type = "armor"
            for rarity in rarities:
                item = {
                    "name": f"{rarity.capitalize()} {slot.title()} Armor {item_id}",
                    "slot": slot,
                    "type": item_type,
                    "rarity": rarity,
                    "level": 1,
                    "stats": {"defense": 5 + rarities.index(rarity) * 5, "hp": 3 + rarities.index(rarity) * 3},
                    "special_effects": []
                }
                items.append(item)
                item_id += 1
        elif slot in jewelry_slots:
            item_type = "jewelry"
            for rarity in rarities:
                item = {
                    "name": f"{rarity.capitalize()} {slot.title()} {item_id}",
                    "slot": slot,
                    "type": item_type,
                    "rarity": rarity,
                    "level": 1,
                    "stats": {"magic": 5 + rarities.index(rarity) * 5, "hp": 2 + rarities.index(rarity) * 2},
                    "special_effects": []
                }
                items.append(item)
                item_id += 1
    
    # Save to file
    with open("items_1337.json", "w") as f:
        json.dump(items, f, indent=2)
    
    print(f"{Fore.GREEN}Created items file with {len(items)} items{Style.RESET_ALL}")
    print(f"{Fore.GREEN}You can now run master_duel.py without errors{Style.RESET_ALL}")
    
except Exception as e:
    print(f"{Fore.RED}Error creating items file: {e}{Style.RESET_ALL}")
    import traceback
    traceback.print_exc()

print(f"{Fore.GREEN}=== Fix Script Completed ==={Style.RESET_ALL}")