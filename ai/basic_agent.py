import random

class BasicAgent:
    def __init__(self, player, aggression=0.7):
        self.player = player
        self.aggression = aggression  # Higher = more likely to attack
        
    def decide_action(self, legal_actions, game_state, opponent):
        """Decide which action to take based on simple heuristics"""
        if not legal_actions:
            return None
            
        # If low health and can eat, sometimes choose to eat
        if self.player.hp < self.player.max_hp * 0.5:
            eat_actions = [a for a in legal_actions if a["type"] == "eat"]
            if eat_actions and random.random() > self.aggression:
                return eat_actions[0]
        
        # If can attack and feeling aggressive, attack
        if random.random() < self.aggression:
            attack_actions = [a for a in legal_actions if a["type"].startswith("attack")]
            if attack_actions:
                action = random.choice(attack_actions)
                action["target"] = opponent
                return action
        
        # Otherwise, consider moving
        move_actions = [a for a in legal_actions if a["type"] == "move"]
        if move_actions:
            return random.choice(move_actions)
            
        # Fallback to random action
        return random.choice(legal_actions) 