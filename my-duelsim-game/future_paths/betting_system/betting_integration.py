"""
Betting System Integration for DuelSim

This module provides functionality for spectators to place bets on duels.
It integrates with the spectator mode and can work with both traditional
currency and cryptocurrency systems.
"""

import os
import time
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class BettingPool:
    """Manages a pool of bets for a duel"""
    
    def __init__(self, duel_id: str, player1_name: str, player2_name: str):
        """Initialize a betting pool for a specific duel"""
        self.duel_id = duel_id
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.bets = {
            player1_name: [],  # List of bets on player1
            player2_name: []   # List of bets on player2
        }
        self.total_pool = 0.0
        self.status = "open"  # open, locked, or settled
        self.winner = None
        self.created_at = datetime.now().isoformat()
        self.settled_at = None
        self.house_fee_percent = 5.0  # 5% house fee
    
    def place_bet(self, user_id: str, player_name: str, amount: float, 
                  currency: str = "credits") -> Dict[str, Any]:
        """Place a bet on a player"""
        if self.status != "open":
            return {
                "success": False,
                "error": f"Betting is {self.status}. No new bets accepted."
            }
        
        if player_name not in [self.player1_name, self.player2_name]:
            return {
                "success": False,
                "error": f"Unknown player: {player_name}"
            }
        
        if amount <= 0:
            return {
                "success": False,
                "error": "Bet amount must be greater than zero"
            }
        
        # Create bet record
        bet_id = str(uuid.uuid4())
        bet = {
            "id": bet_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "player": player_name,
            "timestamp": datetime.now().isoformat(),
            "status": "placed"
        }
        
        # Add to appropriate list
        self.bets[player_name].append(bet)
        self.total_pool += amount
        
        return {
            "success": True,
            "bet_id": bet_id,
            "player": player_name,
            "amount": amount,
            "currency": currency,
            "timestamp": bet["timestamp"]
        }
    
    def lock_betting(self) -> Dict[str, Any]:
        """Lock the betting pool (no more bets accepted)"""
        if self.status != "open":
            return {
                "success": False,
                "error": f"Betting is already {self.status}"
            }
        
        self.status = "locked"
        return {
            "success": True,
            "status": "locked",
            "total_pool": self.total_pool,
            "player1_bets": len(self.bets[self.player1_name]),
            "player2_bets": len(self.bets[self.player2_name])
        }
    
    def settle_bets(self, winner_name: str) -> Dict[str, Any]:
        """Settle all bets based on the winner"""
        if self.status != "locked":
            return {
                "success": False,
                "error": "Betting must be locked before settlement"
            }
        
        if winner_name not in [self.player1_name, self.player2_name]:
            return {
                "success": False,
                "error": f"Unknown winner: {winner_name}"
            }
        
        self.winner = winner_name
        self.status = "settled"
        self.settled_at = datetime.now().isoformat()
        
        # Calculate total bet amounts for each player
        total_winner_bets = sum(bet["amount"] for bet in self.bets[winner_name])
        total_loser_bets = sum(bet["amount"] for bet in self.bets[self.player1_name if winner_name == self.player2_name else self.player2_name])
        
        # Calculate house fee
        house_fee = self.total_pool * (self.house_fee_percent / 100)
        payout_pool = self.total_pool - house_fee
        
        # Calculate payouts for winning bets
        payouts = []
        if total_winner_bets > 0:  # Avoid division by zero
            for bet in self.bets[winner_name]:
                # Proportional share of the pool based on bet size
                share = bet["amount"] / total_winner_bets
                payout_amount = payout_pool * share
                
                payout = {
                    "bet_id": bet["id"],
                    "user_id": bet["user_id"],
                    "original_bet": bet["amount"],
                    "payout": payout_amount,
                    "profit": payout_amount - bet["amount"],
                    "currency": bet["currency"]
                }
                payouts.append(payout)
        
        return {
            "success": True,
            "status": "settled",
            "winner": winner_name,
            "total_pool": self.total_pool,
            "house_fee": house_fee,
            "payout_pool": payout_pool,
            "winning_bets": len(self.bets[winner_name]),
            "losing_bets": len(self.bets[self.player1_name if winner_name == self.player2_name else self.player2_name]),
            "payouts": payouts
        }
    
    def get_odds(self) -> Dict[str, Any]:
        """Calculate and return the current betting odds"""
        total_player1_bets = sum(bet["amount"] for bet in self.bets[self.player1_name])
        total_player2_bets = sum(bet["amount"] for bet in self.bets[self.player2_name])
        
        # Default odds if no bets
        player1_odds = 2.0
        player2_odds = 2.0
        
        # Calculate odds based on bet distribution
        if self.total_pool > 0:
            # Apply house edge to odds calculation
            adjusted_pool = self.total_pool * (1 - (self.house_fee_percent / 100))
            
            if total_player1_bets > 0:
                player1_odds = adjusted_pool / total_player1_bets
            if total_player2_bets > 0:
                player2_odds = adjusted_pool / total_player2_bets
        
        return {
            "player1": {
                "name": self.player1_name,
                "odds": round(player1_odds, 2),
                "total_bets": total_player1_bets,
                "bet_count": len(self.bets[self.player1_name])
            },
            "player2": {
                "name": self.player2_name,
                "odds": round(player2_odds, 2),
                "total_bets": total_player2_bets,
                "bet_count": len(self.bets[self.player2_name])
            },
            "total_pool": self.total_pool,
            "status": self.status
        }
    
    def get_user_bets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bets placed by a specific user"""
        user_bets = []
        
        for player_name, bets in self.bets.items():
            for bet in bets:
                if bet["user_id"] == user_id:
                    bet_info = bet.copy()
                    bet_info["duel_id"] = self.duel_id
                    user_bets.append(bet_info)
        
        return user_bets
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the betting pool to a dictionary for serialization"""
        return {
            "duel_id": self.duel_id,
            "player1_name": self.player1_name,
            "player2_name": self.player2_name,
            "bets": self.bets,
            "total_pool": self.total_pool,
            "status": self.status,
            "winner": self.winner,
            "created_at": self.created_at,
            "settled_at": self.settled_at,
            "house_fee_percent": self.house_fee_percent,
            "odds": self.get_odds()
        }

