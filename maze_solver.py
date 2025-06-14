import random
import numpy as np
from collections import deque
import matplotlib.pyplot as plt

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze = np.ones((height, width), dtype=int)  # 1 represents walls
        self.start = None
        self.end = None
        
    def generate_maze(self):
        # Initialize with all walls
        self.maze.fill(1)
        
        # Start from a random cell
        start_x = random.randint(0, self.width-1)
        start_y = random.randint(0, self.height-1)
        self.maze[start_y, start_x] = 0  # 0 represents path
        
        # Use DFS to generate the maze
        stack = [(start_x, start_y)]
        while stack:
            x, y = stack[-1]
            # Get unvisited neighbors
            neighbors = []
            for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.maze[ny, nx] == 1):
                    neighbors.append((nx, ny))
            
            if neighbors:
                # Choose a random neighbor
                nx, ny = random.choice(neighbors)
                # Remove wall between current cell and chosen neighbor
                self.maze[(y + ny) // 2, (x + nx) // 2] = 0
                self.maze[ny, nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()
        
        # Set start and end points
        self.start = (0, 0)
        self.end = (self.width-1, self.height-1)
        self.maze[self.start[1], self.start[0]] = 0
        self.maze[self.end[1], self.end[0]] = 0
    
    def solve_maze(self):
        if not self.start or not self.end:
            raise ValueError("Maze must be generated before solving")
        
        # Use BFS to find the shortest path
        queue = deque([(self.start, [self.start])])
        visited = {self.start}
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == self.end:
                return path
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.maze[ny, nx] == 0 and (nx, ny) not in visited):
                    queue.append(((nx, ny), path + [(nx, ny)]))
                    visited.add((nx, ny))
        
        return None  # No path found
    
    def visualize(self, path=None):
        plt.figure(figsize=(10, 10))
        plt.imshow(self.maze, cmap='binary')
        
        if path:
            path_x = [x for x, y in path]
            path_y = [y for x, y in path]
            plt.plot(path_x, path_y, 'r-', linewidth=2)
        
        plt.plot(self.start[0], self.start[1], 'go', markersize=10)  # Start in green
        plt.plot(self.end[0], self.end[1], 'ro', markersize=10)      # End in red
        plt.axis('off')
        plt.show()

def main():
    # Create and generate a maze
    maze = Maze(20, 20)
    maze.generate_maze()
    
    # Solve the maze
    path = maze.solve_maze()
    
    # Visualize the maze and solution
    maze.visualize(path)
    
    if path:
        print(f"Path found! Length: {len(path)}")
    else:
        print("No path found!")

if __name__ == "__main__":
    main() 