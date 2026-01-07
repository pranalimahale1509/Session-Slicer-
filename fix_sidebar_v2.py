import os
import tkinter as tk # needed for tk.LEFT constants if used in string, but we are writing strings.
import customtkinter as ctk # not strictly needed for script execution but good practice

file_path = r"c:\Users\ADMIN\Desktop\SessionSlice - Copy\sessionslice_modern.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_sidebar_block = False
sidebar_fixed = False

for line in lines:
    if "def _create_main_widgets(self):" in line:
        new_lines.append(line)
        in_sidebar_block = True
        
        # Insert new code
        new_lines.append("        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLORS['surface'])\n")
        new_lines.append("        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)\n")
        new_lines.append("        self.sidebar.pack_propagate(False)\n")
        new_lines.append("        title_frame = ctk.CTkFrame(self.sidebar, fg_color=\"transparent\")\n")
        new_lines.append("        title_frame.pack(fill=tk.X, padx=15, pady=(25, 20))\n")
        new_lines.append("        ctk.CTkLabel(title_frame, text=\"🎯 SessionSlice\", font=(FONT_FAMILY, FONT_SIZES['title'], 'bold'), text_color=COLORS['text_primary']).pack(anchor=\"w\")\n")
        new_lines.append("        ctk.CTkLabel(title_frame, text=\"Productivity Tracker\", \n")
        new_lines.append("                  font=(FONT_FAMILY, FONT_SIZES['small']), \n")
        new_lines.append("                  text_color=COLORS['text_secondary']).pack(anchor=\"w\")\n")
        sidebar_fixed = True
        continue
    
    if in_sidebar_block:
        if "self.nav_buttons = {}" in line:
            in_sidebar_block = False
            new_lines.append(line) # Keep this line
        else:
            # Skip old sidebar lines
            continue
    else:
        new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Sidebar fixed." if sidebar_fixed else "Sidebar NOT fixed.")
