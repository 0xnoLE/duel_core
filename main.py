from entities.player import Player
from engine.tick_manager import TickManager
from engine.rules import RuleSet
from ai.basic_agent import BasicAgent

def main():
    # Create tick manager
    tick_manager = TickManager(tick_duration_ms=600)
    
    # Create players
    player1 = Player(name="Fighter1", hp=99, attack=75, strength=80, defense=70)
    player2 = Player(name="Fighter2", hp=99, attack=70, strength=75, defense=80)
    
    # Set initial positions
    player1.position = (0, 0)
    player2.position = (1, 0)
    
    # Register players
    tick_manager.register_player(player1)
    tick_manager.register_player(player2)
    
    # Create rule set
    rules = RuleSet({
        "allow_melee": True,
        "allow_ranged": False,
        "allow_magic": False,
        "no_food": False,
        "no_movement": False
    })
    
    # Create AI agents
    agent1 = BasicAgent(player1, aggression=0.8)
    agent2 = BasicAgent(player2, aggression=0.6)
    
    # Pre-load some initial actions
    player1.add_action("attack", target=player2, execute_on=4)
    player2.add_action("move", destination=(2, 0), execute_on=1)
    
    # Start the duel
    print("Starting duel...")
    tick_manager.start_duel()
    
    # After duel ends, print summary
    print("\nDuel Summary:")
    for event in tick_manager.events:
        print(f"[Tick {event['tick']}] {event['message']}")

if __name__ == "__main__":
    main() 