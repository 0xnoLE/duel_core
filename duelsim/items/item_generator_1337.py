"""
Item Generator - Creates a balanced set of 1337 equipment items for DuelSim
"""
import random
import json
import os
from enum import Enum
import sys
from colorama import Fore, Style

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import item classes
try:
    from duelsim.items.item import Item, ItemSlot, ItemRarity
except ImportError:
    # Define locally if imports fail
    class ItemSlot(Enum):
        HEAD = "head"
        CHEST = "chest"
        LEGS = "legs"
        WEAPON = "weapon"
        SHIELD = "shield"
        RING = "ring"
        AMULET = "amulet"
    
    class ItemRarity(Enum):
        COMMON = "common"
        UNCOMMON = "uncommon"
        RARE = "rare"
        EPIC = "epic"
        LEGENDARY = "legendary"
    
    class Item:
        def __init__(self, name, slot, rarity, stats, special_effects=None):
            self.name = name
            self.slot = slot
            self.rarity = rarity
            self.stats = stats
            self.special_effects = special_effects or []
        
        def to_dict(self):
            return {
                "name": self.name,
                "slot": self.slot.value,
                "rarity": self.rarity.value,
                "stats": self.stats,
                "special_effects": self.special_effects
            }
        
        def get_display_name(self):
            """Get colored display name based on rarity"""
            rarity_color = {
                ItemRarity.COMMON: Fore.WHITE,
                ItemRarity.UNCOMMON: Fore.GREEN,
                ItemRarity.RARE: Fore.BLUE,
                ItemRarity.EPIC: Fore.MAGENTA,
                ItemRarity.LEGENDARY: Fore.YELLOW
            }[self.rarity]
            return f"{rarity_color}{self.name}{Style.RESET_ALL}"

# Enhanced item prefixes that better reflect power level
PREFIXES = {
    ItemRarity.COMMON: ["Simple", "Basic", "Plain", "Crude", "Rough", "Worn", "Dull", "Modest"],
    ItemRarity.UNCOMMON: ["Sturdy", "Reliable", "Solid", "Decent", "Improved", "Reinforced", "Hardy", "Practical"],
    ItemRarity.RARE: ["Quality", "Superior", "Excellent", "Refined", "Precise", "Enchanted", "Empowered", "Masterful"],
    ItemRarity.EPIC: ["Magnificent", "Glorious", "Mythical", "Ancient", "Arcane", "Legendary", "Heroic", "Fabled"],
    ItemRarity.LEGENDARY: ["Godly", "Divine", "Celestial", "Eternal", "Ultimate", "Transcendent", "Cosmic", "Omnipotent"]
}

# Enhanced suffixes that better reflect power level
SUFFIXES = {
    ItemRarity.COMMON: ["of the Novice", "of Training", "of the Beginner", "of Practice", "of the Apprentice", "of Mediocrity"],
    ItemRarity.UNCOMMON: ["of Skill", "of Competence", "of the Adept", "of Proficiency", "of the Journeyman", "of Merit"],
    ItemRarity.RARE: ["of Mastery", "of Excellence", "of the Expert", "of Precision", "of the Veteran", "of Distinction"],
    ItemRarity.EPIC: ["of the Champion", "of Dominance", "of the Conqueror", "of Triumph", "of the Vanquisher", "of Glory"],
    ItemRarity.LEGENDARY: ["of the Gods", "of Ascension", "of the Cosmos", "of Eternity", "of the Immortal", "of Transcendence"]
}

# Base item names by slot
BASE_NAMES = {
    ItemSlot.HEAD: ["Helmet", "Cap", "Crown", "Hood", "Circlet", "Helm", "Headguard", "Coif"],
    ItemSlot.CHEST: ["Chestplate", "Armor", "Breastplate", "Robe", "Vest", "Cuirass", "Hauberk", "Tunic"],
    ItemSlot.LEGS: ["Greaves", "Leggings", "Pants", "Kilt", "Trousers", "Cuisses", "Breeches", "Tassets"],
    ItemSlot.WEAPON: ["Sword", "Axe", "Mace", "Dagger", "Staff", "Bow", "Hammer", "Spear", "Blade", "Scythe"],
    ItemSlot.SHIELD: ["Shield", "Buckler", "Aegis", "Bulwark", "Ward", "Defender", "Safeguard", "Barrier"],
    ItemSlot.RING: ["Ring", "Band", "Loop", "Signet", "Seal", "Circle", "Hoop", "Coil"],
    ItemSlot.AMULET: ["Amulet", "Pendant", "Necklace", "Talisman", "Charm", "Medallion", "Locket", "Totem"]
}

