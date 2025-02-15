import networkx as nx
import heapq
from collections import deque
from word_loader import load_words_from_pickle

def is_valid_transformation(word1, word2):
    """
    Check if two words differ by only one letter.
    """
    if len(word1) != len(word2):
        return False  # Words must be of the same length
    differences = sum(1 for a, b in zip(word1, word2) if a != b)
    return differences == 1  # True if only one letter differs

def get_valid_transformations(word, word_list):
    """
    Find all words in the word list that are valid transformations of the given word.
    """
    return {w for w in word_list if is_valid_transformation(word, w)}

def build_graph_optimized(word_list):
    """
    Construct a graph where words are nodes, and edges exist between words 
    that can be transformed into each other using a more efficient approach.
    """
    graph = nx.Graph()

    # Group words by length
    word_groups = {}
    for word in word_list:
        word_groups.setdefault(len(word), []).append(word)

    # Connect words that differ by one letter within the same length group
    for length, words in word_groups.items():
        for i, word in enumerate(words):
            for j in range(i + 1, len(words)):  # Compare only forward to reduce checks
                if is_valid_transformation(word, words[j]):
                    graph.add_edge(word, words[j])

    return graph

def bfs_shortest_path(start, target, word_list):
    """
    Finds the shortest path from start to target using BFS.
    Returns the path as a list of words.
    """
    if start not in word_list or target not in word_list:
        return None  # Ensure words exist

    # **Optimization: Reduce search space to words of the same length**
    word_list = {word for word in word_list if len(word) == len(start)}

    queue = deque([(start, [start])])  # (current word, path taken)
    visited = set()

    while queue:
        current_word, path = queue.popleft()

        if current_word == target:
            return path  # Return the shortest path

        visited.add(current_word)

        # Get valid transformations and explore them
        for neighbor in get_valid_transformations(current_word, word_list):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))

    return None  # No path found

def heuristic(word, target):
    """
    Heuristic function for A* search.
    Returns the number of different letters between word and target.
    """
    return sum(1 for a, b in zip(word, target) if a != b)

def a_star_search(start, target, word_list):
    """
    Finds the shortest path using A* search.
    Uses g(n) = path cost, h(n) = heuristic (letter difference).
    """
    if start not in word_list or target not in word_list:
        return None  # Ensure words exist

    # **Optimization: Reduce search space to words of the same length**
    word_list = {word for word in word_list if len(word) == len(start)}

    # Priority queue for A* search (min-heap)
    pq = [(heuristic(start, target), 0, start, [start])]  # (f(n), g(n), current_word, path)
    visited = set()

    while pq:
        _, g, current_word, path = heapq.heappop(pq)

        if current_word == target:
            return path  # Found the shortest path

        visited.add(current_word)

        for neighbor in get_valid_transformations(current_word, word_list):
            if neighbor not in visited:
                f = g + 1 + heuristic(neighbor, target)  # A* formula: f(n) = g(n) + h(n)
                heapq.heappush(pq, (f, g + 1, neighbor, path + [neighbor]))

    return None  # No path found

def ucs_shortest_path(start, target, word_list):
    """
    Finds the shortest path from start to target using Uniform Cost Search (UCS).
    Uses g(n) = actual path cost. No heuristic function.
    """
    if start not in word_list or target not in word_list:
        return None  # Ensure words exist

    # **Optimization: Reduce search space to words of the same length**
    word_list = {word for word in word_list if len(word) == len(start)}

    # Priority queue for UCS (min-heap)
    pq = [(0, start, [start])]  # (cost, current_word, path)
    visited = set()

    while pq:
        g, current_word, path = heapq.heappop(pq)

        if current_word == target:
            return path  # Found the shortest path

        visited.add(current_word)

        for neighbor in get_valid_transformations(current_word, word_list):
            if neighbor not in visited:
                heapq.heappush(pq, (g + 1, neighbor, path + [neighbor]))

    return None  # No path found

if __name__ == "__main__":
    word_list = load_words_from_pickle()
    
    # **Use only a subset of words (Optional)**
    word_list = set(list(word_list)[:10000])  # Limit to 10,000 words for quick testing

    print(f"Building graph for {len(word_list)} words...")
    word_graph = build_graph_optimized(word_list)
    print(f"Graph created with {len(word_graph.nodes)} nodes and {len(word_graph.edges)} edges.")

    # Example BFS Test
    start_word = "cat"
    target_word = "dog"
    
    bfs_path = bfs_shortest_path(start_word, target_word, word_list)
    if bfs_path:
        print(f"BFS Shortest Path from '{start_word}' to '{target_word}': {bfs_path}")
    else:
        print(f"No BFS path found from '{start_word}' to '{target_word}'.")

    a_star_path = a_star_search(start_word, target_word, word_list)
    if a_star_path:
        print(f"A* Shortest Path from '{start_word}' to '{target_word}': {a_star_path}")
    else:
        print(f"No A* path found from '{start_word}' to '{target_word}'.")

    ucs_path = ucs_shortest_path(start_word, target_word, word_list)
    if ucs_path:
        print(f"UCS Shortest Path from '{start_word}' to '{target_word}': {ucs_path}")
    else:
        print(f"No UCS path found from '{start_word}' to '{target_word}'.")
