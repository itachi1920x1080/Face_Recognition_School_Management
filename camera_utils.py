"""
Camera and Image Utilities Module

This module provides functionality for camera handling and image processing
in the Student Management System. It includes features for capturing photos
from a webcam, uploading images from disk, and displaying images in the UI.

Key Features:
- Webcam capture and preview
- Image upload and display
- Image format conversion
- Camera resource management

Dependencies:
- opencv-python (cv2): For camera capture and image processing
- Pillow (PIL): For image manipulation and display
- tkinter: For GUI components and file dialogs
"""

import cv2
from PIL import Image, ImageTk
import io
import tkinter as tk
from tkinter import messagebox

def update_camera_feed(app):
    """
    Update the camera preview on the main form.
    
    This function is called repeatedly to refresh the camera preview.
    It captures frames from the camera, converts them to a format suitable
    for display, and updates the UI. The function schedules itself to run
    at a reasonable interval to balance smoothness and CPU usage.
    
    Args:
        app: The application instance containing UI elements and camera state
        
    Returns:
        None
        
    Note:
        - Runs at approximately 20 FPS to reduce CPU load
        - Automatically stops when camera_running is set to False
    """
    if app.camera_running:
        ret, frame = app.video_capture.read()
        if ret:
            app.current_frame = frame
            img_rgb = app.cv2.cvtColor(frame, app.cv2.COLOR_BGR2RGB)
            img = app.Image.fromarray(img_rgb)
            
            # Use the label's actual size for resizing
            w, h = app.photo_display_label.winfo_width(), app.photo_display_label.winfo_height()
            if w > 1 and h > 1:
                img.thumbnail((w - 10, h - 10), app.Image.Resampling.LANCZOS)
            
            photo_image = app.ImageTk.PhotoImage(image=img)
            app.photo_display_label.config(image=photo_image, text="")
            app.photo_display_label.image = photo_image
        
        # Increased the delay from 15ms to 50ms (~20 FPS)
        # This significantly reduces CPU usage for the simple preview.
        app.window.after(50, app.update_camera_feed)

def toggle_camera(app):
    """
    Toggle the camera feed on or off.
    
    This function starts or stops the camera feed based on the current state.
    It handles camera initialization, resource management, and UI updates.
    
    Args:
        app: The application instance containing camera state and UI elements
        
    Returns:
        None
        
    Side Effects:
        - Initializes or releases camera resources
        - Updates UI buttons and camera state
        - May show error messages if camera cannot be accessed
    """
    if not app.camera_running:
        app.video_capture = app.cv2.VideoCapture(0)
        if not app.video_capture.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera.")
            return
        app.camera_running = True
        app.btn_toggle_cam.config(text="Stop Camera")
        app.btn_capture.config(state=app.tk.NORMAL)
        update_camera_feed(app)
    else:
        app.camera_running = False
        app.btn_toggle_cam.config(text="Start Camera")
        app.btn_capture.config(state=app.tk.DISABLED)
        if app.video_capture: app.video_capture.release()
        if app.captured_image_data is None: clear_photo_display(app)

def capture_photo(app):
    """
    Capture a photo from the current camera frame.
    
    This function captures the current frame from the camera, converts it
    to RGB format, and stores it in the application's state. It also stops
    the camera after capturing to save resources.
    
    Args:
        app: The application instance containing the camera and image data
        
    Returns:
        None
        
    Side Effects:
        - Updates app.captured_image_data with the captured image
        - Calls toggle_camera() to stop the camera
        - Updates the UI to show the captured image
    """
    if app.current_frame is not None:
        img_rgb = app.cv2.cvtColor(app.current_frame, app.cv2.COLOR_BGR2RGB)
        img = app.Image.fromarray(img_rgb)
        with app.io.BytesIO() as buf:
            img.save(buf, format="PNG")
            app.captured_image_data = buf.getvalue()
        display_image(app, app.captured_image_data)
        toggle_camera(app) # Stop camera after capturing
    else:
        messagebox.showwarning("Capture Error", "No camera frame available.")

def upload_photo(app):
    """
    Open a file dialog to upload a photo from disk.
    
    This function displays a file dialog for the user to select an image file.
    The selected image is loaded into memory and displayed in the UI.
    
    Args:
        app: The application instance for UI and image storage
        
    Returns:
        None
        
    Supported Formats:
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - Bitmap (.bmp)
        
    Note:
        Shows error messages if the file cannot be read or is in an unsupported format.
    """
    file_path = app.filedialog.askopenfilename(title="Select a Photo", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
    if file_path:
        try:
            with open(file_path, 'rb') as f: app.captured_image_data = f.read()
            display_image(app, app.captured_image_data)
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read file:\n{e}")

def display_image(app, image_data):
    """
    Display an image in the photo display area.
    
    This function takes binary image data, converts it to a format suitable
    for display in Tkinter, and updates the photo display label.
    
    Args:
        app: The application instance containing the display label
        image_data (bytes): Binary image data to display
        
    Returns:
        None
        
    Note:
        - Automatically scales the image to fit the display area
        - Preserves the aspect ratio of the original image
        - Silently handles display errors to prevent application crashes
    """
    try:
        img = app.Image.open(app.io.BytesIO(image_data))
        w, h = app.photo_display_label.winfo_width(), app.photo_display_label.winfo_height()
        if w > 1 and h > 1: img.thumbnail((w - 10, h - 10), app.Image.Resampling.LANCZOS)
        photo_image = app.ImageTk.PhotoImage(image=img)
        app.photo_display_label.config(image=photo_image, text=""); app.photo_display_label.image = photo_image
    except Exception as e:
        clear_photo_display(app)
        print(f"Error displaying image: {e}")

def clear_photo_display(app):
    """
    Clear the photo display and reset the image state.
    
    This function removes the currently displayed image, shows a placeholder text,
    and clears any stored image data from the application state.
    
    Args:
        app: The application instance containing the display and image data
        
    Returns:
        None
        
    Side Effects:
        - Updates the photo display label to show "No Photo"
        - Clears the stored image data (app.captured_image_data)
        - Removes any references to the displayed image to free memory
    """
    app.photo_display_label.config(image='', text="No Photo")
    app.photo_display_label.image = None
    app.captured_image_data = None