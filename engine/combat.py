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
        # Very high hit chance (90%) for more consistent combat
        accuracy_roll = random.random() < 0.9
        
        # More consistent damage calculation with controlled RNG
        base_damage = attacker.strength // 7  # Higher base damage
        
        # Add randomness but ensure minimum damage
        variance = random.randint(0, 5)  # 0-5 random variance
        max_hit = base_damage + variance
        
        # Reduced defense impact for more consistent damage
        defense_factor = defender.defense / 400  # Even less reduction from defense
        damage = max(3, int(max_hit * (1 - defense_factor))) if accuracy_roll else 0
        
        defender.hp -= damage
        attacker.cooldown = attacker.weapon_speed
        
        # Log the attack result
        if damage > 0:
            print(f"{attacker.name} hits {damage} on {defender.name}")
        else:
            print(f"{attacker.name} misses {defender.name}")
        
        return damage
    return 0 

def calculate_damage(attacker, defender, tick_manager):
    """Calculate damage for an attack with special effects"""
    # Get base damage using standard formula
    base_damage = calculate_base_damage(attacker, defender)
    
    # Apply special effects
    damage, effects_triggered = apply_special_effects(attacker, defender, base_damage, tick_manager)
    
    return damage, effects_triggered

def calculate_base_damage(attacker, defender):
    """Calculate base damage using combat formulas"""
    # Get effective stats
    attack = attacker.effective_stats["attack"]
    strength = attacker.effective_stats["strength"]
    defense = defender.effective_stats["defense"]
    
    # Calculate hit chance (simplified formula)
    hit_chance = min(0.9, attack / (attack + defense))
    
    # Roll for hit
    if random.random() > hit_chance:
        return 0  # Miss
    
    # Calculate damage (simplified formula)
    max_hit = 1 + (strength / 10)
    damage = random.randint(0, int(max_hit))
    
    return damage

def apply_special_effects(attacker, defender, base_damage, tick_manager):
    """Apply special effects from equipment to damage calculation"""
    damage = base_damage
    effects_triggered = []
    
    # Get all special effects from attacker's equipment
    attacker_effects = attacker.get_special_effects()
    
    # Apply offensive effects
    for effect in attacker_effects:
        effect_type = effect["effect"]
        effect_value = effect["value"]
        
        # Critical strike chance
        if effect_type == "critical_chance" and random.random() < effect_value/100:
            damage = int(damage * 2)
            effects_triggered.append({
                "type": "critical_hit",
                "actor": attacker.name,
                "target": defender.name,
                "message": f"{attacker.name} lands a critical hit!"
            })
        
        # Life steal
        elif effect_type == "life_steal" and damage > 0:
            heal_amount = int(damage * effect_value/100)
            if heal_amount > 0:
                attacker.hp = min(attacker.max_hp, attacker.hp + heal_amount)
                effects_triggered.append({
                    "type": "life_steal",
                    "actor": attacker.name,
                    "heal": heal_amount,
                    "message": f"{attacker.name} steals {heal_amount} life!"
                })
        
        # Double strike
        elif effect_type == "double_strike" and random.random() < effect_value/100:
            extra_damage = calculate_base_damage(attacker, defender)
            damage += extra_damage
            effects_triggered.append({
                "type": "double_strike",
                "actor": attacker.name,
                "target": defender.name,
                "extra_damage": extra_damage,
                "message": f"{attacker.name} strikes twice in rapid succession!"
            })
        
        # Poison chance
        elif effect_type == "poison_chance" and random.random() < effect_value/100:
            # Add poison effect to defender
            poison_damage = max(1, int(damage * 0.2))
            poison_duration = 3
            
            # Schedule poison damage for future ticks
            for i in range(1, poison_duration + 1):
                tick_manager.schedule_event(
                    tick_manager.current_tick + i,
                    lambda: apply_poison_damage(attacker, defender, poison_damage, tick_manager)
                )
            
            effects_triggered.append({
                "type": "poison",
                "actor": attacker.name,
                "target": defender.name,
                "duration": poison_duration,
                "message": f"{defender.name} is poisoned!"
            })
    
    # Get defender's effects
    defender_effects = defender.get_special_effects()
    
    # Apply defensive effects
    for effect in defender_effects:
        effect_type = effect["effect"]
        effect_value = effect["value"]
        
        # Dodge chance
        if effect_type == "dodge_chance" and random.random() < effect_value/100:
            damage = 0
            effects_triggered.append({
                "type": "dodge",
                "actor": defender.name,
                "message": f"{defender.name} dodges the attack!"
            })
            break  # No need to check other defensive effects if dodged
        
        # Damage reflection
        elif effect_type == "damage_reflection" and damage > 0:
            reflect_damage = int(damage * effect_value/100)
            if reflect_damage > 0:
                attacker.hp -= reflect_damage
                effects_triggered.append({
                    "type": "damage_reflection",
                    "actor": defender.name,
                    "target": attacker.name,
                    "damage": reflect_damage,
                    "message": f"{defender.name} reflects {reflect_damage} damage back to {attacker.name}!"
                })
    
    return damage, effects_triggered

def apply_poison_damage(attacker, defender, damage, tick_manager):
    """Apply poison damage on a scheduled tick"""
    if defender.hp <= 0:
        return  # Don't apply poison to dead players
    
    defender.hp -= damage
    
    # Log the poison damage event
    tick_manager.log_event(
        f"{defender.name} takes {damage} poison damage from {attacker.name}!",
        event_type="poison_damage",
        actor=attacker.name,
        target=defender.name,
        damage=damage,
        tick=tick_manager.current_tick
    ) 