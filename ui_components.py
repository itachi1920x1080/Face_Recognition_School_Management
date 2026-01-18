"""
UI Components Module

This module provides all the user interface components for the Student Management System.
It handles the creation and layout of all GUI elements, including forms, buttons, treeviews,
and other interactive components.

Key Features:
- Centralized UI component creation
- Consistent styling and theming
- Responsive layout management
- Reusable UI components

Dependencies:
- tkinter: For basic GUI components
- ttk: For themed widgets
"""

import tkinter as tk
from tkinter import ttk

def create_styles(app):
    """
    Configure and customize the visual styles for all ttk widgets.
    
    This function sets up a consistent visual theme and style for all ttk widgets
    in the application. It defines colors, fonts, and other visual properties.
    
    Args:
        app: The application instance containing the root window
        
    Styles Configured:
        - TLabel: Base label style with Arial 11pt font
        - TButton: Standard button style with hover effects
        - Treeview.Heading: Bold column headers for treeviews
        - Treeview: Custom row height and font for data display
        - Title.TLabel: Large, bold title text
        - Section.TLabelframe.Label: Styled frame headers
        - Accent.TButton: Highlighted action buttons
        
    Note:
        Uses the 'clam' theme as a base for consistent cross-platform appearance.
    """
    style = ttk.Style(app.window)
    style.theme_use("clam")
    style.configure("TLabel", background="#f0f0f0", font=("Arial", 11))
    style.configure("TButton", font=("Arial", 9, "bold"), padding=3)
    style.map("TButton", background=[('active', '#e0e0e0')])
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
    style.configure("Treeview", rowheight=28, font=("Arial", 10))
    style.configure("Title.TLabel", font=("Arial", 20, "bold"), background="#f0f0f0", foreground="#2c3e50")
    style.configure("Section.TLabelframe.Label", font=("Arial", 12, "bold"), background="#f0f0f0")
    style.configure("Accent.TButton", foreground="white", background="navy")

def create_widgets(app):
    """
    Create and arrange all main UI components in the application window.
    
    This is the main layout function that sets up the overall structure of the
    application interface, including the main paned window, scrollable areas,
    and calls to create individual widget groups.
    
    Args:
        app: The application instance containing the root window
        
    Layout Structure:
        - Left Pane (30% width): Scrollable form and controls
            - Student Details form
            - Photo/Camera display
            - Action buttons
        - Right Pane (70% width): Student data table
            - Sortable columns
            - Horizontal and vertical scrolling
            
    Note:
        - Uses a paned window for resizable left/right sections
        - Implements smooth scrolling for the left panel
        - Maintains responsive design principles
    """
    paned_window = ttk.PanedWindow(app.window, orient=tk.HORIZONTAL)
    paned_window.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)

    # --- Scrollable frame for the left pane ---
    left_container = ttk.Frame(paned_window)
    paned_window.add(left_container, weight=1)
    canvas = tk.Canvas(left_container, bg='#f0f0f0', highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="left", fill="y")
    canvas.pack(side="right", fill="both", expand=True)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.columnconfigure(0, weight=1)
    canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

    def on_mouse_wheel(event):
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")
    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    ttk.Label(scrollable_frame, text="Student Management", style="Title.TLabel").pack(pady=(0, 15), padx=10)
    _create_form_widgets(app, scrollable_frame).pack(fill=tk.X, pady=5, padx=10)
    _create_photo_widgets(app, scrollable_frame).pack(fill=tk.BOTH, pady=10, padx=10, expand=True)
    _create_button_widgets(app, scrollable_frame).pack(fill=tk.X, pady=15, padx=10)

    right_pane = ttk.Frame(paned_window)
    paned_window.add(right_pane, weight=3)
    _create_treeview_widgets(app, right_pane).pack(expand=True, fill=tk.BOTH)


