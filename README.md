"# Face_Recognition_School_Management
STUDENT MANAGEMENT SYSTEM WITH FACE RECOGNITION
===============================================

**Project Overview**
--------------------
This is a comprehensive Student Management System (SMS) with integrated face recognition for attendance. It allows you to manage students, departments, majors, classes, academic years, subjects, schedules, and attendance records. The system features a modern Tkinter GUI, MySQL database backend, Excel import/export, and webcam-based photo capture.

**Main Features**
-----------------
- Add, update, delete, and search student records
- Manage departments, majors, classes, academic years, and subjects
- Assign class schedules
- Record attendance (manual and via face recognition)
- Import/export data using Excel files
- View and generate attendance reports

**How to Use**
--------------
1. **Install Requirements:**
   - Python 3.8+
   - MySQL Server (update credentials in `db_utils.py` if needed)
   - Install Python packages:
     ```
     pip install mysql-connector-python opencv-python pillow pandas numpy tkcalendar face_recognition
     ```

2. **Database Setup:**
   - The app will auto-create the database and tables on first run.
   - Alternatively, run the SQL in `MyDatabase.txt` using a MySQL client.

3. **Run the Application:**
   - Launch with:
     ```
     python main_app.py
     ```
   - The main window will open. Use the left panel for student details and actions, and the right panel for the student list.
    
4. **Key Actions:**
   - Use "Add Student" to create new records.
   - Use "Manage Departments/Majors/Classes/Subjects" to edit lookup tables.
   - Use "Import from Excel" to bulk add students.
   - Use "Start Camera" and "Capture Photo" to take student photos.
   - Use "Scan for Attendance" to mark attendance via face recognition.
   - Use "Export Daily Log" to export attendance to Excel.

**Purpose of Each Code File**
----------------------------

- **main_app.py**: Main entry point. Sets up the GUI, connects modules, and manages the application lifecycle.
- **ui_components.py**: All Tkinter UI widgets, layouts, and styles.
- **student_ops.py**: CRUD operations for students, form handling, and treeview management.
- **db_utils.py**: Database connection, schema creation, query execution, and data caching.
- **excel_utils.py**: Import/export student and attendance data from/to Excel files.
- **camera_utils.py**: Webcam integration, photo capture, image upload, and display.
- **manager_dialogs.py**: Dialogs for managing departments, majors, classes, subjects, and schedules.
- **attendance_features.py**: Attendance recording (manual and face recognition), reporting, and schedule viewing.
- **test.py**: Example/test script for Khmer font entry in Tkinter.
- **MyDatabase.txt**: SQL script to create all tables and insert sample data.

**Notes**
---------
- Update MySQL credentials in `db_utils.py` if your setup is different.
- Face recognition requires good quality student photos.
- For Khmer language support, ensure Khmer fonts are installed on your system.

**Contact**
-----------
For questions or issues, please contact the project maintainer.
"