# Enhanced special effects with more descriptive names
SPECIAL_EFFECTS = [
    {"name": "Critical Strike", "stat": "attack", "max_value": 25},
    {"name": "Steadfast Block", "stat": "defense", "max_value": 25},
    {"name": "Vampiric Lifesteal", "stat": "hp", "max_value": 15},
    {"name": "Swift Double Strike", "stat": "attack", "max_value": 10},
    {"name": "Nimble Dodge", "stat": "defense", "max_value": 20},
    {"name": "Berserker's Rage", "stat": "strength", "max_value": 20},
    {"name": "Ironclad Fortify", "stat": "defense", "max_value": 20},
    {"name": "Vital Regeneration", "stat": "hp", "max_value": 10},
    {"name": "Precision Strike", "stat": "attack", "max_value": 15},
    {"name": "Unyielding Defense", "stat": "defense", "max_value": 18},
    {"name": "Warrior's Might", "stat": "strength", "max_value": 22},
    {"name": "Arcane Protection", "stat": "magic_defense", "max_value": 25}
]

# Stat ranges by rarity - enhanced to better reflect power progression
STAT_RANGES = {
    ItemRarity.COMMON: {"min": 1, "max": 5},
    ItemRarity.UNCOMMON: {"min": 4, "max": 12},
    ItemRarity.RARE: {"min": 10, "max": 20},
    ItemRarity.EPIC: {"min": 15, "max": 30},
    ItemRarity.LEGENDARY: {"min": 25, "max": 50}
}

# Special effect chances by rarity
EFFECT_CHANCES = {
    ItemRarity.COMMON: 0.05,
    ItemRarity.UNCOMMON: 0.15,
    ItemRarity.RARE: 0.35,
    ItemRarity.EPIC: 0.65,
    ItemRarity.LEGENDARY: 1.0
}

# Rarity distribution for 1337 items
RARITY_DISTRIBUTION = {
    ItemRarity.COMMON: 0.40,      # ~535 items
    ItemRarity.UNCOMMON: 0.30,    # ~401 items
    ItemRarity.RARE: 0.20,        # ~267 items
    ItemRarity.EPIC: 0.08,        # ~107 items
    ItemRarity.LEGENDARY: 0.02    # ~27 items
}

def generate_item_name(slot, rarity):
    """Generate a random item name based on slot and rarity"""
    prefix = random.choice(PREFIXES[rarity])
    base = random.choice(BASE_NAMES[slot])
    suffix = random.choice(SUFFIXES[rarity])
    return f"{prefix} {base} {suffix}"

def generate_item_stats(rarity, slot):
    """Generate balanced stats for an item based on rarity and slot"""
    stats = {}
    stat_range = STAT_RANGES[rarity]
    
    # Determine which stats this item can have based on slot
    available_stats = ["attack", "defense", "strength", "hp"]
    
    # Bias certain slots toward certain stats
    if slot == ItemSlot.WEAPON:
        primary_stats = ["attack", "strength"]
    elif slot == ItemSlot.SHIELD:
        primary_stats = ["defense", "hp"]
    elif slot == ItemSlot.HEAD or slot == ItemSlot.CHEST or slot == ItemSlot.LEGS:
        primary_stats = ["defense", "hp"]
    elif slot == ItemSlot.RING:
        primary_stats = ["attack", "strength"]
    elif slot == ItemSlot.AMULET:
        primary_stats = ["hp", "defense"]
    else:
        primary_stats = random.sample(available_stats, 2)
    
    # Number of stats based on rarity
    num_stats = {
        ItemRarity.COMMON: random.randint(1, 2),
        ItemRarity.UNCOMMON: random.randint(2, 3),
        ItemRarity.RARE: random.randint(2, 4),
        ItemRarity.EPIC: random.randint(3, 4),
        ItemRarity.LEGENDARY: 4
    }[rarity]
    
    # Always include primary stats first
    stats_to_include = primary_stats.copy()
    
    # Add other stats if needed
    other_stats = [s for s in available_stats if s not in primary_stats]
    random.shuffle(other_stats)
    stats_to_include.extend(other_stats)
    
    # Trim to the number of stats for this rarity
    stats_to_include = stats_to_include[:num_stats]
    
    # Generate stat values
    for stat in stats_to_include:
        # Primary stats get higher values
        if stat in primary_stats:
            min_val = max(stat_range["min"], int(stat_range["min"] * 1.2))
            max_val = int(stat_range["max"] * 1.2)
        else:
            min_val = stat_range["min"]
            max_val = stat_range["max"]
        
        # Generate the stat value
        stats[stat] = random.randint(min_val, max_val)
    
    return stats

