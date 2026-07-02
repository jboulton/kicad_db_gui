"""
KiCad Database Library Manager - Refactored Version
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from ttkbootstrap import Style


@dataclass
class Part:
    """Data class representing a part in the database."""
    description: str = ""
    datasheet: str = ""
    footprint_ref: str = ""
    symbol_ref: str = ""
    model_ref: str = ""
    kicad_part_number: str = ""
    manufacturer_part_number: str = ""
    manufacturer: str = ""
    manufacturer_part_url: str = ""
    note: str = ""
    value: str = ""
    component_type: str = ""
    exclude_from_bom: bool = False
    exclude_from_board: bool = False
    exclude_from_sim: bool = False


@dataclass
class Module:
    """Data class representing a module in the database."""
    description: str = ""
    datasheet: str = ""
    footprint_ref: str = ""
    symbol_ref: str = ""
    model_ref: str = ""
    kicad_part_number: str = ""
    manufacturer_part_number: str = ""
    manufacturer: str = ""
    manufacturer_part_url: str = ""
    note: str = ""
    value: str = ""
    parts: List[str] = field(default_factory=list)


@dataclass
class Supplier:
    """Data class representing a supplier in the database."""
    supplier_name: str = ""
    supplier_address: str = ""
    supplier_web_url: str = ""
    supplier_phone: str = ""
    supplier_email: str = ""


class DatabaseManager:
    """Handles all database operations."""

    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.cursor = db_connection.cursor()

    def add_part(self, part: Part) -> None:
        """Add a new part to the database."""
        sql = """INSERT INTO parts (description, datasheet, footprint_ref,
                symbol_ref, model_ref, kicad_part_number, manufacturer_part_number,
                manufacturer, manufacturer_part_url, note, value, component_type,
                exclude_from_bom, exclude_from_board, exclude_from_sim)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = [
            part.description, part.datasheet, part.footprint_ref,
            part.symbol_ref, part.model_ref, part.kicad_part_number,
            part.manufacturer_part_number, part.manufacturer,
            part.manufacturer_part_url, part.note, part.value, part.component_type,
            part.exclude_from_bom, part.exclude_from_board, part.exclude_from_sim
        ]
        self.cursor.execute(sql, values)
        self.db_connection.commit()

    def update_part(self, part: Part) -> None:
        """Update an existing part in the database."""
        sql = """UPDATE parts SET description = %s, datasheet = %s, footprint_ref = %s,
                symbol_ref = %s, model_ref = %s, manufacturer_part_number = %s,
                manufacturer = %s, manufacturer_part_url = %s, note = %s, value = %s,
                component_type = %s, exclude_from_bom = %s, exclude_from_board = %s,
                exclude_from_sim = %s WHERE kicad_part_number = %s"""
        values = [
            part.description, part.datasheet, part.footprint_ref,
            part.symbol_ref, part.model_ref, part.manufacturer_part_number,
            part.manufacturer, part.manufacturer_part_url, part.note,
            part.value, part.component_type,
            part.exclude_from_bom, part.exclude_from_board, part.exclude_from_sim,
            part.kicad_part_number
        ]
        self.cursor.execute(sql, values)
        self.db_connection.commit()

    # Whitelist mapping of sortable treeview columns to actual DB columns.
    # Used to build ORDER BY safely (never interpolate raw column names from callers).
    SORTABLE_COLUMNS = {
        "kicad_part_number": "kicad_part_number",
        "description": "description",
        "component_type": "component_type",
        "value": "value",
        "symbol_ref": "symbol_ref",
        "footprint_ref": "footprint_ref",
        "manufacturer": "manufacturer",
        "manufacturer_part_number": "manufacturer_part_number",
    }

    def get_parts(self, component_type_filter: Optional[str] = None,
                  search_term: Optional[str] = None,
                  sort_column: Optional[str] = None,
                  sort_descending: bool = False) -> List[Tuple]:
        """Retrieve parts from the database, optionally filtered by component type
        and/or a search term, and optionally sorted by a whitelisted column."""
        base_sql = """SELECT kicad_part_number, description, component_type, value,
                symbol_ref, footprint_ref, manufacturer, manufacturer_part_number
                FROM parts"""

        conditions = []
        params: List[str] = []

        if component_type_filter:
            conditions.append("component_type = %s")
            params.append(component_type_filter)

        if search_term:
            conditions.append("""(description ILIKE %s OR kicad_part_number ILIKE %s
                    OR manufacturer_part_number ILIKE %s OR manufacturer ILIKE %s
                    OR value ILIKE %s)""")
            like_term = f"%{search_term}%"
            params.extend([like_term] * 5)

        sql = base_sql
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        # Validate sort_column against the whitelist to avoid SQL injection via ORDER BY.
        if sort_column and sort_column in self.SORTABLE_COLUMNS:
            direction = "DESC" if sort_descending else "ASC"
            sql += f" ORDER BY {self.SORTABLE_COLUMNS[sort_column]} {direction}"

        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def get_part_details(self, kicad_part_number: str) -> Optional[Tuple]:
        """Get detailed information for a specific part."""
        sql = """SELECT description, datasheet, footprint_ref, symbol_ref, model_ref,
                manufacturer_part_number, manufacturer, manufacturer_part_url, note,
                value, component_type, exclude_from_bom, exclude_from_board,
                exclude_from_sim FROM parts WHERE kicad_part_number = %s"""
        self.cursor.execute(sql, (kicad_part_number,))
        return self.cursor.fetchone()

    def get_parts_for_combobox(self) -> Tuple[List[str], Dict[str, str]]:
        """Get parts data formatted for combobox usage."""
        self.cursor.execute("SELECT parts_uuid, kicad_part_number FROM parts")
        parts = self.cursor.fetchall()
        part_names = [part[1] for part in parts]
        parts_uuid_map = {part[1]: part[0] for part in parts}
        return part_names, parts_uuid_map

    def add_module(self, module: Module) -> str:
        """Add a new module to the database and return its UUID."""
        module_sql = """INSERT INTO module (description, datasheet, footprint_ref,
                        symbol_ref, model_ref, kicad_part_number, manufacturer_part_number,
                        manufacturer, manufacturer_part_url, note, value)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING module_uuid"""
        values = [
            module.description, module.datasheet, module.footprint_ref,
            module.symbol_ref, module.model_ref, module.kicad_part_number,
            module.manufacturer_part_number, module.manufacturer,
            module.manufacturer_part_url, module.note, module.value
        ]
        self.cursor.execute(module_sql, values)
        return self.cursor.fetchone()[0]

    def add_module_parts(self, module_uuid: str, part_uuids: List[str]) -> None:
        """Add parts to a module."""
        module_parts_sql = "INSERT INTO module_parts (module_uuid, part_uuid) VALUES (%s, %s)"
        for part_uuid in part_uuids:
            self.cursor.execute(module_parts_sql, (module_uuid, part_uuid))
        self.db_connection.commit()

    def add_supplier(self, supplier: Supplier) -> None:
        """Add a new supplier to the database."""
        sql = """INSERT INTO supplier (supplier_name, supplier_address, supplier_web_url,
                supplier_phone, supplier_email) VALUES (%s, %s, %s, %s, %s)"""
        values = [
            supplier.supplier_name, supplier.supplier_address, supplier.supplier_web_url,
            supplier.supplier_phone, supplier.supplier_email
        ]
        self.cursor.execute(sql, values)
        self.db_connection.commit()


