import base
from BattleStage.BattleLogic import battle
import Settings

import time
import threading
from mss import mss
import cv2
import numpy as np
import os
from datetime import datetime

def playRegime(app_window,shared_data,resume_live_feed_event):
    def wait_for_battle(battle_found_event,wait_event):
        repeat = 0
        while not battle_found_event.is_set() and repeat<10:
            time.sleep(1)
            repeat+=1
            print(repeat)
        if not battle_found_event.is_set():
            base.LOG_STRING += f"NoBattle\n"
            print('No Battle...\n')
            wait_event.set()

    file_name = os.path.join('PlayRegime','Stored Regimes',Settings.REGIME_FILE) # Add file not found when creating UI
    with open(file_name, 'r') as file:
        lines = file.readlines()
    
    start_time = datetime.now()
    logs_file = start_time.strftime("Logs %m-%d.txt") #  %H-%M
    logs_file = os.path.join('Logs',logs_file)

    if os.path.exists(logs_file):
        with open(logs_file, 'r') as log:
            log_lines = log.readlines()
            if log_lines:  # Check if the file is not empty
                last_line = log_lines[-1].strip()  # Get the last line and remove any trailing whitespace
                parts = last_line.split(' ')  # Split the line by spaces
                if parts:  # Ensure there are parts to process
                    first_part = parts[0]  # Get the first part
                    separated = first_part.split(':')  # Split it by ':'
                    if separated:  # Ensure there are sub-parts
                        base.SEARCH_COUNT = int(separated[1]) + 1
        with open(logs_file, 'a') as logs:
                    logs.write("#####################################\n")
    else:
        open(logs_file, 'w').close()
    
    no_battle_counter = 0
    while True:
    # Process each line
        for line in lines:
            line = line.strip()

            if line not in ['Battle','Train','Logout','Heal'] and 'Wait' not in line:
                parts = line.split()
                coords = parts[0]
                delay = float(parts[1]) if len(parts) > 1 else 2.0
                position = eval(coords)
                print(f'Moving to {position}\n')
                base.click_on(app_window, position)
                # print(delay)
                time.sleep(delay) # default: 2 | wait along with click_positions.txt

            elif line  == 'Battle':

                current_time = datetime.now()
                time_difference = current_time - start_time
                hours, remainder = divmod(time_difference.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                base.LOG_STRING = f"SearchNo:{base.SEARCH_COUNT} {int(hours)}h:{int(minutes)}m:{int(seconds)}s "
                base.SEARCH_COUNT += 1

                if no_battle_counter >= 5:
                    base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
                    time.sleep(2)
                    break
                print('Looking for battle...')

                ## BATTLE SCAN ####
                waiting_event = threading.Event()
                battle_found_event = threading.Event()
                battle_thread = threading.Thread(target=base.searching_for_battle,args=(app_window,shared_data,battle_found_event,waiting_event,))
                battle_thread.start()
                waiting_thread = threading.Thread(target=wait_for_battle,args=(battle_found_event,waiting_event,))
                waiting_thread.start()
                battle_thread.join()
                waiting_thread.join()
                ######################

                if not battle_found_event.is_set():
                    no_battle_counter +=1
                else:
                    no_battle_counter = 0

                battle(app_window, battle_found_event, resume_live_feed_event)
                
                with open(logs_file, 'a') as logs:
                    logs.write(base.LOG_STRING)

            elif line == 'Train':
                print('Training...\n')
                base.train_check(app_window)

            elif line == 'Logout':
                print('Logging Out...\n')
                base.logout(app_window)
            elif 'Wait' in line:
                parts = line.split()
                delay = float(parts[1]) if len(parts) > 1 else 2.0
                print('Waiting...',delay)
                time.sleep(delay)
            else:
                print('Healing...\n')
                base.click_on(app_window,base.click_coord['heal'])
                time.sleep(1)
        
        if no_battle_counter >= 5:
            # base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
            break

