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
import sys
import os
import requests
from collections import deque


from BattleStage.BattleLogic import battle
from BattleStage.WildHunt import playWildHunt
from BattleStage.DoubleBattle import playDoubleBattle
from PlayRegime.PlayRegime import playRegime
from RecordRegime.RecordRegime import recordRegime
import Settings
import base



def main():
    print('App begins')
    app_name = Settings.APPLICATION_NAME  # Replace with the exact title of your application window
    app_window = base.get_application_window(app_name)
    
    shared_data = deque(maxlen=1)

    resume_live_feed_event = threading.Event()
    resume_live_feed_event.set()

    screen_thread = threading.Thread(target=base.recording_feed,args=(app_window,shared_data,resume_live_feed_event,))
    process_thread = threading.Thread(target=recordRegime,args=(app_window,shared_data,resume_live_feed_event,)) # recordRegime playRegime playWildHunt playDoubleBattle

    # Start threads
    screen_thread.start()
    while not shared_data:
        pass
    process_thread.start()

    # Wait for threads to finish
    screen_thread.join()
    process_thread.join()

    print("Program Finished.")

if __name__ == "__main__":
    main()