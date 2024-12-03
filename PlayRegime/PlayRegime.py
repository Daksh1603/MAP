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

            if line not in ['Battle','Train','Logout','Heal']:
                print('Moving...\n')
                parts = line.split()
                coords = parts[0]
                delay = float(parts[1]) if len(parts) > 1 else 2.0
                position = eval(coords)
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
                train_check(app_window)

            elif line == 'Logout':
                print('Logging Out...\n')
                logout(app_window)

            else:
                print('Healing...\n')
                base.click_on(app_window,base.click_coord['heal'])
                time.sleep(1)
        
        if no_battle_counter >= 5:
            base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
            break

def train_check(app_window):
    print('Train Check Begins ########################################')
    base.click_on(app_window,base.click_coord['train'])
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

    M1T = base.extract_text_region_name(frame,*m1t_appears)
    M2T = base.extract_text_region_name(frame,*m2t_appears)
    M3T = base.extract_text_region_name(frame,*m3t_appears)
    M4T = base.extract_text_region_name(frame,*m4t_appears)

    timeDelay = 1.5

    if 'ready' in M1T.lower():
        level_up_miscrit(1,frame,app_window,timeDelay)

    if 'ready' in M2T.lower():
        level_up_miscrit(2,frame,app_window,timeDelay)

    if 'ready' in M3T.lower():
        level_up_miscrit(3,frame,app_window,timeDelay)

    if 'ready' in M4T.lower():
        level_up_miscrit(4,frame,app_window,timeDelay)
    
    base.click_on(app_window,base.click_coord['closeTrainMenu'])
    print('Train Check Ends ########################################')
    time.sleep(2)

def level_up_miscrit(miscrit_number, frame, app_window, timeDelay):
    """Helper function to handle the leveling up process for a miscrit."""
    miscrit_key = str(miscrit_number)
    level = base.extract_text_region_name(frame,*base.regions[f"Miscrit{miscrit_key}Level"])

    base.send_discord_webhook(f"Miscrit {miscrit_key} Leveled Up: {level}")
    
    # Perform the click actions for training
    base.click_on(app_window, base.click_coord[f'miscrit{miscrit_key}Train'])
    time.sleep(timeDelay)
    base.click_on(app_window, base.click_coord['trainMiscrit'])
    time.sleep(timeDelay)
    base.click_on(app_window, base.click_coord['closeTrainMiscrit'])
    time.sleep(timeDelay)
    base.click_on(app_window, base.click_coord['closeNewMoveMiscrit'])
    time.sleep(timeDelay)
    base.click_on(app_window, base.click_coord['evolSkip1'])
    time.sleep(timeDelay)
    base.click_on(app_window, base.click_coord['evolSkip2'])
    time.sleep(timeDelay)

def logout(app_window):
    base.click_on(app_window,base.click_coord['menu'])
    time.sleep(1)
    base.click_on(app_window,base.click_coord['logout'])
    time.sleep(3)
    base.click_on(app_window,base.click_coord['login'])
    time.sleep(7)

