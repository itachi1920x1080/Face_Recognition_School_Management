"""
Excel Utilities Module

This module provides functionality for importing student data from Excel files and
exporting attendance records to Excel format in the Student Management System.

Key Features:
- Import student data from Excel spreadsheets
- Export attendance records to Excel
- Data validation and transformation
- Interactive dialogs for import/export configuration

Dependencies:
- pandas: For Excel file handling and data manipulation
- tkinter: For file dialogs and user interface components
- db_utils: For database operations and cache management
- datetime: For date handling
- os: For file path operations
- xlsxwriter: For advanced Excel formatting
"""

import pandas as pd
from tkinter import filedialog, messagebox, Toplevel, StringVar, BOTH, LEFT, CENTER
from tkinter import ttk
from db_utils import execute_query, load_class_names_to_cache, load_academic_years_to_cache, load_subjects_to_cache
from datetime import datetime
import os
import xlsxwriter

# Assuming db_utils, Calendar, etc., are properly defined in the main application file or other modules.
# The code below assumes 'app' is a class instance with attributes like db_connection, class_cache, etc.

def import_students_from_excel(app):
    """
    Import student data from an Excel file into the database.
    
    This function opens a file dialog to select an Excel file, parses the data,
    validates it, and imports student records into the database. It handles
    data transformation and provides feedback on the import results.
    
    Args:
        app: The application instance containing UI elements and database connection
        
    Returns:
        None
        
    File Format Requirements:
        - Must be an Excel (.xlsx) file
        - Should contain columns for at least name and gender
        - Supports both English and Khmer column headers
        
    Note:
        Shows appropriate error messages for invalid data or missing columns
        Provides a summary of imported and skipped records
    """
    file_path = filedialog.askopenfilename(title="Select an Excel File", filetypes=[("Excel Files", "*.xlsx")])
    if not file_path:
        return

    options = _open_import_dialog(app)
    if not options:
        return

    class_name, academic_year_name, major_name = options['class'], options['year'], options['major']

    if not app.major_cache.get(major_name):
        return messagebox.showerror("Import Error", f"Major '{major_name}' not found. Please manage majors first.")
    
    major_id, department_id = app.major_cache[major_name]['id'], app.major_cache[major_name]['dept_id']

    # Ensure class and academic year exist, creating them if necessary.
    for name, cache, table in [(class_name, app.class_cache, "class"), (academic_year_name, app.academic_year_cache, "academic_year")]:
        if not cache.get(name):
            execute_query(app, f"INSERT IGNORE INTO {table} (name) VALUES (%s)", (name,))

    load_class_names_to_cache(app)
    load_academic_years_to_cache(app)

    class_id = app.class_cache.get(class_name)
    acad_year_id = app.academic_year_cache.get(academic_year_name)

    if not class_id or not acad_year_id:
        return messagebox.showerror("Import Error", "Failed to get class or academic year ID after creation.")

    try:
        df = pd.read_excel(file_path, header=0)
        header_map = {
            'លរ': 'list_id', 'ឈ្មោះ': 'name', 'Name': 'name', 
            'ភេទ': 'sex', 'Sex': 'sex', 'ពិន្ទុ': 'score', 'Score': 'score', 
            'អ៊ីមែល': 'email', 'Email': 'email', 'ទូរស័ព្ទ': 'phone', 'Phone': 'phone'
        }
        df.rename(columns=lambda h: str(h).strip(), inplace=True)
        df.rename(columns=header_map, inplace=True)

        if not all(col in df.columns for col in ['name', 'sex']):
            return messagebox.showerror("Import Error", "Excel file is missing required columns.\nPlease ensure it has headers for at least: ឈ្មោះ (Name) and ភេទ (Sex).")

        records_to_insert, skipped_rows = [], []
        for index, row in df.iterrows():
            name_val = str(row.get('name', '')).strip()
            if not name_val:
                continue

            sex_raw = str(row.get('sex', '')).strip()
            db_sex = None
            if sex_raw.upper() in ['ប', 'ប្រុស', 'MALE', 'M']:
                db_sex = 'M'
            elif sex_raw.upper() in ['ស', 'ស្រី', 'FEMALE', 'F']:
                db_sex = 'F'
            
            if not db_sex:
                skipped_rows.append(f"Row {index + 2}: Invalid gender '{sex_raw}' for student '{name_val}'")
                continue

            score_val = pd.to_numeric(row.get('score'), errors='coerce')
            score = 0.0 if pd.isna(score_val) else float(score_val)
            email = str(row.get('email', '')) if pd.notna(row.get('email')) else None
            phone = str(row.get('phone', '')) if pd.notna(row.get('phone')) else None

            records_to_insert.append((name_val, db_sex, score, email, phone, None, department_id, major_id, class_id, acad_year_id))

        if records_to_insert:
            query = "INSERT INTO mystudent (name, sex, score, email, phone, photo, department_id, major_id, class_id, academic_year_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            execute_query(app, query, records_to_insert, many=True)
            summary = f"Successfully added {len(records_to_insert)} students."
            if skipped_rows:
                summary += f"\n\nSkipped {len(skipped_rows)} rows due to errors:\n" + "\n".join(skipped_rows[:5])
                if len(skipped_rows) > 5: summary += "\n..."
            messagebox.showinfo("Import Complete", summary)
            app.refresh_treeview()
        else:
            messagebox.showwarning("Import Warning", "No valid student records were found to import.")
    except Exception as e:
        messagebox.showerror("Import Error", f"An unexpected error occurred: {e}")

