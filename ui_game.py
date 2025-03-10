import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from word_loader import load_words_from_pickle, get_words_by_length
from word_graph import bfs_shortest_path, a_star_search, ucs_shortest_path, get_valid_transformations, is_valid_transformation, get_word_neighbors, optimized_bfs
import random
from PIL import Image, ImageTk
import os
from matplotlib.animation import FuncAnimation
import heapq
from collections import deque

# Load words
word_list = load_words_from_pickle()
word_graph = nx.Graph()

# Setup Main Game Window
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

root = ctk.CTk()
root.title("Word Ladder Adventure")
root.geometry("1200x700")  # Larger window for two-panel layout
root.resizable(True, True)

# Game Variables
current_word = tk.StringVar()
target_word = tk.StringVar()
game_mode = tk.StringVar(value="Beginner")
moves = 0
banned_letters = []
banned_words = []
graph_canvas = None
current_figure = None
word_path = []  # Initialize this with the game variables

# Game Modes with improved word pair selections
GAME_MODES = {
    "Beginner": [
        ("cat", "dog"),     # Simple 3-letter transformation
        ("sun", "fun"),     # Simple 3-letter change
        ("bat", "hat"),     # Easy single-letter change 
        ("cold", "warm"),   # Interesting conceptual opposite
        ("ship", "slip"),   # One-letter adjustment
        ("hill", "mill")    # Simple change of first letter
    ],
    
    "Advanced": [
        ("stone", "money"),    # Longer, requires multiple steps
        ("water", "flame"),    # Conceptual opposites, tricky path
        ("cloud", "storm"),    # Weather-related, complex path
        ("brake", "train"),    # Transportation theme, longer path
        ("heart", "brain"),    # Body parts, challenging transformation
        ("sword", "peace")     # Conceptual contrast, longer path
    ],
    
    "Challenge": [
        ("magic", "power"),    # Mystical theme with banned letters
        ("smoke", "blaze"),    # Fire-related with banned letters
        ("beach", "waves"),    # Ocean theme with constraints
        ("night", "light"),    # Opposites with banned letters
        ("ghost", "witch"),    # Spooky theme with constraints
        ("frost", "flame")     # Temperature opposites with banned constraints
    ]
}

# Add these variables to track statistics
game_stats = {
    "games_played": 0,
    "moves_total": 0,
    "hints_used": {"BFS": 0, "A*": 0, "UCS": 0},
    "best_score": float('inf')
}

# Remove the THEMES dictionary and replace with fixed colors
DARK_THEME = {
    "bg_color": "#2b2b2b",
    "accent_color": "#1f6aa5",
    "success_color": "#2e7d32",
    "warning_color": "#ff9800",
    "error_color": "#f44336",
    "text_color": "#ffffff"
}

current_animation = None

# First, add variables to track the current word pair index for each mode
current_pair_indices = {
    "Beginner": 0,
    "Advanced": 0,
    "Challenge": 0
}

# Update the mode descriptions in the mode selection dropdown
mode_descriptions = {
    "Beginner": "Simple, short words (3-4 letters)",
    "Advanced": "Longer words with complex paths",
    "Challenge": "Includes banned words and letters"
}

def setup_dark_theme():
    """Apply the dark theme to all UI elements"""
    # Simply set the global theme, we'll configure buttons after they're created
    ctk.set_appearance_mode("Dark")

def apply_theme_to_elements():
    """Apply theme colors to all UI elements"""
    # Set the theme for the buttons that exist at this point
    global btn_submit, btn_start, btn_hint_bfs, btn_hint_astar, btn_hint_ucs
    global btn_compare, btn_custom, btn_stats, error_label
    
    # Define theme colors in local function instead of relying on global variables
    accent_color = DARK_THEME["accent_color"]
    success_color = DARK_THEME["success_color"]
    warning_color = DARK_THEME["warning_color"]
    error_color = DARK_THEME["error_color"]
    
    # These buttons should always exist by the time this function is called
    try:
        if 'btn_submit' in globals() and btn_submit:
            btn_submit.configure(fg_color=accent_color)
        if 'btn_start' in globals() and btn_start:
            btn_start.configure(fg_color=success_color)
        
        # These might exist depending on UI progress
        if 'btn_hint_bfs' in globals() and btn_hint_bfs:
            btn_hint_bfs.configure(fg_color=accent_color)
        if 'btn_hint_astar' in globals() and btn_hint_astar:
            btn_hint_astar.configure(fg_color=success_color)
        if 'btn_hint_ucs' in globals() and btn_hint_ucs:
            btn_hint_ucs.configure(fg_color=warning_color)
        
        if 'error_label' in globals() and error_label:
            error_label.configure(text_color="white", fg_color=error_color)
    
    # Additional buttons
        if 'btn_compare' in globals() and btn_compare:
            btn_compare.configure(fg_color=warning_color)
        if 'btn_custom' in globals() and btn_custom:
            btn_custom.configure(fg_color=accent_color)
        if 'btn_stats' in globals() and btn_stats:
            btn_stats.configure(fg_color=success_color)
    except Exception as e:
        print(f"Theme application error: {e}")

def start_game():
    global moves, word_path, word_list
    moves = 0

    # Get the current mode
    mode = game_mode.get()
    
    # Get the next word pair in the sequence
    index = current_pair_indices[mode]
    start, target = GAME_MODES[mode][index]
    
    # Show loading indicator
    show_loading_screen(f"Loading {len(start)}-letter words...")
    
    # Load only words of the required length
    word_list = get_words_by_length(len(start))
    
    # Update the index for next time
    current_pair_indices[mode] = (index + 1) % len(GAME_MODES[mode])
    
    # Reset word path with starting word
    word_path = [start]

    current_word.set(start)
    target_word.set(target)

    lbl_current.configure(text=f"{start}")
    lbl_target.configure(text=f"{target}")
    lbl_moves.configure(text=f"{moves}")
    
    # Apply and display challenge constraints
    apply_challenge_constraints()
    
    # Show the initial graph with start and target words
    update_embedded_graph(start, target)

    # Customize message based on game mode
    if mode == "Beginner":
        message = f"Transform '{start}' to '{target}' by changing one letter at a time.\nThis is a simple beginner challenge!"
    elif mode == "Advanced":
        message = f"Transform '{start}' to '{target}' by changing one letter at a time.\nThis advanced puzzle may require more steps!"
    else:  # Challenge
        message = f"Transform '{start}' to '{target}' while following the challenge constraints!\nWatch out for banned letters and words."
    
    show_popup("Game Started!", message)
    game_stats["games_played"] += 1

    # Hide loading screen
    hide_loading_screen()

def validate_move():
    global moves, word_path
    next_word = entry_word.get().strip().lower()
    entry_word.delete(0, 'end')  # Clear the entry after submission

    if len(next_word) != len(current_word.get()):
        show_popup("Invalid Move!", "Words must be of the same length.")
        return

    if next_word not in word_list:
        show_popup("Invalid Move!", "This word is not in the dictionary.")
        return

    if sum(1 for a, b in zip(current_word.get(), next_word) if a != b) != 1:
        show_popup("Invalid Move!", "Words must differ by only one letter.")
        return

    if game_mode.get() == "Challenge":
        if next_word in banned_words:
            show_popup("Invalid Move!", f"The word '{next_word}' is banned in this challenge.")
            return
        
        if any(letter in banned_letters for letter in next_word):
            show_popup("Invalid Move!", f"You cannot use the banned letters: {', '.join(banned_letters)}")
            return

    # Add the new word to our path
    word_path.append(next_word)
    
    # Update UI
    current_word.set(next_word)
    lbl_current.configure(text=f"{next_word}")
    moves += 1
    lbl_moves.configure(text=f"{moves}")
    
    # Update visualization with the full word path
    update_embedded_graph(current_word.get(), target_word.get(), path=word_path)
    
    game_stats["moves_total"] += 1

    if next_word == target_word.get():
        if game_stats["best_score"] > moves:
            game_stats["best_score"] = moves
        # Only show popup but don't auto-start a new game
        show_game_completed_popup(f"🎉 Congratulations! You won in {moves} moves!")

def get_hint(algorithm):
    """Get a hint for the next move using the specified algorithm"""
    show_loading_screen("Finding Best Move...")
    
    def fetch_hint():
        try:
            time.sleep(1)  
            start = current_word.get()
            target = target_word.get()

            if algorithm == "BFS":
                path = bfs_shortest_path(start, target, word_list)
            elif algorithm == "A*":
                path = a_star_search(start, target, word_list)
            elif algorithm == "UCS":
                path = ucs_shortest_path(start, target, word_list)
            else:
                path = None

            hide_loading_screen()

            if path and len(path) > 1:
                hint_word = path[1]
                show_popup("AI Hint", f"🔍 Next best move ({algorithm}): {hint_word}")
                hint_label.configure(text=f"Last Hint: {hint_word} (via {algorithm})")
                safe_update_embedded_graph(start, target, path)
            else:
                show_popup("Hint Failed", "No valid path found!")
        except Exception as e:
            hide_loading_screen()
            show_popup("Error", f"An error occurred: {str(e)}")
    
    threading.Thread(target=fetch_hint).start()
    game_stats["hints_used"][algorithm] += 1


