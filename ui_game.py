import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
import threading
import time
from word_loader import load_words_from_pickle
from word_graph import bfs_shortest_path, a_star_search, ucs_shortest_path

# Load words
word_list = load_words_from_pickle()
word_graph = nx.Graph()

# Setup Main Game Window
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

root = ctk.CTk()
root.title("Word Ladder Adventure")
root.geometry("800x600")
root.resizable(False, False)

# Game Variables
current_word = tk.StringVar()
target_word = tk.StringVar()
game_mode = tk.StringVar(value="Beginner")
moves = 0

# Game Modes
GAME_MODES = {
    "Beginner": [("cat", "big"), ("dog", "log"), ("bat", "fat")],
    "Advanced": [("stone", "money"), ("plane", "crane"), ("flame", "grape")],
    "Challenge": [("magic", "space"), ("smoke", "flame"), ("beach", "shark")]
}

def start_game():
    global moves
    moves = 0

    mode = game_mode.get()
    start, target = GAME_MODES[mode][0]  

    current_word.set(start)
    target_word.set(target)

    lbl_current.configure(text=f"🔵 Current Word: {start}")
    lbl_target.configure(text=f"🎯 Target Word: {target}")
    lbl_moves.configure(text="Moves: 0")

    show_popup("Game Started!", f"Transform '{start}' to '{target}' by changing one letter at a time.")

def validate_move():
    global moves
    next_word = entry_word.get().strip().lower()

    if len(next_word) != len(current_word.get()):
        show_popup("Invalid Move!", "Words must be of the same length.")
        return

    if next_word not in word_list:
        show_popup("Invalid Move!", "This word is not in the dictionary.")
        return

    if sum(1 for a, b in zip(current_word.get(), next_word) if a != b) != 1:
        show_popup("Invalid Move!", "Words must differ by only one letter.")
        return

    current_word.set(next_word)
    lbl_current.configure(text=f"🔵 Current Word: {next_word}")
    moves += 1
    lbl_moves.configure(text=f"Moves: {moves}")

    if next_word == target_word.get():
        show_popup("🎉 Game Over!", f"🎉 Congratulations! You won in {moves} moves!")
        start_game()

def get_hint(algorithm):
    show_loading_screen("Finding Best Move...")
    
    def fetch_hint():
        time.sleep(1.5)  
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
            show_popup("AI Hint", f"🔍 Next best move ({algorithm}): {path[1]}")
            visualize_word_ladder(start, target, path)
        else:
            show_popup("Hint Failed", "No valid path found!")

    threading.Thread(target=fetch_hint).start()

def visualize_word_ladder(start, target, path=None):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(word_graph)  
    nx.draw(word_graph, pos, with_labels=True, node_size=700, node_color="gray", edge_color="gray")

    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(word_graph, pos, nodelist=path, node_size=900, node_color="orange")
        nx.draw_networkx_edges(word_graph, pos, edgelist=path_edges, width=3, edge_color="red")

    plt.title(f"Word Ladder: {start} → {target}")
    plt.show()

def show_popup(title, message):
    popup = ctk.CTkToplevel(root)
    popup.geometry("400x200")
    popup.title(title)
    popup.transient(root)
    popup.grab_set()  

    lbl_popup = ctk.CTkLabel(popup, text=message, font=("Arial", 14), wraplength=350, justify="center")
    lbl_popup.pack(pady=20)

    btn_close = ctk.CTkButton(popup, text="OK", command=popup.destroy)
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

# UI Layout
frame = ctk.CTkFrame(root)
frame.pack(pady=20, padx=20, fill="both", expand=True)

lbl_title = ctk.CTkLabel(frame, text="🔠 Word Ladder Adventure", font=("Arial", 24, "bold"))
lbl_title.pack(pady=10)

lbl_mode = ctk.CTkLabel(frame, text="Select Game Mode:", font=("Arial", 14))
lbl_mode.pack()

mode_menu = ctk.CTkOptionMenu(frame, variable=game_mode, values=["Beginner", "Advanced", "Challenge"])
mode_menu.pack(pady=5)

btn_start = ctk.CTkButton(frame, text="▶ Start Game", command=start_game)
btn_start.pack(pady=5)

lbl_current = ctk.CTkLabel(frame, text="🔵 Current Word: ", font=("Arial", 14))
lbl_current.pack(pady=5)

lbl_target = ctk.CTkLabel(frame, text="🎯 Target Word: ", font=("Arial", 14))
lbl_target.pack(pady=5)

lbl_moves = ctk.CTkLabel(frame, text="Moves: 0", font=("Arial", 14))
lbl_moves.pack(pady=5)

entry_word = ctk.CTkEntry(frame, placeholder_text="Type your next word...")
entry_word.pack(pady=5)

btn_submit = ctk.CTkButton(frame, text="✔ Submit Word", command=validate_move)
btn_submit.pack(pady=5)

btn_hint_bfs = ctk.CTkButton(frame, text="🔍 Hint (BFS)", fg_color="blue", command=lambda: get_hint("BFS"))
btn_hint_bfs.pack(pady=5)

btn_hint_astar = ctk.CTkButton(frame, text="🚀 Hint (A*)", fg_color="green", command=lambda: get_hint("A*"))
btn_hint_astar.pack(pady=5)

btn_hint_ucs = ctk.CTkButton(frame, text="🧠 Hint (UCS)", fg_color="purple", command=lambda: get_hint("UCS"))
btn_hint_ucs.pack(pady=5)

root.mainloop()
