"""
Manager Dialogs Module

This module provides dialog windows for managing various aspects of the Student Management System,
including departments, majors, academic years, classes, subjects, and schedules.

Key Features:
- Department management
- Major management with department associations
- Academic year management
- Class and subject management
- Schedule management
- Generic reusable dialog components

Dependencies:
- tkinter: For GUI components
- db_utils: For database operations
- datetime: For date/time handling
"""

import tkinter as tk
from tkinter import ttk, messagebox
from db_utils import execute_query, load_all_caches, load_departments_to_cache, \
    load_majors_to_cache, load_subjects_to_cache, load_class_names_to_cache, \
    load_academic_years_to_cache
from datetime import datetime

def _open_generic_manager(app, title, cache_dict, table_name, refresh_func, use_treeview=False):
    """
    A generic manager dialog for simple CRUD operations on database tables.
    
    This function creates a reusable dialog window for managing simple lookup tables
    like departments, academic years, etc. It provides standard CRUD operations
    with a clean interface.
    
    Args:
        app: The main application instance
        title (str): Title for the dialog window
        cache_dict (dict): Reference to the application's cache dictionary for this entity
        table_name (str): Name of the database table to operate on
        refresh_func (function): Function to call when refreshing the cache
        use_treeview (bool, optional): Whether to use a Treeview for display. 
                                        If False, uses a Listbox. Defaults to False.
    
    Returns:
        None
    """
    manager_win = app.tk.Toplevel(app.window)
    manager_win.title(title)
    manager_win.geometry("450x400")
    manager_win.transient(app.window)
    manager_win.grab_set()

    frame = app.ttk.Frame(manager_win, padding=10)
    frame.pack(expand=True, fill=app.tk.BOTH)

    list_frame = app.ttk.LabelFrame(frame, text=title.replace(" Manager", ""), padding=5)
    list_frame.pack(expand=True, fill=app.tk.BOTH, pady=5)

    if use_treeview:
        widget = app.ttk.Treeview(list_frame, columns=("name",), show="tree headings")
        widget.heading("#0", text="Category") # Changed from "Shift" to "Category" for generic use
        widget.heading("name", text="Name")
    else:
        widget = app.tk.Listbox(list_frame, font=("Arial", 11))
    widget.pack(expand=True, fill=app.tk.BOTH)

    def populate_widget():
        if use_treeview:
            for i in widget.get_children(): widget.delete(i)
            # Dynamic categorization based on first letter for generic treeview
            categories = {}
            for name in sorted(cache_dict.keys()):
                first_char = name[0].upper() if name else '#' # Use '#' for empty/invalid names
                category = categories.setdefault(first_char, widget.insert('', 'end', text=first_char, open=True))
                widget.insert(category, 'end', values=(name,))
            # Add a placeholder if no items at all
            if not categories and not cache_dict:
                widget.insert('', 'end', text='(No Items)', open=False)
        else:
            widget.delete(0, app.tk.END)
            for name in sorted(cache_dict.keys()):
                widget.insert(app.tk.END, name)

    entry_frame = app.ttk.Frame(frame)
    entry_frame.pack(fill=app.tk.X, pady=5)
    app.ttk.Label(entry_frame, text="Name:").pack(side=app.tk.LEFT, padx=5)
    entry = app.ttk.Entry(entry_frame)
    entry.pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=5)

    def on_select(event):
        name = ""
        if use_treeview:
            if (sel := widget.focus()) and widget.parent(sel): # Ensure a child node is selected
                name = widget.item(sel)['values'][0]
        elif widget.curselection():
            name = widget.get(widget.curselection()[0])
        if name:
            entry.delete(0, app.tk.END)
            entry.insert(0, name)

    widget.bind('<<ListboxSelect>>' if not use_treeview else '<<TreeviewSelect>>', on_select)

    def refresh_all_manager(): # Renamed to avoid confusion with app.refresh_treeview
        refresh_func(app) # Call the specific refresh for this cache, passing 'app'
        load_all_caches(app) # Refresh all caches in main app, passing 'app'
        app.refresh_treeview() # Refresh main treeview, passing 'app' implicitly
        populate_widget()
        entry.delete(0, app.tk.END)

    def add_item():
        if name := entry.get().strip():
            execute_query(app, f"INSERT IGNORE INTO {table_name} (name) VALUES (%s)", (name,))
            refresh_all_manager()
        else:
            app.messagebox.showwarning("Input Error", "Name cannot be empty.", parent=manager_win)

    def update_item():
        new_name, old_name = entry.get().strip(), ""
        if use_treeview:
            if (sel := widget.focus()) and widget.parent(sel):
                old_name = widget.item(sel)['values'][0]
        elif widget.curselection():
            old_name = widget.get(widget.curselection()[0])

        if not old_name:
            return app.messagebox.showwarning("Selection Error", "Please select an item to update.", parent=manager_win)
        if not new_name:
            return app.messagebox.showwarning("Input Error", "New name cannot be empty.", parent=manager_win)

        # Retrieve the ID from the cache_dict, assuming name is unique
        old_id = cache_dict.get(old_name)
        if old_id:
            execute_query(app, f"UPDATE {table_name} SET name = %s WHERE id = %s", (new_name, old_id))
            refresh_all_manager()
        else:
            app.messagebox.showerror("Error", f"Could not find ID for '{old_name}'.", parent=manager_win)

    def delete_item():
        name = ""
        if use_treeview:
            if (sel := widget.focus()) and widget.parent(sel):
                name = widget.item(sel)['values'][0]
        elif widget.curselection():
            name = widget.get(widget.curselection()[0])

        if not name:
            return app.messagebox.showwarning("Selection Error", "Please select an item to delete.", parent=manager_win)

        if app.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'? This is permanent.", parent=manager_win):
            item_id = cache_dict.get(name)
            if item_id:
                execute_query(app, f"DELETE FROM {table_name} WHERE id = %s", (item_id,))
                refresh_all_manager()
            else:
                app.messagebox.showerror("Error", f"Could not find ID for '{name}'.", parent=manager_win)

    btn_frame = app.ttk.Frame(frame)
    btn_frame.pack(fill=app.tk.X, pady=5)
    for cmd, text in [(add_item, "Add"), (update_item, "Update"), (delete_item, "Delete")]:
        app.ttk.Button(btn_frame, text=text, command=cmd).pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=2)
    populate_widget()