def _open_import_dialog(app):
    """
    Display a dialog to collect import configuration options.
    
    This internal function creates a modal dialog that allows the user to
    specify the target class, academic year, and major for the import operation.
    
    Args:
        app: The application instance containing UI elements and caches
        
    Returns:
        dict or None: A dictionary containing the selected options (class, year, major)
                        or None if the dialog was cancelled
                        
    UI Elements:
        - Class selection dropdown (populated from class_cache)
        - Academic year dropdown (populated from academic_year_cache)
        - Major selection dropdown (populated from major_cache)
        - Import/Cancel buttons
    """
    app.import_options = None
    dialog = Toplevel(app.window)
    dialog.title("Import Options")
    dialog.geometry("350x200")
    dialog.resizable(False, False)
    dialog.transient(app.window)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding=15)
    frame.pack(expand=True, fill=BOTH)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="Class Name:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
    class_combo = ttk.Combobox(frame, values=list(app.class_cache.keys()))
    class_combo.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

    ttk.Label(frame, text="Academic Year:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
    year_combo = ttk.Combobox(frame, values=list(app.academic_year_cache.keys()))
    year_combo.grid(row=1, column=1, padx=5, pady=8, sticky="ew")

    ttk.Label(frame, text="Major Name:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
    major_combo = ttk.Combobox(frame, values=list(app.major_cache.keys()), state='readonly')
    major_combo.grid(row=2, column=1, padx=5, pady=8, sticky="ew")

    def on_import():
        if not all([class_combo.get(), year_combo.get(), major_combo.get()]):
            return messagebox.showwarning("Input Error", "All fields are required.", parent=dialog)
        app.import_options = {'class': class_combo.get(), 'year': year_combo.get(), 'major': major_combo.get()}
        dialog.destroy()

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(10,0))
    ttk.Button(btn_frame, text="Import", command=on_import, style="Accent.TButton").pack(side=LEFT, padx=5)
    ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    app.window.wait_window(dialog)
    return app.import_options

def export_daily_log_to_xlsx(app):
    """
    Open an interactive tool to manage and export daily attendance records.
    
    This function provides a comprehensive interface for viewing, editing, and exporting
    attendance records. It includes filtering capabilities, data validation, and 
    Excel export functionality.
    
    Args:
        app: The application instance containing UI elements and database connection
        
    Features:
        - Filter records by class, academic year, subject, and date
        - Interactive calendar for date selection
        - Tabular display of attendance records
        - Inline editing of status and notes
        - Export to Excel functionality
        
    UI Components:
        - Filter controls (class, year, subject, date)
        - Interactive calendar picker
        - Sortable attendance records table
        - Action buttons (Load, Save, Export, Close)
        
    Note:
        - Requires valid selections for class, year, and subject
        - Automatically saves changes when switching between records
        - Provides feedback on export success/failure
    """
    # --- Dialog Setup ---
    dialog = Toplevel(app.window)
    dialog.title("Daily Attendance Management & Export")
    dialog.geometry("850x600")
    dialog.minsize(700, 450)
    dialog.transient(app.window)
    dialog.grab_set()

    main_frame = ttk.Frame(dialog, padding=(15, 15, 15, 0))
    main_frame.pack(expand=True, fill=BOTH)
    main_frame.rowconfigure(1, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # --- Filter Controls ---
    filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding=10)
    filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    
    filter_frame.columnconfigure(1, weight=1) 
    filter_frame.columnconfigure(3, weight=1) 
    filter_frame.columnconfigure(5, weight=1) 
    filter_frame.columnconfigure(6, weight=1) # Spacer column

    ttk.Label(filter_frame, text="Class:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    class_combo = ttk.Combobox(filter_frame, state="readonly", values=sorted(list(app.class_cache.keys())), width=30)
    class_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    ttk.Label(filter_frame, text="Acad.Year:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    year_combo = ttk.Combobox(filter_frame, state="readonly", values=sorted(list(app.academic_year_cache.keys())), width=20)
    year_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    
    ttk.Label(filter_frame, text="Subject:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
    subject_combo = ttk.Combobox(filter_frame, state="readonly", values=sorted(list(app.subject_cache.keys())), width=20)
    subject_combo.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

    ttk.Label(filter_frame, text="Date:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    date_var = StringVar(value=datetime.today().isoformat()[:10])
    ttk.Entry(filter_frame, textvariable=date_var, state="readonly").grid(row=1, column=1, sticky="ew", padx=5)

    def _pick_date_internal():
        picker_win = Toplevel(dialog)
        picker_win.title("Select Date")
        picker_win.transient(dialog)
        picker_win.grab_set()
        
        try:
            current_date = datetime.strptime(date_var.get(), '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            current_date = datetime.now().date()
            
        cal = app.Calendar(
            picker_win, 
            selectmode='day', 
            date_pattern='y-mm-dd',
            year=current_date.year,
            month=current_date.month,
            day=current_date.day
        )
        cal.pack(pady=10, padx=10)
        
        def on_select():
            try:
                selected_date = cal.selection_get()
                if selected_date:
                    date_var.set(selected_date.strftime('%Y-%m-%d'))
            except Exception as e:
                messagebox.showerror("Date Error", f"Invalid date selected: {e}", parent=picker_win)
                return
            picker_win.destroy()
            
        btn_frame = ttk.Frame(picker_win)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Select", command=on_select).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=picker_win.destroy).pack(side=LEFT, padx=5)
        
        picker_win.update_idletasks()
        width = picker_win.winfo_width()
        height = picker_win.winfo_height()
        x = (picker_win.winfo_screenwidth() // 2) - (width // 2)
        y = (picker_win.winfo_screenheight() // 2) - (height // 2)
        picker_win.geometry(f'+{x}+{y}')
    
    ttk.Button(filter_frame, text="📅", command=_pick_date_internal, width=3).grid(row=1, column=2, padx=5)

    # --- Data Display and Editing ---
    tree_frame = ttk.LabelFrame(main_frame, text="Attendance Records", padding=10)
    tree_frame.grid(row=1, column=0, sticky="nsew")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    cols = ("student_name", "subject_name", "status", "notes")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=vsb.set)
    
    tree.heading("student_name", text="Student Name")
    tree.column("student_name", width=200)
    tree.heading("subject_name", text="Subject")
    tree.column("subject_name", width=180)
    tree.heading("status", text="Status")
    tree.column("status", width=100, anchor=CENTER)
    tree.heading("notes", text="Notes")

    records_to_process = {}

    def load_records():
        nonlocal records_to_process
        class_name = class_combo.get()
        log_date_str = date_var.get()
        academic_year_name = year_combo.get()
        subject_name = subject_combo.get()

        if not all([class_name, log_date_str, academic_year_name, subject_name]):
            return messagebox.showwarning("Input Missing", "Please select a class, academic year, subject, and date first.", parent=dialog)

        class_id = app.class_cache.get(class_name)
        acad_year_id = app.academic_year_cache.get(academic_year_name)
        subject_id = app.subject_cache.get(subject_name)

        if not all([class_id, acad_year_id, subject_id]):
            return messagebox.showwarning("Data Error", "One or more selections not found in the database. Please refresh caches or check your data.", parent=dialog)

        all_records_query = """
            SELECT 
                s.id AS student_id, s.name AS student_name, 
                sub.id AS subject_id, sub.name AS subject_name,
                a.status, a.notes
            FROM mystudent s
            LEFT JOIN class_schedule cs ON s.class_id = cs.class_id
            LEFT JOIN subject sub ON cs.subject_id = sub.id
            LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = sub.id AND a.attendance_date = %s
            WHERE s.class_id = %s AND s.academic_year_id = %s AND sub.id = %s
            GROUP BY s.id, sub.id ORDER BY s.name, sub.name
        """
        query_params = (log_date_str, class_id, acad_year_id, subject_id)
        
        try:
            results = execute_query(app, all_records_query, query_params, fetch='all')
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load records:\n{e}", parent=dialog) 
            return
        
        tree.delete(*tree.get_children())
        records_to_process.clear()

        if not results:
            messagebox.showinfo("No Data", "No students or scheduled subjects found for the selected filters.", parent=dialog)
            return

        for row in results:
            student_id, student_name, subject_id, subject_name, status, notes = row
            status = status if status else "A"
            notes = notes if notes else ""
            
            item_id = tree.insert("", "end", values=(student_name, subject_name, status, notes))
            
            records_to_process[item_id] = {
                'student_id': student_id,
                'subject_id': subject_id,
                'attendance_date': log_date_str,
                'status': status,
                'notes': notes
            }

    ttk.Button(filter_frame, text="Load Records", command=load_records).grid(row=1, column=7, padx=10, sticky="e")
    
    def update_attendance():
        """Saves all changes in the treeview to the database with date validation."""
        if not records_to_process:
            return messagebox.showwarning("No Data", "No records loaded to update.", parent=dialog)

        selected_date_str = date_var.get().strip()
        if not selected_date_str:
            return messagebox.showerror("Error", "Please select a date.", parent=dialog)
            
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            return messagebox.showerror("Invalid Date", f"Invalid date format. Please use YYYY-MM-DD format.\nGot: {selected_date_str}", parent=dialog)
            
        today = datetime.now().date()
        if selected_date > today:
            if not messagebox.askyesno("Future Date", f"The selected date ({selected_date}) is in the future. Are you sure you want to record attendance for a future date?", parent=dialog):
                return

        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            if len(values) >= 4:
                status_map = {'P': 'Present', 'A': 'Absent', 'L': 'Late', 'E': 'Excused'}
                status_key = str(values[2]).strip().upper()[:1] if values[2] else 'A'
                status = status_map.get(status_key, 'Absent')
                
                records_to_process[item_id]['status'] = status
                records_to_process[item_id]['notes'] = str(values[3]) if len(values) > 3 and values[3] else ''
                records_to_process[item_id]['attendance_date'] = selected_date_str

        query = """
            INSERT INTO attendance (student_id, subject_id, attendance_date, status, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=VALUES(status), notes=VALUES(notes)
        """
        
        try:
            conn = app.db_connection
            cursor = conn.cursor()
            
            conn.autocommit = False
            data_to_upsert = [
                (rec['student_id'], rec['subject_id'], rec['attendance_date'], 
                 rec['status'], rec['notes'])
                for rec in records_to_process.values()
            ]
            cursor.executemany(query, data_to_upsert)
            
            conn.commit()
            conn.autocommit = True
            messagebox.showinfo("Update Successful", f"Successfully updated {len(data_to_upsert)} attendance records for {selected_date_str}.", parent=dialog)
        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred while updating records:\n{e}", parent=dialog)
            return

    def export_to_xlsx_internal(app):
        """
        Exports the attendance data for the selected class and year to a single XLSX file with student index, 
        name, sex, and dates as columns. Date headers are rotated 90 degrees for better readability.
        """
        selected_class = class_combo.get()
        selected_year = year_combo.get()
        selected_subject = subject_combo.get()

        if not all([selected_class, selected_year, selected_subject]):
            return messagebox.showwarning("Input Missing", "Please select a class, academic year, and subject to export.", parent=dialog)

        class_id = app.class_cache.get(selected_class)
        year_id = app.academic_year_cache.get(selected_year)
        subject_id = app.subject_cache.get(selected_subject)

        if not all([class_id, year_id, subject_id]):
            return messagebox.showwarning("Error", "Selected class, year, or subject not found.", parent=dialog)

        try:
            # Fetch all students for the selected class and year
            student_query = """
                SELECT s.id, s.name, s.sex 
                FROM mystudent s 
                WHERE s.class_id = %s AND s.academic_year_id = %s
                ORDER BY s.name
            """
            students = execute_query(app, student_query, (class_id, year_id), fetch='all')
            
            if not students:
                return messagebox.showwarning("No Data", "No students found for the selected class and year.", parent=dialog)
            
            # Fetch all attendance records for the selected class, year, and subject
            attendance_query = """
                SELECT a.student_id, a.attendance_date, a.status
                FROM attendance a
                JOIN mystudent s ON a.student_id = s.id
                WHERE s.class_id = %s AND s.academic_year_id = %s AND a.subject_id = %s
                ORDER BY a.attendance_date, s.name
            """
            attendance_data = execute_query(app, attendance_query, (class_id, year_id, subject_id), fetch='all')
            
            if not attendance_data:
                messagebox.showwarning("No Data", "No attendance records found for the selected filters.", parent=dialog)
                # Still proceed to create a file with just student names
                dates = []
            else:
                dates = sorted(list(set(rec[1] for rec in attendance_data)))
            
            date_headers = [d.strftime('%m/%d/%y') for d in dates]
            attendance_lookup = {(rec[0], rec[1]): rec[2] for rec in attendance_data}
            
            data_rows = []
            for idx, (student_id, name, sex) in enumerate(students, 1):
                row = [idx, name, sex]
                for date_obj in dates:
                    status = attendance_lookup.get((student_id, date_obj), '')
                    row.append(status[0].upper() if status else 'A')
                data_rows.append(row)
                
            columns = ['No.', 'Name', 'Sex'] + date_headers
            df = pd.DataFrame(data_rows, columns=columns)
            
            clean_class = "".join(c for c in selected_class if c.isalnum())
            clean_year = "".join(c for c in selected_year if c.isalnum())
            clean_subject = "".join(c for c in selected_subject if c.isalnum())
            initial_filename = f"Attendance_{clean_class}_{clean_year}_{clean_subject}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            file_path = filedialog.asksaveasfilename(
                title=f"Save Attendance for {selected_class} - {selected_year}",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=initial_filename
            )
            if not file_path:
                return

            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Attendance', header=False, startrow=2)
                
                workbook = writer.book
                worksheet = writer.sheets['Attendance']

                normal_header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'bottom', 'bottom': 1})
                rotated_header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'bottom', 'bottom': 1, 'rotation': 90})

                for col_num, value in enumerate(df.columns):
                    if col_num < 3:
                        worksheet.write(1, col_num, value, normal_header_format)
                    else:
                        worksheet.write(1, col_num, value, rotated_header_format)
                
                title_text = f"Attendance Record for {selected_class} - {selected_year} ({selected_subject})\nDate: {datetime.now().strftime('%B %d, %Y')}"
                title_format = workbook.add_format({'bold': True, 'size': 14, 'align': 'center', 'valign': 'vcenter'})
                worksheet.merge_range('A1:C1', title_text, title_format)

                for i, col in enumerate(df.columns):
                    if len(df) > 0:
                        max_len = max(len(str(col)), df[col].astype(str).str.len().max())
                    else:
                        max_len = len(str(col))
                    worksheet.set_column(i, i, max_len + 2 if i < 3 else 5)

            messagebox.showinfo("Export Successful", f"Attendance report exported to:\n{file_path}", parent=dialog)

        except Exception as e:
            messagebox.showerror("Export Error", f"An unexpected error occurred during export: {e}", parent=dialog)
            import traceback
            traceback.print_exc()

    def on_double_click(event):
        item_id = tree.focus()
        column = tree.identify_column(event.x)
        col_index = int(column.replace('#', '')) - 1
        
        if col_index not in [2, 3]: return

        x, y, width, height = tree.bbox(item_id, column)
        value = tree.item(item_id, 'values')[col_index]

        if col_index == 2:
            editor = ttk.Combobox(tree_frame, values=['Present', 'Absent', 'Late', 'Excused'])
            editor.set(value)
        else:
            editor = ttk.Entry(tree_frame)
            editor.insert(0, value)
            
        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()

        def save_edit(event):
            new_value = editor.get()
            tree.set(item_id, column, new_value)
            editor.destroy()
            
        editor.bind("<FocusOut>", save_edit)
        if isinstance(editor, ttk.Combobox):
            editor.bind("<<ComboboxSelected>>", save_edit)
        editor.bind("<Return>", save_edit)

    tree.bind("<Double-1>", on_double_click)
    
    button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 10))
    button_frame.grid(row=2, column=0, sticky="ew")
    
    ttk.Button(button_frame, text="✅ Update Attendance", command=update_attendance, style="Accent.TButton").pack(side=LEFT, expand=True, padx=5)
    ttk.Button(button_frame, text="📄 Export to Excel", command=lambda: export_to_xlsx_internal(app)).pack(side=LEFT, expand=True, padx=5)
    ttk.Button(button_frame, text="❌ Close", command=dialog.destroy).pack(side=LEFT, expand=True, padx=5)