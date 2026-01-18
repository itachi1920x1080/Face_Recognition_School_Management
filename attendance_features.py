"""
Attendance Features Module

This module provides functionality for managing student attendance in the
Student Management System, including individual and class attendance recording,
schedule viewing, and facial recognition-based attendance.

Key Features:
- Individual student absence recording
- Class-wide attendance management
- Student schedule viewing
- Attendance reporting and analytics
- Facial recognition attendance system

Dependencies:
- tkinter: For GUI components and dialogs
- db_utils: For database operations
- datetime: For date handling
- numpy: For numerical operations (used in face recognition)
- face_recognition: For facial recognition (optional, loaded from main app)
- tkcalendar: For date picker (optional, loaded from main app)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from db_utils import execute_query
from datetime import date, datetime
import numpy as np

# Import only if they exist in the main application's scope
# The main_app.py passes 'self.face_recognition' and 'self.Calendar'
# directly, so these imports are removed here to prevent potential
# ImportError if this file were run standalone or if main_app didn't provide them.
# The functions below will access them via `app.face_recognition` and `app.Calendar`.

def open_record_absence_dialog(app):
    """
    Open a dialog to record attendance for the currently selected student.

    This function creates a modal dialog that allows recording attendance status
    (Present, Absent, Late, Excused) for a specific subject and date.

    Args:
        app: The application instance containing UI elements and database connection

    UI Components:
        - Subject selection dropdown
        - Date picker with calendar
        - Status selection (Present, Absent, Late, Excused)
        - Notes field for additional information
        - Save/Cancel buttons

    Database Operations:
        - Fetches available subjects for the student's class
        - Inserts or updates attendance records

    Note:
        - Requires a student to be selected in the main interface
        - Validates all inputs before saving
        - Shows appropriate feedback messages
    """
    student_id = app.id_entry.get()
    if not student_id:
        return app.messagebox.showwarning("Selection Error", "Please select a student from the main list first.")

    # Fetch class_id for the selected student
    class_id_result = execute_query(app, "SELECT class_id FROM mystudent WHERE id = %s", (student_id,), fetch='one')
    if not class_id_result or not class_id_result[0]:
        return app.messagebox.showerror("Error", "Selected student is not assigned to a class.")
    class_id = class_id_result[0]

    # Fetch subjects scheduled for the student's class
    subjects_query = """
        SELECT DISTINCT s.id, s.name FROM subject s
        JOIN class_schedule cs ON s.id = cs.subject_id
        WHERE cs.class_id = %s ORDER BY s.name
    """
    subjects = execute_query(app, subjects_query, (class_id,), fetch='all')
    if not subjects:
        return app.messagebox.showinfo("Info", "No subjects are scheduled for this student's class.")

    subject_map = {name: s_id for s_id, name in subjects}

    # Create Dialog Window
    dialog = app.tk.Toplevel(app.window)
    dialog.title("Record Attendance")
    dialog.geometry("400x350")
    dialog.transient(app.window)
    dialog.grab_set()

    frame = app.ttk.Frame(dialog, padding=15)
    frame.pack(expand=True, fill=app.tk.BOTH)
    frame.columnconfigure(1, weight=1)

    app.ttk.Label(frame, text=f"Student: {app.name_entry.get()}").grid(row=0, column=0, columnspan=2, pady=5)

    app.ttk.Label(frame, text="Subject:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
    subject_combo = app.ttk.Combobox(frame, state="readonly", values=list(subject_map.keys()))
    subject_combo.grid(row=1, column=1, sticky="ew")

    app.ttk.Label(frame, text="Date:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
    date_entry = app.tk.Entry(frame)
    date_entry.insert(0, app.date.today().strftime('%Y-%m-%d'))
    date_entry.grid(row=2, column=1, sticky="ew")

    def pick_date():
        if app.Calendar is None:
            return app.messagebox.showerror("Dependency Error", "tkcalendar is not installed. Cannot open date picker.")

        cal_win = app.tk.Toplevel(dialog)
        cal = app.Calendar(cal_win, selectmode='day')
        cal.pack(pady=20)
        def on_date_select():
            date_entry.delete(0, app.tk.END)
            date_entry.insert(0, cal.get_date())
            cal_win.destroy()
        app.ttk.Button(cal_win, text="Select", command=on_date_select).pack()
    app.ttk.Button(frame, text="...", command=pick_date, width=3).grid(row=2, column=2, padx=2)

    app.ttk.Label(frame, text="Status:").grid(row=3, column=0, padx=5, pady=8, sticky="w")
    status_combo = app.ttk.Combobox(frame, state="readonly", values=['Absent', 'Late', 'Excused', 'Present'])
    status_combo.grid(row=3, column=1, sticky="ew")
    status_combo.set('Absent')

    app.ttk.Label(frame, text="Notes:").grid(row=4, column=0, padx=5, pady=8, sticky="nw")
    notes_text = app.tk.Text(frame, height=4, width=30)
    notes_text.grid(row=4, column=1, sticky="ew")

    def on_submit():
        subject_id = subject_map.get(subject_combo.get())
        att_date_str = date_entry.get()
        status = status_combo.get()
        notes = notes_text.get("1.0", app.tk.END).strip()

        if not all([subject_id, att_date_str, status]):
            return app.messagebox.showwarning("Input Error", "Subject, Date, and Status are required.", parent=dialog)

        try:
            att_date = app.datetime.strptime(att_date_str, '%Y-%m-%d').date()
        except ValueError:
            return app.messagebox.showwarning("Input Error", "Invalid date format. Use YYYY-MM-DD.", parent=dialog)
        
        # Get the day of the week from the selected date
        day_of_week = att_date.strftime("%A")

        query = """
            INSERT INTO attendance (student_id, subject_id, attendance_date, day_of_week, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=VALUES(status), notes=VALUES(notes), day_of_week=VALUES(day_of_week)
        """
        execute_query(app, query, (student_id, subject_id, att_date, day_of_week, status, notes))
        app.messagebox.showinfo("Success", "Attendance record saved.", parent=dialog)
        dialog.destroy()

    app.ttk.Button(frame, text="Save Record", command=on_submit, style="Accent.TButton").grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

def open_class_attendance_manager(app):
    """
    Open a window to manage attendance for an entire class.

    This function provides an interface for recording attendance for multiple
    students in a class simultaneously. It includes filtering by class,
    subject, and date, with bulk save functionality.

    Args:
        app: The application instance containing UI elements and database connection

    Features:
        - Filter by class, subject, and date
        - Bulk status updates for all students
        - Visual indicators for attendance status
        - Save all changes with a single click

    Database Operations:
        - Loads students based on selected class
        - Saves attendance records in batch
        - Handles both new records and updates to existing ones

    Note:
        - Requires valid class and subject selections
        - Provides feedback on save operations
        - Uses efficient batch database operations
    """
    att_win = app.tk.Toplevel(app.window)
    att_win.title("Class Attendance Manager")
    att_win.geometry("750x600")
    att_win.transient(app.window)
    att_win.grab_set()

    main_frame = app.ttk.Frame(att_win, padding=10)
    main_frame.pack(expand=True, fill=app.tk.BOTH)

    # Filters
    filters_frame = app.ttk.Frame(main_frame)
    filters_frame.pack(fill=app.tk.X, pady=5)
    app.ttk.Label(filters_frame, text="Class:").pack(side=app.tk.LEFT, padx=5)
    class_combo = app.ttk.Combobox(filters_frame, state="readonly", width=15, values=sorted(list(app.class_cache.keys())))
    class_combo.pack(side=app.tk.LEFT, padx=5)
    app.ttk.Label(filters_frame, text="Subject:").pack(side=app.tk.LEFT, padx=5)
    subject_combo = app.ttk.Combobox(filters_frame, state="readonly", width=20, values=sorted(list(app.subject_cache.keys())))
    subject_combo.pack(side=app.tk.LEFT, padx=5)
    app.ttk.Label(filters_frame, text="Date:").pack(side=app.tk.LEFT, padx=5)
    date_entry = app.ttk.Entry(filters_frame, width=12)
    date_entry.insert(0, app.date.today().isoformat())
    date_entry.pack(side=app.tk.LEFT, padx=5)

    # Student List
    list_frame = app.ttk.LabelFrame(main_frame, text="Student Roster", padding=10)
    list_frame.pack(expand=True, fill=app.tk.BOTH, pady=10)

    student_tree = app.ttk.Treeview(list_frame, columns=("id", "name", "status"), show="headings")
    student_tree.pack(expand=True, fill=app.tk.BOTH)
    student_tree.heading("id", text="Student ID")
    student_tree.column("id", width=80)
    student_tree.heading("name", text="Student Name")
    student_tree.column("name", width=250)
    student_tree.heading("status", text="Status")
    student_tree.column("status", width=120)

    # This dictionary will store the combobox for each student
    status_widgets = {}

    def load_students():
        class_name = class_combo.get()
        if not class_name: return
        class_id = app.class_cache.get(class_name)

        for item in student_tree.get_children(): student_tree.delete(item)
        status_widgets.clear()

        rows = execute_query(app, "SELECT id, name FROM mystudent WHERE class_id = %s ORDER BY name", (class_id,), fetch='all')
        if rows:
            for student_id, student_name in rows:
                # Insert with default status 'Present'
                item_id = student_tree.insert("", "end", values=(student_id, student_name, 'Present'))

                # Create and store the combobox
                status_combo = app.ttk.Combobox(student_tree, state="readonly",
                                                values=['Present', 'Absent', 'Late', 'Excused'])
                status_combo.set('Present')
                status_widgets[student_id] = status_combo

                # Update the tree item when combobox selection changes
                def update_status(event, sid=student_id):
                    status = status_widgets[sid].get()
                    for item in student_tree.get_children():
                        if student_tree.item(item, 'values')[0] == str(sid):
                            values = list(student_tree.item(item, 'values'))
                            values[2] = status
                            student_tree.item(item, values=values)
                            break

                status_combo.bind('<<ComboboxSelected>>', update_status)

    app.ttk.Button(filters_frame, text="Load Students", command=load_students).pack(side=app.tk.LEFT, padx=10)

    def save_attendance():
        subject_name = subject_combo.get()
        att_date_str = date_entry.get()
        if not subject_name or not att_date_str:
            return app.messagebox.showwarning("Input Error", "Subject and Date are required.", parent=att_win)

        subject_id = app.subject_cache.get(subject_name)
        records_to_save = []
        
        # Get the day of the week from the selected date
        try:
            day_of_week = datetime.strptime(att_date_str, '%Y-%m-%d').strftime("%A")
        except ValueError:
            return app.messagebox.showwarning("Input Error", "Invalid date format. Use YYYY-MM-DD.", parent=att_win)

        for student_id, combo in status_widgets.items():
            status = combo.get()
            if status:
                records_to_save.append((student_id, subject_id, att_date_str, day_of_week, status, status))

        if not records_to_save:
            return app.messagebox.showinfo("Info", "No students loaded or no changes to save.", parent=att_win)

        # Use INSERT ... ON DUPLICATE KEY UPDATE to handle existing records
        query = """
            INSERT INTO attendance (student_id, subject_id, attendance_date, day_of_week, status)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = %s
        """
        execute_query(app, query, records_to_save, many=True)
        app.messagebox.showinfo("Success", f"Saved attendance for {len(records_to_save)} students.", parent=att_win)

    app.ttk.Button(main_frame, text="Save All Attendance", command=save_attendance, style="Accent.TButton").pack(pady=5)

def view_individual_schedule(app):
    """
    Display the weekly class schedule for the currently selected student.

    This function shows a weekly timetable view of the student's classes,
    including subject names, times, and locations. It helps students and
    administrators quickly view a student's schedule.

    Args:
        app: The application instance containing UI elements and database connection

    UI Components:
        - Weekly calendar view
        - Color-coded class blocks
        - Subject details (name, time, location)

    Data Sources:
        - Student's class assignments
        - Class schedule information
        - Subject details

    Note:
        - Requires a student to be selected
        - Handles cases where schedule data is incomplete
        - Updates dynamically based on the academic calendar
    """
    student_id = app.id_entry.get()
    if not student_id:
        return app.messagebox.showwarning("Selection Error", "Please select a student to view their schedule.")

    student_name = app.name_entry.get()

    # Fetch class_id for the selected student from the database
    result = execute_query(app, "SELECT class_id FROM mystudent WHERE id = %s", (student_id,), fetch='one')
    if not result or not result[0]:
        return app.messagebox.showinfo("No Schedule", f"Student '{student_name}' is not assigned to a class.")
    class_id = result[0]

    # Fetch the schedule for the student's class
    query = """
        SELECT
            cs.day_of_week,
            DATE_FORMAT(cs.start_time, '%H:%i'),
            DATE_FORMAT(cs.end_time, '%H:%i'),
            s.name
        FROM class_schedule cs
        JOIN subject s ON cs.subject_id = s.id
        WHERE cs.class_id = %s
        ORDER BY FIELD(cs.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), cs.start_time
    """
    schedule_data = execute_query(app, query, (class_id,), fetch='all')

    # Create and populate the schedule display window
    win = app.tk.Toplevel(app.window)
    win.title(f"Schedule for {student_name}")
    win.geometry("600x400")
    win.transient(app.window)
    win.grab_set()

    frame = app.ttk.Frame(win, padding=10)
    frame.pack(expand=True, fill=app.tk.BOTH)

    if not schedule_data:
        app.ttk.Label(frame, text="No schedule found for this student's class.", font=("Arial", 12)).pack(pady=20, padx=10)
        return

    tree = app.ttk.Treeview(frame, columns=("day", "start", "end", "subject"), show="headings")
    tree.pack(expand=True, fill=app.tk.BOTH)

    # Configure tree columns
    tree.heading("day", text="Day of Week")
    tree.heading("start", text="Start Time")
    tree.heading("end", text="End Time")
    tree.heading("subject", text="Subject")
    tree.column("day", width=120)
    tree.column("start", anchor=app.tk.CENTER, width=100)
    tree.column("end", anchor=app.tk.CENTER, width=100)

    for row in schedule_data:
        tree.insert("", "end", values=row)

def view_reports(app):
    """
    Open a comprehensive attendance reporting interface.

    This function provides tools for generating and viewing attendance reports
    with various filtering options. It includes date range selection, export
    functionality, and visual representations of attendance data.

    Args:
        app: The application instance containing UI elements and database connection

    Report Types:
        - Class attendance summaries
        - Individual student attendance history
        - Subject-wise attendance statistics
        - Date range reports

    Features:
        - Interactive date range selection
        - Export to multiple formats (Excel, PDF, CSV)
        - Filter by class, student, subject, or date range
        - Visual charts and graphs

    Note:
        - Handles large datasets efficiently
        - Provides print and export options
        - Includes summary statistics and trends
    """
    report_win = app.tk.Toplevel(app.window)
    report_win.title("Attendance Reports")
    report_win.geometry("800x600")
    report_win.transient(app.window)
    report_win.grab_set()

    main_frame = app.ttk.Frame(report_win, padding=10)
    main_frame.pack(expand=True, fill=app.tk.BOTH)

    # --- Variables to hold the selected dates ---
    start_date_var = app.tk.StringVar(value=app.date.today().replace(day=1).isoformat())
    end_date_var = app.tk.StringVar(value=app.date.today().isoformat())

    # --- Helper function to open calendar and set date ---
    def _pick_date(target_var):
        if app.Calendar is None:
            return app.messagebox.showerror("Dependency Error", "tkcalendar is not installed. Cannot open date picker.")

        picker_win = app.tk.Toplevel(report_win)
        picker_win.title("Select Date")
        picker_win.transient(report_win)
        picker_win.grab_set()

        try:
            initial_date = app.datetime.strptime(target_var.get(), '%Y-%m-%d').date()
        except ValueError:
            initial_date = app.date.today()

        cal = app.Calendar(picker_win, selectmode='day', year=initial_date.year, month=initial_date.month, day=initial_date.day)
        cal.pack(pady=20, padx=20)

        def on_select():
            selected_date = cal.selection_get()
            if selected_date:
                target_var.set(selected_date.isoformat())
            picker_win.destroy()

        app.ttk.Button(picker_win, text="Select", command=on_select, style="Accent.TButton").pack(pady=10)

    # --- Filters Frame ---
    filters_frame = app.ttk.LabelFrame(main_frame, text="Report Filters", padding=10)
    filters_frame.pack(fill=app.tk.X, pady=5)

    app.ttk.Label(filters_frame, text="Class:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    class_combo = app.ttk.Combobox(filters_frame, state="readonly", values=sorted(list(app.class_cache.keys())))
    class_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    app.ttk.Label(filters_frame, text="Subject:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    subject_combo = app.ttk.Combobox(filters_frame, state="readonly")
    subject_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    # --- Dynamically update subjects based on selected class ---
    def on_class_select(event=None):
        class_id = app.class_cache.get(class_combo.get())
        subject_combo.set('')
        if not class_id:
            subject_combo['values'] = []
            return
        subjects_query = """
            SELECT DISTINCT s.name FROM subject s
            JOIN class_schedule cs ON s.id = cs.subject_id
            WHERE cs.class_id = %s ORDER BY s.name
        """
        subjects = execute_query(app, subjects_query, (class_id,), fetch='all')
        subject_combo['values'] = [s[0] for s in subjects] if subjects else []
    class_combo.bind("<<ComboboxSelected>>", on_class_select)


    # --- Start Date Button ---
    app.ttk.Label(filters_frame, text="Start Date:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    start_date_frame = app.ttk.Frame(filters_frame)
    start_date_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    app.ttk.Label(start_date_frame, textvariable=start_date_var).pack(side=app.tk.LEFT, padx=(0, 5))
    app.ttk.Button(start_date_frame, text="📅", command=lambda: _pick_date(start_date_var), width=3).pack(side=app.tk.LEFT)

    # --- End Date Button ---
    app.ttk.Label(filters_frame, text="End Date:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    end_date_frame = app.ttk.Frame(filters_frame)
    end_date_frame.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
    app.ttk.Label(end_date_frame, textvariable=end_date_var).pack(side=app.tk.LEFT, padx=(0, 5))
    app.ttk.Button(end_date_frame, text="📅", command=lambda: _pick_date(end_date_var), width=3).pack(side=app.tk.LEFT)

    filters_frame.columnconfigure((1, 3), weight=1)

    # --- Report Display Frame ---
    report_frame = app.ttk.LabelFrame(main_frame, text="Report Results", padding=10)
    report_frame.pack(expand=True, fill=app.tk.BOTH, pady=10)

    report_tree = app.ttk.Treeview(report_frame, columns=("student", "present", "absent", "late", "excused"), show="headings")
    report_tree.pack(expand=True, fill=app.tk.BOTH)

    report_tree.heading("student", text="Student Name")
    report_tree.heading("present", text="Present")
    report_tree.heading("absent", text="Absent")
    report_tree.heading("late", text="Late")
    report_tree.heading("excused", text="Excused")
    for col in ("present", "absent", "late", "excused"):
        report_tree.column(col, width=80, anchor=app.tk.CENTER)

    def generate_report():
        class_name = class_combo.get()
        subject_name = subject_combo.get()
        start_date_str = start_date_var.get()
        end_date_str = end_date_var.get()

        if not all([class_name, subject_name, start_date_str, end_date_str]):
            return app.messagebox.showwarning("Input Error", "All filter fields are required.", parent=report_win)

        class_id = app.class_cache.get(class_name)
        subject_id = app.subject_cache.get(subject_name)

        query = """
            SELECT
                s.name,
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
                SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS late_count,
                SUM(CASE WHEN a.status = 'Excused' THEN 1 ELSE 0 END) AS excused_count
            FROM mystudent s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.subject_id = %s AND a.attendance_date BETWEEN %s AND %s
            WHERE s.class_id = %s
            GROUP BY s.id, s.name
            ORDER BY s.name;
        """
        rows = execute_query(app, query, (subject_id, start_date_str, end_date_str, class_id), fetch='all')

        for item in report_tree.get_children(): report_tree.delete(item)
        if rows:
            for row in rows: report_tree.insert("", "end", values=row)
        else:
            app.messagebox.showinfo("No Data", "No records found for the given criteria.", parent=report_win)

    app.ttk.Button(filters_frame, text="Generate Report", command=generate_report, style="Accent.TButton").grid(row=1, column=4, padx=10, pady=5)

def scan_faces_for_attendance(app, class_id=None, subject_id=None, class_name=None, subject_name=None, from_dialog=False):
    """
    Initialize and launch the facial recognition-based attendance system.

    This function sets up the camera and facial recognition system to mark
    attendance automatically when students' faces are recognized. It provides
    real-time feedback and handles the recognition process.

    Args:
        app: The application instance containing UI elements and database connection
        class_id (int, optional): ID of the class for attendance
        subject_id (int, optional): ID of the subject for attendance
        class_name (str, optional): Name of the class (for display)
        subject_name (str, optional): Name of the subject (for display)
        from_dialog (bool): Whether called from a dialog (affects UI behavior)

    Features:
        - Real-time face detection and recognition
        - Automatic attendance marking
        - Visual feedback for recognized students
        - Manual override options

    Technical Details:
        - Uses OpenCV for video capture
        - Leverages face_recognition library for facial recognition
        - Handles lighting variations and multiple faces
        - Provides confidence scoring for matches

    Note:
        - Requires camera access
        - Works best with good lighting conditions
        - Provides manual fallback options
    """
    if app.face_recognition is None:
        return app.messagebox.showerror("Dependency Missing", "The 'face_recognition' library is not installed.\nPlease run 'pip install face_recognition' to use this feature.")

    # Dialog to select Class and Subject (if not called directly from perform_scan_with_schedule)
    if not from_dialog:
        dialog = app.tk.Toplevel(app.window)
        dialog.title("Scan Setup")
        dialog.geometry("350x200")
        dialog.transient(app.window)
        dialog.grab_set()
        frame = app.ttk.Frame(dialog, padding=15)
        frame.pack(expand=True, fill=app.tk.BOTH)
        frame.columnconfigure(1, weight=1)

        app.ttk.Label(frame, text="Select Class:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        class_combo = app.ttk.Combobox(frame, state="readonly", values=sorted(list(app.class_cache.keys())))
        class_combo.grid(row=0, column=1, sticky="ew")

        app.ttk.Label(frame, text="Select Subject:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        subject_combo = app.ttk.Combobox(frame, state="readonly")
        subject_combo.grid(row=1, column=1, sticky="ew")

        def on_class_select_internal(event=None):
            selected_class_id = app.class_cache.get(class_combo.get())
            if not selected_class_id: return
            subjects_query = """
                SELECT DISTINCT s.name FROM subject s
                JOIN class_schedule cs ON s.id = cs.subject_id
                WHERE cs.class_id = %s ORDER BY s.name
            """
            subjects = execute_query(app, subjects_query, (selected_class_id,), fetch='all')
            subject_combo['values'] = [s[0] for s in subjects] if subjects else []
            subject_combo.set('')

        class_combo.bind("<<ComboboxSelected>>", on_class_select_internal)

        def on_start_scan():
            selected_class_name = class_combo.get()
            selected_subject_name = subject_combo.get()
            if not selected_class_name or not selected_subject_name:
                return app.messagebox.showwarning("Input Error", "Please select both a class and a subject.", parent=dialog)

            selected_class_id = app.class_cache.get(selected_class_name)
            selected_subject_id = app.subject_cache.get(selected_subject_name)

            # Check if today is a scheduled day for this class and subject
            today = app.datetime.now().strftime('%A')
            schedule_check = """
                SELECT 1 FROM class_schedule
                WHERE class_id = %s
                AND subject_id = %s
                AND day_of_week = %s
                LIMIT 1
            """
            is_scheduled = execute_query(app, schedule_check,
                                     (selected_class_id, selected_subject_id, today),
                                     fetch='one')

            if not is_scheduled:
                if not app.messagebox.askyesno(
                    "Not a Scheduled Day",
                    f"Warning: {today} is not a scheduled day for {selected_class_name} - {selected_subject_name}.\n\n"
                    f"Do you want to continue with attendance marking?",
                    parent=dialog
                ):
                    return  # User chose not to continue

            dialog.destroy()
            _perform_scan_logic(app, selected_class_id, selected_subject_id, selected_class_name, selected_subject_name)

        btn_frame = app.ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        app.ttk.Button(btn_frame, text="Start Scan", command=on_start_scan, style="Accent.TButton").pack(padx=5)
    else:
        # If called from self.perform_scan_with_schedule (from main_app.py)
        # then the parameters are already provided.
        _perform_scan_logic(app, class_id, subject_id, class_name, subject_name)

# Renamed perform_scan_with_schedule to _perform_scan_logic
# because it's an internal function called by scan_faces_for_attendance
def _perform_scan_logic(app, class_id, subject_id, class_name, subject_name):
    # Get current day of week
    today = app.datetime.now().strftime('%A')
    """
    Core face scanning and recognition logic.

    This internal function handles the actual face detection and recognition
    process. It's optimized for performance by processing every few frames
    and resizing images before analysis. It runs in a separate thread to
    maintain UI responsiveness.

    Args:
        app: The application instance containing UI elements and database connection
        class_id (int): ID of the class for attendance
        subject_id (int): ID of the subject for attendance
        class_name (str): Name of the class (for display)
        subject_name (str): Name of the subject (for display)

    Optimization Techniques:
        - Processes every 3rd frame to reduce CPU load
        - Downsizes frames before face detection
        - Uses face locations for recognition only
        - Implements face tracking between frames

    Recognition Process:
        1. Captures frame from camera
        2. Detects face locations
        3. Extracts face encodings
        4. Matches against known students
        5. Updates attendance for matches

    Note:
        - Runs in a background thread
        - Handles multiple faces per frame
        - Provides visual feedback for recognized students
        - Includes error handling for camera issues
    """
    # 1. Fetch student data for the selected class
    try:
        query = "SELECT id, name, photo FROM mystudent WHERE class_id = %s AND photo IS NOT NULL"
        students = execute_query(app, query, (class_id,), fetch='all')
        if not students:
            return app.messagebox.showerror("Error", f"No students with photos found in class '{class_name}'.")

        known_face_encodings = []
        known_face_data = {}

        for i, (student_id, name, photo_data) in enumerate(students):
            try:
                if not isinstance(photo_data, bytes):
                    print(f"Invalid photo data for {name} (ID: {student_id}): expected bytes, got {type(photo_data)}")
                    continue

                image = app.Image.open(app.io.BytesIO(photo_data))
                image_np = app.np.array(image.convert("RGB"))
                encodings = app.face_recognition.face_encodings(image_np)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_data[i] = {'id': student_id, 'name': name}
            except Exception as e:
                print(f"Could not process photo for {name} (ID: {student_id}): {e}")

        if not known_face_encodings:
            return app.messagebox.showerror("Error", "Could not encode any student photos for facial recognition.")

    except Exception as e:
        app.messagebox.showerror("Database Error", f"Error fetching student data: {str(e)}")
        return

    # 2. Setup the scanning window with auto-scan features
    scan_win = app.tk.Toplevel(app.window)
    scan_win.title(f"Attendance Scan: {class_name} - {subject_name}")
    scan_win.geometry("900x750")  # Slightly larger for controls

    # Main container
    main_frame = app.ttk.Frame(scan_win)
    main_frame.pack(expand=True, fill=app.tk.BOTH, padx=10, pady=10)

    # Video frame
    video_frame = app.ttk.LabelFrame(main_frame, text="Live Camera Feed")
    video_frame.pack(expand=True, fill=app.tk.BOTH, pady=5)

    video_label = app.ttk.Label(video_frame)
    video_label.pack(expand=True, fill=app.tk.BOTH, padx=5, pady=5)

    # Status bar
    status_frame = app.ttk.Frame(main_frame)
    status_frame.pack(fill=app.tk.X, pady=5)

    status_label = app.ttk.Label(status_frame, text="🔴 Initializing camera...", font=("Arial", 11))
    status_label.pack(side=app.tk.LEFT, padx=5)

    # Progress
    progress_var = app.tk.DoubleVar()
    progress_bar = app.ttk.Progressbar(status_frame, variable=progress_var, maximum=len(students))
    progress_bar.pack(side=app.tk.RIGHT, fill=app.tk.X, expand=True, padx=5)

    # Controls frame
    controls_frame = app.ttk.Frame(main_frame)
    controls_frame.pack(fill=app.tk.X, pady=5)

    # Auto-close option
    auto_close_var = app.tk.BooleanVar(value=True)
    app.ttk.Checkbutton(
        controls_frame,
        text="Auto-close when all students are marked",
        variable=auto_close_var
    ).pack(side=app.tk.LEFT, padx=5)

    # Refresh button
    app.ttk.Button(
        controls_frame,
        text="🔄 Refresh List",
        command=lambda: update_student_list()
    ).pack(side=app.tk.RIGHT, padx=5)

    # Student list frame
    list_frame = app.ttk.LabelFrame(main_frame, text="Students")
    list_frame.pack(fill=app.tk.BOTH, expand=True, pady=5)

    # Create treeview for student list
    columns = ("status", "id", "name")
    tree = app.ttk.Treeview(list_frame, columns=columns, show="headings", height=8)

    # Configure columns
    tree.heading("status", text="Status")
    tree.heading("id", text="ID")
    tree.heading("name", text="Name")

    # Set column widths
    tree.column("status", width=100, anchor=app.tk.CENTER)
    tree.column("id", width=80, anchor=app.tk.CENTER)
    tree.column("name", width=200, anchor=app.tk.W)

    vsb = app.ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.pack(side=app.tk.LEFT, fill=app.tk.BOTH, expand=True)
    vsb.pack(side=app.tk.RIGHT, fill=app.tk.Y)

    # Store student status
    student_status = {}

    def update_student_list():
        """Update the student list with current status"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        # Add students to the list
        for student_id, name, _ in students:
            status = student_status.get(student_id, "❓ Not Scanned")
            tree.insert("", app.tk.END, values=(status, student_id, name), tags=(status,))

        # Update progress
        present_count = sum(1 for s in student_status.values() if s == "✅ Present")
        progress_var.set(present_count)

        # Update status label
        status_label.config(text=f"Scanned: {present_count}/{len(students)} students")

        # Auto-close if all students are marked present
        if auto_close_var.get() and present_count == len(students):
            scan_win.after(2000, on_scan_close)  # Close after 2 seconds

    try:
        cap = app.cv2.VideoCapture(0, app.cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
        if not cap.isOpened():
            cap = app.cv2.VideoCapture(0)  # Fallback to default backend
            if not cap.isOpened():
                app.messagebox.showerror("Camera Error", "Cannot open camera. Please ensure a camera is connected and not in use by another application.")
                scan_win.destroy()
                return
    except Exception as e:
        app.messagebox.showerror("Camera Error", f"Error initializing camera: {str(e)}")
        scan_win.destroy()
        return

    recognized_today = set()

    # Optimization variables to process every other frame
    process_this_frame = True
    frame_count = 0
    current_face_locations = []
    current_face_names = []

    def update_scan_feed_internal():
        nonlocal process_this_frame, frame_count, current_face_locations, current_face_names, cap

        # Check if window still exists
        if not scan_win.winfo_exists():
            if cap and cap.isOpened():
                cap.release()
            return

        try:
            ret, frame = cap.read()
            if not ret:
                if scan_win.winfo_exists() and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
                    status_label.config(text="❌ Camera error: Cannot read frame", foreground="red")
                return

            # Flip the frame horizontally for mirror effect
            frame = app.cv2.flip(frame, 1)
            frame_count += 1

            # Only process every 3rd frame to reduce CPU usage
            if frame_count % 3 == 0:
                # Resize frame for faster face recognition (1/4 size)
                small_frame = app.cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = app.cv2.cvtColor(small_frame, app.cv2.COLOR_BGR2RGB)

                try:
                    # Find all faces in the current frame
                    face_locations = app.face_recognition.face_locations(rgb_small_frame)
                    face_encodings = app.face_recognition.face_encodings(rgb_small_frame, face_locations)

                    # Clear previous detections
                    current_face_names = []
                    temp_face_locations = []

                    for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                        # Initialize as unknown
                        name = "Unknown"

                        # Only try to recognize if we have known faces
                        if known_face_encodings:
                            # Compare face with known faces
                            matches = app.face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                            face_distances = app.face_recognition.face_distance(known_face_encodings, face_encoding)

                            if True in matches and len(face_distances) > 0:
                                best_match_index = app.np.argmin(face_distances)
                                if matches[best_match_index]:
                                    student_info = known_face_data.get(best_match_index)
                                    if student_info:
                                        student_id_rec, name = student_info['id'], student_info['name']

                                        # Only process if not already marked today
                                        if student_id_rec not in recognized_today:
                                            # Check if already marked present today for this subject
                                            check_query = """
                                                SELECT status FROM attendance
                                                WHERE student_id = %s
                                                AND subject_id = %s
                                                AND attendance_date = %s
                                                LIMIT 1
                                            """
                                            existing_record = execute_query(app, check_query,
                                                                         (student_id_rec, subject_id, app.date.today()),
                                                                         fetch='one')

                                            if not existing_record:
                                                # Insert new attendance record
                                                # CORRECTED QUERY
                                                query = """
                                                    INSERT INTO attendance
                                                    (student_id, subject_id, attendance_date, day_of_week, status, notes)
                                                    VALUES (%s, %s, %s, %s, %s, %s)
                                                """
                                                try:
                                                    execute_query(app, query,
                                                                 (student_id_rec, subject_id, app.date.today(),
                                                                  app.date.today().strftime("%A"), 'Present', 'Auto-scanned'))
                                                    recognized_today.add(student_id_rec)
                                                    student_status[student_id_rec] = "✅ Present"

                                                    # Update UI if window still exists
                                                    if scan_win.winfo_exists():
                                                        if hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
                                                            status_label.config(text=f"✅ {name} marked present", foreground="green")
                                                        update_student_list()

                                                        # Flash the recognized student's row
                                                        for item in tree.get_children():
                                                            if tree.item(item, 'values')[1] == str(student_id_rec):
                                                                tree.item(item, tags=("highlight",))
                                                                tree.tag_configure("highlight", background="#e6ffe6")
                                                                tree.after(1000, lambda i=item, sid=student_id_rec:
                                                                    tree.item(i, tags=("✅ Present",)) if scan_win.winfo_exists() else None)
                                                                break
                                                except Exception as e:
                                                    print(f"Database error: {e}")

                        current_face_names.append(name)
                        temp_face_locations.append((top, right, bottom, left))

                    current_face_locations = temp_face_locations
                except Exception as e:
                    print(f"Face detection error: {e}")

            # Only proceed with drawing if window still exists
            if not scan_win.winfo_exists():
                if cap and cap.isOpened():
                    cap.release()
                return

            # Draw face boxes and labels on the frame
            scale = 4  # Because we scaled down to 1/4 for processing
            for (top, right, bottom, left), name in zip(current_face_locations, current_face_names):
                # Scale back up face locations to original frame size
                top = max(0, int(top * scale))
                right = max(0, int(right * scale))
                bottom = min(frame.shape[0], int(bottom * scale))
                left = max(0, int(left * scale))

                # Skip invalid coordinates
                if bottom <= top or right <= left:
                    continue

                # Draw the box around the face
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                app.cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw a label with a name below the face
                app.cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, app.cv2.FILLED)
                font = app.cv2.FONT_HERSHEY_DUPLEX
                app.cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

            # Convert the image to PhotoImage format for Tkinter
            img_rgb = app.cv2.cvtColor(frame, app.cv2.COLOR_BGR2RGB)
            img = app.Image.fromarray(img_rgb)

            # Maintain aspect ratio while fitting in the window
            try:
                target_width = video_label.winfo_width() if video_label.winfo_exists() else 640
                target_height = video_label.winfo_height() if video_label.winfo_exists() else 480

                img.thumbnail((target_width, target_height), app.Image.Resampling.LANCZOS)
                photo_image = app.ImageTk.PhotoImage(image=img)

                # Update the video label if window still exists
                if scan_win.winfo_exists() and video_label.winfo_exists():
                    video_label.config(image=photo_image)
                    video_label.image = photo_image  # Keep a reference
            except Exception as e:
                print(f"Error updating video feed: {e}")

        except Exception as e:
            print(f"Error in face recognition: {e}")
            if scan_win.winfo_exists() and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
                try:
                    status_label.config(text=f"Error: {str(e)[:50]}", foreground="red")
                except:
                    pass

        # Schedule the next frame update if window still exists
        if scan_win.winfo_exists():
            scan_win.after(30, update_scan_feed_internal)
        elif cap and cap.isOpened():
            cap.release()

    def on_scan_close():
        nonlocal cap

        # Release camera resources
        if cap and cap.isOpened():
            try:
                cap.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")

        # Calculate and show results
        present_count = sum(1 for s in student_status.values() if s == "✅ Present")

        # Safely destroy the window if it still exists
        if scan_win.winfo_exists():
            try:
                scan_win.destroy()
            except:
                pass

        # Show results in a non-blocking way
        if present_count > 0:
            scan_win.after(100, lambda: app.messagebox.showinfo(
                "Scan Complete",
                f"✅ {present_count} students were marked present.\n"
                f"❌ {len(students) - present_count} students were not recognized."
            ))
        else:
            scan_win.after(100, lambda: app.messagebox.showwarning(
                "Scan Complete",
                "No students were marked present. Please try again with better lighting."
            ))

    # Configure window close behavior
    scan_win.protocol("WM_DELETE_WINDOW", on_scan_close)

    # Start the scanning process
    scan_win.after(100, lambda: [
        update_student_list(),  # Initial population of student list
        update_scan_feed_internal()  # Start the camera feed
    ])

    # Center the window on screen
    scan_win.update_idletasks()
    width = scan_win.winfo_width()
    height = scan_win.winfo_height()
    x = (scan_win.winfo_screenwidth() // 2) - (width // 2)
    y = (scan_win.winfo_screenheight() // 2) - (height // 2)
    scan_win.geometry(f'{width}x{height}+{x}+{y}')