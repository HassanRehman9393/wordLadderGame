import networkx as nx
import heapq
from collections import deque
from word_loader import load_words_from_pickle
import time

# Cache for word transformations
_transformation_cache = {}

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
    Uses an optimized approach to avoid checking every word in the list.
    """
    # Only consider words of the same length for efficiency
    word_len = len(word)
    
    # Use the more efficient neighbor generation method
    neighbors = set()
    
    # Try changing each position to each letter
    for i in range(word_len):
        prefix = word[:i]
        suffix = word[i+1:]
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            candidate = prefix + letter + suffix
            if candidate != word and candidate in word_list:
                neighbors.add(candidate)
    
    return neighbors

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

def get_word_neighbors(word, word_list):
    """Get valid one-letter transformations with caching"""
    global _transformation_cache
    
    # Cache key is the word and the id of the word_list (since word lists change)
    cache_key = (word, id(word_list))
    
    if cache_key in _transformation_cache:
        return _transformation_cache[cache_key]
    
    # Calculate valid transformations using the optimized method
    neighbors = get_valid_transformations(word, word_list)
    
    # Store in cache
    _transformation_cache[cache_key] = neighbors
    
    return neighbors

# Optimized BFS implementation
def optimized_bfs(start, target, word_list, max_depth=15, max_iterations=10000, max_time=5.0):
    """
    Optimized BFS with depth limit to prevent excessive searching.
    Added timeout and iteration limit to prevent hanging.
    """
    import time
    start_time = time.time()
    
    if start == target:
        return [start]
        
    # If words aren't in the list, return immediately
    if start not in word_list or target not in word_list:
        return None
    
    visited = {start}
    queue = deque([(start, [start], 0)])  # (word, path, depth)
    iterations = 0
    
    while queue and iterations < max_iterations:
        iterations += 1
        
        # Check for timeout
        if time.time() - start_time > max_time:
            print(f"BFS search timed out after {iterations} iterations")
            return None
            
        current, path, depth = queue.popleft()
        
        # Abandon paths that are too long
        if depth > max_depth:
            continue
            
        # Get neighbors through the cached function
        for neighbor in get_word_neighbors(current, word_list):
            if neighbor == target:
                return path + [neighbor]
                
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor], depth + 1))
    
    if iterations >= max_iterations:
        print(f"BFS search reached maximum iterations ({max_iterations})")
        
    return None  # No path found

# Create an alias for backward compatibility
bfs_shortest_path = optimized_bfs

def heuristic(word, target):
    """
    Heuristic function for A* search.
    Returns the number of different letters between word and target.
    """
    return sum(1 for a, b in zip(word, target) if a != b)

def a_star_search(start, target, word_list, max_iterations=10000, max_time=5.0):
    """
    Finds the shortest path using A* search.
    Uses g(n) = path cost, h(n) = heuristic (letter difference).
    Added timeout and iteration limit to prevent hanging.
    """
    import time
    start_time = time.time()
    
    if start not in word_list or target not in word_list:
        return None  # Ensure words exist

    # **Optimization: Reduce search space to words of the same length**
    word_list = {word for word in word_list if len(word) == len(start)}

    # Priority queue for A* search (min-heap)
    pq = [(heuristic(start, target), 0, start, [start])]  # (f(n), g(n), current_word, path)
    visited = set()
    iterations = 0

    while pq and iterations < max_iterations:
        iterations += 1
        
        # Check for timeout
        if time.time() - start_time > max_time:
            print(f"A* search timed out after {iterations} iterations")
            return None
            
        _, g, current_word, path = heapq.heappop(pq)

        if current_word == target:
            return path  # Found the shortest path

        visited.add(current_word)

        for neighbor in get_valid_transformations(current_word, word_list):
            if neighbor not in visited:
                f = g + 1 + heuristic(neighbor, target)  # A* formula: f(n) = g(n) + h(n)
                heapq.heappush(pq, (f, g + 1, neighbor, path + [neighbor]))

    if iterations >= max_iterations:
        print(f"A* search reached maximum iterations ({max_iterations})")
    
    return None  # No path found

def ucs_shortest_path(start, target, word_list, max_iterations=10000, max_time=5.0):
    """
    Finds the shortest path from start to target using Uniform Cost Search (UCS).
    Uses g(n) = actual path cost. No heuristic function.
    Added timeout and iteration limit to prevent hanging.
    """
    import time
    start_time = time.time()
    
    if start not in word_list or target not in word_list:
        return None  # Ensure words exist

    # **Optimization: Reduce search space to words of the same length**
    word_list = {word for word in word_list if len(word) == len(start)}

    # Priority queue for UCS (min-heap)
    pq = [(0, start, [start])]  # (cost, current_word, path)
    visited = set()
    iterations = 0

    while pq and iterations < max_iterations:
        iterations += 1
        
        # Check for timeout
        if time.time() - start_time > max_time:
            print(f"UCS search timed out after {iterations} iterations")
            return None
            
        g, current_word, path = heapq.heappop(pq)

        if current_word == target:
            return path  # Found the shortest path

        visited.add(current_word)

        for neighbor in get_valid_transformations(current_word, word_list):
            if neighbor not in visited:
                heapq.heappush(pq, (g + 1, neighbor, path + [neighbor]))

    if iterations >= max_iterations:
        print(f"UCS search reached maximum iterations ({max_iterations})")
    
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
    
    bfs_path = optimized_bfs(start_word, target_word, word_list)
    if bfs_path:
        print(f"Optimized BFS Shortest Path from '{start_word}' to '{target_word}': {bfs_path}")
    else:
        print(f"No Optimized BFS path found from '{start_word}' to '{target_word}'.")

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


