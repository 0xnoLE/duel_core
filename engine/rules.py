class RuleSet:
    def __init__(self, rules_config=None):
        # Default rules
        self.rules = {
            "allow_melee": True,
            "allow_ranged": True,
            "allow_magic": True,
            "no_food": True,  # Disable healing
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
            arena_size = self.rules.get("arena_size", {"width": 5, "height": 5})
            width, height = arena_size["width"], arena_size["height"]
            
            # Get positions of other players to avoid collisions
            other_positions = []
            for other_player in game_state.players:
                if other_player != player:
                    other_positions.append(other_player.position)
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < width and 0 <= new_y < height and 
                    (new_x, new_y) not in other_positions):
                    legal_actions.append({
                        "type": "move", 
                        "destination": (new_x, new_y)
                    })
        
        # Check if player can eat
        if not self.rules["no_food"] and player.hp < player.max_hp:
            # More significant healing to make it worthwhile
            heal_amount = min(25, player.max_hp - player.hp)  # Heal up to 25 HP but don't overheal
            legal_actions.append({"type": "eat", "heal_amount": heal_amount})
            
        return legal_actions 