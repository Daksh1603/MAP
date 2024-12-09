from BattleStage.BattleLogic import battle
from PlayRegime.PlayRegime import playRegime
from RecordRegime.RecordRegime import recordRegime
import Settings
import base

import time
import pyautogui
from PIL import Image, ImageDraw, ImageGrab
import win32gui
import win32con
import ctypes
from ctypes import wintypes

def background_click_scaled(coord: tuple, window_name: str = "Miscrits (DEBUG)"):
    """
    Simulates a background click on a maximized application window, scaling coordinates based on the window's current size.

    Args:
        coord (tuple): A tuple containing the absolute (x, y) coordinates recorded for the original window size (1936x1096).
        window_name (str): The name of the target window (default is "Miiscrits (DEBUG)").
    """
    # Original Window Size (Maximized)
    original_width = 1936
    original_height = 1096

    # Find the window handle by its name
    hwnd = win32gui.FindWindow(None, window_name)
    if not hwnd:
        raise Exception(f"Window '{window_name}' not found.")

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
    client_x = client_x + win_left
    client_y = client_y + win_top
    print('Final click x and y :',client_x,client_y)

    # Define constants for sending input messages
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202

    # Pack coordinates into LPARAM
    lparam = (client_y << 16) | (client_x & 0xFFFF)

    # ctypes.windll.user32.SetCursorPos(client_x, client_y)
    # time.sleep(10)
    
    # Simulate the click in the background
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 0, lparam)
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)



# Example usage:
if __name__ == "__main__":
    #background_click_scaled(base.click_coord['closeTrainMenu'])
    background_click_scaled((1181,606))
    print("Click performed successfully.")