def generate_special_effects(rarity):
    """Generate special effects for an item based on rarity"""
    # Check if this item should have special effects
    if random.random() > EFFECT_CHANCES[rarity]:
        return []
    
    # Number of effects based on rarity
    max_effects = {
        ItemRarity.COMMON: 1,
        ItemRarity.UNCOMMON: 1,
        ItemRarity.RARE: 2,
        ItemRarity.EPIC: 2,
        ItemRarity.LEGENDARY: 3
    }[rarity]
    
    num_effects = random.randint(1, max_effects)
    
    # Select random effects
    selected_effects = random.sample(SPECIAL_EFFECTS, num_effects)
    
    # Generate effect values based on rarity
    effects = []
    for effect in selected_effects:
        # Higher rarity items get stronger effects
        min_value = max(1, int(effect["max_value"] * {
            ItemRarity.COMMON: 0.2,
            ItemRarity.UNCOMMON: 0.3,
            ItemRarity.RARE: 0.5,
            ItemRarity.EPIC: 0.7,
            ItemRarity.LEGENDARY: 0.8
        }[rarity]))
        
        max_value = int(effect["max_value"] * {
            ItemRarity.COMMON: 0.4,
            ItemRarity.UNCOMMON: 0.6,
            ItemRarity.RARE: 0.8,
            ItemRarity.EPIC: 0.9,
            ItemRarity.LEGENDARY: 1.0
        }[rarity])
        
        value = random.randint(min_value, max_value)
        
        effects.append({
            "name": effect["name"],
            "stat": effect["stat"],
            "value": value
        })
    
    return effects

def generate_items(count):
    """Generate a specified number of balanced items"""
    items = []
    
    # Calculate how many items of each rarity to generate
    rarity_counts = {}
    remaining = count
    
    for rarity, percentage in RARITY_DISTRIBUTION.items():
        if rarity == list(RARITY_DISTRIBUTION.keys())[-1]:
            # Last rarity gets all remaining items
            rarity_counts[rarity] = remaining
        else:
            # Calculate count based on percentage
            rarity_count = int(count * percentage)
            rarity_counts[rarity] = rarity_count
            remaining -= rarity_count
    
    # Generate items for each rarity
    for rarity, rarity_count in rarity_counts.items():
        for _ in range(rarity_count):
            # Select random slot
            slot = random.choice(list(ItemSlot))
            
            # Generate item name
            name = generate_item_name(slot, rarity)
            
            # Generate stats
            stats = generate_item_stats(rarity, slot)
            
            # Generate special effects
            special_effects = generate_special_effects(rarity)
            
            # Create item
            item = Item(name, slot, rarity, stats, special_effects)
            items.append(item)
    
    return items

def save_items_to_json(items, filename="items_1337.json"):
    """Save generated items to a JSON file"""
    # Convert items to dictionaries
    items_data = [item.to_dict() for item in items]
    
    # Save to JSON
    with open(filename, 'w') as f:
        json.dump(items_data, f, indent=2)
    
    return filename

