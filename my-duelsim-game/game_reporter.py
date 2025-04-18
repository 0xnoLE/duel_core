"""
Game Reporter - Generates human-readable reports from duel simulation results
"""
import json
import os
from datetime import datetime

class GameReporter:
    def __init__(self, results_file="game_result.json", output_dir="reports"):
        """Initialize the reporter with file paths"""
        self.results_file = results_file
        self.output_dir = output_dir
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def load_results(self):
        """Load game results from JSON file"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading results: {e}")
            return None
    
    def generate_report(self, result=None, filename=None):
        """Generate a human-readable report from game results"""
        # Load results if not provided
        if result is None:
            result = self.load_results()
            if result is None:
                return False
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            winner = result.get("winner", "unknown")
            filename = f"duel_{winner}_{timestamp}.txt"
        
        # Full path to output file
        output_path = os.path.join(self.output_dir, filename)
        
        # Extract data from result
        winner = result.get("winner", "Unknown")
        events = result.get("events", [])
        final_state = result.get("final_state", {})
        stats = result.get("statistics", {})
        
        # Generate report content
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"DUEL SIMULATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        
        # Summary
        p1 = final_state.get("player1", {})
        p2 = final_state.get("player2", {})
        p1_name = p1.get("name", "Player 1")
        p2_name = p2.get("name", "Player 2")
        
        lines.append("\nSUMMARY:")
        lines.append(f"Winner: {winner}")
        lines.append(f"Duration: {final_state.get('ticks', 0)} ticks")
        lines.append(f"\n{p1_name}: {p1.get('hp', 0)}/{p1.get('max_hp', 100)} HP remaining")
        lines.append(f"{p2_name}: {p2.get('hp', 0)}/{p2.get('max_hp', 100)} HP remaining")
        
        # Statistics
        if stats:
            lines.append("\nSTATISTICS:")
            
            # Damage stats
            damage_stats = stats.get("damage", {})
            for player_name, player_stats in damage_stats.items():
                lines.append(f"\n{player_name}:")
                lines.append(f"  Damage Dealt: {player_stats.get('dealt', 0)}")
                lines.append(f"  Damage Received: {player_stats.get('received', 0)}")
                lines.append(f"  Attacks: {player_stats.get('attacks', 0)}")
                lines.append(f"  Critical Hits: {player_stats.get('critical_hits', 0)}")
                
                # Calculate hit rate if attacks > 0
                attacks = player_stats.get('attacks', 0)
                if attacks > 0:
                    crit_rate = (player_stats.get('critical_hits', 0) / attacks) * 100
                    avg_damage = player_stats.get('dealt', 0) / attacks if attacks > 0 else 0
                    lines.append(f"  Critical Hit Rate: {crit_rate:.1f}%")
                    lines.append(f"  Average Damage per Hit: {avg_damage:.1f}")
            
            # Movement stats
            movement_stats = stats.get("movement", {})
            if movement_stats:
                lines.append("\nMovement:")
                for player_name, moves in movement_stats.items():
                    lines.append(f"  {player_name}: {moves} moves")
        
        # Battle Narrative
        lines.append("\nBATTLE NARRATIVE:")
        for event in events:
            tick = event.get("tick", 0)
            event_type = event.get("type", "unknown")
            message = event.get("message", "")
            
            # Format based on event type
            if event_type == "narrative":
                lines.append(f"\n[Tick {tick}] {message}")
            elif event_type == "victory" or event_type == "draw":
                lines.append(f"\n[Tick {tick}] *** {message} ***")
            else:
                lines.append(f"[Tick {tick}] {message}")
        
        # Write to file
        try:
            with open(output_path, 'w') as f:
                f.write("\n".join(lines))
            print(f"Report saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error writing report: {e}")
            return False
    
    def generate_multi_report(self, results_list, filename=None):
        """Generate a report comparing multiple simulation results"""
        if not results_list:
            print("No results provided for multi-report")
            return False
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_duel_report_{timestamp}.txt"
        
        # Full path to output file
        output_path = os.path.join(self.output_dir, filename)
        
        # Generate report content
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"MULTI-DUEL SIMULATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Number of Simulations: {len(results_list)}")
        lines.append("=" * 60)
        
        # Collect winners
        winners = {}
        total_ticks = 0
        total_damage = 0
        total_crits = 0
        total_attacks = 0
        
        for i, result in enumerate(results_list):
            winner = result.get("winner", "Unknown")
            winners[winner] = winners.get(winner, 0) + 1
            
            # Collect stats
            final_state = result.get("final_state", {})
            total_ticks += final_state.get("ticks", 0)
            
            stats = result.get("statistics", {})
            damage_stats = stats.get("damage", {})
            
            for player_name, player_stats in damage_stats.items():
                total_damage += player_stats.get("dealt", 0)
                total_attacks += player_stats.get("attacks", 0)
                total_crits += player_stats.get("critical_hits", 0)
        
        # Summary statistics
        lines.append("\nWIN DISTRIBUTION:")
        for winner, count in winners.items():
            percentage = (count / len(results_list)) * 100
            lines.append(f"  {winner}: {count} wins ({percentage:.1f}%)")
        
        lines.append("\nAVERAGE STATISTICS:")
        lines.append(f"  Average Duration: {total_ticks / len(results_list):.1f} ticks")
        lines.append(f"  Average Damage per Simulation: {total_damage / len(results_list):.1f}")
        
        if total_attacks > 0:
            lines.append(f"  Overall Critical Hit Rate: {(total_crits / total_attacks) * 100:.1f}%")
        
        # Individual simulation summaries
        lines.append("\nINDIVIDUAL SIMULATION SUMMARIES:")
        for i, result in enumerate(results_list):
            winner = result.get("winner", "Unknown")
            final_state = result.get("final_state", {})
            ticks = final_state.get("ticks", 0)
            
            p1 = final_state.get("player1", {})
            p2 = final_state.get("player2", {})
            
            lines.append(f"\nSimulation #{i+1}:")
            lines.append(f"  Winner: {winner}")
            lines.append(f"  Duration: {ticks} ticks")
            lines.append(f"  {p1.get('name', 'Player 1')}: {p1.get('hp', 0)}/{p1.get('max_hp', 100)} HP remaining")
            lines.append(f"  {p2.get('name', 'Player 2')}: {p2.get('hp', 0)}/{p2.get('max_hp', 100)} HP remaining")
        
        # Write to file
        try:
            with open(output_path, 'w') as f:
                f.write("\n".join(lines))
            print(f"Multi-simulation report saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error writing multi-report: {e}")
            return False


def generate_report_from_file(input_file="game_result.json", output_file=None):
    """Utility function to generate a report from a specific file"""
    reporter = GameReporter(results_file=input_file)
    return reporter.generate_report(filename=output_file)


if __name__ == "__main__":
    # Example usage
    reporter = GameReporter()
    reporter.generate_report() 