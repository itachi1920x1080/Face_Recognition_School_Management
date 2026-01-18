"""
Database Utilities Module

This module provides database connectivity and utility functions for the Student Management System.
It handles all database operations including connection management, schema updates, and data caching.

Key Features:
- Database connection and initialization
- Schema management and updates
- Query execution with error handling
- Data caching for improved performance

Dependencies:
- mysql.connector: For MySQL database connectivity
- tkinter.messagebox: For displaying error messages
"""

import mysql.connector
from tkinter import messagebox

# Placeholder for MySQL credentials - **IMPORTANT: Change these for production**
# It's recommended to load these from environment variables or a secure config file.
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307, # Ensure this port is consistent with your MySQL server
    'user': 'root',
    'password': 'n9*xVz2Je~D.-f*', # ⚠️ CHANGE THIS TO YOUR MYSQL PASSWORD
    'database': 'records'
}

def connect_to_database(app):
    """
    Establish a connection to the MySQL database and create it if it doesn't exist.
    
    This function attempts to connect to the 'records' database. If the database doesn't exist,
    it will be created automatically. After a successful connection, it updates the database
    schema and loads all caches.
    
    Args:
        app: The main application instance containing database configuration
        
    Returns:
        None
        
    Raises:
        mysql.connector.Error: If there's an error connecting to the database
    """
    try:
        app.db_connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        if app.db_connection.is_connected():
            update_database_schema(app)
            load_all_caches(app)
            # app.refresh_treeview() # refresh_treeview is in student_ops, main_app calls it via self.refresh_treeview.
                                    # It's better to let main_app handle initial refresh after connect_to_database.
    except mysql.connector.Error as e:
        if e.errno == 1049: # Database doesn't exist
            try:
                # Establish connection without specifying database to create it
                conn = mysql.connector.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'], # Use consistent port
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'] # Use consistent password
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                conn.close()
                # Retry connecting to the now-created database
                connect_to_database(app)
            except mysql.connector.Error as e_create:
                messagebox.showerror("Database Creation Error", f"Failed to create database '{DB_CONFIG['database']}': {e_create}")
                app.window.destroy()
        else:
            messagebox.showerror("Database Error", f"Failed to connect or update schema:\n{e}")
            app.window.destroy()

