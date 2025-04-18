"""
Enhanced visualizer for DuelSim - Provides colorful and engaging battle visualization
"""
import os
import time
import random
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# ASCII art for different combat actions
ASCII_ATTACKS = [
    "  ⚔️   ",
    " 🗡️    ",
    "   💥  ",
    "  ⚡   ",
]

ASCII_SPECIAL_MOVES = [
    "  ✨✨  ",
    " 🔥🔥🔥 ",
    " ⚡⚡⚡ ",
    " 💫💫💫 ",
]

# Health bar characters
HEALTH_FULL = "█"
HEALTH_EMPTY = "░"

class EnhancedVisualizer:
    def __init__(self, width=5, height=5, animation_speed=0.05):
        """Initialize the enhanced visualizer"""
        self.width = width
        self.height = height
        self.animation_speed = animation_speed
        self.frame_count = 0
        self.players = []  # Store reference to players
        
    def render_health_bar(self, current, maximum, length=20, player_name=""):
        """Render a colorful health bar"""
        # Calculate health percentage
        percentage = max(0, min(current / maximum, 1.0))
        
        # Choose color based on health percentage
        if percentage > 0.7:
            color = Fore.GREEN
        elif percentage > 0.3:
            color = Fore.YELLOW
        else:
            color = Fore.RED
            
        # Calculate filled and empty segments
        filled = int(percentage * length)
        empty = length - filled
        
        # Create the health bar
        health_bar = f"{color}{HEALTH_FULL * filled}{Fore.WHITE}{HEALTH_EMPTY * empty}"
        
        # Format with player name and health values
        return f"{player_name.ljust(10)} {health_bar} {current}/{maximum} HP"
    
    def render_arena(self, players):
        """Render the arena with players and decorations"""
        # Store reference to players
        self.players = players
        
        # Clear screen for better visualization
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print frame counter for animation effect
        print(f"{Fore.CYAN}╔{'═' * (self.width * 4 + 2)}╗")
        
        # Create arena grid
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Place players on grid
        player_chars = {}
        for i, player in enumerate(players):
            x, y = player.position
            if 0 <= x < self.width and 0 <= y < self.height:
                player_color = Fore.BLUE if i == 0 else Fore.RED
                player_char = '1' if i == 0 else '2'
                grid[y][x] = f"{player_color}{player_char}{Style.RESET_ALL}"
                player_chars[player.name] = player_char
        
        # Render grid with decorations
        for y in range(self.height):
            print(f"{Fore.CYAN}║ ", end="")
            for x in range(self.width):
                cell = grid[y][x]
                if cell == ' ':
                    # Add occasional decorative elements to empty cells
                    if random.random() < 0.05:
                        decorations = [f"{Fore.GREEN}.", f"{Fore.YELLOW}*", f"{Fore.WHITE}·"]
                        print(f"{random.choice(decorations)} ", end="")
                    else:
                        print("  ", end="")
                else:
                    print(f"{cell} ", end="")
            print(f"{Fore.CYAN}║")
        
        print(f"{Fore.CYAN}╚{'═' * (self.width * 4 + 2)}╝")
        
        # Render health bars
        print("\n" + "=" * 50)
        for i, player in enumerate(players):
            color = Fore.BLUE if i == 0 else Fore.RED
            print(f"{color}{self.render_health_bar(player.hp, player.max_hp, 20, player.name)}")
        print("=" * 50 + "\n")
        
        # Add equipment display
        for player in players:
            self.render_player_equipment(player)
    
    def render_attack(self, attacker, defender, damage, is_critical=False):
        """Render an attack animation"""
        # Choose attack animation
        attack_symbol = random.choice(ASCII_ATTACKS)
        
        # Determine colors - use stored players reference
        attacker_color = Fore.BLUE if attacker.name == self.players[0].name else Fore.RED
        defender_color = Fore.BLUE if defender.name == self.players[0].name else Fore.RED
        
        # Create message with appropriate styling
        if is_critical:
            damage_text = f"{Fore.YELLOW}CRITICAL! {Fore.RED}{damage} damage"
            attack_symbol = random.choice(ASCII_SPECIAL_MOVES)
        else:
            damage_text = f"{Fore.RED}{damage} damage"
        
        # Print attack message
        print(f"{attacker_color}{attacker.name} {Fore.WHITE}attacks {defender_color}{defender.name}")
        print(f"{attack_symbol} {damage_text}")
        
        # Small delay for effect
        time.sleep(self.animation_speed)
    
    def render_special_move(self, player, move_name):
        """Render a special move animation"""
        # Choose special move animation
        special_symbol = random.choice(ASCII_SPECIAL_MOVES)
        
        # Determine color - use stored players reference
        player_color = Fore.BLUE if player.name == self.players[0].name else Fore.RED
        
        # Print special move message with animation
        print(f"{player_color}{player.name} {Fore.YELLOW}uses {Fore.MAGENTA}{move_name}{Fore.YELLOW}!")
        
        # Animated special move effect
        for _ in range(3):
            print(f"{Fore.YELLOW}{special_symbol}")
            time.sleep(self.animation_speed)
    
    def render_victory(self, winner):
        """Render a victory animation"""
        # Victory banner
        victory_banner = [
            f"{Fore.YELLOW}╔═══════════════════════════════════╗",
            f"{Fore.YELLOW}║{Fore.WHITE}           VICTORY!                {Fore.YELLOW}║",
            f"{Fore.YELLOW}╚═══════════════════════════════════╝"
        ]
        
        # Determine winner color - use stored players reference
        winner_color = Fore.BLUE if winner.name == self.players[0].name else Fore.RED
        
        # Print victory animation
        for _ in range(3):
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n" * 5)
            for line in victory_banner:
                print(f"{' ' * 10}{line}")
            print(f"\n{' ' * 15}{winner_color}{winner.name} {Fore.WHITE}wins!")
            print("\n" * 5)
            time.sleep(0.5)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n" * 6)
            for line in victory_banner:
                print(f"{' ' * 15}{line}")
            print(f"\n{' ' * 20}{winner_color}{winner.name} {Fore.WHITE}wins!")
            print("\n" * 6)
            time.sleep(0.5)
    
    def render_event(self, event_type, message):
        """Render a game event with appropriate styling"""
        if event_type == "narrative":
            print(f"{Fore.CYAN}{message}")
        elif event_type == "movement":
            print(f"{Fore.GREEN}{message}")
        elif event_type == "attack":
            print(f"{Fore.RED}{message}")
        elif event_type == "special":
            print(f"{Fore.MAGENTA}{message}")
        elif event_type == "victory":
            print(f"{Fore.YELLOW}{message}")
        else:
            print(message)
        
        # Small delay for readability
        time.sleep(self.animation_speed)
    
    def render_player_equipment(self, player):
        """Render a player's equipment"""
        if not hasattr(player, 'get_equipped_items'):
            return
        
        equipment = player.get_equipped_items()
        if not equipment:
            return
        
        player_color = Fore.BLUE if player.name == "0xEC" else Fore.RED
        print(f"\n{player_color}{player.name}'s Equipment:{Style.RESET_ALL}")
        print("──────────────────────────────────────────────────")
        
        for item in equipment:
            # Get item name with color based on rarity
            rarity_color = {
                1: Fore.WHITE,      # COMMON
                2: Fore.GREEN,      # UNCOMMON
                3: Fore.BLUE,       # RARE
                4: Fore.MAGENTA,    # EPIC
                5: Fore.YELLOW,     # LEGENDARY
                6: Fore.RED         # MYTHIC
            }.get(item.rarity.value, Fore.WHITE)
            
            item_name = f"{rarity_color}{item.name}{Style.RESET_ALL}"
            
            # Format stats string
            stats_str = ", ".join(f"{stat}: +{value}" for stat, value in item.stats.items())
            
            # Format effects string if any
            effects_str = ""
            if hasattr(item, 'special_effects') and item.special_effects:
                effects_str = f" | Effects: {', '.join(f'{effect['name']} ({effect['value']}%)' for effect in item.special_effects)}"
            
            # Get slot name as string
            slot_name = item.slot.name.lower() if hasattr(item.slot, 'name') else str(item.slot)
            
            # Print item details
            print(f"  {slot_name.ljust(10)}: {item_name} [{stats_str}]{effects_str}")
        
        print("──────────────────────────────────────────────────") 