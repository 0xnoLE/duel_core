class DuelVisualizer:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        
    def render_arena(self, players):
        """Render a simple ASCII representation of the arena"""
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Place players on grid
        for i, player in enumerate(players):
            x, y = player.position
            if 0 <= x < self.width and 0 <= y < self.height:
                grid[y][x] = str(i+1)  # Player 1 or Player 2
        
        # Print the grid with border
        print("+" + "-" * self.width + "+")
        for row in grid:
            print("|" + "".join(row) + "|")
        print("+" + "-" * self.width + "+")
        
        # Print player stats
        for i, player in enumerate(players):
            print(f"Player {i+1}: HP={player.hp}/{player.max_hp} | Cooldown={player.cooldown}") 