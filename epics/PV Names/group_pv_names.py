# %%
import tkinter as tk
from tkinter import ttk

strings = []
with open('pv_names.txt', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('_'):
            line = '#' + line[1:]
        if line.endswith('_'):
            line = line[:-1] + '#'
        strings.append(line)            


def add_to_nested_dict(nested_dict, keys, value):
    """Helper function to add a value to a nested dictionary."""
    for key in keys[:-1]:
        nested_dict = nested_dict.setdefault(key, {})
    nested_dict[keys[-1]] = value


def create_nested_dict(string_list):
    """Function to create a nested dictionary from a list of strings."""
    nested_dict = {}
    for string in string_list:
        keys = string.split('_')
        add_to_nested_dict(nested_dict, keys, string)
    return nested_dict

names = create_nested_dict(strings)

class NestedDictBrowser(tk.Tk):
    def __init__(self, nested_dict):
        super().__init__()
        self.title("PV Browser")
        self.geometry("600x1000") 
        self.tree = ttk.Treeview(self)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.insert_dict('', nested_dict)
        
    def insert_dict(self, parent, dictionary):
        for key, value in dictionary.items():
            node = self.tree.insert(parent, 'end', text=key, open=False)
            if isinstance(value, dict):
                self.insert_dict(node, value)
            else:
                self.tree.insert(node, 'end', text=value)

# Create and run the application
app = NestedDictBrowser(names)
app.mainloop()
# %%
