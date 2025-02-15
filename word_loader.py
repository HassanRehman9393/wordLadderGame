import pickle

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

def load_words_from_pickle(filename="filtered_words.pkl"):
    """
    Load words from a pickle file if it exists.
    """
    try:
        with open(filename, "rb") as f:
            words = pickle.load(f)
        print(f"Loaded {len(words)} words from {filename}.")
        return words
    except FileNotFoundError:
        print(f"File {filename} not found. Run the script to generate it first.")
        return set()

if __name__ == "__main__":
    input_file = "words_alpha.txt"  # Ensure this file exists in your project folder
    output_file = "filtered_words.pkl"

    # Step 1: Load and filter words
    word_list = load_filtered_dictionary(input_file)

    # Step 2: Save filtered words for future use
    save_filtered_words(word_list, output_file)

    # Step 3: Load words from pickle to verify
    loaded_words = load_words_from_pickle(output_file)
