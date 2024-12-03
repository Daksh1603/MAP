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
    "evolSkip1": (951, 793),
    "evolSkip2": (966, 752),
}

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