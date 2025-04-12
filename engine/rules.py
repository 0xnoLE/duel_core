class RuleSet:
    def __init__(self, rules_config=None):
        # Default rules
        self.rules = {
            "allow_melee": True,
            "allow_ranged": True,
            "allow_magic": True,
            "no_food": False,
            "no_movement": False,
            "lock_slots": {}
        }
        
        # Override with provided config
        if rules_config:
            self.rules.update(rules_config)
    
    def is_action_allowed(self, action_type, player=None, game_state=None):
        """Check if an action is allowed under current rules"""
        if action_type == "attack_melee" and not self.rules["allow_melee"]:
            return False
        elif action_type == "attack_ranged" and not self.rules["allow_ranged"]:
            return False
        elif action_type == "attack_magic" and not self.rules["allow_magic"]:
            return False
        elif action_type == "eat" and self.rules["no_food"]:
            return False
        elif action_type == "move" and self.rules["no_movement"]:
            return False
        
        return True
    
    def get_legal_actions(self, player, game_state):
        """Get all legal actions for a player in the current state"""
        legal_actions = []
        
        # Check if player can attack
        if player.cooldown == 0:
            if self.rules["allow_melee"]:
                legal_actions.append({"type": "attack_melee"})
            if self.rules["allow_ranged"]:
                legal_actions.append({"type": "attack_ranged"})
            if self.rules["allow_magic"]:
                legal_actions.append({"type": "attack_magic"})
        
        # Check if player can move
        if not self.rules["no_movement"]:
            # Simplified movement options (cardinal directions)
            x, y = player.position
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                legal_actions.append({
                    "type": "move", 
                    "destination": (x + dx, y + dy)
                })
        
        # Check if player can eat
        if not self.rules["no_food"] and player.hp < player.max_hp:
            legal_actions.append({"type": "eat", "heal_amount": 20})
            
        return legal_actions 