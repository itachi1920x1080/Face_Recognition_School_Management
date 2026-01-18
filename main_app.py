"""
Main Application Module for Student Management System

This module serves as the entry point for the Student Management System application.
It creates the main application window and coordinates between different components
including database operations, UI rendering, and business logic.

Dependencies:
- tkinter: For GUI components
- mysql.connector: For database connectivity
- opencv-python (cv2): For camera operations
- Pillow (PIL): For image processing
- face_recognition: For facial recognition features (optional)
- tkcalendar: For date selection widgets (optional)
- pandas: For data manipulation
- numpy: For numerical operations
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import mysql.connector
import cv2
from PIL import Image, ImageTk
import io
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import os

# Try to import optional dependencies with fallbacks
# face_recognition is required for "Scan for Attendance" feature
try:
    import face_recognition
except ImportError:
    face_recognition = None
    print("Warning: face_recognition module not installed. Face recognition features will be disabled.")
    print("To enable, install with: pip install face_recognition")

# tkcalendar is required for date selection widgets
try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None
    print("Warning: tkcalendar module not installed. Date selection features will be limited.")
    print("To enable, install with: pip install tkcalendar")
# Import application modules
# UI Components
from ui_components import create_styles, create_widgets

# Student Operations
from student_ops import add_student, update_student, delete_student, search_student,refresh_treeview, clear_all_fields, clear_form_fields, on_tree_select
# Database Utilities
from db_utils import connect_to_database, update_database_schema, execute_query, load_all_caches, \
    load_departments_to_cache, load_majors_to_cache, load_subjects_to_cache,load_class_names_to_cache, load_academic_years_to_cache

# Excel Import/Export
from excel_utils import import_students_from_excel, export_daily_log_to_xlsx

# Camera and Image Processing
from camera_utils import toggle_camera, capture_photo, upload_photo, display_image, \
    clear_photo_display, update_camera_feed

# Management Dialogs
from manager_dialogs import open_department_manager, open_major_manager, open_academic_year_manager, \
    open_class_manager, open_subject_manager, open_schedule_manager

# Attendance Features
from attendance_features import open_record_absence_dialog, open_class_attendance_manager, \
    view_individual_schedule, view_reports, scan_faces_for_attendance




"""
    ui_components.py: សម្រាប់ UI widgets និង style

    student_ops.py: CRUD (Add, Update, Delete, Search student)

    db_utils.py: ភ្ជាប់ DB, បន្ទាន់សម័យ Schema, Load caches

    excel_utils.py: Import/Export Excel/CSV

    camera_utils.py: ថត/បង្ហាញរូបភាព

    manager_dialogs.py: បង្ហាញការគ្រប់គ្រងគ្រប់ប្រភេទ (ជំនាញ, ថ្នាក់, អាណត្តិ…)

    attendance_features.py: កំណត់វត្តមាន
