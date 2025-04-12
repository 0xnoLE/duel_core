"""
Master Duel - A complete duel experience with simulation and enhanced visualization
"""
import os
import time
import json
import argparse
from colorama import init, Fore, Back, Style
from duelsim import run_duel_simulation
from duelsim.utils.enhanced_visualizer import EnhancedVisualizer
from game_reporter import GameReporter
import random

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Anime-style ASCII faces
HAPPY_ANIME_FACE = [
    "  (^‿^)  ",
    " \\(≧▽≦)/ ",
    "  (◕‿◕)  ",
    "  (｡◕‿◕｡)",
]

SAD_ANIME_FACE = [
    "  (╥﹏╥)  ",
    "  (;﹏;)  ",
    "  (T_T)   ",
    "  (ಥ﹏ಥ)  ",
]

def load_custom_config(filename="custom_config.json"):
    """Load custom configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {filename}, using default config")
        return {}

def run_master_duel(num_simulations=1, generate_report=True, 
                   enhanced_visuals=True, replay_speed=0.3):
    """Run a complete duel experience with simulation and visualization"""
    # Load custom configuration
    config = load_custom_config()

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

    # Clear screen and show welcome banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           DUELSIM MASTER EXPERIENCE           {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    
    print(f"{Fore.WHITE}A battle between {Fore.BLUE}{player1_config['name']}{Fore.WHITE} and {Fore.RED}{player2_config['name']}{Fore.WHITE} is about to begin!")
    print(f"\n{Fore.BLUE}{player1_config['name']}: {player1_config['hp']} HP, {player1_config['attack']} ATK, {player1_config['defense']} DEF")
    print(f"{Fore.RED}{player2_config['name']}: {player2_config['hp']} HP, {player2_config['attack']} ATK, {player2_config['defense']} DEF\n")
    
    print(f"{Fore.YELLOW}Press Enter to start the battle...{Fore.WHITE}")
    input()
    
    # Run the simulation
    print(f"{Fore.CYAN}Running duel simulation...")
    result = run_duel_simulation(
        max_ticks=200,
        visualize=False,  # We'll handle visualization ourselves
        tick_duration_ms=250,
        player1_config=player1_config,
        player2_config=player2_config,
        rules_config=config,
        enhanced_visuals=False  # We'll handle enhanced visuals ourselves
    )
    
    # Save the result
    with open("game_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    # Generate report if requested
    if generate_report:
        reporter = GameReporter()
        report_path = reporter.generate_report(result)
        print(f"Report generated: {report_path}")
    
    # Now run the visual replay
    if enhanced_visuals:
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
        arena_size = config.get("arena_size", {"width": 5, "height": 5})
        visualizer = EnhancedVisualizer(width=arena_size.get("width", 5), 
                                       height=arena_size.get("height", 5))
        
        # Show replay banner
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           BATTLE REPLAY STARTING           {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        print(f"{Fore.WHITE}Replaying the battle between {Fore.BLUE}{player1.name}{Fore.WHITE} and {Fore.RED}{player2.name}{Fore.WHITE}!")
        time.sleep(1)
        
        # Process events
        events = result.get("events", [])
        current_tick = 0
        
        for event in events:
            # Extract event data
            tick = event.get("tick", 0)
            message = event.get("message", "")
            event_type = event.get("type", "")
            
            # Skip to the current tick
            if tick > current_tick:
                current_tick = tick
                
                # Render arena every few ticks for smoother visualization
                if current_tick % 3 == 0 or "attack" in event_type or "victory" in event_type:
                    visualizer.render_arena([player1, player2])
            
            # Process different event types
            if "attack" in event_type:
                # Extract attacker, defender and damage from message
                if player1.name in message and "strikes" in message:
                    attacker, defender = player1, player2
                else:
                    attacker, defender = player2, player1
                
                # Extract damage
                damage = 0
                is_critical = "CRITICAL" in message
                try:
                    damage_text = message.split("for ")[1].split(" ")[0]
                    damage = int(damage_text)
                except (IndexError, ValueError):
                    pass
                
                # Update health
                defender.hp = max(0, defender.hp - damage)
                
                # Render attack
                visualizer.render_attack(attacker, defender, damage, is_critical)
            
            elif "movement" in event_type:
                # Update positions based on movement message
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
            
            elif "victory" in event_type or "defeated" in message:
                winner_name = result.get("winner", "")
                winner = player1 if winner_name == player1.name else player2
                loser = player2 if winner_name == player1.name else player1
                
                # Custom victory animation with anime faces
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Victory banner
                victory_banner = [
                    f"{Fore.YELLOW}╔═══════════════════════════════════╗",
                    f"{Fore.YELLOW}║{Fore.WHITE}           VICTORY!                {Fore.YELLOW}║",
                    f"{Fore.YELLOW}╚═══════════════════════════════════╝"
                ]
                
                # Determine colors
                winner_color = Fore.BLUE if winner.name == player1.name else Fore.RED
                loser_color = Fore.RED if winner.name == player1.name else Fore.BLUE
                
                # Show victory animation with anime faces
                for _ in range(3):
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\n" * 3)
                    
                    # Print victory banner
                    for line in victory_banner:
                        print(f"{' ' * 10}{line}")
                    
                    # Print winner with happy face
                    happy_face = random.choice(HAPPY_ANIME_FACE)
                    print(f"\n{' ' * 15}{winner_color}{winner.name} {Fore.WHITE}wins!")
                    print(f"{' ' * 15}{winner_color}{happy_face}")
                    
                    # Print loser with sad face
                    sad_face = random.choice(SAD_ANIME_FACE)
                    print(f"\n{' ' * 15}{loser_color}{loser.name} {Fore.WHITE}loses...")
                    print(f"{' ' * 15}{loser_color}{sad_face}")
                    
                    print("\n" * 3)
                    time.sleep(0.7)
                
                visualizer.render_event("victory", message)
            
            else:
                # Render other event types
                visualizer.render_event(event_type, message)
            
            # Wait for next tick
            time.sleep(replay_speed)
        
        # Show final state
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}=== FINAL STATE ===")
        visualizer.render_arena([player1, player2])
        
        # Show winner with anime face
        winner_name = result.get("winner", "Unknown")
        winner = player1 if winner_name == player1.name else player2
        loser = player2 if winner_name == player1.name else player1
        
        winner_color = Fore.BLUE if winner.name == player1.name else Fore.RED
        loser_color = Fore.RED if winner.name == player1.name else Fore.BLUE
        
        happy_face = random.choice(HAPPY_ANIME_FACE)
        sad_face = random.choice(SAD_ANIME_FACE)
        
        print(f"\n{Fore.YELLOW}The winner is: {winner_color}{winner.name}! {winner_color}{happy_face}")
        print(f"{Fore.WHITE}Better luck next time, {loser_color}{loser.name}... {loser_color}{sad_face}")
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a complete duel experience")
    parser.add_argument("--config", default="custom_config.json", 
                        help="Custom configuration file (default: custom_config.json)")
    parser.add_argument("--speed", type=float, default=0.3,
                        help="Replay speed in seconds (default: 0.3)")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip generating reports")
    parser.add_argument("--no-enhanced-visuals", action="store_true",
                        help="Skip enhanced visualization")
    
    args = parser.parse_args()
    
    # Run the master duel
    run_master_duel(
        generate_report=not args.no_report,
        enhanced_visuals=not args.no_enhanced_visuals,
        replay_speed=args.speed
    ) 