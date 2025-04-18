"""
Visual Duel - A script to run duels with enhanced visual effects
"""
import os
import time
import json
import argparse
from colorama import init, Fore, Back, Style
from duelsim.utils.enhanced_visualizer import EnhancedVisualizer

# Initialize colorama for cross-platform color support
init(autoreset=True)

def load_custom_config(filename="custom_config.json"):
    """Load custom configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {filename}, using default config")
        return {}

def run_visual_duel(player1_config=None, player2_config=None, rules_config=None, 
                   max_ticks=150, tick_duration=0.3):
    """
    Run a duel with enhanced visual effects
    """
    # Default player configs if none provided
    if not player1_config:
        player1_config = {
            "name": "0xEC",
            "hp": 99,
            "attack": 99,
            "strength": 99,
            "defense": 99,
            "position": [0, 0]
        }
    
    if not player2_config:
        player2_config = {
            "name": "noLE",
            "hp": 99,
            "attack": 99,
            "strength": 99,
            "defense": 99,
            "position": [4, 4]
        }
    
    # Create a simple player class for visualization
    class SimplePlayer:
        def __init__(self, config):
            self.name = config["name"]
            self.hp = config["hp"]
            self.max_hp = config["hp"]
            self.attack = config["attack"]
            self.strength = config["strength"]
            self.defense = config["defense"]
            self.position = tuple(config.get("position", [0, 0]))
    
    # Create player objects
    player1 = SimplePlayer(player1_config)
    player2 = SimplePlayer(player2_config)
    
    # Create visualizer
    arena_size = rules_config.get("arena_size", {"width": 5, "height": 5})
    visualizer = EnhancedVisualizer(width=arena_size.get("width", 5), 
                                   height=arena_size.get("height", 5))
    
    # Welcome screen
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           DUELSIM ENHANCED VISUALIZER           {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    
    print(f"{Fore.WHITE}A battle between {Fore.BLUE}{player1.name}{Fore.WHITE} and {Fore.RED}{player2.name}{Fore.WHITE} is about to begin!")
    print(f"\n{Fore.BLUE}{player1.name}: {player1.hp} HP, {player1.attack} ATK, {player1.defense} DEF")
    print(f"{Fore.RED}{player2.name}: {player2.hp} HP, {player2.attack} ATK, {player2.defense} DEF\n")
    
    print(f"{Fore.YELLOW}Press Enter to start the battle...{Fore.WHITE}")
    input()
    
    # Load the actual battle data from the result file
    try:
        with open("game_result.json", "r") as f:
            result = json.load(f)
        
        events = result.get("events", [])
        final_state = result.get("final_state", {})
        
        # Update player objects with final state data
        if "player1" in final_state:
            p1_final = final_state["player1"]
            player1.position = tuple(p1_final.get("position", player1.position))
        
        if "player2" in final_state:
            p2_final = final_state["player2"]
            player2.position = tuple(p2_final.get("position", player2.position))
        
        # Render initial arena
        visualizer.render_arena([player1, player2])
        time.sleep(1)
        
        # Process events
        current_tick = 0
        for event in events:
            # Clear screen and show current tick
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{Fore.CYAN}=== TICK {event.get('tick', current_tick)} ===")
            
            # Render arena
            visualizer.render_arena([player1, player2])
            
            # Process event based on type
            event_type = event.get("type", "info")
            message = event.get("message", "")
            
            # Handle different event types
            if event_type == "attack":
                attacker_name = event.get("attacker", "")
                defender_name = event.get("defender", "")
                damage = event.get("damage", 0)
                
                attacker = player1 if attacker_name == player1.name else player2
                defender = player2 if attacker_name == player1.name else player1
                
                # Update health
                defender.hp = max(0, defender.hp - damage)
                
                # Check for critical hit
                is_critical = "CRITICAL" in message
                
                # Render attack
                visualizer.render_attack(attacker, defender, damage, is_critical)
            
            elif event_type == "movement":
                # Update positions based on message
                if player1.name in message and "moves" in message:
                    # Simple position update for demo
                    x, y = player1.position
                    if x < player2.position[0]:
                        player1.position = (x + 1, y)
                    elif x > player2.position[0]:
                        player1.position = (x - 1, y)
                    elif y < player2.position[1]:
                        player1.position = (x, y + 1)
                    elif y > player2.position[1]:
                        player1.position = (x, y - 1)
                
                elif player2.name in message and "moves" in message:
                    # Simple position update for demo
                    x, y = player2.position
                    if x < player1.position[0]:
                        player2.position = (x + 1, y)
                    elif x > player1.position[0]:
                        player2.position = (x - 1, y)
                    elif y < player1.position[1]:
                        player2.position = (x, y + 1)
                    elif y > player1.position[1]:
                        player2.position = (x, y - 1)
                
                visualizer.render_event("movement", message)
            
            elif event_type == "victory":
                winner_name = event.get("winner", "")
                winner = player1 if winner_name == player1.name else player2
                visualizer.render_victory(winner)
            
            else:
                # Render other event types
                visualizer.render_event(event_type, message)
            
            # Wait for next tick
            time.sleep(tick_duration)
            current_tick += 1
        
        # Show final state
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}=== FINAL STATE ===")
        visualizer.render_arena([player1, player2])
        
        # Show winner
        winner_name = result.get("winner", "Unknown")
        print(f"\n{Fore.YELLOW}The winner is: {Fore.WHITE}{winner_name}!")
        
        return result
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{Fore.RED}Error loading battle data: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a visually enhanced duel simulation")
    parser.add_argument("--config", default="custom_config.json", 
                        help="Custom configuration file (default: custom_config.json)")
    parser.add_argument("--speed", type=float, default=0.3,
                        help="Tick duration in seconds (default: 0.3)")
    
    args = parser.parse_args()
    
    # Load custom configuration
    config = load_custom_config(args.config)
    
    # Custom player configurations
    player1_config = {
        "name": "0xEC",
        "hp": 99,
        "attack": 99,
        "strength": 99,
        "defense": 99,
        "position": [0, 0]
    }

    player2_config = {
        "name": "noLE",
        "hp": 99,
        "attack": 99,
        "strength": 99,
        "defense": 99,
        "position": [4, 4]
    }
    
    # Run the visual duel
    print(f"{Fore.CYAN}Running enhanced visual duel simulation...")
    run_visual_duel(
        player1_config=player1_config,
        player2_config=player2_config,
        rules_config=config,
        tick_duration=args.speed
    ) 