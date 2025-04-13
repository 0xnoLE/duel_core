"""
DuelSim Crypto Integration Prototype

This module demonstrates how cryptocurrency and blockchain technology 
could be integrated into DuelSim.
"""

from web3 import Web3
import json
import os
import time
from datetime import datetime

class CryptoIntegration:
    def __init__(self, provider_url=None, contract_address=None):
        """Initialize the crypto integration module"""
        # Use default provider if none specified (for demo purposes)
        if provider_url is None:
            # For demonstration, we'll use a public Ethereum testnet node
            # In production, you would use your own node or a service like Infura
            provider_url = "https://goerli.infura.io/v3/your-infura-key"
        
        # Connect to the blockchain
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Check connection
        self.connected = self.web3.isConnected()
        if not self.connected:
            print("Warning: Could not connect to blockchain provider")
        
        # Load smart contract ABI (Application Binary Interface)
        self.betting_contract = None
        self.nft_contract = None
        
        if contract_address and self.connected:
            try:
                # Load ABI from file (would be included in a real implementation)
                with open("contracts/betting_abi.json", "r") as f:
                    betting_abi = json.load(f)
                
                # Create contract instance
                self.betting_contract = self.web3.eth.contract(
                    address=contract_address,
                    abi=betting_abi
                )
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load contract ABI: {e}")
    
    def connect_wallet(self, wallet_address):
        """Connect a user's wallet to the system"""
        if not self.connected:
            return {"success": False, "error": "Blockchain provider not connected"}
        
        if self.web3.isAddress(wallet_address):
            # In a real implementation, we would verify ownership
            # through a signature or similar mechanism
            return {
                "success": True, 
                "address": wallet_address,
                "balance": self.web3.eth.get_balance(wallet_address)
            }
        return {"success": False, "error": "Invalid wallet address"}
    
    def place_bet(self, wallet_address, fighter_id, amount, token="ETH"):
        """Place a bet on a fighter"""
        if not self.connected:
            return {"success": False, "error": "Blockchain provider not connected"}
        
        if not self.betting_contract:
            # For demo purposes, simulate a successful bet
            return {
                "success": True,
                "bet_id": f"bet_{int(time.time())}",
                "fighter_id": fighter_id,
                "amount": amount,
                "token": token,
                "timestamp": datetime.now().isoformat(),
                "status": "pending"
            }
        
        # In a real implementation, this would call the smart contract
        try:
            # Example of how this might work with a real contract
            tx_hash = self.betting_contract.functions.placeBet(
                fighter_id
            ).transact({
                'from': wallet_address,
                'value': self.web3.toWei(amount, 'ether')
            })
            
            # Wait for transaction to be mined
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "success": True,
                "bet_id": tx_hash.hex(),
                "fighter_id": fighter_id,
                "amount": amount,
                "token": token,
                "timestamp": datetime.now().isoformat(),
                "status": "confirmed" if tx_receipt.status == 1 else "failed",
                "transaction": tx_receipt
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def mint_fighter_nft(self, wallet_address, fighter_data):
        """Mint a new fighter as an NFT"""
        if not self.connected:
            return {"success": False, "error": "Blockchain provider not connected"}
        
        # For demo purposes, simulate a successful NFT minting
        fighter_id = f"fighter_{int(time.time())}"
        
        return {
            "success": True,
            "fighter_id": fighter_id,
            "owner": wallet_address,
            "metadata": fighter_data,
            "timestamp": datetime.now().isoformat(),
            "token_uri": f"https://duelsim.example/api/fighters/{fighter_id}"
        }
    
    def record_battle_result(self, battle_data):
        """Record battle result on the blockchain"""
        if not self.connected:
            return {"success": False, "error": "Blockchain provider not connected"}
        
        # For demo purposes, simulate recording the battle result
        battle_id = f"battle_{int(time.time())}"
        
        # In a real implementation, this would store a hash of the battle data
        # on-chain for verification purposes
        
        return {
            "success": True,
            "battle_id": battle_id,
            "timestamp": datetime.now().isoformat(),
            "data_hash": Web3.keccak(text=json.dumps(battle_data)).hex(),
            "status": "recorded"
        }
    
    def get_fighter_history(self, fighter_id):
        """Get the battle history of a fighter from the blockchain"""
        if not self.connected:
            return {"success": False, "error": "Blockchain provider not connected"}
        
        # For demo purposes, generate some fake battle history
        battles = []
        for i in range(5):
            battles.append({
                "battle_id": f"battle_{int(time.time()) - i*86400}",
                "opponent": f"fighter_{int(time.time()) - i*100}",
                "result": "win" if i % 2 == 0 else "loss",
                "timestamp": datetime.fromtimestamp(time.time() - i*86400).isoformat()
            })
        
        return {
            "success": True,
            "fighter_id": fighter_id,
            "battles": battles,
            "stats": {
                "wins": sum(1 for b in battles if b["result"] == "win"),
                "losses": sum(1 for b in battles if b["result"] == "loss"),
                "total_battles": len(battles)
            }
        }