class FormValidator:
    """Handles form validation logic."""

    @staticmethod
    def validate_part(part: Part) -> Tuple[bool, str]:
        """Validate part data. Returns (is_valid, error_message)."""
        required_fields = {
            'KiCAD Part Number': part.kicad_part_number,
            'Manufacturer Part Number': part.manufacturer_part_number,
            'Footprint Ref': part.footprint_ref,
            'Symbol Ref': part.symbol_ref
        }

        for field_name, value in required_fields.items():
            if not value or not value.strip():
                return False, f"{field_name} is required."

        return True, ""


class BaseWindow(ABC):
    """Base class for dialog windows."""

    def __init__(self, parent, title: str):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.columnconfigure(1, weight=1)
        self.entries = {}
        self._setup_window()

    @abstractmethod
    def _setup_window(self) -> None:
        """Setup the window layout."""
        pass

    @abstractmethod
    def _on_submit(self) -> None:
        """Handle form submission."""
        pass

    def _create_form_fields(self, fields: List[str], defaults: Dict[str, str] | None = None) -> None:
        """Create form fields with labels and entries."""
        defaults = defaults or {}

        for i, items in enumerate(fields):
            ttk.Label(self.window, text=items).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(self.window)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)

            # Set default values
            if items in defaults:
                entry.insert(0, defaults[items])
            elif items == "Footprint Ref":
                entry.insert(0, "db_footprints:")
            elif items == "Symbol Ref":
                entry.insert(0, "db_library:")

            self.entries[items] = entry

    def _create_exclude_checkboxes(self, row: int, defaults: Dict[str, bool] | None = None) -> int:
        """Create the exclude_from_bom/board/sim checkboxes starting at the given row.

        Returns the next free row after the checkboxes.
        """
        defaults = defaults or {}
        self.exclude_vars: Dict[str, tk.BooleanVar] = {}

        checkbox_frame = ttk.Frame(self.window)
        checkbox_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        labels_and_keys = [
            ("Exclude from BOM", "exclude_from_bom"),
            ("Exclude from Board", "exclude_from_board"),
            ("Exclude from Sim", "exclude_from_sim"),
        ]

        for i, (label, key) in enumerate(labels_and_keys):
            var = tk.BooleanVar(value=defaults.get(key, False))
            chk = ttk.Checkbutton(checkbox_frame, text=label, variable=var)
            chk.grid(row=0, column=i, padx=(0 if i == 0 else 10, 0), sticky="w")
            self.exclude_vars[key] = var

        return row + 1

    def _create_submit_button(self, text: str, row: int) -> None:
        """Create submit and close buttons."""
        # Create a frame to hold both buttons
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)

        # Submit button
        submit_button = ttk.Button(button_frame, text=text, command=self._on_submit)
        submit_button.pack(side="left", padx=(0, 5))

        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=self.destroy)
        close_button.pack(side="left", padx=(5, 0))

    def destroy(self) -> None:
        """Close the window."""
        self.window.destroy()


