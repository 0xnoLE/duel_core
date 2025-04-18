from duelsim.items.item import ItemType

class Inventory:
    """Player inventory for storing items"""
    
    def __init__(self, max_slots=28):
        self.max_slots = max_slots
        self.items = []
        self.equipped_weapon_index = 0
    
    def add_item(self, item):
        """Add an item to the inventory"""
        if len(self.items) < self.max_slots:
            self.items.append(item)
            return True
        return False
    
    def remove_item(self, index):
        """Remove an item from the inventory"""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def has_food(self):
        """Check if inventory has food items"""
        return any(item.item_type == ItemType.FOOD for item in self.items)
    
    def get_food(self):
        """Get the first food item"""
        for i, item in enumerate(self.items):
            if item.item_type == ItemType.FOOD:
                return self.remove_item(i)
        return None
    
    def has_weapons(self):
        """Check if inventory has weapon items"""
        return any(item.item_type in [ItemType.MELEE_WEAPON, ItemType.RANGED_WEAPON, ItemType.MAGIC_WEAPON] 
                  for item in self.items)
    
    def get_next_weapon(self):
        """Get the next weapon in the inventory rotation"""
        weapons = [i for i, item in enumerate(self.items) 
                  if item.item_type in [ItemType.MELEE_WEAPON, ItemType.RANGED_WEAPON, ItemType.MAGIC_WEAPON]]
        
        if not weapons:
            return None
            
        # Find the next weapon after the currently equipped one
        self.equipped_weapon_index = (self.equipped_weapon_index + 1) % len(weapons)
        weapon_index = weapons[self.equipped_weapon_index]
        return self.items[weapon_index]
    
    def has_potions(self):
        """Check if inventory has potion items"""
        return any(item.item_type == ItemType.POTION for item in self.items)
    
    def get_potion(self):
        """Get the first potion item"""
        for i, item in enumerate(self.items):
            if item.item_type == ItemType.POTION:
                return self.remove_item(i)
        return None
    
    def to_dict(self):
        """Convert inventory to dictionary for serialization"""
        return {
            "max_slots": self.max_slots,
            "items": [item.to_dict() for item in self.items],
            "equipped_weapon_index": self.equipped_weapon_index
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create inventory from dictionary data"""
        from duelsim.items.item import Item
        
        inventory = cls(max_slots=data.get("max_slots", 28))
        inventory.equipped_weapon_index = data.get("equipped_weapon_index", 0)
        
        for item_data in data.get("items", []):
            inventory.add_item(Item.from_dict(item_data))
            
        return inventory 