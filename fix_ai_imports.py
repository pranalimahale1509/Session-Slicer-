"""
Script to fix sessionslice_modern.py by removing duplicate AI class definitions
"""

# Read the file
with open('sessionslice_modern.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the import line
import_line_idx = None
for i, line in enumerate(lines):
    if 'from ai_assistant import AIAssistant, ProductivityChatbot' in line:
        import_line_idx = i
        break

# Find the real ChatWindow class (the one with proper __init__)
real_chatwindow_idx = None
for i in range(len(lines) - 1, -1, -1):  # Search from end
    if 'class ChatWindow(tk.Toplevel):' in lines[i]:
        # Check if next few lines have the correct __init__
        if i + 2 < len(lines) and 'def __init__(self, parent, chatbot):' in lines[i + 2]:
            real_chatwindow_idx = i
            break

if import_line_idx and real_chatwindow_idx:
    # Keep everything before import + 2 lines (import and blank line)
    # Then skip to real ChatWindow
    new_lines = lines[:import_line_idx + 2] + lines[real_chatwindow_idx:]
    
    # Write back
    with open('sessionslice_modern.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ File fixed successfully!")
    print(f"Removed lines {import_line_idx + 2} to {real_chatwindow_idx - 1}")
else:
    print("❌ Could not find required markers in file")
    print(f"Import line: {import_line_idx}, Real ChatWindow: {real_chatwindow_idx}")
