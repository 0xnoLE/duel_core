import argparse
from duelsim.main import run_duel_simulation

def main():
    parser = argparse.ArgumentParser(description='DuelSim Human vs AI')
    parser.add_argument('--player1', choices=['human', 'ai'], default='human',
                        help='Controller for Player 1 (default: human)')
    parser.add_argument('--player2', choices=['human', 'ai'], default='ai',
                        help='Controller for Player 2 (default: ai)')
    parser.add_argument('--ticks', type=int, default=300,
                        help='Maximum number of ticks (default: 300)')
    parser.add_argument('--tick-duration', type=int, default=600,
                        help='Duration of each tick in milliseconds (default: 600)')
    parser.add_argument('--no-visuals', action='store_true',
                        help='Disable enhanced visuals')
    
    args = parser.parse_args()
    
    # Print controls
    print("=== DuelSim Human Controls ===")
    print("A: Attack")
    print("S: Special Attack")
    print("E: Eat Food")
    print("W: Switch Weapon")
    print("Arrow Keys: Move")
    print("P: Toggle Prayer")
    print("O: Use Potion")
    print("R: Toggle Run")
    print("============================")
    
    # Run the simulation
    run_duel_simulation(
        max_ticks=args.ticks,
        tick_duration_ms=args.tick_duration,
        enhanced_visuals=not args.no_visuals,
        player1_human=(args.player1 == 'human'),
        player2_human=(args.player2 == 'human')
    )

if __name__ == "__main__":
    main() 