def print_item_stats(items):
    """Print statistics about the generated items"""
    total = len(items)
    
    # Count rarities
    rarity_counts = {}
    for rarity in ItemRarity:
        rarity_counts[rarity] = sum(1 for item in items if item.rarity == rarity)
    
    # Count slots
    slot_counts = {}
    for slot in ItemSlot:
        slot_counts[slot] = sum(1 for item in items if item.slot == slot)
    
    # Count stats
    stat_counts = {}
    for item in items:
        for stat in item.stats:
            if stat not in stat_counts:
                stat_counts[stat] = 0
            stat_counts[stat] += 1
    
    # Count special effects
    effect_count = sum(len(item.special_effects) for item in items)
    effect_types = {}
    for item in items:
        for effect in item.special_effects:
            if effect["name"] not in effect_types:
                effect_types[effect["name"]] = 0
            effect_types[effect["name"]] += 1
    
    # Print statistics
    print(f"\n{Fore.YELLOW}Item Statistics:{Style.RESET_ALL}")
    print(f"Total items: {total}")
    
    print(f"\n{Fore.YELLOW}Rarity Distribution:{Style.RESET_ALL}")
    for rarity, count in rarity_counts.items():
        percentage = (count / total) * 100
        rarity_color = {
            ItemRarity.COMMON: Fore.WHITE,
            ItemRarity.UNCOMMON: Fore.GREEN,
            ItemRarity.RARE: Fore.BLUE,
            ItemRarity.EPIC: Fore.MAGENTA,
            ItemRarity.LEGENDARY: Fore.YELLOW
        }[rarity]
        print(f"{rarity_color}{rarity.value.capitalize()}: {count} ({percentage:.1f}%){Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Slot Distribution:{Style.RESET_ALL}")
    for slot, count in slot_counts.items():
        percentage = (count / total) * 100
        print(f"{slot.value.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\n{Fore.YELLOW}Stat Distribution:{Style.RESET_ALL}")
    for stat, count in stat_counts.items():
        percentage = (count / total) * 100
        print(f"{stat.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\n{Fore.YELLOW}Special Effects:{Style.RESET_ALL}")
    print(f"Total effects: {effect_count}")
    print(f"Items with effects: {sum(1 for item in items if item.special_effects)} ({(sum(1 for item in items if item.special_effects) / total) * 100:.1f}%)")
    
    if effect_types:
        print(f"\n{Fore.YELLOW}Effect Types:{Style.RESET_ALL}")
        for effect, count in sorted(effect_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / effect_count) * 100
            print(f"{effect}: {count} ({percentage:.1f}%)")

def main():
    """Main function to generate and save items"""
    print(f"{Fore.GREEN}Generating 1337 balanced equipment items...{Style.RESET_ALL}")
    
    # Set seed for reproducibility (optional)
    random.seed(1337)
    
    # Generate items
    items = generate_items(1337)
    
    # Save to JSON
    filename = save_items_to_json(items)
    print(f"{Fore.GREEN}Items saved to {filename}{Style.RESET_ALL}")
    
    # Print statistics
    print_item_stats(items)
    
    # Print sample items
    print(f"\n{Fore.YELLOW}Sample Items:{Style.RESET_ALL}")
    for rarity in ItemRarity:
        for item in items:
            if item.rarity == rarity:
                rarity_color = {
                    ItemRarity.COMMON: Fore.WHITE,
                    ItemRarity.UNCOMMON: Fore.GREEN,
                    ItemRarity.RARE: Fore.BLUE,
                    ItemRarity.EPIC: Fore.MAGENTA,
                    ItemRarity.LEGENDARY: Fore.YELLOW
                }[rarity]
                
                print(f"\n{rarity_color}{item.name} ({item.rarity.value.capitalize()}){Style.RESET_ALL}")
                print(f"Slot: {item.slot.value.capitalize()}")
                print(f"Stats: {', '.join(f'{stat}: +{value}' for stat, value in item.stats.items())}")
                
                if item.special_effects:
                    print(f"Special Effects: {', '.join(f'{effect['name']} ({effect['value']}%)' for effect in item.special_effects)}")
                
                break  # Just show one example of each rarity

if __name__ == "__main__":
    main() 