class AddPartWindow(BaseWindow):
    """Window for adding new parts."""

    def __init__(self, parent, db_manager: DatabaseManager, component_types: List[str],
                 refresh_callback):
        self.db_manager = db_manager
        self.component_types = component_types
        self.refresh_callback = refresh_callback
        super().__init__(parent, "Add Part")

    def _setup_window(self) -> None:
        fields = [
            "Description", "Datasheet", "Footprint Ref", "Symbol Ref",
            "Model Ref", "KiCad Part Number", "Manufacturer Part Number",
            "Manufacturer", "Manufacturer Part URL", "Note", "Value"
        ]
        self._create_form_fields(fields)

        # Component Type Combobox
        row = len(fields)
        ttk.Label(self.window, text="Component Type").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        self.component_type_combobox = ttk.Combobox(self.window, values=self.component_types)
        self.component_type_combobox.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

        # Exclude checkboxes
        row = self._create_exclude_checkboxes(row + 1)

        self._create_submit_button("Add Part", row)

    def _on_submit(self) -> None:
        # Create Part object from form data
        part = Part(
            description=self.entries["Description"].get(),
            datasheet=self.entries["Datasheet"].get(),
            footprint_ref=self.entries["Footprint Ref"].get(),
            symbol_ref=self.entries["Symbol Ref"].get(),
            model_ref=self.entries["Model Ref"].get(),
            kicad_part_number=self.entries["KiCad Part Number"].get(),
            manufacturer_part_number=self.entries["Manufacturer Part Number"].get(),
            manufacturer=self.entries["Manufacturer"].get(),
            manufacturer_part_url=self.entries["Manufacturer Part URL"].get(),
            note=self.entries["Note"].get(),
            value=self.entries["Value"].get(),
            component_type=self.component_type_combobox.get(),
            exclude_from_bom=self.exclude_vars["exclude_from_bom"].get(),
            exclude_from_board=self.exclude_vars["exclude_from_board"].get(),
            exclude_from_sim=self.exclude_vars["exclude_from_sim"].get()
        )

        # Validate
        is_valid, error_msg = FormValidator.validate_part(part)
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return

        try:
            self.db_manager.add_part(part)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add part: {str(e)}")


