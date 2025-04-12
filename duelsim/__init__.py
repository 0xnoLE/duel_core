"""
DuelSim - A turn-based duel simulation engine
"""
import random
import math

__version__ = "0.1.0"

# Only export the main function
def run_duel_simulation(max_ticks=150, visualize=True, tick_duration_ms=300,
                        player1_config=None, player2_config=None, rules_config=None):
    """
    Simulation function with randomized combat outcomes
    """
    print("Running duel simulation...")
    
    # Default player configs
    default_p1 = {"name": "Fighter1", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    default_p2 = {"name": "Fighter2", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    
    # Apply custom configs if provided
    if player1_config:
        default_p1.update(player1_config)
    if player2_config:
        default_p2.update(player2_config)
    
    # Create working copies of player stats that will change during combat
    p1 = default_p1.copy()
    p2 = default_p2.copy()
    p1["current_hp"] = p1["hp"]
    p2["current_hp"] = p2["hp"]
    
    # Track positions
    p1["position"] = [0, 0]
    p2["position"] = [4, 4]
    
    # Generate events with randomized outcomes
    events = []
    current_tick = 0
    
    # Opening narrative
    events.append({
        "tick": current_tick,
        "type": "narrative",
        "message": f"The duel between {p1['name']} and {p2['name']} begins!"
    })
    current_tick += 1
    
    # Combat stats
    p1_damage_dealt = 0
    p2_damage_dealt = 0
    p1_attacks = 0
    p2_attacks = 0
    p1_crits = 0
    p2_crits = 0
    p1_movements = 0
    p2_movements = 0
    
    # Main simulation loop
    while current_tick < max_ticks and p1["current_hp"] > 0 and p2["current_hp"] > 0:
        # Determine actions based on randomness
        action_roll = random.random()
        
        # Player 1's turn (roughly every other tick)
        if current_tick % 2 == 0:
            if action_roll < 0.3:  # 30% chance to move
                # Movement
                old_pos = p1["position"].copy()
                # Move toward opponent
                dx = p2["position"][0] - p1["position"][0]
                dy = p2["position"][1] - p1["position"][1]
                
                # Normalize and move
                if abs(dx) > 0 or abs(dy) > 0:
                    if abs(dx) > abs(dy):
                        p1["position"][0] += 1 if dx > 0 else -1
                    else:
                        p1["position"][1] += 1 if dy > 0 else -1
                
                events.append({
                    "tick": current_tick,
                    "type": "movement",
                    "actor": p1["name"],
                    "from_position": old_pos,
                    "to_position": p1["position"].copy(),
                    "message": f"{p1['name']} moves closer to {p2['name']}"
                })
                p1_movements += 1
            else:
                # Calculate distance between players
                distance = math.sqrt((p1["position"][0] - p2["position"][0])**2 + 
                                    (p1["position"][1] - p2["position"][1])**2)
                
                if distance <= 1.5:  # Close enough to attack
                    # Attack calculation with randomness
                    attack_roll = random.random()
                    is_critical = attack_roll > 0.85  # 15% chance of critical hit
                    
                    # Base damage calculation
                    accuracy = p1["attack"] / 100  # 0.0-1.0 scale
                    hit_chance = 0.5 + (accuracy * 0.4)  # 50-90% hit chance
                    
                    if random.random() < hit_chance:  # Hit connects
                        # Damage calculation
                        base_damage = random.randint(5, 15)
                        strength_bonus = p1["strength"] / 10
                        defense_reduction = p2["defense"] / 200  # 0-0.5 reduction
                        
                        damage = int(base_damage * (1 + strength_bonus) * (1 - defense_reduction))
                        
                        if is_critical:
                            damage = int(damage * 2)
                            p1_crits += 1
                        
                        # Apply damage
                        p2["current_hp"] -= damage
                        p1_damage_dealt += damage
                        p1_attacks += 1
                        
                        # Create event
                        events.append({
                            "tick": current_tick,
                            "type": "attack",
                            "attack_type": "melee",
                            "attacker": p1["name"],
                            "defender": p2["name"],
                            "damage": damage,
                            "is_critical": is_critical,
                            "defender_hp_before": p2["current_hp"] + damage,
                            "defender_hp_after": p2["current_hp"],
                            "message": f"{p1['name']} {'lands a CRITICAL HIT on' if is_critical else 'strikes'} {p2['name']} for {damage} damage!"
                        })
                    else:
                        # Miss
                        events.append({
                            "tick": current_tick,
                            "type": "attack",
                            "attack_type": "melee",
                            "attacker": p1["name"],
                            "defender": p2["name"],
                            "damage": 0,
                            "message": f"{p1['name']} attacks but misses {p2['name']}"
                        })
                        p1_attacks += 1
                else:
                    # Too far to attack, must move
                    old_pos = p1["position"].copy()
                    # Move toward opponent
                    dx = p2["position"][0] - p1["position"][0]
                    dy = p2["position"][1] - p1["position"][1]
                    
                    # Normalize and move
                    if abs(dx) > 0 or abs(dy) > 0:
                        if abs(dx) > abs(dy):
                            p1["position"][0] += 1 if dx > 0 else -1
                        else:
                            p1["position"][1] += 1 if dy > 0 else -1
                    
                    events.append({
                        "tick": current_tick,
                        "type": "movement",
                        "actor": p1["name"],
                        "from_position": old_pos,
                        "to_position": p1["position"].copy(),
                        "message": f"{p1['name']} moves toward {p2['name']}"
                    })
                    p1_movements += 1
        
        # Player 2's turn (roughly every other tick)
        else:
            if action_roll < 0.3:  # 30% chance to move
                # Movement
                old_pos = p2["position"].copy()
                # Move toward opponent
                dx = p1["position"][0] - p2["position"][0]
                dy = p1["position"][1] - p2["position"][1]
                
                # Normalize and move
                if abs(dx) > 0 or abs(dy) > 0:
                    if abs(dx) > abs(dy):
                        p2["position"][0] += 1 if dx > 0 else -1
                    else:
                        p2["position"][1] += 1 if dy > 0 else -1
                
                events.append({
                    "tick": current_tick,
                    "type": "movement",
                    "actor": p2["name"],
                    "from_position": old_pos,
                    "to_position": p2["position"].copy(),
                    "message": f"{p2['name']} moves closer to {p1['name']}"
                })
                p2_movements += 1
            else:
                # Calculate distance between players
                distance = math.sqrt((p1["position"][0] - p2["position"][0])**2 + 
                                    (p1["position"][1] - p2["position"][1])**2)
                
                if distance <= 1.5:  # Close enough to attack
                    # Attack calculation with randomness
                    attack_roll = random.random()
                    is_critical = attack_roll > 0.85  # 15% chance of critical hit
                    
                    # Base damage calculation
                    accuracy = p2["attack"] / 100  # 0.0-1.0 scale
                    hit_chance = 0.5 + (accuracy * 0.4)  # 50-90% hit chance
                    
                    if random.random() < hit_chance:  # Hit connects
                        # Damage calculation
                        base_damage = random.randint(5, 15)
                        strength_bonus = p2["strength"] / 10
                        defense_reduction = p1["defense"] / 200  # 0-0.5 reduction
                        
                        damage = int(base_damage * (1 + strength_bonus) * (1 - defense_reduction))
                        
                        if is_critical:
                            damage = int(damage * 2)
                            p2_crits += 1
                        
                        # Apply damage
                        p1["current_hp"] -= damage
                        p2_damage_dealt += damage
                        p2_attacks += 1
                        
                        # Create event
                        events.append({
                            "tick": current_tick,
                            "type": "attack",
                            "attack_type": "melee",
                            "attacker": p2["name"],
                            "defender": p1["name"],
                            "damage": damage,
                            "is_critical": is_critical,
                            "defender_hp_before": p1["current_hp"] + damage,
                            "defender_hp_after": p1["current_hp"],
                            "message": f"{p2['name']} {'lands a CRITICAL HIT on' if is_critical else 'strikes'} {p1['name']} for {damage} damage!"
                        })
                    else:
                        # Miss
                        events.append({
                            "tick": current_tick,
                            "type": "attack",
                            "attack_type": "melee",
                            "attacker": p2["name"],
                            "defender": p1["name"],
                            "damage": 0,
                            "message": f"{p2['name']} attacks but misses {p1['name']}"
                        })
                        p2_attacks += 1
                else:
                    # Too far to attack, must move
                    old_pos = p2["position"].copy()
                    # Move toward opponent
                    dx = p1["position"][0] - p2["position"][0]
                    dy = p1["position"][1] - p2["position"][1]
                    
                    # Normalize and move
                    if abs(dx) > 0 or abs(dy) > 0:
                        if abs(dx) > abs(dy):
                            p2["position"][0] += 1 if dx > 0 else -1
                        else:
                            p2["position"][1] += 1 if dy > 0 else -1
                    
                    events.append({
                        "tick": current_tick,
                        "type": "movement",
                        "actor": p2["name"],
                        "from_position": old_pos,
                        "to_position": p2["position"].copy(),
                        "message": f"{p2['name']} moves toward {p1['name']}"
                    })
                    p2_movements += 1
        
        # Occasionally add special moves or narrative events
        if current_tick > 0 and current_tick % 10 == 0:
            # Add a special move or narrative event
            special_roll = random.random()
            
            if special_roll < 0.5:
                # Player 1 special
                events.append({
                    "tick": current_tick,
                    "type": "special",
                    "actor": p1["name"],
                    "move_name": random.choice(["Power Attack", "Quick Strike", "Defensive Stance"]),
                    "message": f"{p1['name']} prepares a special move"
                })
            else:
                # Player 2 special
                events.append({
                    "tick": current_tick,
                    "type": "special",
                    "actor": p2["name"],
                    "move_name": random.choice(["Power Attack", "Quick Strike", "Defensive Stance"]),
                    "message": f"{p2['name']} prepares a special move"
                })
        
        # Increment tick
        current_tick += 1
    
    # Determine winner and add victory event
    winner = None
    if p1["current_hp"] <= 0:
        winner = p2["name"]
        events.append({
            "tick": current_tick,
            "type": "victory",
            "winner": p2["name"],
            "message": f"{p1['name']} is defeated! {p2['name']} is victorious!"
        })
    elif p2["current_hp"] <= 0:
        winner = p1["name"]
        events.append({
            "tick": current_tick,
            "type": "victory",
            "winner": p1["name"],
            "message": f"{p2['name']} is defeated! {p1['name']} is victorious!"
        })
    else:
        winner = "draw"
        events.append({
            "tick": current_tick,
            "type": "draw",
            "message": f"The duel ends in a draw after {current_tick} ticks!"
        })
    
    # Compile statistics
    stats = {
        "duration": {
            "ticks": current_tick,
            "seconds": current_tick * (tick_duration_ms/1000)
        },
        "damage": {
            p1["name"]: {
                "dealt": p1_damage_dealt,
                "received": p2_damage_dealt,
                "attacks": p1_attacks,
                "critical_hits": p1_crits
            },
            p2["name"]: {
                "dealt": p2_damage_dealt,
                "received": p1_damage_dealt,
                "attacks": p2_attacks,
                "critical_hits": p2_crits
            }
        },
        "movement": {
            p1["name"]: p1_movements,
            p2["name"]: p2_movements
        }
    }
    
    # Return enhanced result
    return {
        "winner": winner,
        "events": events,
        "final_state": {
            "player1": {
                "name": p1["name"],
                "hp": max(0, p1["current_hp"]),
                "max_hp": p1["hp"],
                "attack": p1["attack"],
                "strength": p1["strength"],
                "defense": p1["defense"],
                "position": p1["position"]
            },
            "player2": {
                "name": p2["name"],
                "hp": max(0, p2["current_hp"]),
                "max_hp": p2["hp"],
                "attack": p2["attack"],
                "strength": p2["strength"],
                "defense": p2["defense"],
                "position": p2["position"]
            },
            "ticks": current_tick
        },
        "statistics": stats
    } 