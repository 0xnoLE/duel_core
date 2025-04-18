import websocket
import json
import time

def on_message(ws, message):
    print(f"Received: {message}")
    try:
        data = json.loads(message)
        print(f"Message type: {data.get('type')}")
    except:
        print("Not JSON data")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connection opened")

if __name__ == "__main__":
    # Connect to the WebSocket server
    ws = websocket.WebSocketApp("ws://localhost:5556",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever() 