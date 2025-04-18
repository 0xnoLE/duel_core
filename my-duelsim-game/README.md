# DuelSim - Turn-based Duel Simulation Engine

![DuelSim Banner](https://via.placeholder.com/800x200/0073CF/FFFFFF?text=DuelSim)

DuelSim is a turn-based combat simulation engine that creates exciting duels between two fighters. With rich narrative, randomized combat outcomes, and colorful visualizations, it's perfect for creating engaging battle simulations.

## ✨ Features

- **Turn-based Combat System**: Strategic combat with movement, attacks, and special moves
- **Rich Narrative**: Detailed battle descriptions with varied combat narration
- **Randomized Outcomes**: Each battle is unique with critical hits, dodges, and special events
- **Enhanced Visualization**: Colorful terminal-based battle visualization with ASCII art
- **Detailed Statistics**: Comprehensive battle statistics and reports
- **Anime-style Victory Screens**: Fun victory/defeat screens with ASCII emoticons
- **Multiple Simulation Modes**: Run single battles or tournament-style multiple simulations

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Colorama (`pip install colorama`)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/duelsim.git
   cd duelsim
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run a sample duel:
   ```
   python master_duel.py
   ```

## 🎮 Usage

### Running a Basic Duel

The simplest way to run a duel is with the master script:

```
python master_duel.py
```

This will:
1. Run a simulation between two fighters
2. Generate a detailed report
3. Show an enhanced visual replay of the battle

### Command Line Options

```
python master_duel.py --help
```

Available options:
- `--speed <seconds>`: Adjust replay speed (default: 0.3)
- `--config <filename>`: Use a custom configuration file
- `--no-report`: Skip generating a report
- `--no-enhanced-visuals`: Skip the visual replay

### Running Multiple Simulations

To run multiple simulations and generate statistics:

```
python run_custom_game.py -n 10
```

This will run 10 simulations and generate a summary report.

### Customizing Fighters

Edit the player configurations in `run_custom_game.py` or `master_duel.py`:

```python
player1_config = {
    "name": "YourFighter",
    "hp": 100,
    "attack": 85,
    "strength": 80,
    "defense": 70
}
```

## 📊 Battle Reports

After each battle, DuelSim generates detailed reports in the `reports/` directory. These include:

- Winner and battle duration
- Damage statistics
- Movement patterns
- Critical hit rates
- Turn-by-turn narrative

## 🎨 Visualization

DuelSim offers two visualization modes:

1. **Basic Visualization**: Simple text-based arena display
2. **Enhanced Visualization**: Colorful terminal graphics with:
   - Color-coded health bars
   - ASCII battle effects
   - Animated attacks and special moves
   - Victory celebrations with anime-style emoticons

## 🛠️ Customization

### Custom Rules

Create a `custom_config.json` file to customize:
- Arena size
- Starting positions
- Combat mechanics
- Special move probabilities

Example:
```json
{
  "arena_size": {
    "width": 7,
    "height": 7
  },
  "starting_positions": [[0, 0], [6, 6]]
}
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by classic turn-based combat systems
- ASCII art and emoticons from various sources

---

Made with ❤️ by 0xEC