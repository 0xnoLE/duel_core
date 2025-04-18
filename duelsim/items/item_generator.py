import random
import math
from duelsim.items.item import Item, ItemRarity, ItemSlot, ItemType

class ItemGenerator:
    """Generates random items with appropriate stats based on level and rarity"""
    
    # Base stat values for different item types
    BASE_STATS = {
        ItemType.MELEE_WEAPON: {
            "attack": 5,
            "strength": 5,
            "attack_speed": -3  # Lower is faster
        },
        ItemType.RANGED_WEAPON: {
            "ranged": 5,
            "ranged_strength": 5,
            "attack_speed": -3
        },
        ItemType.MAGIC_WEAPON: {
            "magic": 5,
            "magic_damage": 5,
            "attack_speed": -4
        },
        ItemType.ARMOR: {
            "defense": 3,
            "magic_defense": 2,
            "ranged_defense": 2
        },
        ItemType.JEWELRY: {
            "strength": 2,
            "attack": 2,
            "defense": 2,
            "magic": 2,
            "ranged": 2
        }
    }
    
    # Special effect templates
    SPECIAL_EFFECTS = [
        {"name": "Critical Strike", "effect": "critical_chance", "value": 5},
        {"name": "Life Steal", "effect": "life_steal", "value": 5},
        {"name": "Damage Reflection", "effect": "damage_reflection", "value": 10},
        {"name": "Dodge Chance", "effect": "dodge_chance", "value": 5},
        {"name": "Double Strike", "effect": "double_strike", "value": 5},
        {"name": "Stun Chance", "effect": "stun_chance", "value": 5},
        {"name": "Poison Chance", "effect": "poison_chance", "value": 10},
        {"name": "Bleed Chance", "effect": "bleed_chance", "value": 10}
    ]
    
    # Item name components
    NAME_PREFIXES = {
        ItemType.MELEE_WEAPON: ["Sharp", "Heavy", "Brutal", "Mighty", "Savage", "Fierce"],
        ItemType.RANGED_WEAPON: ["Accurate", "Swift", "Piercing", "Deadly", "Precise", "Hunter's"],
        ItemType.MAGIC_WEAPON: ["Arcane", "Mystic", "Enchanted", "Magical", "Sorcerer's", "Wizard's"],
        ItemType.ARMOR: ["Sturdy", "Reinforced", "Protective", "Hardened", "Impenetrable", "Guardian's"],
        ItemType.JEWELRY: ["Gleaming", "Enchanted", "Blessed", "Mystical", "Powerful", "Ancient"]
    }
    
    NAME_BASES = {
        ItemType.MELEE_WEAPON: ["Sword", "Axe", "Mace", "Dagger", "Hammer", "Scimitar", "Longsword"],
        ItemType.RANGED_WEAPON: ["Bow", "Crossbow", "Throwing Knives", "Javelin", "Sling", "Blowpipe"],
        ItemType.MAGIC_WEAPON: ["Staff", "Wand", "Orb", "Tome", "Scepter", "Rod"],
        ItemType.ARMOR: {
            ItemSlot.HEAD: ["Helmet", "Cap", "Hood", "Crown", "Circlet"],
            ItemSlot.BODY: ["Chestplate", "Robe", "Armor", "Breastplate", "Tunic"],
            ItemSlot.LEGS: ["Greaves", "Leggings", "Pants", "Kilt", "Tassets"],
            ItemSlot.HANDS: ["Gauntlets", "Gloves", "Bracers", "Vambraces"],
            ItemSlot.FEET: ["Boots", "Shoes", "Sandals", "Greaves"]
        },
        ItemType.JEWELRY: {
            ItemSlot.RING: ["Ring", "Band", "Loop", "Signet"],
            ItemSlot.AMULET: ["Amulet", "Necklace", "Pendant", "Talisman", "Charm"]
        }
    }
    
    NAME_SUFFIXES = [
        "of Power", "of Might", "of Destruction", "of the Warrior", "of the Mage",
        "of the Hunter", "of Protection", "of Swiftness", "of Precision", "of Fortune",
        "of the Berserker", "of the Assassin", "of the Guardian", "of the Oracle"
    ]
    
    @classmethod
    def generate_item(cls, level=1, rarity=None, slot=None, item_type=None):
        """Generate a random item with the given parameters"""
        # Determine rarity if not specified
        if rarity is None:
            rarity = cls._random_rarity()
        
        # Determine slot if not specified
        if slot is None:
            slot = random.choice(list(ItemSlot))
        
        # Determine item type if not specified
        if item_type is None:
            possible_types = ItemType.for_slot(slot)
            item_type = random.choice(possible_types)
        
        # Generate name
        name = cls._generate_name(item_type, slot)
        
        # Generate stats
        stats = cls._generate_stats(item_type, level, rarity)
        
        # Generate special effects for rare+ items
        special_effects = []
        if rarity.value >= ItemRarity.RARE.value:
            num_effects = min(rarity.value - 2, 3)  # 1 effect for rare, 2 for epic, 3 for legendary+
            special_effects = cls._generate_special_effects(num_effects, rarity)
        
        return Item(name, slot, item_type, rarity, level, stats, special_effects)
    
    @classmethod
    def _random_rarity(cls):
        """Generate a random rarity based on weighted probabilities"""
        roll = random.random() * 100
        if roll < 50:
            return ItemRarity.COMMON
        elif roll < 80:
            return ItemRarity.UNCOMMON
        elif roll < 95:
            return ItemRarity.RARE
        elif roll < 99:
            return ItemRarity.EPIC
        elif roll < 99.9:
            return ItemRarity.LEGENDARY
        else:
            return ItemRarity.MYTHIC
    
    @classmethod
    def _generate_name(cls, item_type, slot):
        """Generate a random name for an item"""
        prefix = random.choice(cls.NAME_PREFIXES.get(item_type, ["Mysterious"]))
        
        # Get appropriate base name
        if item_type in [ItemType.ARMOR, ItemType.JEWELRY]:
            base_options = cls.NAME_BASES[item_type].get(slot, ["Item"])
        else:
            base_options = cls.NAME_BASES.get(item_type, ["Item"])
        
        base = random.choice(base_options)
        
        # Add suffix for uncommon+ items (50% chance)
        if random.random() < 0.5:
            suffix = random.choice(cls.NAME_SUFFIXES)
            return f"{prefix} {base} {suffix}"
        else:
            return f"{prefix} {base}"
    
    @classmethod
    def _generate_stats(cls, item_type, level, rarity):
        """Generate appropriate stats for an item"""
        base_stats = cls.BASE_STATS.get(item_type, {}).copy()
        
        # Scale stats based on level
        level_multiplier = 1 + (level * 0.1)
        for stat in base_stats:
            # Add some randomness to stats (±20%)
            randomness = 0.8 + (random.random() * 0.4)  # 0.8 to 1.2
            base_stats[stat] = round(base_stats[stat] * level_multiplier * randomness)
        
        return base_stats
    
    @classmethod
    def _generate_special_effects(cls, num_effects, rarity):
        """Generate special effects for an item"""
        effects = []
        available_effects = cls.SPECIAL_EFFECTS.copy()
        
        for _ in range(num_effects):
            if not available_effects:
                break
                
            effect = random.choice(available_effects)
            available_effects.remove(effect)  # Prevent duplicates
            
            # Scale effect value based on rarity
            effect_copy = effect.copy()
            effect_copy["value"] = round(effect["value"] * rarity.power_multiplier)
            effects.append(effect_copy)
            
        return effects
