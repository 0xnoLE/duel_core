"""
Betting Analytics for DuelSim
Tracks prediction accuracy and profitability over time
"""
import os
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
from colorama import init, Fore, Style
import uuid
import argparse
from datetime import datetime, timedelta

# Initialize colorama
init(autoreset=True)

class BettingAnalytics:
    """Tracks and analyzes betting predictions vs actual outcomes"""
    
    def __init__(self, analytics_file="betting_analytics.json", session_id=None):
        self.analytics_file = analytics_file
        self.session_id = session_id or str(uuid.uuid4())[:8]  # Generate a short session ID if none provided
        self.data = self._load_data()
        
        # Initialize session if it doesn't exist
        if "sessions" not in self.data:
            self.data["sessions"] = {}
        
        # Create or access current session
        if self.session_id not in self.data["sessions"]:
            self.data["sessions"][self.session_id] = {
                "start_time": datetime.now().isoformat(),
                "matches": [],
                "summary": self._create_empty_summary()
            }
    
    def _create_empty_summary(self):
        """Create an empty summary structure"""
        return {
            "total_matches": 0,
            "favorite_wins": 0,
            "underdog_wins": 0,
            "probability_buckets": {
                "50-60": {"predicted": 0, "actual": 0},
                "60-70": {"predicted": 0, "actual": 0},
                "70-80": {"predicted": 0, "actual": 0},
                "80-90": {"predicted": 0, "actual": 0},
                "90-100": {"predicted": 0, "actual": 0}
            },
            "profit_tracking": {
                "bet_on_favorite": 0,
                "bet_on_underdog": 0,
                "optimal_strategy": 0
            }
        }
    
    def _load_data(self):
        """Load existing analytics data or create new structure"""
        try:
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create new data structure
            return {
                "matches": [],
                "summary": self._create_empty_summary(),
                "sessions": {}
            }
    
    def record_match(self, player1, player2, predicted_probs, winner, equipment_scores=None, bet_multiplier=1):
        """
        Record match outcome and prediction accuracy
        
        Args:
            player1: First player name or object
            player2: Second player name or object
            predicted_probs: Tuple of (p1_prob, p2_prob)
            winner: Name of the winning player
            equipment_scores: Optional dict with equipment scores
            bet_multiplier: Betting multiplier (default: 1)
        """
        # Get player names
        p1_name = player1.name if hasattr(player1, 'name') else player1
        p2_name = player2.name if hasattr(player2, 'name') else player2
        
        # Extract probabilities
        p1_prob, p2_prob = predicted_probs
        
        # Determine favorite and underdog
        favorite = p1_name if p1_prob > p2_prob else p2_name
        underdog = p2_name if p1_prob > p2_prob else p1_name
        favorite_prob = max(p1_prob, p2_prob)
        
        # Record match data
        match_data = {
            "timestamp": datetime.now().isoformat(),
            "player1": p1_name,
            "player2": p2_name,
            "predicted_p1_prob": p1_prob,
            "predicted_p2_prob": p2_prob,
            "winner": winner,
            "favorite": favorite,
            "underdog": underdog,
            "favorite_prob": favorite_prob,
            "favorite_won": winner == favorite,
            "session_id": self.session_id,
            "bet_multiplier": bet_multiplier
        }
        
        # Add equipment scores if provided
        if equipment_scores:
            match_data["equipment_scores"] = equipment_scores
        
        # Add to global matches list
        self.data["matches"].append(match_data)
        
        # Add to session matches list
        self.data["sessions"][self.session_id]["matches"].append(match_data)
        
        # Update global summary statistics
        self._update_summary(match_data, self.data["summary"])
        
        # Update session summary statistics
        self._update_summary(match_data, self.data["sessions"][self.session_id]["summary"])
        
        # Save updated data
        self._save_data()
        
        # Print match analytics
        self._print_match_analytics(match_data)
    
    def _update_summary(self, match_data, summary):
        """Update summary statistics based on match outcome"""
        # Increment total matches
        summary["total_matches"] += 1
        
        # Track favorite vs underdog wins
        if match_data["favorite_won"]:
            summary["favorite_wins"] += 1
        else:
            summary["underdog_wins"] += 1
        
        # Update probability buckets
        favorite_prob = match_data["favorite_prob"] * 100
        
        # Determine which bucket this falls into
        for bucket in ["50-60", "60-70", "70-80", "80-90", "90-100"]:
            lower, upper = map(int, bucket.split("-"))
            if lower <= favorite_prob < upper or (upper == 100 and favorite_prob == 100):
                summary["probability_buckets"][bucket]["predicted"] += 1
                if match_data["favorite_won"]:
                    summary["probability_buckets"][bucket]["actual"] += 1
                break
        
        # Get bet multiplier
        bet_multiplier = match_data.get("bet_multiplier", 1)
        
        # Update profit tracking (assuming $100 bet)
        bet_amount = 100 * bet_multiplier
        
        # Calculate realistic payouts with caps
        favorite_payout = self._calculate_capped_payout(match_data["favorite_prob"], min_payout=1.1, max_payout=5.0)
        underdog_prob = 1 - match_data["favorite_prob"]
        underdog_payout = self._calculate_capped_payout(underdog_prob, min_payout=1.1, max_payout=20.0)
        
        # Profit if betting on favorite
        if match_data["favorite_won"]:
            # Win amount = bet * (payout - 1)
            profit = bet_amount * (favorite_payout - 1)
            summary["profit_tracking"]["bet_on_favorite"] += profit
        else:
            # Lost the bet
            summary["profit_tracking"]["bet_on_favorite"] -= bet_amount
        
        # Profit if betting on underdog
        if not match_data["favorite_won"]:
            # Win amount = bet * (payout - 1)
            profit = bet_amount * (underdog_payout - 1)
            summary["profit_tracking"]["bet_on_underdog"] += profit
        else:
            # Lost the bet
            summary["profit_tracking"]["bet_on_underdog"] -= bet_amount
        
        # Optimal strategy (bet when expected value is positive)
        if match_data["favorite_prob"] > 0.55:
            # Bet on favorite
            if match_data["favorite_won"]:
                profit = bet_amount * (favorite_payout - 1)
                summary["profit_tracking"]["optimal_strategy"] += profit
            else:
                summary["profit_tracking"]["optimal_strategy"] -= bet_amount
        elif match_data["favorite_prob"] < 0.45:
            # Bet on underdog
            if not match_data["favorite_won"]:
                profit = bet_amount * (underdog_payout - 1)
                summary["profit_tracking"]["optimal_strategy"] += profit
            else:
                summary["profit_tracking"]["optimal_strategy"] -= bet_amount
    
    def _calculate_capped_payout(self, probability, min_payout=1.1, max_payout=20.0):
        """Calculate a realistic payout with caps"""
        if probability <= 0.01:
            # Prevent division by zero or extremely small probabilities
            return max_payout
        
        # Base payout calculation: 1/probability
        raw_payout = 1 / probability
        
        # Apply caps
        return max(min_payout, min(raw_payout, max_payout))
    
    def _save_data(self):
        """Save analytics data to file"""
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _print_match_analytics(self, match_data):
        """Print analytics for the current match"""
        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           BETTING ANALYTICS                {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        # Format probabilities as percentages
        p1_prob = match_data["predicted_p1_prob"] * 100
        p2_prob = match_data["predicted_p2_prob"] * 100
        
        print(f"Match: {Fore.BLUE}{match_data['player1']}{Fore.WHITE} vs {Fore.RED}{match_data['player2']}")
        print(f"Prediction: {Fore.BLUE}{match_data['player1']}: {p1_prob:.1f}%{Fore.WHITE} | {Fore.RED}{match_data['player2']}: {p2_prob:.1f}%")
        
        # Determine favorite color
        fav_color = Fore.BLUE if match_data["favorite"] == match_data["player1"] else Fore.RED
        und_color = Fore.RED if match_data["favorite"] == match_data["player1"] else Fore.BLUE
        
        # Calculate realistic payouts
        favorite_payout = self._calculate_capped_payout(match_data["favorite_prob"])
        underdog_payout = self._calculate_capped_payout(1 - match_data["favorite_prob"])
        
        print(f"Favorite: {fav_color}{match_data['favorite']}{Fore.WHITE} ({match_data['favorite_prob']*100:.1f}%) - Payout: {favorite_payout:.2f}x")
        print(f"Underdog: {und_color}{match_data['underdog']}{Fore.WHITE} ({(1-match_data['favorite_prob'])*100:.1f}%) - Payout: {underdog_payout:.2f}x")
        
        # Get bet multiplier
        bet_multiplier = match_data.get("bet_multiplier", 1)
        multiplier_color = {
            1: Fore.BLUE,
            2: Fore.GREEN,
            3: Fore.YELLOW,
            5: Fore.MAGENTA,
            10: Fore.RED,
            20: Fore.RED
        }.get(bet_multiplier, Fore.WHITE)
        
        print(f"Bet Multiplier: {multiplier_color}{bet_multiplier}x{Fore.WHITE}")
        
        # Outcome
        winner_color = Fore.BLUE if match_data["winner"] == match_data["player1"] else Fore.RED
        print(f"Winner: {winner_color}{match_data['winner']}")
        
        # Prediction accuracy
        bet_amount = 100 * bet_multiplier
        if match_data["favorite_won"]:
            print(f"Prediction: {Fore.GREEN}CORRECT{Fore.WHITE} (Favorite won)")
            profit = bet_amount * (favorite_payout - 1)
            print(f"Profit from betting ${bet_amount} on favorite: {Fore.GREEN}+${profit:.2f}")
        else:
            print(f"Prediction: {Fore.RED}INCORRECT{Fore.WHITE} (Underdog won)")
            profit = bet_amount * (underdog_payout - 1)
            print(f"Profit from betting ${bet_amount} on underdog: {Fore.GREEN}+${profit:.2f}")
        
        # Session info
        print(f"Session ID: {match_data['session_id']}")
    
    def reset_analytics(self, keep_sessions=False):
        """Reset analytics data"""
        # Store sessions if needed
        sessions = self.data["sessions"] if keep_sessions else {}
        
        # Create new data structure
        self.data = {
            "matches": [],
            "summary": self._create_empty_summary(),
            "sessions": sessions
        }
        
        # Save updated data
        self._save_data()
        
        print(f"{Fore.GREEN}Analytics data has been reset.")
        if keep_sessions:
            print(f"{Fore.GREEN}Session data was preserved.")
        else:
            print(f"{Fore.YELLOW}All session data was also reset.")
    
    def start_new_session(self, name=None):
        """Start a new betting session"""
        # Generate a new session ID
        session_id = name or str(uuid.uuid4())[:8]
        
        # Create new session
        self.data["sessions"][session_id] = {
            "start_time": datetime.now().isoformat(),
            "matches": [],
            "summary": self._create_empty_summary()
        }
        
        # Update current session
        self.session_id = session_id
        
        # Save updated data
        self._save_data()
        
        print(f"{Fore.GREEN}Started new session with ID: {Fore.YELLOW}{session_id}")
        return session_id
    
    def end_session(self):
        """End the current session"""
        if self.session_id in self.data["sessions"]:
            self.data["sessions"][self.session_id]["end_time"] = datetime.now().isoformat()
            self._save_data()
            print(f"{Fore.GREEN}Ended session: {Fore.YELLOW}{self.session_id}")
        else:
            print(f"{Fore.RED}No active session found with ID: {self.session_id}")
    
    def list_sessions(self):
        """List all sessions"""
        if not self.data["sessions"]:
            print(f"{Fore.YELLOW}No sessions found.")
            return
        
        print(f"\n{Fore.CYAN}╔{'═' * 50}╗")
        print(f"{Fore.CYAN}║{Fore.YELLOW}           BETTING SESSIONS                {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 50}╝\n")
        
        print(f"{'ID':<10} | {'Start Time':<19} | {'Status':<10} | {'Matches':<7} | {'Profit'}")
        print(f"{'-' * 10}+{'-' * 20}+{'-' * 11}+{'-' * 8}+{'-' * 15}")
        
        for session_id, session in self.data["sessions"].items():
            # Format start time
            start_time = datetime.fromisoformat(session["start_time"]).strftime("%Y-%m-%d %H:%M")
            
            # Determine status
            status = "Completed" if "end_time" in session else "Active"
            status_color = Fore.GREEN if status == "Completed" else Fore.YELLOW
            
            # Get match count
            match_count = len(session["matches"])
            
            # Get profit from optimal strategy
            profit = session["summary"]["profit_tracking"]["optimal_strategy"]
            profit_color = Fore.GREEN if profit >= 0 else Fore.RED
            
            print(f"{session_id:<10} | {start_time:<19} | {status_color}{status:<10}{Fore.WHITE} | {match_count:<7} | {profit_color}${profit:.2f}{Fore.WHITE}")
        
        print()
    
    def generate_session_report(self, session_id=None):
        """Generate a report for a specific session"""
        session_id = session_id or self.session_id
        
        if session_id not in self.data["sessions"]:
            print(f"{Fore.RED}Session {session_id} not found.{Style.RESET_ALL}")
            return None
        
        session_data = self.data["sessions"][session_id]
        
        if not session_data["matches"]:
            print(f"{Fore.YELLOW}No matches in session {session_id}.{Style.RESET_ALL}")
            return None
        
        # Create reports directory
        os.makedirs("reports", exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create report file
        report_file = f"reports/betting_session_{session_id}_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"DUELSIM BETTING ANALYTICS - SESSION REPORT\n")
            f.write(f"Session ID: {session_id}\n")
            
            # Session duration
            start_time = datetime.fromisoformat(session_data["start_time"])
            if "end_time" in session_data:
                end_time = datetime.fromisoformat(session_data["end_time"])
                duration = end_time - start_time
                f.write(f"Duration: {duration}\n")
            else:
                f.write(f"Start Time: {start_time}\n")
                f.write(f"Status: Active\n")
            
            f.write("\n")
            
            # Summary statistics
            summary = session_data["summary"]
            f.write(f"SUMMARY STATISTICS\n")
            f.write(f"-" * 50 + "\n")
            f.write(f"Total Matches: {summary['total_matches']}\n")
            
            if summary['total_matches'] > 0:
                favorite_win_pct = (summary['favorite_wins'] / summary['total_matches']) * 100
                underdog_win_pct = (summary['underdog_wins'] / summary['total_matches']) * 100
                f.write(f"Favorite Wins: {summary['favorite_wins']} ({favorite_win_pct:.1f}%)\n")
                f.write(f"Underdog Wins: {summary['underdog_wins']} ({underdog_win_pct:.1f}%)\n")
            
            f.write("\n")
            
            # Probability accuracy
            f.write(f"PROBABILITY ACCURACY\n")
            f.write(f"-" * 50 + "\n")
            f.write(f"{'Range':<10} | {'Predicted':<9} | {'Actual':<6} | {'Accuracy':<7}\n")
            
            for bucket, data in summary["probability_buckets"].items():
                if data["predicted"] > 0:
                    accuracy = (data["actual"] / data["predicted"]) * 100
                    f.write(f"{bucket}%      | {data['predicted']:9d} | {data['actual']:6d} | {accuracy:7.1f}%\n")
            
            f.write("\n")
            
            # Profit tracking
            f.write("PROFIT TRACKING (based on $100 bets)\n")
            f.write("-" * 50 + "\n")
            f.write(f"Always Bet on Favorite: ${summary['profit_tracking']['bet_on_favorite']:.2f}\n")
            f.write(f"Always Bet on Underdog: ${summary['profit_tracking']['bet_on_underdog']:.2f}\n")
            f.write(f"Optimal Strategy: ${summary['profit_tracking']['optimal_strategy']:.2f}\n\n")
            
            # Match details
            f.write("MATCH DETAILS\n")
            f.write("-" * 50 + "\n")
            
            for match in session_data["matches"]:
                f.write(f"{match['player1']} vs {match['player2']}\n")
                f.write(f"Prediction: {match['player1']} ({match['predicted_p1_prob']*100:.1f}%) vs ")
                f.write(f"{match['player2']} ({match['predicted_p2_prob']*100:.1f}%)\n")
                f.write(f"Winner: {match['winner']}\n")
                f.write(f"Favorite: {match['favorite']} ({match['favorite_prob']*100:.1f}%)\n")
                f.write(f"Outcome: {'Favorite won' if match['favorite_won'] else 'Underdog won'}\n")
                
                if "equipment_scores" in match:
                    f.write(f"Equipment Scores: {match['equipment_scores']}\n")
                
                f.write("-" * 30 + "\n")
        
        # Generate plots for this session
        self._generate_session_plots(session_id, timestamp)
        
        return report_file
    
    def _generate_session_plots(self, session_id, timestamp):
        """Generate plots for a specific session"""
        session_data = self.data["sessions"][session_id]
        
        # Create plots directory
        os.makedirs("reports/plots", exist_ok=True)
        
        # 1. Favorite vs Underdog Win Rate for this session
        self._plot_session_win_rates(session_data, f"reports/plots/session_{session_id}_win_rates_{timestamp}.png")
        
        # 2. Profit Tracking for this session
        self._plot_session_profit_tracking(session_data, f"reports/plots/session_{session_id}_profit_{timestamp}.png")
    
    def _plot_session_win_rates(self, session_data, filename):
        """Plot favorite vs underdog win rates for a session"""
        summary = session_data["summary"]
        if summary["total_matches"] == 0:
            return
        
        labels = ['Favorite', 'Underdog']
        values = [summary["favorite_wins"], summary["underdog_wins"]]
        colors = ['#3498db', '#e74c3c']
        
        plt.figure(figsize=(8, 6))
        plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title(f'Session Win Distribution: Favorite vs Underdog')
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
    
    def _plot_session_profit_tracking(self, session_data, filename):
        """Plot profit tracking for a session"""
        matches = session_data["matches"]
        if not matches:
            return
        
        # Extract match timestamps and calculate cumulative profits
        timestamps = []
        favorite_profit = []
        underdog_profit = []
        optimal_profit = []
        
        cum_favorite = 0
        cum_underdog = 0
        cum_optimal = 0
        
        for match in matches:
            timestamps.append(datetime.fromisoformat(match["timestamp"]))
            
            # Calculate profit for this match
            bet_amount = 100
            
            # Favorite bet
            if match["favorite_won"]:
                profit = bet_amount * (1 / match["favorite_prob"] - 1)
                cum_favorite += profit
            else:
                cum_favorite -= bet_amount
            
            # Underdog bet
            if not match["favorite_won"]:
                underdog_prob = 1 - match["favorite_prob"]
                profit = bet_amount * (1 / underdog_prob - 1)
                cum_underdog += profit
            else:
                cum_underdog -= bet_amount
            
            # Optimal strategy
            if match["favorite_prob"] > 0.55:
                # Bet on favorite
                if match["favorite_won"]:
                    profit = bet_amount * (1 / match["favorite_prob"] - 1)
                    cum_optimal += profit
                else:
                    cum_optimal -= bet_amount
            elif match["favorite_prob"] < 0.45:
                # Bet on underdog
                underdog_prob = 1 - match["favorite_prob"]
                if not match["favorite_won"]:
                    profit = bet_amount * (1 / underdog_prob - 1)
                    cum_optimal += profit
                else:
                    cum_optimal -= bet_amount
            
            favorite_profit.append(cum_favorite)
            underdog_profit.append(cum_underdog)
            optimal_profit.append(cum_optimal)
        
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, favorite_profit, label='Bet on Favorite', color='#3498db')
        plt.plot(timestamps, underdog_profit, label='Bet on Underdog', color='#e74c3c')
        plt.plot(timestamps, optimal_profit, label='Optimal Strategy', color='#2ecc71', linewidth=2)
        
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.xlabel('Time')
        plt.ylabel('Cumulative Profit ($)')
        plt.title(f'Session Betting Strategy Profit')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()


def main():
    """Run betting analytics as standalone script"""
    parser = argparse.ArgumentParser(description='DuelSim Betting Analytics')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate analytics report')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset analytics data')
    reset_parser.add_argument('--keep-sessions', action='store_true', 
                             help='Keep session data when resetting')
    
    # Session commands
    session_parser = subparsers.add_parser('session', help='Session management')
    session_subparsers = session_parser.add_subparsers(dest='session_command', help='Session command')
    
    # Start new session
    start_parser = session_subparsers.add_parser('start', help='Start a new session')
    start_parser.add_argument('--name', help='Custom session name')
    
    # End session
    end_parser = session_subparsers.add_parser('end', help='End current session')
    
    # List sessions
    list_parser = session_subparsers.add_parser('list', help='List all sessions')
    
    # Report session
    report_session_parser = session_subparsers.add_parser('report', help='Generate report for a session')
    report_session_parser.add_argument('session_id', help='Session ID to report on')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create analytics object
    analytics = BettingAnalytics()
    
    # Process commands
    if args.command == 'report':
        report_file = analytics.generate_report()
        if report_file:
            print(f"Report generated: {report_file}")
        else:
            print("No data available for report generation.")
    
    elif args.command == 'reset':
        analytics.reset_analytics(keep_sessions=args.keep_sessions)
    
    elif args.command == 'session':
        if args.session_command == 'start':
            analytics.start_new_session(args.name)
        
        elif args.session_command == 'end':
            analytics.end_session()
        
        elif args.session_command == 'list':
            analytics.list_sessions()
        
        elif args.session_command == 'report':
            report_file = analytics.generate_session_report(args.session_id)
            if report_file:
                print(f"Session report generated: {report_file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 