from duelsim.items.item import ItemSlot
from duelsim.controllers.human_controller import HumanController

class Player:
    def __init__(self, name, hp=99, attack=70, strength=70, defense=70, **kwargs):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.strength = strength
        self.defense = defense
        
        # Position
        self.position = (0, 0)
        
        # Equipment and stats
        self.weapon = None
        self.weapon_speed = 4  # Default (whip-like)
        self.cooldown = 0
        
        # Action queue
        self.action_queue = []
        self.next_action = None
        
        # Equipment slots
        self.equipment = {slot.value: None for slot in ItemSlot}
        
        # Base stats (without equipment)
        self.base_stats = {
            "hp": hp,
            "attack": attack,
            "strength": strength,
            "defense": defense,
            "magic": kwargs.get("magic", 1),
            "ranged": kwargs.get("ranged", 1),
            "magic_defense": kwargs.get("magic_defense", defense // 2),
            "ranged_defense": kwargs.get("ranged_defense", defense // 2),
            "attack_speed": kwargs.get("attack_speed", 4)  # Default attack speed (ticks)
        }
        
        # Calculate effective stats
        self._update_effective_stats()
        
        # Input control
        self.controller = None
        self.is_human_controlled = False
        
        # Additional stats for human players
        self.special_energy = 100  # Special attack energy (0-100)
        self.prayer_points = 99    # Prayer points
        self.is_running = False    # Running state
        
    def add_action(self, action_type, **kwargs):
        """Add an action to the queue with execution tick"""
        self.action_queue.append({
            "type": action_type,
            **kwargs
        })
        
    def is_action_ready(self, current_tick):
        """Check if there's an action ready to execute on this tick"""
        for i, action in enumerate(self.action_queue):
            if action.get("execute_on", 0) <= current_tick:
                self.next_action = self.action_queue.pop(i)
                return True
        return False
    
    def update_cooldowns(self):
        """Update cooldown timers"""
        if self.cooldown > 0:
            self.cooldown -= 1 

    def equip_item(self, item):
        """Equip an item in the appropriate slot"""
        if item.slot.value in self.equipment:
            self.equipment[item.slot.value] = item
            self._update_effective_stats()
            return True
        return False

    def unequip_item(self, slot):
        """Remove an item from the specified slot"""
        if slot in self.equipment and self.equipment[slot] is not None:
            item = self.equipment[slot]
            self.equipment[slot] = None
            self._update_effective_stats()
            return item
        return None

    def _update_effective_stats(self):
        """Update effective stats based on equipment"""
        # Start with base stats
        self.effective_stats = self.base_stats.copy()
        
        # Add equipment bonuses
        for slot, item in self.equipment.items():
            if item is not None:
                for stat, value in item.stats.items():
                    if stat in self.effective_stats:
                        self.effective_stats[stat] += value
        
        # Update derived attributes
        self.max_hp = self.effective_stats["hp"]
        self.hp = min(self.hp, self.max_hp)  # Cap current HP at max
        self.weapon_speed = self.effective_stats["attack_speed"]

    def get_special_effects(self):
        """Get all special effects from equipped items"""
        effects = []
        for slot, item in self.equipment.items():
            if item is not None and hasattr(item, 'special_effects'):
                effects.extend(item.special_effects)
        return effects

    def to_dict(self):
        """Convert player to dictionary for serialization"""
        player_dict = {
            "name": self.name,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "attack": self.attack,
            "strength": self.strength,
            "defense": self.defense,
            "position": self.position,
            "weapon_speed": self.weapon_speed,
            "cooldown": self.cooldown,
            "action_queue": self.action_queue,
            "next_action": self.next_action,
            "equipment": {
                slot: (item.to_dict() if item else None) 
                for slot, item in self.equipment.items()
            }
        }
        return player_dict 

    def set_controller(self, controller):
        """Set the controller for this player"""
        self.controller = controller
        self.is_human_controlled = isinstance(controller, HumanController)
        return self

    def update(self, game_state, tick):
        """Update player state based on controller input"""
        if self.controller:
            action = self.controller.update(game_state, tick)
            if action:
                self.add_action(**action)

class SimplePlayer:
    def __init__(self, name, hp, max_hp, position):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.position = position
        # Add the missing equipment attribute
        self.equipment = {} # Initialize as an empty dictionary

    # ... other methods of SimplePlayer ...