class EditPartWindow(BaseWindow):
    """Window for editing existing parts."""

    def __init__(self, parent, db_manager: DatabaseManager, component_types: List[str],
                 kicad_part_number: str, refresh_callback):
        self.db_manager = db_manager
        self.component_types = component_types
        self.kicad_part_number = kicad_part_number
        self.refresh_callback = refresh_callback
        super().__init__(parent, "Edit Part")

    def _setup_window(self) -> None:
        # Get existing part details
        part_details = self.db_manager.get_part_details(self.kicad_part_number)
        if not part_details:
            messagebox.showerror("Error", "Part not found")
            self.destroy()
            return

        fields = [
            "Description", "Datasheet", "Footprint Ref", "Symbol Ref",
            "Model Ref", "Manufacturer Part Number", "Manufacturer",
            "Manufacturer Part URL", "Note", "Value"
        ]

        # Create defaults dictionary
        defaults = {field: str(part_details[i]) for i, field in enumerate(fields)}
        self._create_form_fields(fields, defaults)

        # Component Type Combobox
        row = len(fields)
        ttk.Label(self.window, text="Component Type").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        self.component_type_combobox = ttk.Combobox(self.window, values=self.component_types)
        self.component_type_combobox.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        self.component_type_combobox.set(part_details[10])  # Set current component type

        # Exclude checkboxes, pre-populated from existing values
        # part_details indices: 11=exclude_from_bom, 12=exclude_from_board, 13=exclude_from_sim
        exclude_defaults = {
            "exclude_from_bom": bool(part_details[11]),
            "exclude_from_board": bool(part_details[12]),
            "exclude_from_sim": bool(part_details[13]),
        }
        row = self._create_exclude_checkboxes(row + 1, exclude_defaults)

        self._create_submit_button("Update Part", row)

    def _on_submit(self) -> None:
        # Create Part object from form data
        part = Part(
            description=self.entries["Description"].get(),
            datasheet=self.entries["Datasheet"].get(),
            footprint_ref=self.entries["Footprint Ref"].get(),
            kicad_part_number=self.kicad_part_number,
            symbol_ref=self.entries["Symbol Ref"].get(),
            model_ref=self.entries["Model Ref"].get(),
            manufacturer_part_number=self.entries["Manufacturer Part Number"].get(),
            manufacturer=self.entries["Manufacturer"].get(),
            manufacturer_part_url=self.entries["Manufacturer Part URL"].get(),
            note=self.entries["Note"].get(),
            value=self.entries["Value"].get(),
            component_type=self.component_type_combobox.get(),
            exclude_from_bom=self.exclude_vars["exclude_from_bom"].get(),
            exclude_from_board=self.exclude_vars["exclude_from_board"].get(),
            exclude_from_sim=self.exclude_vars["exclude_from_sim"].get()
        )

        # Validate
        is_valid, error_msg = FormValidator.validate_part(part)
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return

        try:
            self.db_manager.update_part(part)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update part: {str(e)}")


