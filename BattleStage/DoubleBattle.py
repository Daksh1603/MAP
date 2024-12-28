import base
import Settings
from BattleStage.BattleLogic import battle
from BattleStage.AutoCapture import auto_capture

import cv2
from mss import mss
import time
import numpy as np
import threading
import asyncio
import subprocess
import json
import ast
import os
from datetime import datetime

tracking_list = None
with open("TrackingMiscrits.txt", "r") as f:
    tracking_list = eval(f.read() or "[]")

def playDoubleBattle(app_window,shared_data,resume_live_feed_event):
    search_count_wh = [0]
    def search_cooldown(search_count_wh):

        if search_count_wh[0] % 100 == 0 and search_count_wh[0] != 0:
            base.send_discord_webhook(f"We are on Search {search_count_wh[0]}!")

        if search_count_wh[0] >= Settings.DOUBLE_BATTLE_SEARCH_COUNT:
            base.send_discord_webhook(f"Tired af, fininshed all {Settings.DOUBLE_BATTLE_SEARCH_COUNT} searches , imma chill now ")
            time.sleep(24*60*60)
        else:
            search_count_wh[0] += 1
            time.sleep(20)

    file_name = os.path.join('PlayRegime','Stored Regimes',Settings.REGIME_FILE) # Add file not found when creating UI
    with open(file_name, "r") as file:
        first_line = file.readline().strip() 
    coord = eval(first_line.split()[0])

    ############# LOGGING #######################    
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
                    logs.write("##################################### ")
    else:
        open(logs_file, 'w').close()
    ###############################################
    no_battle_counter = 0

    while True:
        print('Search No. : ',search_count_wh[0])
        current_time = datetime.now()
        time_difference = current_time - start_time
        hours, remainder = divmod(time_difference.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        base.LOG_STRING = f"\nSearchNo:{base.SEARCH_COUNT} {int(hours)}h:{int(minutes)}m:{int(seconds)}s "
        base.SEARCH_COUNT += 1
            
        waiting_event = threading.Event()
        battle_found_event = threading.Event()
        
        ##### WILD HUNT #####
        double_battle_thread = threading.Thread(target=DoubleBattle_WRAPPER,args=(app_window,shared_data,battle_found_event,waiting_event,coord,))
        double_battle_thread.start()
        search_cooldown_thread = threading.Thread(target=search_cooldown,args=(search_count_wh,))
        search_cooldown_thread.start()
        double_battle_thread.join()
        search_cooldown_thread.join()
        ######################

        if not battle_found_event.is_set():
            no_battle_counter +=1
        else:
            no_battle_counter = 0
        if no_battle_counter >= 5:
            base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
            break

        with open(logs_file, 'a') as logs:
            logs.write(base.LOG_STRING)

def DoubleBattle_WRAPPER(app_window,shared_data,battle_found_event,resume_live_feed_event,coord):
    def wait_for_battle(battle_found_event,wait_event):
        repeat = 0
        while not battle_found_event.is_set() and repeat<10:
            time.sleep(1)
            repeat+=1
            print(repeat)
        if not battle_found_event.is_set():
            base.LOG_STRING += f"NoBattle "
            print('No Battle...\n')
            wait_event.set()

    print('Clicking on Object...')
    base.click_on(app_window,coord)
    print('Looking for battle...')

    ## BATTLE SCAN ####
    waiting_event = threading.Event()
    battle_thread = threading.Thread(target=base.searching_for_battle,args=(app_window,shared_data,battle_found_event,waiting_event,))
    battle_thread.start()
    waiting_thread = threading.Thread(target=wait_for_battle,args=(battle_found_event,waiting_event,))
    waiting_thread.start()
    battle_thread.join()
    waiting_thread.join()
    ######################
    
    DoubleBattle(app_window, battle_found_event, resume_live_feed_event)



def DoubleBattle(app_window,battle_found_event,resume_live_feed_event,active_window=False):
    global tracking_list

    right_pokemon_name_region = (1180, 72, 80, 15)
    skip_region = (934,607,40,20)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15)
    skip_new_miscrit_caught = (930,743,70,20)
    capture_rate_region = (951,150,20,20)
    common_miscrits_file = 'CommonMiscrits.txt'

    need_to_train = None
    register_cap = 1
    
    if battle_found_event.is_set():
        print('Cleared resume_live_feed_event')
        resume_live_feed_event.clear()


        with open(common_miscrits_file, 'r') as file:
            file_content = file.read().strip()
        commonAreaPokemon = ast.literal_eval(file_content)

        print("Battle Started")

        sct = mss()
        ###########################

        discord_battle_completed = 0
        raise_alert = 0

        existing_list = None
        with open('capRates.txt', 'r') as file:
            content = file.read().strip()
            existing_list = eval(content)
        

        while True:
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            current_miscrit = base.extract_text_region_name(frame, *right_pokemon_name_region)
            close = base.extract_text_region_name(frame,*close_region) # -> close (t1)
            turn = base.extract_text_region_name(frame,*turn_region)
            cap_rate = base.extract_text_region_name(frame, *capture_rate_region)

            if 'turn' in turn.lower() or 'your' in turn.lower():
                ######################## RARE MISCRIT LOGIC ###############################
                if cap_rate not in existing_list:
                        if cap_rate == 'ry:':
                            cap_rate = 'ry'
                        filepath = os.path.join('capRates', f"{cap_rate}.png")
                        cv2.imwrite(filepath, frame)
                        existing_list.append(cap_rate)
                        with open('capRates.txt', 'w') as file:
                            file.write(str(existing_list))
                            
                if register_cap:
                    register_cap = 0
                    if str(cap_rate) in Settings.RATING_ALERT_LIST:
                        raise_alert = 1
                    base.LOG_STRING += f"MISCRIT:{current_miscrit.strip()} CAP_RATE:{cap_rate} "

                if (current_miscrit not in commonAreaPokemon or (current_miscrit in tracking_list) or raise_alert) and not active_window:
                    auto_capture(app_window,current_miscrit,cap_rate)
                    with open("TrackingMiscrits.txt", "r") as f:
                            tracking_list = eval(f.read() or "[]")  
                    break
                ########################### ADD DISCORD LOGIC ############################## Only Defeating Currently, Can Add Capture Logic Later
                print('Attacking!')
                base.click_on(app_window,base.click_coord['attack_1'])
                time.sleep(1.5)
                print('Ending Turn\n#####################################################')
                ############################################################################
            elif 'close' in close.lower():
                need_to_train = check_if_train_req(frame)
                base.click_on(app_window,base.click_coord["close"])
                time.sleep(1.5)
                print("Finished Battle")
                break
            else:
                pass
        
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        Skip = base.extract_text_region_name(frame, *skip_new_miscrit_caught)
        if 'skip' in Skip.lower():
            base.click_on(app_window,base.click_coord["caughCritSkip"])
            time.sleep(1)
    
    if need_to_train is not None:
        base.train_check(app_window,*need_to_train)
    resume_live_feed_event.set()

def check_if_train_req(frame):
    miscrit1ready_region = (680,482,93,10)
    miscrit2ready_region = (824,482,93,10)
    miscrit3ready_region = (680,576,93,10)
    miscrit4ready_region = (824,576,93,10)

    M1R = base.extract_text_region_name(frame,*miscrit1ready_region)
    M2R = base.extract_text_region_name(frame,*miscrit2ready_region)
    M3R = base.extract_text_region_name(frame,*miscrit3ready_region)
    M4R = base.extract_text_region_name(frame,*miscrit4ready_region)

    if 'train' in M1R.lower() or 'train' in M2R.lower() or 'train' in M3R.lower() or 'train' in M4R.lower():
        return (M1R,M2R,M3R,M4R)
    else:
        return None