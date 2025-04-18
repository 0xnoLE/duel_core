



# DuelSim: Tick-Based Combat Simulator

This document outlines the core architecture of our tick-based combat simulator that recreates the fundamental mechanics of OSRS-style PvP combat.

## 🧠 Core Concept: "Tick-Muscle" Simulation

At its heart, **our combat system is deterministic and tick-based**:
- One game tick = 600ms (configurable for testing)
- All inputs, damage, animations, etc. are aligned to this global rhythm
- Players respond to time-pressure and ruleset-induced logic states

## 🧩 System Architecture

### 1. **Tick Scheduler (Global Loop)**
```python
TICK_DURATION_MS = 600
tick = 0
while duel_active:
    tick += 1
    for player in duel_players:
        process_actions(player, tick)
    update_game_state()
    broadcast_events()
    sleep(TICK_DURATION_MS)
```

### 2. **Action Queue**
Each player has a queue of actions:
```python
player.action_queue = [
    {"type": "attack", "target": other_player, "execute_on": tick+4},
    {"type": "move", "destination": (x, y), "execute_on": tick+1},
]
```
- Queue is **non-preemptive** unless specific interrupts (e.g., stun, death)
- Actions are processed at their scheduled tick

### 3. **Combat Logic**
```python
def resolve_attack(attacker, defender):
    if attacker.cooldown == 0:
        accuracy_roll = rng()
        damage = calculate_max_hit(attacker) if accuracy_roll else 0
        defender.hp -= damage
        attacker.cooldown = attacker.weapon_speed  # e.g., 4 ticks for whip
        
        # Broadcast event to spectators
        broadcast_event({
            "type": "attack",
            "actor": attacker.name,
            "target": defender.name,
            "damage": damage,
            "tick": current_tick
        })
```

### 4. **Rule System**
```python
rules = {
    "allow_melee": True,
    "allow_ranged": False,
    "allow_magic": False,
    "no_food": True,
    "no_movement": False,
    "lock_slots": {"head": True, "weapon": False}
}
```

### 5. **Input System**
```python
if player.next_action is None:
    available_actions = get_legal_actions(player, game_state, rules)
    player.next_action = player_controller.decide_action(available_actions)
```

## 🌐 WebSocket Integration

Our system broadcasts events to spectators via WebSocket:

```python
def broadcast_event(event):
    """Broadcast an event to all connected spectators"""
    message = {
        "type": "event",
        "data": event
    }
    websocket_server.broadcast(json.dumps(message))
```

Events include:
- Battle start/end
- Player attacks
- Damage dealt
- Player movement
- Special attacks

## 🖥️ Web Client

The web client connects to the WebSocket server and:
1. Receives battle information
2. Displays player stats and positions
3. Animates attacks and damage
4. Shows battle log

## 🧪 Testing Tools

We've implemented several testing tools:
- `test_websocket.py`: Manual testing of WebSocket events
- `debug_system.py`: End-to-end testing of the entire system
- `websocket_debug.html`: Browser-based WebSocket debugging

## 🚀 Future Enhancements

1. **Player Input**: Allow real players to control fighters
2. **Enhanced Rules**: More complex rule sets and combat mechanics
3. **AI Agents**: Smarter AI with different fighting styles
4. **Betting System**: Integrated betting for spectators
5. **Tournament Mode**: Automated tournaments with multiple fighters