class AddModuleWindow(BaseWindow):
    """Window for adding new modules."""

    def __init__(self, parent, db_manager: DatabaseManager, refresh_callback):
        self.db_manager = db_manager
        self.refresh_callback = refresh_callback
        self.parts_uuid_map = {}
        super().__init__(parent, "Add Module")

    def _setup_window(self) -> None:
        fields = [
            "Description", "Datasheet", "Footprint Ref", "Symbol Ref", "Model Ref",
            "KiCad Part Number", "Manufacturer Part Number", "Manufacturer",
            "Manufacturer Part URL", "Note", "Value"
        ]
        self._create_form_fields(fields)

        row = len(fields)

        # Selected parts treeview
        ttk.Label(self.window, text="Selected Parts").grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        self.selected_parts_tree = ttk.Treeview(self.window, columns=("Part",), selectmode="extended", height=6)
        self.selected_parts_tree.heading("#0", text="Selected Parts")
        self.selected_parts_tree.column("#0", width=300)
        self.selected_parts_tree.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Parts selection combobox
        self.parts_combobox = ttk.Combobox(self.window, state="readonly")
        self.parts_combobox.grid(row=row + 2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self._populate_parts_combobox()

        # Buttons for managing parts
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=row + 3, column=0, columnspan=2, pady=5)

        ttk.Button(button_frame, text="Add Part", command=self._add_part_to_module).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Part", command=self._remove_part_from_module).pack(side=tk.LEFT, padx=5)

        self._create_submit_button("Add Module", row + 4)

    def _populate_parts_combobox(self) -> None:
        """Populate the parts combobox with available parts."""
        part_names, self.parts_uuid_map = self.db_manager.get_parts_for_combobox()
        self.parts_combobox['values'] = part_names

    def _add_part_to_module(self) -> None:
        """Add selected part to the module."""
        selected_part = self.parts_combobox.get()
        if selected_part:
            self.selected_parts_tree.insert("", "end", text=selected_part)

    def _remove_part_from_module(self) -> None:
        """Remove selected parts from the module."""
        selected_items = self.selected_parts_tree.selection()
        for item in selected_items:
            self.selected_parts_tree.delete(item)

    def _on_submit(self) -> None:
        # Create Module object from form data
        module = Module(
            description=self.entries["Description"].get(),
            datasheet=self.entries["Datasheet"].get(),
            footprint_ref=self.entries["Footprint Ref"].get(),
            symbol_ref=self.entries["Symbol Ref"].get(),
            model_ref=self.entries["Model Ref"].get(),
            kicad_part_number=self.entries["KiCad Part Number"].get(),
            manufacturer_part_number=self.entries["Manufacturer Part Number"].get(),
            manufacturer=self.entries["Manufacturer"].get(),
            manufacturer_part_url=self.entries["Manufacturer Part URL"].get(),
            note=self.entries["Note"].get(),
            value=self.entries["Value"].get()
        )

        # Get selected parts
        selected_parts = [self.selected_parts_tree.item(item, "text") for item in self.selected_parts_tree.get_children()]
        part_uuids = [self.parts_uuid_map[part] for part in selected_parts if part in self.parts_uuid_map]

        try:
            module_uuid = self.db_manager.add_module(module)
            if part_uuids:
                self.db_manager.add_module_parts(module_uuid, part_uuids)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add module: {str(e)}")


class AddSupplierWindow(BaseWindow):
    """Window for adding new suppliers."""

    def __init__(self, parent, db_manager: DatabaseManager):
        self.db_manager = db_manager
        super().__init__(parent, "Add Supplier")

    def _setup_window(self) -> None:
        fields = ["Supplier Name", "Address", "Web URL", "Phone", "Email"]
        self._create_form_fields(fields)
        self._create_submit_button("Add Supplier", len(fields))

    def _on_submit(self) -> None:
        supplier = Supplier(
            supplier_name=self.entries["Supplier Name"].get(),
            supplier_address=self.entries["Address"].get(),
            supplier_web_url=self.entries["Web URL"].get(),
            supplier_phone=self.entries["Phone"].get(),
            supplier_email=self.entries["Email"].get()
        )

        try:
            self.db_manager.add_supplier(supplier)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add supplier: {str(e)}")


