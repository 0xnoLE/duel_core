import threading
import queue
import time
import keyboard
from enum import Enum

class InputAction(Enum):
    ATTACK = "attack"
    SPECIAL_ATTACK = "special_attack"
    EAT_FOOD = "eat_food"
    SWITCH_WEAPON = "switch_weapon"
    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_EAST = "move_east"
    MOVE_WEST = "move_west"
    USE_PRAYER = "use_prayer"
    USE_POTION = "use_potion"
    TOGGLE_RUN = "toggle_run"

class InputHandler:
    """Handles keyboard input for player control"""
    
    def __init__(self, player_name):
        self.player_name = player_name
        self.input_queue = queue.Queue()
        self.running = False
        self.input_thread = None
        
        # Default key bindings
        self.key_bindings = {
            'a': InputAction.ATTACK,
            's': InputAction.SPECIAL_ATTACK,
            'e': InputAction.EAT_FOOD,
            'w': InputAction.SWITCH_WEAPON,
            'up': InputAction.MOVE_NORTH,
            'down': InputAction.MOVE_SOUTH,
            'right': InputAction.MOVE_EAST,
            'left': InputAction.MOVE_WEST,
            'p': InputAction.USE_PRAYER,
            'o': InputAction.USE_POTION,
            'r': InputAction.TOGGLE_RUN
        }
        
        # Cooldowns for actions (in seconds)
        self.cooldowns = {
            InputAction.ATTACK: 0.6,  # 1 tick
            InputAction.SPECIAL_ATTACK: 3.0,  # 5 ticks
            InputAction.EAT_FOOD: 1.8,  # 3 ticks
            InputAction.SWITCH_WEAPON: 0.6,  # 1 tick
            InputAction.USE_PRAYER: 0.6,  # 1 tick
            InputAction.USE_POTION: 1.2,  # 2 ticks
        }
        
        # Last action times for cooldown tracking
        self.last_action_times = {action: 0 for action in InputAction}
    
    def start(self):
        """Start listening for keyboard input"""
        if self.running:
            return
            
        self.running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        print(f"Input handler started for {self.player_name}")
    
    def stop(self):
        """Stop listening for keyboard input"""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=1.0)
            self.input_thread = None
        print(f"Input handler stopped for {self.player_name}")
    
    def _input_loop(self):
        """Main input loop that runs in a separate thread"""
        while self.running:
            # Check for key presses
            for key, action in self.key_bindings.items():
                if keyboard.is_pressed(key):
                    current_time = time.time()
                    last_time = self.last_action_times[action]
                    cooldown = self.cooldowns.get(action, 0)
                    
                    # Check if action is off cooldown
                    if current_time - last_time >= cooldown:
                        self.input_queue.put(action)
                        self.last_action_times[action] = current_time
                        # Small delay to prevent multiple inputs from a single press
                        time.sleep(0.1)
            
            # Don't hog the CPU
            time.sleep(0.05)
    
    def get_action(self):
        """Get the next action from the input queue, if any"""
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_key_binding(self, key, action):
        """Change a key binding"""
        if not isinstance(action, InputAction):
            raise ValueError(f"Action must be an InputAction, got {type(action)}")
        
        self.key_bindings[key] = action
        print(f"Bound key '{key}' to action '{action.value}' for {self.player_name}")
    
    def get_key_bindings(self):
        """Get all current key bindings"""
        return {k: v.value for k, v in self.key_bindings.items()} 