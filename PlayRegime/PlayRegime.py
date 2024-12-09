import base
from BattleStage.BattleLogic import battle
import Settings

import time
import threading
from mss import mss
import cv2
import numpy as np
import os

def playRegime(app_window,shared_data,resume_live_feed_event):
    def wait_for_battle(battle_found_event,wait_event):
        repeat = 0
        while not battle_found_event.is_set() and repeat<10:
            time.sleep(1)
            repeat+=1
            print(repeat)
        if not battle_found_event.is_set():
            print('No Battle...\n')
            wait_event.set()

    file_name = os.path.join('PlayRegime','Stored Regimes',Settings.REGIME_FILE) # Add file not found when creating UI
    with open(file_name, 'r') as file:
        lines = file.readlines()

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
                #print(delay)
                time.sleep(delay) # default: 2 | wait along with click_positions.txt

            elif line  == 'Battle':
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
            base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
            break