class DatabaseConnectionWindow(BaseWindow):
    """Window for viewing/editing the database connection settings.

    Unlike other dialogs, this doesn't take a DatabaseManager (there may not
    be a working one yet) — it takes a reference to the MainGUI instance so
    it can hand off a validated settings dict and let MainGUI coordinate the
    actual reconnect via its on_update_connection callback.
    """

    def __init__(self, parent, main_gui: "MainGUI", current_settings: Dict[str, str]):
        self.main_gui = main_gui
        self.current_settings = current_settings
        super().__init__(parent, "Database Connection")

    def _setup_window(self) -> None:
        fields = ["Host", "Port", "Database", "User"]
        defaults = {
            "Host": str(self.current_settings.get("db_host", "")),
            "Port": str(self.current_settings.get("db_port", "")),
            "Database": str(self.current_settings.get("db_database", "")),
            "User": str(self.current_settings.get("db_user", "")),
        }
        self._create_form_fields(fields, defaults)

        # Password gets its own masked entry - _create_form_fields doesn't support
        # show="*", and we don't want it echoed to the screen by default.
        row = len(fields)
        ttk.Label(self.window, text="Password").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        password_entry = ttk.Entry(self.window, show="*")
        password_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        password_entry.insert(0, str(self.current_settings.get("db_password", "")))
        self.entries["Password"] = password_entry

        show_password_var = tk.BooleanVar(value=False)

        def _toggle_password_visibility():
            password_entry.config(show="" if show_password_var.get() else "*")

        ttk.Checkbutton(
            self.window, text="Show password", variable=show_password_var,
            command=_toggle_password_visibility
        ).grid(row=row + 1, column=1, sticky="w", padx=5, pady=(0, 5))

        self._create_submit_button("Save && Reconnect", row + 2)

    def _on_submit(self) -> None:
        host = self.entries["Host"].get().strip()
        port_text = self.entries["Port"].get().strip()
        database = self.entries["Database"].get().strip()
        user = self.entries["User"].get().strip()
        password = self.entries["Password"].get()

        if not host or not database or not user:
            messagebox.showerror("Error", "Host, Database, and User are required.")
            return

        try:
            port = int(port_text)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return

        new_settings = {
            "db_host": host,
            "db_port": port,
            "db_database": database,
            "db_user": user,
            "db_password": password,
        }

        # Give some feedback while we attempt the (potentially slow) connection.
        self.window.config(cursor="watch")
        self.window.update_idletasks()
        try:
            self.main_gui.apply_new_connection(new_settings)
        except Exception as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect with the given settings:\n{str(e)}\n\n"
                "Your previous connection is still active and nothing was saved."
            )
            return
        finally:
            self.window.config(cursor="")

        messagebox.showinfo("Success", f"Connected to '{database}' and saved settings.")
        self.destroy()