def open_department_manager(app):
    """
    Open the Department Manager dialog.
    
    This function launches a dialog for managing academic departments.
    It allows adding, editing, and removing department records.
    
    Args:
        app: The main application instance
        
    Returns:
        None
    """
    _open_generic_manager(app, "Department Manager", app.department_cache, "department", load_departments_to_cache)

def open_academic_year_manager(app):
    """
    Open the Academic Year Manager dialog.
    
    This function launches a dialog for managing academic years.
    It allows adding, editing, and removing academic year records.
    
    Args:
        app: The main application instance
        
    Returns:
        None
    """
    _open_generic_manager(app, "Academic Year Manager", app.academic_year_cache, "academic_year", load_academic_years_to_cache)

def open_class_manager(app):
    """
    Open the Class Manager dialog.
    
    This function launches a dialog for managing class records.
    It provides a treeview interface for better organization.
    
    Args:
        app: The main application instance
        
    Returns:
        None
    """
    _open_generic_manager(app, "Class Manager", app.class_cache, "class", load_class_names_to_cache, use_treeview=True)

def open_subject_manager(app):
    """
    Open the Subject Manager dialog.
    
    This function launches a dialog for managing subject/course records.
    It allows adding, editing, and removing subject records.
    
    Args:
        app: The main application instance
        
    Returns:
        None
    """
    _open_generic_manager(app, "Subject Manager", app.subject_cache, "subject", load_subjects_to_cache)

