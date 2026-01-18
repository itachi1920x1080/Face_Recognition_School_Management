"""
Student Operations Module

This module contains functions for handling all student-related operations in the
Student Management System, including CRUD operations and form handling.

Key Features:
- Student record management (Create, Read, Update, Delete)
- Search functionality
- Form field population and clearing
- Treeview management
- Photo handling

Dependencies:
- tkinter: For GUI components and message boxes
- db_utils: For database operations
- camera_utils: For image display and management
"""

import tkinter as tk
from tkinter import messagebox
from db_utils import execute_query, load_all_caches
from camera_utils import display_image, clear_photo_display

def refresh_treeview(app):
    """
    Clear and repopulate the student treeview with current data.
    
    This function fetches all student records from the database and displays them
    in the main treeview widget. It includes related information from other tables
    such as department, major, class, and academic year.
    
    Args:
        app: The application instance containing the treeview and database connection
        
    Returns:
        None
    """
    for item in app.tree.get_children(): app.tree.delete(item)
    query = """
        SELECT s.id, s.name, d.name, m.name, ay.name, s.sex, s.score, c.name, s.email, s.phone 
        FROM mystudent s 
        LEFT JOIN department d ON s.department_id = d.id
        LEFT JOIN major m ON s.major_id = m.id
        LEFT JOIN class c ON s.class_id = c.id
        LEFT JOIN academic_year ay ON s.academic_year_id = ay.id
        ORDER BY s.name
    """
    rows = execute_query(app, query, fetch='all')
    if rows:
        for row in rows: app.tree.insert("", app.tk.END, values=[(v if v is not None else "") for v in row])
    load_all_caches(app) # Refresh caches as well

def on_tree_select(app, event=None):
    """
    Handle student selection from the treeview and populate form fields.
    
    This function is triggered when a student is selected in the main treeview.
    It retrieves the student's data from the database and populates all form
    fields with the corresponding values.
    
    Args:
        app: The application instance containing UI elements and database connection
        event: The selection event (default: None)
        
    Returns:
        None
    """
    clear_form_fields(app)
    selected_item = app.tree.focus()
    if not selected_item: return
    item_values = app.tree.item(selected_item)['values']
    if not item_values: return
    (student_id, name, dept, major, acad_year, sex, score, s_class, email, phone) = [v if v != 'None' else '' for v in item_values]

    app.id_entry.config(state='normal'); app.id_entry.delete(0, app.tk.END); app.id_entry.insert(0, student_id); app.id_entry.config(state='readonly')
    app.name_entry.delete(0, app.tk.END); app.name_entry.insert(0, name)
    app.department_combo.set(dept)
    app.on_department_select() # Call the bound method
    app.major_combo.set(major)
    app.academic_year_entry.set(acad_year)
    app.sex_var.set(sex)
    app.score_entry.delete(0, app.tk.END); app.score_entry.insert(0, str(score))
    app.class_combo.set(s_class)
    app.email_entry.delete(0, app.tk.END); app.email_entry.insert(0, email)
    app.phone_entry.delete(0, app.tk.END); app.phone_entry.insert(0, phone)

    result = execute_query(app, "SELECT photo FROM mystudent WHERE id = %s", (student_id,), fetch='one')
    if result and result[0]:
        app.captured_image_data = result[0]
        display_image(app, app.captured_image_data)
    else:
        clear_photo_display(app)

def add_student(app):
    """
    Add a new student record to the database.
    
    This function validates the input fields, collects the data from the form,
    and inserts a new student record into the database. It handles photo data
    and relationships with other entities like department, major, class, etc.
    
    Args:
        app: The application instance containing form data and database connection
        
    Returns:
        None
        
    Note:
        Shows appropriate success or error messages to the user.
        Refreshes the treeview after successful addition.
    """
    dept_id = app.department_cache.get(app.department_combo.get())
    major_info = app.major_cache.get(app.major_combo.get())
    major_id = major_info['id'] if major_info else None
    class_id = app.class_cache.get(app.class_combo.get())
    acad_year_id = app.academic_year_cache.get(app.academic_year_entry.get())

    if not all([app.name_entry.get(), app.sex_var.get(), dept_id, major_id, class_id, acad_year_id]):
        return messagebox.showwarning("Input Error", "Name, Sex, and all dropdowns must be filled.")
    try:
        score = float(app.score_entry.get() or 0)
    except ValueError:
        return messagebox.showwarning("Input Error", "Score must be a valid number.")

    query = "INSERT INTO mystudent (name, sex, score, email, phone, photo, department_id, major_id, class_id, academic_year_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    params = (app.name_entry.get(), app.sex_var.get(), score, app.email_entry.get() or None, app.phone_entry.get() or None, app.captured_image_data, dept_id, major_id, class_id, acad_year_id)
    
    new_student_id = execute_query(app, query, params)

    if new_student_id:
        messagebox.showinfo("Success", f"Student added successfully with ID: {new_student_id}")
        refresh_treeview(app)
        
        # Auto-select the newly added student
        for item in app.tree.get_children():
            if str(app.tree.item(item, 'values')[0]) == str(new_student_id):
                app.tree.selection_set(item)
                app.tree.focus(item)
                app.tree.see(item)
                break

