import pickle
import os

# Dictionary to cache words by length
_words_by_length = {}

def load_filtered_dictionary(filename, min_length=3, max_length=8):
    """
    Load words from a text file and filter them by length.
    Only words between min_length and max_length are kept.
    """
    with open(filename, 'r') as file:
        words = {word.strip().lower() for word in file if min_length <= len(word.strip()) <= max_length}
    return words


def save_filtered_words(word_list, output_filename="filtered_words.pkl"):
    """
    Save the filtered words into a pickle file for faster future access.
    """
    with open(output_filename, "wb") as f:
        pickle.dump(word_list, f)
    print(f"Filtered word list saved to {output_filename}.")

def load_words_from_pickle(file_path="filtered_words.pkl"):
    """Load words from pickle file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                words = pickle.load(f)
                print(f"Loaded {len(words)} words from {file_path}.")
                return words
        else:
            print(f"File {file_path} not found.")
            return set()
    except Exception as e:
        print(f"Error loading words: {e}")
        return set()

def get_words_by_length(length):
    """Efficiently retrieve only words of specified length"""
    global _words_by_length
    
    # If we've already filtered words of this length, return them
    if length in _words_by_length:
        return _words_by_length[length]
    
    # Load all words
    all_words = load_words_from_pickle()
    
    # Filter to only words of the specified length
    filtered_words = {word for word in all_words if len(word) == length}
    
    # Cache for future use
    _words_by_length[length] = filtered_words
    
    print(f"Filtered {len(filtered_words)} words of length {length}")
    return filtered_words

if __name__ == "__main__":
    input_file = "words_alpha.txt"  # Ensure this file exists in your project folder
    output_file = "filtered_words.pkl"

    # Step 1: Load and filter words
    word_list = load_filtered_dictionary(input_file)

    # Step 2: Save filtered words for future use
    save_filtered_words(word_list, output_file)

    # Step 3: Load words from pickle to verify
    loaded_words = load_words_from_pickle(output_file)
