"""
Fighter classes for DuelSim

This module defines the different fighter classes available in the game.
"""

import random
from enum import Enum

class FighterType(Enum):
    """Types of fighters"""
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    RANGER = "Ranger"
    PALADIN = "Paladin"
    BERSERKER = "Berserker"
    MONK = "Monk"
    NECROMANCER = "Necromancer"

class BaseFighter:
    """Base class for all fighters"""
    
    def __init__(self, name=None):
        self.name = name or self._generate_name()
        self.hp = 100
        self.max_hp = 100
        self.attack = 10
        self.defense = 5
        self.position = [0, 0]
        self.type = FighterType.WARRIOR
    
    def _generate_name(self):
        """Generate a random name for the fighter"""
        prefixes = ["Dark", "Light", "Swift", "Mighty", "Shadow", "Flame", "Ice", "Storm", "Ancient", "Mystic"]
        suffixes = ["Blade", "Fist", "Knight", "Warrior", "Mage", "Hunter", "Slayer", "Master", "Lord", "Champion"]
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def move(self, dx, dy):
        """Move the fighter by the given delta"""
        self.position[0] = max(0, min(4, self.position[0] + dx))
        self.position[1] = max(0, min(4, self.position[1] + dy))
    
    def attack_damage(self):
        """Calculate attack damage"""
        return random.randint(self.attack // 2, self.attack)
    
    def take_damage(self, damage):
        """Take damage, reduced by defense"""
        actual_damage = max(1, damage - random.randint(0, self.defense))
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage
    
    def is_alive(self):
        """Check if the fighter is alive"""
        return self.hp > 0
    
    def to_dict(self):
        """Convert fighter to dictionary for serialization"""
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "position": self.position,
            "type": self.type.value
        }

class Warrior(BaseFighter):
    """Warrior class - balanced fighter with good defense"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 120
        self.max_hp = 120
        self.attack = 12
        self.defense = 8
        self.type = FighterType.WARRIOR

class Mage(BaseFighter):
    """Mage class - high attack, low defense"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 80
        self.max_hp = 80
        self.attack = 18
        self.defense = 3
        self.type = FighterType.MAGE

class Rogue(BaseFighter):
    """Rogue class - fast and evasive"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 90
        self.max_hp = 90
        self.attack = 14
        self.defense = 5
        self.type = FighterType.ROGUE

class Ranger(BaseFighter):
    """Ranger class - ranged attacks"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 95
        self.max_hp = 95
        self.attack = 13
        self.defense = 4
        self.type = FighterType.RANGER

class Paladin(BaseFighter):
    """Paladin class - high defense"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 130
        self.max_hp = 130
        self.attack = 10
        self.defense = 10
        self.type = FighterType.PALADIN

class Berserker(BaseFighter):
    """Berserker class - high attack, low defense"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 110
        self.max_hp = 110
        self.attack = 16
        self.defense = 2
        self.type = FighterType.BERSERKER

class Monk(BaseFighter):
    """Monk class - balanced stats"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 100
        self.max_hp = 100
        self.attack = 12
        self.defense = 6
        self.type = FighterType.MONK

class Necromancer(BaseFighter):
    """Necromancer class - special abilities"""
    
    def __init__(self, name=None):
        super().__init__(name)
        self.hp = 85
        self.max_hp = 85
        self.attack = 15
        self.defense = 4
        self.type = FighterType.NECROMANCER

# Dictionary of fighter classes
FIGHTER_CLASSES = {
    "Warrior": Warrior,
    "Mage": Mage,
    "Rogue": Rogue,
    "Ranger": Ranger,
    "Paladin": Paladin,
    "Berserker": Berserker,
    "Monk": Monk,
    "Necromancer": Necromancer
} 