import time

class TickManager:
    def __init__(self, tick_duration_ms=600):
        self.TICK_DURATION_MS = tick_duration_ms
        self.current_tick = 0
        self.duel_active = True
        self.players = []
        self.events = []
        
    def register_player(self, player):
        """Add a player to the duel"""
        self.players.append(player)
        
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
            # Add game state reference to the action execution
            self.execute_action(player, action)
            player.next_action = None
            
    def execute_action(self, player, action):
        """Execute a specific action"""
        action_type = action.get("type")
        
        if action_type == "attack" or action_type.startswith("attack_"):
            from engine.combat import resolve_attack
            target = action.get("target")
            damage = resolve_attack(player, target)
            self.log_event(f"{player.name} attacks {target.name} for {damage} damage")
            
        elif action_type == "move":
            destination = action.get("destination")
            player.position = destination
            self.log_event(f"{player.name} moved to {destination}")
            
        elif action_type == "eat":
            heal_amount = action.get("heal_amount", 0)
            old_hp = player.hp
            player.hp = min(player.max_hp, player.hp + heal_amount)
            actual_heal = player.hp - old_hp
            self.log_event(f"{player.name} healed for {actual_heal}")
    
    def update_game_state(self):
        """Update game state after actions are processed"""
        # Update cooldowns
        for player in self.players:
            player.update_cooldowns()
            
        # Log health milestones to create tension
        for player in self.players:
            opponent = [p for p in self.players if p != player][0]
            
            # Log when players reach certain health thresholds
            if player.hp <= 50 and player.hp > 40 and not any(e['message'].startswith(f"{player.name} is at half") for e in self.events):
                self.log_event(f"{player.name} is at half health!")
                
            if player.hp <= 25 and player.hp > 0:
                if player.hp <= 10:
                    if not any(e['message'].startswith(f"{player.name} is critically") for e in self.events[-10:]):
                        self.log_event(f"{player.name} is critically wounded ({player.hp} HP)!")
                elif not any(e['message'].startswith(f"{player.name} is badly") for e in self.events[-10:]):
                    self.log_event(f"{player.name} is badly wounded!")
                    
            # Log when a player has a significant health advantage
            health_diff = player.hp - opponent.hp
            if health_diff >= 30 and not any(e['message'].startswith(f"{player.name} has a significant") for e in self.events[-15:]):
                self.log_event(f"{player.name} has a significant health advantage!")
        
        # Check win conditions
        for player in self.players:
            if player.hp <= 0:
                opponent = [p for p in self.players if p != player][0]
                self.log_event(f"{opponent.name} has defeated {player.name}!")
                self.duel_active = False
                
    def log_event(self, message):
        """Log a game event"""
        self.events.append({
            "tick": self.current_tick,
            "message": message
        })
        print(f"[Tick {self.current_tick}] {message}") 