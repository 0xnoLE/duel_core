import random

def rng():
    """Simple RNG for hit chance"""
    return random.random() < 0.7  # 70% hit chance for simplicity

def calculate_max_hit(attacker):
    """Calculate maximum possible hit"""
    # Simplified formula based on strength
    base_damage = attacker.strength // 10
    return random.randint(0, base_damage * 2)

def resolve_attack(attacker, defender):
    """Resolve an attack between two players"""
    if attacker.cooldown == 0:
        accuracy_roll = rng()
        damage = calculate_max_hit(attacker) if accuracy_roll else 0
        defender.hp -= damage
        attacker.cooldown = attacker.weapon_speed
        
        # Log the attack result
        if damage > 0:
            print(f"{attacker.name} hits {damage} on {defender.name}")
        else:
            print(f"{attacker.name} misses {defender.name}")
        
        return damage
    return 0 