def update_student(app):
    """
    Update an existing student's information in the database.
    
    This function validates the input fields, collects the updated data from the form,
    and updates the corresponding student record in the database. It handles all
    related fields including photo data and relationships.
    
    Args:
        app: The application instance containing form data and database connection
        
    Returns:
        None
        
    Note:
        Shows appropriate success or error messages to the user.
        Refreshes the treeview and clears the form after successful update.
    """
    # Get student ID
    student_id = app.id_entry.get()
    if not student_id: return messagebox.showwarning("Selection Error", "Please select a student to update.")
    
    # Get department, major, class, and academic year IDs
    dept_id = app.department_cache.get(app.department_combo.get())
    major_info = app.major_cache.get(app.major_combo.get())
    major_id = major_info['id'] if major_info else None
    class_id = app.class_cache.get(app.class_combo.get())
    acad_year_id = app.academic_year_cache.get(app.academic_year_entry.get())

    if not all([app.name_entry.get(), app.sex_var.get(), dept_id, major_id, class_id, acad_year_id]):
        return messagebox.showwarning("Input Error", "Name, Sex, and all dropdowns must be filled.")
    try:
        score = float(app.score_entry.get() or 0)
    except ValueError:
        return messagebox.showwarning("Input Error", "Score must be a valid number.")

    query = "UPDATE mystudent SET name=%s, sex=%s, score=%s, email=%s, phone=%s, photo=%s, department_id=%s, major_id=%s, class_id=%s, academic_year_id=%s WHERE id=%s"
    params = (app.name_entry.get(), app.sex_var.get(), score, app.email_entry.get() or None, app.phone_entry.get() or None, app.captured_image_data, dept_id, major_id, class_id, acad_year_id, student_id)
    execute_query(app, query, params)
    messagebox.showinfo("Success", "Student updated successfully."); clear_all_fields(app); refresh_treeview(app)

def delete_student(app):
    """
    Delete the currently selected student from the database.
    
    This function prompts for confirmation before deleting the selected student.
    If confirmed, it removes the student record from the database and updates the UI.
    
    Args:
        app: The application instance containing the selected student and database connection
        
    Returns:
        None
        
    Note:
        Shows a confirmation dialog before deletion.
        Shows success message and refreshes the UI after deletion.
    """
    student_id = app.id_entry.get()
    if not student_id: return messagebox.showwarning("Selection Error", "Please select a student to delete.")
    if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete student ID {student_id}? This is permanent."):
        execute_query(app, "DELETE FROM mystudent WHERE id = %s", (student_id,))
        messagebox.showinfo("Success", "Student deleted successfully."); clear_all_fields(app); refresh_treeview(app)

def search_student(app):
    """
    Search for students based on a search term and update the treeview.
    
    This function prompts the user for a search term and performs a case-insensitive
    search across student names, departments, majors, classes, and academic years.
    The results are displayed in the treeview.
    
    Args:
        app: The application instance containing UI elements and database connection
        
    Returns:
        None
        
    Note:
        Shows a message if no results are found.
        The search is performed using SQL LIKE with wildcards.
    """
    search_term = app.simpledialog.askstring("Search", "Enter Name, Class, Department, or Major:")
    if not search_term: return
    for item in app.tree.get_children(): app.tree.delete(item)
    query = """
        SELECT s.id, s.name, d.name, m.name, ay.name, s.sex, s.score, c.name, s.email, s.phone 
        FROM mystudent s 
        LEFT JOIN department d ON s.department_id = d.id 
        LEFT JOIN major m ON s.major_id = m.id
        LEFT JOIN class c ON s.class_id = c.id
        LEFT JOIN academic_year ay ON s.academic_year_id = ay.id
        WHERE s.name LIKE %s OR c.name LIKE %s OR d.name LIKE %s OR m.name LIKE %s OR ay.name LIKE %s
        ORDER BY d.name, m.name, s.name
    """
    params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
    rows = execute_query(app, query, params, fetch='all')
    if not rows:
        messagebox.showinfo("Search Result", f"No records found for '{search_term}'."); refresh_treeview(app)
    else:
        for row in rows: app.tree.insert("", app.tk.END, values=[(v if v is not None else "") for v in row])

def clear_form_fields(app):
    """
    Clear all input fields on the main student form.
    
    This function resets all form fields to their default empty state.
    It also clears any selection in the treeview.
    
    Args:
        app: The application instance containing the form fields
        
    Returns:
        None
    """
    app.id_entry.config(state='normal'); app.id_entry.delete(0, app.tk.END); app.id_entry.config(state='readonly')
    app.name_entry.delete(0, app.tk.END); app.department_combo.set(""); app.major_combo.set(""); app.major_combo['values'] = []
    app.academic_year_entry.set(""); app.sex_var.set(""); app.score_entry.delete(0, app.tk.END); app.class_combo.set("")
    app.email_entry.delete(0, app.tk.END); app.phone_entry.delete(0, app.tk.END); app.name_entry.focus()
    if app.tree.selection(): app.tree.selection_remove(app.tree.selection()[0])

def clear_all_fields(app):
    """
    Clear all input fields and the photo display.
    
    This function extends clear_form_fields() by also clearing any displayed photo.
    It provides a complete reset of the form to its initial state.
    
    Args:
        app: The application instance containing the form fields and photo display
        
    Returns:
        None
    """
    clear_form_fields(app)
    clear_photo_display(app)