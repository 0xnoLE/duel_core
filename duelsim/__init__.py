"""
DuelSim - A turn-based duel simulation engine
"""

__version__ = "0.1.0"

# Import key components for easy access
from duelsim.entities.player import Player
from duelsim.engine.rules import RuleSet
from duelsim.engine.tick_manager import TickManager
from duelsim.ai.basic_agent import BasicAgent
from duelsim.utils.visualizer import DuelVisualizer

# Import main simulation function
from duelsim.main import run_duel_simulation, load_rules 