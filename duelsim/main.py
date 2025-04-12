import json
import time
import os
import random
from duelsim.entities.player import Player
from duelsim.engine.tick_manager import TickManager
from duelsim.engine.rules import RuleSet
from duelsim.ai.basic_agent import BasicAgent
from duelsim.utils.visualizer import DuelVisualizer
from duelsim.utils.enhanced_visualizer import EnhancedVisualizer

# Add special combat events for more excitement
SPECIAL_COMBAT_EVENTS = [
    {"name": "CRITICAL STRIKE", "message": "{attacker} lands a devastating blow on {defender}!", "damage_multiplier": 2.5},
    {"name": "COUNTER ATTACK", "message": "{defender} counters {attacker}'s move!", "counter_damage": True},
    {"name": "DODGE", "message": "{defender} skillfully dodges {attacker}'s attack!", "damage_nullify": True},
    {"name": "COMBO ATTACK", "message": "{attacker} performs a lightning-fast combo on {defender}!", "extra_attack": True},
    {"name": "LAST STAND", "message": "{defender} refuses to fall and fights with renewed strength!", "heal_percentage": 0.15},
]

# Add combat narration templates for variety
COMBAT_NARRATIONS = [
    "{attacker} strikes at {defender} with precision!",
    "{attacker} lunges forward with a powerful attack!",
    "{attacker} feints and then attacks {defender}!",
    "{attacker} circles around {defender} before striking!",
    "{attacker} tests {defender}'s defenses with a quick jab!",
    "{attacker} charges at {defender} with determination!",
]

def load_rules(filename="default_rules.json"):
    """Load rules from a JSON configuration file"""
    # Look in package config directory first
    package_config_path = os.path.join(os.path.dirname(__file__), "config", filename)
    
    # Then look in current working directory
    local_config_path = os.path.join("config", filename)
    
    # Try package path first, then local path
    for config_path in [package_config_path, local_config_path]:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
    print(f"Warning: Could not load {filename}, using default rules")
    return {}

