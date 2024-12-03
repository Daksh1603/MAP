import base
from BattleStage.BattleLogic import battle

import threading
import time
import os
from pynput import mouse
import keyboard

def recordRegime(app_window,shared_data,resume_live_feed_event):
    file_path = "click_positions.txt"
    open(file_path, 'w').close()

    battle_found_event = threading.Event()
    recording_regime = threading.Event()
    while not recording_regime.is_set():
        

        ##### SEARCHING FOR BATTLE AND LOGGING ######
        battle_found_event.clear()
        battle_thread = threading.Thread(target=base.searching_for_battle,args=(app_window,shared_data,battle_found_event))
        battle_thread.start()
        clicker_thread = threading.Thread(target=click_logger,args=(app_window,battle_found_event,))
        clicker_thread.start()
        battle_thread.join()
        clicker_thread.join()
        #############################################

        with open(file_path, "a") as f:
            f.write(f"\nBattle\n")

        battle(app_window,battle_found_event,resume_live_feed_event,active_window=True)
        shared_data.append("Battle Ended...")

        # Call the rename function on key press ('S')
        rename_and_save_click_positions(file_path,recording_regime)
        

def click_logger(app_window,battle_found_event,file_path='click_positions.txt'):
    print('STARTED LOGGING ##########################')
    last_click_time = [None]

    def on_click(x, y, button, pressed):
        if pressed:  # Check if the mouse button is pressed
            # Check if the click is within the application window
            if (app_window["left"] <= x <= app_window["left"] + app_window["width"] and
                app_window["top"] <= y <= app_window["top"] + app_window["height"]):
                
                # Calculate the position of the mouse relative to the application window
                relative_x = x - app_window["left"]
                relative_y = y - app_window["top"]

                # Record the current time
                current_time = time.time()

                # Calculate time difference if there's a previous click
                time_difference = None
                if last_click_time[0] is not None:
                    time_difference = current_time - last_click_time[0]
                
                # Update last click time
                last_click_time[0] = current_time

                # Append the relative position to the Notepad file
                if not battle_found_event.is_set():
                    print(f"Logged: ({relative_x},{relative_y})")
                    with open(file_path, "a") as f:
                        if time_difference is not None:
                            f.write(f"{time_difference:.2f}\n({relative_x},{relative_y})  ")
                        else:
                            f.write(f"({relative_x},{relative_y})  ")
            else:
                print("Mouse click outside the application window.")

            # Stop the listener after one click
            return False

    # This will run until the battle_found_event is set
    while not battle_found_event.is_set():
        # Start the mouse listener for a single click
        listener = mouse.Listener(on_click=on_click)
        listener.start()

        # Wait for the listener to process the click
        while listener.running:
            time.sleep(0.1)

        # Simulate a small delay between checking
        time.sleep(0.5)

    print('ENDED LOGGING ##########################')

def rename_and_save_click_positions(file_path, recording_regime, timeout=2):
    print("Press 'S' to rename the file")
    start_time = time.time()  # Start the timer
    
    while True:
        if keyboard.is_pressed('s'):  # Detect 'S' key press
            new_name = input("Enter the new file name (without extension): ") + ".txt"
            if os.path.exists(file_path):
                # Rename the file to user input name
                os.rename(file_path, new_name)
                print(f"File renamed to {new_name}")
                recording_regime.set()
                break
            else:
                print(f"File {file_path} not found.")
                break
        
        # Check if timeout is reached
        if time.time() - start_time > timeout:
            print(f"Timeout reached. File was not renamed.\n")
            break
        
        time.sleep(0.1)  # Polling delay to avoid high CPU usage during the loop

