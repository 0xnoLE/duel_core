"""
Simple Item Generator for DuelSim with enhanced logging
"""
import random
import json
import os
import sys
import traceback
from colorama import Fore, Style

# Import the actual item classes from your codebase
try:
    print(f"{Fore.CYAN}Attempting to import Item classes...{Style.RESET_ALL}")
    from duelsim.items.item import Item, ItemSlot, ItemRarity, ItemType
    print(f"{Fore.GREEN}Successfully imported Item classes{Style.RESET_ALL}")
    
    # Log the available enum values
    print(f"{Fore.CYAN}Available ItemSlot values:{Style.RESET_ALL}")
    for slot in ItemSlot:
        print(f"  - {slot.name}: {slot.value}")
    
    print(f"{Fore.CYAN}Available ItemRarity values:{Style.RESET_ALL}")
    for rarity in ItemRarity:
        print(f"  - {rarity.name}: {rarity.value}")
    
    print(f"{Fore.CYAN}Available ItemType values:{Style.RESET_ALL}")
    for item_type in ItemType:
        print(f"  - {item_type.name}: {item_type.value}")
        
except ImportError as e:
    print(f"{Fore.RED}Error importing Item classes: {e}{Style.RESET_ALL}")
    traceback.print_exc()
    sys.exit(1)

