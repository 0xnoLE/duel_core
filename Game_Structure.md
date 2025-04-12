Perfect. If you’re focused on **rebuilding the "muscle"** of the Duel Arena — meaning **the logic engine that compels and governs player response** — then your goal is to reconstruct a tick-based combat simulator that *responds to rule inputs and produces pressure states* requiring real-time or strategic decisions.

Let’s break down how to **reconstruct this tick logic-based system**, step-by-step.

---

## 🧠 Core Concept: “Tick-Muscle” Simulation

At its heart, **OSRS combat is deterministic and tick-based**:
- One game tick = 600ms
- All inputs, damage, animations, etc. are aligned to this global rhythm
- Players respond not to *graphics*, but to **time-pressure and ruleset-induced logic states**

---

## 🧩 Layer Breakdown (For Simulation Engine)

### 1. **Tick Scheduler (Global Loop)**
```python
TICK_DURATION_MS = 600
tick = 0
while duel_active:
    tick += 1
    for player in duel_players:
        process_actions(player, tick)
    update_game_state()
    sleep(TICK_DURATION_MS)
```

---

### 2. **Action Queue**
Each player has a queue like:
```python
player.action_queue = [
    {"type": "attack", "target": other_player, "execute_on": tick+4},
    {"type": "move", "destination": (x, y), "execute_on": tick+1},
]
```
- Queue is **non-preemptive** unless specific interrupts (e.g., stun, death)
- You **only process actions at their scheduled tick**

---

### 3. **Combat Logic (Pressure Generator)**
```python
def resolve_attack(attacker, defender):
    if attacker.cooldown == 0:
        accuracy_roll = rng()
        damage = calculate_max_hit(attacker) if accuracy_roll else 0
        defender.hp -= damage
        attacker.cooldown = attacker.weapon_speed  # e.g., 4 ticks for whip
        log_event(f"{attacker.name} hits {damage} on {defender.name}")
```

- Pressure emerges when players **must choose to pre-load actions**:
  - Do I risk eating next tick or attack now?
  - Do I fake a movement delay?
  - Is spec ready?

---

### 4. **Rule Mask System**
A bitmask or boolean array that sets the environment:
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
- This restricts player *affordances*, which adjusts **input space** and creates **game-state tension**
- Example: `no_food=True` + `no_movement=True` = “pure damage trade" meta
- Obstacle logic can dynamically create route-find failures → time loss pressure

---

### 5. **Input Window (AI-Simulated or Real-Time)**
```python
if player.next_action is None:
    available_actions = get_legal_actions(player, game_state, rules)
    player.next_action = player_controller.decide_action(available_actions)
```

- Can simulate **“player brain”** using a decision engine
- In full version: plug in **RL agent**, scripted logic, or remote human input

---

## 🛠 Example: Tick Flow with Weapon Cooldowns

| Tick | Player A                 | Player B                 |
|------|--------------------------|--------------------------|
| 0    | Input: Attack → T+4      | Input: Move → T+1        |
| 1    | Movement executed        |                          |
| 2    |                          |                          |
| 3    |                          |                          |
| 4    | Attack resolves (hits 12)|                          |
| 5    | Cooldown (can’t act)     | Attack enqueued          |
| 6    |                          | Attack resolves (hits 6) |

This tick structure forces response to **cooldowns**, **spacing**, and **rule-induced constraints**.

---

## 🧠 Summary: What You’re Re-Creating
You're rebuilding:
- A tick-based **loop**
- A constrained **affordance matrix** (via rule set)
- A system that **forces players into time-sensitive choices**
- A reactive **muscle model** where player input is shaped by engine rhythm, not animation

---

Would you like:
- A C-Based framework with modular components to simulate a full duel?
- A config file to easily change rule sets and test resulting state tensions?
- Or a simplified prototype with dummy AI agents first?

Let's proceed.