def _create_form_widgets(app, parent):
    """
    Create and configure the student details form widgets.
    
    This internal function builds the input form for student information,
    including fields for personal details, academic information, and contact data.
    
    Args:
        app: The application instance for storing widget references
        parent: The parent widget for these form elements
        
    Returns:
        ttk.LabelFrame: The frame containing all form elements
        
    Form Fields:
        - ID (readonly)
        - Name
        - Department (dropdown)
        - Major (dropdown, updates based on department)
        - Academic Year (dropdown)
        - Score
        - Class (dropdown)
        - Email
        - Phone
        - Sex (radio buttons)
        
    Note:
        - Uses grid layout for precise control
        - Implements proper tab order
        - Sets up dynamic updates between dependent fields
    """
    frame = ttk.LabelFrame(parent, text="Student Details", padding=10, style="Section.TLabelframe")
    frame.columnconfigure(1, weight=1)

    fields = {
        "ID:": ("id_entry", "readonly"), "Name:": ("name_entry", "normal"),
        "Department:": ("department_combo", "readonly"), "Major:": ("major_combo", "readonly"),
        "Academic Year:": ("academic_year_entry", "readonly"), "Score:": ("score_entry", "normal"),
        "Class:": ("class_combo", "readonly"), "Email:": ("email_entry", "normal"), "Phone:": ("phone_entry", "normal")
    }

    for row_idx, (label_text, (widget_name, state)) in enumerate(fields.items()):
        ttk.Label(frame, text=label_text).grid(row=row_idx, column=0, padx=5, pady=6, sticky="w")
        widget = ttk.Combobox(frame, state=state) if "combo" in widget_name or "year" in widget_name else ttk.Entry(frame)
        if isinstance(widget, ttk.Combobox):
            if widget_name == "department_combo":
                widget.bind("<<ComboboxSelected>>", app.on_department_select)
        elif state == 'readonly':
            widget.config(state='readonly')
        widget.grid(row=row_idx, column=1, padx=5, pady=6, sticky="ew")
        setattr(app, widget_name, widget)

    row_idx = len(fields)
    ttk.Label(frame, text="Sex:").grid(row=row_idx, column=0, padx=5, pady=6, sticky="w")
    app.sex_var = tk.StringVar()
    sex_frame = ttk.Frame(frame)
    ttk.Radiobutton(sex_frame, text="Male", variable=app.sex_var, value="M").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(sex_frame, text="Female", variable=app.sex_var, value="F").pack(side=tk.LEFT, padx=5)
    sex_frame.grid(row=row_idx, column=1, padx=5, pady=6, sticky="w")
    return frame

def _create_photo_widgets(app, parent):
    """
    Create the photo display area for student photos and camera feed.
    
    This function sets up the container and label for displaying student photos
    or the live camera feed when capturing new images.
    
    Args:
        app: The application instance for storing widget references
        parent: The parent widget for the photo display
        
    Returns:
        ttk.LabelFrame: The frame containing the photo display area
        
    Features:
        - Fixed aspect ratio container
        - Centered placeholder text
        - Groove border for visual separation
        
    Note:
        The actual image display is handled by the camera_utils module
    """
    photo_frame = ttk.LabelFrame(parent, text="Photo / Camera Feed", padding=5, style="Section.TLabelframe")
    photo_frame.rowconfigure(0, weight=1, minsize=250)
    photo_frame.columnconfigure(0, weight=1)
    app.photo_display_label = ttk.Label(photo_frame, text="No Photo", anchor=tk.CENTER, relief="groove")
    app.photo_display_label.grid(row=0, column=0, sticky="nsew")
    return photo_frame

