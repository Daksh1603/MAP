import cv2
import numpy as np
from mss import mss
import pygetwindow as gw
import pyautogui  # For mouse position
import time
import pytesseract
from collections import Counter

def recordRegime(self,app_window):
    print("Variable access thread started...")
    while True:
        process_data = read_from_file()
        frame_count = process_data.get("frame_count", 0)
        timestamp = process_data.get("timestamp", "")
        avg_color = process_data.get("avg_color", (0, 0, 0))

        # Simulate processing or logging
        print(f"Processed Frame {frame_count}: Timestamp = {timestamp}, Avg Color = {avg_color}")

        # Simulate some delay in processing
        time.sleep(1)

        # Exit condition (optional)
        if frame_count >= 100:  # Exit after processing 100 frames
            print("Stopping variable access thread...")
            break
        