def insert_sample_data(app):
    """
    Insert sample data into the database if tables are empty.
    
    This function populates the database with initial sample data for demonstration
    and testing purposes. It checks if tables are empty before inserting data
    to avoid duplicate entries.
    
    Args:
        app: The application instance with database connection
        
    Returns:
        None
    """
    cursor = app.db_connection.cursor(buffered=True)
    
    try:
        # Check if any data exists in the department table
        cursor.execute("SELECT COUNT(*) FROM department")
        if cursor.fetchone()[0] == 0:
            # Insert sample departments
            departments = [
                ('Computer Science',),
                ('Information Technology',),
                ('Electrical Engineering',),
                ('Business Administration',)
            ]
            cursor.executemany("INSERT IGNORE INTO department (name) VALUES (%s)", departments)
            app.db_connection.commit()
            
            # Insert sample subjects
            subjects = [
                ('Mathematics', 'MATH101', 'Basic mathematics'),
                ('Programming', 'CS102', 'Introduction to programming'),
                ('Networking', 'CS203', 'Computer networks'),
                ('Database', 'CS204', 'Relational databases'),
                ('Computer Applications', 'CA101', 'Introduction to computer applications')
            ]
            cursor.executemany("""
                INSERT IGNORE INTO subject (name, code, description) 
                VALUES (%s, %s, %s)
            """, subjects)
            app.db_connection.commit()
            
            # Insert sample classes
            classes = [('M1',), ('M2',), ('M3',), ('M4',), ('M5',), ('M6',), ('M7',),
                     ('L1',), ('L2',), ('L3',), ('L4',), ('L5',), ('L6',), ('L7',),
                     ('S1',), ('S2',)]
            cursor.executemany("INSERT IGNORE INTO class (name) VALUES (%s)", classes)
            app.db_connection.commit()
            
            # Insert sample academic years
            academic_years = [('2023-2024',), ('2024-2025',), ('2025-2026',)]
            cursor.executemany("INSERT IGNORE INTO academic_year (name) VALUES (%s)", academic_years)
            app.db_connection.commit()
            
            # Insert sample majors with department relationships
            cursor.execute("""
                INSERT IGNORE INTO major (name, department_id) 
                SELECT 'Software Engineering', id FROM department WHERE name = 'Computer Science'
                UNION ALL
                SELECT 'Artificial Intelligence', id FROM department WHERE name = 'Computer Science'
                UNION ALL
                SELECT 'Cybersecurity', id FROM department WHERE name = 'Computer Science'
                UNION ALL
                SELECT 'Business Analytics', id FROM department WHERE name = 'Business Administration'
            """)
            app.db_connection.commit()
            
            # Insert sample class schedules
            cursor.execute("""
                INSERT IGNORE INTO class_schedule (class_id, subject_id, day_of_week, start_time, end_time)
                SELECT 
                    (SELECT id FROM class WHERE name = 'M1' LIMIT 1),
                    (SELECT id FROM subject WHERE name = 'Programming' LIMIT 1),
                    'Monday', '09:00:00', '10:30:00'
                UNION ALL
                SELECT 
                    (SELECT id FROM class WHERE name = 'M2' LIMIT 1),
                    (SELECT id FROM subject WHERE name = 'Database' LIMIT 1),
                    'Tuesday', '10:00:00', '11:30:00'
                UNION ALL
                SELECT 
                    (SELECT id FROM class WHERE name = 'L3' LIMIT 1),
                    (SELECT id FROM subject WHERE name = 'Mathematics' LIMIT 1),
                    'Wednesday', '13:00:00', '14:00:00'
                UNION ALL
                SELECT 
                    (SELECT id FROM class WHERE name = 'S1' LIMIT 1),
                    (SELECT id FROM subject WHERE name = 'Networking' LIMIT 1),
                    'Thursday', '15:00:00', '16:30:00'
                UNION ALL
                SELECT 
                    (SELECT id FROM class WHERE name = 'M5' LIMIT 1),
                    (SELECT id FROM subject WHERE name = 'Computer Applications' LIMIT 1),
                    'Thursday', '07:00:00', '09:00:00'
            """)
            app.db_connection.commit()
            
            # Insert sample students
            cursor.execute("""
                INSERT IGNORE INTO mystudent (name, sex, score, email, phone, department_id, major_id, class_id, academic_year_id)
                SELECT 
                    'Alice Smith', 'Female', 85.5, 'alice.s@example.com', '123-456-7890',
                    (SELECT id FROM department WHERE name = 'Computer Science' LIMIT 1),
                    (SELECT id FROM major WHERE name = 'Software Engineering' LIMIT 1),
                    (SELECT id FROM class WHERE name = 'M1' LIMIT 1),
                    (SELECT id FROM academic_year WHERE name = '2024-2025' LIMIT 1)
                UNION ALL
                SELECT 
                    'Bob Johnson', 'Male', 72.0, 'bob.j@example.com', '098-765-4321',
                    (SELECT id FROM department WHERE name = 'Computer Science' LIMIT 1),
                    (SELECT id FROM major WHERE name = 'Artificial Intelligence' LIMIT 1),
                    (SELECT id FROM class WHERE name = 'M2' LIMIT 1),
                    (SELECT id FROM academic_year WHERE name = '2024-2025' LIMIT 1)
                UNION ALL
                SELECT 
                    'Charlie Brown', 'Male', 91.2, 'charlie.b@example.com', '111-222-3333',
                    (SELECT id FROM department WHERE name = 'Business Administration' LIMIT 1),
                    (SELECT id FROM major WHERE name = 'Business Analytics' LIMIT 1),
                    (SELECT id FROM class WHERE name = 'L3' LIMIT 1),
                    (SELECT id FROM academic_year WHERE name = '2023-2024' LIMIT 1)
            """)
            app.db_connection.commit()
            
    except mysql.connector.Error as e:
        print(f"Error inserting sample data: {e}")
        messagebox.showwarning("Sample Data", f"Could not insert sample data: {e}")
        app.db_connection.rollback()
    finally:
        cursor.close()

