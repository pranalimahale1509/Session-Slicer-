import os

file_path = r"c:\Users\ADMIN\Desktop\SessionSlice - Copy\sessionslice_modern.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """    def _create_main_widgets(self):
        self.sidebar = ttk.Frame(self, style="Card.TFrame", width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        self.sidebar.pack_propagate(False)
        title_frame = ttk.Frame(self.sidebar)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 20))
        ttk.Label(title_frame, text="🎯 SessionSlice", style="Title.TLabel").pack()
        ttk.Label(title_frame, text="Productivity Tracker", 
                  font=(FONT_FAMILY, FONT_SIZES['small']), 
                  foreground=COLORS['text_secondary']).pack()"""

new_block = """    def _create_main_widgets(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLORS['surface'])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill=tk.X, padx=15, pady=(25, 20))
        
        ctk.CTkLabel(title_frame, text="🎯 SessionSlice", font=(FONT_FAMILY, FONT_SIZES['title'], 'bold'), text_color=COLORS['text_primary']).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Productivity Tracker", 
                  font=(FONT_FAMILY, FONT_SIZES['small']), 
                  text_color=COLORS['text_secondary']).pack(anchor="w")"""

if old_block in content:
    print("Found block, replacing...")
    new_content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Success.")
else:
    print("Block not found. Checking variations...")
    # Debugging: print what is actually there around the line
    idx = content.find("def _create_main_widgets(self):")
    if idx != -1:
        print(f"Found function def at index {idx}. Next 300 chars:")
        print(content[idx:idx+300])
    else:
        print("Function definition not found.")
