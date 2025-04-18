"""
Standalone script to generate items_1337.json
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the simple item generator
    from duelsim.items.simple_item_generator import generate_items, save_items_to_json
    
    print("Generating 1337 items...")
    items = generate_items(1337)
    
    filename = save_items_to_json(items)
    print(f"Items saved to {filename}")
    
    print(f"Total items generated: {len(items)}")
    
except ImportError as e:
    print(f"Error importing item generator: {e}")
except Exception as e:
    print(f"Error generating items: {e}")