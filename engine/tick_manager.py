import time

class TickManager:
    def __init__(self, tick_duration_ms=600):
        self.TICK_DURATION_MS = tick_duration_ms
        self.current_tick = 0
        self.duel_active = False
        self.players = []
        self.events = []
        
    def register_player(self, player):
        """Add a player to the duel"""
        self.players.append(player)
        
    def start_duel(self):
        """Begin the duel loop"""
        self.duel_active = True
        self.current_tick = 0
        self.run()
        
    def end_duel(self):
        """End the duel"""
        self.duel_active = False
        
    def run(self):
        """Main tick loop"""
        while self.duel_active:
            start_time = time.time()
            
            # Process this tick
            self.current_tick += 1
            self.process_tick()
            
            # Sleep for remainder of tick duration
            elapsed = (time.time() - start_time) * 1000
            sleep_time = max(0, (self.TICK_DURATION_MS - elapsed) / 1000)
            time.sleep(sleep_time)
            
    def process_tick(self):
        """Process a single game tick"""
        # Process player actions
        for player in self.players:
            self.process_actions(player)
            
        # Update game state
        self.update_game_state()
        
    def process_actions(self, player):
        """Process actions for a player on this tick"""
        if player.is_action_ready(self.current_tick):
            action = player.next_action
            self.execute_action(player, action)
            player.next_action = None
            
    def execute_action(self, player, action):
        """Execute a specific action"""
        action_type = action.get("type")
        
        if action_type == "attack":
            from engine.combat import resolve_attack
            target = action.get("target")
            resolve_attack(player, target)
            
        elif action_type == "move":
            destination = action.get("destination")
            player.position = destination
            self.log_event(f"{player.name} moved to {destination}")
            
        elif action_type == "eat":
            heal_amount = action.get("heal_amount", 0)
            player.hp = min(player.max_hp, player.hp + heal_amount)
            self.log_event(f"{player.name} healed for {heal_amount}")
    
    def update_game_state(self):
        """Update game state after actions are processed"""
        # Update cooldowns
        for player in self.players:
            player.update_cooldowns()
            
        # Check win conditions
        for player in self.players:
            if player.hp <= 0:
                opponent = [p for p in self.players if p != player][0]
                self.log_event(f"{opponent.name} has defeated {player.name}!")
                self.end_duel()
                
    def log_event(self, message):
        """Log a game event"""
        self.events.append({
            "tick": self.current_tick,
            "message": message
        })
        print(f"[Tick {self.current_tick}] {message}") 