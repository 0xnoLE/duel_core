"""
Custom game runner that works with the installed duelsim package
"""
from duelsim import run_duel_simulation
import json
import os
from game_reporter import GameReporter

def load_custom_config(filename="custom_config.json"):
    """Load custom configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not load {filename}, using default config")
        return {}

def run_custom_game(num_simulations=1, generate_report=True, enhanced_visuals=True):
    """Run one or more games with custom configuration"""
    # Load custom configuration
    config = load_custom_config()

    # Custom player configurations
    player1_config = {
        "name": "0xEC",
        "hp": 99,
        "attack": 99,
        "strength": 99,
        "defense": 99
    }

    player2_config = {
        "name": "noLE",
        "hp": 99,
        "attack": 99,
        "strength":99,
        "defense": 99
    }

    # Store results for multiple simulations
    all_results = []
    
    for i in range(num_simulations):
        if num_simulations > 1:
            print(f"\nRunning simulation {i+1}/{num_simulations}...")
        
        # Run the simulation using the imported function
        result = run_duel_simulation(
            max_ticks=200,
            visualize=True if num_simulations == 1 else False,  # Only visualize single runs
            tick_duration_ms=250,
            player1_config=player1_config,
            player2_config=player2_config,
            rules_config=config,
            enhanced_visuals=enhanced_visuals  # Use enhanced visuals
        )
        
        # Save the result
        all_results.append(result)
        
        # For single simulations, save to the standard file
        if num_simulations == 1:
            with open("game_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nCustom game finished. Winner: {result['winner']}")
            print(f"Result saved to game_result.json")
    
    # Generate reports if requested
    if generate_report:
        reporter = GameReporter()
        
        if num_simulations == 1:
            # Generate single report
            report_path = reporter.generate_report()
            print(f"Report generated: {report_path}")
        else:
            # Save all results to a file
            with open("multi_game_results.json", "w") as f:
                json.dump(all_results, f, indent=2)
            
            # Generate multi-simulation report
            report_path = reporter.generate_multi_report(all_results)
            print(f"Multi-simulation report generated: {report_path}")
    
    return all_results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run custom duel simulations")
    parser.add_argument("-n", "--num-simulations", type=int, default=1,
                        help="Number of simulations to run (default: 1)")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip generating reports")
    parser.add_argument("--no-enhanced-visuals", action="store_true",
                        help="Use basic visualization instead of enhanced")
    
    args = parser.parse_args()
    
    run_custom_game(num_simulations=args.num_simulations, 
                   generate_report=not args.no_report,
                   enhanced_visuals=not args.no_enhanced_visuals) 