def _create_button_widgets(app, parent):
    """
    Create and organize all action buttons in the application.
    
    This function groups related buttons into labeled frames and assigns
    their respective command handlers from the main application.
    
    Args:
        app: The application instance containing button command methods
        parent: The parent widget for the button containers
        
    Returns:
        ttk.Frame: The container frame holding all button groups
        
    Button Groups:
        1. Management Actions
           - Department, Major, Class management
           - Academic Year and Subject management
           - Schedule management
           
        2. Student & Data Actions
           - CRUD operations
           - Search and refresh
           - Form clearing
           - Report generation
           
        3. Photo & Import
           - Camera controls
           - Photo upload
           - Excel import
           
        4. Attendance & Export
           - Attendance recording
           - Face scanning
           - Data export
           
    Note:
        - Buttons are organized in a grid within their respective frames
        - Uses consistent padding and spacing
        - Implements responsive layout for different window sizes
    """
    frame = ttk.Frame(parent)

    mgmt_frame = ttk.LabelFrame(frame, text="Management Actions", style="Section.TLabelframe", padding=10)
    mgmt_frame.pack(fill=tk.X, pady=5)
    mgmt_buttons = {
        "Manage Departments": app.open_department_manager, "Manage Majors": app.open_major_manager,
        "Manage Classes": app.open_class_manager, "Manage Acad. Years": app.open_academic_year_manager,
        "Manage Subjects": app.open_subject_manager, "Manage Class Schedules": app.open_schedule_manager,
        "View Student Schedule": app.view_individual_schedule
    }
    for i, (text, command) in enumerate(mgmt_buttons.items()):
        ttk.Button(mgmt_frame, text=text, command=command).grid(row=i//3, column=i%3, padx=4, pady=4, sticky="ew")
        mgmt_frame.columnconfigure(i%3, weight=1)

    student_frame = ttk.LabelFrame(frame, text="Student & Data Actions", style="Section.TLabelframe", padding=10)
    student_frame.pack(fill=tk.X, pady=5)
    student_buttons = {
        "Add Student": app.add_student, "Update Selected": app.update_student, "Delete Selected": app.delete_student,
        "Search": app.search_student, "Refresh List": app.refresh_treeview, "Clear Form": app.clear_all_fields,
    }
    for i, (text, command) in enumerate(student_buttons.items()):
        ttk.Button(student_frame, text=text, command=command).grid(row=i//3, column=i%3, padx=4, pady=4, sticky="ew")
        student_frame.columnconfigure(i%3, weight=1)
    
    ttk.Button(student_frame, text="View Reports", command=app.view_reports).grid(row=2, column=0, padx=4, pady=4, sticky="ew")

    photo_frame = ttk.LabelFrame(frame, text="Photo & Import", style="Section.TLabelframe", padding=10)
    photo_frame.pack(fill=tk.X, pady=5)
    app.btn_toggle_cam = ttk.Button(photo_frame, text="Start Camera", command=app.toggle_camera)
    app.btn_toggle_cam.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
    app.btn_capture = ttk.Button(photo_frame, text="Capture Photo", command=app.capture_photo, state=tk.DISABLED)
    app.btn_capture.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    app.btn_upload = ttk.Button(photo_frame, text="Upload Photo", command=app.upload_photo)
    app.btn_upload.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    ttk.Button(photo_frame, text="Import from Excel", command=app.import_from_excel, style="Accent.TButton").grid(row=1, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
    for i in range(3): photo_frame.columnconfigure(i, weight=1)

    attendance_frame = ttk.LabelFrame(frame, text="Attendance & Export", style="Section.TLabelframe", padding=10)
    attendance_frame.pack(fill=tk.X, pady=5)
    attendance_buttons = {
        "Record Single Absence": app.open_record_absence_dialog, "Class Attendance": app.open_class_attendance_manager,
        "Scan for Attendance": app.scan_faces_for_attendance, "Export Daily Log": app.export_daily_log
    }
    for i, (text, command) in enumerate(attendance_buttons.items()):
        ttk.Button(attendance_frame, text=text, command=command).grid(row=i//2, column=i%2, padx=4, pady=4, sticky="ew")
        attendance_frame.columnconfigure(i%2, weight=1)

    ttk.Button(frame, text="Exit Application", command=app.on_closing).pack(fill=tk.X, pady=(10, 0))
    return frame

def _create_treeview_widgets(app, parent):
    """
    Create and configure the main student data table.
    
    This function sets up a sortable, scrollable table for displaying
    student records with columns for all relevant student information.
    
    Args:
        app: The application instance for storing the treeview reference
        parent: The parent widget for the treeview
        
    Returns:
        ttk.Frame: The frame containing the treeview and scrollbars
        
    Columns:
        - ID: Student identifier
        - Name: Full name
        - Department: Department name
        - Major: Major/Program
        - Acad. Year: Academic year
        - Sex: Gender
        - Score: Academic score
        - Class: Class/Group
        - Email: Contact email
        - Phone: Contact number
        
    Features:
        - Horizontal and vertical scrolling
        - Sortable columns
        - Custom column widths and alignment
        - Row selection handling
        
    Note:
        - Uses ttk.Treeview for consistent theming
        - Implements smooth scrolling
        - Handles window resizing
    """
    frame = ttk.Frame(parent)
    scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
    

    columns = ("id", "name", "department", "major", "academic_year", "sex", "score", "class", "email", "phone")
    app.tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    scroll_y.config(command=app.tree.yview)
    scroll_x.config(command=app.tree.xview)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    app.tree.pack(expand=True, fill=tk.BOTH)

    headings = {
        "id": {"text": "ID", "width": 40, "anchor": tk.CENTER},
        "name": {"text": "Name", "width": 180},
        "department": {"text": "Department", "width": 150},
        "major": {"text": "Major", "width": 150},
        "academic_year": {"text": "Acad. Year", "width": 100, "anchor": tk.CENTER},
        "sex": {"text": "Sex", "width": 50, "anchor": tk.CENTER},
        "score": {"text": "Score", "width": 60, "anchor": tk.E},
        "class": {"text": "Class", "width": 80, "anchor": tk.CENTER},
        "email": {"text": "Email", "width": 180},
        "phone": {"text": "Phone", "width": 120}
    }
    for col, props in headings.items():
        app.tree.heading(col, text=props["text"])
        app.tree.column(col, width=props["width"], anchor=props.get("anchor", tk.W), stretch=False if col in ['id', 'sex'] else True)

    app.tree.bind("<<TreeviewSelect>>", app.on_tree_select)
    return frame