def update_embedded_graph(start, target, path=None, animated=False):
    """Update the graph visualization with animation support"""
    global current_figure, current_animation
    
    # Use the word_path by default if no specific path is provided
    if path is None and len(word_path) > 0:
        path = word_path
        
    # If we only have one word in the path and it's not already at the target,
    # calculate a suggested path from start to target to show possibilities
    if (path is None or len(path) <= 1) and start != target:
        # Try to find a path using BFS
        suggested_path = bfs_shortest_path(start, target, word_list)
        if suggested_path:
            # If we found a path, show it as a dotted/faded suggestion
            show_suggested_path = True
        else:
            show_suggested_path = False
    else:
        show_suggested_path = False
        suggested_path = None
    
    # Stop any existing animation
    if current_animation:
        current_animation.event_source.stop()
        current_animation = None
    
    # Clear previous figure if it exists
    if current_figure is not None:
        current_figure.clear()
    else:
        current_figure = plt.figure(figsize=(4, 3.5), dpi=100)  # Reduced size from (6, 5)
    
    # Create a subgraph of relevant words
    relevant_words = set()
    if path:
        relevant_words = set(path)
        # Add the target word if it's not in the path yet
        relevant_words.add(target)
    else:
        # Add at least start and target
        relevant_words.add(start)
        relevant_words.add(target)
    
    # If we're showing a suggested path, add those words too
    if show_suggested_path and suggested_path:
        relevant_words.update(suggested_path)
    
    # Create a copy of the set to avoid modifying while iterating
    words_to_process = relevant_words.copy()
    
    # Add neighboring words for context
    for word in words_to_process:
        neighbors = get_valid_transformations(word, word_list)
        # Limit to 2 neighbors to keep graph readable
        for neighbor in list(neighbors)[:2]:
            relevant_words.add(neighbor)
    
    # Create subgraph
    subgraph = nx.Graph()
    for word in relevant_words:
        subgraph.add_node(word)
        
    # Add edges
    for word in relevant_words:
        for neighbor in relevant_words:
            if word != neighbor and is_valid_transformation(word, neighbor):
                subgraph.add_edge(word, neighbor)
    
    ax = current_figure.add_subplot(111)
    pos = nx.spring_layout(subgraph, seed=42)  # Fixed seed for consistent layout
    
    # Set figure background color to match theme
    bg_color = DARK_THEME["bg_color"]  # Use the theme's background color
    ax.set_facecolor(bg_color)
    current_figure.patch.set_facecolor(bg_color)
    
    # Create node groups for legend
    regular_nodes = set(subgraph.nodes()) - {start, target}
    if path and len(path) > 1:
        path_nodes = set(path) - {start, target}  # Remove start/target to avoid double-coloring
        regular_nodes -= path_nodes  # Remove path nodes from regular nodes
    else:
        path_nodes = set()
    
    # Draw background nodes (regular nodes) with 3D-like effect
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=list(regular_nodes), 
                        node_size=650,  # Increased size
                        node_color="#555555",  # Darker gray but still visible
                        alpha=0.8,
                        edgecolors="#777777",  # Lighter border for 3D effect
                        linewidths=2)  # Thicker border
    
    # Draw regular edges with better visibility
    nx.draw_networkx_edges(subgraph, pos, ax=ax, 
                        width=1.7,  # Thicker lines
                        edge_color="#888888",  # Lighter color for visibility
                        alpha=0.8,  # More opacity
                        style='solid')  # Solid lines
    
    # Highlight the user's path with more vivid colors if it exists
    if path and len(path) > 1:
        path_edges = list(zip(path, path[1:]))
        
        # Draw path nodes with larger size, glow effect
        nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                            nodelist=list(path_nodes), 
                            node_size=750,  # Even bigger
                            node_color="#3584e4",  # Bright blue 
                            edgecolors="#66a5ff",  # Lighter blue border for glow effect
                            linewidths=2.5,
                            alpha=1.0)
        
        # Draw path edges with animated arrow and brighter color
        nx.draw_networkx_edges(subgraph, pos, ax=ax, 
                            edgelist=path_edges, 
                            width=4.0,  # Thicker than before
                            edge_color="#ffaa33",  # Brighter orange for better visibility
                            arrows=True,
                            arrowsize=18,  # Larger arrows
                            connectionstyle="arc3,rad=0.15")  # More curved for better visibility
    
    # If appropriate, show a suggested path with dotted lines
    if show_suggested_path and suggested_path and len(suggested_path) > 1:
        suggested_edges = list(zip(suggested_path, suggested_path[1:]))
        nx.draw_networkx_edges(subgraph, pos, ax=ax, 
                            edgelist=suggested_edges, 
                            width=3.0,  # Thicker
                            edge_color="#b366ff",  # Brighter purple
                            style='dashed',
                            alpha=0.85,  # More visible
                            arrows=True,
                            arrowsize=15)  # Larger arrows
    
    # Highlight start word with distinct color, largest size, and glow effect
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=[start], 
                        node_size=950,  # Largest size
                        node_color="#2ecc71",  # Brighter green
                        edgecolors="#87f5b3",  # Light green for glow effect
                        linewidths=3.0)  # Thicker border
    
    # Highlight target word with distinct color, large size and glow effect
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=[target], 
                        node_size=950,  # Same size as start
                        node_color="#e74c3c",  # Red for target
                        edgecolors="#ff8b81",  # Light red for glow effect
                        linewidths=3.0)  # Thicker border
    
    # Improved network labels with better visibility and background
    label_options = {
        "font_size": 11,
        "font_weight": "bold",
        "font_color": "white",
        "font_family": "Arial",
        "bbox": {"boxstyle": "round,pad=0.3", "fc": "#333333", "ec": "#555555", "alpha": 0.8}
    }
    nx.draw_networkx_labels(subgraph, pos, ax=ax, **label_options)
    
    # Set the title with improved styling
    if len(word_path) > 0:
        ax.set_title(f"Word Ladder: {word_path[0]} → {target}", 
                   fontsize=15, 
                   fontweight="bold", 
                   color="white",
                   pad=12)
    else:
        ax.set_title(f"Word Ladder: {start} → {target}", 
                   fontsize=15, 
                   fontweight="bold", 
                   color="white",
                   pad=12)
    
    # Create legend elements with larger markers and better colors
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#2ecc71", markeredgecolor="#87f5b3", 
                  markersize=15, markeredgewidth=2, label='Start Word'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#e74c3c", markeredgecolor="#ff8b81", 
                  markersize=15, markeredgewidth=2, label='Target Word'),
    ]
    
    # Only add path elements to legend if there's a path
    if path and len(path) > 1:
        legend_elements.extend([
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#3584e4", markeredgecolor="#66a5ff", 
                      markersize=15, markeredgewidth=2, label='Path Words'),
            plt.Line2D([0], [0], color="#ffaa33", lw=4, label='Current Path')
        ])
        
    # If there's a suggested path, add it to legend
    if show_suggested_path and suggested_path:
        legend_elements.append(
            plt.Line2D([0], [0], color="#b366ff", lw=3, dashes=(5, 2), label='Suggested Path')
        )
    
    # Add other words to legend
    legend_elements.append(
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#555555", markeredgecolor="#777777", 
                  markersize=15, markeredgewidth=2, label='Other Words')
    )
    
    # Place legend in the bottom right corner with enhanced visibility
    legend = ax.legend(handles=legend_elements, 
                      loc='lower right',  # Bottom right corner
                      fontsize=10,  # Larger font
                      frameon=True,
                      framealpha=0.9,  # More opaque
                      facecolor='#222222',  # Dark background
                      edgecolor='#555555',  # Border color
                      title="Legend",  # Add a title
                      title_fontsize=12)  # Make title larger
    
    # Set legend title color to a bright color for visibility
    legend.get_title().set_color('#ffcc00')  # Bright gold color
    
    # Set legend text color to white with improved spacing
    for text in legend.get_texts():
        text.set_color('white')
    
    # Add padding around the plot to ensure legend is fully visible
    plt.subplots_adjust(right=0.85)
    
    # Hide axis
    ax.axis('off')
    current_figure.tight_layout()
    
    # Update the canvas
    graph_canvas.draw()

def show_popup(title, message):
    popup = ctk.CTkToplevel(root)
    popup.geometry("400x200")
    popup.title(title)
    popup.transient(root)
    popup.grab_set()  

    lbl_popup = ctk.CTkLabel(popup, text=message, font=("Arial", 14), wraplength=350, justify="center")
    lbl_popup.pack(pady=20)

    btn_close = ctk.CTkButton(popup, text="✓ OK", 
                           command=popup.destroy, 
                           font=("Arial", 14, "bold"),
                           fg_color=DARK_THEME["accent_color"],
                           hover_color="#155485",
                           height=36)
    btn_close.pack(pady=10)

def show_loading_screen(message):
    global loading_popup
    loading_popup = ctk.CTkToplevel(root)
    loading_popup.geometry("300x150")
    loading_popup.title("Loading...")
    loading_popup.transient(root)
    loading_popup.grab_set()

    lbl_loading = ctk.CTkLabel(loading_popup, text=message, font=("Arial", 14))
    lbl_loading.pack(pady=20)

    progress = ctk.CTkProgressBar(loading_popup)
    progress.pack(pady=10)
    progress.set(0.5)

def hide_loading_screen():
    loading_popup.destroy()

