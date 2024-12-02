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

no_battle_counter = 0
# Replace with your Discord webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1313072656311910431/bA2WxdlWoZnQnkSyqEhK6e6PVU17GF_GuGbjL32fiI6JknEL_cJEe190FU4jV5X7bSTx"

miscrit_levels = {"1":32,"2":18,"3":17,"4":18}

def send_discord_webhook(message):
    """
    Sends a message to the Discord channel via webhook.
    """
    data = {"content": message}  # Message payload
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(WEBHOOK_URL, json=data, headers=headers)
        if response.status_code == 204:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

# def fight_miscrit(app_window):
#     while True:
#         screenshot = take_screenshot
#         send_message_screent(message='rare miscrit',screenshot=screenshot)
#         userInput = add3buttons([{'attack_1':'red','attack_2':'red','capture':'yellow'}],waitTime=10)
        
#         # additional code


battle_found_event = threading.Event()
feed_stopped = threading.Event()

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

def get_mouse_location_relative_on_click(app_window):
    result = {"relative_position": None}

    def on_click(x, y, button, pressed):
        if pressed:  # Check if the mouse button is pressed
            # Check if the click is within the application window
            if (app_window["left"] <= x <= app_window["left"] + app_window["width"] and
                app_window["top"] <= y <= app_window["top"] + app_window["height"]):
                
                # Calculate the position of the mouse relative to the application window
                relative_x = x - app_window["left"]
                relative_y = y - app_window["top"]
                result["relative_position"] = (relative_x, relative_y)

            else:
                pass
            
            # Stop the listener after one click
            return False  # Returning False stops the listener

    # Start the mouse listener (non-blocking)
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    # Wait for the listener to process the click (optional, but avoids exiting too soon)
    while listener.running:
        pass

    # Return the result (relative position or None)
    return result["relative_position"]

def initialize_shared_file(shared_file):
    with open(shared_file, "w") as f:
        json.dump({"frame_count": 0, "timestamp": "", "avg_color": (0, 0, 0)}, f)

def write_to_file(shared_file,data):
    with open(shared_file, "w") as f:
        json.dump(data, f)

