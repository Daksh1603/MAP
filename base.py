import tkinter as tk
from tkinter import messagebox
import time
from threading import Thread
import cv2
import numpy as np
from mss import mss
import pygetwindow as gw
import pyautogui  # For mouse position
import time
import pytesseract
from collections import Counter
import json
import threading
from pynput import mouse
import discord
import asyncio
import threading
import time

import requests

click_coord = {
    "keep": (1057, 634),
    "attack_1": (785,1018),
    "attack_2": (885,1018),
    "attack_3": (1000,1018),
    "attack_4": (1200,1018),
    "close": (995,791),
    "skip": (943,617),
    "capture": (952,141),
    "skip_listener": (900,200),
    "train": (432,64),
    "trainMiscrit": (1015, 291),
    "miscrit1Train": (732,334),
    "miscrit2Train": (732,388),
    "miscrit3Train": (732,434),
    "miscrit4Train": (732,480),
    "logout": (1852, 1029),
    "login": (883, 695),
    "heal": (1700, 81),
    "closeTrainMiscrit": (1093, 859),
    "menu":(1852, 1061),
    "closeNewMoveMiscrit": (1000, 657),
    "closeTrainMenu": (1313, 267),
    "attackRightTab" : (1342, 1025),
    "attackLeftTab" : (596, 1023),
    "evolSkip1": (951, 793),
    "evolSkip2": (966, 752),
}

regions = {
    "Miscrit1Level":(677,339,14,16),
    "Miscrit2Level":(677, 389,14,16),
    "Miscrit3Level":(677,439,14,16),
    "Miscrit4Level":(677, 489,14,16),
}

left_pokemon_name_region = (720, 72, 80, 20)  # x, y, w, h (adjust based on your game UI)
right_pokemon_name_region = (1180, 72, 80, 15)
capture_appears = (928,132,90,18)
skip_appears = (914,609,70,18)
keep_appears = (1028,621,70,20)
CaptureRate = (951,150,20,20)

WEBHOOK_URL = "https://discord.com/api/webhooks/1313072656311910431/bA2WxdlWoZnQnkSyqEhK6e6PVU17GF_GuGbjL32fiI6JknEL_cJEe190FU4jV5X7bSTx"

def send_discord_webhook(message):
    """
    Sends a message to the Discord channel via webhook.
    """
    data = {"content": message}  # Message payload
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(WEBHOOK_URL, json=data, headers=headers)
        if response.status_code == 204:
            pass
        else:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

def click_on(app_window, coord):
    x = coord[0]
    y = coord[1]

    window_left = app_window['left']
    window_top = app_window['top']

    # Calculate the absolute screen coordinates
    screen_x = window_left + x
    screen_y = window_top + y

    # Move the mouse to the calculated position and click
    pyautogui.moveTo(screen_x, screen_y)
    pyautogui.click()

def extract_text_region_name(frame, x, y, w, h):
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

def recording_feed(app_window,shared_data,resume_live_feed_event):
    sct = mss()

    while True:
        # Check if Resume
        resume_live_feed_event.wait()

        screenshot = sct.grab(app_window)

        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR

        cv2.imshow("Capture Appears", frame[capture_appears[1]:capture_appears[1] + capture_appears[3],capture_appears[0]:capture_appears[0] + capture_appears[2]])

        capture = extract_text_region_name(frame, *capture_appears)
        shared_data.append(capture)
        #print(shared_data[0])

def search_for_application(app_name):
    while True:
        app_window = get_application_window(app_name)
        if app_window is not None:
            return app_window
        
def get_application_window(app_name):
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

def searching_for_battle(app_window,shared_data,battle_found_event,wait_event=threading.Event()):
    while not wait_event.is_set():
        capture = shared_data[0]
        #time.sleep(waiting_time)
        if 'capture'.lower() in capture.lower():
            print("Battle search complete!")
            battle_found_event.set()
            click_on(app_window,click_coord['skip_listener'])
            break