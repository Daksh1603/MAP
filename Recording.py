import cv2
import numpy as np
from mss import mss
import pygetwindow as gw
import pyautogui  # For mouse position
import time
import pytesseract
from collections import Counter

def get_application_window(app_name):
    """Get the application window's position and size by name."""
    windows = gw.getWindowsWithTitle(app_name)
    if not windows:
        print(f"Application '{app_name}' not found.")
        return None
    window = windows[0]  # Select the first matching window
    return {
        "top": window.top,
        "left": window.left,
        "width": window.width,
        "height": window.height
    }

# Define a function to create a mask for the rocks
def mask_rocks(frame):
    # Convert the frame to HSV (Hue, Saturation, Value) color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the color range for rocks (adjust these values based on your image)
    lower_gray = np.array([0, 0, 100])  # Lower bound of gray color in HSV
    upper_gray = np.array([180, 50, 200])  # Upper bound of gray color in HSV

    # Create a binary mask where gray colors are white, and everything else is black
    mask = cv2.inRange(hsv, lower_gray, upper_gray)

    # Optionally, clean up the mask using morphological operations
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Close small gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Remove noise

    # Apply the mask to the original frame
    result = cv2.bitwise_and(frame, frame, mask=mask)
    return result


def find_max_occurrence_with_condition(texts):
    print(texts)
    occurrences = Counter()
    for text in texts:
        occurrences[text] += 1  # Increment count if valid

    # Sort by frequency in descending order
    sorted_occurrences = sorted(occurrences.items(), key=lambda x: x[1], reverse=True)
    for text, count in sorted_occurrences:
        return text