class BettingManager:
    """Manages betting pools for multiple duels"""
    
    def __init__(self, data_dir: str = "data/betting"):
        """Initialize the betting manager"""
        self.data_dir = data_dir
        self.active_pools = {}  # duel_id -> BettingPool
        self.user_balances = {}  # user_id -> balance
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing user balances
        self._load_user_balances()
    
    def _load_user_balances(self):
        """Load user balances from file"""
        balance_file = os.path.join(self.data_dir, "user_balances.json")
        try:
            if os.path.exists(balance_file):
                with open(balance_file, 'r') as f:
                    self.user_balances = json.load(f)
        except Exception as e:
            print(f"Error loading user balances: {e}")
    
    def _save_user_balances(self):
        """Save user balances to file"""
        balance_file = os.path.join(self.data_dir, "user_balances.json")
        try:
            with open(balance_file, 'w') as f:
                json.dump(self.user_balances, f, indent=2)
        except Exception as e:
            print(f"Error saving user balances: {e}")
    
    def create_betting_pool(self, duel_id: str, player1_name: str, player2_name: str) -> BettingPool:
        """Create a new betting pool for a duel"""
        if duel_id in self.active_pools:
            return self.active_pools[duel_id]
        
        pool = BettingPool(duel_id, player1_name, player2_name)
        self.active_pools[duel_id] = pool
        return pool
    
    def get_pool(self, duel_id: str) -> Optional[BettingPool]:
        """Get a betting pool by duel ID"""
        return self.active_pools.get(duel_id)
    
    def place_bet(self, duel_id: str, user_id: str, player_name: str, 
                  amount: float, currency: str = "credits") -> Dict[str, Any]:
        """Place a bet on a duel"""
        pool = self.get_pool(duel_id)
        if not pool:
            return {
                "success": False,
                "error": f"No betting pool found for duel {duel_id}"
            }
        
        # Check user balance
        user_balance = self.get_user_balance(user_id)
        if user_balance < amount:
            return {
                "success": False,
                "error": f"Insufficient balance. You have {user_balance} {currency}."
            }
        
        # Place the bet
        result = pool.place_bet(user_id, player_name, amount, currency)
        
        # If successful, deduct from user balance
        if result["success"]:
            self.update_user_balance(user_id, -amount)
        
        return result
    
    def settle_duel(self, duel_id: str, winner_name: str) -> Dict[str, Any]:
        """Settle bets for a completed duel"""
        pool = self.get_pool(duel_id)
        if not pool:
            return {
                "success": False,
                "error": f"No betting pool found for duel {duel_id}"
            }
        
        # Settle the bets
        result = pool.settle_bets(winner_name)
        
        # If successful, process payouts
        if result["success"]:
            for payout in result["payouts"]:
                self.update_user_balance(payout["user_id"], payout["payout"])
            
            # Save the settled pool
            self._save_pool(pool)
            
            # Remove from active pools
            del self.active_pools[duel_id]
        
        return result
    
    def _save_pool(self, pool: BettingPool):
        """Save a betting pool to file"""
        pool_file = os.path.join(self.data_dir, f"pool_{pool.duel_id}.json")
        try:
            with open(pool_file, 'w') as f:
                json.dump(pool.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving betting pool: {e}")
    
    def get_user_balance(self, user_id: str) -> float:
        """Get a user's balance"""
        return self.user_balances.get(user_id, 0.0)
    
    def update_user_balance(self, user_id: str, amount_change: float) -> float:
        """Update a user's balance"""
        current_balance = self.get_user_balance(user_id)
        new_balance = current_balance + amount_change
        
        # Ensure balance doesn't go negative
        new_balance = max(0.0, new_balance)
        
        self.user_balances[user_id] = new_balance
        self._save_user_balances()
        
        return new_balance
    
    def add_funds(self, user_id: str, amount: float) -> Dict[str, Any]:
        """Add funds to a user's account (e.g., from a purchase)"""
        if amount <= 0:
            return {
                "success": False,
                "error": "Amount must be greater than zero"
            }
        
        new_balance = self.update_user_balance(user_id, amount)
        
        return {
            "success": True,
            "user_id": user_id,
            "amount_added": amount,
            "new_balance": new_balance
        }
    
    def get_user_bets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bets placed by a user across all pools"""
        user_bets = []
        
        for duel_id, pool in self.active_pools.items():
            user_bets.extend(pool.get_user_bets(user_id))
        
        return user_bets
    
    def get_all_pools(self) -> Dict[str, Dict[str, Any]]:
        """Get all active betting pools"""
        return {duel_id: pool.to_dict() for duel_id, pool in self.active_pools.items()}

# Integration with spectator mode
class BettingSpectatorIntegration:
    """Integrates betting functionality with the spectator mode"""
    
    def __init__(self, spectator_server, betting_manager=None):
        """Initialize the integration"""
        self.spectator_server = spectator_server
        self.betting_manager = betting_manager or BettingManager()
        self.current_duel_id = None
        self.current_pool = None
    
    def start_duel(self, duel_id: str, player1_name: str, player2_name: str):
        """Start a new duel with betting"""
        self.current_duel_id = duel_id
        self.current_pool = self.betting_manager.create_betting_pool(
            duel_id, player1_name, player2_name
        )
        
        # Broadcast betting pool creation to spectators
        self.spectator_server.broadcast(json.dumps({
            'type': 'betting_pool_created',
            'data': {
                'duel_id': duel_id,
                'player1': player1_name,
                'player2': player2_name,
                'status': 'open',
                'odds': self.current_pool.get_odds()
            }
        }))
    
    def process_betting_command(self, client_socket, user_id: str, command: str, args: List[str]):
        """Process a betting command from a spectator"""
        if not self.current_pool:
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_error',
                'data': {'message': 'No active betting pool'}
            }))
            return
        
        if command == 'bet':
            # Format: /bet <player_name> <amount>
            if len(args) != 2:
                self._send_to_client(client_socket, json.dumps({
                    'type': 'betting_error',
                    'data': {'message': 'Usage: /bet <player_name> <amount>'}
                }))
                return
            
            player_name = args[0]
            try:
                amount = float(args[1])
            except ValueError:
                self._send_to_client(client_socket, json.dumps({
                    'type': 'betting_error',
                    'data': {'message': 'Amount must be a number'}
                }))
                return
            
            # Place the bet
            result = self.betting_manager.place_bet(
                self.current_duel_id, user_id, player_name, amount
            )
            
            # Send result to client
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_result',
                'data': result
            }))
            
            # If successful, broadcast updated odds
            if result["success"]:
                self.spectator_server.broadcast(json.dumps({
                    'type': 'betting_odds_update',
                    'data': self.current_pool.get_odds()
                }))
        
        elif command == 'odds':
            # Get current odds
            odds = self.current_pool.get_odds()
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_odds',
                'data': odds
            }))
        
        elif command == 'balance':
            # Get user balance
            balance = self.betting_manager.get_user_balance(user_id)
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_balance',
                'data': {'user_id': user_id, 'balance': balance}
            }))
        
        elif command == 'mybets':
            # Get user's bets
            bets = self.betting_manager.get_user_bets(user_id)
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_user_bets',
                'data': {'user_id': user_id, 'bets': bets}
            }))
        
        else:
            self._send_to_client(client_socket, json.dumps({
                'type': 'betting_error',
                'data': {'message': f'Unknown betting command: {command}'}
            }))
    
    def lock_betting(self):
        """Lock betting when the duel starts"""
        if self.current_pool:
            result = self.current_pool.lock_betting()
            
            # Broadcast betting locked
            self.spectator_server.broadcast(json.dumps({
                'type': 'betting_locked',
                'data': result
            }))
    
    def settle_duel(self, winner_name: str):
        """Settle bets when the duel ends"""
        if self.current_pool and self.current_duel_id:
            result = self.betting_manager.settle_duel(self.current_duel_id, winner_name)
            
            # Broadcast settlement results
            self.spectator_server.broadcast(json.dumps({
                'type': 'betting_settled',
                'data': result
            }))
            
            # Clear current duel
            self.current_duel_id = None
            self.current_pool = None
    
    def _send_to_client(self, client_socket, message):
        """Send a message to a specific client"""
        try:
            client_socket.send((message + '\n').encode('utf-8'))
        except Exception as e:
            print(f"Error sending to client: {e}") 