def demo():
    """Run a demonstration of the crypto integration"""
    print("DuelSim Crypto Integration Demo")
    print("===============================\n")
    
    # Initialize the integration
    crypto = CryptoIntegration()
    
    # Check connection
    if not crypto.connected:
        print("Could not connect to blockchain. Running in simulation mode.\n")
    
    # Demo wallet connection
    wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Example wallet address
    wallet_result = crypto.connect_wallet(wallet)
    
    if wallet_result["success"]:
        print(f"Connected wallet: {wallet_result['address']}")
        if "balance" in wallet_result:
            balance_eth = crypto.web3.fromWei(wallet_result["balance"], "ether")
            print(f"Wallet balance: {balance_eth} ETH\n")
    else:
        print(f"Failed to connect wallet: {wallet_result['error']}\n")
    
    # Demo placing a bet
    bet_result = crypto.place_bet(wallet, "fighter_123", 0.1)
    
    if bet_result["success"]:
        print(f"Bet placed successfully!")
        print(f"Bet ID: {bet_result['bet_id']}")
        print(f"Fighter: {bet_result['fighter_id']}")
        print(f"Amount: {bet_result['amount']} {bet_result['token']}")
        print(f"Status: {bet_result['status']}\n")
    else:
        print(f"Failed to place bet: {bet_result['error']}\n")
    
    # Demo minting a fighter NFT
    fighter_data = {
        "name": "CryptoChampion",
        "attributes": {
            "strength": 85,
            "defense": 70,
            "speed": 90,
            "special_moves": ["Blockchain Bash", "Crypto Crush"]
        },
        "appearance": {
            "color": "#00ff00",
            "weapon": "Digital Daggers"
        }
    }
    
    nft_result = crypto.mint_fighter_nft(wallet, fighter_data)
    
    if nft_result["success"]:
        print(f"Fighter NFT minted successfully!")
        print(f"Fighter ID: {nft_result['fighter_id']}")
        print(f"Owner: {nft_result['owner']}")
        print(f"Token URI: {nft_result['token_uri']}\n")
    else:
        print(f"Failed to mint fighter NFT: {nft_result['error']}\n")
    
    # Demo recording a battle result
    battle_data = {
        "fighters": ["fighter_123", "fighter_456"],
        "winner": "fighter_123",
        "rounds": 5,
        "moves": 27,
        "critical_hits": 3,
        "timestamp": datetime.now().isoformat()
    }
    
    record_result = crypto.record_battle_result(battle_data)
    
    if record_result["success"]:
        print(f"Battle result recorded successfully!")
        print(f"Battle ID: {record_result['battle_id']}")
        print(f"Data Hash: {record_result['data_hash']}")
        print(f"Status: {record_result['status']}\n")
    else:
        print(f"Failed to record battle result: {record_result['error']}\n")
    
    # Demo getting fighter history
    history_result = crypto.get_fighter_history("fighter_123")
    
    if history_result["success"]:
        print(f"Fighter History for {history_result['fighter_id']}:")
        print(f"Total Battles: {history_result['stats']['total_battles']}")
        print(f"Wins: {history_result['stats']['wins']}")
        print(f"Losses: {history_result['stats']['losses']}")
        print("\nRecent Battles:")
        
        for battle in history_result["battles"]:
            print(f"  - {battle['timestamp']}: {battle['result'].upper()} against {battle['opponent']}")
    else:
        print(f"Failed to get fighter history: {history_result['error']}\n")

if __name__ == "__main__":
    demo() 