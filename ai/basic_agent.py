import random

class BasicAgent:
    def __init__(self, player, aggression=0.7):
        self.player = player
        self.aggression = aggression  # Higher = more likely to attack
        
    def decide_action(self, legal_actions, game_state, opponent):
        """Decide which action to take based on simple heuristics"""
        if not legal_actions:
            return None
            
        # Calculate distance to opponent
        x1, y1 = self.player.position
        x2, y2 = opponent.position
        distance = abs(x1 - x2) + abs(y1 - y2)
        
        # If low health and can eat, sometimes choose to eat
        if self.player.hp < self.player.max_hp * 0.5:
            eat_actions = [a for a in legal_actions if a["type"] == "eat"]
            if eat_actions and random.random() > self.aggression:
                return eat_actions[0]
        
        # If adjacent to opponent and can attack, prioritize attacking
        if distance <= 1 and self.player.cooldown == 0:
            attack_actions = [a for a in legal_actions if a["type"].startswith("attack")]
            if attack_actions and random.random() < self.aggression:
                action = random.choice(attack_actions)
                action["target"] = opponent
                return action
        
        # If not adjacent to opponent, try to move closer
        if distance > 1:
            move_actions = [a for a in legal_actions if a["type"] == "move"]
            if move_actions:
                # Find moves that bring us closer to opponent
                best_moves = []
                for move in move_actions:
                    new_x, new_y = move["destination"]
                    new_distance = abs(new_x - x2) + abs(new_y - y2)
                    if new_distance < distance:
                        best_moves.append(move)
                
                if best_moves:
                    return random.choice(best_moves)
        
        # Otherwise, consider any move
        move_actions = [a for a in legal_actions if a["type"] == "move"]
        if move_actions:
            return random.choice(move_actions)
            
        # Fallback to random action
        return random.choice(legal_actions) 