def generate_items(count=100):
    """Generate a specified number of items"""
    print(f"{Fore.CYAN}Starting item generation, count={count}{Style.RESET_ALL}")
    items = []
    
    try:
        # Get actual enum values from your codebase
        slots = list(ItemSlot)
        rarities = list(ItemRarity)
        
        print(f"{Fore.CYAN}Found {len(slots)} slots and {len(rarities)} rarities{Style.RESET_ALL}")
        
        # Map slots to appropriate item types
        slot_to_type = {}
        for slot in slots:
            if slot == ItemSlot.WEAPON:
                # Weapons can be melee, ranged, or magic
                slot_to_type[slot] = [ItemType.MELEE_WEAPON, ItemType.RANGED_WEAPON, ItemType.MAGIC_WEAPON]
            elif slot in [ItemSlot.HEAD, ItemSlot.BODY, ItemSlot.LEGS, ItemSlot.HANDS, ItemSlot.FEET]:
                # Armor slots
                slot_to_type[slot] = [ItemType.ARMOR]
            elif slot in [ItemSlot.RING, ItemSlot.AMULET]:
                # Jewelry slots
                slot_to_type[slot] = [ItemType.JEWELRY]
            else:
                # Default fallback
                slot_to_type[slot] = [ItemType.ARMOR]
        
        # Stats that can be on items
        stats = ["attack", "defense", "strength", "hp"]
        
        # Base names for items - using actual slot values from your enum
        base_names = {}
        for slot in slots:
            slot_value = slot.value
            print(f"{Fore.CYAN}Processing slot: {slot.name} = {slot_value}{Style.RESET_ALL}")
            
            if "head" in str(slot_value).lower():
                base_names[slot] = ["Helmet", "Cap", "Crown", "Hood", "Circlet"]
            elif "body" in str(slot_value).lower() or "chest" in str(slot_value).lower():
                base_names[slot] = ["Armor", "Breastplate", "Robe", "Vest", "Cuirass"]
            elif "leg" in str(slot_value).lower():
                base_names[slot] = ["Greaves", "Leggings", "Pants", "Trousers"]
            elif "weapon" in str(slot_value).lower():
                base_names[slot] = ["Sword", "Axe", "Mace", "Dagger", "Staff"]
            elif "shield" in str(slot_value).lower() or "hand" in str(slot_value).lower():
                base_names[slot] = ["Shield", "Buckler", "Aegis", "Bulwark", "Gauntlets", "Gloves"]
            elif "feet" in str(slot_value).lower():
                base_names[slot] = ["Boots", "Shoes", "Sandals", "Greaves"]
            elif "ring" in str(slot_value).lower():
                base_names[slot] = ["Ring", "Band", "Loop", "Signet"]
            elif "amulet" in str(slot_value).lower() or "neck" in str(slot_value).lower():
                base_names[slot] = ["Amulet", "Pendant", "Necklace", "Talisman"]
            else:
                # Default for any other slot types
                base_names[slot] = ["Item", "Artifact", "Relic", "Trinket"]
        
        print(f"{Fore.CYAN}Created base names for {len(base_names)} slot types{Style.RESET_ALL}")
        
        # Prefixes and suffixes by rarity
        prefixes = {
            "1": ["Basic", "Simple", "Plain", "Ordinary"],  # COMMON
            "2": ["Sturdy", "Quality", "Fine", "Solid"],    # UNCOMMON
            "3": ["Superior", "Excellent", "Remarkable", "Exceptional"],  # RARE
            "4": ["Magnificent", "Glorious", "Majestic", "Splendid"],     # EPIC
            "5": ["Divine", "Mythical", "Godly", "Transcendent"],         # LEGENDARY
            "6": ["Cosmic", "Eternal", "Infinite", "Omnipotent"]          # MYTHIC
        }
        
        suffixes = {
            "1": ["of the Novice", "of Training", "of the Apprentice"],
            "2": ["of Skill", "of Competence", "of Merit"],
            "3": ["of Excellence", "of Mastery", "of Expertise"],
            "4": ["of the Champion", "of the Conqueror", "of Triumph"],
            "5": ["of the Gods", "of Eternity", "of the Cosmos"],
            "6": ["of Creation", "of Destiny", "of Ultimate Power"]
        }
        
        # Generate items
        print(f"{Fore.CYAN}Starting to generate {count} items...{Style.RESET_ALL}")
        for i in range(count):
            if i % 100 == 0:
                print(f"{Fore.CYAN}Generated {i} items so far...{Style.RESET_ALL}")
                
            # Select random slot and rarity
            slot = random.choice(slots)
            rarity = random.choice(rarities)
            
            # Select appropriate item type for this slot
            item_type = random.choice(slot_to_type[slot])
            
            # Get base name options for this slot
            if slot not in base_names:
                print(f"{Fore.YELLOW}Slot {slot} not found in base_names, using fallback{Style.RESET_ALL}")
                slot = slots[0]  # Use first slot as fallback
            base_name_options = base_names[slot]
            
            # Generate name based on rarity
            rarity_key = str(rarity.value)
            prefix_list = prefixes.get(rarity_key, prefixes["1"])
            suffix_list = suffixes.get(rarity_key, suffixes["1"])
            
            prefix = random.choice(prefix_list)
            base = random.choice(base_name_options)
            suffix = random.choice(suffix_list)
            name = f"{prefix} {base} {suffix}"
            
            # Generate stats based on rarity
            num_stats = min(3, 1 + (rarities.index(rarity) // 2))
            item_stats = {}
            for _ in range(num_stats):
                stat = random.choice(stats)
                # Scale value based on rarity
                value = random.randint(1, 5) * rarity.value
                item_stats[stat] = value
            
            # Create item with appropriate constructor
            try:
                item = Item(
                    name=name,
                    slot=slot,
                    item_type=item_type,
                    rarity=rarity,
                    level=1,
                    stats=item_stats
                )
                items.append(item)
            except Exception as e:
                print(f"{Fore.RED}Error creating item {i} ({name}): {e}{Style.RESET_ALL}")
                traceback.print_exc()
                # Continue with next item instead of failing completely
                continue
        
        print(f"{Fore.GREEN}Successfully generated {len(items)} items{Style.RESET_ALL}")
        return items
        
    except Exception as e:
        print(f"{Fore.RED}Error in generate_items: {e}{Style.RESET_ALL}")
        traceback.print_exc()
        return []

def save_items_to_json(items, filename="items_1337.json"):
    """Save generated items to a JSON file"""
    print(f"{Fore.CYAN}Saving {len(items)} items to {filename}{Style.RESET_ALL}")
    
    try:
        # Convert items to dictionaries
        items_data = []
        for i, item in enumerate(items):
            try:
                item_dict = item.to_dict()
                items_data.append(item_dict)
            except Exception as e:
                print(f"{Fore.RED}Error converting item {i} to dict: {e}{Style.RESET_ALL}")
                traceback.print_exc()
        
        print(f"{Fore.CYAN}Converted {len(items_data)} items to dictionaries{Style.RESET_ALL}")
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(items_data, f, indent=2)
        
        print(f"{Fore.GREEN}Successfully saved items to {filename}{Style.RESET_ALL}")
        return filename
    except Exception as e:
        print(f"{Fore.RED}Error in save_items_to_json: {e}{Style.RESET_ALL}")
        traceback.print_exc()
        return None

def main():
    """Main function"""
    print(f"{Fore.GREEN}Starting item generation process...{Style.RESET_ALL}")
    
    # Set seed for reproducibility
    random.seed(1337)
    
    # Generate items
    items = generate_items(1337)
    
    if items:
        # Save to JSON
        filename = save_items_to_json(items)
        if filename:
            print(f"{Fore.GREEN}Items saved to {filename}{Style.RESET_ALL}")
        
        print(f"Total items generated: {len(items)}")
    else:
        print(f"{Fore.RED}No items were generated{Style.RESET_ALL}")

if __name__ == "__main__":
    main()