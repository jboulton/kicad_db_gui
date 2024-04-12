
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap import Style


class mainGUI():

    def _create_menus(self, root, menu_bar: tk.Menu):
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New")
        file_menu.add_command(label="Open")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def _create_status_bar(self, root):
        status_bar = ttk.Label(
            root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_side_pane(self, root):
        side_pane = ttk.Frame(root, width=200)
        side_pane.pack(side=tk.LEFT, fill=tk.Y)
        object_tree = ttk.Treeview(side_pane)
        object_tree.pack(fill=tk.BOTH, expand=True)
        return object_tree

    def _create_main_content(self, root):
        main_content = tk.Text(root)
        main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection
        self.root = tk.Tk()
        self.style = Style(theme='darkly')  # Using the "darkly" theme
        self.root.title("KiCAD DB Library Manager")
        self.root.geometry("800x600")

        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        self._create_menus(self.root, menu_bar)

        self._create_status_bar(self.root)
        self.object_tree = self._create_side_pane(self.root)
        self._create_main_content(self.root)

        self.root.mainloop()
