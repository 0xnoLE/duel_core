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
from math import exp
from duelsim.items.item import Item, ItemSlot, ItemRarity, ItemType
import math
from betting_analytics import BettingAnalytics

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

# Add the SimplePlayer class at the top level of the file, before the functions
class SimplePlayer:
    """A simplified player class for visualization that supports equipment"""
    def __init__(self, name, hp, attack, defense, strength, position):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.strength = strength
        
        # Convert string positions to coordinates
        if isinstance(position, str):
            if position == "left":
                self.position = (0, 2)  # Left side of the arena
            elif position == "right":
                self.position = (4, 2)  # Right side of the arena
            else:
                self.position = (0, 0)  # Default position
        else:
            self.position = position
            
        self.equipment = {}  # Store equipped items
    
    def equip_item(self, item):
        """Equip an item to this player"""
        # Get the slot from the item
        if isinstance(item, dict):
            slot = item.get("slot", "weapon")
            stats = item.get("stats", {})
        else:
            slot = item.slot
            stats = item.stats if hasattr(item, 'stats') else {}
        
        # Store the item
        self.equipment[slot] = item
        
        # Apply item stats
        for stat, value in stats.items():
            if stat == "hp":
                self.hp += value
                self.max_hp += value
            elif hasattr(self, stat):
                setattr(self, stat, getattr(self, stat) + value)
        
        return True
    
    def get_equipped_items(self):
        """Get all equipped items"""
        return list(self.equipment.values())

