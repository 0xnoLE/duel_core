import random

def rng():
    """Simple RNG for hit chance"""
    return random.random()  # Returns a value between 0.0 and 1.0

def calculate_max_hit(attacker):
    """Calculate maximum possible hit"""
    # Simplified formula based on strength
    base_damage = attacker.strength // 10
    return base_damage + random.randint(0, base_damage // 2)

def resolve_attack(attacker, defender):
    """Resolve an attack between two players"""
    # Calculate distance between players
    x1, y1 = attacker.position
    x2, y2 = defender.position
    distance = abs(x1 - x2) + abs(y1 - y2)  # Manhattan distance
    
    # Check if target is in range (adjacent for melee)
    if distance > 1:  # For melee attacks
        print(f"{attacker.name} is too far from {defender.name} to attack")
        return 0
        
    if attacker.cooldown == 0:
        # Implement proper RNG function
        accuracy_roll = random.random() < (attacker.attack / 100)
        
        # Calculate damage based on strength
        base_damage = attacker.strength // 10
        max_hit = base_damage + random.randint(0, base_damage // 2)
        
        # Apply defense reduction
        damage_reduction = defender.defense / 200  # 50% reduction at 100 defense
        damage = int(max_hit * (1 - damage_reduction)) if accuracy_roll else 0
        
        defender.hp -= damage
        attacker.cooldown = attacker.weapon_speed
        
        # Log the attack result
        if damage > 0:
            print(f"{attacker.name} hits {damage} on {defender.name}")
        else:
            print(f"{attacker.name} misses {defender.name}")
        
        return damage
    return 0 