def open_major_manager(app):
    """
    Open the Major Manager dialog with department associations.
    
    This function provides a specialized dialog for managing academic majors.
    Unlike the generic manager, it handles the relationship between majors and departments.
    
    Args:
        app: The main application instance containing department and major caches
        
    Returns:
        None
        
    Features:
        - Treeview display organized by department
        - Validation to ensure majors are associated with departments
        - Automatic refresh of dependent UI elements
    """
    manager_win = app.tk.Toplevel(app.window)
    manager_win.title("Major Manager")
    manager_win.geometry("550x450")
    manager_win.transient(app.window)
    manager_win.grab_set()

    main_frame = app.ttk.Frame(manager_win, padding=10)
    main_frame.pack(expand=True, fill=app.tk.BOTH)

    tree_frame = app.ttk.LabelFrame(main_frame, text="Majors by Department", padding=5)
    tree_frame.pack(expand=True, fill=app.tk.BOTH, pady=5)
    
    tree = app.ttk.Treeview(tree_frame, columns=("major_name", "major_id"), show="headings")
    tree.heading("major_name", text="Major Name")
    tree.heading("major_id", text="ID")
    tree.column("major_id", width=50, anchor=app.tk.CENTER)
    tree.pack(expand=True, fill=app.tk.BOTH)

    form_frame = app.ttk.Frame(main_frame)
    form_frame.pack(fill=app.tk.X, pady=10)
    form_frame.columnconfigure(1, weight=1)

    app.ttk.Label(form_frame, text="Major Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    major_name_entry = app.ttk.Entry(form_frame)
    major_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    app.ttk.Label(form_frame, text="Department:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    dept_combo = app.ttk.Combobox(form_frame, state="readonly", values=list(app.department_cache.keys()))
    dept_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    def populate_tree():
        for i in tree.get_children(): tree.delete(i)
        rev_dept_cache = {v: k for k, v in app.department_cache.items()}
        majors_data = execute_query(app, "SELECT m.id, m.name, m.department_id FROM major m ORDER BY m.department_id, m.name", fetch='all')
        
        if not majors_data: return

        dept_majors = {}
        for m_id, m_name, d_id in majors_data:
            dept_name = rev_dept_cache.get(d_id, "Unknown Department")
            dept_majors.setdefault(dept_name, []).append((m_name, m_id))
        
        for dept_name in sorted(dept_majors.keys()):
            parent = tree.insert("", "end", text=dept_name, values=(dept_name, ""), open=True)
            for m_name, m_id in dept_majors[dept_name]:
                tree.insert(parent, "end", values=(m_name, m_id))

    def on_tree_select(event):
        if not (selected_item := tree.focus()) or not tree.parent(selected_item): return # Only select actual major items, not department headings
        values = tree.item(selected_item, "values")
        parent_id = tree.parent(selected_item)
        dept_name = tree.item(parent_id, "values")[0] # Get department name from parent node
        major_name_entry.delete(0, app.tk.END)
        major_name_entry.insert(0, values[0])
        dept_combo.set(dept_name)

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    def refresh_all_manager(): # Renamed to differentiate from main app's refresh
        load_majors_to_cache(app)
        load_departments_to_cache(app) # In case department names changed
        app.refresh_treeview()
        populate_tree()
        major_name_entry.delete(0, app.tk.END)
        dept_combo.set("")

    def add_major():
        name, dept_name = major_name_entry.get().strip(), dept_combo.get()
        dept_id = app.department_cache.get(dept_name)

        if not name or not dept_id:
            return app.messagebox.showwarning("Input Error", "Major Name and Department are required.", parent=manager_win)
        
        # Check for duplicate major name within the same department
        existing_majors = execute_query(app, "SELECT id FROM major WHERE name = %s AND department_id = %s", (name, dept_id), fetch='one')
        if existing_majors:
            return app.messagebox.showwarning("Duplicate Entry", f"Major '{name}' already exists in '{dept_name}'.", parent=manager_win)

        execute_query(app, "INSERT INTO major (name, department_id) VALUES (%s, %s)", (name, dept_id))
        refresh_all_manager()

    def update_major():
        if not (selected_item := tree.focus()) or not tree.parent(selected_item):
            return app.messagebox.showwarning("Selection Error", "Please select a major to update.", parent=manager_win)
        
        major_id = tree.item(selected_item, "values")[1] # Get actual major ID
        new_name, new_dept_name = major_name_entry.get().strip(), dept_combo.get()
        new_dept_id = app.department_cache.get(new_dept_name)

        if not new_name or not new_dept_id:
            return app.messagebox.showwarning("Input Error", "New Name and Department are required.", parent=manager_win)

        # Check for duplicate major name within the same new department, excluding the current major
        existing_majors = execute_query(app, "SELECT id FROM major WHERE name = %s AND department_id = %s AND id != %s", (new_name, new_dept_id, major_id), fetch='one')
        if existing_majors:
            return app.messagebox.showwarning("Duplicate Entry", f"Major '{new_name}' already exists in '{new_dept_name}'.", parent=manager_win)

        execute_query(app, "UPDATE major SET name = %s, department_id = %s WHERE id = %s", (new_name, new_dept_id, major_id))
        refresh_all_manager()

    def delete_major():
        if not (selected_item := tree.focus()) or not tree.parent(selected_item):
            return app.messagebox.showwarning("Selection Error", "Please select a major to delete.", parent=manager_win)
        
        major_name, major_id = tree.item(selected_item, "values")
        if app.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{major_name}'? This is permanent.", parent=manager_win):
            execute_query(app, "DELETE FROM major WHERE id = %s", (major_id,))
            refresh_all_manager()

    btn_frame = app.ttk.Frame(main_frame)
    btn_frame.pack(fill=app.tk.X, pady=5)
    app.ttk.Button(btn_frame, text="Add New", command=add_major).pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=2)
    app.ttk.Button(btn_frame, text="Update Selected", command=update_major).pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=2)
    app.ttk.Button(btn_frame, text="Delete Selected", command=delete_major).pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=2)
    populate_tree()

