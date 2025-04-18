from duelsim.input.input_handler import InputHandler, InputAction

class HumanController:
    """Controller for human player input"""
    
    def __init__(self, player):
        self.player = player
        self.input_handler = InputHandler(player.name)
        self.input_handler.start()
        
        # Action mapping
        self.action_mapping = {
            InputAction.ATTACK: self._handle_attack,
            InputAction.SPECIAL_ATTACK: self._handle_special_attack,
            InputAction.EAT_FOOD: self._handle_eat_food,
            InputAction.SWITCH_WEAPON: self._handle_switch_weapon,
            InputAction.MOVE_NORTH: lambda: self._handle_move(0, -1),
            InputAction.MOVE_SOUTH: lambda: self._handle_move(0, 1),
            InputAction.MOVE_EAST: lambda: self._handle_move(1, 0),
            InputAction.MOVE_WEST: lambda: self._handle_move(-1, 0),
            InputAction.USE_PRAYER: self._handle_use_prayer,
            InputAction.USE_POTION: self._handle_use_potion,
            InputAction.TOGGLE_RUN: self._handle_toggle_run
        }
        
        # State
        self.target = None
        self.is_running = False
    
    def update(self, game_state, tick):
        """Process input and update player actions"""
        # Get the next input action, if any
        action = self.input_handler.get_action()
        
        if action:
            # Set target if not set
            if self.target is None and len(game_state.players) > 1:
                for player in game_state.players:
                    if player != self.player:
                        self.target = player
                        break
            
            # Handle the action
            handler = self.action_mapping.get(action)
            if handler:
                return handler(game_state, tick)
        
        return None
    
    def _handle_attack(self, game_state, tick):
        """Handle attack action"""
        if self.target and self.player.cooldown <= 0:
            return {
                "type": "attack",
                "target": self.target,
                "execute_on": tick
            }
        return None
    
    def _handle_special_attack(self, game_state, tick):
        """Handle special attack action"""
        if self.target and self.player.cooldown <= 0:
            # Check if player has special attack energy
            if hasattr(self.player, 'special_energy') and self.player.special_energy >= 25:
                self.player.special_energy -= 25  # Use 25% special energy
                return {
                    "type": "special_attack",
                    "target": self.target,
                    "execute_on": tick
                }
        return None
    
    def _handle_eat_food(self, game_state, tick):
        """Handle eat food action"""
        # Check if player has food
        if hasattr(self.player, 'inventory') and self.player.inventory.has_food():
            food = self.player.inventory.get_food()
            return {
                "type": "eat_food",
                "food": food,
                "execute_on": tick
            }
        return None
    
    def _handle_switch_weapon(self, game_state, tick):
        """Handle weapon switch action"""
        if hasattr(self.player, 'inventory') and self.player.inventory.has_weapons():
            next_weapon = self.player.inventory.get_next_weapon()
            return {
                "type": "switch_weapon",
                "weapon": next_weapon,
                "execute_on": tick
            }
        return None
    
    def _handle_move(self, dx, dy, game_state, tick):
        """Handle movement action"""
        x, y = self.player.position
        new_x, new_y = x + dx, y + dy
        
        # Check if movement is valid
        if game_state.is_valid_position(new_x, new_y):
            return {
                "type": "move",
                "position": (new_x, new_y),
                "execute_on": tick,
                "running": self.is_running
            }
        return None
    
    def _handle_use_prayer(self, game_state, tick):
        """Handle prayer activation"""
        if hasattr(self.player, 'prayers'):
            return {
                "type": "toggle_prayer",
                "execute_on": tick
            }
        return None
    
    def _handle_use_potion(self, game_state, tick):
        """Handle potion use"""
        if hasattr(self.player, 'inventory') and self.player.inventory.has_potions():
            potion = self.player.inventory.get_potion()
            return {
                "type": "use_potion",
                "potion": potion,
                "execute_on": tick
            }
        return None
    
    def _handle_toggle_run(self, game_state, tick):
        """Handle run toggle"""
        self.is_running = not self.is_running
        return {
            "type": "toggle_run",
            "running": self.is_running,
            "execute_on": tick
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.input_handler.stop() 