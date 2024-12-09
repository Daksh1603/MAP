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

import win32gui
import win32con
import ctypes
import subprocess

import requests

import Settings

click_coord = {
    "keep": (1057, 634),
    "attack_1": (785,1018),
    "attack_2": (885,1018),
    "attack_3": (1000,1018),
    "attack_4": (1200,1018),
    "close": (995,791),
    "skip": (943,617),
    "capture": (952,141),
    "capture2prompt": (1010,617),
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
    "evolSkip2": (966, 757),
    "caughCritSkip": (940,747),
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
train_appears = (432,64,60,24) # Need to adjust this through Recording.py

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

def click_on(app_window, coord, window_name = 'Miscrits (DEBUG)'):
    ################## ACTIVE CLICK ############################
    x,y = coord

    window_left = app_window['left']
    window_top = app_window['top']

    # Calculate the absolute screen coordinates
    screen_x = window_left + x
    screen_y = window_top + y

    # Move the mouse to the calculated position and click
    pyautogui.moveTo(screen_x, screen_y)
    pyautogui.click()


def background_click_scaled(coord: tuple, window_name: str = "Miscrits (DEBUG)"):
    # Original Window Size (Maximized)
    original_width = 1936
    original_height = 1096

    # Find the window handle by its name
    hwnd = win32gui.FindWindow(None, window_name)
    if not hwnd:
        raise Exception(f"Window '{window_name}' not found.")
    print('HWND : ',hwnd)
    # Get the current window's position and size using GetWindowRect
    rect = win32gui.GetWindowRect(hwnd)
    win_left, win_top, win_right, win_bottom = rect
    print('Client window Rect : ',win_left, win_top, win_right, win_bottom)

    # Get current window size (width and height)
    current_width = win_right - win_left
    current_height = win_bottom - win_top

    print('Current Width and Height : ',current_width,current_height)

    # Ensure the current size is different from the original size (to scale)
    original_x, original_y = coord
    scale_x = current_width / original_width
    scale_y = current_height / original_height

    # Scale the coordinates
    client_x = int(original_x * scale_x)
    client_y = int(original_y * scale_y)

    print('Click x and y scaled : ',client_x,client_y)

    # Convert to client area coordinates
    client_x = client_x # + win_left
    client_y = client_y + win_top
    print('Final click x and y :',client_x,client_y)

    # Define constants for sending input messages
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202

    # Pack coordinates into LPARAM
    lparam = (client_y << 16) | (client_x & 0xFFFF)

    #ctypes.windll.user32.SetCursorPos(client_x, client_y)
    #time.sleep(10)
    # Simulate the click in the background
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 0, lparam)
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)


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
    print(f"Capturing application window: {app_window}")
    while True:
        # Check if Resume
        resume_live_feed_event.wait()

        screenshot = sct.grab(app_window)

        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR

        #cv2.imshow("Capture Appears", frame[capture_appears[1]:capture_appears[1] + capture_appears[3],capture_appears[0]:capture_appears[0] + capture_appears[2]])

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
        if 'capture' in capture.lower() or 'ture' in capture.lower():
            print("Battle search complete!")
            battle_found_event.set()
            click_on(app_window,click_coord['skip_listener'])
            break

def train_check(app_window,M1R=None,M2R=None,M3R=None,M4R=None):
    print('Train Check Begins ########################################')
    click_on(app_window,click_coord['train'])
    print('Train Menu Opens')
    time.sleep(2)

    m1t_appears = (733,338,100,14)
    m2t_appears = (732,388,100,14)
    m3t_appears = (732,438,100,14)
    m4t_appears = (732,488,100,14)
    
    tempSct = mss()
    tempScreenshot = tempSct.grab(app_window)
    frame = np.array(tempScreenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # M1T = tempFrame[m1t_appears[1]:m1t_appears[1] + m1t_appears[3],m1t_appears[0]:m1t_appears[0] + m1t_appears[2]]
    if M1R is not None:
        M1T,M2T,M3T,M4T = M1R,M2R,M3R,M4R
    else:
        M1T = extract_text_region_name(frame,*m1t_appears)
        M2T = extract_text_region_name(frame,*m2t_appears)
        M3T = extract_text_region_name(frame,*m3t_appears)
        M4T = extract_text_region_name(frame,*m4t_appears)

    timeDelay = Settings.TRAIN_TIME_DELAY

    if 'ready' in M1T.lower():
        level_up_miscrit(1,frame,app_window,timeDelay)

    if 'ready' in M2T.lower():
        level_up_miscrit(2,frame,app_window,timeDelay)

    if 'ready' in M3T.lower():
        level_up_miscrit(3,frame,app_window,timeDelay)

    if 'ready' in M4T.lower():
        level_up_miscrit(4,frame,app_window,timeDelay)
    
    click_on(app_window,click_coord['closeTrainMenu'])
    print('Train Check Ends ########################################')
    time.sleep(2)

def level_up_miscrit(miscrit_number, frame, app_window, timeDelay):
    """Helper function to handle the leveling up process for a miscrit."""
    miscrit_key = str(miscrit_number)
    level = extract_text_region_name(frame,*regions[f"Miscrit{miscrit_key}Level"])

    send_discord_webhook(f"Miscrit {miscrit_key} Leveled Up: {level}") # <@{Settings.DISCORD_USER_ID}> 
    
    # Perform the click actions for training
    click_on(app_window, click_coord[f'miscrit{miscrit_key}Train'])
    time.sleep(timeDelay)
    click_on(app_window, click_coord['trainMiscrit'])
    time.sleep(timeDelay)
    click_on(app_window, click_coord['closeTrainMiscrit'])
    time.sleep(timeDelay)
    click_on(app_window, click_coord['closeNewMoveMiscrit'])
    time.sleep(timeDelay)
    click_on(app_window, click_coord['evolSkip1'])
    time.sleep(timeDelay)
    click_on(app_window, click_coord['evolSkip2'])
    time.sleep(timeDelay)

def logout(app_window):
    click_on(app_window,click_coord['menu'])
    time.sleep(1)
    click_on(app_window,click_coord['logout'])
    time.sleep(3)
    click_on(app_window,click_coord['login'])
    time.sleep(7)