def open_schedule_manager(app):
    """
    Open the Schedule Manager dialog.
    
    This function provides a comprehensive interface for managing class schedules,
    including the association of classes with subjects, days, and time slots.
    
    Args:
        app: The main application instance
        
    Returns:
        None
        
    Features:
        - Visual schedule grid
        - Drag-and-drop support (if implemented)
        - Time conflict detection
        - Batch operations for recurring schedules
    """
    win = app.tk.Toplevel(app.window)
    win.title("Class Schedule Manager")
    win.geometry("800x600")
    win.transient(app.window)
    win.grab_set()
    
    main_frame = app.ttk.Frame(win, padding=10)
    main_frame.pack(expand=True, fill=app.tk.BOTH)
    
    # Treeview to display existing schedules
    tree_frame = app.ttk.LabelFrame(main_frame, text="Existing Schedules", padding=5)
    tree_frame.pack(expand=True, fill=app.tk.BOTH, pady=5)
    tree = app.ttk.Treeview(tree_frame, columns=("id", "class", "subject", "day", "start", "end", "academic_year"), show="headings")
    for col, text, width in [("id", "ID", 40), ("class", "Class", 120), ("subject", "Subject", 120), ("day", "Day", 80), 
                             ("start", "Start", 70), ("end", "End", 70), ("academic_year", "Academic Year", 100)]:
        tree.heading(col, text=text)
        tree.column(col, width=width, anchor=app.tk.CENTER)
    tree.pack(expand=True, fill=app.tk.BOTH)

    # Form for adding/updating schedules
    form_frame = app.ttk.LabelFrame(main_frame, text="Schedule Details", padding=10)
    form_frame.pack(fill=app.tk.X, pady=10)
    form_frame.columnconfigure(1, weight=1)
    form_frame.columnconfigure(3, weight=1)
    
    # Widgets
    app.ttk.Label(form_frame, text="Class:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    class_combo = app.ttk.Combobox(form_frame, state="readonly", values=sorted(list(app.class_cache.keys())))
    class_combo.grid(row=0, column=1, sticky="ew", padx=5)
    
    app.ttk.Label(form_frame, text="Subject:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    subject_combo = app.ttk.Combobox(form_frame, state="readonly", values=sorted(list(app.subject_cache.keys())))
    subject_combo.grid(row=0, column=3, sticky="ew", padx=5)

    app.ttk.Label(form_frame, text="Day of Week:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_combo = app.ttk.Combobox(form_frame, state="readonly", values=days)
    day_combo.grid(row=1, column=1, sticky="ew", padx=5)

    app.ttk.Label(form_frame, text="Start Time (HH:MM):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    start_time_entry = app.ttk.Entry(form_frame)    
    start_time_entry.grid(row=2, column=1, sticky="ew", padx=5)

    app.ttk.Label(form_frame, text="End Time (HH:MM):").grid(row=2, column=2, padx=5, pady=5, sticky="w")
    end_time_entry = app.ttk.Entry(form_frame)
    end_time_entry.grid(row=2, column=3, sticky="ew", padx=5)

    app.ttk.Label(form_frame, text="Academic Year:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    academic_year_combo = app.ttk.Combobox(form_frame, state="readonly", values=sorted(list(app.academic_year_cache.keys())))
    academic_year_combo.grid(row=1, column=3, sticky="ew", padx=5)

    def populate_tree():
        for i in tree.get_children(): tree.delete(i)
        query = """
            SELECT cs.id, c.name, s.name, cs.day_of_week, 
                DATE_FORMAT(cs.start_time, '%H:%i'), DATE_FORMAT(cs.end_time, '%H:%i'),
                COALESCE(ay.name, 'N/A') as academic_year
            FROM class_schedule cs
            JOIN class c ON cs.class_id = c.id
            JOIN subject s ON cs.subject_id = s.id
            LEFT JOIN academic_year ay ON cs.academic_year_id = ay.id
            ORDER BY ay.name, c.name, FIELD(cs.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), cs.start_time
        """
        schedules = execute_query(app, query, fetch='all')
        if schedules:
            for row in schedules: tree.insert("", "end", values=row)

    def on_tree_select(event):
        if not (selected_item := tree.focus()): return
        values = tree.item(selected_item, "values")
        class_combo.set(values[1])
        subject_combo.set(values[2])
        day_combo.set(values[3])
        start_time_entry.delete(0, app.tk.END)
        start_time_entry.insert(0, values[4])
        end_time_entry.delete(0, app.tk.END)
        end_time_entry.insert(0, values[5])
        if len(values) > 6:  # Check if academic year exists in the values
            academic_year_combo.set(values[6])

    def clear_form():
        class_combo.set('')
        subject_combo.set('')
        day_combo.set('')
        start_time_entry.delete(0, app.tk.END)
        end_time_entry.delete(0, app.tk.END)
        academic_year_combo.set('')
        if tree.focus():
            tree.selection_remove(tree.focus())

    def validate_time_format(time_str):
        try:
            app.datetime.strptime(time_str, '%H:%M') # Use app.datetime
            return True
        except ValueError:
            return False

    def save_schedule():
        if not all([class_combo.get(), subject_combo.get(), day_combo.get(), 
                    start_time_entry.get(), end_time_entry.get(), academic_year_combo.get()]):
            return app.messagebox.showwarning("Input Error", "All fields are required!")
            
        if not validate_time_format(start_time_entry.get()) or not validate_time_format(end_time_entry.get()):
            return app.messagebox.showwarning("Input Error", "Invalid time format! Use HH:MM (24-hour format)")
            
        class_id = app.class_cache.get(class_combo.get())
        subject_id = app.subject_cache.get(subject_combo.get())
        academic_year_id = app.academic_year_cache.get(academic_year_combo.get())
        
        if not class_id or not subject_id or not academic_year_id:
            return app.messagebox.showerror("Error", "Invalid class, subject, or academic year selected!")
            
        # Check for time conflicts
        query = """
            SELECT id FROM class_schedule 
            WHERE class_id = %s AND day_of_week = %s 
            AND academic_year_id = %s
            AND (
                (start_time <= TIME(%s) AND end_time > TIME(%s)) OR   -- New event starts during existing
                (start_time < TIME(%s) AND end_time >= TIME(%s)) OR   -- New event ends during existing
                (start_time >= TIME(%s) AND end_time <= TIME(%s))     -- New event is within existing
            )
            AND id != COALESCE(%s, -1)
        """
        params = (
            class_id, day_combo.get(), academic_year_id,
            start_time_entry.get(), start_time_entry.get(),
            end_time_entry.get(), end_time_entry.get(),
            start_time_entry.get(), end_time_entry.get(),
            tree.item(tree.focus())['values'][0] if tree.focus() else None
        )
        
        conflict = execute_query(app, query, params, fetch='one')
        if conflict:
            return app.messagebox.showerror("Conflict", "This time slot conflicts with an existing schedule!")
            
        # Save to database
        if tree.focus():
            # Update existing
            query = """
                UPDATE class_schedule 
                SET class_id = %s, subject_id = %s, day_of_week = %s, 
                    start_time = %s, end_time = %s, academic_year_id = %s
                WHERE id = %s
            """
            data = (
                class_id, subject_id, day_combo.get(),
                start_time_entry.get(), end_time_entry.get(), academic_year_id,
                tree.item(tree.focus())['values'][0]
            )
        else:
            # Insert new
            query = """
                INSERT INTO class_schedule 
                (class_id, subject_id, day_of_week, start_time, end_time, academic_year_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (
                class_id, subject_id, day_combo.get(),
                start_time_entry.get(), end_time_entry.get(), academic_year_id
            )
            
        execute_query(app, query, data)
        populate_tree()
        clear_form()

    def delete_schedule():
        if not (selected_item := tree.focus()):
            return app.messagebox.showwarning("Selection Error", "Please select a schedule to delete.", parent=win)
        schedule_id = tree.item(selected_item, "values")[0]
        if app.messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this schedule entry?", parent=win):
            execute_query(app, "DELETE FROM class_schedule WHERE id = %s", (schedule_id,))
            populate_tree()

    def search_schedule():
        """
        Search schedules based on selected criteria with partial matching support
        - Class: Partial match (case-insensitive)
        - Subject: Exact match
        - Day: Exact match
        - Academic Year: Exact match
        """
        try:
            # Get search criteria
            search_class = class_combo.get().strip()
            search_subject = subject_combo.get().strip()
            search_day = day_combo.get().strip()
            search_year = academic_year_combo.get().strip()
            
            # If all fields are empty, show all records
            if not any([search_class, search_subject, search_day, search_year]):
                return populate_tree()
                
            # Build the base query
            query = """
                SELECT cs.id, c.name, s.name, cs.day_of_week, 
                    DATE_FORMAT(cs.start_time, '%%H:%%i') as start_time, 
                    DATE_FORMAT(cs.end_time, '%%H:%%i') as end_time,
                    COALESCE(ay.name, 'N/A') as academic_year
                FROM class_schedule cs
                JOIN class c ON cs.class_id = c.id
                JOIN subject s ON cs.subject_id = s.id
                LEFT JOIN academic_year ay ON cs.academic_year_id = ay.id
                WHERE 1=1
            """.replace('%%', '%')  # Fix the percentage signs for DATE_FORMAT
            
            conditions = []
            params = []
            
            # Add conditions based on search criteria with partial matching for class
            if search_class:
                conditions.append("c.name LIKE %s")
                params.append(f"%{search_class}%")
            if search_subject:
                conditions.append("s.name = %s")
                params.append(search_subject)
            if search_day:
                conditions.append("cs.day_of_week = %s")
                params.append(search_day)
            if search_year:
                if search_year == 'N/A':
                    conditions.append("ay.name IS NULL")
                else:
                    conditions.append("ay.name = %s")
                    params.append(search_year)
            
            # Add all conditions to the query
            if conditions:
                query += " AND " + " AND ".join(conditions)
                
            # Add ordering
            query += """
                ORDER BY 
                    COALESCE(ay.name, 'ZZZZZZZZZZ') ASC,  # Sort NULLs last
                    c.name ASC,
                    FIELD(cs.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                    cs.start_time
            """
            
            # Clear existing items in treeview
            for item in tree.get_children():
                tree.delete(item)
            
            # Execute query and update treeview
            try:
                schedules = execute_query(app, query, tuple(params) if params else None, fetch='all')
                if schedules:
                    for row in schedules:
                        tree.insert("", "end", values=row)
                else:
                    app.messagebox.showinfo("No Results", "No matching schedules found.", parent=win)
            except Exception as e:
                app.logger.error(f"Database error in search_schedule: {str(e)}")
                app.messagebox.showerror("Search Error", "An error occurred while searching the database.", parent=win)
                # Fall back to showing all schedules
                populate_tree()
                
        except Exception as e:
            app.logger.error(f"Unexpected error in search_schedule: {str(e)}")
            app.messagebox.showerror("Error", "An unexpected error occurred.", parent=win)
            populate_tree()
    
    # Create buttons frame and buttons
    btn_frame = app.ttk.Frame(main_frame)
    btn_frame.pack(fill=app.tk.X, pady=5)
    
    # Add buttons with commands
    buttons = [
        ("Save", save_schedule, "Accent.TButton"),
        ("Clear Form", clear_form, None),
        ("Delete Selected", delete_schedule, None),
        ("Refresh", populate_tree, None),
        ("Search", search_schedule, None),
        ("Close", win.destroy, None)
    ]
    
    for text, command, style in buttons:
        btn = app.ttk.Button(btn_frame, text=text, command=command)
        if style:
            btn.configure(style=style)
        btn.pack(side=app.tk.LEFT, expand=True, fill=app.tk.X, padx=2)
    
    # Set up treeview and populate with data
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    populate_tree()