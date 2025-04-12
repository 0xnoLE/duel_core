# DuelSim

A turn-based duel simulation engine written in Python.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/yourusername/duelsim.git

# Or install in development mode
git clone https://github.com/yourusername/duelsim.git
cd duelsim
pip install -e .
```

## Basic Usage

```python
from duelsim import run_duel_simulation

# Run a basic duel
result = run_duel_simulation()

# Print the winner
print(f"The winner is: {result['winner']}")
```

## Features

- Turn-based combat system
- Configurable rules and arena size
- AI agents with customizable behavior
- Visualization of the duel
- Extensible architecture

## Examples

See the `examples/` directory for usage examples:

- `basic_duel.py`: Simple duel with default settings
- `custom_rules.py`: Duel with custom rules and player stats
- `headless_simulation.py`: Running multiple simulations without visualization

## Custom Configuration

You can customize player stats and rules:

```python
# Custom rules
custom_rules = {
    "allow_melee": True,
    "allow_ranged": False,
    "allow_magic": False,
    "no_food": True,
    "arena_size": {"width": 7, "height": 7},
    "starting_positions": [[0, 0], [6, 6]]
}

# Custom player configurations
player1 = {
    "name": "Tank",
    "hp": 120,
    "attack": 70,
    "strength": 80,
    "defense": 80
}

player2 = {
    "name": "Striker",
    "hp": 80,
    "attack": 90,
    "strength": 90,
    "defense": 50
}

# Run with custom settings
result = run_duel_simulation(
    player1_config=player1,
    player2_config=player2,
    rules_config=custom_rules
)
```

## License

MIT