# Add this class to manage player bank and bets
class BettingManager:
    """Manages player bank and betting for DuelSim"""
    
    def __init__(self, initial_bank=1000):
        self.bank = initial_bank
        self.current_bet = 0
        self.bet_on = None  # 'player1' or 'player2'
        self.session_profit = 0
        self.session_bets = 0
        self.session_wins = 0
    
    def place_bet(self, amount, bet_on):
        """Place a bet on a player"""
        if amount <= 0:
            print(f"{Fore.RED}Bet amount must be positive.")
            return False
        
        if amount > self.bank:
            print(f"{Fore.RED}Insufficient funds! Your bank: ${self.bank}")
            return False
        
        self.current_bet = amount
        self.bet_on = bet_on
        self.bank -= amount
        self.session_bets += 1
        
        return True
    
    def process_result(self, winner, payouts):
        """Process the result of a bet"""
        if not self.bet_on or self.current_bet <= 0:
            return 0  # No bet placed
        
        # Determine if player won the bet
        won_bet = (self.bet_on == winner)
        
        # Calculate winnings
        if won_bet:
            # Get the appropriate payout
            payout = payouts[self.bet_on]
            winnings = self.current_bet * payout
            self.bank += winnings
            profit = winnings - self.current_bet
            self.session_profit += profit
            self.session_wins += 1
            
            return profit
        else:
            # Lost the bet (money already removed from bank)
            self.session_profit -= self.current_bet
            return -self.current_bet
    
    def display_bank(self):
        """Display current bank balance"""
        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           YOUR BETTING BANK               {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        print(f"Current Balance: {Fore.GREEN}${self.bank:.2f}")
        print(f"Session Profit: {Fore.GREEN if self.session_profit >= 0 else Fore.RED}${self.session_profit:.2f}")
        print(f"Win Rate: {self.session_wins}/{self.session_bets} ({(self.session_wins/self.session_bets)*100:.1f}% win rate)" if self.session_bets > 0 else "No bets placed yet")
    
    def prompt_for_bet(self, player1, player2, p1_payout, p2_payout):
        """Prompt the user to place a bet"""
        self.display_bank()
        
        # If bank is empty, skip betting
        if self.bank <= 0:
            print(f"{Fore.RED}You have no funds available for betting.")
            print(f"{Fore.YELLOW}Skipping bet for this round.")
            return False
        
        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           PLACE YOUR BET                 {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        p1_name = player1.name if hasattr(player1, 'name') else player1["name"]
        p2_name = player2.name if hasattr(player2, 'name') else player2["name"]
        
        print(f"1. {Fore.BLUE}{p1_name}{Fore.WHITE} - Payout: {p1_payout:.2f}x")
        print(f"2. {Fore.RED}{p2_name}{Fore.WHITE} - Payout: {p2_payout:.2f}x")
        print(f"3. Skip betting this round")
        print(f"4. Return to main menu")
        
        # Get player choice
        while True:
            try:
                choice = int(input(f"\n{Fore.GREEN}Who would you like to bet on? (1-4): {Fore.WHITE}"))
                if choice in [1, 2, 3, 4]:
                    break
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Betting cancelled.")
                return False
        
        if choice == 3:
            print(f"{Fore.YELLOW}Skipping bet for this round.")
            return False
        elif choice == 4:
            print(f"{Fore.YELLOW}Returning to main menu.")
            return "exit"
        
        # Get bet amount
        while True:
            try:
                # Calculate suggested bets based on current bank
                suggested_bets = []
                if self.bank >= 10:
                    suggested_bets.append(10)
                if self.bank >= 50:
                    suggested_bets.append(50)
                if self.bank >= 100:
                    suggested_bets.append(100)
                if self.bank >= 2:
                    suggested_bets.append(self.bank // 2)
                
                # If no suggested bets, add a small amount
                if not suggested_bets and self.bank > 0:
                    suggested_bets.append(round(self.bank / 2, 2))
                
                # Display suggested bets if available
                if suggested_bets:
                    print(f"\nSuggested bets: " + ", ".join([f"${bet:.2f}" for bet in suggested_bets]))
                
                print(f"Your bank: ${self.bank:.2f}")
                print(f"Enter 'b' to go back, 'a' to bet all, or a specific amount")
                
                amount_input = input(f"{Fore.GREEN}How much would you like to bet? ${Fore.WHITE}")
                
                # Check for special commands
                if amount_input.lower() == 'b':
                    return self.prompt_for_bet(player1, player2, p1_payout, p2_payout)
                elif amount_input.lower() == 'a':
                    amount = self.bank
                else:
                    amount = float(amount_input)
                
                if 0 < amount <= self.bank:
                    break
                elif amount > self.bank:
                    print(f"{Fore.RED}Insufficient funds! Your bank: ${self.bank:.2f}")
                else:
                    print(f"{Fore.RED}Bet amount must be positive.")
            except ValueError:
                print(f"{Fore.RED}Please enter a valid amount.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Betting cancelled.")
                return False
        
        # Place the bet
        bet_on = p1_name if choice == 1 else p2_name
        if self.place_bet(amount, bet_on):
            bet_color = Fore.BLUE if choice == 1 else Fore.RED
            print(f"\n{Fore.GREEN}You bet ${amount:.2f} on {bet_color}{bet_on}{Fore.GREEN}!")
            print(f"If you win, you'll receive ${amount * (p1_payout if choice == 1 else p2_payout):.2f} (profit: ${amount * ((p1_payout if choice == 1 else p2_payout) - 1):.2f})")
            return True
        
        return False

def load_custom_config(filename="custom_config.json"):
    """Load custom configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {filename}, using default config")
        return {}

def calculate_elo_difference(player1_stats, player2_stats):
    """Calculate ELO difference based on player stats"""
    # Calculate base power levels
    p1_power = (player1_stats["attack"] * 0.4 + 
                player1_stats["strength"] * 0.3 + 
                player1_stats["defense"] * 0.3)
    
    p2_power = (player2_stats["attack"] * 0.4 + 
                player2_stats["strength"] * 0.3 + 
                player2_stats["defense"] * 0.3)
    
    # Calculate ELO difference (positive means player1 is favored)
    return p1_power - p2_power

def calculate_win_probability(elo_diff):
    """Calculate win probability using logistic function"""
    return 1 / (1 + exp(-elo_diff/40))  # 40 is a scaling factor

def calculate_betting_odds(win_probability):
    """Calculate betting odds from win probability"""
    # Add a small epsilon to avoid floating point precision issues
    epsilon = 1e-10
    
    # Handle near 50% case (even odds)
    if abs(win_probability - 0.5) < epsilon:
        return 100.0  # Even money
    
    if win_probability > 0.5:
        # Favorite: how much you need to bet to win $100
        return -100 / (win_probability - 0.5)
    else:
        # Underdog: how much you win on a $100 bet
        return 100 / (0.5 - win_probability)

def analyze_equipment(player):
    """Analyze player equipment and return stat bonuses"""
    bonuses = {"attack": 0, "defense": 0, "strength": 0, "hp": 0}
    
    # Handle dictionary format
    if isinstance(player, dict):
        # Dictionary players typically don't have equipment in our current setup
        return bonuses
    
    # Handle object format
    if not hasattr(player, 'equipment') or not player.equipment:
        return bonuses
    
    for slot, item in player.equipment.items():
        if item and hasattr(item, 'stats'):
            for stat, value in item.stats.items():
                if stat in bonuses:
                    bonuses[stat] += value
    
    return bonuses

def display_matchup_analysis(player1, player2):
    """Display a detailed matchup analysis between two players"""
    # Get player names
    if hasattr(player1, 'name'):
        p1_name = player1.name
    elif isinstance(player1, dict) and 'name' in player1:
        p1_name = player1['name']
    else:
        p1_name = 'Player 1'
        
    if hasattr(player2, 'name'):
        p2_name = player2.name
    elif isinstance(player2, dict) and 'name' in player2:
        p2_name = player2['name']
    else:
        p2_name = 'Player 2'
    
    # Get player stats
    def get_stat(player, stat_name, default=0):
        """Helper function to get a stat from either an object or dict"""
        if hasattr(player, stat_name):
            return getattr(player, stat_name)
        elif isinstance(player, dict) and stat_name in player:
            return player[stat_name]
        return default
    
    # Get stats using the helper function
    p1_hp = get_stat(player1, 'hp')
    p1_attack = get_stat(player1, 'attack')
    p1_defense = get_stat(player1, 'defense')
    p1_strength = get_stat(player1, 'strength')
    
    p2_hp = get_stat(player2, 'hp')
    p2_attack = get_stat(player2, 'attack')
    p2_defense = get_stat(player2, 'defense')
    p2_strength = get_stat(player2, 'strength')
    
    # Calculate win probabilities
    p1_prob, p2_prob, total_diff = compute_win_probability(player1, player2)
    
    # Calculate payouts
    p1_payout = calculate_payout(p1_prob)
    p2_payout = calculate_payout(p2_prob)
    
    # Determine who has the advantage
    advantage = p1_name if total_diff > 0 else p2_name if total_diff < 0 else "EVEN"
    
    # Print the analysis
    print(f"{p1_name} vs {p2_name}")
    print("=" * 50)
    print(f"{'Stat':<10} | {p1_name:<15} | {p2_name}")
    print(f"{'-'*10}+{'-'*17}+{'-'*16}")
    
    # HP comparison
    hp_diff = p1_hp - p2_hp
    hp_indicator = f" | +{abs(hp_diff)}" if hp_diff != 0 else " | EVEN"
    print(f"{'HP':<10} | {p1_hp:<15} | {p2_hp:<14}{hp_indicator}")
    
    # Attack comparison
    atk_diff = p1_attack - p2_attack
    atk_indicator = f" | +{abs(atk_diff)}" if atk_diff != 0 else " | EVEN"
    print(f"{'ATTACK':<10} | {p1_attack:<15} | {p2_attack:<14}{atk_indicator}")
    
    # Defense comparison
    def_diff = p1_defense - p2_defense
    def_indicator = f" | +{abs(def_diff)}" if def_diff != 0 else " | EVEN"
    print(f"{'DEFENSE':<10} | {p1_defense:<15} | {p2_defense:<14}{def_indicator}")
    
    # Strength comparison
    str_diff = p1_strength - p2_strength
    str_indicator = f" | +{abs(str_diff)}" if str_diff != 0 else " | EVEN"
    print(f"{'STRENGTH':<10} | {p1_strength:<15} | {p2_strength:<14}{str_indicator}")
    
    print("=" * 50)
    
    # Print equipment bonuses if available
    if (hasattr(player1, 'equipment') and hasattr(player2, 'equipment') and 
        hasattr(player1.equipment, 'values') and hasattr(player2.equipment, 'values')):
        # Calculate equipment bonuses
        p1_equip_bonuses = {"attack": 0, "defense": 0, "hp": 0, "strength": 0}
        p2_equip_bonuses = {"attack": 0, "defense": 0, "hp": 0, "strength": 0}
        
        # Calculate player 1 equipment bonuses
        for item in player1.equipment.values():
            if hasattr(item, 'stats'):
                for stat, value in item.stats.items():
                    if stat in p1_equip_bonuses:
                        p1_equip_bonuses[stat] += value
        
        # Calculate player 2 equipment bonuses
        for item in player2.equipment.values():
            if hasattr(item, 'stats'):
                for stat, value in item.stats.items():
                    if stat in p2_equip_bonuses:
                        p2_equip_bonuses[stat] += value
        
        # Print equipment bonuses
        print("\nEQUIPMENT BONUSES:")
        print(f"{'Stat':<10} | {p1_name:<15} | {p2_name}")
        print(f"{'-'*10}+{'-'*17}+{'-'*16}")
        
        for stat in ["attack", "defense", "hp", "strength"]:
            stat_diff = p1_equip_bonuses[stat] - p2_equip_bonuses[stat]
            stat_indicator = f" | +{abs(stat_diff)}" if stat_diff != 0 else " | EVEN"
            print(f"{stat.upper():<10} | {p1_equip_bonuses[stat]:<15} | {p2_equip_bonuses[stat]:<14}{stat_indicator}")
        
        print("=" * 50)
    
    # Print battle predictions
    print("\nBATTLE PREDICTIONS:")
    print(f"Total Score Difference: {abs(total_diff):.1f} in favor of {advantage}")
    print(f"Win Probability: {p1_name}: {p1_prob*100:.1f}% | {p2_name}: {p2_prob*100:.1f}%")
    
    # Print betting odds
    print("\nBETTING ODDS:")
    print(f"{p1_name}: x{p1_payout:.1f}")
    print(f"{p2_name}: x{p2_payout:.1f}")
    
    # Print analysis summary
    if abs(total_diff) < 0.1:
        print("\nANALYSIS: This appears to be an even matchup. Could go either way!")
    elif abs(total_diff) < 0.3:
        print(f"\nANALYSIS: {advantage} has a slight edge, but it's still a close match.")
    elif abs(total_diff) < 0.5:
        print(f"\nANALYSIS: {advantage} has a moderate advantage in this matchup.")
    else:
        print(f"\nANALYSIS: {advantage} has a significant advantage and is heavily favored to win.")

def load_items(filename="items_1337.json"):
    """Load items from JSON file or generate them if file doesn't exist"""
    try:
        with open(filename, 'r') as f:
            items_data = json.load(f)
            
        items = []
        for item_data in items_data:
            try:
                # Convert string slot and rarity to enum values
                slot = next(s for s in ItemSlot if s.value == item_data["slot"])
                
                # Handle different rarity formats (name or value)
                if isinstance(item_data["rarity"], str):
                    try:
                        rarity = ItemRarity[item_data["rarity"]]  # Try by name (COMMON, RARE, etc.)
                    except KeyError:
                        # Try to find by value if name lookup fails
                        rarity = next(r for r in ItemRarity if r.value == item_data["rarity"])
                else:
                    # If it's a number, find by value
                    rarity = next(r for r in ItemRarity if r.value == item_data["rarity"])
                
                # Get item type
                item_type = next(t for t in ItemType if t.value == item_data["type"])
                
                # Create item object
                item = Item(
                    name=item_data["name"],
                    slot=slot,
                    item_type=item_type,
                    rarity=rarity,
                    level=item_data.get("level", 1),
                    stats=item_data["stats"],
                    special_effects=item_data.get("special_effects", [])
                )
                items.append(item)
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Skipping invalid item: {e}{Fore.WHITE}")
                continue
        
        print(f"{Fore.GREEN}Loaded {len(items)} items from {filename}{Fore.WHITE}")
        return items
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{Fore.YELLOW}Warning: {e}. Using fix_items.py to generate items...{Fore.WHITE}")
        
        try:
            # Run the fix_items.py script
            import subprocess
            result = subprocess.run(["python", "fix_items.py"], capture_output=True, text=True)
            print(result.stdout)
            
            if os.path.exists(filename):
                # Try loading again
                return load_items(filename)
            else:
                print(f"{Fore.RED}Error: Could not generate items file.{Fore.WHITE}")
                return []
        except Exception as e:
            print(f"{Fore.RED}Error: {e}. No items will be available.{Fore.WHITE}")
            return []

def equip_random_items(player, items, num_items=3, return_items=False):
    """Equip random items to a player with balanced distribution"""
    if not items:
        print(f"{Fore.RED}No items available to equip")
        return [] if return_items else None
    
    # Group items by slot
    items_by_slot = {}
    for item in items:
        # Get the slot from the item
        slot = item.get("slot") if isinstance(item, dict) else item.slot
            
        if slot not in items_by_slot:
            items_by_slot[slot] = []
        items_by_slot[slot].append(item)
    
    # Select unique slots to ensure variety
    available_slots = list(items_by_slot.keys())
    if len(available_slots) < num_items:
        selected_slots = available_slots * (num_items // len(available_slots) + 1)
        selected_slots = selected_slots[:num_items]
    else:
        selected_slots = random.sample(available_slots, num_items)
    
    # Select one item from each selected slot
    selected_items = []
    for slot in selected_slots:
        slot_items = items_by_slot[slot]
        # Prefer lower rarity items for balance
        weighted_items = []
        for item in slot_items:
            # Get rarity from the item
            rarity = item.get("rarity", "COMMON") if isinstance(item, dict) else item.rarity
                
            # Higher weight for common/uncommon items
            weight = {
                "COMMON": 10,
                ItemRarity.COMMON: 10,
                "UNCOMMON": 7,
                ItemRarity.UNCOMMON: 7,
                "RARE": 5,
                ItemRarity.RARE: 5,
                "EPIC": 3,
                ItemRarity.EPIC: 3,
                "LEGENDARY": 2,
                ItemRarity.LEGENDARY: 2,
                "MYTHIC": 1,
                ItemRarity.MYTHIC: 1
            }.get(rarity, 1)
            weighted_items.extend([item] * weight)
        
        if weighted_items:
            selected_items.append(random.choice(weighted_items))
    
    # Equip the selected items
    equipped_items = []
    for item_data in selected_items:
        try:
            # Apply the item stats directly without creating a new Item object
            if isinstance(item_data, dict):
                # For dictionary items, apply stats directly
                slot = item_data.get("slot", "weapon")
                name = item_data.get("name", "Unknown Item")
                stats = item_data.get("stats", {})
                rarity = item_data.get("rarity", "COMMON")
                
                # Apply stats to player
                for stat, value in stats.items():
                    if stat == "hp":
                        player.hp += value
                        player.max_hp += value
                    elif hasattr(player, stat):
                        setattr(player, stat, getattr(player, stat) + value)
                
                # Store the item in player's equipment
                player.equipment[slot] = item_data
                equipped_items.append(item_data)
                
                # Determine color based on rarity
                rarity_colors = {
                    "COMMON": Fore.WHITE,
                    "UNCOMMON": Fore.GREEN,
                    "RARE": Fore.BLUE,
                    "EPIC": Fore.MAGENTA,
                    "LEGENDARY": Fore.YELLOW,
                    "MYTHIC": Fore.RED
                }
                rarity_color = rarity_colors.get(rarity, Fore.WHITE)
                
                # Print equipment info
                print(f"Equipped {rarity_color}{name}{Fore.WHITE} to {player.name}")
                stats_str = ", ".join([f"{stat}: +{value}" for stat, value in stats.items()])
                print(f"  Stats: {stats_str}")
            else:
                # For Item objects, use the equip_item method
                player.equip_item(item_data)
                equipped_items.append(item_data)
                
                # Print equipment info
                rarity_colors = {
                    "COMMON": Fore.WHITE,
                    ItemRarity.COMMON: Fore.WHITE,
                    "UNCOMMON": Fore.GREEN,
                    ItemRarity.UNCOMMON: Fore.GREEN,
                    "RARE": Fore.BLUE,
                    ItemRarity.RARE: Fore.BLUE,
                    "EPIC": Fore.MAGENTA,
                    ItemRarity.EPIC: Fore.MAGENTA,
                    "LEGENDARY": Fore.YELLOW,
                    ItemRarity.LEGENDARY: Fore.YELLOW,
                    "MYTHIC": Fore.RED,
                    ItemRarity.MYTHIC: Fore.RED
                }
                
                rarity_color = rarity_colors.get(item_data.rarity, Fore.WHITE)
                print(f"Equipped {rarity_color}{item_data.name}{Fore.WHITE} to {player.name}")
                
                if hasattr(item_data, 'stats'):
                    stats_str = ", ".join([f"{stat}: +{value}" for stat, value in item_data.stats.items()])
                    print(f"  Stats: {stats_str}")
        except Exception as e:
            print(f"{Fore.RED}Error equipping item: {e}")
            print(f"Item data: {item_data}")
            continue
    
    if return_items:
        return equipped_items
    return None

def calculate_equipment_score(player):
    """Calculate a score for the player's equipment based on rarity and stats"""
    if not hasattr(player, 'equipment') or not player.equipment:
        return 0
    
    total_score = 0
    
    for slot, item in player.equipment.items():
        # Calculate rarity score
        if isinstance(item, dict):
            # For dictionary items
            rarity_str = item.get("rarity", "COMMON")
            rarity_values = {
                "COMMON": 1,
                "UNCOMMON": 2,
                "RARE": 3,
                "EPIC": 4,
                "LEGENDARY": 5,
                "MYTHIC": 6
            }
            rarity_score = rarity_values.get(rarity_str, 1) * 2
            
            # Calculate stats score
            stats_score = sum(item.get("stats", {}).values())
        else:
            # For Item objects
            rarity_score = item.rarity.value * 2
            
            # Calculate stats score
            stats_score = sum(item.stats.values()) if hasattr(item, 'stats') else 0
        
        # Add to total score
        total_score += rarity_score + stats_score
    
    return total_score

def compute_win_probability(player1, player2):
    """
    Calculate win probability with a more balanced approach
    that prevents extreme probabilities of 0 or 1
    """
    # Get base stats
    p1_attack = getattr(player1, 'attack', 0)
    p1_defense = getattr(player1, 'defense', 0)
    p1_hp = getattr(player1, 'hp', 0)
    p1_strength = getattr(player1, 'strength', 0)
    
    p2_attack = getattr(player2, 'attack', 0)
    p2_defense = getattr(player2, 'defense', 0)
    p2_hp = getattr(player2, 'hp', 0)
    p2_strength = getattr(player2, 'strength', 0)
    
    # Calculate offensive and defensive power
    p1_offense = p1_attack * 0.7 + p1_strength * 0.3
    p1_defense_power = p1_defense * 0.7 + p1_hp * 0.3
    
    p2_offense = p2_attack * 0.7 + p2_strength * 0.3
    p2_defense_power = p2_defense * 0.7 + p2_hp * 0.3
    
    # Calculate overall power
    p1_power = p1_offense * 0.6 + p1_defense_power * 0.4
    p2_power = p2_offense * 0.6 + p2_defense_power * 0.4
    
    # Calculate power difference
    total_power = p1_power + p2_power
    if total_power == 0:
        # Equal chance if both have zero power
        return 0.5, 0.5, 0
    
    # Calculate normalized power difference
    power_diff = (p1_power - p2_power) / total_power
    
    # Apply sigmoid function to get probability between 0.1 and 0.9
    # This ensures no probability is ever exactly 0 or 1
    p1_prob = 0.5 + (0.4 * power_diff)
    
    # Ensure probability is between 0.1 and 0.9
    p1_prob = max(0.1, min(0.9, p1_prob))
    p2_prob = 1 - p1_prob
    
    return p1_prob, p2_prob, power_diff

def calculate_payout(prob, min_payout=1.1, max_payout=10.0):
    """Calculate payout based on probability with safety checks"""
    # Handle edge cases
    if prob <= 0.01:
        return max_payout
    elif prob >= 0.99:
        return min_payout
    
    # Calculate payout with caps
    raw_payout = 1 / prob
    return max(min_payout, min(raw_payout, max_payout))

def run_master_duel(num_simulations=1, generate_report=True, 
                   enhanced_visuals=True, replay_speed=0.3,
                   session_id=None, bet_multiplier=1, betting_manager=None):
    """Run a complete duel experience with simulation and visualization"""
    # Load custom configuration
    config_file = "custom_config.json"
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Fore.YELLOW}Warning: Could not load custom configuration. Using defaults.{Fore.WHITE}")
        config = {}
    
    # Get player configurations
    player1_config = config.get("player1", {
        "name": "0xEC",
        "hp": 99,
        "attack": 99,
        "defense": 99,
        "strength": 99,
        "position": "left"
    })
    
    player2_config = config.get("player2", {
        "name": "noLE",
        "hp": 99,
        "attack": 99,
        "defense": 99,
        "strength": 99,
        "position": "right"
    })
    
    # Create player objects
    player1 = SimplePlayer(
        name=player1_config["name"],
        hp=player1_config["hp"],
        attack=player1_config["attack"],
        defense=player1_config["defense"],
        strength=player1_config["strength"],
        position=player1_config["position"]
    )
    
    player2 = SimplePlayer(
        name=player2_config["name"],
        hp=player2_config["hp"],
        attack=player2_config["attack"],
        defense=player2_config["defense"],
        strength=player2_config["strength"],
        position=player2_config["position"]
    )
    
    # Display welcome message
    print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           DUELSIM MASTER EXPERIENCE           {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    
    print(f"A battle between {Fore.BLUE}{player1.name}{Fore.WHITE} and {Fore.RED}{player2.name}{Fore.WHITE} is about to begin!\n")
    print(f"{Fore.BLUE}{player1.name}: {player1.hp} HP, {player1.attack} ATK, {player1.defense} DEF")
    print(f"{Fore.RED}{player2.name}: {player2.hp} HP, {player2.attack} ATK, {player2.defense} DEF\n")
    
    # Display initial matchup analysis (before equipment)
    print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           PRE-BATTLE ANALYSIS              {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    display_matchup_analysis(player1, player2)
    
    # Prompt user to continue
    print(f"\n{Fore.YELLOW}Press Enter to equip items and start the battle...{Fore.WHITE}")
    input()
    
    # Load items
    print(f"\nLoading equipment...")
    items_file = "balanced_items_1337.json"  # Use balanced items
    try:
        with open(items_file, 'r') as f:
            items = json.load(f)
        print(f"Loaded {len(items)} items from {items_file}")
    except (FileNotFoundError, json.JSONDecodeError):
        # Try the original items file if balanced doesn't exist
        items_file = "items_1337.json"
        try:
            with open(items_file, 'r') as f:
                items = json.load(f)
            print(f"Loaded {len(items)} items from {items_file}")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"{Fore.RED}Error: Could not load items. Run fix_items.py first.")
            items = []
    
    # Equip random items to players
    print(f"\nEquipping random items to players:")
    equipped_items_p1 = equip_random_items(player1, items, num_items=3, return_items=True)
    equipped_items_p2 = equip_random_items(player2, items, num_items=3, return_items=True)
    
    # Update the configs with the new stats
    player1_config["hp"] = player1.hp
    player1_config["attack"] = player1.attack
    player1_config["defense"] = player1.defense
    player1_config["strength"] = player1.strength
    
    player2_config["hp"] = player2.hp
    player2_config["attack"] = player2.attack
    player2_config["defense"] = player2.defense
    player2_config["strength"] = player2.strength
    
    print(f"\n{Fore.BLUE}{player1.name}: {player1.hp} HP, {player1.attack} ATK, {player1.defense} DEF, {player1.strength} STR")
    print(f"{Fore.RED}{player2.name}: {player2.hp} HP, {player2.attack} ATK, {player2.defense} DEF, {player2.strength} STR\n")
    
    # Display updated matchup analysis (after equipment)
    print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}        UPDATED ANALYSIS WITH EQUIPMENT      {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    
    # Calculate win probabilities and payouts
    p1_prob, p2_prob, total_diff = compute_win_probability(player1, player2)
    p1_payout = calculate_payout(p1_prob)
    p2_payout = calculate_payout(p2_prob)
    
    # Display updated analysis with equipment
    display_matchup_analysis(player1, player2)
    
    # Prompt for bet if we have a betting manager
    bet_placed = False
    if betting_manager:
        bet_placed = betting_manager.prompt_for_bet(player1, player2, p1_payout, p2_payout)
    
    # Run the simulation (no additional prompt)
    print(f"\n{Fore.CYAN}Running duel simulation...")
    
    # Convert string positions to coordinates if needed
    if isinstance(player1.position, str):
        if player1.position == "left":
            player1.position = (0, 2)  # Left side of the arena
        elif player1.position == "right":
            player1.position = (4, 2)  # Right side of the arena
        else:
            player1.position = (0, 0)  # Default position
    
    if isinstance(player2.position, str):
        if player2.position == "right":
            player2.position = (4, 2)  # Right side of the arena
        elif player2.position == "left":
            player2.position = (0, 2)  # Left side of the arena
        else:
            player2.position = (4, 4)  # Default position
    
    # Create player configs from player objects
    player1_config = {
        "name": player1.name,
        "hp": player1.hp,
        "attack": player1.attack,
        "defense": player1.defense,
        "strength": player1.strength,
        "position": player1.position
    }
    
    player2_config = {
        "name": player2.name,
        "hp": player2.hp,
        "attack": player2.attack,
        "defense": player2.defense,
        "strength": player2.strength,
        "position": player2.position
    }
    
    # Now run the simulation with the updated positions
    try:
        result = run_duel_simulation(
            max_ticks=200,
            visualize=enhanced_visuals,
            tick_duration_ms=int(replay_speed * 1000),
            player1_config=player1_config,
            player2_config=player2_config,
            rules_config={}
        )
    except TypeError as e:
        # If the function signature is different, try an alternative approach
        print(f"{Fore.YELLOW}Warning: Adjusting simulation parameters: {e}")
        result = run_duel_simulation(
            max_ticks=200,
            visualize=enhanced_visuals,
            tick_duration_ms=int(replay_speed * 1000),
            player1=player1,
            player2=player2
        )
    
    # Get the winner
    winner_name = result.get("winner", "")
    
    # Process bet result if a bet was placed
    if betting_manager and bet_placed:
        payouts = {player1.name: p1_payout, player2.name: p2_payout}
        profit = betting_manager.process_result(winner_name, payouts)
        
        profit_color = Fore.GREEN if profit >= 0 else Fore.RED
        print(f"\n{Fore.YELLOW}Bet Result: {profit_color}${profit:.2f}")
        betting_manager.display_bank()
    
    # Record betting analytics
    analytics = BettingAnalytics(session_id=session_id)
    
    # Record equipment scores for analysis
    equipment_scores = {
        player1.name: calculate_equipment_score(player1),
        player2.name: calculate_equipment_score(player2)
    }
    
    analytics.record_match(
        player1=player1,
        player2=player2,
        predicted_probs=(p1_prob, p2_prob),
        winner=winner_name,
        equipment_scores=equipment_scores,
        bet_multiplier=bet_multiplier
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
        # Create a simple Item-like class that mimics the Item class
        class SimpleItem:
            def __init__(self, name, slot, stats, rarity="COMMON"):
                self.name = name
                self.slot = slot
                self.stats = stats
                
                # Create a rarity object that mimics ItemRarity enum
                class SimpleRarity:
                    def __init__(self, rarity_str):
                        self.name = rarity_str
                        # Map string rarities to values
                        rarity_values = {
                            "COMMON": 1,
                            "UNCOMMON": 2,
                            "RARE": 3,
                            "EPIC": 4,
                            "LEGENDARY": 5,
                            "MYTHIC": 6
                        }
                        self.value = rarity_values.get(rarity_str, 1)
                
                self.rarity = SimpleRarity(rarity)
        
        # Create visualization players with equipment
        viz_player1 = SimplePlayer(
            name=player1.name,
            hp=player1.hp,
            attack=player1.attack,
            defense=player1.defense,
            strength=player1.strength,
            position=player1.position
        )
        
        viz_player2 = SimplePlayer(
            name=player2.name,
            hp=player2.hp,
            attack=player2.attack,
            defense=player2.defense,
            strength=player2.strength,
            position=player2.position
        )
        
        # Copy equipment to visualization players
        for slot, item in player1.equipment.items():
            if isinstance(item, dict):
                # For dictionary items, create a simple Item object
                try:
                    simple_item = SimpleItem(
                        name=item.get("name", "Unknown Item"),
                        slot=slot,  # Use the slot from the equipment dictionary key
                        stats=item.get("stats", {}),
                        rarity=item.get("rarity", "COMMON")
                    )
                    
                    # Add the item to the visualization player
                    viz_player1.equipment[slot] = simple_item
                except Exception as e:
                    print(f"Error loading item for visualization: {e}")
            else:
                # For Item objects, copy directly
                viz_player1.equipment[slot] = item
        
        # Do the same for player2
        for slot, item in player2.equipment.items():
            if isinstance(item, dict):
                # For dictionary items, create a simple Item object
                try:
                    simple_item = SimpleItem(
                        name=item.get("name", "Unknown Item"),
                        slot=slot,  # Use the slot from the equipment dictionary key
                        stats=item.get("stats", {}),
                        rarity=item.get("rarity", "COMMON")
                    )
                    
                    # Add the item to the visualization player
                    viz_player2.equipment[slot] = simple_item
                except Exception as e:
                    print(f"Error loading item for visualization: {e}")
            else:
                # For Item objects, copy directly
                viz_player2.equipment[slot] = item
        
        # Create visualizer
        arena_size = config.get("arena_size", {"width": 5, "height": 5})
        visualizer = EnhancedVisualizer(width=arena_size.get("width", 5), 
                                       height=arena_size.get("height", 5))
        
        # Display pre-battle analysis with ELO and betting odds
        display_matchup_analysis(viz_player1, viz_player2)
        
        # Show replay banner
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           BATTLE REPLAY STARTING           {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        print(f"{Fore.WHITE}Replaying the battle between {Fore.BLUE}{viz_player1.name}{Fore.WHITE} and {Fore.RED}{viz_player2.name}{Fore.WHITE}!")
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
                    visualizer.render_arena([viz_player1, viz_player2])
            
            # Process different event types
            if "attack" in event_type:
                # Extract attacker, defender and damage from message
                if viz_player1.name in message and "strikes" in message:
                    attacker, defender = viz_player1, viz_player2
                else:
                    attacker, defender = viz_player2, viz_player1
                
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
                if viz_player1.name in message and "moves" in message:
                    # Simple position update for demo
                    x, y = viz_player1.position
                    if x < viz_player2.position[0]:
                        viz_player1.position = (x + 1, y)
                    elif x > viz_player2.position[0]:
                        viz_player1.position = (x - 1, y)
                    elif y < viz_player2.position[1]:
                        viz_player1.position = (x, y + 1)
                    elif y > viz_player2.position[1]:
                        viz_player1.position = (x, y - 1)
                
                elif viz_player2.name in message and "moves" in message:
                    # Simple position update for demo
                    x, y = viz_player2.position
                    if x < viz_player1.position[0]:
                        viz_player2.position = (x + 1, y)
                    elif x > viz_player1.position[0]:
                        viz_player2.position = (x - 1, y)
                    elif y < viz_player1.position[1]:
                        viz_player2.position = (x, y + 1)
                    elif y > viz_player1.position[1]:
                        viz_player2.position = (x, y - 1)
                
                visualizer.render_event("movement", message)
            
            elif "victory" in event_type or "defeated" in message:
                winner_name = result.get("winner", "")
                winner = viz_player1 if winner_name == viz_player1.name else viz_player2
                loser = viz_player2 if winner_name == viz_player1.name else viz_player1
                
                # Custom victory animation with anime faces
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Victory banner
                victory_banner = [
                    f"{Fore.YELLOW}╔═══════════════════════════════════╗",
                    f"{Fore.YELLOW}║{Fore.WHITE}           VICTORY!                {Fore.YELLOW}║",
                    f"{Fore.YELLOW}╚═══════════════════════════════════╝"
                ]
                
                # Determine colors
                winner_color = Fore.BLUE if winner.name == viz_player1.name else Fore.RED
                loser_color = Fore.RED if winner.name == viz_player1.name else Fore.BLUE
                
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
        visualizer.render_arena([viz_player1, viz_player2])
        
        # Show winner with anime face
        winner_name = result.get("winner", "Unknown")
        winner = viz_player1 if winner_name == viz_player1.name else viz_player2
        loser = viz_player2 if winner_name == viz_player1.name else viz_player1
        
        winner_color = Fore.BLUE if winner.name == viz_player1.name else Fore.RED
        loser_color = Fore.RED if winner.name == viz_player1.name else Fore.BLUE
        
        happy_face = random.choice(HAPPY_ANIME_FACE)
        sad_face = random.choice(SAD_ANIME_FACE)
        
        print(f"\n{Fore.YELLOW}The winner is: {winner_color}{winner.name}! {winner_color}{happy_face}")
        print(f"{Fore.WHITE}Better luck next time, {loser_color}{loser.name}... {loser_color}{sad_face}")
    
    return result

def main():
    """Main function for the master duel experience"""
    # Initialize colorama
    init(autoreset=True)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DuelSim Master Experience')
    parser.add_argument('--initial-bank', type=float, default=1000.0, help='Initial betting bank amount')
    parser.add_argument('--session-id', type=str, default=None, help='Session ID for analytics')
    args = parser.parse_args()
    
    # Display welcome message
    print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           WELCOME TO DUELSIM!              {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
    
    # Create betting manager
    betting_manager = BettingManager(initial_bank=args.initial_bank)
    print(f"You have ${betting_manager.bank:.2f} in your betting bank. Good luck!")
    
    # Main game loop
    while True:
        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           MAIN MENU                     {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        print("1. Run a single duel")
        print("2. Run multiple duels")
        print("3. View betting analytics")
        print("4. Exit")
        
        try:
            choice = int(input(f"\n{Fore.GREEN}Enter your choice (1-4): {Fore.WHITE}"))
            
            if choice == 1:
                # Run a single duel
                run_master_duel(
                    num_simulations=1,
                    generate_report=True,
                    enhanced_visuals=True,
                    replay_speed=0.3,
                    session_id=args.session_id,
                    bet_multiplier=1,
                    betting_manager=betting_manager
                )
            
            elif choice == 2:
                # Run multiple duels
                try:
                    num_games = int(input(f"\n{Fore.GREEN}How many games would you like to run? (1-100): {Fore.WHITE}"))
                    num_games = max(1, min(100, num_games))  # Limit between 1 and 100
                    
                    # Ask about betting strategy for multiple games
                    print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                    print(f"{Fore.CYAN}║{Fore.YELLOW}           BETTING STRATEGY              {Fore.CYAN}║")
                    print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                    
                    print("1. Single bet at the start (bet once for all games)")
                    print("2. Equal bets across all games (divide your bet amount by the number of games)")
                    print("3. No betting")
                    
                    bet_strategy = int(input(f"\n{Fore.GREEN}Choose your betting strategy (1-3): {Fore.WHITE}"))
                    
                    # Set up betting based on strategy
                    if bet_strategy == 1:
                        # Single bet at the start
                        print(f"\n{Fore.YELLOW}You'll place a single bet that applies to all {num_games} games.")
                        print(f"If you win more than 50% of the games, you win the bet.")
                        
                        # Store original prompt_for_bet method
                        original_prompt = betting_manager.prompt_for_bet
                        
                        # Override with a version that explains the multi-game betting
                        def multi_game_prompt(player1, player2, p1_payout, p2_payout):
                            betting_manager.display_bank()
                            
                            print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                            print(f"{Fore.CYAN}║{Fore.YELLOW}           PLACE YOUR BET                 {Fore.CYAN}║")
                            print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                            
                            p1_name = player1.name if hasattr(player1, 'name') else player1["name"]
                            p2_name = player2.name if hasattr(player2, 'name') else player2["name"]
                            
                            print(f"{Fore.YELLOW}This bet applies to all {num_games} games.")
                            print(f"You'll win if your chosen player wins the majority of games.\n")
                            
                            print(f"1. {Fore.BLUE}{p1_name}{Fore.WHITE} - Payout: {p1_payout:.2f}x")
                            print(f"2. {Fore.RED}{p2_name}{Fore.WHITE} - Payout: {p2_payout:.2f}x")
                            print(f"3. Skip betting this round")
                            
                            # Get player choice
                            while True:
                                try:
                                    choice = int(input(f"\n{Fore.GREEN}Who would you like to bet on? (1/2/3): {Fore.WHITE}"))
                                    if choice in [1, 2, 3]:
                                        break
                                    print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")
                                except ValueError:
                                    print(f"{Fore.RED}Please enter a valid number.")
                            
                            if choice == 3:
                                print(f"{Fore.YELLOW}Skipping bet for this round.")
                                return False
                            
                            # Get bet amount
                            while True:
                                try:
                                    # Suggest bet amounts
                                    print(f"\nSuggested bets: ${min(10, betting_manager.bank)}, ${min(50, betting_manager.bank)}, ${min(100, betting_manager.bank)}, ${min(betting_manager.bank//2, betting_manager.bank)}")
                                    print(f"Your bank: ${betting_manager.bank}")
                                    
                                    amount = float(input(f"{Fore.GREEN}How much would you like to bet? ${Fore.WHITE}"))
                                    if 0 < amount <= betting_manager.bank:
                                        break
                                    elif amount > betting_manager.bank:
                                        print(f"{Fore.RED}Insufficient funds! Your bank: ${betting_manager.bank}")
                                    else:
                                        print(f"{Fore.RED}Bet amount must be positive.")
                                except ValueError:
                                    print(f"{Fore.RED}Please enter a valid amount.")
                            
                            # Place the bet
                            bet_on = p1_name if choice == 1 else p2_name
                            if betting_manager.place_bet(amount, bet_on):
                                bet_color = Fore.BLUE if choice == 1 else Fore.RED
                                print(f"\n{Fore.GREEN}You bet ${amount:.2f} on {bet_color}{bet_on}{Fore.GREEN}!")
                                print(f"If you win, you'll receive ${amount * (p1_payout if choice == 1 else p2_payout):.2f} (profit: ${amount * ((p1_payout if choice == 1 else p2_payout) - 1):.2f})")
                                return True
                            
                            return False
                        
                        # Replace the prompt method temporarily
                        betting_manager.prompt_for_bet = multi_game_prompt
                        
                        # Variables to track multi-game results
                        multi_game_bet_placed = False
                        multi_game_bet_on = None
                        multi_game_bet_amount = 0
                        multi_game_payout = 0
                        wins_for_bet = 0
                        total_games_played = 0
                        
                    elif bet_strategy == 2:
                        # Equal bets across all games
                        print(f"\n{Fore.YELLOW}Your bet amount will be divided equally across all {num_games} games.")
                        
                        # Store original prompt_for_bet method
                        original_prompt = betting_manager.prompt_for_bet
                        
                        # Override with a version that explains the divided betting
                        def divided_bet_prompt(player1, player2, p1_payout, p2_payout):
                            if not hasattr(divided_bet_prompt, 'initial_bet_made'):
                                divided_bet_prompt.initial_bet_made = False
                                divided_bet_prompt.bet_on = None
                                divided_bet_prompt.total_amount = 0
                                divided_bet_prompt.per_game_amount = 0
                                divided_bet_prompt.payout = 0
                            
                            if not divided_bet_prompt.initial_bet_made:
                                betting_manager.display_bank()
                                
                                print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                                print(f"{Fore.CYAN}║{Fore.YELLOW}           PLACE YOUR BET                 {Fore.CYAN}║")
                                print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                                
                                p1_name = player1.name if hasattr(player1, 'name') else player1["name"]
                                p2_name = player2.name if hasattr(player2, 'name') else player2["name"]
                                
                                print(f"{Fore.YELLOW}Your bet will be divided into {num_games} equal parts.")
                                print(f"Each game will use 1/{num_games} of your total bet amount.\n")
                                
                                print(f"1. {Fore.BLUE}{p1_name}{Fore.WHITE} - Payout: {p1_payout:.2f}x")
                                print(f"2. {Fore.RED}{p2_name}{Fore.WHITE} - Payout: {p2_payout:.2f}x")
                                print(f"3. Skip betting this round")
                                
                                # Get player choice
                                while True:
                                    try:
                                        choice = int(input(f"\n{Fore.GREEN}Who would you like to bet on? (1/2/3): {Fore.WHITE}"))
                                        if choice in [1, 2, 3]:
                                            break
                                        print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")
                                    except ValueError:
                                        print(f"{Fore.RED}Please enter a valid number.")
                                
                                if choice == 3:
                                    print(f"{Fore.YELLOW}Skipping bet for this round.")
                                    return False
                                
                                # Get bet amount
                                while True:
                                    try:
                                        # Suggest bet amounts
                                        print(f"\nSuggested bets: ${min(10, betting_manager.bank)}, ${min(50, betting_manager.bank)}, ${min(100, betting_manager.bank)}, ${min(betting_manager.bank//2, betting_manager.bank)}")
                                        print(f"Your bank: ${betting_manager.bank}")
                                        
                                        amount = float(input(f"{Fore.GREEN}How much would you like to bet in total? ${Fore.WHITE}"))
                                        if 0 < amount <= betting_manager.bank:
                                            break
                                        elif amount > betting_manager.bank:
                                            print(f"{Fore.RED}Insufficient funds! Your bank: ${betting_manager.bank}")
                                        else:
                                            print(f"{Fore.RED}Bet amount must be positive.")
                                    except ValueError:
                                        print(f"{Fore.RED}Please enter a valid amount.")
                                
                                # Calculate per-game amount
                                per_game_amount = amount / num_games
                                
                                # Store bet details
                                divided_bet_prompt.initial_bet_made = True
                                divided_bet_prompt.bet_on = p1_name if choice == 1 else p2_name
                                divided_bet_prompt.total_amount = amount
                                divided_bet_prompt.per_game_amount = per_game_amount
                                divided_bet_prompt.payout = p1_payout if choice == 1 else p2_payout
                                
                                bet_color = Fore.BLUE if choice == 1 else Fore.RED
                                print(f"\n{Fore.GREEN}You bet ${amount:.2f} total on {bet_color}{divided_bet_prompt.bet_on}{Fore.GREEN}!")
                                print(f"Each game will use ${per_game_amount:.2f} of your bet.")
                                print(f"If you win all games, you'll receive ${amount * divided_bet_prompt.payout:.2f} (profit: ${amount * (divided_bet_prompt.payout - 1):.2f})")
                            
                            # Place the per-game bet
                            if betting_manager.place_bet(divided_bet_prompt.per_game_amount, divided_bet_prompt.bet_on):
                                return True
                            
                            return False
                        
                        # Replace the prompt method temporarily
                        betting_manager.prompt_for_bet = divided_bet_prompt
                    
                    # Ask if they want to see visualizations for all games
                    print(f"\n{Fore.YELLOW}Running {num_games} duels in sequence...{Fore.WHITE}")
                    show_visuals = input(f"\n{Fore.GREEN}Show visualizations for all games? (y/n): {Fore.WHITE}").lower() == 'y'
                    
                    # Run the games
                    for i in range(num_games):
                        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                        print(f"{Fore.CYAN}║{Fore.YELLOW}           GAME {i+1} OF {num_games}                {Fore.CYAN}║")
                        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                        
                        # Run the duel
                        result = run_master_duel(
                            num_simulations=1,
                            generate_report=True,
                            enhanced_visuals=show_visuals,
                            replay_speed=0.3 if show_visuals else 0,
                            session_id=args.session_id,
                            bet_multiplier=1,
                            betting_manager=betting_manager
                        )
                        
                        # Track results for multi-game betting
                        if bet_strategy == 1 and hasattr(result, 'get'):
                            winner = result.get('winner', '')
                            if multi_game_bet_on == winner:
                                wins_for_bet += 1
                            total_games_played += 1
                    
                    # Restore original prompt method
                    if bet_strategy in [1, 2]:
                        betting_manager.prompt_for_bet = original_prompt
                    
                    # Process multi-game bet result
                    if bet_strategy == 1 and multi_game_bet_placed:
                        win_percentage = (wins_for_bet / total_games_played) * 100
                        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                        print(f"{Fore.CYAN}║{Fore.YELLOW}           MULTI-GAME BET RESULT          {Fore.CYAN}║")
                        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                        
                        print(f"Your bet: ${multi_game_bet_amount:.2f} on {multi_game_bet_on}")
                        print(f"Games won by {multi_game_bet_on}: {wins_for_bet}/{total_games_played} ({win_percentage:.1f}%)")
                        
                        # Determine if bet is won (more than 50% wins)
                        if win_percentage > 50:
                            winnings = multi_game_bet_amount * multi_game_payout
                            profit = winnings - multi_game_bet_amount
                            betting_manager.bank += winnings  # Add winnings to bank
                            betting_manager.session_profit += profit
                            betting_manager.session_wins += 1
                            
                            print(f"{Fore.GREEN}Congratulations! You won your multi-game bet!")
                            print(f"Winnings: ${winnings:.2f} (Profit: ${profit:.2f})")
                        else:
                            print(f"{Fore.RED}Sorry, you lost your multi-game bet of ${multi_game_bet_amount:.2f}.")
                            betting_manager.session_profit -= multi_game_bet_amount
                    
                    print(f"\n{Fore.GREEN}Completed {num_games} duels!{Fore.WHITE}")
                    betting_manager.display_bank()
                    
                except ValueError:
                    print(f"{Fore.RED}Please enter a valid number of games.")
            
            elif choice == 3:
                # View betting analytics
                print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
                print(f"{Fore.CYAN}║{Fore.YELLOW}           BETTING ANALYTICS            {Fore.CYAN}║")
                print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
                
                betting_manager.display_bank()
                
                # Ask if they want to generate a full report
                if input(f"\n{Fore.GREEN}Generate full analytics report? (y/n): {Fore.WHITE}").lower() == 'y':
                    analytics = BettingAnalytics(session_id=args.session_id)
                    report_file = analytics.generate_report()
                    if report_file:
                        print(f"Report generated: {report_file}")
            
            elif choice == 4:
                # Exit the game
                break
            
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and 4.")
                
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.")
    
    # Display final stats
    profit = betting_manager.bank - args.initial_bank
    profit_color = Fore.GREEN if profit >= 0 else Fore.RED
    
    print(f"Starting Bank: ${args.initial_bank:.2f}")
    print(f"Final Bank: ${betting_manager.bank:.2f}")
    print(f"Total Profit: {profit_color}${profit:.2f}")
    print(f"Win Rate: {betting_manager.session_wins}/{betting_manager.session_bets} ({(betting_manager.session_wins/betting_manager.session_bets)*100:.1f}% win rate)" if betting_manager.session_bets > 0 else "No bets placed")

    print(f"\n{Fore.GREEN}Thanks for playing DuelSim! Come back soon!")

if __name__ == "__main__":
    main() 