def extract_text_region_health(frame, x, y, w, h):
    region = frame[y:y+h, x:x+w]

    scale_factor = 2  # 200% scaling for better performance and clarity
    resized = cv2.resize(region, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Step 3: Threshold to make text more distinct
    _, preprocessed = cv2.threshold(contrast_enhanced, 150, 255, cv2.THRESH_BINARY)

    # Step 4: Apply sharpening (optional)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])  # Sharpening kernel
    sharpened = cv2.filter2D(preprocessed, -1, sharpen_kernel)

    # Step 6: Use Tesseract OCR to extract text
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Path to Tesseract
    custom_config = r'--oem 3 --psm 8 tessedit_char_whitelist=1234567890'
    text = pytesseract.image_to_string(preprocessed, config=custom_config).strip()

    return text


def get_rock_coordinates_centered(mask, percent=80):
    """Find the coordinates of rocks in the masked frame."""
    # Find contours in the mask
    cropped_mask, offset_x, offset_y = crop_to_center(mask, percent)
    # Get the contours from the cropped mask
    contours, _ = cv2.findContours(cropped_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    coordinates = []
    for contour in contours:
        # Get the bounding box and calculate the centroid
        x, y, w, h = cv2.boundingRect(contour)
        centroid_x = x + w // 2
        centroid_y = y + h // 2

        # Add the offset to get coordinates relative to the original frame
        coordinates.append((centroid_x + offset_x, centroid_y + offset_y))
    return coordinates

def click_on_rocks(app_name, coordinates, app_window):
    """Click on the detected rock coordinates."""
    for coord in coordinates:
        # Convert relative coordinates to screen coordinates
        screen_x = app_window["left"] + coord[0]
        screen_y = app_window["top"] + coord[1]
        pyautogui.moveTo(screen_x, screen_y)
        pyautogui.click()
        print(f"Clicked at ({screen_x}, {screen_y}) on '{app_name}'.")

        time.sleep(10)

def draw_mouse_cursor(frame, app_window):
    """Draw the mouse cursor on the frame if it is within the application window."""
    # Get the current mouse position
    mouse_x, mouse_y = pyautogui.position()
    
    # Check if the mouse is within the application window
    if (app_window["left"] <= mouse_x <= app_window["left"] + app_window["width"] and
        app_window["top"] <= mouse_y <= app_window["top"] + app_window["height"]):
        
        # Calculate the position of the mouse relative to the application window
        cursor_x = mouse_x - app_window["left"]
        cursor_y = mouse_y - app_window["top"]
        
        # Draw a small circle at the mouse position
        cv2.circle(frame, (cursor_x, cursor_y), 10, (0, 0, 255), -1)  # Red circle
    
    return frame

def click_in_application(app_name, x, y):
    """
    Clicks on the specified (x, y) position inside the given application's window.

    Parameters:
    - app_name (str): The title of the application window.
    - x (int): The x-coordinate relative to the application's window.
    - y (int): The y-coordinate relative to the application's window.
    """
    # Get the application's window position and size
    windows = gw.getWindowsWithTitle(app_name)
    if not windows:
        print(f"Application '{app_name}' not found.")
        return
    window = windows[0]  # Use the first matching window

    # Get the window's position on the screen
    window_left = window.left
    window_top = window.top

    # Calculate the absolute screen coordinates
    screen_x = window_left + x
    screen_y = window_top + y

    # Move the mouse to the calculated position and click
    pyautogui.moveTo(screen_x, screen_y)
    pyautogui.click()
    print(f"Clicked at ({screen_x}, {screen_y}) on '{app_name}'.")

def crop_to_center(mask, percent=80):
    if len(mask.shape) == 3:  # Convert to grayscale if it's a 3-channel image
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    height, width = mask.shape
    crop_width = int(width * (percent / 100))
    crop_height = int(height * (percent / 100))

    offset_x = (width - crop_width) // 2
    offset_y = (height - crop_height) // 2

    cropped_mask = mask[offset_y:offset_y + crop_height, offset_x:offset_x + crop_width]
    return cropped_mask, offset_x, offset_y

def get_mouse_location_relative(app_window):
    """
    Get the current mouse position relative to the application's window.
    
    Parameters:
        app_window (dict): The application's window position and size.
        
    Returns:
        tuple: (x, y) position of the mouse relative to the application's window.
               Returns None if the mouse is outside the application's window.
    """
    # Get the current mouse position on the screen
    mouse_x, mouse_y = pyautogui.position()

    # Check if the mouse is within the application window
    if (app_window["left"] <= mouse_x <= app_window["left"] + app_window["width"] and
        app_window["top"] <= mouse_y <= app_window["top"] + app_window["height"]):
        
        # Calculate the position of the mouse relative to the application window
        relative_x = mouse_x - app_window["left"]
        relative_y = mouse_y - app_window["top"]
        
        return relative_x, relative_y
    
    # If the mouse is outside the window, return None
    return None

def extract_text_region_name(frame, x, y, w, h):
    """
    Extract text from a specified region of the frame.

    Parameters:
        frame (ndarray): The screenshot of the game.
        x, y, w, h (int): Coordinates and dimensions of the region.

    Returns:
        str: Extracted text.
    """
    region = frame[y:y+h, x:x+w]

    scale_factor = 2  # 200% scaling for better performance and clarity
    resized = cv2.resize(region, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Step 3: Threshold to make text more distinct
    _, preprocessed = cv2.threshold(contrast_enhanced, 150, 255, cv2.THRESH_BINARY)

    # Step 4: Apply sharpening (optional)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])  # Sharpening kernel
    sharpened = cv2.filter2D(preprocessed, -1, sharpen_kernel)

    # Step 6: Use Tesseract OCR to extract text
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Path to Tesseract
    custom_config = r'--oem 3 --psm 8 tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    text = pytesseract.image_to_string(preprocessed, config=custom_config).strip()

    return text

def main():
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Set the name of the application window
    app_name = "Miscrits"  # Replace with the exact title of your application window

    left_pokemon_name_region = (720, 72, 80, 20)  # x, y, w, h (adjust based on your game UI)
    right_pokemon_name_region = (1180, 72, 80, 15)
    capture_appears = (928,132,90,18)
    skip_appears = (914,609,70,18)
    keep_appears = (1028,621,70,20)
    train_appears = (432,64,60,24)

    m1t_appears = (733,338,100,14)
    m2t_appears = (732,388,100,14)
    m3t_appears = (732,438,100,14)
    m4t_appears = (732,488,100,14)

    CaptureRate = (951,150,20,20)
    
    # Get the application's window position and size
    app_window = get_application_window(app_name)
    if not app_window:
        return
    
    # Initialize MSS for screen capturing
    sct = mss()

    print(f"Capturing application window: {app_window}")
    
    # Capture the application window in a loop
    while True:
        # Grab the screen based on the application's window
        screenshot = sct.grab(app_window)
        
        # Convert the screenshot to a NumPy array (BGR format for OpenCV)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR
        
        # Draw the mouse cursor on the frame
        #frame = draw_mouse_cursor(frame, app_window)
        masked_frame = mask_rocks(frame)
        
        # Show the frame in a window
        coordinates = get_rock_coordinates_centered(masked_frame, percent=80)

        # Draw the detected points on the frame
        #for coord in coordinates:
        #    cv2.circle(frame, coord, 10, (0, 0, 255), -1)

        # Display the frame with detected rocks
        #cv2.imshow("Rock Detection", frame)
        #frame = replace_color_with_black(frame, 'B4C8E1')
    
        # Left Pokémon Name Region
        left_name_image = frame[left_pokemon_name_region[1]:left_pokemon_name_region[1] + left_pokemon_name_region[3],
                                left_pokemon_name_region[0]:left_pokemon_name_region[0] + left_pokemon_name_region[2]]

        # Right Pokémon Name Region
        right_name_image = frame[right_pokemon_name_region[1]:right_pokemon_name_region[1] + right_pokemon_name_region[3],
                                right_pokemon_name_region[0]:right_pokemon_name_region[0] + right_pokemon_name_region[2]]
        
        capture_image = frame[capture_appears[1]:capture_appears[1] + capture_appears[3],capture_appears[0]:capture_appears[0] + capture_appears[2]]

        skip_image = frame[skip_appears[1]:skip_appears[1] + skip_appears[3],skip_appears[0]:skip_appears[0] + skip_appears[2]]

        keep_image = frame[keep_appears[1]:keep_appears[1] + keep_appears[3],keep_appears[0]:keep_appears[0] + keep_appears[2]]

        cr_image = frame[CaptureRate[1]:CaptureRate[1] + CaptureRate[3],CaptureRate[0]:CaptureRate[0] + CaptureRate[2]]

        ta_image = frame[train_appears[1]:train_appears[1] + train_appears[3],train_appears[0]:train_appears[0] + train_appears[2]]
        
    
        m1ta_image = frame[m1t_appears[1]:m1t_appears[1] + m1t_appears[3],m1t_appears[0]:m1t_appears[0] + m1t_appears[2]]
        m2ta_image = frame[m2t_appears[1]:m2t_appears[1] + m2t_appears[3],m2t_appears[0]:m2t_appears[0] + m2t_appears[2]]
        m3ta_image = frame[m3t_appears[1]:m3t_appears[1] + m3t_appears[3],m3t_appears[0]:m3t_appears[0] + m3t_appears[2]]
        m4ta_image = frame[m4t_appears[1]:m4t_appears[1] + m4t_appears[3],m4t_appears[0]:m4t_appears[0] + m4t_appears[2]]
        #cv2.imwrite("preprocessed_image.png", left_health_image)

        # Display the cropped health images
        # cv2.imshow("Left Pokémon Health", left_health_image)
        # cv2.imshow("Right Pokémon Health", right_health_image)
        #cv2.imshow("Left Pokémon Name", left_name_image)
        #cv2.imshow("Right Pokémon Name", right_name_image)
        #cv2.imshow("Capture Appears", capture_image)
        #cv2.imshow("Capture Rate", cr_image)
        #cv2.imshow("Train Appears", ta_image)
        #cv2.imshow("M3T Appears", m3ta_image)
        cv2.imshow("M4T Appears", m4ta_image)

        # left_pokemon_name = extract_text_region_name(frame, *left_pokemon_name_region)
        # right_pokemon_name = extract_text_region_name(frame, *right_pokemon_name_region)
        # capture = extract_text_region_name(frame, *capture_appears)
        # skip = extract_text_region_name(frame, *skip_appears)
        # keep = extract_text_region_name(frame, *keep_appears)
        # capRate = extract_text_region_health(frame,*CaptureRate)
        train = extract_text_region_name(frame,*train_appears)
        M3T = extract_text_region_name(frame,*m3t_appears) # READY,TO,TRAIN a
        M4T = extract_text_region_name(frame,*m4t_appears) # READY,TO,TRAIN a


        # print(f"Left Pokémon: {left_pokemon_name}" + f"Right Pokémon: {right_pokemon_name} ")
        # print(f"Capture Present: {capture} Capture Rate : {capRate}\n\n\n\n")
        # print(f"Skip Present: {skip} Keep present : {keep}\n\n\n\n")
        print(f"Train : {train}  M3T : {M3T}  M4T : {M4T}")
              
        # Perform clicks on detected rocks
        # if coordinates:
        #     click_on_rocks(app_name, coordinates, app_window)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
