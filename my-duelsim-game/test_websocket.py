# test_websocket.py
import json
import time
import threading
import argparse
from websocket_server import WebSocketServer

def main():
    parser = argparse.ArgumentParser(description='Test WebSocket server')
    parser.add_argument('--port', type=int, default=5556, help='WebSocket server port')
    args = parser.parse_args()
    
    # Create WebSocket server
    ws_server = WebSocketServer(port=args.port)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=ws_server.start)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"WebSocket server running on port {args.port}")
    print("Open websocket_debug.html in your browser to connect")
    
    # Wait for server to start
    time.sleep(1)
    
    # Sample battle data
    battle_data = {
        "players": [
            {
                "name": "Fighter1",
                "hp": 99,
                "max_hp": 99,
                "position": [2, 2]
            },
            {
                "name": "Fighter2",
                "hp": 99,
                "max_hp": 99,
                "position": [3, 2]
            }
        ],
        "arena_size": {"width": 5, "height": 5}
    }
    
    # Set battle data
    ws_server.set_battle_data(battle_data)
    
    try:
        tick = 0
        while True:
            # Wait for user input
            cmd = input("Enter command (info/attack/damage/end/quit): ")
            
            if cmd == "quit":
                break
            
            if cmd == "info":
                # Send battle info again
                ws_server.set_battle_data(battle_data)
                print("Sent battle info")
            
            elif cmd == "attack":
                # Send a sample attack event
                tick += 1
                event = {
                    "type": "attack",
                    "actor": "Fighter1",
                    "target": "Fighter2",
                    "tick": tick,
                    "message": f"Fighter1 attacks Fighter2!"
                }
                ws_server.add_event(event)
                print(f"Sent attack event at tick {tick}")
                
            elif cmd == "damage":
                # Send a damage event
                tick += 1
                event = {
                    "type": "damage",
                    "target": "Fighter2",
                    "damage": 10,
                    "tick": tick,
                    "message": f"Fighter2 takes 10 damage!"
                }
                ws_server.add_event(event)
                
                # Update battle data
                battle_data["players"][1]["hp"] -= 10
                ws_server.set_battle_data(battle_data)
                
                print(f"Sent damage event at tick {tick}")
                
            elif cmd == "end":
                # Send battle end event
                ws_server.broadcast(json.dumps({
                    "type": "battle_end",
                    "data": {
                        "winner": "Fighter1",
                        "tick": tick
                    }
                }))
                print("Sent battle end event")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    # Close server
    ws_server.stop()

if __name__ == "__main__":
    main()