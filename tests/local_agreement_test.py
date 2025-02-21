import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from speech_to_text.local_agreement import LocalAgreement

def print_transcription_details(index, transcription, result, agreement):
    print(f"\n=== Transcription {index} ===")
    print(f"Input: '{transcription}'")
    print(f"Newly confirmed words: '{result}'")
    print(f"Last confirmed index: {agreement.last_confirmed_position}")
    print(f"Words at confirmed positions: {transcription.split()[:agreement.last_confirmed_position + 1]}")
    print("-" * 50)

agreement = LocalAgreement()

# First transcription
result = agreement.process_transcription("The way the way forw")
print_transcription_details(1, "The way the way forw", result, agreement)

# Second transcription
result = agreement.process_transcription("The way the way forward is clear")
print_transcription_details(2, "The way the way forward is clear", result, agreement)

# Third transcription
result = agreement.process_transcription("A way way forward is clear and the way is long")
print_transcription_details(3, "A way way forward is clear and the way is long", result, agreement)

# Fourth transcription
result = agreement.process_transcription("A way the way forward is clear and the way is long for me too die")
print_transcription_details(4, "A way the way forward is clear and the way is long for me too die", result, agreement)

# Fifth transcription
result = agreement.process_transcription("A way the way forward is clear and the way is long for me too die meow")
print_transcription_details(5, "A way the way forward is clear and the way is long for me too die meow", result, agreement)

# Sixth transcription
result = agreement.process_transcription("A way the way forward is clear and the way is long for me too die meow TEST PASSED")
print_transcription_details(6, "A way the way forward is clear and the way is long for me too die meow TEST PASSED", result, agreement)

# transcription_split = agreement.transcription_history[-1].split()
# last_word = len(agreement.transcription_history[-1])
# print(transcription_split)
# final_unconfirmed_words = transcription_split[agreement.last_confirmed_position+1:last_word]

# print(' '.join(final_unconfirmed_words))

agreement.reset_history()

print(agreement.process_transcription("Technology has revolutionized the way we live."))
print(agreement.process_transcription("Technology has revolutionized the way we live and work, transforming industries, economies, and societies in profound ways."))
print(agreement.process_transcription("Technology has revolutionized the way we live and work, transforming industries, economies, and societies in profound ways, from artificial intelligence and machine learning."))
print(agreement.process_transcription("Technology has revolutionized the way we live and work, transforming industries, economies, and societies in profound ways, from artificial intelligence and machine learning to advanced robotics and automation."))