def read_from_file(shared_file):
    try:
        with open(shared_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

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

def search_for_application(app_name):
    while True:
        app_window = get_application_window(app_name)
        if app_window is not None:
            return app_window
        
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

def searching_for_battle(app_window,battle_found_event,wait_event=threading.Event()):
    while not wait_event.is_set():
        process_data = read_from_file('Temp.json')
        capture = process_data.get("capture","Don't Know")
        time.sleep(2)
        # print(capture)
        if 'capture'.lower() in capture.lower():
            print("Battle search complete!")
            battle_found_event.set()
            click_on(app_window,click_coord['skip_listener'])
            break

def get_mouse_location_relative_on_click_and_write_to_notepad(app_window,battle_found_event, last_click_time, file_path="click_positions.txt"):
    result = {"relative_position": None}

    def on_click(x, y, button, pressed):
        if pressed:  # Check if the mouse button is pressed
            # Check if the click is within the application window
            if (app_window["left"] <= x <= app_window["left"] + app_window["width"] and
                app_window["top"] <= y <= app_window["top"] + app_window["height"]):
                
                # Calculate the position of the mouse relative to the application window
                relative_x = x - app_window["left"]
                relative_y = y - app_window["top"]
                result["relative_position"] = (relative_x, relative_y)

                 # Record the current time
                current_time = time.time()

                # Calculate time difference if there's a previous click
                if last_click_time[0] is not None:
                    time_difference = current_time - last_click_time[0]
                else:
                    time_difference = None

                # Update last click time
                last_click_time[0] = current_time

                # Append the relative position to the Notepad file
                if not battle_found_event.is_set():
                    with open(file_path, "a") as f:
                        if time_difference is not None:
                            f.write(f"({relative_x}, {relative_y})  {time_difference:.2f}\n")
                        else:
                            f.write(f"({relative_x}, {relative_y})\n")

                #print(f"Relative position: ({relative_x}, {relative_y})")
            else:
                print("Mouse click outside the application window.")
            
            # Stop the listener after one click
            return False  # Returning False stops the listener

    # Start the mouse listener (non-blocking)
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    # Wait for the listener to process the click (optional, but avoids exiting too soon)
    while listener.running:
        pass

    # Return the result (relative position or None)
    return result["relative_position"]

def click_logger(app_window,battle_found_event):
    # Path to the Notepad file where the click positions will be stored
    file_path = "click_positions.txt"
    print('STARTED LOGGING ##########################')
    last_click_time = [None]

    # This will run the clicker function until the battle_found_event is set
    while not battle_found_event.is_set():
        get_mouse_location_relative_on_click_and_write_to_notepad(app_window,battle_found_event, last_click_time, file_path)
        
        # Simulate a delay between checking
        time.sleep(0.5)
    print('ENDED LOGGING ##########################')

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
    #print(f"Clicked at ({screen_x}, {screen_y}) .")

def clicking_on_keep(app_window,waitEvent):
    while not waitEvent.is_set():
        process_data = read_from_file('Temp.json')
        keep = process_data.get("keep","Don't Know")
        if 'keep' in keep.lower():
            click_on(app_window,click_coord['keep'])
            break

def train_check(app_window):
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
    tempFrame = np.array(tempScreenshot)
    tempFrame = cv2.cvtColor(tempFrame, cv2.COLOR_BGRA2BGR)

    # M1T = tempFrame[m1t_appears[1]:m1t_appears[1] + m1t_appears[3],m1t_appears[0]:m1t_appears[0] + m1t_appears[2]]

    M1T = extract_text_region_name(tempFrame,*m1t_appears)
    M2T = extract_text_region_name(tempFrame,*m2t_appears)
    M3T = extract_text_region_name(tempFrame,*m3t_appears)
    M4T = extract_text_region_name(tempFrame,*m4t_appears)

    # print(M1T)
    # print(M2T)
    # print(M3T)
    # print(M4T)

    if 'ready' in M1T.lower():
        miscrit_levels["1"] += 1
        temp = miscrit_levels["1"]
        #send_discord_webhook(f"Miscrit 1 Leveled Up: {temp}")

        click_on(app_window,click_coord['miscrit1Train'])
        time.sleep(1)
        click_on(app_window,click_coord['trainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeTrainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeNewMoveMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip1'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip2'])
        time.sleep(1)
        

    if 'ready' in M2T.lower():
        miscrit_levels["2"] += 1
        temp = miscrit_levels["2"]
        #send_discord_webhook(f"Miscrit 2 Leveled Up: {temp}")

        click_on(app_window,click_coord['miscrit2Train'])
        time.sleep(1)
        click_on(app_window,click_coord['trainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeTrainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeNewMoveMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip1'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip2'])
        time.sleep(1)

    if 'ready' in M3T.lower():
        miscrit_levels["3"] += 1
        temp = miscrit_levels["3"]
        #send_discord_webhook(f"Miscrit 3 Leveled Up: {temp}")

        click_on(app_window,click_coord['miscrit3Train'])
        time.sleep(1)
        click_on(app_window,click_coord['trainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeTrainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeNewMoveMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip1'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip2'])
        time.sleep(1)

    if 'ready' in M4T.lower():
        miscrit_levels["4"] += 1
        temp = miscrit_levels["4"]
        #send_discord_webhook(f"Miscrit 4 Leveled Up: {temp}")

        click_on(app_window,click_coord['miscrit4Train'])
        time.sleep(1)
        click_on(app_window,click_coord['trainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeTrainMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['closeNewMoveMiscrit'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip1'])
        time.sleep(1)
        click_on(app_window,click_coord['evolSkip2'])
        time.sleep(1)
    
    click_on(app_window,click_coord['closeTrainMenu'])
    print('Train Check Ends ########################################')
    time.sleep(2)

def logout(app_window):
    click_on(app_window,click_coord['menu'])
    time.sleep(1)
    click_on(app_window,click_coord['logout'])
    time.sleep(3)
    click_on(app_window,click_coord['login'])
    time.sleep(7)

def battle(app_window,battle_found_event,threshold=60):
    global no_battle_counter

    if no_battle_counter >= 5:
        send_discord_webhook(f"Program Stuck.")

    if battle_found_event.is_set():
        no_battle_counter = 0
        #click_on(app_window,click_coord['attackRightTab'])

        print("Battle Started")
        process_data = read_from_file('Temp.json')
        capture = process_data.get("capture","Don't Know")

        commonAreaPokemon = ['Lumera','Snatcher','Hotfoot','Nessy >','Elefauma','Flameling \u2014','our >']
        #commonAreaPokemon = []

        right_pokemon = process_data.get("right_pokemon_name","Unkown")
        if right_pokemon not in commonAreaPokemon:
            send_discord_webhook(f"Rare Miscrit Found: {right_pokemon}")
            time.sleep(600)

        capturedOnce = 1 # 0

        while 'capture' in capture.lower() or 'cet' in capture.lower() or 'ya' in capture.lower() or 'c' in capture.lower():

            print('Waiting For Turn!')
            while True: 
                process_data = read_from_file('Temp.json')
                cap = process_data.get("capture","Don't Know")
                if 'capture' not in cap.lower() or 'cet' in cap.lower() or 'ya' in cap.lower() or 'c' in cap.lower():
                    break
                if cap.lower().strip() == '(Capture!)'.lower():
                    break
            print('Our Turn!')
            #time.sleep(2)

            process_data = read_from_file('Temp.json')
            capture = process_data.get("capture","Don't Know")
            capRate = process_data.get("capRate","Don't Know")
            currentIteration = process_data.get("iteration",-1)
            try:
                print('Capture Rate: ',capRate)
                try:
                    print(int(capRate))
                except:
                    pass
                if (capRate == '10C' or int(capRate) > threshold) and capturedOnce == 0:
                    print('Capturing!')
                    click_on(app_window,click_coord['capture'])
                    capturedOnce = 1
            except:
                pass
            print('Attacking!')
            click_on(app_window,click_coord['attack_1'])
            time.sleep(6) # Attack property
            print('Ending Turn\n#####################################################')
            
            while True:
                process_data = read_from_file('Temp.json')
                iteration = process_data.get("iteration",-1)
                if iteration!=currentIteration:
                    break  
            print('Capture Value:',capture)



        print("Finished Battle")
        click_on(app_window,click_coord['skip'])
        time.sleep(1)
        click_on(app_window,click_coord['close'])
        time.sleep(1)


        def wait_miscrits_caught(waitEvent):
            time.sleep(5)
            waitEvent.set()

        wait_event = threading.Event()
        click_thread = threading.Thread(target=clicking_on_keep,args=(app_window,wait_event,))
        click_thread.start()
        
        # Start the clicker function in its own thread
        waiting_thread = threading.Thread(target=wait_miscrits_caught,args=(wait_event,))
        waiting_thread.start()
        
        # Wait for both threads to finish
        click_thread.join()
        waiting_thread.join()

def recordRegime(app_window):
    file_path = "click_positions.txt"
    print("Variable access thread started...")
    battle_found_event = threading.Event()
    while not feed_stopped.is_set():
        # process_data = read_from_file('Temp.json')
        # left_pokemon_name = process_data.get("left_pokemon_name", "Unknown")
        # right_pokemon_name = process_data.get("right_pokemon_name", "Unknown")
        # capture = process_data.get("capture","Don't Know")
        # capRate = process_data.get("capRate","Don't Know")
        # skip = process_data.get("skip","Don't Know")
        # keep = process_data.get("keep","Don't Know")

        # # Simulate some delay in processing
        # time.sleep(1)

        # print(f"Left Pokémon: {left_pokemon_name}" + f"  Right Pokémon: {right_pokemon_name} ")
        # print(f"Capture Present: {capture} Capture Rate : {capRate}")
        # print(f"Skip Present: {skip} Keep present : {keep}\n\n\n\n")
        battle_found_event.clear()
        battle_thread = threading.Thread(target=searching_for_battle,args=(app_window,battle_found_event,))
        battle_thread.start()
        
        # Start the clicker function in its own thread
        clicker_thread = threading.Thread(target=click_logger,args=(app_window,battle_found_event,))
        clicker_thread.start()
        
        # Wait for both threads to finish
        battle_thread.join()
        clicker_thread.join()

        with open(file_path, "a") as f:
            f.write(f"Battle\n")
        battle(app_window,battle_found_event)

        # Blighted feindeer 
        
def playRegime(app_window):

    def wait_for_battle(battle_found_event,wait_event):
        global no_battle_counter
        time.sleep(10)
        if not battle_found_event.is_set():
            print('No Battle...\n')
            no_battle_counter += 1
            wait_event.set()

    file_name = 'Regime3.txt'
    with open(file_name, 'r') as file:
        lines = file.readlines()


    while True:
    # Process each line
        for line in lines:
            line = line.strip()  # Rem
            if line  not in ['Battle','Train','Logout','Heal']:
                print('Moving...\n')
                position = eval(line)
                #timeInt = i[1]
                click_on(app_window, position)
                time.sleep(4) # default: 2 | wait along with click_positions.txt
            elif line  == 'Battle':
                print('Battling...\n')
                waiting_event = threading.Event()
                battle_found_event = threading.Event()

                battle_found_event.clear()
                battle_thread = threading.Thread(target=searching_for_battle,args=(app_window,battle_found_event,waiting_event,))
                battle_thread.start()
                
                # Start the clicker function in its own thread
                waiting_thread = threading.Thread(target=wait_for_battle,args=(battle_found_event,waiting_event,))
                waiting_thread.start()
                
                # Wait for both threads to finish
                battle_thread.join()
                waiting_thread.join()

                battle(app_window,battle_found_event)

            elif line == 'Train':
                print('Training...\n')
                train_check(app_window)
            elif line == 'Logout':
                print('Logging Out...\n')
                logout(app_window)
            else:
                print('Healing...\n')
                click_on(app_window,click_coord['heal'])
                time.sleep(1)

def recording_feed(app_window,left_pokemon_name_region,right_pokemon_name_region,capture_appears,skip_appears,keep_appears,CaptureRate):
    sct = mss()

    print(f"Capturing application window: {app_window}")
    
    # Capture the application window in a loop
    iterationScanned = 0

    while True:
        # Grab the screen based on the application's window
        iterationScanned += 1
        screenshot = sct.grab(app_window)
        
        # Convert the screenshot to a NumPy array (BGR format for OpenCV)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR

        capture_image = frame[capture_appears[1]:capture_appears[1] + capture_appears[3],capture_appears[0]:capture_appears[0] + capture_appears[2]]
        cv2.imshow("Capture Appears", capture_image)

        #left_pokemon_name = extract_text_region_name(frame, *left_pokemon_name_region)
        right_pokemon_name = extract_text_region_name(frame, *right_pokemon_name_region)
        capture = extract_text_region_name(frame, *capture_appears)
        #skip = extract_text_region_name(frame, *skip_appears)
        keep = extract_text_region_name(frame, *keep_appears)
        capRate = extract_text_region_health(frame,*CaptureRate)

        process_data = {
        #    "left_pokemon_name": left_pokemon_name,
            "iteration":iterationScanned,
            "right_pokemon_name": right_pokemon_name,
            "capture": capture,
        #    "skip":skip,
            "keep":keep,
            "capRate":capRate,
        }
        write_to_file('Temp.json',process_data)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Stopping screen recording...")
            feed_stopped.set()
            break

def main():
    app_name = "Miscrits"  # Replace with the exact title of your application window
    initialize_shared_file('Temp.json')
    app_window = get_application_window(app_name)

    left_pokemon_name_region = (720, 72, 80, 20)  # x, y, w, h (adjust based on your game UI)
    right_pokemon_name_region = (1180, 72, 80, 15)
    capture_appears = (928,132,90,18)
    skip_appears = (914,609,70,18)
    keep_appears = (1028,621,70,20)
    CaptureRate = (951,150,20,20)

    screen_thread = threading.Thread(target=recording_feed,args=(app_window,left_pokemon_name_region,right_pokemon_name_region,capture_appears,skip_appears,keep_appears,CaptureRate))
    process_thread = threading.Thread(target=playRegime,args=(app_window,)) # recordRegime playRegime

    # Start threads
    screen_thread.start()
    process_thread.start()

    # Wait for threads to finish
    screen_thread.join()
    process_thread.join()

    print("All threads completed.")

if __name__ == "__main__":
    main()