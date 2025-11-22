from googletrans import Translator

# Initialize translator
translator = Translator()

text = "Hello, how are you?"

# Translate to Vietnamese
translation = translator.translate(text, src='en', dest='vi')

# Print result
print("Original:", text)
print("Translated:", translation.text)