def apply_challenge_constraints():
    """Apply specific constraints for challenge mode games"""
    global banned_letters, banned_words
    
    # Reset constraints
    banned_letters = []
    banned_words = []
    
    # Only apply constraints in Challenge mode
    mode = game_mode.get()
    if mode != "Challenge":
        constraints_label.configure(text="")
        return
    
    # Set specific constraints based on the current word pair
    start = current_word.get()
    target = target_word.get()
    
    if start == "magic" and target == "power":
        banned_letters = ['q', 'x', 'z']
        banned_words = ["manic", "major"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: q, x, z\n🚫 Cannot use words: 'manic' or 'major'"
    
    elif start == "smoke" and target == "blaze":
        banned_letters = ['j', 'k', 'q']
        banned_words = ["shake", "smote"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: j, k, q\n🚫 Cannot use words: 'shake' or 'smote'"
    
    elif start == "beach" and target == "waves":
        banned_letters = ['w', 'y', 'z']
        banned_words = ["bench", "reach"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: w, y, z\n🚫 Cannot use words: 'bench' or 'reach'"
    
    elif start == "night" and target == "light":
        banned_letters = ['p', 'q', 'z']
        banned_words = ["sight", "eight"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: p, q, z\n🚫 Cannot use words: 'sight' or 'eight'"
    
    elif start == "ghost" and target == "witch":
        banned_letters = ['f', 'q', 'z']
        banned_words = ["chest", "whist"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: f, q, z\n🚫 Cannot use words: 'chest' or 'whist'"
    
    elif start == "frost" and target == "flame":
        banned_letters = ['b', 'x', 'z']
        banned_words = ["front", "frame"]
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: b, x, z\n🚫 Cannot use words: 'front' or 'frame'"
    
    else:
        # Default constraints if we have a custom challenge pair
        banned_letters = ['q', 'x', 'z']
        banned_words = []
        constraint_text = "⚔️ Challenge Rules:\n🚫 Cannot use letters: q, x, z"
    
    # Create a visually distinct constraint label
    constraints_label.configure(
        text=constraint_text,
        fg_color=DARK_THEME["error_color"],
        text_color="white",
        corner_radius=8
    )

def compare_algorithms():
    start = current_word.get()
    target = target_word.get()
    
    if not start or not target:
        show_popup("Error", "Please start a game first!")
        return
    
    show_loading_screen("Comparing Algorithms...")
    
    def perform_comparison():
        import time
        results = {}
        MAX_TIME = 5.0  # Maximum time in seconds to allow for each algorithm
        
        # Define the heuristic function here to ensure it's available
        def heuristic(word, target):
            """Heuristic function for A* search - returns number of differing letters"""
            return sum(1 for a, b in zip(word, target) if a != b)
        
        # Create dictionaries to store g(n), h(n), and f(n) values for each algorithm and each node in the path
        algorithm_functions = {
            "BFS": {"paths": {}, "visited": set()},
            "A*": {"paths": {}, "visited": set()},
            "UCS": {"paths": {}, "visited": set()}
        }
        
        # Function to run algorithm with timeout and track function values
        def run_with_timeout(algorithm, algo_name):
            start_time = time.time()
            path = None
            visited = set()
            
            try:
                if algo_name == "BFS":
                    # For BFS, g(n) is path length, h(n) is not used directly (we'll calculate it for comparison)
                    visited = set([start])
                    queue = deque([(start, [start], 0)])  # (word, path, depth/g-value)
                    
                    # Store g, h, f for start
                    g_value = 0
                    h_value = sum(1 for a, b in zip(start, target) if a != b)
                    f_value = g_value  # BFS doesn't use f = g + h directly
                    algorithm_functions[algo_name]["paths"][start] = {"g": g_value, "h": h_value, "f": f_value}
                    
                    iterations = 0
                    while queue and iterations < 10000:
                        iterations += 1
                        current, path_so_far, g = queue.popleft()
                        
                        if current == target:
                            path = path_so_far
                            break
                            
                        # Get neighbors
                        for neighbor in get_word_neighbors(current, word_list):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                new_g = g + 1
                                new_h = sum(1 for a, b in zip(neighbor, target) if a != b)
                                new_f = new_g  # BFS doesn't use f = g + h directly
                                
                                # Store function values
                                algorithm_functions[algo_name]["paths"][neighbor] = {"g": new_g, "h": new_h, "f": new_f}
                                
                                queue.append((neighbor, path_so_far + [neighbor], new_g))
                    
                    algorithm_functions[algo_name]["visited"] = visited
                
                elif algo_name == "A*":
                    # For A*, f(n) = g(n) + h(n)
                    visited = set()
                    
                    # Store g, h, f for start
                    g_value = 0
                    h_value = heuristic(start, target)
                    f_value = g_value + h_value
                    algorithm_functions[algo_name]["paths"][start] = {"g": g_value, "h": h_value, "f": f_value}
                    
                    pq = [(f_value, g_value, start, [start])]  # (f(n), g(n), current_word, path)
                    
                    iterations = 0
                    while pq and iterations < 10000:
                        iterations += 1
                        f, g, current, path_so_far = heapq.heappop(pq)
                        
                        if current == target:
                            path = path_so_far
                            break
                            
                        if current in visited:
                            continue
                            
                        visited.add(current)
                        
                        # Get neighbors
                        for neighbor in get_word_neighbors(current, word_list):
                            if neighbor not in visited:
                                new_g = g + 1
                                new_h = heuristic(neighbor, target)
                                new_f = new_g + new_h
                                
                                # Store function values
                                algorithm_functions[algo_name]["paths"][neighbor] = {"g": new_g, "h": new_h, "f": new_f}
                                
                                heapq.heappush(pq, (new_f, new_g, neighbor, path_so_far + [neighbor]))
                    
                    algorithm_functions[algo_name]["visited"] = visited
                
                elif algo_name == "UCS":
                    # For UCS, f(n) = g(n), h(n) is not used
                    visited = set()
                    
                    # Store g, h, f for start
                    g_value = 0
                    h_value = heuristic(start, target)  # We'll calculate it for comparison
                    f_value = g_value
                    algorithm_functions[algo_name]["paths"][start] = {"g": g_value, "h": h_value, "f": f_value}
                    
                    pq = [(g_value, start, [start])]  # (cost/g-value, current_word, path)
                    
                    iterations = 0
                    while pq and iterations < 10000:
                        iterations += 1
                        g, current, path_so_far = heapq.heappop(pq)
                        
                        if current == target:
                            path = path_so_far
                            break
                            
                        if current in visited:
                            continue
                            
                        visited.add(current)
                        
                        # Get neighbors
                        for neighbor in get_word_neighbors(current, word_list):
                            if neighbor not in visited:
                                new_g = g + 1
                                new_h = heuristic(neighbor, target)  # We'll calculate it for comparison
                                new_f = new_g
                                
                                # Store function values
                                algorithm_functions[algo_name]["paths"][neighbor] = {"g": new_g, "h": new_h, "f": new_f}
                                
                                heapq.heappush(pq, (new_g, neighbor, path_so_far + [neighbor]))
                    
                    algorithm_functions[algo_name]["visited"] = visited
                
                time_taken = time.time() - start_time
                
                # If takes too long, consider it timed out
                if time_taken > MAX_TIME:
                    return {"path": None, "time": time_taken, "timeout": True, "visited": visited}
                else:
                    return {"path": path, "time": time_taken, "timeout": False, "visited": visited}
                    
            except Exception as e:
                print(f"Error in {algo_name}: {str(e)}")
                return {"path": None, "time": time.time() - start_time, "timeout": False, "error": str(e), "visited": visited}
        
        # Test algorithms
        results["BFS"] = run_with_timeout(bfs_shortest_path, "BFS")
        results["A*"] = run_with_timeout(a_star_search, "A*")
        results["UCS"] = run_with_timeout(ucs_shortest_path, "UCS")
        
        hide_loading_screen()
        
        # Create comparison popup with tabbed interface
        comparison_popup = ctk.CTkToplevel(root)
        comparison_popup.geometry("800x600")  # Larger window for more content
        comparison_popup.title("Algorithm Comparison")
        comparison_popup.transient(root)
        comparison_popup.grab_set()
        
        # Create a header
        header = ctk.CTkLabel(comparison_popup, text=f"Algorithm Comparison: '{start}' to '{target}'", 
                              font=("Arial", 16, "bold"))
        header.pack(pady=10)
        
        # Create tabview for different tabs (Summary, BFS, A*, UCS)
        tabview = ctk.CTkTabview(comparison_popup)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs for each view
        tab_summary = tabview.add("Summary")
        tab_bfs = tabview.add("BFS")
        tab_astar = tabview.add("A*")
        tab_ucs = tabview.add("UCS")
        
        # Summary tab - display basic comparison
        summary_frame = ctk.CTkFrame(tab_summary)
        summary_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add explanation about the algorithms at the top
        explanation_frame = ctk.CTkFrame(summary_frame)
        explanation_frame.pack(padx=10, pady=10, fill="x")
        
        explanation_title = ctk.CTkLabel(explanation_frame, 
                                      text="Search Algorithm Functions", 
                                      font=("Arial", 14, "bold"),
                                      text_color=DARK_THEME["warning_color"])
        explanation_title.pack(pady=(5, 5))
        
        explanation_text = (
            "Each algorithm follows a structured search strategy, with these core functions:\n\n"
            "• g(n): Cost function - measures effort spent to reach the current word\n"
            "• h(n): Heuristic - estimates remaining transformations to target\n"
            "• f(n) = g(n) + h(n): Prioritizes best path for optimal solutions\n\n"
            "BFS: Uses equal weights (g(n) = path length)\n"
            "A*: Combines path cost and heuristic (f(n) = g(n) + h(n))\n"
            "UCS: Prioritizes based on path cost only (f(n) = g(n))"
        )
        
        explanation_label = ctk.CTkLabel(explanation_frame, 
                                      text=explanation_text,
                                      font=("Arial", 12),
                                      justify="left")
        explanation_label.pack(padx=10, pady=5)
        
        # Results table
        summary_table = ctk.CTkFrame(summary_frame)
        summary_table.pack(pady=10, fill="x")
        
        # Add headers
        headers = ["Algorithm", "Path Length", "Time (s)", "Nodes Explored", "Path"]
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(summary_table, text=header, font=("Arial", 12, "bold"))
            header_label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Find the best performing algorithm based on time and path length
        best_algo = None
        best_score = float('inf')  # Lower is better
        
        for algo, data in results.items():
            if data["path"]:
                # Score = time * path_length (weighted average of both metrics)
                score = data["time"] * len(data["path"])
                if score < best_score:
                    best_score = score
                    best_algo = algo
        
        # Add data for each algorithm
        row = 1
        for algo, data in results.items():
            # Algorithm name with color
            if algo == "BFS":
                color = DARK_THEME["accent_color"]
            elif algo == "A*":
                color = DARK_THEME["success_color"]
            else:  # UCS
                color = DARK_THEME["warning_color"]
                
            # Add a star to the best performing algorithm
            algo_text = f"{algo} ⭐" if algo == best_algo else algo
            
            algo_label = ctk.CTkLabel(summary_table, text=algo_text, 
                                   font=("Arial", 12, "bold"),
                                   text_color="white",
                                   fg_color=color,
                                   corner_radius=5,
                                   width=60,
                                   height=24)
            algo_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            # Path length
            if data["path"]:
                path_len = len(data["path"]) - 1
                path_text = f"{path_len} steps"
            else:
                path_text = "No path"
                
            path_len_label = ctk.CTkLabel(summary_table, text=path_text, font=("Arial", 12))
            path_len_label.grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Time taken
            time_text = f"{data['time']:.3f}s"
            time_label = ctk.CTkLabel(summary_table, text=time_text, font=("Arial", 12))
            time_label.grid(row=row, column=2, padx=10, pady=5, sticky="w")
            
            # Nodes explored
            nodes_text = str(len(data["visited"]))
            nodes_label = ctk.CTkLabel(summary_table, text=nodes_text, font=("Arial", 12))
            nodes_label.grid(row=row, column=3, padx=10, pady=5, sticky="w")
            
            # Path (shortened if needed)
            if data["path"]:
                if len(data["path"]) > 5:
                    path_display = f"{' → '.join(data['path'][:2])} → ... → {' → '.join(data['path'][-2:])}"
                else:
                    path_display = " → ".join(data["path"])
            else:
                path_display = "No path found"
                
            path_label = ctk.CTkLabel(summary_table, text=path_display, font=("Arial", 12), wraplength=400)
            path_label.grid(row=row, column=4, padx=10, pady=5, sticky="w")
            
            row += 1
            
        # Add performance summary
        if best_algo:
            best_result = results[best_algo]
            summary_text = (
                f"\n🏆 Best Performing Algorithm: {best_algo}\n"
                f"Time: {best_result['time']:.3f}s | Path Length: {len(best_result['path'])-1} steps | "
                f"Nodes Explored: {len(best_result['visited'])}\n"
                f"This algorithm provided the best balance of speed and path efficiency."
            )
            
            summary_label = ctk.CTkLabel(summary_frame, 
                                     text=summary_text,
                                     font=("Arial", 12, "bold"),
                                     text_color="#ffcc00")  # Gold color
            summary_label.pack(pady=10, padx=10)
            
        # Function to create detailed tab for each algorithm
        def create_algorithm_tab(tab, algo_name):
            algo_frame = ctk.CTkFrame(tab)
            algo_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Path results section
            path_frame = ctk.CTkFrame(algo_frame)
            path_frame.pack(fill="x", padx=10, pady=10)
            
            # Get algorithm data
            data = results[algo_name]
            func_values = algorithm_functions[algo_name]["paths"]
            
            # Algorithm title with color
            if algo_name == "BFS":
                color = DARK_THEME["accent_color"]
                algo_desc = "Breadth-First Search: Explores all paths of length n before any of length n+1"
                formula_desc = "Uses g(n) = path length. Does not use h(n) in path finding."
            elif algo_name == "A*":
                color = DARK_THEME["success_color"]
                algo_desc = "A* Search: Uses heuristic to prioritize paths that seem closer to goal"
                formula_desc = "Uses f(n) = g(n) + h(n) to prioritize exploration."
            else:  # UCS
                color = DARK_THEME["warning_color"]
                algo_desc = "Uniform Cost Search: Explores paths in order of their total cost"
                formula_desc = "Uses only g(n) = path cost. Ignores h(n) in path finding."
                
            title_label = ctk.CTkLabel(path_frame, text=f"{algo_name} Algorithm", 
                                    font=("Arial", 16, "bold"),
                                    text_color="white",
                                    fg_color=color,
                                    corner_radius=10,
                                    width=150,
                                    height=30)
            title_label.pack(pady=5)
            
            desc_label = ctk.CTkLabel(path_frame, text=algo_desc, font=("Arial", 12))
            desc_label.pack(pady=5)
            
            # Add formula description with highlighted styling
            formula_frame = ctk.CTkFrame(path_frame, fg_color="#252525", corner_radius=5)
            formula_frame.pack(fill="x", padx=10, pady=5)
            
            formula_label = ctk.CTkLabel(formula_frame, 
                                      text=f"⚙️ Formula: {formula_desc}", 
                                      font=("Arial", 12, "bold"),
                                      text_color="#ffcc00")  # Gold color for emphasis
            formula_label.pack(pady=5, padx=5)
            
            # Display path
            if data["path"]:
                path_label = ctk.CTkLabel(path_frame, text="Path:", font=("Arial", 14, "bold"))
                path_label.pack(pady=(10, 5))
                
                path_display = ctk.CTkLabel(path_frame, text=" → ".join(data["path"]), 
                                         font=("Arial", 12),
                                         wraplength=700)
                path_display.pack(pady=5)
                
                # Function values table
                func_frame = ctk.CTkFrame(algo_frame)
                func_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Table title with function explanation
                if algo_name == "BFS":
                    table_title = "Search Function Values (BFS uses g(n) = path length)"
                elif algo_name == "A*":
                    table_title = "Search Function Values (A* uses f(n) = g(n) + h(n))"
                else:  # UCS
                    table_title = "Search Function Values (UCS uses f(n) = g(n), ignores h(n))"
                
                table_label = ctk.CTkLabel(func_frame, text=table_title, 
                                       font=("Arial", 14, "bold"))
                table_label.pack(pady=5)
                
                # Create table for function values
                table = ctk.CTkFrame(func_frame)
                table.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Headers
                headers = ["Step", "Word", "g(n)", "h(n)", "f(n)"]
                for i, header in enumerate(headers):
                    header_label = ctk.CTkLabel(table, text=header, font=("Arial", 12, "bold"))
                    header_label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
                
                # Fill in function values for each word in the path
                for i, word in enumerate(data["path"]):
                    # Step
                    step_label = ctk.CTkLabel(table, text=str(i), font=("Arial", 12))
                    step_label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
                    
                    # Word
                    word_label = ctk.CTkLabel(table, text=word, font=("Arial", 12))
                    word_label.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
                    
                    # Function values
                    if word in func_values:
                        values = func_values[word]
                        
                        g_label = ctk.CTkLabel(table, text=str(values["g"]), font=("Arial", 12))
                        g_label.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")
                        
                        h_label = ctk.CTkLabel(table, text=str(values["h"]), font=("Arial", 12))
                        h_label.grid(row=i+1, column=3, padx=10, pady=5, sticky="w")
                        
                        # Highlight the f(n) calculation based on algorithm
                        if algo_name == "BFS":
                            f_text = f"{values['g']} (g only)"
                        elif algo_name == "A*":
                            f_text = f"{values['f']} = {values['g']} + {values['h']}"
                        else:  # UCS
                            f_text = f"{values['g']} (g only)"
                            
                        f_label = ctk.CTkLabel(table, text=f_text, 
                                           font=("Arial", 12, "bold"),
                                           text_color="#ffcc00" if algo_name == "A*" else "white")
                        f_label.grid(row=i+1, column=4, padx=10, pady=5, sticky="w")
                    else:
                        for j in range(3):
                            na_label = ctk.CTkLabel(table, text="N/A", font=("Arial", 12))
                            na_label.grid(row=i+1, column=j+2, padx=10, pady=5, sticky="w")
                
                # Add buttons to visualize this algorithm's path and graph
                buttons_frame = ctk.CTkFrame(func_frame, fg_color="transparent")
                buttons_frame.pack(pady=10)
                
                # Visualize path button
                viz_path_btn = ctk.CTkButton(
                    buttons_frame, 
                    text=f"Visualize Path", 
                    command=lambda algo_path=data["path"]: [comparison_popup.destroy(), 
                                    safe_update_embedded_graph(start, target, algo_path, animated=True)],
                    font=("Arial", 12, "bold"),
                    fg_color=color,
                    hover_color="#155485" if algo_name == "BFS" else 
                               "#1e5c22" if algo_name == "A*" else "#cc7a00",
                    width=150
                )
                viz_path_btn.pack(side="left", padx=10)
                
                # Visualize full graph button
                if algo_name == "BFS":
                    visited = algorithm_functions[algo_name]["visited"]
                    viz_graph_btn = ctk.CTkButton(
                        buttons_frame, 
                        text=f"Show {algo_name} Graph", 
                        command=lambda algo_visited=visited, algo_path=data["path"]: 
                                      visualize_algorithm_graph(start, target, algo_name, algo_visited, algo_path),
                        font=("Arial", 12, "bold"),
                        fg_color="#333333",
                        hover_color="#444444",
                        width=150
                    )
                    viz_graph_btn.pack(side="right", padx=10)
                else:
                    visited = algorithm_functions[algo_name]["visited"]
                    viz_graph_btn = ctk.CTkButton(
                        buttons_frame, 
                        text=f"Show {algo_name} Graph", 
                        command=lambda algo_visited=visited, algo_path=data["path"]: 
                                      visualize_algorithm_graph(start, target, algo_name, algo_visited, algo_path),
                        font=("Arial", 12, "bold"),
                        fg_color="#333333",
                        hover_color="#444444",
                        width=150
                    )
                    viz_graph_btn.pack(side="right", padx=10)
                
            else:
                # No path found
                no_path_label = ctk.CTkLabel(path_frame, 
                                        text=f"No path found using {algo_name}",
                                        font=("Arial", 14, "bold"),
                                        text_color=DARK_THEME["error_color"])
                no_path_label.pack(pady=50)
        
        # Create tabs for each algorithm
        create_algorithm_tab(tab_bfs, "BFS")
        create_algorithm_tab(tab_astar, "A*")
        create_algorithm_tab(tab_ucs, "UCS")
        
        # Close button
        close_btn = ctk.CTkButton(comparison_popup, 
                               text="Close", 
                               command=comparison_popup.destroy,
                               fg_color=DARK_THEME["accent_color"],
                               hover_color="#155485",
                               font=("Arial", 12, "bold"),
                               height=36)
        close_btn.pack(pady=10)
        
    threading.Thread(target=perform_comparison).start()

def custom_word_ladder():
    custom_popup = ctk.CTkToplevel(root)
    custom_popup.geometry("400x250")
    custom_popup.title("Custom Word Ladder")
    custom_popup.transient(root)
    custom_popup.grab_set()
    
    ctk.CTkLabel(custom_popup, text="🔠 Create your own Word Ladder", 
                font=("Arial", 14, "bold")).pack(pady=10)
    
    start_frame = ctk.CTkFrame(custom_popup)
    start_frame.pack(pady=5, fill="x", padx=20)
    ctk.CTkLabel(start_frame, text="Start Word:").pack(side="left", padx=5)
    start_entry = ctk.CTkEntry(start_frame)
    start_entry.pack(side="right", fill="x", expand=True, padx=5)
    
    target_frame = ctk.CTkFrame(custom_popup)
    target_frame.pack(pady=5, fill="x", padx=20)
    ctk.CTkLabel(target_frame, text="Target Word:").pack(side="left", padx=5)
    target_entry = ctk.CTkEntry(target_frame)
    target_entry.pack(side="right", fill="x", expand=True, padx=5)
    
    def validate_custom_words():
        start = start_entry.get().strip().lower()
        target = target_entry.get().strip().lower()
        
        if len(start) != len(target):
            messagebox.showerror("Error", "Words must be the same length!")
            return
            
        if start not in word_list:
            messagebox.showerror("Error", f"'{start}' is not in the dictionary!")
            return
            
        if target not in word_list:
            messagebox.showerror("Error", f"'{target}' is not in the dictionary!")
            return
            
        # Check if there's a path using BFS
        path = bfs_shortest_path(start, target, word_list)
        if not path:
            messagebox.showerror("Error", "No valid word ladder exists between these words!")
            return
            
        # Start game with custom words
        current_word.set(start)
        target_word.set(target)
        global moves
        moves = 0
        lbl_current.configure(text=f"{start}")
        lbl_target.configure(text=f"{target}")
        lbl_moves.configure(text=f"{moves}")
        
        # Update graph
        update_embedded_graph(start, target)
        
        custom_popup.destroy()
    
    btn_frame = ctk.CTkFrame(custom_popup)
    btn_frame.pack(pady=15, fill="x", padx=20)
    
    ctk.CTkButton(btn_frame, text="❌ Cancel", 
                command=custom_popup.destroy,
                fg_color=DARK_THEME["error_color"],
                hover_color="#c62828",
                font=("Arial", 12, "bold"),
                height=36).pack(side="left", padx=10)
                
    ctk.CTkButton(btn_frame, text="✅ Start Game", 
                command=validate_custom_words,
                fg_color=DARK_THEME["success_color"],
                hover_color="#1e5c22",
                font=("Arial", 12, "bold"),
                height=36).pack(side="right", padx=10)

def show_statistics():
    stats_popup = ctk.CTkToplevel(root)
    stats_popup.geometry("400x300")
    stats_popup.title("Game Statistics")
    stats_popup.transient(root)
    stats_popup.grab_set()
    
    ctk.CTkLabel(stats_popup, text="📊 Word Ladder Statistics", 
                font=("Arial", 16, "bold")).pack(pady=10)
    
    stats_frame = ctk.CTkFrame(stats_popup)
    stats_frame.pack(padx=20, pady=10, fill="both", expand=True)
    
    stats_text = f"""
    🎮 Games Played: {game_stats['games_played']}
    🔢 Total Moves: {game_stats['moves_total']}
    🏆 Best Score: {game_stats['best_score'] if game_stats['best_score'] != float('inf') else 'N/A'}
    
    💡 Hints Used:
    - 🔍 BFS: {game_stats['hints_used']['BFS']}
    - ⭐ A*: {game_stats['hints_used']['A*']}
    - 🧭 UCS: {game_stats['hints_used']['UCS']}
    """
    
    ctk.CTkLabel(stats_frame, text=stats_text, justify="left", 
                font=("Arial", 12)).pack(padx=20, pady=10)
    
    ctk.CTkButton(stats_popup, text="✓ Close", 
                command=stats_popup.destroy,
                fg_color=DARK_THEME["accent_color"],
                hover_color="#155485",
                font=("Arial", 12, "bold"),
                height=36).pack(pady=10)

def animate_word_change(old_word, new_word):
    """Animate the transition between words"""
    # Create a more reliable animation using color changes instead of alpha
    colors = ["#ffffff", "#dddddd", "#bbbbbb", "#999999", "#777777", "#555555", 
              "#333333", "#111111", "#000000", "#111111", "#333333", "#555555", 
              "#777777", "#999999", "#bbbbbb", "#dddddd", "#ffffff"]
    
    # We'll use the existing label and just change its text/color
    lbl_current.configure(text=old_word)
    
    def animate_step(step):
        if step >= len(colors):
            # Animation complete, show new word
            lbl_current.configure(text=new_word, text_color=DARK_THEME["text_color"])
            return
        
        # Change text color for fade effect
        lbl_current.configure(text_color=colors[step])
        
        # At midpoint, change text to new word
        if step == len(colors) // 2:
            lbl_current.configure(text=new_word)
        
        # Schedule next step
        root.after(50, lambda: animate_step(step+1))
    
    # Start animation
    animate_step(0)

def update_validate_move():
    """Enhanced version of validate_move with animations and highlighting"""
    global moves
    next_word = entry_word.get().strip().lower()
    entry_word.delete(0, 'end')  # Clear the entry after submission
    
    # All the validation checks as before
    if len(next_word) != len(current_word.get()):
        flash_error_message("Words must be of the same length.")
        return

    if next_word not in word_list:
        flash_error_message("This word is not in the dictionary.")
        return

    if sum(1 for a, b in zip(current_word.get(), next_word) if a != b) != 1:
        flash_error_message("Words must differ by only one letter.")
        return

    if game_mode.get() == "Challenge":
        if next_word in banned_words:
            flash_error_message(f"The word '{next_word}' is banned in this challenge.")
            return
        
        if any(letter in banned_letters for letter in next_word):
            flash_error_message(f"Cannot use banned letters: {', '.join(banned_letters)}")
            return
    
    # Word is valid - proceed with the move
    old_word = current_word.get()
    current_word.set(next_word)
    
    # Animate the word change
    animate_word_change(old_word, next_word)
    
    moves += 1
    lbl_moves.configure(text=f"{moves}")
    
    # Update visualization with a smooth transition
    safe_update_embedded_graph(current_word.get(), target_word.get(), animated=True)
    
    game_stats["moves_total"] += 1

    if next_word == target_word.get():
        if game_stats["best_score"] > moves:
            game_stats["best_score"] = moves
        celebrate_win()

def flash_error_message(message):
    """Display an error message with a flashing effect"""
    error_label.configure(text=message)
    
    # Make it visible
    error_label.pack(fill="x", padx=10, pady=5)
    
    # Flash effect - use predefined colors instead of alpha values
    def flash_step(step):
        if step >= 6:  # 3 flashes (on-off-on-off-on-off)
            error_label.pack_forget()  # Hide the error label
            return
        
        if step % 2 == 0:
            error_label.configure(fg_color=DARK_THEME["error_color"])
        else:
            error_label.configure(fg_color=DARK_THEME["bg_color"])
        
        root.after(300, lambda: flash_step(step + 1))
    
    flash_step(0)

def celebrate_win():
    """Celebrate winning the game with a special effect"""
    win_popup = ctk.CTkToplevel(root)
    win_popup.geometry("500x400")
    win_popup.title("🎉 CONGRATULATIONS! 🎉")
    win_popup.transient(root)
    win_popup.grab_set()
    
    # Confetti-like animation
    canvas = tk.Canvas(win_popup, bg="#1a1a1a", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    
    # Create confetti particles
    particles = []
    colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
    
    for _ in range(50):
        x = random.randint(0, 500)
        y = random.randint(-100, 0)
        size = random.randint(5, 15)
        color = random.choice(colors)
        
        particle = canvas.create_rectangle(x, y, x+size, y+size, fill=color, outline="")
        vx = random.uniform(-2, 2)
        vy = random.uniform(2, 5)
        
        particles.append((particle, vx, vy))
    
    # Congratulations text
    canvas.create_text(250, 150, text=f"You Won in {moves} Moves!", 
                      font=("Arial", 24, "bold"), fill="white")
    
    if game_stats["best_score"] == moves:
        canvas.create_text(250, 200, text="New Best Score!", 
                          font=("Arial", 18), fill="#ffd700")
    
    def animate_particles():
        for i, (particle, vx, vy) in enumerate(particles):
            canvas.move(particle, vx, vy)
            x1, y1, x2, y2 = canvas.coords(particle)
            
            # Reset particles that fall off the screen
            if y1 > 400:
                canvas.coords(particle, 
                             random.randint(0, 500), 
                             random.randint(-100, 0),
                             random.randint(0, 500) + (x2-x1), 
                             random.randint(-100, 0) + (y2-y1))
        
        # Continue animation
        win_popup.after(30, animate_particles)
    
    animate_particles()
    
    # Add buttons to give user choice
    button_frame = ctk.CTkFrame(win_popup, fg_color="transparent")
    button_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.8)
    
    # Button to start a new game
    new_game_btn = ctk.CTkButton(button_frame, text="New Game", 
                              command=lambda: [win_popup.destroy(), start_game()])
    new_game_btn.pack(side="left", padx=10, expand=True)
    
    # Button to just close the popup and return to the current game state
    close_btn = ctk.CTkButton(button_frame, text="Close", 
                           command=win_popup.destroy)
    close_btn.pack(side="right", padx=10, expand=True)

def show_game_completed_popup(message):
    """Show a simpler, theme-consistent completion popup"""
    win_popup = ctk.CTkToplevel(root)
    win_popup.geometry("400x350")
    win_popup.title("🎉 Congratulations! 🎉")
    win_popup.transient(root)
    win_popup.grab_set()
    
    # Create a frame with the same dark theme and a nice border
    main_frame = ctk.CTkFrame(win_popup, border_width=2, border_color=DARK_THEME["warning_color"])
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Trophy icon (using emoji as a simple solution)
    trophy_label = ctk.CTkLabel(main_frame, text="🏆", font=("Arial", 48))
    trophy_label.pack(pady=(20, 0))
    
    # Congratulations message
    ctk.CTkLabel(main_frame, text="🎉 CONGRATULATIONS! 🎉", 
               font=("Arial", 20, "bold")).pack(pady=(10, 5))
    
    # Game results message
    ctk.CTkLabel(main_frame, text=message, 
               font=("Arial", 16)).pack(pady=5)
    
    # Best score message if applicable
    if game_stats["best_score"] == moves:
        ctk.CTkLabel(main_frame, text="✨ New Best Score! ✨", 
                   font=("Arial", 16, "bold"), 
                   text_color=DARK_THEME["warning_color"]).pack(pady=5)
    
    # Path length information
    path_length = len(word_path) - 1  # Subtract 1 to get number of moves
    ctk.CTkLabel(main_frame, text=f"Your path: {' → '.join(word_path)}", 
               font=("Arial", 12), wraplength=350).pack(pady=(10, 20))
    
    # Buttons frame
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill="x", pady=10)
    
    # New game button
    new_game_btn = ctk.CTkButton(button_frame, text="🎮 New Game", 
                              fg_color=DARK_THEME["success_color"],
                              hover_color="#1e5c22",
                              font=("Arial", 14, "bold"),
                              command=lambda: [win_popup.destroy(), start_game()])
    new_game_btn.pack(side="left", padx=10, expand=True)
    
    # Close button
    close_btn = ctk.CTkButton(button_frame, text="✓ Close", 
                           fg_color=DARK_THEME["accent_color"],
                           hover_color="#155485",
                           font=("Arial", 14, "bold"),
                           command=win_popup.destroy)
    close_btn.pack(side="right", padx=10, expand=True)

# Main Game Panel Layout
def create_game_ui():
    global game_controls, left_panel, right_panel
    global lbl_current, lbl_target, lbl_moves, entry_word
    global btn_submit, btn_start, constraints_label, hint_label
    global error_label, graph_canvas, current_figure
    global btn_compare, btn_custom, btn_stats

    # Create a two-panel layout with specific weights
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Configure the main_frame to use grid instead of pack for better control
    main_frame.grid_columnconfigure(0, weight=1)  # Left panel
    main_frame.grid_columnconfigure(1, weight=1)  # Right panel
    main_frame.grid_rowconfigure(0, weight=1)

    # Left Panel - Game Controls (exactly half the width)
    left_panel = ctk.CTkFrame(main_frame, 
                           fg_color=DARK_THEME["bg_color"],
                           border_width=1,
                           border_color="#404040",
                           corner_radius=10)
    left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # Set up a scrollable frame inside the left panel if needed
    left_panel.grid_columnconfigure(0, weight=1)  # Make content take full width
    left_panel.grid_rowconfigure(0, weight=1)  # Make content take full height

    # Create a scrollable frame to contain all left panel content
    scrollable_frame = ctk.CTkScrollableFrame(left_panel, 
                                           label_text="Word Ladder Controls",
                                           label_font=("Arial", 14, "bold"),
                                           label_fg_color=DARK_THEME["bg_color"],
                                           border_width=1,
                                           border_color="#404040",
                                           corner_radius=8)
    scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # Game Controls (Inside scrollable frame)
    game_controls = ctk.CTkFrame(scrollable_frame)
    game_controls.pack(fill="x", padx=5, pady=5)

    # Game title
    title_label = ctk.CTkLabel(game_controls, text="🎮 Word Ladder Adventure", 
                            font=("Arial", 24, "bold"), 
                            text_color=DARK_THEME["text_color"])
    title_label.pack(pady=(5, 10))

    # MOVED: Game Mode Selection to top with themed styling
    mode_frame = ctk.CTkFrame(game_controls, 
                           fg_color=DARK_THEME["bg_color"],
                           border_width=1,
                           border_color="#3a6a8a",  # Lighter version of accent color
                           corner_radius=8)
    mode_frame.pack(fill="x", padx=5, pady=5)

    lbl_mode = ctk.CTkLabel(mode_frame, text="🎯 Game Mode:", 
                          font=("Arial", 14, "bold"),
                          text_color=DARK_THEME["text_color"])
    lbl_mode.pack(side="left", padx=10, pady=8)

    # Function to update mode info when changed
    def on_mode_change(new_mode):
        mode_info.configure(text=mode_descriptions[new_mode])
        game_mode.set(new_mode)

    mode_menu = ctk.CTkOptionMenu(mode_frame, variable=game_mode, 
                               values=["Beginner", "Advanced", "Challenge"],
                               command=on_mode_change,
                               width=140,
                               font=("Arial", 12, "bold"),
                               fg_color=DARK_THEME["accent_color"],
                               button_color=DARK_THEME["accent_color"],
                               button_hover_color="#155485",
                               dropdown_fg_color=DARK_THEME["bg_color"],
                               dropdown_hover_color="#3a3a3a",
                               dropdown_text_color=DARK_THEME["text_color"])
    mode_menu.pack(side="right", padx=10, pady=8)

    # Add a label to describe the selected mode with styled container
    mode_info_frame = ctk.CTkFrame(game_controls, 
                                fg_color=DARK_THEME["bg_color"],
                                corner_radius=5)
    mode_info_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    mode_info = ctk.CTkLabel(mode_info_frame, 
                          text=mode_descriptions["Beginner"], 
                          font=("Arial", 12, "italic"),
                          text_color=DARK_THEME["text_color"],
                          wraplength=350)
    mode_info.pack(fill="x", padx=10, pady=5)

    # MOVED: Start Game Button to top with improved styling
    btn_start = ctk.CTkButton(game_controls, text="🎮 START NEW GAME", 
                           font=("Arial", 16, "bold"), command=start_game,
                           height=40, fg_color=DARK_THEME["success_color"],
                           hover_color="#1e5c22")  # Darker shade for hover
    btn_start.pack(fill="x", padx=5, pady=(5, 15))  # Added more padding below

    # Create a separator with gradient effect
    separator1 = ctk.CTkFrame(game_controls, 
                           height=3, 
                           fg_color=DARK_THEME["accent_color"], 
                           corner_radius=0)
    separator1.pack(fill="x", padx=5, pady=10)

    # Game Status Section
    status_label = ctk.CTkLabel(game_controls, text="🎯 Game Status", 
                             font=("Arial", 16, "bold"))
    status_label.pack(pady=5)

    # Current Word and Target Display - Enhanced with border and better styling
    word_display = ctk.CTkFrame(game_controls, fg_color=DARK_THEME["bg_color"])
    word_display.pack(fill="x", padx=5, pady=3)

    # Current Word with border
    current_frame = ctk.CTkFrame(word_display, 
                              fg_color="#252525",
                              corner_radius=8)
    current_frame.pack(side="left", fill="x", expand=True, padx=5)
    ctk.CTkLabel(current_frame, text="🔤 Current Word:", 
                font=("Arial", 16)).pack(pady=5)
    lbl_current = ctk.CTkLabel(current_frame, text="", 
                            font=("Arial", 20, "bold"))
    lbl_current.pack(pady=5)

    # Target Word with border
    target_frame = ctk.CTkFrame(word_display, 
                             border_width=1, 
                             border_color="#3d834c",  # Lighter version of success color
                             fg_color="#252525",
                             corner_radius=8)
    target_frame.pack(side="right", fill="x", expand=True, padx=5)
    ctk.CTkLabel(target_frame, text="🎯 Target Word:", 
                font=("Arial", 16)).pack(pady=5)
    lbl_target = ctk.CTkLabel(target_frame, text="", 
                           font=("Arial", 20, "bold"))
    lbl_target.pack(pady=5)

    # Moves Counter with improved styling
    moves_frame = ctk.CTkFrame(game_controls, 
                            border_width=1, 
                            border_color="#cc8500",  # Lighter version of warning color
                            fg_color="#252525",
                            corner_radius=8)
    moves_frame.pack(fill="x", padx=5, pady=5)
    
    moves_label = ctk.CTkLabel(moves_frame, 
                            text="🔢 Moves:", 
                            font=("Arial", 16, "bold"),
                            text_color=DARK_THEME["text_color"])
    moves_label.pack(side="left", padx=10, pady=8)
    
    lbl_moves = ctk.CTkLabel(moves_frame, 
                          text="0", 
                          font=("Arial", 20, "bold"),
                          text_color=DARK_THEME["warning_color"])
    lbl_moves.pack(side="right", padx=10, pady=8)

    # Challenge Constraints Display with improved styling
    constraints_label = ctk.CTkLabel(game_controls, 
                                  text="", 
                                  font=("Arial", 12, "bold"),
                                  justify="left", 
                                  wraplength=350,
                                  corner_radius=8,
                                  fg_color="transparent",
                                  text_color=DARK_THEME["text_color"])
    constraints_label.pack(fill="x", padx=5, pady=5)

    # Error Message Display
    error_label = ctk.CTkLabel(game_controls, text="", 
                             font=("Arial", 12, "bold"),
                             text_color="white", fg_color="#f44336",
                             corner_radius=8)
    error_label.pack(fill="x", padx=10, pady=5)
    error_label.pack_forget()  # Initially hidden

    # Create a separator with gradient effect
    separator2 = ctk.CTkFrame(game_controls, 
                           height=3, 
                           fg_color=DARK_THEME["accent_color"], 
                           corner_radius=0)
    separator2.pack(fill="x", padx=5, pady=10)

    # Input Section with enhanced label
    input_label = ctk.CTkLabel(game_controls, 
                            text="⌨️ Make Your Move", 
                            font=("Arial", 16, "bold"),
                            text_color=DARK_THEME["text_color"])
    input_label.pack(pady=5)

    # Input for next word with improved styling
    input_frame = ctk.CTkFrame(game_controls, 
                            fg_color="#252525",
                            border_width=1,
                            border_color="#3a6a8a",  # Lighter version of accent color
                            corner_radius=8)
    input_frame.pack(fill="x", padx=5, pady=5)

    entry_word = ctk.CTkEntry(input_frame, 
                           font=("Arial", 16),
                           placeholder_text="Enter next word...",
                           height=40, 
                           corner_radius=8,
                           border_width=1,
                           border_color=DARK_THEME["accent_color"],
                           fg_color="#232323",
                           text_color=DARK_THEME["text_color"])
    entry_word.pack(fill="x", padx=10, pady=10)

    btn_submit = ctk.CTkButton(input_frame, 
                            text="✅ SUBMIT WORD", 
                            font=("Arial", 14, "bold"), 
                            command=validate_move,
                            height=40, 
                            fg_color=DARK_THEME["accent_color"],
                            hover_color="#155485")  # Darker shade for hover
    btn_submit.pack(fill="x", padx=10, pady=10)

    # Create a separator with gradient effect
    separator3 = ctk.CTkFrame(scrollable_frame, 
                           height=3, 
                           fg_color=DARK_THEME["accent_color"], 
                           corner_radius=0)
    separator3.pack(fill="x", padx=5, pady=10)

    # Hint System with improved styling
    hint_frame = ctk.CTkFrame(scrollable_frame,
                           fg_color="#252525",
                           border_width=1,
                           border_color="#cc8500",  # Lighter version of warning color
                           corner_radius=8)
    hint_frame.pack(fill="x", padx=5, pady=10)

    hint_title = ctk.CTkLabel(hint_frame, 
                           text="💡 Hint System", 
                           font=("Arial", 16, "bold"),
                           text_color=DARK_THEME["text_color"])
    hint_title.pack(pady=8)

    # Create a container for hint buttons to ensure even spacing
    hint_buttons_frame = ctk.CTkFrame(hint_frame, fg_color="transparent")
    hint_buttons_frame.pack(fill="x", padx=10, pady=5)
    
    btn_hint_bfs = ctk.CTkButton(hint_buttons_frame, 
                              text="🔍 BFS Hint", 
                              command=lambda: get_hint("BFS"),
                              width=105, 
                              height=36, 
                              font=("Arial", 12, "bold"),
                              fg_color=DARK_THEME["accent_color"],
                              hover_color="#155485",
                              corner_radius=8)
    btn_hint_bfs.pack(side="left", expand=True, padx=5, pady=5)

    btn_hint_astar = ctk.CTkButton(hint_buttons_frame, 
                                text="⭐ A* Hint", 
                                command=lambda: get_hint("A*"),
                                width=105, 
                                height=36, 
                                font=("Arial", 12, "bold"),
                                fg_color=DARK_THEME["success_color"],
                                hover_color="#1e5c22",
                                corner_radius=8)
    btn_hint_astar.pack(side="left", expand=True, padx=5, pady=5)

    btn_hint_ucs = ctk.CTkButton(hint_buttons_frame, 
                              text="🧭 UCS Hint", 
                              command=lambda: get_hint("UCS"),
                              width=105, 
                              height=36, 
                              font=("Arial", 12, "bold"),
                              fg_color=DARK_THEME["warning_color"],
                              hover_color="#cc7a00",
                              corner_radius=8)
    btn_hint_ucs.pack(side="left", expand=True, padx=5, pady=5)

    hint_label = ctk.CTkLabel(hint_frame, 
                           text="", 
                           font=("Arial", 12),
                           wraplength=350,
                           text_color=DARK_THEME["text_color"],
                           fg_color="transparent")
    hint_label.pack(pady=8, fill="x", padx=10)

    # Additional Buttons - Now at the bottom of scrollable_frame
    button_frame = ctk.CTkFrame(scrollable_frame, 
                             fg_color=DARK_THEME["bg_color"])
    button_frame.pack(fill="x", padx=5, pady=15)  # Increased padding for better spacing

    # Add a distinct header for additional options
    options_header = ctk.CTkLabel(button_frame, 
                               text="✨ Additional Options", 
                               font=("Arial", 16, "bold"), 
                               text_color=DARK_THEME["warning_color"])
    options_header.pack(pady=5)
    
    # Add a thin border to make the section stand out
    border_frame = ctk.CTkFrame(button_frame, 
                             fg_color="#252525", 
                             border_width=1, 
                             border_color="#cc8500",  # Lighter version of warning color
                             corner_radius=8)
    border_frame.pack(fill="x", padx=10, pady=5)

    # Create a container for additional buttons with more spacing
    additional_buttons_frame = ctk.CTkFrame(border_frame, fg_color="transparent")
    additional_buttons_frame.pack(fill="x", padx=10, pady=10)
    
    btn_compare = ctk.CTkButton(additional_buttons_frame, 
                             text="🔄 Compare", 
                             fg_color=DARK_THEME["warning_color"], 
                             command=compare_algorithms,
                             width=120, 
                             height=40, 
                             hover_color="#cc7a00",
                             font=("Arial", 14, "bold"),
                             corner_radius=8)
    btn_compare.pack(side="left", expand=True, padx=10, pady=10)

    btn_custom = ctk.CTkButton(additional_buttons_frame, 
                            text="🔠 Custom", 
                            command=custom_word_ladder,
                            fg_color=DARK_THEME["accent_color"],
                            width=120, 
                            height=40, 
                            hover_color="#155485",
                            font=("Arial", 14, "bold"),
                            corner_radius=8)
    btn_custom.pack(side="left", expand=True, padx=10, pady=10)

    btn_stats = ctk.CTkButton(additional_buttons_frame, 
                           text="📊 Stats", 
                            command=show_statistics,
                           fg_color=DARK_THEME["success_color"],
                           width=120, 
                           height=40, 
                           hover_color="#1e5c22",
                           font=("Arial", 14, "bold"),
                           corner_radius=8)
    btn_stats.pack(side="left", expand=True, padx=10, pady=10)

    # Right Panel - Graph Visualization (exactly half the width)
    right_panel = ctk.CTkFrame(main_frame,
                            fg_color=DARK_THEME["bg_color"],
                            border_width=1,
                            border_color="#404040",
                            corner_radius=10)
    right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    # Visualization frame inside right panel - updated with theme color
    visualization_frame = ctk.CTkFrame(right_panel,
                                    fg_color=DARK_THEME["bg_color"],
                                    border_width=1,
                                    border_color="#3a6a8a",  # Lighter version of accent color
                                    corner_radius=8)
    visualization_frame.pack(fill="both", expand=True, padx=10, pady=10)

    viz_title = ctk.CTkLabel(visualization_frame, 
                          text="🔄 Word Ladder Visualization", 
                          font=("Arial", 16, "bold"),
                          text_color=DARK_THEME["text_color"])
    viz_title.pack(pady=10)

    # Create a matplotlib figure for the graph visualization - updated with theme color
    current_figure = plt.figure(figsize=(5, 4), dpi=90)
    current_figure.patch.set_facecolor(DARK_THEME["bg_color"])  # Use theme background color
    
    # Create a titled frame for the visualization area
    viz_container = ctk.CTkFrame(visualization_frame, 
                              fg_color="transparent")
    viz_container.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Create the graph frame with improved styling - updated with theme color
    graph_frame = ctk.CTkFrame(viz_container,
                            fg_color=DARK_THEME["bg_color"],  # Use theme background
                            border_width=1,
                            border_color="#3a6a8a",
                            corner_radius=8)
    graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Use a dark-themed canvas for the graph - updated with theme color
    canvas_widget = tk.Frame(graph_frame, bg=DARK_THEME["bg_color"])
    canvas_widget.pack(fill="both", expand=True, padx=5, pady=5)
    graph_canvas = FigureCanvasTkAgg(current_figure, master=canvas_widget)
    graph_canvas.draw()
    graph_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Add a note about the graph visualization
    graph_note = ctk.CTkLabel(visualization_frame, 
                           text="Hover over nodes to see words. The legend shows different node types.",
                           font=("Arial", 10),
                           text_color="#aaaaaa",
                           justify="center")
    graph_note.pack(pady=(0, 5))

# Define these functions BEFORE root.mainloop() is called
def clear_graph():
    """Clear the visualization graph"""
    global current_figure, current_animation
    
    # Stop any existing animation
    if current_animation:
        current_animation.event_source.stop()
        current_animation = None
    
    # Clear previous figure if it exists
    if current_figure is not None:
        current_figure.clear()
        ax = current_figure.add_subplot(111)
        # Use consistent theme background color
        bg_color = DARK_THEME["bg_color"]
        ax.set_facecolor(bg_color)
        current_figure.patch.set_facecolor(bg_color)
        
        # Create a nicer message with better styling
        ax.text(0.5, 0.5, "Start a game to view the word graph", 
               horizontalalignment='center', 
               verticalalignment='center',
               transform=ax.transAxes, 
               color='white', 
               fontsize=14,
               fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.6", fc="#333333", ec="#555555", alpha=0.8))
               
        ax.axis('off')
        current_figure.tight_layout()
        graph_canvas.draw()

def safe_update_embedded_graph(start, target, path=None, animated=False):
    """Error-catching wrapper for graph updates"""
    try:
        update_embedded_graph(start, target, path, animated)
    except Exception as e:
        print(f"Graph update error: {e}")
        # Fallback to simple display without animation
        try:
            update_embedded_graph(start, target, path, False)
        except Exception as e2:
            print(f"Critical graph error: {e2}")

def initialize_ui():
    """Initialize the UI without starting a game"""
    # Just set up the UI with empty values
    lbl_current.configure(text="")
    lbl_target.configure(text="")
    lbl_moves.configure(text="0")
    clear_graph()
    
    # Update the welcome message
    constraints_label.configure(text="Welcome to Word Ladder Adventure! Select a game mode and click 'Start Game' to begin.")

# Call the setup_dark_theme function during initialization (just for global theme)
setup_dark_theme()

# Create the main UI
create_game_ui()

# Add a keyboard binding for the entry widget to submit when Enter is pressed
def on_entry_return(event):
    validate_move()
    return "break"  # Prevents the default behavior

entry_word.bind("<Return>", on_entry_return)

# Now that all UI elements are created, apply the theme
try:
    apply_theme_to_elements()
except Exception as e:
    print(f"Error applying theme: {e}")

# Initialize the UI with empty values
initialize_ui()

def visualize_algorithm_graph(start, target, algo_name, visited_nodes, path):
    """
    Visualize the graph explored by a specific algorithm, highlighting the path found.
    This function creates a new popup window with a graph showing nodes visited by the algorithm.
    """
    # Create a new popup window for the graph visualization
    graph_popup = ctk.CTkToplevel(root)
    graph_popup.geometry("800x600")
    graph_popup.title(f"{algo_name} Search Visualization")
    graph_popup.transient(root)
    graph_popup.grab_set()
    
    # Create header explaining what's shown
    if algo_name == "BFS":
        color = DARK_THEME["accent_color"]
        explanation = "BFS explores all nodes at the current depth before moving to the next level."
        formula = "BFS prioritizes by g(n) = depth (path length)"
    elif algo_name == "A*":
        color = DARK_THEME["success_color"]
        explanation = "A* prioritizes paths that minimize g(n) + h(n), often finding optimal paths more efficiently."
        formula = "A* prioritizes by f(n) = g(n) + h(n)"
    else:  # UCS
        color = DARK_THEME["warning_color"]
        explanation = "UCS explores nodes in order of path cost, guaranteeing the shortest path."
        formula = "UCS prioritizes by f(n) = g(n) only"
    
    header_frame = ctk.CTkFrame(graph_popup)
    header_frame.pack(fill="x", padx=10, pady=10)
    
    title_label = ctk.CTkLabel(header_frame, text=f"{algo_name} Search Graph Visualization", 
                            font=("Arial", 16, "bold"),
                            text_color="white",
                            fg_color=color,
                            corner_radius=8)
    title_label.pack(pady=5)
    
    desc_label = ctk.CTkLabel(header_frame, text=explanation, font=("Arial", 12))
    desc_label.pack(pady=5)
    
    formula_label = ctk.CTkLabel(header_frame, text=formula, 
                              font=("Arial", 12, "bold"),
                              text_color="#ffcc00")  # Gold color
    formula_label.pack(pady=5)
    
    stats_label = ctk.CTkLabel(header_frame, 
                            text=f"Nodes explored: {len(visited_nodes)} | Path length: {len(path)-1} steps",
                            font=("Arial", 12))
    stats_label.pack(pady=5)
    
    # Create frame for the graph
    graph_container = ctk.CTkFrame(graph_popup, fg_color=DARK_THEME["bg_color"])
    graph_container.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create matplotlib figure
    fig = plt.figure(figsize=(6, 5), dpi=100)
    fig.patch.set_facecolor(DARK_THEME["bg_color"])
    
    # Create subgraph of visited nodes
    subgraph = nx.Graph()
    
    # Add all visited nodes to the graph
    for word in visited_nodes:
        subgraph.add_node(word)
    
    # Add edges between neighboring words
    for word in visited_nodes:
        for neighbor in get_word_neighbors(word, word_list):
            if neighbor in visited_nodes:
                subgraph.add_edge(word, neighbor)
    
    ax = fig.add_subplot(111)
    ax.set_facecolor(DARK_THEME["bg_color"])
    
    # Layout adjustments based on graph size
    if len(visited_nodes) < 50:
        pos = nx.spring_layout(subgraph, seed=42)
    else:
        # For larger graphs, use fast layout
        pos = nx.fruchterman_reingold_layout(subgraph, seed=42)
    
    # Define node groups
    path_nodes = set(path[1:-1])  # Path nodes excluding start/target
    unexplored = set(word_list) - visited_nodes  # All unvisited nodes
    
    regular_nodes = visited_nodes - {start, target} - path_nodes
    
    # Draw regular visited nodes
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=list(regular_nodes), 
                        node_size=350,
                        node_color="#555555",
                        alpha=0.7,
                        edgecolors="#777777")
    
    # Draw edges with better visibility
    nx.draw_networkx_edges(subgraph, pos, ax=ax, 
                        width=1.0,
                        edge_color="#666666",
                        alpha=0.7)
    
    # Draw path edges with animation
    if path and len(path) > 1:
        path_edges = list(zip(path, path[1:]))
        
        # Draw path nodes
        nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                            nodelist=list(path_nodes), 
                            node_size=450,
                            node_color="#3584e4",
                            edgecolors="#66a5ff")
        
        # Draw path edges with better visibility
        nx.draw_networkx_edges(subgraph, pos, ax=ax, 
                            edgelist=path_edges, 
                            width=3.0,
                            edge_color="#ffaa33",
                            arrows=True,
                            arrowsize=15,
                            connectionstyle="arc3,rad=0.15")
    
    # Highlight start node
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=[start], 
                        node_size=550,
                        node_color="#2ecc71",
                        edgecolors="#87f5b3")
                        
    # Highlight target node
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, 
                        nodelist=[target], 
                        node_size=550,
                        node_color="#e74c3c",
                        edgecolors="#ff8b81")
    
    # Add labels to nodes, but only for a reasonable number of nodes
    if len(visited_nodes) < 30:
        # Create labels for all nodes
        labels = {node: node for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, 
                              labels=labels, 
                              font_size=9,
                              font_color="white",
                              font_weight="bold")
    else:
        # If too many nodes, only label key nodes
        key_nodes = {start, target} | set(path)
        labels = {node: node for node in key_nodes}
        nx.draw_networkx_labels(subgraph, pos, 
                              labels=labels, 
                              font_size=9,
                              font_color="white",
                              font_weight="bold")
    
    # Set title and hide axis
    ax.set_title(f"{algo_name} Search Path", color="white", fontsize=14)
    ax.axis('off')
    
    # Create canvas
    canvas_widget = tk.Frame(graph_container, bg=DARK_THEME["bg_color"])
    canvas_widget.pack(fill="both", expand=True, padx=5, pady=5)
    
    canvas = FigureCanvasTkAgg(fig, master=canvas_widget)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Create legend with color explanations
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#2ecc71", markeredgecolor="#87f5b3", 
                  markersize=12, markeredgewidth=2, label='Start Word'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#e74c3c", markeredgecolor="#ff8b81", 
                  markersize=12, markeredgewidth=2, label='Target Word'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#3584e4", markeredgecolor="#66a5ff", 
                  markersize=12, markeredgewidth=2, label='Path Words'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#555555", markeredgecolor="#777777", 
                  markersize=12, markeredgewidth=2, label='Explored Words'),
        plt.Line2D([0], [0], color="#ffaa33", lw=3, label='Final Path')
    ]
    
    legend = ax.legend(handles=legend_elements, 
                      loc='upper right',
                      fontsize=9,
                      frameon=True,
                      framealpha=0.9,
                      facecolor='#222222',
                      edgecolor='#555555',
                      title=f"{algo_name} Legend")
    
    legend.get_title().set_color('#ffcc00')
    for text in legend.get_texts():
        text.set_color('white')
    
    # Add close button at the bottom
    close_btn = ctk.CTkButton(graph_popup, 
                           text="Close", 
                           command=graph_popup.destroy,
                           fg_color=DARK_THEME["accent_color"],
                           hover_color="#155485",
                           font=("Arial", 12, "bold"),
                           height=36)
    close_btn.pack(pady=10)

# Start the main event loop - THIS IS A BLOCKING CALL
# Code after this line won't execute until the application is closed
root.mainloop()
