class Player:
    def __init__(self, name, hp=99, attack=70, strength=70, defense=70):
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