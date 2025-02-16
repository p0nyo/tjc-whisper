from collections import Counter

class LocalAgreement:
    def __init__(self, history_size=5):
        self.transcription_history = []
        self.history_size = history_size
        self.confirmed_positions = {}
        self.last_confirmed_position = -1  # Track the last position we confirmed

    def process_transcription(self, new_transcription: str) -> str:
        # print("\n=== Processing New Transcription ===")
        # print(f"Input: '{new_transcription}'")
        
        # Add new transcription to history
        self.transcription_history.append(new_transcription)
        if len(self.transcription_history) > self.history_size:
            self.transcription_history.pop(0)
            
        # If this is the first transcription, nothing to confirm
        if len(self.transcription_history) == 1:
            return ""
            
        # Get the previous transcription for comparison
        previous_trans = self.transcription_history[-2]
        previous_words = previous_trans.split()
        current_words = new_transcription.split()
        
        newly_confirmed = []
        start_checking = self.last_confirmed_position + 1
        
        # Find matching subsequences starting from last confirmed position
        i = start_checking
        while i < len(current_words) and i < len(previous_words):
            if current_words[i].lower() == previous_words[i].lower():
                if not self.is_position_confirmed(current_words[i].lower(), i, new_transcription):
                    newly_confirmed.append(current_words[i])
                    self.mark_position_confirmed(current_words[i].lower(), i, new_transcription)
                    self.last_confirmed_position = i
                i += 1
            else:
                break
                
        result = ' '.join(newly_confirmed)
        # print(f"\nNewly confirmed words: '{result}'")
        return result

    def is_position_confirmed(self, word: str, position: int, transcription: str) -> bool:
        if word not in self.confirmed_positions:
            return False
        return any(pos == position and trans == transcription 
                  for trans, pos in self.confirmed_positions[word])
    
    def mark_position_confirmed(self, word: str, position: int, transcription: str):
        if word not in self.confirmed_positions:
            self.confirmed_positions[word] = []
        self.confirmed_positions[word].append((transcription, position))

    def reset_history(self):
        self.transcription_history.clear()
        self.confirmed_positions.clear()
        
        last_transcription_split = self.transcription_history[-1].split()
        last_word_index = len(last_transcription_split)
        final_unconfirmed_words = last_transcription_split[self.last_confirmed_position+1:last_word_index]

        print(final_unconfirmed_words)

        self.last_confirmed_position = -1
        


