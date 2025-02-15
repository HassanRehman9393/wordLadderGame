from word_loader import load_words_from_pickle
from word_graph import is_valid_transformation, bfs_shortest_path, a_star_search, ucs_shortest_path

# Load words from the filtered word list
word_list = load_words_from_pickle()

def play_game_with_ai():
    """
    Allows the user to play the Word Ladder game with AI hints.
    """
    start = input("Enter start word: ").strip().lower()
    target = input("Enter target word: ").strip().lower()

    # Check if both words exist in the dictionary
    if start not in word_list or target not in word_list:
        print("Error: One or both words are not in the dictionary.")
        return
    
    # Ensure words are of the same length
    if len(start) != len(target):
        print("Error: Words must be of the same length.")
        return

    print(f"\nStarting game: Transform '{start}' → '{target}'")

    current_word = start
    moves = 0

    while current_word != target:
        print(f"\nCurrent word: {current_word}")
        next_word = input("Enter next word (or type 'hint' for BFS, 'astar' for A*, 'ucs' for UCS, 'exit' to quit): ").strip().lower()

        if next_word == "exit":
            print("Game exited.")
            return
        
        if next_word == "hint":
            ai_path = bfs_shortest_path(current_word, target, word_list)
            if ai_path:
                print(f"Hint (BFS): Next suggested move is '{ai_path[1]}'")
            else:
                print("No valid path found!")
            continue

        if next_word == "astar":
            ai_path = a_star_search(current_word, target, word_list)
            if ai_path:
                print(f"Hint (A*): Next suggested move is '{ai_path[1]}'")
            else:
                print("No valid path found!")
            continue

        if next_word == "ucs":
            ai_path = ucs_shortest_path(current_word, target, word_list)
            if ai_path:
                print(f"Hint (UCS): Next suggested move is '{ai_path[1]}'")
            else:
                print("No valid path found!")
            continue

        # Validate the move
        if next_word not in word_list:
            print("Invalid word! Not in dictionary.")
            continue

        if not is_valid_transformation(current_word, next_word):
            print("Invalid move! Words must differ by exactly one letter.")
            continue

        # Move to the next word
        current_word = next_word
        moves += 1

    print(f"\n🎉 Congratulations! You reached '{target}' in {moves} moves.")

if __name__ == "__main__":
    play_game_with_ai()