def run_duel_simulation(max_ticks=150, visualize=True, tick_duration_ms=300, 
                        player1_config=None, player2_config=None, rules_config=None,
                        enhanced_visuals=True):
    """
    Run a complete duel simulation
    
    Args:
        max_ticks (int): Maximum number of ticks to run
        visualize (bool): Whether to visualize the simulation
        tick_duration_ms (int): Duration of each tick in milliseconds
        player1_config (dict): Configuration for player 1 (optional)
        player2_config (dict): Configuration for player 2 (optional)
        rules_config (dict): Custom rules configuration (optional)
        enhanced_visuals (bool): Whether to use enhanced visualization
    
    Returns:
        dict: Simulation results including winner, events, and final state
    """
    # Load rules
    rule_config = rules_config or load_rules()
    rules = RuleSet(rule_config)
    
    # Create tick manager
    tick_manager = TickManager(tick_duration_ms=tick_duration_ms)
    
    # Default player configs
    default_p1 = {"name": "Fighter1", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    default_p2 = {"name": "Fighter2", "hp": 99, "attack": 80, "strength": 75, "defense": 65}
    
    # Apply custom configs if provided
    if player1_config:
        default_p1.update(player1_config)
    if player2_config:
        default_p2.update(player2_config)
    
    # Create players
    player1 = Player(**default_p1)
    player2 = Player(**default_p2)
    
    # Set faster weapon speeds for more frequent attacks
    player1.weapon_speed = 2  # Attack every 2 ticks
    player2.weapon_speed = 2
    
    # Set initial positions from config or defaults
    starting_positions = rule_config.get("starting_positions", [[0, 0], [4, 4]])
    player1.position = tuple(starting_positions[0])
    player2.position = tuple(starting_positions[1])
    
    # Register players
    tick_manager.register_player(player1)
    tick_manager.register_player(player2)
    
    # Create AI agents with different aggression levels for variety
    agent1 = BasicAgent(player1, aggression=0.9)  # Very aggressive
    agent2 = BasicAgent(player2, aggression=0.8)  # Slightly less aggressive
    
    # Create visualizer - use enhanced visualizer if requested
    arena_size = rule_config.get("arena_size", {"width": 5, "height": 5})
    if enhanced_visuals and visualize:
        visualizer = EnhancedVisualizer(width=arena_size["width"], height=arena_size["height"])
    else:
        visualizer = DuelVisualizer(width=arena_size["width"], height=arena_size["height"])
    
    # Track statistics for more detailed reporting
    stats = {
        "damage": {
            player1.name: {"dealt": 0, "received": 0, "attacks": 0, "critical_hits": 0, "special_events": 0},
            player2.name: {"dealt": 0, "received": 0, "attacks": 0, "critical_hits": 0, "special_events": 0}
        },
        "movement": {
            player1.name: 0,
            player2.name: 0
        },
        "special_events": []
    }
    
    # Main simulation loop
    if visualize:
        print("Starting duel simulation...")
    current_tick = 0
    
    while current_tick < max_ticks and tick_manager.duel_active:
        # Clear screen for better visualization
        if visualize:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"=== TICK {current_tick} ===")
            visualizer.render_arena([player1, player2])
        
        # AI decision making
        if current_tick % 2 == 0:  # Every other tick to simulate thinking time
            # Get legal actions for each player
            legal_actions1 = rules.get_legal_actions(player1, tick_manager)
            legal_actions2 = rules.get_legal_actions(player2, tick_manager)
            
            # Let AI decide actions
            action1 = agent1.decide_action(legal_actions1, tick_manager, player2)
            action2 = agent2.decide_action(legal_actions2, tick_manager, player1)
            
            # Schedule actions
            if action1:
                # Extract action_type and add execute_on parameter
                action_type1 = action1.pop('type')
                action1["execute_on"] = current_tick + 1  # Next tick
                
                # Track movement statistics
                if action_type1 == "move":
                    stats["movement"][player1.name] += 1
                
                player1.add_action(action_type=action_type1, **action1)
                
            if action2:
                # Extract action_type and add execute_on parameter
                action_type2 = action2.pop('type')
                action2["execute_on"] = current_tick + 1  # Next tick
                
                # Track movement statistics
                if action_type2 == "move":
                    stats["movement"][player2.name] += 1
                
                player2.add_action(action_type=action_type2, **action2)
        
        # Process this tick
        tick_manager.current_tick = current_tick
        
        # Intercept combat events for enhanced narration and special events
        original_log_event = tick_manager.log_event
        
        def enhanced_log_event(message, event_type="info", **kwargs):
            # Check if this is a combat event
            if "attacks" in message and "for" in message and "damage" in message:
                parts = message.split()
                attacker_name = parts[0]
                defender_name = parts[2]
                damage = int(parts[4])
                
                attacker = player1 if attacker_name == player1.name else player2
                defender = player2 if attacker_name == player1.name else player1
                
                # Track attack statistics
                stats["damage"][attacker.name]["attacks"] += 1
                stats["damage"][attacker.name]["dealt"] += damage
                stats["damage"][defender.name]["received"] += damage
                
                # Random chance for special combat event (15%)
                if random.random() < 0.15:
                    special_event = random.choice(SPECIAL_COMBAT_EVENTS)
                    event_name = special_event["name"]
                    event_message = special_event["message"].format(attacker=attacker.name, defender=defender.name)
                    
                    # Apply special event effects
                    if "damage_multiplier" in special_event:
                        bonus_damage = int(damage * (special_event["damage_multiplier"] - 1))
                        defender.hp -= bonus_damage
                        damage += bonus_damage
                        stats["damage"][attacker.name]["dealt"] += bonus_damage
                        stats["damage"][defender.name]["received"] += bonus_damage
                        stats["damage"][attacker.name]["critical_hits"] += 1
                    
                    if special_event.get("counter_damage", False):
                        counter_damage = int(damage * 0.5)
                        attacker.hp -= counter_damage
                        stats["damage"][defender.name]["dealt"] += counter_damage
                        stats["damage"][attacker.name]["received"] += counter_damage
                    
                    if special_event.get("damage_nullify", False):
                        defender.hp += damage  # Restore the damage
                        stats["damage"][attacker.name]["dealt"] -= damage
                        stats["damage"][defender.name]["received"] -= damage
                        damage = 0
                    
                    if special_event.get("extra_attack", False):
                        extra_damage = int(damage * 0.7)
                        defender.hp -= extra_damage
                        stats["damage"][attacker.name]["dealt"] += extra_damage
                        stats["damage"][defender.name]["received"] += extra_damage
                        damage += extra_damage
                    
                    if "heal_percentage" in special_event:
                        heal_amount = int(defender.max_hp * special_event["heal_percentage"])
                        defender.hp = min(defender.hp + heal_amount, defender.max_hp)
                    
                    # Record the special event
                    stats["damage"][attacker.name]["special_events"] += 1
                    stats["special_events"].append({
                        "tick": current_tick,
                        "name": event_name,
                        "message": event_message,
                        "attacker": attacker.name,
                        "defender": defender.name
                    })
                    
                    # Log the special event
                    original_log_event(f"[{event_name}] {event_message}", event_type="special", **kwargs)
                    
                    # Update the damage message if it changed
                    message = f"{attacker.name} attacks {defender.name} for {damage} damage"
                
                # Use varied combat narration occasionally
                elif random.random() < 0.3:
                    narration = random.choice(COMBAT_NARRATIONS).format(
                        attacker=attacker.name, defender=defender.name)
                    original_log_event(narration, event_type="narrative", **kwargs)
            
            # Pass through to original log event
            return original_log_event(message, event_type, **kwargs)
        
        # Replace log_event temporarily
        tick_manager.log_event = enhanced_log_event
        
        # Process the tick with enhanced logging
        tick_manager.process_tick()
        
        # Restore original log_event
        tick_manager.log_event = original_log_event
        
        current_tick += 1
        
        # Slow down simulation for visualization
        if visualize:
            time.sleep(tick_duration_ms / 1000)
    
    # Print final state
    if visualize:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== FINAL STATE ===")
        visualizer.render_arena([player1, player2])
    
    # Print duel summary
    if visualize:
        print("\nDuel Summary:")
        for event in tick_manager.events:
            print(f"[Tick {event['tick']}] {event['message']}")
    
    # Determine winner
    winner = None
    if player1.hp <= 0:
        winner = player2.name
    elif player2.hp <= 0:
        winner = player1.name
    else:
        # If no clear winner, determine by remaining HP percentage
        p1_hp_percent = player1.hp / player1.max_hp
        p2_hp_percent = player2.hp / player2.max_hp
        
        if p1_hp_percent > p2_hp_percent:
            winner = player1.name
        elif p2_hp_percent > p1_hp_percent:
            winner = player2.name
        else:
            winner = "draw"
    
    # Prepare events for return
    formatted_events = []
    for event in tick_manager.events:
        formatted_event = {
            "tick": event["tick"],
            "type": event.get("event_type", "info"),
            "message": event["message"]
        }
        
        # Add combat details for attack events
        if "attacks" in event["message"] and "for" in event["message"] and "damage" in event["message"]:
            parts = event["message"].split()
            attacker = parts[0]
            defender = parts[2]
            damage = int(parts[4])
            
            formatted_event.update({
                "type": "attack",
                "attack_type": "melee",
                "attacker": attacker,
                "defender": defender,
                "damage": damage
            })
        
        formatted_events.append(formatted_event)
    
    # Add final victory event
    formatted_events.append({
        "tick": current_tick,
        "type": "victory",
        "winner": winner,
        "message": f"The duel ends with {winner} as the victor!" if winner != "draw" else "The duel ends in a draw!"
    })
    
    # Return comprehensive result
    return {
        "winner": winner,
        "events": formatted_events,
        "final_state": {
            "player1": {
                "name": player1.name,
                "hp": max(0, player1.hp),
                "max_hp": player1.max_hp,
                "attack": player1.attack,
                "strength": player1.strength,
                "defense": player1.defense,
                "position": player1.position
            },
            "player2": {
                "name": player2.name,
                "hp": max(0, player2.hp),
                "max_hp": player2.max_hp,
                "attack": player2.attack,
                "strength": player2.strength,
                "defense": player2.defense,
                "position": player2.position
            },
            "ticks": current_tick
        },
        "statistics": stats
    }

def main():
    """Run a simple demonstration"""
    result = run_duel_simulation()
    print(f"\nWinner: {result['winner']}")

if __name__ == "__main__":
    main() 