import json
import time
import os
from entities.player import Player
from engine.tick_manager import TickManager
from engine.rules import RuleSet
from ai.basic_agent import BasicAgent
from utils.visualizer import DuelVisualizer

def load_rules(filename="default_rules.json"):
    """Load rules from a JSON configuration file"""
    config_path = os.path.join("config", filename)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {config_path}, using default rules")
        return {}

def run_duel_simulation(max_ticks=30, visualize=True, tick_duration_ms=600):
    """Run a complete duel simulation"""
    # Load rules
    rule_config = load_rules()
    rules = RuleSet(rule_config)
    
    # Create tick manager
    tick_manager = TickManager(tick_duration_ms=tick_duration_ms)
    
    # Create players
    player1 = Player(name="Fighter1", hp=99, attack=75, strength=80, defense=70)
    player2 = Player(name="Fighter2", hp=99, attack=70, strength=75, defense=80)
    
    # Set initial positions from config or defaults
    starting_positions = rule_config.get("starting_positions", [[0, 0], [4, 4]])
    player1.position = tuple(starting_positions[0])
    player2.position = tuple(starting_positions[1])
    
    # Register players
    tick_manager.register_player(player1)
    tick_manager.register_player(player2)
    
    # Create AI agents
    agent1 = BasicAgent(player1, aggression=0.8)
    agent2 = BasicAgent(player2, aggression=0.6)
    
    # Create visualizer
    arena_size = rule_config.get("arena_size", {"width": 5, "height": 5})
    visualizer = DuelVisualizer(width=arena_size["width"], height=arena_size["height"])
    
    # Main simulation loop
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
    print("\nDuel Summary:")
    for event in tick_manager.events:
        print(f"[Tick {event['tick']}] {event['message']}")
    
    # Determine winner
    if player1.hp <= 0:
        print(f"\nWinner: {player2.name}")
    elif player2.hp <= 0:
        print(f"\nWinner: {player1.name}")
    else:
        print("\nDuel ended in a draw (max ticks reached)")

def main():
    # Run simulation with visualization
    run_duel_simulation(max_ticks=30, visualize=True, tick_duration_ms=300)  # Faster for demo

if __name__ == "__main__":
    main() 