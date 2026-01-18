import tkinter as tk
from tkinter import font

# Create the main window
root = tk.Tk()
root.title("Khmer Language Entry")
root.geometry("400x150")

# --- Set up the Khmer font ---
# Replace 'Khmer OS Battambang' with the exact name of the font you installed.
try:
    khmer_font = font.Font(family="Khmer (NIDA)", size=14)
except tk.TclError:
    print("Could not find the font 'Khmer OS Battambang'. Please install a Khmer font.")
    # Fallback to a generic font that might not work
    khmer_font = font.Font(family="Arial", size=14)

# --- Create the Tkinter Entry widget with the specified font ---
entry_label = tk.Label(root, text="Please enter your name in Khmer:", font=khmer_font)
entry_label.pack(pady=10)

name_entry = tk.Entry(root, font=khmer_font, width=30)
name_entry.pack(pady=5)

# Optional: Pre-fill the entry with some Khmer text to test
name_entry.insert(0, "សួស្តីពិភពលោក") # "Hello World" in Khmer

# Run the application
root.mainloop()