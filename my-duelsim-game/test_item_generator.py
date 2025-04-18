"""
Test script for the item generator
"""
import os
import sys
import traceback
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

print(f"{Fore.GREEN}=== Item Generator Test Script ==={Style.RESET_ALL}")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print(f"{Fore.CYAN}Importing simple_item_generator...{Style.RESET_ALL}")
    from duelsim.items.simple_item_generator import generate_items, save_items_to_json
    
    # Generate a small number of items first as a test
    print(f"{Fore.CYAN}Generating 10 test items...{Style.RESET_ALL}")
    test_items = generate_items(10)
    
    if test_items:
        print(f"{Fore.GREEN}Successfully generated {len(test_items)} test items{Style.RESET_ALL}")
        
        # Save test items
        test_filename = save_items_to_json(test_items, "test_items.json")
        if test_filename:
            print(f"{Fore.GREEN}Test items saved to {test_filename}{Style.RESET_ALL}")
            
            # If test was successful, generate the full set
            print(f"{Fore.CYAN}Now generating 1337 items...{Style.RESET_ALL}")
            items = generate_items(1337)
            
            if items:
                print(f"{Fore.GREEN}Successfully generated {len(items)} items{Style.RESET_ALL}")
                
                # Save to JSON
                filename = save_items_to_json(items)
                if filename:
                    print(f"{Fore.GREEN}Items saved to {filename}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}Item generation completed successfully!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Failed to save items to file{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to generate 1337 items{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to save test items to file{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to generate test items{Style.RESET_ALL}")
        
except ImportError as e:
    print(f"{Fore.RED}Error importing item generator: {e}{Style.RESET_ALL}")
    traceback.print_exc()
except Exception as e:
    print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
    traceback.print_exc()

print(f"{Fore.GREEN}=== Test Script Completed ==={Style.RESET_ALL}") 