"""
class StudentApp:
    """
    Main application class for the Student Management System.
    
    This class serves as the central controller for the application, managing the GUI,
    database connections, and coordinating between different modules. It provides
    a comprehensive interface for managing student records, attendance, and related data.
    
    Key Features:
    - Student record management (CRUD operations)
    - Department and major management
    - Class and subject management
    - Attendance tracking with face recognition
    - Data import/export via Excel
    - Report generation
    
    The application uses a MySQL database for data persistence and Tkinter for the GUI.
    """
    def __init__(self, window):
        """
        Initialize the Student Management System application.
        
        Args:
            window: The root Tkinter window for the application
            
        Initializes the main application window, sets up the UI components,
        establishes database connection, and loads initial data.
        """
        self.window = window
        self.window.title("Comprehensive Student Management System")
        self.window.geometry("1300x800")
        self.window.resizable(True, True)
        self.window.minsize(1200, 800)
        self.window.configure(bg='#f0f0f0')

        if Calendar is None or face_recognition is None:
            missing = []
            if Calendar is None: missing.append("'tkcalendar'")
            if face_recognition is None: missing.append("'face_recognition'")
            messagebox.showerror(
                "Dependency Missing",
                f"The following libraries are not installed: {', '.join(missing)}.\n"
                f"Please run 'pip install tkcalendar face_recognition' to use this application."
            )
            self.window.destroy()
            return

        # --- State Variables ---
        self.db_connection = None   #attribute ឈ្មោះ db_connection ដោយផ្ដល់តម្លៃដើមជា None ក្នុង context នៃ class/object
        self.camera_running = False
        self.video_capture = None
        self.captured_image_data = None
        self.current_frame = None
        self.department_cache = {}#context នៃ class (OOP), វាកំពុងបង្កើត attribute ឈ្មោះ department_cache ជាមួយនឹងតម្លៃដើមគឺ dictionary ទទេ {} ។
        self.major_cache = {}
        self.subject_cache = {}
        self.class_cache = {}
        self.academic_year_cache = {}
        self.import_options = None

        # Expose common modules to instance for easier access
        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.simpledialog = simpledialog
        self.filedialog = filedialog
        self.mysql_connector = mysql.connector
        self.cv2 = cv2
        self.Image = Image
        self.ImageTk = ImageTk
        self.io = io
        self.date = date
        self.datetime = datetime
        self.timedelta = timedelta
        self.np = np
        self.pd = pd
        self.os = os
        self.face_recognition = face_recognition 
        self.Calendar = Calendar
        # --- UI Setup ---
        create_styles(self)
        create_widgets(self)

        # --- App Start ---
        # Define a helper function to perform initial setup
        def initial_setup():
            connect_to_database(self) #ភ្ជាប់ទៅ DB
            self.refresh_treeview() # បង្ហាញ/ធ្វើបច្ចុប្បន្នភាព UI Treeview

        self.window.after(100, initial_setup) 
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_department_select(self, event=None):
        """
        Handle department selection change event.
        
        This method is triggered when a department is selected from the dropdown.
        It updates the majors dropdown to show only majors belonging to the selected department.
        
        Args:
            event: The event object (default: None)
            
        Returns:
            None
        """
        # Get the selected department ID from cache
        dept_id = self.department_cache.get(self.department_combo.get())
        # Clear current major selection
        self.major_combo.set('')
        
        # Fetch majors for the selected department if a department is selected
        majors = execute_query(
            self, 
            "SELECT name FROM major WHERE department_id = %s ORDER BY name", 
            (dept_id,), 
            fetch='all'
        ) if dept_id else []
        
        # Update the majors dropdown with filtered results
        self.major_combo['values'] = [m[0] for m in majors] if majors else []

    def on_tree_select(self, event=None):
        """
        Handle student selection from the treeview.
        
        This method is called when a student is selected in the main treeview.
        It populates the form fields with the selected student's data.
        
        Args:
            event: The selection event (default: None)
            
        Returns:
            None
        """
        on_tree_select(self, event)

    def add_student(self):
        """
        Add a new student to the database.
        
        This method validates the input fields and calls the student_ops.add_student()
        function to add a new student record to the database.
        
        Returns:
            None
        """
        add_student(self)

    def update_student(self):
        """
        Update an existing student's information.
        
        This method validates the input fields and calls student_ops.update_student()
        to update the selected student's record in the database.
        
        Returns:
            None
        """
        update_student(self)

    def delete_student(self):
        """
        Delete the currently selected student.
        
        This method prompts for confirmation and then calls student_ops.delete_student()
        to remove the selected student from the database.
        
        Returns:
            None
        """
        delete_student(self)

    def search_student(self):
        """
        Search for students based on a search term.
        
        This method prompts the user for a search term and calls student_ops.search_student()
        to find and display matching student records.
        
        Returns:
            None
        """
        search_student(self)

    def refresh_treeview(self):
        """
        Refresh the student treeview with current data.
        
        This method calls student_ops.refresh_treeview() to update the treeview
        with the latest student records from the database.
        
        Returns:
            None
        """
        refresh_treeview(self)

    def clear_form_fields(self):
        """
        Clear all form input fields.
        
        This method calls student_ops.clear_form_fields() to reset all
        input fields in the student form.
        
        Returns:
            None
        """
        clear_form_fields(self)

    def clear_all_fields(self):
        """
        Clear all form fields and reset the form.
        
        This method calls student_ops.clear_all_fields() to clear all input fields
        and reset the form to its initial state.
        
        Returns:
            None
        """
        clear_all_fields(self)

    def import_from_excel(self):
        """
        Import student data from an Excel file.
        
        This method calls excel_utils.import_students_from_excel() to handle
        the import of student records from an Excel file.
        
        Returns:
            None
        """
        import_students_from_excel(self)

    def update_camera_feed(self):
        """
        Update the camera feed display.
        
        This method calls camera_utils.update_camera_feed() to refresh
        the camera preview in the UI.
        
        Returns:
            None
        """
        update_camera_feed(self)

    def toggle_camera(self):
        """
        Toggle the camera on/off.
        
        This method calls camera_utils.toggle_camera() to start or stop
        the camera feed.
        
        Returns:
            None
        """
        toggle_camera(self)

    def capture_photo(self):
        """
        Capture a photo from the camera.
        
        This method calls camera_utils.capture_photo() to take a photo
        from the active camera feed.
        
        Returns:
            None
        """
        capture_photo(self)

    def upload_photo(self):
        """
        Upload a photo from the file system.
        
        This method calls camera_utils.upload_photo() to allow the user
        to select and upload a photo from their computer.
        
        Returns:
            None
        """
        upload_photo(self)

    def display_image(self, image_data):
        """
        Display an image in the UI.
        
        This method calls camera_utils.display_image() to show an image
        in the application's image display area.
        
        Args:
            image_data: Binary image data to display
            
        Returns:
            None
        """
        display_image(self, image_data)

    def clear_photo_display(self):
        """
        Clear the photo display area.
        
        This method calls camera_utils.clear_photo_display() to clear
        the image display area in the UI.
        
        Returns:
            None
        """
        clear_photo_display(self)

    # Manager dialogs
    def open_department_manager(self):
        """
        Open the Department Manager dialog.
        
        This method calls manager_dialogs.open_department_manager() to open
        a dialog for managing departments.
        
        Returns:
            None
        """
        open_department_manager(self)

    def open_major_manager(self):
        """
        Open the Major Manager dialog.
        
        This method calls manager_dialogs.open_major_manager() to open
        a dialog for managing majors.
        
        Returns:
            None
        """
        open_major_manager(self)

    def open_academic_year_manager(self):
        """
        Open the Academic Year Manager dialog.
        
        This method calls manager_dialogs.open_academic_year_manager() to open
        a dialog for managing academic years.
        
        Returns:
            None
        """
        open_academic_year_manager(self)

    def open_class_manager(self):
        """
        Open the Class Manager dialog.
        
        This method calls manager_dialogs.open_class_manager() to open
        a dialog for managing classes.
        
        Returns:
            None
        """
        open_class_manager(self)

    def open_subject_manager(self):
        """
        Open the Subject Manager dialog.
        
        This method calls manager_dialogs.open_subject_manager() to open
        a dialog for managing subjects.
        
        Returns:
            None
        """
        open_subject_manager(self)

    def open_schedule_manager(self):
        """
        Open the Schedule Manager dialog.
        
        This method calls manager_dialogs.open_schedule_manager() to open
        a dialog for managing class schedules.
        
        Returns:
            None
        """
        open_schedule_manager(self)

    # Attendance features
    def open_record_absence_dialog(self):
        open_record_absence_dialog(self)

    def open_class_attendance_manager(self):
        open_class_attendance_manager(self)

    def view_individual_schedule(self):
        view_individual_schedule(self)
    def view_reports(self):
        view_reports(self)

    def scan_faces_for_attendance(self):
        scan_faces_for_attendance(self)

    def perform_scan_with_schedule(self, class_id, subject_id, class_name, subject_name):
        scan_faces_for_attendance(self, class_id, subject_id, class_name, subject_name, from_dialog=True)

    def export_daily_log(self):
        export_daily_log_to_xlsx(self)


    def on_closing(self):
        if self.messagebox.askokcancel("Quit", "Do you want to exit?"):
            if self.camera_running:
                self.toggle_camera() # បញ្ឈប់ camera
            if self.db_connection and self.db_connection.is_connected():
                self.db_connection.close()
            self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()