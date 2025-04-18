import random
import math
from enum import Enum

class ItemRarity(Enum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    MYTHIC = 6
    
    @property
    def power_multiplier(self):
        """Return a power multiplier based on rarity"""
        return 1.0 + (self.value * 0.15)
    
    @property
    def color_code(self):
        """Return ANSI color code for this rarity"""
        colors = {
            ItemRarity.COMMON: "\033[37m",      # White
            ItemRarity.UNCOMMON: "\033[32m",    # Green
            ItemRarity.RARE: "\033[34m",        # Blue
            ItemRarity.EPIC: "\033[35m",        # Purple
            ItemRarity.LEGENDARY: "\033[33m",   # Yellow
            ItemRarity.MYTHIC: "\033[31m"       # Red
        }
        return colors.get(self, "\033[0m")

class ItemSlot(Enum):
    WEAPON = "weapon"
    HEAD = "head"
    BODY = "body"
    LEGS = "legs"
    HANDS = "hands"
    FEET = "feet"
    RING = "ring"
    AMULET = "amulet"
    
    @classmethod
    def get_all_slots(cls):
        return [slot.value for slot in cls]

class ItemType(Enum):
    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MAGIC_WEAPON = "magic_weapon"
    ARMOR = "armor"
    JEWELRY = "jewelry"
    
    @classmethod
    def for_slot(cls, slot):
        """Return appropriate item types for a given slot"""
        slot_map = {
            ItemSlot.WEAPON: [cls.MELEE_WEAPON, cls.RANGED_WEAPON, cls.MAGIC_WEAPON],
            ItemSlot.HEAD: [cls.ARMOR],
            ItemSlot.BODY: [cls.ARMOR],
            ItemSlot.LEGS: [cls.ARMOR],
            ItemSlot.HANDS: [cls.ARMOR],
            ItemSlot.FEET: [cls.ARMOR],
            ItemSlot.RING: [cls.JEWELRY],
            ItemSlot.AMULET: [cls.JEWELRY]
        }
        return slot_map.get(slot, [])

class Item:
    """Represents an equippable item with stats and special effects"""
    
    def __init__(self, name, slot, item_type, rarity, level=1, stats=None, special_effects=None):
        self.name = name
        self.slot = slot if isinstance(slot, ItemSlot) else ItemSlot(slot)
        self.item_type = item_type if isinstance(item_type, ItemType) else ItemType(item_type)
        self.rarity = rarity if isinstance(rarity, ItemRarity) else ItemRarity(rarity)
        self.level = level
        self.stats = stats or {}
        self.special_effects = special_effects or []
        
        # Apply rarity multiplier to stats
        self._apply_rarity_multiplier()
    
    def _apply_rarity_multiplier(self):
        """Apply rarity multiplier to all stats"""
        multiplier = self.rarity.power_multiplier
        for stat in self.stats:
            self.stats[stat] = round(self.stats[stat] * multiplier)
    
    def get_display_name(self):
        """Return colored name based on rarity"""
        return f"{self.rarity.color_code}{self.name}\033[0m"
    
    def to_dict(self):
        """Convert item to dictionary for serialization"""
        return {
            "name": self.name,
            "slot": self.slot.value,
            "type": self.item_type.value,
            "rarity": self.rarity.name,
            "level": self.level,
            "stats": self.stats,
            "special_effects": self.special_effects
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an item from dictionary data"""
        return cls(
            name=data["name"],
            slot=data["slot"],
            item_type=data["type"],
            rarity=ItemRarity[data["rarity"]],
            level=data.get("level", 1),
            stats=data.get("stats", {}),
            special_effects=data.get("special_effects", [])
        )
    
    def __str__(self):
        stats_str = ", ".join([f"{k}: {v}" for k, v in self.stats.items()])
        return f"{self.get_display_name()} [{self.slot.value}] ({stats_str})"
