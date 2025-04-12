import json
import time
import os
from duelsim.entities.player import Player
from duelsim.engine.tick_manager import TickManager
from duelsim.engine.rules import RuleSet
from duelsim.ai.basic_agent import BasicAgent
from duelsim.utils.visualizer import DuelVisualizer

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
                        player1_config=None, player2_config=None, rules_config=None):
    """
    Run a complete duel simulation
    
    Args:
        max_ticks (int): Maximum number of ticks to run
        visualize (bool): Whether to visualize the simulation
        tick_duration_ms (int): Duration of each tick in milliseconds
        player1_config (dict): Configuration for player 1 (optional)
        player2_config (dict): Configuration for player 2 (optional)
        rules_config (dict): Custom rules configuration (optional)
    
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
    
    # Create visualizer
    arena_size = rule_config.get("arena_size", {"width": 5, "height": 5})
    visualizer = DuelVisualizer(width=arena_size["width"], height=arena_size["height"])
    
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
                player1.add_action(action_type=action_type1, **action1)
                
            if action2:
                # Extract action_type and add execute_on parameter
                action_type2 = action2.pop('type')
                action2["execute_on"] = current_tick + 1  # Next tick
                player2.add_action(action_type=action_type2, **action2)
        
        # Process this tick
        tick_manager.current_tick = current_tick
        tick_manager.process_tick()
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
        if visualize:
            print(f"\nWinner: {player2.name}")
    elif player2.hp <= 0:
        winner = player1.name
        if visualize:
            print(f"\nWinner: {player1.name}")
    else:
        winner = "draw"
        if visualize:
            print("\nDuel ended in a draw (max ticks reached)")
    
    # Return simulation results
    return {
        "winner": winner,
        "events": tick_manager.events,
        "final_state": {
            "player1": {
                "name": player1.name,
                "hp": player1.hp,
                "position": player1.position
            },
            "player2": {
                "name": player2.name,
                "hp": player2.hp,
                "position": player2.position
            },
            "ticks": current_tick
        }
    }

def main():
    """Entry point when run as a script"""
    # Run simulation with visualization
    # 45 seconds = 45,000ms / 300ms per tick = 150 ticks
    run_duel_simulation(max_ticks=150, visualize=True, tick_duration_ms=300)

if __name__ == "__main__":
    main() 