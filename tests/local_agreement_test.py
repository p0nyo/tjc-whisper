import time
from collections import Counter

# Example: Simulated real-time transcriptions from multiple models
# Each item represents a chunk of transcription received in real-time
real_time_transcriptions = [
    "The quick brown fox",
    "The quick brown fox jumped over",
    "The quick brown fox jumped over the lazy dog",
    "The quick brown fox jumped over the lazy dog while a bright blue butterfly flew by",
    "The quick brown fox jumped over the lazy dog while a bright blue butterfly fluttered past",
    "The quick brown fox jumped over the lazy dog while a bright blue butterfly fluttered past. Nearby, a group of children were playing soccer."
]

# A simple function to apply local agreement in real-time
def real_time_local_agreement(new_transcription, previous_transcriptions):
    """
    Applies local agreement algorithm to reconcile new transcription with previous transcriptions.
    We assume that each transcription chunk is a sentence or a portion of it.
    """
    # Combine the new transcription with previous ones
    all_transcriptions = previous_transcriptions + [new_transcription]
    
    # Split transcriptions into words (tokenize)
    tokenized_transcriptions = [t.split() for t in all_transcriptions]

    # Initialize the final transcription (list of words)
    final_transcription = []

    # For each word position, perform majority vote or consensus
    max_length = max(len(t) for t in tokenized_transcriptions)
    for i in range(max_length):
        words_at_i = [t[i] for t in tokenized_transcriptions if i < len(t)]  # Avoid index out of range

        # If there are multiple words (disagreement), apply majority vote
        word_count = Counter(words_at_i)
        most_common_word = word_count.most_common(1)[0][0]

        # Add the agreed word to final transcription
        final_transcription.append(most_common_word)

    # Join the final transcription into a single string
    return " ".join(final_transcription)

# Real-time simulation: Process each transcription chunk
previous_transcriptions = []

for transcription in real_time_transcriptions:
    # Apply local agreement on each new chunk of transcription
    final_transcription = real_time_local_agreement(transcription, previous_transcriptions)

    # Output the agreed transcription in real-time (after processing each chunk)
    print(f"Updated Transcription: {final_transcription}")

    # Append the current transcription to the list of previous transcriptions
    previous_transcriptions.append(transcription)

    # Simulate delay to represent real-time processing (e.g., waiting for new audio)
    time.sleep(1)  # Adjust the sleep time based on your real-time streaming

