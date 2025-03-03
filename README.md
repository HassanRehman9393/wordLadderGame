# Word Ladder Game 🎮

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)

A modern, interactive educational game that demonstrates classic search algorithms through word transformation puzzles.

<p align="center">
  <img src="screenshots/game_screenshot.png" alt="Word Ladder Game Screenshot" width="600">
</p>

## 📖 Overview

Word Ladder is a classic word game invented by Lewis Carroll, where players transform one word into another by changing only one letter at a time, with each intermediate step forming a valid English word. This implementation features an AI-powered solution finder using three different search algorithms:

- **Breadth-First Search (BFS)**
- **A* Search** 
- **Uniform Cost Search (UCS)**

The game showcases how different algorithms explore the same problem space with varying efficiency and approaches.

## ✨ Features

### Core Gameplay
- Transform words by changing one letter at a time
- Validate moves against a dictionary of 148,000+ English words
- Multiple difficulty levels (Beginner, Advanced, Challenge)
- Interactive graph visualization showing word connections
- Algorithm comparison with detailed metrics

### Educational Components
- Visual representation of algorithm exploration patterns
- Detailed explanation of g(n), h(n), and f(n) functions
- Performance metrics display for each algorithm
- Interactive graphs showing algorithm traversal paths

### Advanced Features
- Challenge mode with banned letters and words
- Custom word ladder creation
- Game statistics tracking
- Hint system with algorithm choice
- Celebration animations on puzzle completion

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher

### Installation Steps
```bash
# Clone this repository
git clone https://github.com/yourusername/wordLadderGame.git
cd wordLadderGame

# Create a requirements.txt file with the following content:
# networkx==2.8.8
# matplotlib==3.6.2
# customtkinter==5.1.2
# pillow==9.3.0
# numpy==1.23.5
# ttkthemes==3.2.2
# tk==0.1.0

# Install required packages
pip install -r requirements.txt
```

If you don't have a requirements.txt file yet, create one with the following content:

```
networkx==2.8.8
matplotlib==3.6.2
customtkinter==5.1.2
pillow==9.3.0
numpy==1.23.5
ttkthemes==3.2.2
tk==0.1.0
```

### Required Libraries
The game relies on several external libraries:

- **NetworkX**: For graph creation and manipulation
- **Matplotlib**: For graph visualization and plotting
- **CustomTkinter**: For the modern UI elements and dark theme
- **Pillow (PIL)**: For image processing (used by CustomTkinter)
- **NumPy**: For numerical operations (used by Matplotlib)
- **ttkthemes**: For additional UI themes
- **tk**: For core GUI functionality

**Note**: The exact version numbers may vary, but these are the recommended versions that have been tested with the game.

## 🎮 How to Play

```bash
# Start the game with GUI
python ui_game.py

# Or use the console version
python main.py
```

### Game Rules:
1. Enter a starting word and target word of the same length
2. Change one letter at a time to form a new valid word
3. Continue until you transform your word into the target word
4. Try to complete the transformation in the minimum number of steps

## 🧠 Algorithm Implementation

The game implements three classic search algorithms with different approaches:

### Breadth-First Search (BFS)
- Explores all neighbor words at the current depth before moving deeper
- **g(n)**: Path length (steps from start)
- **f(n) = g(n)**: Only considers path length
- **Optimal for**: Finding shortest paths when all edges have equal weight

### A* Search
- Uses a heuristic function to guide search toward the target
- **g(n)**: Path length (steps from start)
- **h(n)**: Number of differing letters from target
- **f(n) = g(n) + h(n)**: Balances path cost and estimated cost to goal
- **Optimal for**: Efficiently finding solutions for longer words

### Uniform Cost Search (UCS)
- Explores paths in order of increasing cost
- **g(n)**: Path cost (in this case, steps from start)
- **f(n) = g(n)**: Only considers path cost
- **Optimal for**: Finding least-cost paths when edges have different weights

## 🔍 Algorithm Comparison

<p align="center">
  <img src="screenshots/algorithm_comparison.png" alt="Algorithm Comparison" width="600">
</p>

The visual comparison shows how:
- BFS explores in "waves" outward from the start word
- A* focuses exploration toward the target using the heuristic
- UCS (with uniform costs) behaves similarly to BFS but orders exploration by cost

## 📊 Technical Implementation

### Word Management
- Filtered 370,000+ words to ~148,000 words (3-8 letters)
- Optimized storage with pickle serialization
- Efficient loading with length-based indexing
- Cached word transformations for better performance

### Search Implementation
- Timeout mechanisms to prevent long-running searches
- Iteration limits for search safety
- Optimized neighbor generation by only considering valid letter replacements
- Dynamic sub-graph creation for efficient visualization

### Visualization
- NetworkX for graph structure
- Matplotlib for interactive visualization
- Custom node and edge styling
- Path animation capabilities

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/wordLadderGame/issues).

## 📝 License

This project is [MIT](LICENSE) licensed.

## 🙏 Acknowledgements

- Lewis Carroll for inventing the Word Ladder game concept
- NetworkX and Matplotlib for visualization capabilities
- The extensive English dictionary that makes the game possible

---

*Created as part of a course project on Artificial Intelligence and Search Algorithms*
 