def update_database_schema(app):
    """
    Ensure all required database tables exist with the correct schema.
    
    This function checks for the existence of all required tables and creates them
    if they don't exist. It also sets up all necessary relationships between tables.
    
    Tables created:
    - department: Stores department information
    - subject: Stores subject/course information
    - major: Stores major information with department relationships
    - class: Stores class information
    - academic_year: Stores academic year information
    - mystudent: Main student records table
    - class_schedule: Manages class schedules
    - attendance: Tracks student attendance
    - absence: Tracks specific student absences (added based on SQL)
    
    Args:
        app: The application instance with database connection
        
    Returns:
        None
    """
    cursor = app.db_connection.cursor(buffered=True)
    tables = {
        "department": """
            CREATE TABLE IF NOT EXISTS department (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL UNIQUE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "subject": """
            CREATE TABLE IF NOT EXISTS subject (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL UNIQUE, 
                code VARCHAR(20), 
                description TEXT
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "major": """
            CREATE TABLE IF NOT EXISTS major (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL, 
                department_id INT NOT NULL, 
                UNIQUE KEY uq_major_name (name),
                CONSTRAINT fk_major_department 
                    FOREIGN KEY (department_id) 
                    REFERENCES department(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "class": """
            CREATE TABLE IF NOT EXISTS class (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL UNIQUE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "academic_year": """
            CREATE TABLE IF NOT EXISTS academic_year (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL UNIQUE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "mystudent": """
            CREATE TABLE IF NOT EXISTS mystudent (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(100), 
                sex VARCHAR(10),
                score FLOAT, 
                email VARCHAR(100), 
                phone VARCHAR(20),
                photo LONGBLOB, 
                department_id INT NULL, 
                major_id INT NULL,
                class_id INT NULL, 
                academic_year_id INT NULL,
                FOREIGN KEY (department_id) 
                    REFERENCES department(id) 
                    ON DELETE SET NULL 
                    ON UPDATE CASCADE,
                FOREIGN KEY (major_id) 
                    REFERENCES major(id) 
                    ON DELETE SET NULL 
                    ON UPDATE CASCADE,
                FOREIGN KEY (class_id) 
                    REFERENCES class(id) 
                    ON DELETE SET NULL 
                    ON UPDATE CASCADE,
                FOREIGN KEY (academic_year_id) 
                    REFERENCES academic_year(id) 
                    ON DELETE SET NULL 
                    ON UPDATE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "class_schedule": """
            CREATE TABLE IF NOT EXISTS class_schedule (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL, 
                subject_id INT NOT NULL,
                day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
                start_time TIME NOT NULL, 
                end_time TIME NOT NULL,
                FOREIGN KEY (class_id) 
                    REFERENCES class(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                FOREIGN KEY (subject_id) 
                    REFERENCES subject(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                UNIQUE KEY uq_schedule (class_id, day_of_week, start_time)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "attendance": """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL, 
                subject_id INT NOT NULL,
                attendance_date DATE NOT NULL,
                status ENUM('Absent', 'Present', 'Late', 'Excused') NOT NULL,
                notes TEXT,
                FOREIGN KEY (student_id) 
                    REFERENCES mystudent(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                FOREIGN KEY (subject_id) 
                    REFERENCES subject(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                UNIQUE KEY uq_attendance (student_id, subject_id, attendance_date)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;""",
            
        "absence": """
            CREATE TABLE IF NOT EXISTS absence (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                reason VARCHAR(255),
                FOREIGN KEY (student_id) 
                    REFERENCES mystudent(id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                UNIQUE KEY uq_absence (student_id, date)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"""
    }
    
    for table_name, query in tables.items():
        try:
            cursor.execute(query)
            app.db_connection.commit()  # Commit after each table creation
        except mysql.connector.Error as e:
            print(f"Error creating/updating table {table_name}: {e}")
            messagebox.showerror("Schema Error", f"Failed to create table '{table_name}':\n{e}")
            app.db_connection.rollback()  # Rollback on error
    
    # Insert sample data if tables are empty
    insert_sample_data(app)
    
    # Load all caches after schema update
    load_all_caches(app)
    cursor.close()

def execute_query(app, query, params=None, fetch=None, many=False):
    """
    Execute a SQL query with proper error handling and connection management.
    
    This is a generic function to execute any SQL query with parameters. It handles
    database connections, transactions, and error reporting automatically.
    
    Args:
        app: The StudentApp instance containing the database connection
        query (str): The SQL query to execute
        params (tuple/list/dict, optional): Parameters for the query
        fetch (str, optional): 
            - 'all': Fetch all results
            - 'one': Fetch a single result
            - None: For DML operations (INSERT, UPDATE, DELETE)
        many (bool, optional): If True, uses executemany() for batch operations
        
    Returns:
        - For SELECT with fetch='all': List of tuples containing all rows
        - For SELECT with fetch='one': A single row as a tuple
        - For INSERT: The lastrowid of the inserted record
        - For UPDATE/DELETE: The number of affected rows
        - None: If an error occurs
        
    Note:
        This function automatically handles database reconnection if needed and
        includes transaction management with proper commit/rollback.
    """
    if not app.db_connection or not app.db_connection.is_connected():
        connect_to_database(app) # Attempt to reconnect
        if not app.db_connection or not app.db_connection.is_connected(): 
            return None # If reconnection fails, exit

    try:
        with app.db_connection.cursor(buffered=True) as cursor:
            if many:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params or ())

            if fetch == 'all': return cursor.fetchall()
            elif fetch == 'one': return cursor.fetchone()
            else:
                app.db_connection.commit()
                # For INSERT, lastrowid; for UPDATE/DELETE, rowcount (though not directly returned for DML operations here)
                return cursor.lastrowid if query.strip().upper().startswith("INSERT") else cursor.rowcount
    except mysql.connector.Error as e:
        app.db_connection.rollback()
        messagebox.showerror("Database Query Error", f"Error: {e}\nQuery: {query}")
        return None

def load_all_caches(app):
    """
    Load all lookup data into the application's cache dictionaries.
    
    This function populates all cache dictionaries in the application instance
    by calling individual cache loading functions. It also updates the UI elements
    that depend on these caches.
    
    Caches loaded:
    - department_cache: {department_name: department_id}
    - major_cache: {major_name: {'id': major_id, 'dept_id': department_id}}
    - subject_cache: {subject_name: subject_id}
    - class_cache: {class_name: class_id}
    - academic_year_cache: {year_name: year_id}
    
    Args:
        app: The application instance where caches will be stored
        
    Returns:
        None
    """
    load_departments_to_cache(app)
    load_majors_to_cache(app)
    load_subjects_to_cache(app)
    load_class_names_to_cache(app)
    load_academic_years_to_cache(app)

    # These attribute accesses should come after the cache loading functions,
    # and should always use 'app.' to access properties of the app instance.
    # Also, it's good to check if the UI elements (comboboxes) exist before trying to update them.
    # Assuming these attributes exist on the 'app' object if the UI is initialized
    if hasattr(app, 'department_combo'):
        app.department_combo['values'] = list(app.department_cache.keys())
    if hasattr(app, 'class_combo'):
        app.class_combo['values'] = list(app.class_cache.keys())
    if hasattr(app, 'academic_year_entry'): # This is likely a ttk.Combobox, though named _entry
        app.academic_year_entry['values'] = list(app.academic_year_cache.keys())


def load_departments_to_cache(app):
    """
    Load department data from the database into the department cache.
    
    This function populates the department_cache dictionary in the application
    instance with data from the department table. The cache is used to avoid
    repeated database queries for department lookups.
    
    Cache format:
        {department_name: department_id, ...}
    
    Args:
        app: The application instance where the cache will be stored
        
    Returns:
        None
    """
    rows = execute_query(app, "SELECT name, id FROM department ORDER BY name", fetch='all')
    app.department_cache = dict(rows) if rows else {}

def load_majors_to_cache(app):
    """
    Load major data from the database into the major cache.
    
    This function populates the major_cache dictionary in the application
    instance with data from the major table. The cache includes both major
    information and its associated department ID.
    
    Cache format:
        {
            major_name: {
                'id': major_id,
                'dept_id': department_id
            },
            ...
        }
    
    Args:
        app: The application instance where the cache will be stored
        
    Returns:
        None
    """
    # No need to clear() explicitly as we are reassigning the dictionary
    rows = execute_query(app, "SELECT id, name, department_id FROM major ORDER BY name", fetch='all')
    if rows: 
        app.major_cache = {name: {'id': m_id, 'dept_id': d_id} for m_id, name, d_id in rows}
    else:
        app.major_cache = {}

def load_subjects_to_cache(app):
    """
    Load subject data from the database into the subject cache.
    
    This function populates the subject_cache dictionary in the application
    instance with data from the subject table.
    
    Cache format:
        {subject_name: subject_id, ...}
    
    Args:
        app: The application instance where the cache will be stored
        
    Returns:
        None
    """
    # No need to clear() explicitly as we are reassigning the dictionary
    rows = execute_query(app, "SELECT id, name FROM subject ORDER BY name", fetch='all')
    if rows: 
        app.subject_cache = {name: s_id for s_id, name in rows}
    else: 
        app.subject_cache = {}

def load_class_names_to_cache(app):
    """
    Load class data from the database into the class cache.
    
    This function populates the class_cache dictionary in the application
    instance with data from the class table.
    
    Cache format:
        {class_name: class_id, ...}
    
    Args:
        app: The application instance where the cache will be stored
        
    Returns:
        None
    """
    rows = execute_query(app, "SELECT name, id FROM class ORDER BY name", fetch='all')
    app.class_cache = dict(rows) if rows else {}

def load_academic_years_to_cache(app):
    """
    Load academic year data from the database into the academic year cache.
    
    This function populates the academic_year_cache dictionary in the application
    instance with data from the academic_year table. Years are ordered in
    descending order (newest first).
    
    Cache format:
        {academic_year_name: academic_year_id, ...}
    
    Args:
        app: The application instance where the cache will be stored
        
    Returns:
        None
    """
    rows = execute_query(app, "SELECT name, id FROM academic_year ORDER BY name DESC", fetch='all')
    app.academic_year_cache = dict(rows) if rows else {}