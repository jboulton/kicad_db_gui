
import tkinter as tk
import tkinter.messagebox as messagebox
import ttkbootstrap as ttk
from ttkbootstrap import Style


class mainGUI():

    def _open_add_part_window(self):
        self.add_part_window = ttk.Toplevel("Add Part")
        self.add_part_window.title("Add Part")

        self.add_part_window.columnconfigure(1, weight=1)

        # Create and pack labels and entry widgets for input fields
        fields = [
            "Description", "Datasheet", "Footprint Ref", "Symbol Ref",
            "Model Ref", "KiCad Part Number", "Manufacturer Part Number",
            "Manufacturer", "Manufacturer Part URL", "Note", "Value"
        ]
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(self.add_part_window, text=field).grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(self.add_part_window)
            entry.grid(row=i, column=1, sticky="ew")
            if field == "Footprint Ref":
                entry.insert(0, "db_footprints:")
            if field == "Symbol Ref":
                entry.insert(0, "db_library:")
            self.entries[field] = entry

        # Create a Combobox for Component Type
        ttk.Label(self.add_part_window, text="Component Type").grid(row=len(fields), column=0, sticky="e")
        self.component_type_combobox = ttk.Combobox(self.add_part_window, values=[
            '', 'Resistor', 'Capacitor', 'Connector', 'Diode', 'Electro Mechanical',
            'Mechanical', 'Inductor', 'Opto', 'OpAmp', 'Transister', 'Power Supply IC', 'Semiconductor'
        ])
        self.component_type_combobox.grid(row=len(fields), column=1, sticky="ew")

        # Create button to add part
        self.add_part_button = ttk.Button(
            self.add_part_window, text="Add Part", command=self._add_part)
        self.add_part_button.grid(row=len(fields) + 1, column=0, columnspan=2)

    def _add_part(self):
        # Retrieve values from entry widgets and combobox
        values = [self.entries[field].get() for field in self.entries]
        component_type = self.component_type_combobox.get()
        values.append(component_type)  # Insert component_type at index 1
        print(values)
        # Insert values into the database
        if values[2] == '' or values[3] == '' or values[5] == '':
            messagebox.showerror("Error", "Need to have KiCAD Part Number, Man Part Number, Footprint Ref, Symbol Ref.")
            return
        sql = """INSERT INTO parts (description, datasheet, footprint_ref,
                symbol_ref, model_ref, kicad_part_number, manufacturer_part_number,
                manufacturer, manufacturer_part_url, note, value, component_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        self.cursor.execute(sql, values)
        self.db_connection.commit()

        # Close the add part window
        self.add_part_window.destroy()

        # Refresh the Treeview to display the newly added part
        self.tree.delete(*self.tree.get_children())
        self._populate_parts_tree()

    def _populate_parts_tree(self, component_type_filter=None):
        # Clear current Treeview data
        self.tree.delete(*self.tree.get_children())

        # Fetch existing parts from the database based on the filter
        if component_type_filter:
            sql = """SELECT kicad_part_number, description, component_type, value, symbol_ref, footprint_ref, manufacturer, manufacturer_part_number
                    FROM parts WHERE component_type = %s"""
            self.cursor.execute(sql, (component_type_filter,))
        else:
            self.cursor.execute("""SELECT kicad_part_number, description, component_type, value, symbol_ref, footprint_ref, manufacturer, manufacturer_part_number
                                FROM parts""")
        parts = self.cursor.fetchall()

        # Insert parts into the Treeview
        for part in parts:
            self.tree.insert("", "end", text=part[0], values=(
                part[1], part[2], part[3], part[4], part[5], part[6], part[7]), tags="center")

    def _open_add_supplier_window(self):
        self.add_supplier_window = ttk.Toplevel("Add Supplier")
        self.add_supplier_window.title("Add Supplier")
        self.add_supplier_window.columnconfigure(1, weight=1)
        # Create and pack labels and entry widgets for input fields
        fields = ["Supplier Name", "Address", "Web URL", "Phone", "Email"]
        self.supplier_entries = {}
        for i, field in enumerate(fields):
            ttk.Label(self.add_supplier_window, text=field).grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(self.add_supplier_window)
            entry.grid(row=i, column=1, sticky="ew")
            self.supplier_entries[field] = entry

        # Create button to add supplier
        self.add_supplier_button = ttk.Button(
            self.add_supplier_window,
            text="Add Supplier",
            command=self._add_supplier
        )
        self.add_supplier_button.grid(row=len(fields), column=0, columnspan=2, pady=5)

    def _add_supplier(self):
        # Retrieve values from entry widgets
        values = [self.supplier_entries[field].get() for field in self.supplier_entries]

        # Insert values into the database
        sql = """INSERT INTO supplier (supplier_name, supplier_address, supplier_web_url, supplier_phone, supplier_email) VALUES (%s, %s, %s, %s, %s)"""
        self.cursor.execute(sql, values)
        self.db_connection.commit()

        # Close the add supplier window
        self.add_supplier_window.destroy()

    def _create_menus(self, menu_bar: ttk.Menu):
        file_menu = ttk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New")
        file_menu.add_command(label="Open")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def _create_status_bar(self, root):
        status_bar = ttk.Label(
            root, text="Ready", relief=ttk.SUNKEN, anchor=ttk.W)
        status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)

    def _create_side_pane(self, root):
        pane = ttk.Frame(root, width=200)
        pane.pack(fill=ttk.Y)
        object_tree = ttk.Treeview(pane)
        object_tree.pack(fill=ttk.BOTH, expand=True)
        return object_tree

    def _create_main_content(self):
        # Create a frame to hold the main content
        pane = ttk.Frame(self.root)
        pane.pack(fill=ttk.BOTH, expand=True)

        # Create Treeview widget
        self.tree = ttk.Treeview(pane)
        self.tree.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)

        # Define columns
        self.tree["columns"] = ("description", "component_type", "value", "symbol_ref", "footprint_ref", "manufacturer", "manufacturer_part_number")

        # Add headings
        self.tree.heading("#0", text="KiCad Part Number")
        self.tree.heading("description", text="Description")
        self.tree.heading("component_type", text="Component Type")
        self.tree.heading("value", text="Value")
        self.tree.heading("symbol_ref", text="Symbol reference")
        self.tree.heading("footprint_ref", text="Footprint reference")
        self.tree.heading("manufacturer", text="Manufacturer")
        self.tree.heading("manufacturer_part_number", text="Manufacturer Part Number")

        # Fetch existing parts from the database and populate the Treeview
        self._populate_parts_tree()

        # Create buttons for actions
        self.add_part_button = ttk.Button(pane, text="Add Part", command=self._open_add_part_window)
        self.add_part_button.pack(side=ttk.LEFT, padx=5, pady=5)

        self.add_supplier_button = ttk.Button(pane, text="Add Supplier", command=self._open_add_supplier_window)
        self.add_supplier_button.pack(side=ttk.RIGHT, padx=5, pady=5)

        self.edit_part_button = ttk.Button(pane, text="Edit Part", command=self._edit_part)
        self.edit_part_button.pack(side=ttk.LEFT, padx=5, pady=5)

        # Create a menu for filtering component types
        self.component_type_menu = tk.Menu(self.root, tearoff=0)
        self.component_type_menu.add_command(label="All", command=lambda: self._filter_by_component_type(""))
        self.component_type_menu.add_command(label="Resistor", command=lambda: self._filter_by_component_type("Resistor"))
        self.component_type_menu.add_command(label="Capacitor", command=lambda: self._filter_by_component_type("Capacitor"))
        self.component_type_menu.add_command(label="Connector", command=lambda: self._filter_by_component_type("Connector"))
        self.component_type_menu.add_command(label="Diode", command=lambda: self._filter_by_component_type("Diode"))
        self.component_type_menu.add_command(label="Electro Mechanical", command=lambda: self._filter_by_component_type("Electro Mechanical"))
        self.component_type_menu.add_command(label="Inductor", command=lambda: self._filter_by_component_type("Inductor"))
        self.component_type_menu.add_command(label="Mechanical", command=lambda: self._filter_by_component_type("Mechanical"))
        self.component_type_menu.add_command(label="Opto", command=lambda: self._filter_by_component_type("Opto"))
        self.component_type_menu.add_command(label="OpAmp", command=lambda: self._filter_by_component_type("OpAmp"))
        self.component_type_menu.add_command(label="Opto", command=lambda: self._filter_by_component_type("Opto"))
        self.component_type_menu.add_command(label="Transister", command=lambda: self._filter_by_component_type("Transister"))
        self.component_type_menu.add_command(label="Power Supply IC", command=lambda: self._filter_by_component_type("Power Supply IC"))
        self.component_type_menu.add_command(label="Semiconductor", command=lambda: self._filter_by_component_type("Semiconductor"))
        # Add other component types similarly
        # Create a Filter button to apply the filter
        self.filter_button = ttk.Button(pane, text="Filter", command=self._apply_filter)
        self.filter_button.pack(side=ttk.RIGHT, padx=5, pady=5)

    def _filter_by_component_type(self, component_type):
        # Clear current Treeview data
        self.tree.delete(*self.tree.get_children())
        self._populate_parts_tree(component_type)
        # Fetch data from the database based on the selected component type
        # Populate the Treeview with the filtered data

    def _apply_filter(self):
        # Display the component type filter menu
        self.component_type_menu.post(self.filter_button.winfo_rootx(), self.filter_button.winfo_rooty() + self.filter_button.winfo_height())

    def _edit_part(self):
        # Get the selected item from the Treeview
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No part selected.")
            return

        # Open a window to edit the selected part
        selected_part_id = selected_item[0]  # Get the ID of the selected item
        selected_part = self.tree.item(selected_part_id)
        kicad_part_number = selected_part["text"]

        # Fetch current values from the database
        sql = """SELECT description, datasheet, footprint_ref,
                symbol_ref, model_ref, manufacturer_part_number,
                manufacturer, manufacturer_part_url, note, value, component_type
                FROM parts WHERE kicad_part_number = %s"""
        self.cursor.execute(sql, (kicad_part_number,))
        part_details = self.cursor.fetchone()

        # Open an edit window with the details of the selected part pre-filled
        self.edit_part_window = ttk.Toplevel("Edit Part")

        # Configure resizing behavior
        self.edit_part_window.columnconfigure(1, weight=1)

        # Create and pack labels and entry widgets for input fields
        fields = [
            "Description", "Datasheet", "Footprint Ref",
            "Symbol Ref", "Model Ref", "Manufacturer Part Number",
            "Manufacturer", "Manufacturer Part URL", "Note", "Value"
        ]
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(self.edit_part_window, text=field).grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(self.edit_part_window)
            entry.grid(row=i, column=1, sticky="ew")
            # Pre-fill entry with existing value if available
            if part_details:
                entry.insert(0, part_details[i])
            self.entries[field] = entry

        # Create selector for Component Type
        ttk.Label(self.edit_part_window, text="Component Type").grid(row=len(fields), column=0, sticky="e")
        self.component_type_combobox = ttk.Combobox(self.edit_part_window, values=[
            '', 'Resistor', 'Capacitor', 'Connector', 'Diode', 'Electro Mechanical',
            'Mechanical', 'Inductor', 'Opto', 'OpAmp', 'Transister', 'Power Supply IC', 'Semiconductor'
        ])
        self.component_type_combobox.grid(row=len(fields), column=1, sticky="ew")
        if part_details:
            self.component_type_combobox.set(part_details[-1])  # Pre-select existing component type

        # Create button to update part
        self.update_part_button = ttk.Button(self.edit_part_window, text="Update Part", command=self._update_part)
        self.update_part_button.grid(row=len(fields) + 1, column=0, columnspan=2, pady=5)

    def _update_part(self):
        # Retrieve values from entry widgets
        values = [self.entries[field].get() for field in self.entries]

        # Retrieve value from combobox for Component Type
        component_type = self.component_type_combobox.get()
        values.append(component_type)  # Append component_type to the values list

        # Check if required fields are not empty
        required_fields = {
            "Footprint Ref": values[2],
            "Symbol Ref": values[3],
            "Manufacturer Part Number": values[6]
        }
        for field, value in required_fields.items():
            if not value.strip():
                messagebox.showerror("Error", f"{field} cannot be empty.")
                return

        # Get the KiCad Part Number of the selected item from the Treeview
        selected_item = self.tree.selection()
        selected_part_id = selected_item[0]  # Get the ID of the selected item
        selected_kicad_part_number = self.tree.item(selected_part_id, "text")

        # Update values in the database
        sql = """UPDATE parts SET description = %s, datasheet = %s, footprint_ref = %s,
                symbol_ref = %s, model_ref = %s, manufacturer_part_number = %s,
                manufacturer = %s, manufacturer_part_url = %s, note = %s, value = %s,
                component_type = %s
                WHERE kicad_part_number = %s"""
        print(values + [selected_kicad_part_number])
        self.cursor.execute(sql, values + [selected_kicad_part_number])  # Exclude KiCad Part Number from the values
        self.db_connection.commit()

        # Close the edit part window
        self.edit_part_window.destroy()
        self.tree.delete(*self.tree.get_children())
        self._populate_parts_tree()

    def _center_window(self, window):
        window.update_idletasks()  # Update the window to get correct width and height
        width = window.winfo_width()
        height = window.winfo_height()

        # Calculate the position to center the window
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        window.geometry(f'{width}x{height}+{x}+{y}')

    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection
        self.cursor = self.db_connection.cursor()
        self.root = tk.Tk()
        self.style = Style(theme='darkly')  # Using the "darkly" theme
        self.style.theme_use("darkly")
        self.root.title("KiCAD DB Library Manager")
        self.root.geometry("800x600")

        menu_bar = ttk.Menu(self.root)
        self.root.config(menu=menu_bar)
        self._create_menus(menu_bar)

        self._create_status_bar(self.root)
        self._create_main_content()
        self.root.geometry("800x600")
        self._center_window(self.root)
        self.root.mainloop()

    def close(self):
        """Close the gui"""
        self.root.quit()