class MainGUI:
    """Main application window."""

    COMPONENT_TYPES = [
        '', 'Resistor', 'Capacitor', 'Connector', 'Diode', 'Electro Mechanical',
        'Mechanical', 'Inductor', 'Opto', 'OpAmp', 'Transister', 'Power Supply IC', 'Semiconductor'
    ]

    def __init__(self, db_connection, connection_settings: Optional[Dict[str, object]] = None,
                 on_update_connection: Optional[Callable[[Dict[str, object]], object]] = None):
        self.db_manager = DatabaseManager(db_connection)
        # Current DB connection settings (host/port/database/user/password), used to
        # pre-fill the DatabaseConnectionWindow. Owned by the caller (main.py), which
        # is responsible for actually persisting them (e.g. to the .ini file).
        self.connection_settings: Dict[str, object] = connection_settings or {}
        # Callback: takes a new settings dict, attempts to connect, persists the
        # settings on success, and returns the new live connection. Should raise
        # on failure rather than returning anything, so MainGUI knows not to swap in
        # a broken connection.
        self.on_update_connection = on_update_connection
        self.current_component_type_filter: Optional[str] = None
        self.sort_column: Optional[str] = None
        self.sort_descending: bool = False
        self._search_after_id: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self.style = Style(theme='pulse')
        self.root = self.style.master
        self.style.theme_use("darkly")
        self.root.title("KiCAD DB Library Manager")
        self.root.geometry("1000x700")

        self._create_menus()
        self._create_status_bar()
        self._create_main_content()
        self._center_window()

    def _create_menus(self) -> None:
        """Create the application menu bar."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New Part", command=self._open_add_part_window)
        file_menu.add_command(label="Edit Part", command=self._open_edit_part_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=False)
        settings_menu.add_command(label="Database Connection...", command=self._open_db_connection_window)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_main_content(self) -> None:
        """Create the main content area."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create search bar
        self._create_search_bar(main_frame)

        # Create parts treeview
        self._setup_parts_treeview(main_frame)

        # Create button frame
        self._create_button_frame(main_frame)

        # Initialize data
        self._refresh_parts_list()

    def _create_search_bar(self, parent) -> None:
        """Create the search bar above the parts treeview."""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(search_frame, text="Clear", command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=(5, 0))

    def _on_search_changed(self, *_args) -> None:
        """Debounce search input so we don't hit the DB on every keystroke."""
        if self._search_after_id is not None:
            self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(300, self._refresh_parts_list)

    # Maps treeview column identifiers to the DB column names understood by
    # DatabaseManager.SORTABLE_COLUMNS. "#0" is the tree's special first column.
    COLUMN_DB_MAP = {
        "#0": "kicad_part_number",
        "description": "description",
        "component_type": "component_type",
        "value": "value",
        "symbol_ref": "symbol_ref",
        "footprint_ref": "footprint_ref",
        "manufacturer": "manufacturer",
        "manufacturer_part_number": "manufacturer_part_number",
    }

    def _setup_parts_treeview(self, parent) -> None:
        """Setup the parts treeview widget."""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-click a row to edit it directly, without needing to select + click "Edit Part"
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Define columns
        columns = ("description", "component_type", "value", "symbol_ref", "footprint_ref", "manufacturer", "manufacturer_part_number")
        self.tree["columns"] = columns

        # Configure column headings, with click-to-sort wired to each one
        headings = {
            "#0": "KiCad Part Number",
            "description": "Description",
            "component_type": "Component Type",
            "value": "Value",
            "symbol_ref": "Symbol Reference",
            "footprint_ref": "Footprint Reference",
            "manufacturer": "Manufacturer",
            "manufacturer_part_number": "Manufacturer Part Number",
        }
        for col_id, label in headings.items():
            self.tree.heading(col_id, text=label, command=lambda c=col_id: self._on_column_header_click(c))

        # Configure column widths
        self.tree.column("#0", width=150)
        for col in columns:
            self.tree.column(col, width=120)

    def _on_column_header_click(self, col_id: str) -> None:
        """Handle a click on a treeview column header: sort by that column,
        toggling direction if it's already the active sort column."""
        db_column = self.COLUMN_DB_MAP.get(col_id)
        if not db_column:
            return

        if self.sort_column == db_column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = db_column
            self.sort_descending = False

        self._update_column_heading_indicators()
        self._refresh_parts_list()

    def _update_column_heading_indicators(self) -> None:
        """Add a \u25b2/\u25bc arrow to the active sort column's heading, clear others."""
        base_labels = {
            "#0": "KiCad Part Number",
            "description": "Description",
            "component_type": "Component Type",
            "value": "Value",
            "symbol_ref": "Symbol Reference",
            "footprint_ref": "Footprint Reference",
            "manufacturer": "Manufacturer",
            "manufacturer_part_number": "Manufacturer Part Number",
        }
        arrow = " \u25bc" if self.sort_descending else " \u25b2"
        for col_id, label in base_labels.items():
            db_column = self.COLUMN_DB_MAP.get(col_id)
            text = label + arrow if db_column == self.sort_column else label
            self.tree.heading(col_id, text=text)

    def _create_button_frame(self, parent) -> None:
        """Create the button frame with action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Left side buttons
        ttk.Button(button_frame, text="Add Part", command=self._open_add_part_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Part", command=self._open_edit_part_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Module", command=self._open_add_module_window).pack(side=tk.LEFT, padx=5)

        # Right side buttons
        ttk.Button(button_frame, text="Add Supplier", command=self._open_add_supplier_window).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Filter", command=self._show_filter_menu).pack(side=tk.RIGHT, padx=5)

        # Create filter menu
        self._create_filter_menu()

    def _create_filter_menu(self) -> None:
        """Create the component type filter menu."""
        self.filter_menu = tk.Menu(self.root, tearoff=0)
        self.filter_menu.add_command(label="All", command=lambda: self._filter_by_component_type(None))
        for component_type in self.COMPONENT_TYPES[1:]:  # Skip empty string
            self.filter_menu.add_command(
                label=component_type,
                command=lambda ct=component_type: self._filter_by_component_type(ct)
            )

    def _show_filter_menu(self) -> None:
        """Show the filter menu."""
        try:
            x = self.root.winfo_rootx() + 100
            y = self.root.winfo_rooty() + 100
            self.filter_menu.post(x, y)
        except tk.TclError:
            pass  # Menu might be destroyed

    def _filter_by_component_type(self, component_type: Optional[str]) -> None:
        """Filter parts by component type."""
        self.current_component_type_filter = component_type
        self._refresh_parts_list()
        filter_text = component_type or "All"
        self.status_bar.config(text=f"Filtered by: {filter_text}")

    def _refresh_parts_list(self, component_type_filter: Optional[str] = None) -> None:
        """Refresh the parts list in the treeview, applying the current search
        term and sort column/direction. component_type_filter, if given,
        updates the persisted filter (used by callers like AddPartWindow's
        refresh_callback that don't know about the current filter state)."""
        if component_type_filter is not None:
            self.current_component_type_filter = component_type_filter

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Fetch and display parts
        try:
            search_term = self.search_var.get().strip() if hasattr(self, "search_var") else ""
            parts = self.db_manager.get_parts(
                self.current_component_type_filter,
                search_term=search_term or None,
                sort_column=self.sort_column,
                sort_descending=self.sort_descending,
            )
            for part in parts:
                self.tree.insert("", "end", text=part[0], values=part[1:])
            self.status_bar.config(text=f"{len(parts)} part(s)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parts: {str(e)}")

    def _open_add_part_window(self) -> None:
        """Open the add part window."""
        AddPartWindow(self.root, self.db_manager, self.COMPONENT_TYPES, self._refresh_parts_list)

    def _on_row_double_click(self, event) -> None:
        """Open the edit window for whichever row was double-clicked.

        Ignores double-clicks on the header row (event.y in the header area
        returns region "heading", not "cell"/"tree") so this doesn't fight
        with the column-sort click handler.
        """
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            return

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return  # double-click landed on empty space below the last row

        self.tree.selection_set(row_id)
        kicad_part_number = self.tree.item(row_id, "text")
        EditPartWindow(self.root, self.db_manager, self.COMPONENT_TYPES, kicad_part_number, self._refresh_parts_list)

    def _open_edit_part_window(self) -> None:
        """Open the edit part window."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No part selected.")
            return

        kicad_part_number = self.tree.item(selected_item[0], "text")
        EditPartWindow(self.root, self.db_manager, self.COMPONENT_TYPES, kicad_part_number, self._refresh_parts_list)

    def _open_add_module_window(self) -> None:
        """Open the add module window."""
        AddModuleWindow(self.root, self.db_manager, self._refresh_parts_list)

    def _open_add_supplier_window(self) -> None:
        """Open the add supplier window."""
        AddSupplierWindow(self.root, self.db_manager)

    def _open_db_connection_window(self) -> None:
        """Open the database connection settings window."""
        DatabaseConnectionWindow(self.root, self, self.connection_settings)

    def apply_new_connection(self, new_settings: Dict[str, object]) -> None:
        """Attempt to switch to a new database connection.

        Delegates the actual connect-and-persist work to on_update_connection
        (owned by main.py, since it also manages the app-level global
        connection and the .ini file). Only swaps self.db_manager over and
        refreshes the UI once that succeeds; if it raises, this re-raises to
        the caller (DatabaseConnectionWindow) and the current connection and
        settings are left untouched.
        """
        if self.on_update_connection is None:
            raise RuntimeError("No connection update handler is configured.")

        new_connection = self.on_update_connection(new_settings)

        self.db_manager = DatabaseManager(new_connection)
        self.connection_settings = new_settings
        self.current_component_type_filter = None
        self.sort_column = None
        self.sort_descending = False
        if hasattr(self, "search_var"):
            self.search_var.set("")
        self._refresh_parts_list()
        self.status_bar.config(
            text=f"Connected to {new_settings.get('db_database')}@{new_settings.get('db_host')}"
        )

    def _center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def run(self) -> None:
        """Start the application."""
        self.root.mainloop()

    def close(self) -> None:
        """Close the application."""
        self.root.quit()


# Example usage
if __name__ == "__main__":
    # This would be your database connection setup
    # db_connection = your_database_connection_here

    # Initialize and run the application
    # app = MainGUI(db_connection)
    # app.run()
    pass